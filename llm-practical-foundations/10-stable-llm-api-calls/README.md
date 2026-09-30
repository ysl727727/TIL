# 10장. 안정적인 LLM API 호출 — Timeout · Rate Limit · Retry · Fallback

> 2026-09-29 기록(강의 자료는 2026-09-23 확보). 10장 1강 이론을 정리했습니다. 밀려 있던 강의를 뒤늦게 따라잡은 회차라 앞 장(2\~9장)보다 먼저 정리되었습니다. 실습 파일은 아직 받지 못해 이론만 기록합니다.
>
> 선수지식으로 걸려 있는 7-3강(Validation Error 처리와 출력 복구)과 8장(Tool/Function Calling 파이프라인)은 아직 수강 전이라, Tool 관련 서술은 개념 수준으로만 정리했습니다. 데이터 엔지니어링 8장이 **우리가 만든 API 안에서의 최소 안정성**이었다면, 이 장은 **OpenAI Responses API를 직접 호출하는 쪽**의 재시도·대기·대체 경로 설계를 다룹니다.

## 학습 목표

- API 오류를 재시도 가능 여부에 따라 분류한다.
- OpenAI Python SDK의 기본 retry·timeout 동작을 설명한다.
- `APIConnectionError` / `APITimeoutError` / `RateLimitError` / `APIStatusError`를 구분한다.
- Exponential backoff와 Full Jitter를 구현한다.
- 인증·잘못된 요청처럼 재시도하면 안 되는 오류를 구분한다.
- 실패 시 모델·기능·사람 처리로 이어지는 fallback ladder를 설계한다.

## 실습 파일

| 강 | 파일 | 실습 상태 |
| --- | --- | --- |
| 10-1 | — | **자료 미수령** — 교안의 로컬 retry 함수·Responses API wrapper 코드만 읽고 정리. 직접 실행하지 않음 |

## 핵심 이론

### 1. 안정적인 호출은 오류를 숨기는 코드가 아니다

네트워크 API는 정상적인 코드에서도 일시적으로 실패한다. 안정적인 호출 코드는 다음 여섯 질문에 답한다 — 이 오류는 다시 시도하면 해결될 가능성이 있나? 얼마나 기다렸다 시도하나? 최대 몇 번 시도하나? 재시도하는 동안 같은 부작용이 중복되지 않나? 모두 실패하면 사용자에게 무엇을 안내하나? 운영자가 원인을 찾도록 무엇을 기록하나?

**Retry는 오류를 없애는 마법이 아니라, 일시적 실패에서 회복할 기회를 주는 제한된 정책이다.**

### 2. 오류 분류가 먼저

| 종류 | 예시 | 기본 대응 |
| --- | --- | --- |
| 입력·인증 | 400, 401, 403 | 요청 수정 또는 즉시 중단 |
| Rate limit | 429 | jitter가 있는 backoff |
| 일시 서버 오류 | 5xx | 제한적 retry |
| 네트워크·Timeout | 연결 실패 | retry 또는 fallback |
| 업무 실패 | Schema·도구 오류 | 복구 정책 또는 사용자 안내 |

재시도를 고려하는 오류는 네트워크 연결 실패, timeout, 408, 409, 429, 5xx다. 반대로 **재시도 전에 설정을 고쳐야 하는 오류**는 잘못된 API key, 400 Bad Request, 지원하지 않는 model/feature, Pydantic 업무 규칙 실패, permission denied다.

HTTP status만으로 부족할 때는 응답 body의 오류 코드, `Retry-After` header, 외부 Tool의 `retryable` 필드까지 확인한다. 예외 객체의 status code와 request ID를 로그에 남기면 운영자가 원인을 찾기 쉽다.

### 3. 오류 처리의 큰 그림

```text
API 요청 → 성공: 응답 검증 후 반환
         → 실패 ├ retryable: backoff 후 제한 횟수 재시도
                ├ non-retryable: 즉시 중단하고 설정/입력 오류 반환
                └ 횟수 소진: fallback 또는 사용자 안내
```

