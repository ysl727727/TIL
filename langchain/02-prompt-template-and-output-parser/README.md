# Chapter 2: PromptTemplate과 ChatPromptTemplate, ChatModel과 Output Parser

> 2026-09-29 학습 기록. 2-1강(PromptTemplate과 ChatPromptTemplate), 2-2강(ChatModel과 Output Parser 연결) 이론을 정리했습니다. 이 장의 실습 파일(`실습.py`)은 아직 받지 못해 이론만 기록합니다.

## Learning Goals

- Prompt에서 고정 문장과 실행할 때 바뀌는 입력값을 구분한다.
- `PromptTemplate`으로 재사용 가능한 문자열 Prompt를 만든다.
- `ChatPromptTemplate`으로 system·human 역할이 구분된 메시지를 만든다.
- Prompt → ChatModel → Output Parser의 입출력 자료형을 순서대로 설명한다.
- `StrOutputParser`로 `AIMessage`를 문자열로 바꾼다.
- List Parser와 JSON Parser로 응답을 `list`·`dict`로 바꾸고, 필요한 키가 있는지 확인한다.

## Practice Files

| Lesson | File | Practice status |
| --- | --- | --- |
| 2-1 / 2-2 | — | **자료 미수령** — 강의 교안만 확보. 실습 `실습.py`는 1-2강에서 만든 프로젝트의 하위 폴더에서 `uv run python 실습.py`로 실행하는 구조 |

## Core Theory

### 1. Template은 편지 양식 (2-1강)

Prompt는 모델에 전달하는 지시와 입력이다. 매번 전체를 새로 쓰면 오타가 생기고, 답변 원칙을 한꺼번에 바꾸기 어렵다. Template은 **고정 문장은 그대로 두고 바뀌는 값만 교체**하는 방식이다.

```python
from langchain_core.prompts import PromptTemplate

template = PromptTemplate.from_template(
    "주제: {topic}\n독자 수준: {audience}\n주제를 한 문장으로 설명하세요."
)
print(template.format(topic="LangChain", audience="파이썬 입문자"))
```

중괄호로 감싼 `{topic}`, `{audience}`가 입력 변수이고, `format()`이 값을 채워 **일반 문자열**을 반환한다.

Template을 쓰는 이유 — 공통 지시문을 한 곳에서 관리, 질문·문서만 바꿔 같은 형식 재사용, 필요한 입력값을 변수 이름으로 확인, 역할 기반 메시지 순서 유지.

### 2. 필요한 입력 변수 확인

```python
print(template.input_variables)   # ['topic', 'audience']
```

변수 이름은 대소문자까지 정확히 일치해야 한다. Template에 `{question}`이 있는데 `query=`로 전달하면 값이 채워지지 않는다.

입력값 앞에 `독자 수준:` 같은 이름표를 붙이면 값이 바뀌어도 한국어 조사가 어색해지지 않는다. Template은 값을 정확히 치환할 뿐 **문장의 자연스러움이나 사실성까지 확인하지는 않는다** — 모델 호출 전에 완성된 Prompt를 직접 읽어 보는 습관이 필요하다.

### 3. `ChatPromptTemplate`으로 역할 나누기

```python
from langchain_core.prompts import ChatPromptTemplate

chat_template = ChatPromptTemplate.from_messages([
    ("system", "당신은 {subject} 입문 수업의 튜터입니다. 전문 용어를 먼저 풀어 쓰세요."),
    ("human", "{question}"),
])
messages = chat_template.format_messages(subject="LangChain", question="...")
```

- `system`: 모든 질문에 공통으로 따를 역할과 답변 원칙
- `human`: 사용자가 현재 실행에서 전달하는 질문

`from_messages()`에 전달한 목록 순서가 실제 전달 순서다. 공통 지시를 먼저, 현재 질문을 다음에 둔다. 답변 원칙을 바꾸고 싶으면 **system 메시지 한 곳만** 고치면 된다.

### 4. 두 Template 비교

| 비교 항목 | `PromptTemplate` | `ChatPromptTemplate` |
| --- | --- | --- |
| 결과 형태 | 하나의 문자열 | 역할별 메시지 목록 |
| 역할 구분 | 문자열 안에서 직접 표현 | system·human 역할로 보존 |
| 적합한 상황 | 단순 텍스트 생성·문자열 가공 | 채팅 모델에 역할별 메시지 전달 |
| 메서드 | `format()` | `format_messages()` |

둘 중 하나가 항상 낫지는 않다. **다음 단계가 어떤 입력을 받는지** 보고 고른다.

Template이 하지 않는 일: 모델 API 호출, 답변의 사실성 확인, 개인정보 제거, 결과를 리스트·JSON으로 변환. 이 강의에서는 **모델 호출 전 메시지를 만드는 역할**에만 집중한다.

### 5. 중괄호를 문자 그대로 쓰기

```python
PromptTemplate.from_template('다음 형식으로 답하세요: {{"answer": "{value}"}}')
```

JSON 예시처럼 중괄호 자체를 남기려면 두 번 쓴다. 안쪽 `{value}`만 입력 변수로 처리된다.

### 6. 기본 체인의 자료형 흐름 (2-2강)

