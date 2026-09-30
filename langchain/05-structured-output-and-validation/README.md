# 5장. 구조화 출력 — 스키마 · 검증 · 복구

> 2026-09-30 학습 기록. 모델 답변을 Pydantic 객체로 받고, 문자열을 스키마로 검증해 실패 원인을 읽고, 실패하면 한 번만 고쳐 달라고 요청한 뒤 같은 규칙으로 다시 검증하는 흐름을 정리했습니다.

## 학습 목표

- `BaseModel`·`Field`·`Literal`로 스키마를 정의하고 `with_structured_output()`으로 객체를 받는다.
- `PydanticOutputParser.parse()`가 JSON 해석 → 스키마 검증 두 단계로 동작함을 설명한다.
- 호출한 함수에 따라 `OutputParserException`과 `ValidationError`를 구분해 잡는다.
- 검증 실패 시 수정 요청을 **최대 1회**만 보내고, 같은 Parser로 재검증한다.
- 스키마 통과는 형식만 보장하고 내용의 정확성은 보장하지 않는다는 점을 구분한다.

## 실습 파일

| 강 | 주제 | 실습 상태 |
| --- | --- | --- |
| 5-1 | Pydantic schema와 structured output | 📘 이론 정리 |
| 5-2 | Parser 기반 검증과 validation error | 📘 이론 정리 |
| 5-3 | 출력 복구와 retry 연결 | 📘 이론 정리 |

실습 노트북은 이번 기록에 포함하지 않았습니다. 아래 확인 문제는 API 없이 풀 수 있도록 만든 복습용 문제입니다.

## 전체 흐름

1. **5-1 받기** — 스키마를 정의하고 `model.with_structured_output(스키마)`로 모델이 곧장 `QuestionClassification` 객체를 돌려주게 함. `prompt | structured_model`로 체인 연결.
2. **5-2 검증하기** — 이미 있는 JSON **문자열**을 `PydanticOutputParser`로 객체로 바꿈. 실패 유형(JSON 문법 / 필수 필드 누락 / 허용값 위반)과 예외 종류(`OutputParserException` vs `ValidationError`)를 구분하고, 오류의 `loc`·`type`만 짧게 읽음.
3. **5-3 복구하기** — 검증 실패한 문자열은 쓰지 않음. 원래 질문 + 실패한 출력 + 형식 안내를 담은 수정 Prompt로 **한 번만** 다시 받고, **같은 Parser**로 재검증. 또 실패하면 `None`으로 최종 실패.

```text
5-1  질문 dict → Prompt → structured_model (with_structured_output) → QuestionClassification 객체

5-2  JSON 문자열 → parser.parse ─┬─ ① JSON 해석 실패 (쉼표·따옴표·중괄호)      ─┐
                                ├─ ② 스키마 검증 실패 (missing, literal_error) ─┴→ OutputParserException
                                └─ 둘 다 통과 → QuestionClassification 객체

5-3  첫 try_parse ─ 성공 → 그대로 사용 (수정 요청 없음)
          │
          └ 실패(None) → repair_prompt | model | StrOutputParser  (최대 1회, str 반환)
                               │
                               └→ 같은 parser로 try_parse ─ 성공 → 객체
                                                          └ 실패 → None → "최종 실패" (추가 요청 없음)
```

4장 → 5장 연결고리: 4장까지 결과는 `str`이나 `dict`였습니다. 5장은 결과를 **타입이 보장된 객체**로 만들어, 뒤에서 `if result.category == "오류":` 같은 분기를 안전하게 쓸 수 있게 합니다. 3-3에서 배운 "자료형 먼저 확인" 습관은 5장에서 "검증 통과 여부 먼저 확인"으로 이어집니다.

## 핵심 이론

이번 장 내내 쓰는 스키마입니다.

```python
from typing import Literal
from pydantic import BaseModel, Field

class QuestionClassification(BaseModel):
    category: Literal["개념", "코드", "오류"] = Field(description="질문의 가장 알맞은 분류")
    summary: str = Field(description="질문의 핵심을 정리한 한 문장")          # 필수
    needs_code: bool = Field(default=False, description="코드 예시가 필요한지 여부")  # 기본값 있음
```

### 1. Pydantic schema와 structured output (5-1강)

