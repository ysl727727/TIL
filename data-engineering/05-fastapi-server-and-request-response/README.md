# Chapter 5: FastAPI 서버 구조와 요청/응답 설계

> 2026-09-29 기록(강의는 2026-09-22 수강). 5장 이론을 정리했습니다. 지금까지는 남의 API를 호출하는 쪽이었다면, 이 장부터는 직접 API를 세우고 path·query·body 입력과 상태 코드 계약을 정하는 쪽으로 자리가 바뀝니다. 실습 파일은 아직 받지 못해 이론만 기록합니다.

## Learning Goals

- FastAPI(경로와 처리 함수 정의)와 Uvicorn(요청을 받아 실행하는 ASGI 서버)의 역할 차이를 설명한다.
- REST에서 경로는 자원, method는 동작이라는 원칙으로 엔드포인트 이름을 정한다.
- path parameter / query parameter / request body를 입력 성격에 따라 구분해 사용한다.
- `Query(...)`로 기본값과 허용 범위를 선언하고, 위반 시 422가 나오는 흐름을 이해한다.
- `HTTPException`으로 404를 명시적으로 반환하고, 404와 422의 의미 차이를 구분한다.
- `TestClient`로 서버를 띄우지 않고 요청·응답 계약을 검증한다.

## Practice Files

| Lesson | File | Practice status |
| --- | --- | --- |
| 5장 통합 | — | **자료 미수령** — 강의 교안만 받았고 실습 노트북이 없어 이론 정리만 진행 |

## Core Theory

### 1. FastAPI와 Uvicorn의 역할 분리

- **FastAPI**: 어떤 경로에 어떤 함수가 대응하는지, 입력이 무엇이고 응답이 무엇인지를 **선언**한다.
- **Uvicorn**: 실제 포트를 열고 HTTP 요청을 받아 그 함수를 **실행**한다.

```bash
uvicorn main:app --reload
```

`main`은 파일 이름, `app`은 그 안의 FastAPI 객체 이름이다. 코드에는 포트가 없고 실행 명령에 있다 — 그래서 같은 코드를 개발과 운영에서 다른 포트·설정으로 띄울 수 있다.

### 2. 경로는 자원, method는 동작

```text
GET  /documents        → 목록 조회
GET  /documents/{id}   → 한 건 조회
POST /documents        → 등록
```

`/getDocuments`, `/createDocument`처럼 **경로에 동사를 넣지 않는다.** 동사는 이미 method가 담당하고 있어 중복이며, 같은 자원이 여러 이름으로 흩어진다.

```python
@app.get("/documents/{document_id}")
def read_document(document_id: str):
    ...
```

데코레이터의 method와 함수가 하는 일이 어긋나면(예: `@app.get`인데 데이터를 저장) 문서와 실제 동작이 달라진다.

### 3. 입력 세 자리: path · query · body

| 자리 | 언제 쓰나 | 예 |
| --- | --- | --- |
| path | 자원을 **특정**하는 값 | `/documents/doc-news-001` |
| query | 결과를 **거르거나 자르는** 값 | `/documents?limit=30` |
| body | 새로 **보내는 구조화된 데이터** | `POST /documents` 의 JSON |

판단 기준은 "이 값이 없으면 어떤 자원인지 알 수 없는가"다. 없어도 자원이 정해지면 query, 정해지지 않으면 path다.

### 4. `Query`로 기본값과 범위 선언

```python
from fastapi import Query

@app.get("/documents")
def list_documents(limit: int = Query(default=30, ge=5, le=100)):
    ...
```

- `default=30`: 클라이언트가 보내지 않아도 동작한다.
- `ge=5`, `le=100`: 범위를 벗어나면 함수 본문이 실행되기 **전에** 422가 반환된다.

검증을 함수 안에서 `if`로 하면 규칙이 코드에 숨지만, `Query`에 선언하면 `/docs`와 `/openapi.json`에 그대로 노출되어 호출하는 쪽이 미리 알 수 있다.

### 5. 404와 422의 차이

| 상태 | 의미 | 발생 위치 |
| --- | --- | --- |
| 422 | 요청 **형식**이 계약을 어김 | FastAPI 검증 단계(함수 진입 전) |
| 404 | 형식은 맞지만 그 자원이 **없음** | 함수 본문에서 명시적으로 발생 |

```python
from fastapi import HTTPException

if document_id not in DOCUMENTS:
    raise HTTPException(status_code=404, detail="document not found")
```

없는 문서를 조회했을 때 빈 객체나 `200 + null`을 돌려주면 호출하는 쪽이 "없음"과 "비어 있음"을 구분하지 못한다.

### 6. 자동 문서와 계약 확인

- `/docs`: 브라우저에서 직접 호출해 볼 수 있는 화면.
- `/openapi.json`: 경로·입력·응답 스키마가 담긴 기계용 계약서.

둘 다 코드에서 자동 생성되므로 **타입 힌트와 `Query` 선언을 정확히 쓰는 것이 곧 문서를 쓰는 일**이다.

### 7. `TestClient`로 포트 없이 검증

```python
from fastapi.testclient import TestClient

client = TestClient(app)
response = client.get("/documents", params={"limit": 3})
assert response.status_code == 200
```

서버를 띄우지 않고 같은 앱 객체에 요청을 보낸다. 포트 충돌·실행 순서에 영향받지 않아 상태 코드와 응답 구조를 반복 확인하기에 적합하다.

### 8. `/health`를 먼저 만드는 이유

```python
@app.get("/health")
def health():
    return {"status": "ok"}
```

본 기능을 붙이기 전에 **서버가 떴는지**만 확인하는 최소 엔드포인트를 둔다. 문제가 생겼을 때 "서버가 안 뜬 것"과 "로직이 틀린 것"을 바로 갈라 볼 수 있다.

## Questions and Newly Learned Points

- 코드에 포트를 적지 않는 구조가 처음엔 낯설었는데, 실행 환경(개발/운영)과 코드를 분리하기 위한 것이었다.
- 경로에 동사를 넣고 싶어지는 순간은 대부분 **자원 이름을 아직 못 정한 경우**다 — 무엇에 대한 동작인지 먼저 정하면 경로가 자연스럽게 명사가 된다.
- 422는 "내가 만든 오류"가 아니라 FastAPI가 계약 위반을 감지해 자동으로 낸 것이고, 404는 내가 직접 올려야 하는 것이라는 점이 핵심 차이였다.
- 자주 하는 오해: "FastAPI가 서버다"(실행은 Uvicorn) / "검증은 함수 안에서 하면 된다"(문서에 안 나온다) / "없는 자원은 빈 목록을 주면 친절하다"(호출하는 쪽이 오류를 놓친다) / "테스트하려면 서버를 띄워야 한다"(`TestClient`로 충분하다).
