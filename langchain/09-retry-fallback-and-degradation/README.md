# 9장. 실패 대응 — Retry · Fallback · graceful degradation

> 2026-10-01 학습 기록. 예외 종류로 다음 행동을 정해서, 회복 가능한 오류만 제한된 횟수로 다시 하고(Retry), 계속 안 되면 기능이 줄었음을 알리는 대체 경로로 가며(Fallback), 입력·코드 오류는 바로 멈추는 흐름을 정리했습니다.

## 학습 목표

- 오류를 "다시 하면 회복될 수 있나"로 나눠 Retry / Fallback / 즉시 실패를 고른다.
- `stop_after_attempt=N`의 N이 **최초 호출을 포함한** 전체 시도 횟수임을 설명한다.
- Retry는 모델 호출 같은 좁은 단계에만 붙이고, 내부 재시도(`max_retries=0`)와 곱해지지 않게 한 계층만 주인으로 둔다.
- Primary와 Fallback이 같은 출력 계약(`UserAnswer`)을 돌려주고 `status`·`route`로만 구분하게 한다.
- `exceptions_to_handle`에는 구체적인 예외만 넣어 입력·코드 오류를 숨기지 않는다.

## 실습 파일

| 강 | 주제 | 실습 상태 |
| --- | --- | --- |
| 9-1 | with_retry와 예외 유형별 처리 | 📘 이론 정리 |
| 9-2 | Fallback model/chain과 graceful degradation | 📘 이론 정리 |

실습 노트북은 이번 기록에 포함하지 않았습니다. 6\~10장은 이론 분량이 많아, 실습은 10장 통합 실습(`starter.py`) 하나로 정리했습니다. 아래 확인 문제는 API 없이 풀 수 있는 복습용 문제입니다.

## 전체 흐름

### 한 문장

**실패를 세 갈래로 나눕니다. 다시 하면 될 것은 정해진 횟수만큼 다시 하고(Retry), 계속 안 되면 기능을 줄인 대체 경로로 가고(Fallback), 입력·코드 문제는 바로 멈춥니다.**

### 왜 필요한가

모델 서버는 잠깐씩 응답하지 못할 때가 있습니다. 한 번 실패했다고 끝내면 사용자는 아무것도 못 받습니다. 그렇다고 빈 질문 같은 입력 오류까지 반복하면 시간만 낭비합니다.

**비유:** 친구에게 전화를 겁니다.

- 신호가 잠깐 끊겼다 → **다시 건다** (Retry, 최대 2번까지만)
- 계속 안 받는다 → **문자를 남긴다**: "지금 통화가 안 돼서 나중에 다시 연락할게" (Fallback, 할 수 있는 만큼만 하고 한계를 알림)
- 전화번호가 틀렸다 → 몇 번을 다시 걸어도 소용없으니 **번호부터 고친다** (즉시 실패)

### 그림으로 보기 — 예외 종류가 다음 행동을 정한다

```text
오류 발생 → 어떤 예외인가?
 ├─ 일시 오류 (TemporaryModelError)  → Retry: 같은 모델 단계를 다시 (첫 호출 포함 최대 N번)
 │                                       ├─ 중간에 성공 → 정상 결과
 │                                       └─ N번 다 실패 → 마지막 오류를 위로 전달 ─┐
 ├─ Primary 장애 (PrimaryUnavailable) ← ──────────────────────────────────────────┘
 │                                    → Fallback 1번: UserAnswer(status="degraded", route="fallback")
 └─ 입력·코드 오류 (ValueError, TypeError) → 반복도 대체도 없이 바로 호출자에게 전달

정상일 때: Primary → UserAnswer(status="ok", route="primary")   (Fallback은 실행 안 함)
```

### 강의 흐름

