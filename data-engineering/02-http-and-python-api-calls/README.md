# Chapter 2: HTTP 요청/응답과 Python API 호출

> 2026-09-21 학습 기록. 2-1강(HTTP 요청/응답과 API 문서 읽기), 2-2강(Python API 호출과 인증/환경변수) 이론과 2장 통합 실습을 정리했습니다.

## Learning Goals

- HTTP 요청과 응답이 오가는 흐름을 설명하고 URL, endpoint, method, header, query parameter, request body를 구분한다.
- API 문서에서 한 번의 요청에 필요한 정보(기능·경로·인증·입력·출력·오류)를 찾는다.
- `200`, `400`, `401`, `404`, `429`, `500` 상태 코드의 기본 의미와 다음 행동을 설명한다.
- API 키를 코드에 직접 쓰지 않고 환경 변수에서 읽는다.
- HTTPX Client에 `headers`, `params`, `timeout`을 지정해 GET 요청을 작성한다.
- `raise_for_status()`가 필요한 이유를 설명하고 상태 → Content-Type → JSON 구조 순서로 응답을 검증한다.
- HTTPX의 `MockTransport`로 인터넷 없이 요청·응답을 재현한다.

## Practice Files

| Lesson | File | Practice status |
| --- | --- | --- |
| 2장 통합 | `01-public-api-request-and-validation.ipynb` | **완료** — `live` 모드로 JSONPlaceholder 공개 API에 실제 GET 요청, 상태 200·글 2건 확인. 로컬 `MockTransport` 인증 연습(`Bearer` 접두사 검사) 통과 |

실행 결과: `로컬 인증 연습: True` / `실행 모드: live` / `GET https://jsonplaceholder.typicode.com/posts?userId=1&_page=1&_limit=2` / `응답: 200 | 글 수: 2`.

## Core Theory

### 1. 클라이언트와 서버의 대화 (2-1강)

API 호출에는 **클라이언트**(필요한 데이터를 요청하는 프로그램)와 **서버**(요청을 해석하고 결과를 응답하는 프로그램)가 있다. HTTP는 요청 하나와 응답 하나가 짝을 이루는 왕복이다.

- 요청의 기본 요소: 어느 주소로 / 어떤 method로 / 어떤 조건과 인증 정보를 보낼 것인가 / 본문이 필요한가
- 응답의 기본 요소: 상태 코드는 무엇인가 / 응답 형식은 무엇인가 / 본문에 어떤 데이터가 있는가

서버가 JSON을 보냈다고 해서 그 내용이 항상 성공 데이터인 것은 아니다. **먼저 상태 코드를 확인하고 그다음 본문을 읽는다.**

### 2. URL과 endpoint 구분하기

```text
https://api.example.org/v1/books?q=python&page=1
  scheme    host        base   endpoint  query
```

**base URL**은 여러 endpoint가 공유하는 앞부분이고, **endpoint**는 특정 기능이나 자원을 나타내는 경로다. 문서에서 `{book_id}`처럼 중괄호로 표시된 값은 보통 path parameter이며 실제 요청에서는 구체적인 값으로 바뀐다. `/books`만으로는 어느 서버에 요청할지 알 수 없고, 반대로 문서의 예제 전체 URL을 무조건 복사하면 테스트 서버와 운영 서버를 혼동할 수 있으므로 base URL과 endpoint를 따로 확인한다.

### 3. method와 header / query / body

| method | 기본 의미 |
| --- | --- |
| GET | 자원 조회 |
| POST | 새 자원 생성 또는 작업 요청 |
| PUT | 자원 전체 교체 |
| PATCH | 자원 일부 수정 |
| DELETE | 자원 삭제 |

URL이 같아도 method가 다르면 다른 기능일 수 있으므로 method와 endpoint를 한 쌍으로 기록한다. 브라우저 주소창은 주로 GET을 보내므로 POST 요청을 주소창만으로 시험할 수 없다.

| 요소 | 대표 용도 | 문서에서 찾을 것 |
| --- | --- | --- |
| header | 인증, 원하는 형식 | 이름, 값 형식, 필수 여부 |
| query | 검색/필터/페이지 | 이름, 자료형, 기본값 |
| body | 생성/처리할 데이터 | JSON 구조, 필수 필드 |

세 요소 모두 서버에 정보를 보내지만 위치와 역할이 다르며 서로 바꿔 넣을 수 없다. 인증 헤더의 원문은 로그에 출력하지 않는다.