### 4. Retry 책임은 한 계층에만 모은다

오류 처리에는 세 층이 있다 — SDK 층(OpenAI Python SDK가 일부 네트워크/HTTP 오류를 기본 재시도), 애플리케이션 층(업무 단위 retry·fallback·circuit breaker·사용자 메시지), Tool/외부 시스템 층(DB·사내 API·결제 시스템 각각의 정책).

여러 층에서 모두 긴 retry를 쓰면 실제 호출 횟수가 곱셈처럼 늘어난다.

```text
SDK 3회 × 애플리케이션 3회 × Tool API 3회 → 최악의 경우 최대 27회
```

OpenAI Python SDK는 연결 오류·408·409·429·5xx를 **기본 두 번 재시도**한다. 따라서 둘 중 하나를 명시적으로 고른다.

- **A**: SDK retry를 사용하고 애플리케이션은 fallback만 담당한다.
- **B**: `OpenAI(max_retries=0)`으로 SDK retry를 끄고 애플리케이션 wrapper가 횟수·deadline·로그를 통합 관리한다.

```python
client = OpenAI(max_retries=0, timeout=20.0)   # 수동 retry 동작을 명확히 보기 위한 설정
```

### 5. Timeout은 작업 유형별로

```python
client = OpenAI(
    timeout=httpx.Timeout(60.0, connect=5.0, read=45.0, write=10.0)
)
```

SDK 기본 timeout은 매우 길 수 있어 사용자-facing 서비스에서는 명시하는 편이 좋다. Reasoning이나 큰 멀티모달 요청은 단순 분류보다 오래 걸리므로, **모든 태스크에 같은 값을 쓰기보다 작업 유형별 기준을 정한다.**

### 6. Exponential Backoff와 Full Jitter

Exponential backoff는 재시도 간격을 점점 늘린다(1초 → 2초 → 4초). Jitter는 여러 client가 정확히 같은 시각에 다시 몰리지 않도록 대기 시간을 무작위화한다. 이 교안은 **Full Jitter**를 쓴다.

```text
상한 = min(max_delay, base_delay × 2^attempt)
대기 시간 = Uniform(0, 상한)
```

```python
def calculate_backoff_seconds(attempt_index: int, base_delay: float = 1.0,
                              max_delay: float = 20.0) -> float:
    if attempt_index < 0:
        raise ValueError("attempt_index는 0 이상이어야 합니다.")
    if base_delay <= 0 or max_delay <= 0:
        raise ValueError("base_delay와 max_delay는 0보다 커야 합니다.")
    exponential_limit = base_delay * (2 ** attempt_index)
    upper_bound = min(exponential_limit, max_delay)
    return random.uniform(0.0, upper_bound)
```

상한은 지수적으로 커지지만 실제 대기 시간은 0과 상한 사이에서 무작위로 고른다. `max_delay`로 장애가 길어져도 한 번에 기다리는 시간이 무한히 커지지 않게 막는다.

**Rate limit에 걸린 실패 요청도 사용량 제한 계산에 포함될 수 있다** — 기다림 없이 빠르게 반복하면 상황이 악화된다. 서버가 `Retry-After`를 주면 그 값을 우선 고려하되, 무한정 긴 값을 그대로 기다리지 않도록 애플리케이션 최대 대기 정책도 함께 둔다.

### 7. Fallback Ladder

모든 재시도가 실패했을 때의 다음 경로를 미리 정의한다.

```text
1. 기본 모델 호출
2. 같은 모델 재시도
3. 더 단순한 Prompt 또는 출력 축소
4. 허용된 대체 모델
5. 캐시된 이전 결과 또는 기능 축소
6. 사람 검토 / 나중에 다시 시도 안내
```