| 구분 | 자연어 문자열 | 구조화 출력 |
| --- | --- | --- |
| 대표 자료형 | `str` | Pydantic 객체 |
| 값을 읽는 방법 | 문장을 다시 해석 | 정해진 필드에 접근 |
| 필드 누락 확인 | 직접 확인해야 함 | 스키마가 검증 |
| 허용값 제한 | 별도 코드 필요 | `Literal`로 표현 |
| 적합한 상황 | 설명문을 그대로 보여 줄 때 | 분류, 저장, 조건 분기 |

| 도구 | 하는 일 |
| --- | --- |
| `BaseModel` | 필드를 읽고 규칙에 맞는 객체를 만듦 (상속해서 스키마 클래스 작성) |
| `Field` | 필드 설명·기본값 기록 |
| `Literal[...]` | 받을 수 있는 값을 정해진 목록으로 제한 |

- 기본값이 없는 `category`, `summary`는 **필수**, `needs_code`는 생략하면 `False`.
- 허용 목록 밖의 값(`category="기타"`)이나 필수 필드 누락은 객체를 만들 때 `ValidationError`.
- 필드는 **점 표기법**으로 읽습니다: `result.category` (O), `result["category"]` (X).
- dict가 필요하면 `result.model_dump()` → `{'category': ..., 'summary': ..., 'needs_code': ...}`.
- `structured_model = model.with_structured_output(QuestionClassification)` — 별도 API가 아니라 같은 ChatModel에 출력 스키마를 알려 준 실행 객체. 이때는 세 필드를 모두 응답에 포함하도록 요청합니다.
- 체인: `chain = prompt | structured_model` → `chain.invoke({"question": ...})` → `QuestionClassification` 객체.
- Prompt는 **무엇을** 분류할지, 스키마는 **어떤 모양으로** 받을지 정합니다.
- 주의: 스키마 통과 = **형식**이 맞음. **내용**(분류가 맞는지)까지 보장하지 않습니다.

| 자주 나는 오류 | 원인 → 해결 |
| --- | --- |
| `OPENAI_API_KEY`가 없음 | `.env` 확인 (로컬 객체 부분은 키 없이도 실행됨) |
| `ModuleNotFoundError: pydantic` | uv 프로젝트 `.venv` 선택, `uv sync --frozen` |
| `ValidationError` | 필수 필드 누락 / `category` 허용값 밖 → 스키마와 필드 이름 비교 |
| 필드를 못 읽음 | dict처럼 읽음 → 점 표기법 또는 `model_dump()` |
| `KeyError: 'question'` | Prompt 변수와 invoke 키 불일치 |
| 매번 summary 문장이 다름 | 정상. 클래스·필드 이름·타입으로 확인 |

### 2. Parser 기반 검증과 validation error (5-2강)

```python
from langchain_core.output_parsers import PydanticOutputParser
parser = PydanticOutputParser(pydantic_object=QuestionClassification)   # 객체 말고 "클래스"를 전달
parser.get_format_instructions()   # 모델에게 줄 형식 안내 (str, 모델 호출 없음)
result = parser.parse('{"category":"개념","summary":"LCEL의 의미를 묻는 질문입니다.","needs_code":false}')
# → QuestionClassification 객체, result.category == '개념'
```

`parser.parse()`의 두 단계: **① JSON 문법 해석 → ② Pydantic 스키마 검증 → 객체 반환**. 둘 중 하나라도 실패하면 객체가 없습니다.

| 실패 유형 | 예시 | 실패 단계 | 첫 오류 (`loc` / `type`) |
| --- | --- | --- | --- |
| JSON 문법 오류 | `'{"category":"개념" "summary":"..."}'` (쉼표 누락) | ① | - |
| 필수 필드 누락 | `'{"category":"개념","needs_code":false}'` | ② | `summary` / `missing` |
| `Literal` 허용값 위반 | `'{"category":"기타", ...}'` | ② | `category` / `literal_error` |
| 불리언 타입 문제 | `needs_code`에 잘못된 값 | ② | `needs_code` / 타입 관련 오류 |

`needs_code`를 생략한 JSON은 성공하고 기본값 `False`가 들어갑니다.

**어떤 함수를 호출했는지**에 따라 잡는 예외가 다릅니다.