### 4. 응답의 세 가지 확인 지점

**① 상태 코드 → ② Content-Type → ③ 응답 본문** 순서로 확인한다. JSON을 기대했는데 HTML이 왔다면 오류 안내 페이지일 수 있다. 성공 예제에서 최상위가 객체인지 배열인지 확인하고, 객체라면 필요한 배열이 `items`, `data`, `results` 중 어디에 있는지 확인한다. 오류 응답도 JSON일 수 있으므로(`{"detail": "invalid api key"}`) **JSON 파싱 성공만으로 API 호출 성공이라고 결론 내리지 않는다.**

| 코드 | 기본 의미 | 먼저 할 일 |
| --- | --- | --- |
| 200 / 201 | 성공 / 생성 성공 | 응답 형식과 본문 확인 |
| 400 | 잘못된 요청 | 파라미터 이름·자료형 확인 |
| 401 | 인증 필요 또는 실패 | 키 전달 위치/값 확인 |
| 403 | 이해했지만 허용되지 않음 | 권한·정책 확인 |
| 404 | 자원 또는 경로 없음 | endpoint·식별자 확인 |
| 429 | 너무 많은 요청 | 안내에 따라 대기 후 재시도 |
| 500 | 서버 내부 오류 | 요청을 기록하고 제공자 상태 확인 |

### 5. API 문서에서 여섯 가지 찾기

코드를 쓰기 전에 문서에서 먼저 답할 질문: ① 무엇을 하는가 ② 어디로, 어떻게(base URL·endpoint·method) ③ 어떻게 인증하는가 ④ 무엇을 입력하는가(query/path/header/body 구분) ⑤ 무엇이 돌아오는가(상태 코드·Content-Type·필요한 배열 위치) ⑥ 어떻게 실패하는가(401/403, 429와 500 구분). 한 칸이라도 확인되지 않았다면 구현 전에 '미확인'으로 표시한다.

예제 코드부터 복사하면 어떤 값이 필수인지 이해하지 못한 채 실행할 수 있다.

### 6. API 키를 환경 변수로 분리하기 (2-2강)

API 키는 호출 주체와 사용량을 식별하는 비밀값일 수 있다. 코드에 직접 쓰면 Git 이력, 공유 노트북, 화면 캡처에 남을 수 있다.

```python
def load_api_key(variable_name: str = "COURSE_API_KEY") -> str:
    raw_value = os.getenv(variable_name)
    if raw_value is None or not raw_value.strip():
        raise RuntimeError(f"{variable_name} 환경 변수를 설정하세요.")
    return raw_value.strip()
```

`os.getenv()`는 환경 변수가 없으면 `None`을 반환하며, 공백만 있는 값도 유효한 키로 보내지 않도록 `strip()`으로 확인한다. 노트북에서는 `getpass`로 화면에 표시하지 않고 입력받을 수 있고, 운영 환경에서는 플랫폼의 secret 관리 기능을 우선 사용한다. **키를 로그나 오류 메시지에 출력하지 않는다.**

### 7. HTTPX Client와 요청 구성

```python
headers = {"X-API-Key": api_key, "Accept": "application/json"}
params = {"q": "데이터", "limit": 2}

with httpx.Client(base_url="https://api.example.org/v1", timeout=5.0) as client:
    response = client.get("/news", headers=headers, params=params)
```

Client를 쓰는 이유: 공통 base URL을 한곳에 둘 수 있고, 여러 요청에서 연결을 재사용할 수 있으며, 공통 header와 timeout 설정을 관리하기 쉽고, `with`로 자원 종료 시점을 분명히 할 수 있다. HTTPX가 공백과 한글을 URL에 맞게 인코딩하므로 `?q=...&limit=...` 문자열을 직접 만들 필요가 없다.

인증 헤더 이름은 API 문서의 표기를 그대로 따른다 — `X-API-Key`, `Authorization: Bearer ...`, `serviceKey` query parameter, OAuth 토큰 등 방식이 다르므로 한 API의 방식을 다른 API에 복사하지 않는다.

### 8. timeout과 raise_for_status()

timeout은 "몇 초 안에 전체 작업이 반드시 끝난다"는 보장이 아니라, 각 네트워크 단계의 무기한 대기를 막는 기본 설정이다.

`raise_for_status()`를 호출하지 않으면 4xx·5xx 오류 응답의 JSON을 정상 데이터로 처리할 수 있다. 상태 확인을 JSON 해석보다 먼저 두는 이유다.