1. **9-1 구분하기** — 오류가 나면 먼저 "같은 입력·같은 경로를 반복하면 결과가 달라질 수 있나?"를 판단. 일시적인 연결 실패·서버 과부하는 제한된 Retry, 빈 질문·잘못된 자료형·코드의 `TypeError`는 즉시 실패.
2. **9-1 다시 하기** — 실패 가능성이 있는 **좁은 단계(모델 호출)**만 `RunnableLambda(...).with_retry(...)`. 시도 예산을 다 써도 실패하면 마지막 오류를 호출자에게 전달.
3. **9-2 대체하기** — Primary가 허용된 장애(`PrimaryUnavailable`)로 실패하면 Fallback을 한 번 실행. Fallback은 상세 답을 추측하지 않고 "지금은 제한됨 + 다음 행동"을 `status="degraded"`, `route="fallback"`으로 반환. 정책 밖 오류(`ValueError`)는 그대로 전달.

```text
오류 발생 ─ 어떤 예외인가?
   ├─ TemporaryModelError (회복 가능) ─→ with_retry: 같은 모델 단계 다시 실행 (최초 포함 최대 N회)
   │                                        ├─ 중간에 성공 → 결과
   │                                        └─ N회 모두 실패 → 마지막 오류를 호출자에게 전달
   │                                                             │
   │                                         with_fallbacks가 이 오류를 허용하면 ↓
   ├─ PrimaryUnavailable (대체 허용) ────→ Fallback 1회 → UserAnswer(status="degraded", route="fallback")
   └─ ValueError · TypeError (입력·코드) → 반복·대체 없이 즉시 호출자에게 전달

정상: Primary → UserAnswer(status="ok", route="primary")   ← Fallback 호출 0회
```

8장 → 9장 연결고리: 8-2에서 `ChatOpenAI(max_retries=0)`으로 SDK 내부 Retry를 끈 이유가 여기서 나옵니다. 바깥 LCEL Retry와 내부 Retry를 동시에 켜면 시도 횟수가 **곱해집니다.** 5-3의 "수정 요청은 1회"도 같은 생각입니다: 반복에는 반드시 상한이 있어야 합니다.

## 핵심 이론

### 1. with_retry와 예외 유형별 처리 (9-1강)

Retry는 모든 오류를 없애는 기능이 아니라, **다시 실행하면 회복될 가능성이 있는 오류**에 제한된 시도 기회를 추가하는 정책입니다.

| 오류 사례 | 기본 처리 | 이유 |
| --- | --- | --- |
| 일시적인 모델 연결 실패 | 제한된 Retry | 다음 호출에서 연결이 회복될 수 있음 |
| 순간적인 서버 과부하 | 제한된 Retry | 잠시 뒤 처리될 가능성 |
| 비어 있는 질문 | 즉시 실패 | 같은 입력을 반복해도 안 바뀜 |
| 잘못된 자료형 | 즉시 실패 | 입력 계약을 먼저 수정 |
| 코드의 `TypeError` | 즉시 실패 | 코드를 고쳐야 해결 |

**계획된 일시 오류** — 우연한 장애를 기다리면 결과가 매번 달라지므로, 호출 횟수를 세어 정해진 횟수만큼 오류를 냅니다.

```python
from langchain_core.runnables import RunnableLambda

class TemporaryModelError(RuntimeError):
    """다시 시도하면 회복될 수 있는 교육용 일시 오류"""

state = {"attempts": 0}
def call_model(question: str) -> str:
    state["attempts"] += 1                                   # 진입할 때마다 +1
    if not isinstance(question, str) or not question.strip():
        raise ValueError("질문은 비어 있지 않은 문자열이어야 합니다.")   # Retry 제외
    if state["attempts"] <= 1:
        raise TemporaryModelError("계획된 일시 모델 오류입니다.")        # Retry 대상
    return "정상 응답"

model_step = RunnableLambda(call_model)
retry_step = model_step.with_retry(
    retry_if_exception_type=(TemporaryModelError,),   # 이 예외만 다시 실행
    stop_after_attempt=2,                             # 최초 호출 포함 최대 2번
    wait_exponential_jitter=False,                    # 수업용: 실제 대기·무작위 지연 제거
)
answer = retry_step.invoke("LCEL Retry를 설명해 주세요.")   # 정상 응답, attempts=2
```

- `with_retry()`는 기존 `model_step`을 바꾸지 않고 **새 Runnable**을 반환합니다 → 이후에는 `retry_step.invoke(...)`.
- `stop_after_attempt=2` = 최초 1번 + 추가 1번. "첫 호출 뒤 두 번 더"가 **아닙니다**.

