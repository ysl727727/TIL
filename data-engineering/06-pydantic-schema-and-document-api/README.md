# Chapter 6: Pydantic 스키마와 문서 등록/조회 API

> 2026-09-29 기록(강의는 2026-09-23 수강). 6장 이론을 정리했습니다. 받을 JSON의 계약을 코드로 선언하고, 그 데이터를 저장·조회하는 API를 완성하는 단계입니다. 실습 파일은 아직 받지 못해 이론만 기록합니다.

## Learning Goals

- `BaseModel`과 `Field`로 요청 JSON의 타입·길이·기본값 계약을 선언한다.
- `default_factory=list`가 필요한 이유(가변 기본값 공유 문제)를 설명한다.
- `ConfigDict`로 문자열 자동 trim과 정의되지 않은 키 거부를 설정한다.
- `@field_validator`와 `@model_validator`의 적용 시점과 대상 차이를 구분한다.
- `ValidationError.errors()`의 `loc`·`type`을 읽어 어느 필드가 왜 실패했는지 찾는다.
- 요청 모델과 응답 모델을 분리하고 `response_model`로 응답 형태를 고정한다.
- 201 / 404 / 409 / 422를 상황에 맞게 구분해 반환한다.

## Practice Files

| Lesson | File | Practice status |
| --- | --- | --- |
| 6장 통합 | — | **자료 미수령** — 강의 교안만 받았고 실습 노트북이 없어 이론 정리만 진행 |

## Core Theory

### 1. 스키마는 "받을 것"을 미리 적어 두는 계약서

```python
from pydantic import BaseModel, Field, ConfigDict

class DocumentCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    document_id: str = Field(min_length=3, max_length=64, description="문서 고유 ID")
    content: str = Field(min_length=1, description="검색 대상 본문")
    tags: list[str] = Field(default_factory=list, max_length=10)
```

함수 안에서 `if not isinstance(...)`를 반복하는 대신 **필드 옆에 규칙을 적는다.** 이 선언이 곧 검증 코드이자 `/openapi.json` 문서가 된다.

### 2. `default_factory=list`를 쓰는 이유

`tags: list[str] = []`로 쓰면 그 리스트 객체 하나가 모든 인스턴스에 공유될 수 있다. `default_factory=list`는 **인스턴스를 만들 때마다 새 리스트를 생성**한다. 기본값이 가변 객체(list, dict, set)일 때는 항상 `default_factory`를 쓴다.

### 3. `max_length`가 가리키는 대상

| 필드 타입 | `max_length`의 의미 |
| --- | --- |
| `str` | 글자 수 |
| `list` | **원소 개수** |

`tags`에 `max_length=10`을 걸면 태그 문자열 길이가 아니라 태그가 10개를 넘는지를 본다. 태그 하나하나의 길이를 제한하려면 원소 타입 쪽에 조건을 건다.

### 4. `ConfigDict` 두 가지 설정

- `str_strip_whitespace=True`: 모든 문자열 필드의 앞뒤 공백을 자동으로 제거한다. `" doc-001 "`과 `"doc-001"`이 다른 ID로 저장되는 사고를 막는다.
- `extra="forbid"`: 모델에 없는 키가 들어오면 422로 거부한다. 기본값은 조용히 무시하는 쪽이라, 오타(`contnet`)가 들어와도 `content`가 비었다는 사실만 뒤늦게 드러난다.

### 5. 필드 검증과 모델 검증

```python
from pydantic import field_validator, model_validator

class DocumentCreate(BaseModel):
    ...

    @field_validator("document_id", mode="before")
    @classmethod
    def normalize_id(cls, value: str) -> str:
        return value.strip().lower()

    @model_validator(mode="after")
    def check_pair(self):
        if self.tags and not self.content:
            raise ValueError("태그만 있고 본문이 없습니다.")
        return self
```

