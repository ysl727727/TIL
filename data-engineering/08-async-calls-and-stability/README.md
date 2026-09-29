# Chapter 8: 비동기 호출과 안정성

> 2026-09-29 기록(강의는 2026-09-23 수강). 8-1강(비동기 처리와 `httpx.AsyncClient`), 8-2강(Timeout/retry/rate limit/middleware 통합) 이론을 정리했습니다. 대기 시간이 겹치는 비동기 호출에 timeout·제한된 재시도·502 변환·요청 로그를 더해 "느려도 예측 가능한" API로 만드는 단계입니다. 실습 파일은 아직 받지 못해 이론만 기록합니다.

## Learning Goals

- `async def` / `await` / `asyncio.run()`의 역할과, 비동기가 빨라지는 조건(대기 시간이 겹칠 때)을 설명한다.
- `httpx.AsyncClient`를 `async with`로 한 번만 만들어 공유한다.
- `asyncio.gather()`의 결과가 완료 순서가 아니라 **입력 순서**를 따른다는 점을 확인한다.
- `timeout` 값이 전체 시간이 아니라 단계별 최대 시간이라는 점을 구분한다.
- 재시도를 timeout과 5xx로만 제한하고, 4xx(429 포함)는 즉시 실패시킨다.
- 외부 실패를 우리 API의 502로 바꾸고, middleware로 method·path·status만 기록한다.

## Practice Files

| Lesson | File | Practice status |
| --- | --- | --- |
| 8장 통합 | — | **자료 미수령** — 강의 교안만 받았고 실습 노트북이 없어 이론 정리만 진행 |

## Core Theory

### 1. 비동기가 빨라지는 조건

비동기는 CPU 계산을 빠르게 만들지 않는다. **기다리는 시간이 있을 때만** 이득이 있다 — 외부 API 응답을 기다리는 동안 다른 요청을 보내 대기 구간을 겹치는 것이다.

```python
async def ask(client, question):
    response = await client.post(URL, json={"question": question})
    return response.json()          # json()은 await 하지 않는다

async def main():
    async with httpx.AsyncClient(timeout=2.0) as client:
        jobs = [ask(client, q) for q in questions]
        results = await asyncio.gather(*jobs)

asyncio.run(main())
```

- `await`는 **기다림이 있는 호출**에만 붙인다. `response.json()`은 이미 받은 바이트를 파싱하는 동기 작업이라 `await`하면 오류가 난다.
- `asyncio.run()`은 프로그램 진입점에서 한 번만 호출한다.

### 2. Client는 한 번만 만들어 공유한다

```python
async with httpx.AsyncClient(timeout=2.0) as client:
    ...
```

요청마다 새 client를 만들면 연결 재사용이 되지 않아 매번 새로 연결을 맺는다. `async with`로 감싸면 블록을 벗어날 때 연결이 정리된다.

### 3. `gather`는 입력 순서를 지킨다

```python
results = await asyncio.gather(*jobs)
```

세 요청이 각각 다른 시각에 끝나도 `results[0]`은 언제나 `jobs[0]`의 결과다. **완료 순서와 결과 순서를 혼동하지 않는 것**이 질문 목록과 답변 목록을 짝지을 때 중요하다.

### 4. `timeout`의 범위

```python
httpx.AsyncClient(timeout=2.0)
```

여기서 2초는 전체 소요 시간이 아니라 **connect / read / write / pool 각 단계에 적용되는 최대 시간**이다. 그래서 실제 한 요청은 2초보다 오래 걸릴 수 있다. "전체 2초 안에 끝난다"고 가정하면 예상과 다른 지연이 생긴다.

timeout을 아예 주지 않으면 응답이 없는 요청이 무한정 매달려 서버 자원을 잡는다 — 사용자를 마주하는 경로에는 반드시 명시한다.

### 5. 제한된 재시도

```python
for attempt in range(2):     # 최초 1회 + 재시도 1회 = 최대 2회 호출
    try:
        response = await client.post(URL, json=payload)
        if response.status_code >= 500:
            raise ExternalServiceError("server error")
        return response
    except httpx.TimeoutException:
        if attempt == 1:
            raise ExternalServiceError("timeout")
    except httpx.RequestError:
        raise ExternalServiceError("request error")
```

- `range(2)`는 **호출 2회**를 뜻한다(재시도 2회가 아니다). 이 숫자를 잘못 읽으면 실제 호출 횟수가 생각보다 늘어난다.
- 재시도 대상은 **timeout과 5xx**뿐이다. 4xx는 요청 자체가 잘못된 것이라 다시 보내도 같은 결과다.
- **429도 즉시 실패시킨다.** 기다림 없이 다시 보내면 호출 한도를 더 소진해 상황이 나빠진다(대기 정책은 상위 과정에서 다룬다).
- `httpx.TimeoutException`은 `httpx.RequestError`의 하위 클래스이므로 **timeout을 먼저 잡아야** 한다. 순서가 바뀌면 timeout이 일반 요청 오류로 처리돼 재시도가 사라진다.

### 6. 예외를 우리 API의 502로

```python
class ExternalServiceError(RuntimeError):
    pass

try:
    data = await call_llm(payload)
except ExternalServiceError as error:
    raise HTTPException(status_code=502, detail="upstream failed") from error
```

호출 계층에서는 `httpx` 예외를 그대로 올려 보내지 않고 **우리 도메인 예외 하나로 좁힌 뒤** 경계에서 502로 바꾼다. 이렇게 하면 라우터 코드가 외부 라이브러리 예외 종류를 알 필요가 없다.

응답 본문에 외부 오류 원문을 그대로 넣지 않는다 — 내부 URL이나 키 일부가 새어 나갈 수 있다. 자세한 내용은 로그로만 남긴다.

### 7. 최소 요청 로그 middleware

```python
@app.middleware("http")
async def log_requests(request, call_next):
    response = await call_next(request)
    logger.info("%s %s %s", request.method, request.url.path, response.status_code)
    return response
```

- `call_next(request)`를 호출해야 실제 처리가 진행되고, 그 반환값을 **반드시 돌려주어야** 응답이 클라이언트에 전달된다.
- 기록하는 것은 method·path·status **세 가지뿐**이다. 요청 본문이나 header 전체를 남기면 질문 내용과 인증 값이 로그에 쌓인다.
- 쿼리 문자열까지 남기면 query에 들어간 값이 함께 기록되므로 `url.path`만 쓴다.

## Questions and Newly Learned Points

- `await`를 "비동기 함수 앞에 붙이는 것"으로 외우면 `response.json()`에서 걸린다 — **기다림이 있는지**가 기준이다.
- `except`의 순서가 동작을 바꾼다는 점(하위 클래스를 먼저)이 이 장에서 가장 실수하기 쉬운 부분이었다.
- `range(2)`가 "2번 재시도"가 아니라 "총 2회 호출"이라는 것 — 재시도 정책은 숫자보다 **최대 호출 횟수**로 말하는 편이 안전하다.
- middleware에서 `return response`를 빠뜨리면 로그는 남는데 응답이 사라진다.
- 자주 하는 오해: "비동기로 바꾸면 무조건 빨라진다"(대기가 없으면 그대로다) / "timeout 2초면 2초 안에 끝난다"(단계별 값이다) / "429도 재시도 대상이다"(한도를 더 쓴다) / "외부 오류는 그대로 보여 주는 게 친절하다"(내부 정보가 샌다).