| 설정된 실패 횟수 | 최대 시도 | 결과 | 실제 호출 |
| --- | --- | --- | --- |
| 0 | 2 | 첫 호출 성공 | 1 |
| 1 | 2 | 두 번째 호출 성공 | 2 |
| 3 | 2 | 두 번 실패 후 마지막 오류 전달 | 2 |

- 예산을 다 쓰면 마지막 `TemporaryModelError`가 호출자에게 전달됩니다. 빈 문자열이나 성공처럼 바꾸면 상위 코드가 실패를 알 수 없어 Fallback·사용자 안내를 선택할 수 없습니다.
- `ValueError`는 목록에 없으므로 `stop_after_attempt=3`이어도 **한 번만** 실행됩니다. Retry 정책은 성공 결과뿐 아니라 제외 오류의 실제 호출 횟수로도 검증합니다.

| 예외 | Retry | 다음 행동 |
| --- | --- | --- |
| `TemporaryModelError` | 예 | 허용 횟수 안에서 같은 모델 단계 다시 실행 |
| `ValueError` | 아니요 | 입력을 고친 뒤 새로 실행 |
| `TypeError` | 아니요 | 코드와 자료형 계약 확인 |

**Retry 적용 경계와 timeout**

```text
입력 확인 → 문서 검색 → 모델 호출 → 결과 저장
                          ↑ Retry는 여기에만
```

- 전체 흐름에 Retry를 붙이면 모델 오류 한 번에 검색·저장까지 반복되고, 저장·메시지 전송 같은 **부작용이 두 번** 일어날 수 있습니다.
- Retry(실패한 호출을 조건에 따라 다시 실행) ≠ timeout(한 번의 호출이 기다릴 수 있는 시간 제한). `with_retry()`를 붙여도 한 호출이 끝없이 기다리는 문제는 해결되지 않습니다 → 모델 클라이언트의 `timeout`을 따로 설정.
- **Retry의 주인은 한 계층만.** 바깥 `with_retry(stop_after_attempt=2)` × 클라이언트 내부(최초 + 내부 Retry 2번 = 3번) = 최악 **2 × 3 = 6회** HTTP 요청. 바깥에서 관리하면 `ChatOpenAI(timeout=20, max_retries=0, ...)`로 내부 Retry를 끕니다. 내부 Retry를 쓴다면 곱해지는 요청 수·지연·비용을 계산해 기록합니다.

완성 실습 출력:

```text
=== Retry 복구 ===        status=success attempts=2 answer=정상 응답
=== Retry 소진 ===        status=error attempts=2 error=TemporaryModelError
=== Retry 제외 오류 ===   status=error attempts=1 error=ValueError
```

세 사례는 각각 **새 호출 횟수 dict**를 써서 이전 실행의 상태가 섞이지 않습니다.

| 자주 생기는 오해 | 바로잡기 |
| --- | --- |
| `stop_after_attempt=2`는 최초 호출 뒤 두 번 더 | 최초 포함 전체 2번, 추가 Retry는 최대 1번 |
| 모든 예외를 Retry하면 더 안정적 | 입력·코드 오류는 반복해도 해결 안 됨 → 구체 예외만 |
| Retry를 적용하면 timeout도 설정됨 | 별도 정책. 한 호출의 제한 시간은 따로 |
| 바깥 Retry만 세면 실제 요청 수를 앎 | 내부 자동 Retry가 곱해짐 → 한 계층만 주인으로 |
| 전체 앱에 Retry가 가장 간단 | 검색·저장까지 반복 → 좁은 단계에만 |
| 마지막 실패를 빈 문자열로 바꾸기 | 실패가 성공처럼 보임 → 호출자에게 전달, Fallback으로 처리 |

### 2. Fallback model/chain과 graceful degradation (9-2강)

| 처리 방식 | 판단 질문 | 예시 |
| --- | --- | --- |
| Retry | 같은 경로를 다시 실행하면 회복될 수 있는가? | 첫 모델 호출의 일시 오류 |
| Fallback | Primary 대신 쓸 수 있는 **허용된** 대체 경로가 있는가? | 상세 답변 대신 고정된 제한 안내 |
| 즉시 실패 | 반복하거나 대체하면 안 되는 오류인가? | 빈 입력, 코드 오류 |