| 호출한 코드 | 잡는 예외 |
| --- | --- |
| `parser.parse(JSON_문자열)` | `OutputParserException` (`langchain_core.exceptions`) |
| `QuestionClassification.model_validate(딕셔너리)` | `ValidationError` (`pydantic`) |

Parser도 내부에서 Pydantic을 쓰지만, 호출한 쪽에는 LangChain의 Parser 예외로 전달됩니다.

**짧게 오류 읽기** — 긴 전문 대신 첫 오류의 위치와 유형만:

```python
try:
    QuestionClassification.model_validate(json.loads('{"category":"개념","needs_code":false}'))
except ValidationError as error:
    first_error = error.errors(include_input=False)[0]
    field_path = ".".join(str(part) for part in first_error["loc"])
    print(f"필드={field_path}")          # 필드=summary
    print(f"유형={first_error['type']}")  # 유형=missing
```

읽는 순서: **필드 위치 먼저, 그다음 유형.** 입력을 고칠 때도 JSON 문법 → 필수 필드 → 허용값 순서로 하나씩 확인합니다. 실패한 값을 빈 객체나 임의 기본값으로 바꾸지 않습니다.

| 자주 나는 오류 | 원인 → 해결 |
| --- | --- |
| 모든 실패를 `ValidationError`로 잡음 | `parser.parse()`를 불렀다면 `OutputParserException` |
| JSON에 `False` 사용 | JSON은 소문자 `false`/`true`, Python dict는 `False`/`True` |
| JSON 키·값에 작은따옴표 | 표준 JSON은 큰따옴표. 바깥 Python 문자열 따옴표와 구분 |
| 실패한 결과를 계속 사용 | `except` 안에서 `return`하거나 성공/실패 분기 분리 |
| 유형만 보고 입력을 안 봄 | 문법 → 필수 필드 → 허용값 순으로 한 번에 하나씩 |

### 3. 출력 복구와 retry 연결 (5-3강)

**원칙 6가지**: ① 첫 검증에 실패한 문자열은 쓰지 않는다 ② 원래 질문과 실패한 출력을 수정 Prompt에 넣는다 ③ Parser의 형식 안내를 준다 ④ 수정 요청은 한 번만 ⑤ 수정 결과도 같은 Parser로 재검증 ⑥ 재검증 실패면 최종 실패로 종료.

```python
def try_parse(parser, raw_output: str) -> QuestionClassification | None:
    try:
        return parser.parse(raw_output)
    except OutputParserException:
        return None                     # 고치지 않고 "검증된 객체 없음"만 알림
```

첫 출력이 이미 정상이면 수정 요청을 **보내지 않습니다** (불필요한 모델 호출 방지).

수정 Prompt의 입력 3개:

| 입력 변수 | 역할 |
| --- | --- |
| `format_instructions` | Parser가 요구하는 필드와 형식 (`parser.get_format_instructions()`) |
| `question` | 구조화하려던 원래 질문 (의미 유지) |
| `broken_output` | 첫 검증에 실패한 문자열 (고칠 대상) |

```python
repair_prompt = ChatPromptTemplate.from_messages([
    ("system", "다음 출력을 설명 없이 올바른 JSON 객체로 다시 작성하세요.\n요구 형식:\n{format_instructions}"),
    ("human", "질문:{question}\n검증에 실패한 출력:{broken_output}"),
])
repair_chain = repair_prompt | model | StrOutputParser()   # 결과는 아직 str!
MAX_REPAIR_ATTEMPTS = 1
```

- `repair_chain` 결과는 `QuestionClassification`이 아니라 **문자열** → 반드시 같은 `try_parse(parser, ...)`로 재검증.
- 두 Parser의 역할 분리: `StrOutputParser`는 `AIMessage` → `str`(본문 꺼내기), `PydanticOutputParser`는 JSON `str` → 객체(필드·값 검증).
- 복구 횟수에 상한이 없으면 끝나는 시점을 알 수 없고 API 비용이 계속 늘어납니다. (네트워크 재시도·예외별 정책은 9장)
- 최종 결과는 `None` 여부를 **먼저** 확인한 뒤에만 필드에 접근합니다. 최종 실패는 "검증되지 않은 값을 쓰지 않고 분명한 실패 상태로 끝낸다"는 뜻입니다.
- 성공 여부는 모델이 "수정했습니다"라고 말하는지가 아니라 **Parser가 객체를 반환했는지**로 판단합니다.

