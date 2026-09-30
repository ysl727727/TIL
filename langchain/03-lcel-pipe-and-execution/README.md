# 3장. LCEL과 Runnable 실행 — invoke · batch · stream

> 2026-09-30 학습 기록. `prompt | model | parser` 체인을 만들고, 실행 방식을 고르고, 오류가 나면 단계별 자료형으로 원인을 찾는 흐름을 정리했습니다.

## 학습 목표

- `|`(pipe 연산자)로 Prompt·Model·Parser를 하나의 `RunnableSequence`로 연결한다.
- 체인을 **만드는 코드**와 **실행하는 코드**(`invoke`)를 구분하고, API 호출 시점을 설명한다.
- 입력 개수와 표시 방식에 따라 `invoke()` / `batch()` / `stream()`을 고른다.
- `dict → ChatPromptValue → AIMessage → str` 자료형 경계를 따라 오류 위치를 좁힌다.
- 체인 생성 함수로 같은 구조를 입력만 바꿔 재사용한다.

## 실습 파일

| 강 | 주제 | 실습 상태 |
| --- | --- | --- |
| 3-1 | LCEL pipe 연산자와 Runnable | 📘 이론 정리 |
| 3-2 | invoke / batch / stream | 📘 이론 정리 |
| 3-3 | 중간 출력 디버깅과 체인 재사용 | 📘 이론 정리 |

실습 노트북은 이번 기록에 포함하지 않았습니다. 아래 확인 문제는 API 없이 풀 수 있도록 만든 복습용 문제입니다.

## 전체 흐름

3장은 2장에서 따로따로 실행하던 Prompt, Model, Parser를 **한 줄로 묶고(3-1)**, 그 한 줄을 **상황에 맞게 실행하고(3-2)**, 고장 나면 단계별로 쪼개 원인을 찾고 함수로 재사용(3-3)하는 흐름입니다.

1. **3-1 연결하기** — `chain = prompt | model | parser`. `|`는 왼쪽 출력을 오른쪽 입력으로 넘기는 pipe 연산자. 결과물은 `RunnableSequence`이고, 이것도 Runnable이라 `invoke()`로 실행.
2. **3-2 실행 방식 고르기** — 같은 `chain`을 입력 개수·보여 주는 방식에 따라 `invoke()` / `batch()` / `stream()`으로 실행.
3. **3-3 고치고 재사용하기** — 실행이 실패하면 입력 → Prompt → Model → Parser 순서로 자료형을 출력해 경계를 찾음. 잘 도는 체인은 `build_..._chain()` 함수로 만들어 입력만 바꿔 재사용.

```text
chain.invoke 한 번에 dict에서 str까지 자료형이 차례로 바뀝니다

   dict          ChatPromptValue          AIMessage           str
 ───────► [Prompt] ─────────────► [Model] ──────────► [Parser] ───────►
          변수 채워               여기서               본문만
          메시지 만들기           API 호출             str로 꺼내기

chain = prompt | model | parser 는 연결만 합니다. 실행은 invoke / batch / stream 때 일어납니다.
```

화살표 위 이름이 각 경계에서 넘겨지는 자료형입니다. 오류가 나면 이 네 칸 중 어디서 기대와 달라졌는지 찾으면 됩니다.

2장 → 3장 연결고리: 2장의 `prompt.invoke()` → `model.invoke()` → `parser.invoke()` 세 줄이 3-1에서 `chain.invoke()` 한 줄이 됩니다. 3-3의 디버깅은 그 한 줄을 다시 세 줄로 펼쳐 보는 작업입니다.

## 핵심 이론

### 1. LCEL pipe 연산자와 Runnable (3-1강)

LCEL(LangChain Expression Language)은 구성 요소를 `|`로 이어 실행 흐름을 표현하는 방법입니다. `chain = prompt | model | parser`는 **연결만** 하는 코드이고, 모델 API는 `chain.invoke(...)`를 호출할 때 처음 불립니다.

| 위치 | 구성 요소 | 받는 값 | 내보내는 값 |
| --- | --- | --- | --- |
| 시작 | 입력 | - | `dict` (`{"question": ...}`) |
| 1단계 | `ChatPromptTemplate` | `dict` | `ChatPromptValue` (역할별 메시지) |
| 2단계 | `ChatOpenAI` | 역할별 메시지 | `AIMessage` |
| 3단계 | `StrOutputParser` | `AIMessage` | `str` |