```python
payload = response.json()
items = payload.get("items")          # 키가 없으면 KeyError 대신 None
if not isinstance(items, list):       # 원하는 형식인지 검사
    raise ValueError("응답의 items는 배열이어야 합니다.")
```

`payload["items"]`는 키가 없으면 곧바로 `KeyError`를 내지만, `.get()`으로 꺼낸 뒤 `isinstance`로 검사하면 오류 원인을 더 구체적으로 설명할 수 있다. 응답 필드 이름은 API마다 다르므로(`items`, `data`, `results`, `documents`) 문서의 성공 응답 예제에서 실제 위치를 확인한다.

### 9. 실패 위치를 나누어 이해하기

**200 OK만으로는 충분하지 않다** — 설정·연결·HTTP·형식·데이터 계약 5단계를 모두 통과해야 안전하게 사용할 수 있다.

| 실패 위치 | 예시 | 먼저 확인할 것 |
| --- | --- | --- |
| 설정 | API 키 환경 변수 없음 | 변수 이름과 값 |
| 연결 | 서버에 연결할 수 없음 | URL, 네트워크, timeout |
| HTTP 상태 | 401, 404, 429, 500 | 상태 코드와 오류 본문 |
| JSON 파싱 | HTML이 돌아옴 | Content-Type과 본문 |
| 데이터 구조 | `items`가 없음 | API 문서와 응답 버전 |

### 10. 오프라인 fixture로 재현하기

실제 API는 네트워크·키·제공자 상태에 따라 결과가 달라지므로, HTTPX의 `MockTransport`로 같은 요청과 응답을 로컬에서 재현한다. 핸들러 함수가 서버로 연결하는 대신 메모리 안에서 HTTP 응답을 돌려준다.

이번 실습에서는 이 방식으로 ① 로컬 인증 연습(헤더의 `Bearer ` 접두사 확인)과 ② `sample` 모드의 고정 응답 두 건을 처리했다. **로컬 인증 헤더는 공개 API 클라이언트에 전달하지 않는다** — 인증 연습이 외부로 키를 보내는 동작으로 이어지지 않도록 클라이언트를 분리한다. 출력의 `True`는 헤더 형식이 확인되었다는 뜻이며 실제 계정 인증 성공을 뜻하지 않는다.

`live` 요청이나 응답 확인에 실패하면 제공 샘플로 전환해 `sample_fallback`을 표시한다. 샘플에 붙어 있는 요청 URL은 HTTPX가 만든 요청 정보이며 그 주소로 네트워크 연결을 했다는 증거가 아니다.

## Questions and Newly Learned Points

- `request_posts`(요청+상태 확인, 응답 객체 반환)와 `read_posts`(본문 해석, 리스트 반환)는 반환값의 종류가 다르다 — 두 함수가 모두 리스트를 반환한다고 생각하면 뒤에서 `.headers`나 `.json()`을 쓸 때 오류가 난다.
- 404인 JSON 응답은 상태 검사에서 멈추고, 200이지만 본문이 객체 하나인 응답은 상태·JSON 문법 검사를 통과한 뒤 리스트 검사에서 멈춘다 — 같은 "실패"라도 멈추는 위치가 다르다.
- `.issubset()`으로 필수 키를 검사하면 `userId` 같은 추가 키가 있어도 허용된다. 딕셔너리인지 먼저 확인하면 글 대신 문자열이나 숫자가 들어온 경우도 구조 오류로 다룰 수 있다.
- 구조 검사를 통과했다고 데이터가 질문의 근거로 적합하다는 뜻은 아니다 — 빈 제목, 내용의 사실 여부, 중복은 별도 판단이 필요하다.
- `os.getenv`의 기본값을 빈 문자열로 두면 변수가 없을 때도 `.strip()`을 쓸 수 있고, 공백만 있던 값은 빈 문자열이 되어 요청 전에 `RuntimeError`로 멈출 수 있다.
- 자주 하는 오해: "환경 변수를 쓰면 키를 출력해도 괜찮다"(로그와 화면 출력도 유출 경로) / "timeout은 인터넷이 느릴 때만 필요하다"(로컬 네트워크와 서버도 멈출 수 있다) / "200이면 원하는 필드가 반드시 있다"(API 버전이나 응답 조건에 따라 구조가 다를 수 있다).

## Environment

```bash
pip install -r requirements.txt
```