| 실행 경우 | 출력 |
| --- | --- |
| 첫 검증 성공 | `[첫 검증] 성공 · 복구 요청 없음` |
| 실패 → 복구 성공 | `[첫 검증] 실패` → `[복구 1회] 성공` → 세 필드 출력 |
| 실패 → 복구도 실패 | `[첫 검증] 실패` → `[복구 1회] 실패` → `[최종 결과] 구조화 출력을 만들지 못했습니다.` |

| 자주 나는 오류 | 원인 → 해결 |
| --- | --- |
| 첫 검증이 성공해 복구 흐름이 안 보임 | `BROKEN_OUTPUT`을 수업 중엔 원본(잘못된 값) 그대로 유지 |
| 수정 Prompt에 형식 안내 없음 | `format_instructions`를 Prompt에 넣고 invoke 때 같은 키로 전달 |
| 수정 문자열을 바로 정상 결과로 사용 | `repair_chain` 결과는 str → 같은 Parser로 재검증 |
| 실패 뒤 `final_result.category` 접근 | `None` 먼저 확인 |
| 수정 요청이 여러 번 실행됨 | `MAX_REPAIR_ATTEMPTS = 1`, 함수를 바깥에서 반복 호출하지 않기 |
| 응답 문구로 성공 판단 | Parser가 객체를 돌려줬는지로 판단 |

## 확인 문제

모두 API 없이 풀 수 있습니다. 위의 `QuestionClassification` 스키마와 `parser = PydanticOutputParser(pydantic_object=QuestionClassification)`가 준비되어 있다고 가정합니다. 각 문제 바로 아래에 정답과 해설이 있습니다. 먼저 풀어 본 뒤 확인하세요.

### 5-Q1. 객체가 만들어질까? (5-1)

아래 네 줄을 각각 실행하면 객체가 만들어지나요, `ValidationError`가 나나요? 만들어지면 `needs_code` 값도, 실패하면 원인도 쓰세요.

```python
QuestionClassification(category="개념", summary="LCEL 질문")                      # (a)
QuestionClassification(category="기타", summary="분류 불가 질문")                  # (b)
QuestionClassification(category="코드")                                           # (c)
QuestionClassification(category="오류", summary="KeyError 질문", needs_code=True)  # (d)
```

> 힌트: 기본값이 있는 필드는 하나뿐이고, `Literal`의 허용 목록은 세 개입니다.

<details>
<summary>정답 보기</summary>

(a) 성공, `needs_code=False`(기본값). (b) `ValidationError` — `"기타"`는 `Literal["개념","코드","오류"]`에 없음. (c) `ValidationError` — 필수 `summary` 누락. (d) 성공, `needs_code=True`.

</details>

### 5-Q2. 필드 읽기 (5-1)

```python
result = QuestionClassification(category="코드", summary="예제 코드 요청", needs_code=True)
print(result["category"])        # (가)
print(result.model_dump())       # (나)
```

(가)는 왜 실패하나요? 올바르게 고치는 방법 두 가지를 쓰고, (나)의 출력을 쓰세요.

> 힌트: Pydantic 객체와 딕셔너리는 읽는 방법이 다릅니다.

<details>
<summary>정답 보기</summary>

(가) Pydantic 객체는 딕셔너리처럼 대괄호로 읽을 수 없어 `TypeError`(`'QuestionClassification' object is not subscriptable`)가 납니다. 고치기: `result.category` 또는 `result.model_dump()["category"]`. (나) `{'category': '코드', 'summary': '예제 코드 요청', 'needs_code': True}` — dict로 바뀌어 Python의 `True`로 보입니다.

</details>

### 5-Q3. 어느 단계에서 실패할까? (5-2)

각 문자열을 `parser.parse()`에 넣으면 성공/실패 중 무엇인가요? 실패라면 ① JSON 해석 단계인지 ② 스키마 검증 단계인지, 그리고 성공이라면 `needs_code` 값을 쓰세요.

```python
A = '{"category":"코드","summary":"예제 요청"}'
B = '{"category":"코드" "summary":"예제 요청"}'
C = '{"category":"기타","summary":"예제 요청","needs_code":false}'
D = '{"category":"오류","needs_code":true}'
```