Fallback은 오류를 숨기는 장치가 아니라 **사용자가 현재 상태와 다음 행동을 알게 하는 graceful degradation**이다. 품질과 기능이 달라질 수 있으므로 사용자에게 숨기지 않고, fallback이 사용되었다는 로그를 남긴다.

대체 모델을 쓸 때는 같은 Tool과 Structured Output을 지원하는지, model-specific 파라미터가 지원되는지, 품질·가격 차이가 어떤지를 먼저 확인한다.

### 8. 로컬 retry 함수 (기본 실습)

API 비용 없이 동작을 확인하려면 **정해진 횟수만 실패하는 가짜 함수**를 만들어 wrapper에 넣는다.

```python
def retry_call(operation, max_attempts=3, sleep_function=time.sleep):
    if max_attempts < 1:
        raise ValueError("max_attempts는 1 이상이어야 합니다.")
    total_wait = 0.0
    for attempt in range(1, max_attempts + 1):
        try:
            value = operation()
            return value, RetryReport(attempt, total_wait)
        except TemporaryError:
            if attempt == max_attempts:
                raise
            delay = calculate_backoff_seconds(attempt - 1)
            total_wait += delay
            sleep_function(delay)
```

- 재시도 대상 예외(`TemporaryError`)만 잡고 나머지는 그대로 올린다.
- `sleep_function`을 인자로 받으면 테스트에서 실제 대기 없이 호출만 기록할 수 있다.
- 시도 횟수와 누적 대기 시간을 함께 반환해 나중에 관찰할 수 있게 한다.

### 9. Responses API wrapper (추가 실습)

```python
def is_retryable_status(status_code: int | None) -> bool:
    if status_code is None:
        return False
    return status_code in {408, 409, 429} or status_code >= 500
```

`create_response_with_retry()`는 예외 종류별로 갈라진다.

| 예외 | 처리 |
| --- | --- |
| `AuthenticationError`, `BadRequestError` | **즉시 중단** — 설정·입력을 고치지 않으면 같은 오류가 반복된다 |
| `RateLimitError` | 재시도하되 횟수/deadline을 제한 |
| `APIConnectionError`, `APITimeoutError` | 재시도 |
| `APIStatusError` | `is_retryable_status()`로 판단 |

결과는 `ok` / `output_text` / `error_code` / `attempts` / `latency_ms` / `request_id`를 담은 하나의 객체로 반환한다. `request_id`는 장애 문의와 추적에 쓰이므로 **성공·실패 로그 모두에** 남긴다. 성공 여부를 예외 대신 반환값으로 표현하면 호출하는 쪽이 분기하기 쉽다.

## 질문과 새로 알게 된 점

- 가장 인상 깊었던 것은 **retry 계층을 겹치면 27회까지 늘어날 수 있다**는 계산이었다. "SDK도 재시도한다"는 사실을 모르면 내 wrapper의 3회가 실제로는 3회가 아니다.
- Jitter는 "대충 랜덤하게"가 아니라 여러 client가 같은 순간에 다시 몰리는 재시도 폭주를 막기 위한 것이다.
- 429를 즉시 빠르게 재시도하면 실패 요청도 한도에 포함돼 상황이 더 나빠진다 — 데이터 엔지니어링 8장에서 429를 재시도 대상에서 뺀 이유와 같은 맥락이다. 두 과정이 다른 자리(외부 호출 / 우리 API)에서 같은 결론에 도달한 점이 인상적이었다.
- `sleep_function`을 주입 가능하게 만든 설계 덕분에 테스트가 빨라진다는 점이 실용적이었다.
- 자주 하는 오해: "재시도를 많이 하면 안정적이다"(비용과 지연만 커진다) / "429는 키가 틀렸다는 뜻이다"(인증 실패는 401) / "fallback은 사용자에게 안 보여도 된다"(품질이 달라진 것을 숨기면 안 된다) / "SDK 기본 설정만 믿으면 된다"(어느 계층이 retry를 담당하는지 문서화해야 한다).