- **Runnable** = 입력을 받아 작업하고 출력을 돌려주는 구성 요소의 공통 실행 방식. Prompt, Model, Parser, 그리고 이어 붙인 `chain` 전체가 모두 Runnable이라 똑같이 `invoke()`를 씁니다.
- `type(chain).__name__` → `RunnableSequence`. 연결한 전체도 다시 실행 가능한 Runnable이 된다는 뜻입니다.
- `|`는 자료형을 자동으로 바꿔 주지 않습니다. 왼쪽 출력을 오른쪽이 받을 수 있어야 체인이 돕니다.
- 입력 dict의 키 이름은 Prompt의 `{question}`과 정확히 같아야 합니다.

| 자주 나는 오류 | 원인 → 해결 |
| --- | --- |
| `OPENAI_API_KEY`가 없음 | `.env` 확인. 키를 코드에 적거나 출력하지 않기 |
| `KeyError` / Prompt 변수 오류 | `{"query": ...}`처럼 다른 키 전달 → `question`으로 맞추기 |
| 결과가 `AIMessage` | Parser를 빼먹음 → 끝에 `StrOutputParser()` 연결 |
| 아무것도 출력 안 됨 | 체인만 만들고 `invoke()`·`print()`를 안 함 |
| `unsupported operand type` | `\|` 양쪽 중 Runnable이 아닌 일반 값이 있음 → `type()`으로 확인 |

### 2. invoke / batch / stream 실행 방식 (3-2강)

체인 구조는 그대로 두고, 실행 메서드만 바꿉니다.

| 비교 | `invoke()` | `batch()` | `stream()` |
| --- | --- | --- | --- |
| 입력 | 한 건 (`dict`) | 여러 건의 리스트 (`[dict, dict]`) | 한 건 (`dict`) |
| 결과 | 최종 결과 한 개 (`str`) | 결과 리스트 (`list[str]`), 입력 순서대로 | 도착 순서대로 나오는 조각 |
| 결과 처리 | 변수에 바로 저장 | 반복문으로 목록 확인 | 반복문으로 조각 확인 |
| 쓰는 때 | 질문 하나에 답하기 | 독립 입력 여러 개 요약·분류 | 긴 답변을 생성 중부터 보여 주기 |

```python
for chunk in chain.stream({"question": "stream의 장점은?"}):
    print(chunk, end="", flush=True)   # 줄바꿈 없이 이어 출력
print()
```

- 조각을 모아 전체 답변을 만들려면 리스트에 `append` 후 `"".join(chunks)`.
- 조각의 개수와 끊기는 위치는 실행마다 다릅니다. 조각 개수가 아니라 합친 문자열이 비어 있지 않은지 확인합니다.
- `Runnable.batch()`는 LangChain 메서드이며, 파일을 올려 나중에 받는 공급자 Batch API와는 다른 기능입니다.
- 처음엔 `invoke()`로 체인이 도는지 확인한 뒤 `batch()`/`stream()`으로 바꾸는 것이 쉽습니다. 세 방식을 연달아 돌리면 API 호출도 그만큼 늘어납니다.

| 자주 나는 오류 | 원인 → 해결 |
| --- | --- |
| `batch()`에 dict 하나 전달 | 리스트로 감싸기: `chain.batch([{...}])` |
| `results.upper()` 실패 | batch 결과는 리스트 → 반복문으로 꺼내기 |
| `print(chain.stream(...))`에 객체 표시 | stream은 반복 가능한 값 → `for`로 꺼내기 |
| 조각마다 줄바꿈 | `print(chunk, end="", flush=True)` |
| `"Invoke"` 모드 이름 | 대소문자까지 정확히 `"invoke"` |

### 3. 중간 출력 디버깅과 chain 재사용 (3-3강)

체인 오류는 **왼쪽부터 한 단계씩** 좁혀 갑니다. ① 처음 입력의 자료형·키가 Prompt 요구와 맞나 → ② Prompt 결과를 Model이 받을 수 있나 → ③ Model 결과를 Parser가 받을 수 있나.

- `prompt.input_variables` → `['example', 'topic']`처럼 필요한 키 목록 확인 (정렬되어 보일 수 있음).
- 변수가 2개인 Prompt에 `"LCEL"` 같은 **문자열**을 넣으면 어느 값을 어디에 넣을지 몰라 오류 → `{"topic": "LCEL", "example": "..."}` **dict**로 수정.
- 오류 메시지가 길어도 먼저 `print(type(x).__name__)`으로 `str`인지 `dict`인지 봅니다.
- `prompt.invoke(...)` 후 `to_messages()`로 system/human 메시지가 제대로 채워졌는지 확인할 수 있고, 이 단계는 API를 부르지 않습니다.
- 단계를 쪼개 실행하면 정상 흐름은 `입력: dict → Prompt 결과: ChatPromptValue → Model 결과: AIMessage → Parser 결과: str`.