- Primary가 정상이면 Fallback을 호출하지 않습니다. `PrimaryUnavailable`이면 Fallback을 한 번 실행하고, `ValueError`는 숨기지 않고 전달합니다.
- Fallback은 "Primary가 정상인데 더 싼 경로를 고르는 분기"가 아니라, **Primary가 처리할 수 없을 때만** 실행되는 경로입니다.
- 실제 모델이 Primary라면 내부 Retry + 바깥 Retry가 모두 소진된 뒤 Fallback으로 가므로 요청 수·대기 시간이 겹쳐 커질 수 있습니다 → `max_retries=0`으로 내부를 끄고 Fallback 전 최대 요청 수를 한곳에서 계산.

**공통 출력 계약** — 두 경로가 같은 타입을 반환해야 호출자·화면이 하나의 코드로 처리하고 상태만 구분합니다.

```python
from typing import Literal
from pydantic import BaseModel

class UserAnswer(BaseModel):
    status: Literal["ok", "degraded"]
    answer: str
    route: Literal["primary", "fallback"]
```

| 필드 | Primary 정상 | Fallback 전환 |
| --- | --- | --- |
| `status` | `"ok"` | `"degraded"` |
| `answer` | 정상 처리 문장 | 기능 제한 + 재시도 안내 |
| `route` | `"primary"` | `"fallback"` |

`status="degraded"`는 "실패"만 뜻하지 않습니다. 대체 경로가 **정상 실행됐지만 제공 기능이 줄었다**는 뜻입니다.

**Primary의 세 가지 동작 (`primary_mode`)**

| `primary_mode` | Primary 동작 | 기대 결과 |
| --- | --- | --- |
| `"normal"` | 정상 `UserAnswer` 반환 | Primary로 종료 |
| `"unavailable"` | `PrimaryUnavailable` 발생 | Fallback 전환 |
| `"invalid"` | `ValueError` 발생 | 호출자에게 오류 전달 |

```python
class PrimaryUnavailable(RuntimeError):
    """Primary가 일시적으로 응답할 수 없음"""

def fallback(payload: dict[str, str]) -> UserAnswer:
    calls["fallback"] += 1
    if not payload.get("question", "").strip():            # Fallback도 최소 입력 계약 확인
        raise ValueError("Fallback 질문도 비어 있지 않아야 합니다.")
    return UserAnswer(status="degraded",
                      answer="현재 상세 답변을 만들 수 없습니다. 잠시 후 다시 시도해 주세요.",
                      route="fallback")

resilient_chain = RunnableLambda(primary).with_fallbacks(
    [RunnableLambda(fallback)],                    # Primary 실패 시 시도할 대체 Runnable 목록
    exceptions_to_handle=(PrimaryUnavailable,),    # Fallback 전환을 허용할 예외
)
```

- Fallback은 Primary가 만들었을 법한 상세 답을 **추측하지 않습니다.** 좋은 기능 저하 안내 = ① 지금 상세 기능을 쓸 수 없다는 사실 ② 잠시 후 재시도 같은 다음 행동.
- Primary가 허용 예외로 실패하면 **원래 입력**이 Fallback에 전달됩니다.
- `exceptions_to_handle=(Exception,)`처럼 모든 오류를 받으면 입력·코드 오류까지 정상적인 기능 저하처럼 보입니다 → 구체 예외만.
- **Graceful degradation** = 장애를 숨기는 게 아니라, 쓸 수 있는 기능은 유지하되 줄어든 기능과 한계를 사용자에게 분명히 표시하는 것.

| 경로 | status | route | Primary 호출 | Fallback 호출 |
| --- | --- | --- | --- | --- |
| 정상 | ok | primary | 1 | 0 |
| 기능 저하 | degraded | fallback | 1 | 1 |
| 정책 밖 오류 | 결과 없음 | 결과 없음 | 1 | 0 |

완성 실습 출력:

```text
=== Primary 정상 ===       status=ok route=primary primary_calls=1 fallback_calls=0
=== Fallback 전환 ===      status=degraded route=fallback primary_calls=1 fallback_calls=1
=== 처리하지 않는 오류 === error=ValueError primary_calls=1 fallback_calls=0
```

| 자주 생기는 오해 | 바로잡기 |
| --- | --- |
| Retry와 Fallback은 같은 기능 | Retry는 같은 경로 다시, Fallback은 허용된 다른 경로 |
| Fallback은 다른 출력 타입이어야 함 | 같은 계약 + 상태 필드로 구분하는 편이 단순 |
| 모든 예외를 Fallback으로 보내면 안 멈춤 | 입력·코드 오류까지 숨김 → 구체 예외만 |
| Fallback 결과도 정상처럼 표시 | `status="degraded"`와 실제 `route` 표시 |
| Fallback은 근거 없이도 상세 답을 추측 | 기능 제한과 다음 행동을 안내 |

## 확인 문제

모두 API 없이 풀 수 있습니다. `from langchain_core.runnables import RunnableLambda`, 위 요약의 `TemporaryModelError`, `PrimaryUnavailable`, `UserAnswer`가 준비되어 있고, `with_retry`에는 항상 `wait_exponential_jitter=False`를 준다고 가정합니다. 각 문제 바로 아래에 정답과 해설이 있습니다. 먼저 풀어 본 뒤 확인하세요.

### 9-Q1. Retry할까, 멈출까? (9-1)

각 오류를 "제한된 Retry" 또는 "즉시 실패"로 분류하고 이유를 한 줄로 쓰세요.

1. 모델 서버가 순간적인 과부하로 응답하지 못했다.
2. 사용자가 공백만 입력했다.
3. 함수에 dict 대신 int를 넘겨 `TypeError`가 났다.
4. 네트워크 연결이 잠깐 끊겨 모델 연결에 실패했다.
5. Prompt 변수 이름 오타로 `KeyError`가 났다.

> 힌트: "같은 입력·같은 경로로 다시 하면 결과가 달라질 수 있나?"

<details>
<summary>정답 보기</summary>

1 Retry (잠시 뒤 처리될 가능성) · 2 즉시 실패 (같은 빈 입력은 반복해도 안 바뀜) · 3 즉시 실패 (코드·자료형 계약을 고쳐야 함) · 4 Retry (다음 호출에서 연결이 회복될 수 있음) · 5 즉시 실패 (코드 오류 — 몇 번을 다시 해도 같은 키가 없음).

</details>

### 9-Q2. 결과와 호출 횟수 (9-1)

`call_model`은 처음 `F`번 호출에서 `TemporaryModelError`를 내고 그다음부터 `"정상 응답"`을 반환합니다. `retry_if_exception_type=(TemporaryModelError,)`일 때 표를 채우세요.

| 경우 | 실패 횟수 F | `stop_after_attempt` | 결과 | 실제 호출 |
| --- | --- | --- | --- | --- |
| A | 0 | 3 | ? | ? |
| B | 2 | 3 | ? | ? |
| C | 2 | 2 | ? | ? |
| D | 5 | 4 | ? | ? |
| E | 항상 `ValueError` | 5 | ? | ? |

> 힌트: `stop_after_attempt`는 최초 호출을 포함한 전체 횟수입니다.

<details>
<summary>정답 보기</summary>

| 경우 | 결과 | 실제 호출 |
| --- | --- | --- |
| A | 성공 (`정상 응답`) | 1 |
| B | 성공 (세 번째에 회복) | 3 |
| C | `TemporaryModelError` 전달 (예산 소진) | 2 |
| D | `TemporaryModelError` 전달 (예산 소진) | 4 |
| E | `ValueError` 전달 (Retry 제외) | 1 |

E처럼 목록에 없는 예외는 `stop_after_attempt`가 아무리 커도 한 번만 실행됩니다.

</details>

### 9-Q3. 소진 결과 출력 (9-1)