| 구분 | 대상 | 시점 |
| --- | --- | --- |
| `@field_validator(..., mode="before")` | 필드 하나 | 타입 변환 **전** 원본 값 |
| `@model_validator(mode="after")` | 모델 전체 | 모든 필드가 채워진 **뒤** |

- `field_validator`에는 `@classmethod`를 함께 붙인다.
- `model_validator(mode="after")`는 반드시 `self`를 반환해야 한다 — 반환을 빠뜨리면 모델이 `None`이 된다.
- 여러 필드를 함께 봐야 하는 규칙은 `field_validator`로는 표현할 수 없다(그 시점에 다른 필드가 아직 없을 수 있다).

### 6. 검증 실패 읽기

```python
try:
    DocumentCreate(**payload)
except ValidationError as error:
    for item in error.errors():
        print(item["loc"], item["type"], item["msg"])
```

- `loc`: 어느 필드(중첩이면 경로)에서 실패했는지.
- `type`: `missing`, `string_too_short`, `extra_forbidden`처럼 실패 **종류**.

메시지 문장만 로그에 남기면 나중에 분류가 어렵다. `loc`과 `type`을 같이 남기면 어떤 오류가 자주 나는지 집계할 수 있다.

### 7. 요청 모델과 응답 모델을 나누는 이유

```python
class DocumentResponse(BaseModel):
    document_id: str
    content: str
    tags: list[str]

@app.post("/documents", response_model=DocumentResponse, status_code=201)
def create_document(payload: DocumentCreate):
    ...
```

받는 형태와 돌려주는 형태는 대체로 다르다 — 서버가 채우는 값(등록 시각, 내부 상태)은 요청에 없어야 하고, 내부에만 쓰는 값은 응답에 없어야 한다. `response_model`을 지정하면 함수가 무엇을 반환하든 **응답은 선언한 필드만** 나간다.

`model_dump()`로 모델을 dict로 바꿔 저장소에 넣고, 조회 시 다시 모델로 만들어 반환하면 저장·응답 경로가 같은 계약을 통과한다.

### 8. 상태 코드 구분

| 코드 | 상황 |
| --- | --- |
| 201 | 새 문서 등록 성공 |
| 404 | 조회한 `document_id`가 없음 |
| 409 | 이미 있는 `document_id`로 다시 등록 시도(충돌) |
| 422 | 요청 JSON이 스키마 계약을 어김 |

409를 200으로 처리하면 "새로 만들었는지 덮어썼는지"를 호출하는 쪽이 알 수 없다.

### 9. 메모리 저장소 두 개를 함께 관리하기

```python
DOCUMENTS: dict[str, dict] = {}     # document_id → 문서
SOURCE_INDEX: dict[str, list[str]] = {}  # source → document_id 목록
```

조회 조건이 늘면 보조 인덱스를 두게 되는데, **등록·삭제·초기화에서 두 dict를 항상 함께 갱신**해야 한다. 테스트에서 하나만 비우면 다음 테스트에서 "목록에는 있는데 본문이 없는" 상태가 만들어진다.

## Questions and Newly Learned Points

- 검증 코드를 함수 안에서 밖으로 꺼냈더니, 그 자체가 API 문서가 되는 것이 가장 큰 변화였다.
- `mode="before"`는 "아직 문자열일 때 손보는 자리", `mode="after"`는 "전부 채워진 뒤 관계를 보는 자리"로 기억하면 헷갈리지 않았다.
- `extra="forbid"`가 없으면 오타 키가 조용히 버려진다 — 입력이 틀렸는데 200이 나오는 상황이 제일 찾기 어렵다.
- 자주 하는 오해: "list 기본값은 `[]`로 충분하다"(공유 문제) / "`max_length`는 항상 글자 수다"(list는 원소 수) / "검증기는 함수만 있으면 된다"(`@classmethod` 필요) / "요청 모델 하나로 응답까지 쓰면 간단하다"(내부 값이 새어 나간다) / "없는 문서 등록 충돌은 400이면 된다"(409가 상황을 더 정확히 전달한다).