| 단계 | 받는 값 | 내보내는 값 |
| --- | --- | --- |
| `ChatPromptTemplate` | 입력 변수의 값 | 역할별 메시지 목록 |
| `ChatOpenAI` | 역할별 메시지 목록 | `AIMessage` |
| `StrOutputParser` | `AIMessage` | `str` |
| List Parser | `AIMessage` | `list[str]` |
| JSON Parser | `AIMessage` | `dict` 또는 `list` |

오류가 나면 **앞 단계가 무엇을 내보냈고 다음 단계가 무엇을 기대했는지**를 먼저 확인한다.

### 7. `StrOutputParser`

```python
from langchain_core.output_parsers import StrOutputParser

text_result = StrOutputParser().invoke(ai_message)
print(isinstance(text_result, str))   # True
```

부가 정보가 필요하면 Parser를 붙이기 전 `AIMessage`를 유지한다. 화면에 답변 글만 보여 주거나 문자열 함수에 넘길 때는 Parser로 본문만 꺼내는 편이 간단하다.

Parser 동작만 확인할 때는 API 호출 없이 `AIMessage(content="...")`를 직접 만들어 넣으면 된다 — 비용이 들지 않고 결과가 항상 같다.

### 8. List Parser

```python
from langchain_core.output_parsers import CommaSeparatedListOutputParser

list_parser = CommaSeparatedListOutputParser()
format_instructions = list_parser.get_format_instructions()
```

**Parser는 모델이 형식을 지키게 만드는 장치가 아니다.** 두 단계가 필요하다 — `get_format_instructions()`로 원하는 형식을 Prompt에 알려 주고, 실제 응답을 Parser로 변환한다.

항목 안에 쉼표가 자주 들어가는 데이터에는 맞지 않는다. 짧은 키워드·태그 목록에 쓴다.

### 9. JSON Parser와 결과 검사

```python
from langchain_core.output_parsers import JsonOutputParser

json_result = json_parser.invoke(json_ai_message)

if not isinstance(json_result, dict):
    raise TypeError("JSON 객체를 기대했지만 다른 자료형이 반환되었습니다.")
if "category" not in json_result or "reason" not in json_result:
    raise ValueError("JSON 결과에 category 또는 reason 키가 없습니다.")
print(json_result["category"])
```

**자료형 확인 → 필요한 키 확인 → 값 읽기** 순서를 지키면 키가 없는 상태에서 값을 먼저 읽어 `KeyError`가 나는 일을 피할 수 있다. 지금 단계의 검사는 키의 존재만 확인하며, 값의 허용 범위 같은 세밀한 규칙은 다루지 않는다.

```python
from langchain_core.exceptions import OutputParserException

try:
    json_result = json_parser.invoke(json_ai_message)
except OutputParserException as error:
    print("모델 응답을 JSON으로 변환하지 못했습니다.", type(error).__name__)
```

실패를 빈 딕셔너리로 바꿔 넘기면 데이터 문제를 놓친다. **실패 사실을 로그나 사용자에게 분명히 남긴다.**

### 10. Parser 선택 순서

1. 애플리케이션에서 최종적으로 필요한 Python 자료형을 정한다.
2. 그 자료형에 맞는 Parser를 고른다.
3. Parser의 형식 안내를 Prompt에 포함한다.
4. 모델 응답을 Parser로 변환한다.
5. 변환 결과에 필요한 키와 값이 있는지 확인한다.

| Parser | 요청할 형식 | Python 결과 | 적합한 예 |
| --- | --- | --- | --- |
| `StrOutputParser` | 일반 문장 | `str` | 설명, 요약, 답변 |
| `CommaSeparatedListOutputParser` | 쉼표로 구분한 항목 | `list[str]` | 짧은 키워드, 태그 |
| `JsonOutputParser` | JSON 객체 또는 배열 | `dict` 또는 `list` | 분류 결과, 여러 필드 |

실습 `실습.py`는 상단의 `EXAMPLE = "text"` 값을 `"list"`, `"json"`으로 바꿔 한 번에 예제 하나만 실행한다 — **각 실행이 실제 API를 한 번씩 호출**하므로 필요한 예제만 돌린다.

## Questions and Newly Learned Points

- Parser를 "모델이 형식을 지키게 하는 장치"로 오해하기 쉬운데, 실제로는 **형식 안내를 Prompt에 넣는 일**과 **응답을 변환하는 일**이 따로다.
- Template을 만들었는데 모델 답변이 없는 것은 정상이다 — Template은 메시지만 만든다.
- JSON 결과를 바로 `["category"]`로 읽지 않고 자료형·키를 먼저 검사하는 순서가 `KeyError`를 없애는 핵심이었다.
- 중괄호 두 번 쓰기(`{{`)는 JSON 형식 예시를 Prompt에 넣을 때 반드시 필요하다.
- 자주 하는 오해: "Parser가 사실성도 검사한다"(형식 해석만 한다) / "List Parser면 어떤 목록이든 안전하다"(항목에 쉼표가 있으면 깨진다) / "변환 실패는 빈 값으로 넘기면 된다"(문제를 숨긴다).