```python
state = {"attempts": 0}
def always_fail(question: str) -> str:
    state["attempts"] += 1
    raise TemporaryModelError("계획된 지속 모델 오류입니다.")

step = RunnableLambda(always_fail).with_retry(
    retry_if_exception_type=(TemporaryModelError,),
    stop_after_attempt=3,
    wait_exponential_jitter=False,
)
try:
    step.invoke("Retry 소진을 확인해 주세요.")
    print("성공")
except TemporaryModelError as error:
    print(type(error).__name__, state["attempts"])
```

출력은? 그리고 `except` 안에서 `return ""`처럼 빈 문자열을 성공 결과로 돌려주면 안 되는 이유는?

> 힌트: 예산을 다 쓰면 마지막 오류가 호출자에게 전달됩니다.

<details>
<summary>정답 보기</summary>

`TemporaryModelError 3`. 최초 포함 3번 모두 실패하고 마지막 오류가 전달됩니다. 빈 문자열을 성공처럼 돌려주면 상위 코드가 **실패했다는 사실을 알 수 없어** Fallback이나 사용자 안내를 선택할 수 없습니다. 처리할 수 없는 실패는 호출자에게 전달합니다 (오해 6).

</details>

### 9-Q4. 버그 찾기 — Retry가 안 걸림 (9-1)

```python
model_step = RunnableLambda(call_model)          # 첫 호출에서 TemporaryModelError
retry_step = model_step.with_retry(
    retry_if_exception_type=(Exception,),
    stop_after_attempt=3,
    wait_exponential_jitter=False,
)
answer = model_step.invoke("질문")               # (가)
```

(1) (가)를 실행하면 어떻게 되나요? (2) `retry_if_exception_type=(Exception,)`의 문제점은?

> 힌트: `with_retry()`는 원래 Runnable을 바꾸지 않습니다.

<details>
<summary>정답 보기</summary>

(1) Retry 정책이 없는 **원래 `model_step`**을 실행했으므로 첫 `TemporaryModelError`가 그대로 올라와 호출 1번으로 끝납니다. `retry_step.invoke("질문")`으로 바꿔야 합니다. (2) 모든 예외를 다시 실행하므로 빈 질문(`ValueError`)이나 코드 오류(`TypeError`)도 3번씩 반복해 지연만 늘어납니다. 회복 가능성이 있는 **구체적인 예외**(`TemporaryModelError,`)만 지정합니다 (오해 2).

</details>

### 9-Q5. 상태를 공유하면? (9-1)

```python
state = {"attempts": 0}
def call_model(question: str) -> str:
    state["attempts"] += 1
    if state["attempts"] == 1:
        raise TemporaryModelError("첫 호출의 계획된 오류입니다.")
    return "정상 응답"

chain = RunnableLambda(call_model).with_retry(
    retry_if_exception_type=(TemporaryModelError,), stop_after_attempt=2, wait_exponential_jitter=False,
)
print(chain.invoke("첫 질문"), state["attempts"])
print(chain.invoke("두 번째 질문"), state["attempts"])
```

출력은? 두 번째 실행도 "첫 호출 실패 → 두 번째 성공"을 재현하려면 어떻게 해야 하나요?

> 힌트: 두 번째 invoke가 시작될 때 `attempts`는 이미 2입니다.

<details>
<summary>정답 보기</summary>

```text
정상 응답 2
정상 응답 3
```

두 실행이 같은 `state`를 공유해서, 두 번째 실행은 `attempts`가 3이 되어 **실패 없이 바로 성공**합니다. 실행마다 새 상태를 만드는 함수(`build_chain()` 안에서 `state = {"attempts": 0}`을 만들고 체인과 함께 반환)를 쓰면 각 체인의 호출 횟수가 각각 2가 됩니다.

</details>

### 9-Q6. 최대 HTTP 요청 수 (9-1)

모델 클라이언트는 한 번 실행될 때 "최초 요청 + 내부 Retry"를 합니다. 바깥에는 `with_retry(stop_after_attempt=N)`이 있습니다. 최악의 경우 HTTP 요청 수를 쓰세요.

1. 바깥 `N=2`, 내부 `max_retries=2`
2. 바깥 `N=3`, 내부 `max_retries=2`
3. 바깥 `N=3`, 내부 `max_retries=0`