**체인 생성 함수**: Prompt·Model·Parser를 조립해 **반환만** 하는 함수입니다.

```python
def build_explain_chain(model, audience: str):
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"당신은 {audience} 대상 LangChain 튜터입니다."),
        ("human", "주제:{topic}\n간단한 예:{example}"),
    ])
    return prompt | model | StrOutputParser()   # 여기서는 API 호출 없음

beginner_chain = build_explain_chain(model, "파이썬 입문자")
beginner_chain.invoke({"topic": "LCEL", "example": "prompt | model | parser"})
```

- 재사용되는 것: system 역할, human 문장 구조, 같은 Model·Parser, 실행 순서. 바뀌는 것: 입력 dict의 값.
- 주의: `f"...{audience}..."`는 함수 호출 시점에 채워지고, `{topic}`은 실행 시점에 채워집니다.

| 자주 나는 오류 | 원인 → 해결 |
| --- | --- |
| 문자열을 dict 자리에 전달 | 두 키를 가진 dict로 |
| 키 이름 오타 (`topics`) | `prompt.input_variables`와 비교 |
| 생성 함수 결과가 `None` | `return prompt \| model \| parser` 누락 |
| 함수 안에서 `invoke()`까지 실행 | 입력을 바꿔 재사용할 수 없음 → 체인만 반환 |
| 같은 입력이면 같은 답이라고 기대 | 모델 문장은 매번 다를 수 있음 → 자료형·형식으로 확인 |

## 확인 문제

모든 문제는 API 없이 풀 수 있습니다. 코드 문제는 `from langchain_core.runnables import RunnableLambda`가 이미 되어 있다고 가정합니다. 각 문제 바로 아래에 정답과 해설이 있습니다. 먼저 풀어 본 뒤 확인하세요.

### 3-Q1. API 호출 횟수 (3-1, 3-2)

`prompt`, `model`(ChatOpenAI), `parser`가 준비되어 있습니다. 아래 코드 전체에서 모델 API는 몇 번 호출될까요? 첫 번째 `print`의 출력도 쓰세요.

```python
chain = prompt | model | parser
print(type(chain).__name__)
r = chain.invoke({"question": "A"})
rs = chain.batch([{"question": "B"}, {"question": "C"}])
```

> 힌트: 체인을 "만드는" 줄과 "실행하는" 줄을 구분하세요.

<details>
<summary>정답 보기</summary>

출력 `RunnableSequence`, API 호출 **3회**. `chain = ...` 줄은 연결만 하므로 0회, `invoke` 1건 = 1회, `batch` 입력 2건 = 2회.

</details>

### 3-Q2. 자료형 빈칸 (3-1, 3-3)

빈칸을 채우세요. 그리고 `chain = prompt | model`처럼 Parser를 빼면 최종 결과의 자료형은 무엇이 될까요?

`dict` → Prompt → ( ① ) → Model → ( ② ) → Parser → `str`

> 힌트: 3-3 실습에서 `type(...).__name__`으로 찍었던 네 줄을 떠올려 보세요.

<details>
<summary>정답 보기</summary>

① `ChatPromptValue` ② `AIMessage`. Parser를 빼면 마지막 단계가 Model이므로 결과는 `str`이 아니라 `AIMessage`입니다 (3-1 오류 3).

</details>

### 3-Q3. 출력 예측 (3-1, 3-2)

```python
a = RunnableLambda(lambda x: x * 2)
b = RunnableLambda(lambda x: x + 3)
print((a | b).invoke(4))
print((b | a).invoke(4))
print((a | b).batch([1, 2, 3]))
```

> 힌트: `|`의 왼쪽이 먼저 실행됩니다. batch는 각 입력에 체인 전체를 따로 적용합니다.

<details>
<summary>정답 보기</summary>

`11`, `14`, `[5, 7, 9]`. (a|b)는 4×2=8 → 8+3=11, (b|a)는 4+3=7 → 7×2=14. 순서를 바꾸면 결과가 바뀝니다. batch는 1→5, 2→7, 3→9를 입력 순서대로 리스트에 담습니다.

</details>

### 3-Q4. 버그 찾기 — batch (3-2)

아래 코드에서 잘못된 곳 두 군데를 찾고 고치세요.

```python
results = chain.batch({"question": "batch는 무엇인가요?"})
print(results.upper())
```

> 힌트: batch의 입력과 결과는 각각 어떤 자료형이어야 하나요?

<details>
<summary>정답 보기</summary>