> 힌트: JSON으로 읽을 수는 있지만 스키마를 못 지키는 경우가 두 개 있습니다.

<details>
<summary>정답 보기</summary>

| 문자열 | 결과 | 단계 / 값 |
| --- | --- | --- |
| A | 성공 | `needs_code=False` (생략 → 기본값) |
| B | 실패 | ① JSON 해석 (값 뒤 쉼표 누락) |
| C | 실패 | ② 스키마 검증 (`category` `literal_error`) |
| D | 실패 | ② 스키마 검증 (`summary` `missing`) |

C, D는 JSON으로는 읽히지만 스키마를 지키지 못합니다. "JSON이 맞다 ≠ 스키마가 맞다"의 예입니다.

</details>

### 5-Q4. 예외 잡기 (5-2)

아래 코드를 실행하면 `"실패 처리"`가 출력될까요, 프로그램이 Traceback으로 멈출까요? 이유와 고친 코드를 쓰세요.

```python
from pydantic import ValidationError
try:
    parser.parse('{"category":"개념"}')
except ValidationError:
    print("실패 처리")
```

> 힌트: 무엇을 호출했는지에 따라 올라오는 예외가 다릅니다.

<details>
<summary>정답 보기</summary>

프로그램이 멈춥니다. `parser.parse()`는 실패를 `OutputParserException`으로 올리므로 `except ValidationError`에 걸리지 않습니다.

```python
from langchain_core.exceptions import OutputParserException
try:
    parser.parse('{"category":"개념"}')
except OutputParserException:
    print("실패 처리")
```

`ValidationError`는 `QuestionClassification.model_validate(dict)`처럼 Pydantic을 **직접** 호출할 때 잡습니다.

</details>

### 5-Q5. 첫 오류 읽기 (5-2)

아래 세 dict를 각각 `QuestionClassification.model_validate()`로 검증했을 때, `error.errors(include_input=False)[0]`의 필드 위치와 유형을 쓰세요.

```python
{"category": "기타", "summary": "x"}   # (가)
{"category": "개념"}                    # (나)
{}                                     # (다)
```

> 힌트: (다)는 오류가 두 개입니다. 목록의 첫 항목은 스키마에 먼저 적힌 필드입니다.

<details>
<summary>정답 보기</summary>

(가) `category` / `literal_error` (나) `summary` / `missing` (다) `category` / `missing` — 오류는 `category`, `summary` 두 개이고 첫 항목은 먼저 정의된 `category`입니다.

</details>

### 5-Q6. 버그 찾기 — 수정 결과 사용 (5-3)

아래 코드의 문제 두 가지를 찾고 고치세요.

```python
repaired_output = repair_chain.invoke(repair_input)
print(repaired_output.category)

final_result = try_parse(parser, repaired_output)
print(final_result.summary)
```

> 힌트: `repair_chain`의 마지막은 `StrOutputParser`입니다. `try_parse`는 무엇을 반환할 수 있나요?

<details>
<summary>정답 보기</summary>

① `repaired_output`은 `StrOutputParser`가 만든 **문자열**이라 `.category`가 없음 → `AttributeError`. 재검증 전에는 필드를 읽지 않습니다. ② `try_parse`는 실패 시 `None`을 반환하므로 `final_result.summary`가 `AttributeError: 'NoneType' ...`가 될 수 있음 → `None` 먼저 확인.

```python
repaired_output = repair_chain.invoke(repair_input)       # str
final_result = try_parse(parser, repaired_output)          # 객체 또는 None
if final_result is None:
    print("[최종 결과] 구조화 출력을 만들지 못했습니다.")
else:
    print(final_result.summary)
```

</details>

### 5-Q7. 복구 흐름 추적 (5-3)

모델 대신 고정 문자열을 돌려주는 가짜 복구 함수를 씁니다.

```python
calls = 0
def fake_repair(broken: str) -> str:
    global calls
    calls += 1
    return REPAIR_TEXT

def repair_once(raw: str):
    first = try_parse(parser, raw)
    if first is not None:
        return first
    fixed = fake_repair(raw)
    return try_parse(parser, fixed)
```

`VALID = '{"category":"개념","summary":"LCEL 질문"}'`, `BROKEN = '{"category":"기타"}'`일 때, 각 경우의 `calls` 값과 반환값(객체 / `None`)을 쓰세요.