> 힌트: 내부 한 번 실행 = 1 + `max_retries`번 요청. 바깥 시도마다 곱해집니다.

<details>
<summary>정답 보기</summary>

1 2 × (1+2) = **6회** · 2 3 × 3 = **9회** · 3 3 × 1 = **3회**. 두 계층을 모두 켜면 요청 수·지연·비용이 곱으로 늘어납니다. 바깥에서 정책을 관리할 때는 `max_retries=0`으로 내부를 끄고 한 계층만 시도 횟수의 주인으로 둡니다.

</details>

### 9-Q7. Retry를 어디에 붙일까? (9-1)

```text
입력 확인 → 문서 검색 → 모델 호출 → 결과 저장(DB) → 알림 메시지 전송
```

(1) Retry를 어느 단계에 붙여야 하나요? (2) 전체 체인에 `with_retry(stop_after_attempt=3)`을 붙이고 모델 호출이 두 번 실패했다면, 알림 메시지 전송은 몇 번 일어날 수 있나요? (마지막 시도에서 성공 가정) (3) `with_retry`를 붙이면 모델 호출 하나가 60초 넘게 멈추는 문제도 해결되나요?

> 힌트: 실패한 시도는 모델 호출에서 멈추므로 뒤 단계까지 가지 않습니다. 저장 뒤에서 실패하는 경우도 생각해 보세요.

<details>
<summary>정답 보기</summary>

(1) 실패 가능성이 있는 **모델 호출 단계에만**. (2) 이 경우는 실패한 두 시도가 모델 호출에서 멈추므로 알림은 1번이지만, 입력 확인과 **문서 검색은 3번 반복**됩니다. 저장이나 알림 뒤에서 오류가 나면 **저장·알림 같은 부작용이 두 번 이상** 실행될 수 있어 위험합니다. (3) 아닙니다. Retry는 실패한 호출을 다시 실행할 뿐이고, 한 호출이 기다릴 수 있는 시간은 모델 클라이언트의 `timeout`으로 따로 제한합니다.

</details>

### 9-Q8. Retry? Fallback? 즉시 실패? (9-2)

1. 첫 모델 호출이 일시 오류로 실패했다. 다시 하면 될 것 같다.
2. 상세 답변 모델이 계속 응답하지 않는다. 대신 "잠시 후 다시 시도해 주세요" 안내는 줄 수 있다.
3. 질문이 비어 있다.
4. Primary는 정상인데 비용을 아끼려고 더 저렴한 경로를 쓰고 싶다.

> 힌트: 4번은 Fallback의 정의에 맞을까요?

<details>
<summary>정답 보기</summary>

1 Retry · 2 Fallback (허용된 대체 경로, 기능 저하 안내) · 3 즉시 실패 (반복·대체해도 안 바뀜) · 4 **Fallback이 아닙니다.** Fallback은 Primary가 처리할 수 **없을 때만** 실행되는 경로이고, 정상 상태에서 경로를 고르는 것은 일반적인 분기입니다.

</details>

### 9-Q9. 세 모드의 출력 (9-2)

9-2 완성 실습처럼 `primary`는 `primary_mode`에 따라 동작하고(`"normal"`/`"unavailable"`/`"invalid"`), 체인은 아래와 같습니다. 각 모드에서 `{"question": "질문"}`을 넣었을 때 결과(`status`, `route` 또는 오류 이름)와 `primary_calls`, `fallback_calls`를 쓰세요.

```python
chain = RunnableLambda(primary).with_fallbacks(
    [RunnableLambda(fallback)], exceptions_to_handle=(PrimaryUnavailable,),
)
```

> 힌트: `ValueError`는 `exceptions_to_handle`에 없습니다.

<details>
<summary>정답 보기</summary>

| 모드 | 결과 | primary_calls | fallback_calls |
| --- | --- | --- | --- |
| `normal` | `status=ok route=primary` | 1 | 0 |
| `unavailable` | `status=degraded route=fallback` | 1 | 1 |
| `invalid` | `error=ValueError` (호출자에게 전달) | 1 | 0 |