```python
results = chain.batch([{"question": "batch는 무엇인가요?"}])   # ① 리스트로 감싸기
for r in results:                                              # ② 결과도 리스트 → 반복문
    print(r.upper())
```

</details>

### 3-Q5. stream 코드 작성 (3-2)

아래 연습 체인을 `stream()`으로 실행하세요. 조각을 줄바꿈 없이 바로 출력하면서 리스트에도 모으고, 마지막에 합친 전체 문자열과 그 길이(`len`)를 새 줄에 출력하세요.

```python
chain = RunnableLambda(lambda d: f"답: {d['question']}")
input_data = {"question": "stream"}
```

> 힌트: `print(..., end="", flush=True)`, `"".join(...)`. 연습 체인은 조각을 한 개만 줄 수도 있습니다.

<details>
<summary>정답 보기</summary>

```python
chunks = []
for raw_chunk in chain.stream(input_data):
    chunk = str(raw_chunk)
    chunks.append(chunk)
    print(chunk, end="", flush=True)
print()                         # 스트리밍 뒤 줄바꿈
full_text = "".join(chunks)
print(full_text)                # 답: stream
print(len(full_text))           # 9
```

`"답: stream"`은 `답`, `:`, 공백, `stream`(6자) → 9자. 연습 체인은 조각이 1개여도 정상입니다.

</details>

### 3-Q6. 디버깅 — 입력 불일치 (3-3)

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "당신은 튜터입니다."),
    ("human", "주제:{topic}\n예:{example}"),
])
prompt.invoke("LCEL")                                        # (가)
prompt.invoke({"topic": "LCEL", "examples": "a | b"})       # (나)
```

(1) `print(prompt.input_variables)`의 출력은? (2) (가), (나)가 각각 왜 실패하는지 쓰고, 둘 다 통과하는 입력 하나를 쓰세요.

> 힌트: (가)는 자료형 문제, (나)는 키 이름 문제입니다.

<details>
<summary>정답 보기</summary>

(1) `['example', 'topic']` (정렬되어 보일 수 있음). (2) (가) 변수가 2개인 Prompt에 **문자열** 하나를 줘서 어느 칸에 넣을지 알 수 없음. (나) 자료형은 dict지만 `examples`는 오타라 `example` 값이 없음. 정답 입력: `{"topic": "LCEL", "example": "a | b"}`.

</details>

### 3-Q7. 체인 생성 함수 고치기 (3-3)

아래 함수로 `quiz_chain = build_quiz_chain(model, "입문")`을 만들고 `quiz_chain.invoke({"topic": "Runnable"})`을 하면 오류가 납니다. 문제 두 가지를 찾고 고치세요. 덤으로, `{level}`과 `{topic}`은 각각 언제 값이 채워지나요?

```python
def build_quiz_chain(model, level: str):
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"{level} 수준의 문제를 하나 내세요."),
        ("human", "{topic}"),
    ])
    chain = prompt | model | StrOutputParser()
    result = chain.invoke({"topic": "LCEL"})
```

> 힌트: 이 함수는 무엇을 반환하나요? 함수 안에서 질문을 고정하면 재사용이 될까요?

<details>
<summary>정답 보기</summary>

① `return`이 없어 함수가 `None`을 돌려줌 → `quiz_chain.invoke(...)`에서 `AttributeError: 'NoneType' object has no attribute 'invoke'`. ② 함수 안에서 `invoke({"topic": "LCEL"})`로 질문을 고정해 실행함 → 만들 때마다 API가 불리고 입력을 바꿔 재사용할 수 없음. 고친 끝부분:

```python
    return prompt | model | StrOutputParser()
```

`{level}`은 f-string이라 `build_quiz_chain(...)`을 **호출할 때** 채워지고, `{topic}`은 Prompt 변수라 `invoke()`로 **실행할 때** 채워집니다.

</details>

### 3-Q8. 실행 방식 고르기 (3-2)

각 상황에 `invoke()` / `batch()` / `stream()` 중 하나를 고르고 이유를 한 줄로 쓰세요.

1. 상품 리뷰 100개를 각각 긍정·부정으로 분류해 표로 저장한다.
2. 채팅 화면에 긴 답변이 타이핑되듯 조금씩 나타나게 하고 싶다.
3. 사용자가 버튼을 눌러 보낸 질문 하나에 답하고, 완성된 답만 DB에 저장한다.

> 힌트: 입력이 몇 건인가? 완성 전부터 보여 줘야 하나?

<details>
<summary>정답 보기</summary>

1 → `batch()` (독립 입력 여러 건), 2 → `stream()` (완성 전부터 표시), 3 → `invoke()` (입력 1건, 완성 결과 1개만 필요).

</details>