| 경우 | `raw` | `REPAIR_TEXT` | `calls` | 반환값 |
| --- | --- | --- | --- | --- |
| 1 | `VALID` | `BROKEN` | ? | ? |
| 2 | `BROKEN` | `VALID` | ? | ? |
| 3 | `BROKEN` | `BROKEN` | ? | ? |

> 힌트: 첫 검증이 성공하면 복구 함수까지 가지 않습니다.

<details>
<summary>정답 보기</summary>

| 경우 | `calls` | 반환값 |
| --- | --- | --- |
| 1 | 0 | 객체 (`category='개념'`, `needs_code=False`) |
| 2 | 1 | 객체 (복구 결과를 같은 Parser로 통과) |
| 3 | 1 | `None` (재검증 실패, 추가 요청 없음) |

경우 1에서 `REPAIR_TEXT`가 잘못된 값이어도 상관없는 이유: 복구 함수가 아예 호출되지 않기 때문입니다.

</details>

### 5-Q8. 수정 Prompt 채우기 (5-3)

(1) 아래 입력으로 `repair_chain.invoke(repair_input)`를 하면 어떤 문제가 생길까요? (2) `format_instructions`를 넣어 주는 이유를 한 문장으로 쓰세요.

```python
repair_input = {
    "question": "LCEL에서 pipe 연산자는 어떤 역할을 하나요?",
    "broken_output": '{"category":"기타"}',
}
```

> 힌트: `repair_prompt`의 system 메시지에 있는 변수를 확인하세요.

<details>
<summary>정답 보기</summary>

(1) system 메시지의 `{format_instructions}` 변수 값이 없어 Prompt를 완성할 수 없으므로 오류가 납니다 (3장의 키 불일치와 같은 종류). `"format_instructions": parser.get_format_instructions()`를 추가합니다. (2) 모델에게 최종 JSON이 따라야 할 필드와 형식(허용값 포함)을 알려 줘야 올바르게 다시 쓸 수 있기 때문입니다.

</details>

### 5-Q9. 무한 재시도 고치기 (5-3)

아래 코드는 어떤 위험이 있나요? `MAX_REPAIR_ATTEMPTS = 1` 원칙에 맞게 고치세요 (반복문 없이 써도 됩니다).

```python
result = try_parse(parser, raw)
while result is None:
    fixed = repair_chain.invoke({...})
    result = try_parse(parser, fixed)
print(result.category)
```

> 힌트: 모델이 계속 잘못된 JSON을 주면 어떻게 될까요? 마지막 줄도 확인하세요.

<details>
<summary>정답 보기</summary>

모델이 계속 잘못 응답하면 반복이 끝나지 않아 실행 시간과 API 비용이 무한히 늘어납니다. 또 반복을 벗어난 뒤에도 `None` 확인 없이 필드를 읽는 구조입니다.

```python
result = try_parse(parser, raw)
if result is None:                                   # 첫 검증 실패일 때만
    fixed = repair_chain.invoke({...})                # 수정 요청 딱 1회
    result = try_parse(parser, fixed)                 # 같은 Parser로 재검증

if result is None:
    print("[최종 결과] 구조화 출력을 만들지 못했습니다.")
else:
    print(result.category)
```

</details>

### 5-Q10. 개념 O/X (5장 전체)

1. `with_structured_output()`을 쓰면 `category` 분류가 실제로 맞다는 것까지 보장된다.
2. `get_format_instructions()`를 호출하면 모델 API가 한 번 호출된다.
3. `PydanticOutputParser(pydantic_object=QuestionClassification())`처럼 객체를 넣어야 한다.
4. 첫 검증이 성공했더라도 안전을 위해 수정 요청을 한 번 보내는 것이 좋다.
5. 재검증까지 실패하면 `None`을 반환하고, 필드를 읽기 전에 `None`인지 확인한다.

> 힌트: 5-1의 "형식 vs 내용", 5-2의 Parser 만들기, 5-3의 원칙을 떠올려 보세요.

<details>
<summary>정답 보기</summary>

1 X (형식만 검증, 내용의 정확성은 아님) · 2 X (형식 안내 문자열만 만듦) · 3 X (클래스 `QuestionClassification`을 전달) · 4 X (불필요한 호출이므로 생략) · 5 O

</details>