두 성공 경로 모두 `UserAnswer`를 반환하지만 `status`와 `route`가 다릅니다. 정책 밖 `ValueError`는 Fallback으로 숨지 않습니다.

</details>

### 9-Q10. 모든 예외를 받으면? (9-2)

9-Q9의 체인을 `exceptions_to_handle=(Exception,)`으로 바꿨습니다.

1. `primary_mode="invalid"`, 질문 `"질문"` → 결과와 호출 횟수는?
2. `primary_mode="normal"`, 질문 `"   "`(공백) → 결과와 호출 횟수는?
3. 이 설정의 문제점은?

> 힌트: Fallback도 빈 질문을 검사합니다.

<details>
<summary>정답 보기</summary>

1. `status=degraded route=fallback`, primary 1 · fallback 1 — 코드/입력 오류인 `ValueError`가 **정상적인 기능 저하처럼 숨겨집니다.**
2. `error=ValueError`, primary 1 · fallback 1 — Primary의 `ValueError`가 Fallback으로 넘어갔지만 Fallback의 최소 입력 계약 검사가 빈 질문을 다시 `ValueError`로 거부합니다.
3. 입력·코드를 고쳐야 하는 오류까지 "잠시 후 다시 시도하세요"로 보여 원인을 찾기 어렵게 만듭니다. 대체 경로로 처리할 수 있는 **구체적인 예외만** 지정합니다 (오해 3).

</details>

### 9-Q11. Retry와 Fallback을 함께 (9-1 + 9-2)

Primary는 항상 `PrimaryUnavailable`을 냅니다.

```python
primary_step = RunnableLambda(primary).with_retry(
    retry_if_exception_type=(PrimaryUnavailable,), stop_after_attempt=2, wait_exponential_jitter=False,
)
chain = primary_step.with_fallbacks(
    [RunnableLambda(fallback)], exceptions_to_handle=(PrimaryUnavailable,),
)
result = chain.invoke({"question": "질문"})
```

`result.status`, `result.route`, `primary_calls`, `fallback_calls`는? Primary가 정상이면 호출 횟수는?

> 힌트: Retry 예산을 모두 쓴 뒤 마지막 오류가 with_fallbacks에 전달됩니다.

<details>
<summary>정답 보기</summary>

`status=degraded`, `route=fallback`, `primary_calls=2`, `fallback_calls=1`. Primary를 최대 2번 시도(Retry 소진) → 마지막 `PrimaryUnavailable`이 허용 예외라 Fallback 1번 실행. Primary가 정상이면 `status=ok route=primary`, primary 1 · fallback 0입니다. 실제 모델이라면 여기에 내부 Retry까지 곱해질 수 있으니, Fallback 전 최대 요청 수를 한곳에서 계산합니다.

</details>

### 9-Q12. 출력 계약과 개념 O/X (9-2)

(1) Fallback이 `UserAnswer` 대신 문자열 `"잠시 후 다시 시도해 주세요."`를 반환하면 호출자에게 어떤 불편이 생기나요? (2) `UserAnswer(status="failed", answer="x", route="fallback")`을 만들면? (3) O/X:

1. `status="degraded"`는 결과를 전혀 만들지 못했다는 뜻이다.
2. Fallback은 Primary가 했을 법한 상세 답을 최대한 추측해 채운다.
3. Primary가 정상이어도 안전을 위해 Fallback을 항상 한 번 실행한다.
4. Primary가 허용 예외로 실패하면 원래 입력이 Fallback에 전달된다.

> 힌트: `status`는 `Literal["ok", "degraded"]`입니다.

<details>
<summary>정답 보기</summary>

(1) 경로마다 반환 타입이 달라 호출자가 `str`인지 `UserAnswer`인지 따로 처리해야 하고, 상태·경로 정보도 사라집니다. 같은 계약 + 상태 필드로 구분하는 편이 단순합니다. (2) `status`가 허용값이 아니라 `ValidationError`가 납니다 (5장의 `Literal` 검증과 같은 원리). (3) 1 X (대체 경로가 정상 실행됐지만 기능이 줄었다는 뜻) · 2 X (기능 제한과 다음 행동을 안내) · 3 X (Primary가 처리할 수 없을 때만) · 4 O

</details>
