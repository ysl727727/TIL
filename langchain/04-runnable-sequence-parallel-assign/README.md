# 4장. Runnable 조합 — Sequence · Parallel · assign

> 2026-09-30 학습 기록. 3장에서 만든 체인을 부품으로 삼아 순서대로 잇거나, 같은 입력을 여러 갈래로 나누거나, 기존 dict에 필드를 덧붙이는 방법을 정리했습니다.

## 학습 목표

- 다음 단계가 앞 결과를 쓰는지로 순차(`RunnableSequence`)와 병렬(`RunnableParallel`)을 구분한다.
- 병렬 결과가 branch 이름을 키로 한 dict라는 점과, 모델 branch 수만큼 API가 호출된다는 점을 설명한다.
- `RunnablePassthrough`(보존)·`RunnableLambda`(계산)·`.assign()`(추가)의 역할을 구분한다.
- 의존성이 있는 필드는 assign을 단계별로 나눠 순서대로 연결한다.

## 실습 파일

| 강 | 주제 | 실습 상태 |
| --- | --- | --- |
| 4-1 | RunnableSequence와 RunnableParallel | 📘 이론 정리 |
| 4-2 | RunnablePassthrough / RunnableLambda / assign | 📘 이론 정리 |

실습 노트북은 이번 기록에 포함하지 않았습니다. 아래 확인 문제는 API 없이 풀 수 있도록 만든 복습용 문제입니다.

## 전체 흐름

4장은 3장에서 만든 `Prompt | Model | Parser` 체인을 **부품**으로 삼아, 더 큰 파이프라인으로 조합하는 방법입니다. 판단 기준은 단 하나, *다음 단계가 앞 단계의 결과를 필요로 하는가* 입니다.

1. **4-1 순서와 갈래** — 앞 결과가 필요하면 `RunnableSequence`(순차), 같은 입력을 각자 쓰면 `RunnableParallel`(병렬). 완성 실습: 문자열 전처리(순차) → 요약 branch + 키워드 branch(병렬) → `{"summary", "keywords"}` dict.
2. **4-2 기존 dict 확장** — 병렬처럼 새 dict를 만드는 대신, 입력 dict를 **보존**(`RunnablePassthrough`)하면서 일반 함수로 **계산**(`RunnableLambda`)한 값을 새 필드로 **추가**(`.assign()`). 완성 실습: 입력 확인 → `clean_question` 추가 → `question_length` 추가.

```text
4-1  순차 전처리 → 병렬 분석

 입력: 원문 str
 ┌──────────────┐        ┌─────────────────────────┐
 │ prepare_step │   ┌───►│ summary_chain           │───┐     ┌──────────────────────┐
 │ strip,       │───┤    │ Prompt | Model | Parser │   ├────►│ 결과 dict            │
 │ 빈 문자열 검사 │   │    └─────────────────────────┘   │     │ summary: 요약 문자열  │
 └──────────────┘   │    ┌─────────────────────────┐   │     │ keywords: 키워드 문자열│
 출력: text 키 dict  └───►│ keyword_chain           │───┘     └──────────────────────┘
                         │ Prompt | Model | Parser │
                         └─────────────────────────┘
 같은 text dict가 두 branch에 각각 들어가고, 모델 branch가 2개라 invoke 1번에 API가 2번 호출됩니다.

4-2  보존 · 계산 · 추가로 같은 dict를 확장

 ┌───────────────┐   ┌────────────────┐   ┌──────────────────┐   ┌─────────────────────┐
 │ 입력 dict      │──►│ validate_step  │──►│ assign ①         │──►│ assign ②            │
 │ question      │   │ dict인지,       │   │ + clean_question │   │ + question_length   │
 │ student_level │   │ 키·문자열 확인   │   │ question.strip() │   │ len(clean_question) │
 └───────────────┘   └────────────────┘   └──────────────────┘   └─────────────────────┘
 원본 question은 그대로 두고, 정리한 값은 새 필드에 넣습니다.
 ②는 ①이 만든 clean_question을 읽으므로, 순서를 바꾸면 KeyError가 납니다.
```

위는 새 dict를 만드는 병렬, 아래는 원래 dict에 필드를 덧붙이는 assign입니다. 두 경우 모두 결과는 dict입니다.

3장 → 4장 연결고리: 3장의 `chain` 한 개가 4장에서는 branch 하나가 됩니다. 3-3에서 배운 "자료형 경계 확인"은 4장에서 더 중요해집니다. 단계가 늘수록 경계도 늘기 때문입니다.

## 핵심 이론

### 1. RunnableSequence와 RunnableParallel (4-1강)

| 판단 질문 | 구조 |
| --- | --- |
| 두 번째 단계가 첫 번째 결과를 쓰나? | 순차 (`RunnableSequence`) |
| 두 작업이 같은 입력을 각자 쓰나? | 병렬 (`RunnableParallel`) |
| 입력을 정리한 뒤 두 분석으로 나누나? | 순차 뒤 병렬 (이번 실습) |

**RunnableSequence** — 여러 Runnable을 정해진 순서대로 실행하고, 마지막 단계의 출력을 전체 결과로 돌려줍니다. `RunnableSequence(a, b)`와 `a | b`는 같은 체인이며 둘 다 `type()`이 `RunnableSequence`입니다.

```python
sequence = RunnableSequence(RunnableLambda(clean_text), RunnableLambda(add_label))
sequence.invoke("  LangChain  ")   # → '학습 주제: LangChain'
```

**RunnableParallel** — 같은 입력을 여러 branch에 각각 전달하고, 결과를 **branch 이름을 키로 한 dict**로 모읍니다. 키 이름(`upper`, `length`)은 LangChain이 정한 게 아니라 작성자가 정합니다.

```python
parallel = RunnableParallel(upper=RunnableLambda(make_upper),
                            length=RunnableLambda(count_length))
parallel.invoke("LangChain")   # → {'upper': 'LANGCHAIN', 'length': 9}
```

완성 실습의 자료 흐름:

| 순서 | 단계 | 입력 | 출력 |
| --- | --- | --- | --- |
| 1 | `prepare_step` (문자열 확인·strip) | `str` | `{"text": str}` |
| 2-A | `summary_chain` (Prompt\|Model\|Parser) | `{"text": str}` | 요약 `str` |
| 2-B | `keyword_chain` (Prompt\|Model\|Parser) | `{"text": str}` | 키워드 `str` |
| 3 | `RunnableParallel` | 두 문자열 | `{"summary": ..., "keywords": ...}` |

- 전처리는 **한 번** 실행되고 그 결과가 두 branch의 공통 입력이 됩니다. 두 Prompt 모두 `{text}`를 쓰므로 전처리는 `text` 키를 반환해야 합니다.
- 두 branch가 같은 `model` 객체를 써도 요청은 별개 → `invoke()` 한 번에 **API 호출 2회**.
- 결과는 `result["summary"]`, `result["keywords"]`로 읽습니다. 키를 바꾸면 읽는 쪽도 바꿔야 합니다.

| 자주 나는 오류 | 원인 → 해결 |
| --- | --- |
| `OPENAI_API_KEY`가 없음 | `.env` 확인 |
| `text는 문자열이어야 합니다` | 숫자 등 비문자열 입력 → 문자열로 |
| `text는 비어 있을 수 없습니다` | `"   "` 같은 공백 입력 |
| Prompt 변수 불일치 | 전처리가 `{"content": ...}` 반환 → `text`로 맞추기 |
| 결과 `KeyError` | `result["keyword"]`처럼 branch 이름과 다른 키 |
| API 1회일 거라 예상 | 모델 branch 2개 = 2회 |

### 2. RunnablePassthrough / RunnableLambda / assign (4-2강)

| 도구 | 받는 값 | 하는 일 | 내보내는 값 |
| --- | --- | --- | --- |
| `RunnablePassthrough()` | 어떤 입력 | 바꾸지 않고 전달 (보존) | 받은 입력의 내용 |
| `RunnableLambda(function)` | 함수가 받을 입력 | 일반 Python 함수 실행 (계산) | 함수의 반환값 |
| `RunnablePassthrough.assign(...)` | **dict** | 기존 필드 유지 + 새 필드 추가 (확장) | 필드가 늘어난 dict |

```python
add_clean_question = RunnablePassthrough.assign(
    clean_question=RunnableLambda(extract_clean_question)   # 키 이름 = 새 필드 이름
)
add_question_length = RunnablePassthrough.assign(
    question_length=RunnableLambda(count_clean_question)    # 앞 단계의 clean_question을 읽음
)
chain = validate_step | add_clean_question | add_question_length
chain.invoke({"question": "  LCEL  ", "student_level": "입문"})
# → {'question': '  LCEL  ', 'student_level': '입문', 'clean_question': 'LCEL', 'question_length': 4}
```

- 원본 `question`은 **덮어쓰지 않습니다.** 정리된 값은 `clean_question`에 따로 들어가므로 두 값이 다른 것은 의도한 결과입니다.
- `assign()`의 입력은 dict여야 합니다. 문자열만 넣으면 기존 필드와 새 필드를 합칠 기준이 없어 오류.
- **순서가 중요**: 두 번째 assign은 첫 번째가 만든 `clean_question`을 읽으므로 반대로 연결하면 `KeyError`. 같은 assign 안의 두 계산은 서로의 새 값을 볼 수 없어서, 의존성은 다음 단계로 나눕니다.
- 완성 실습은 맨 앞에 `validate_step`(`require_input_dict`)을 두어 dict인지, `question` 키가 있는지, 값이 문자열인지 먼저 확인합니다. `extract_clean_question`은 strip 후 빈 문자열이면 `ValueError`.
- `"RunnablePassthrough는 어떤 역할을 하나요?"`의 `len()`은 32. 이 실습은 모델을 쓰지 않아 API 호출이 없습니다.

| 자주 나는 오류 | 원인 → 해결 |
| --- | --- |
| 입력은 딕셔너리여야 합니다 | 문자열만 전달 → `{"question": ...}` |
| question 키가 필요합니다 | `query`, `text` 등 다른 키 |
| question 값은 문자열이어야 합니다 | `{"question": 100}` |
| question은 비어 있을 수 없습니다 | `{"question": "   "}` |
| `clean_question` KeyError | `add_question_length \| add_clean_question` 순서 |
| 원본 question이 바뀔 거라 기대 | 원본 보존, 정리값은 새 필드 |

## 확인 문제

`from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough, RunnableSequence`가 되어 있다고 가정합니다. 모두 API 없이 실행됩니다.

### 4-Q1. 순차? 병렬? (4-1)

각 작업을 순차 / 병렬 / 순차 뒤 병렬 중 하나로 분류하세요.

1. 한국어 문장을 영어로 번역한 뒤, 그 **번역문**을 요약한다.
2. 같은 리뷰 하나에서 감성(긍정·부정)과 상품 카테고리를 각각 뽑는다.
3. 입력 문자열의 공백을 정리한 뒤, 정리된 글로 요약과 키워드를 각각 만든다.

> 힌트: "두 번째 작업이 첫 번째 결과를 입력으로 쓰는가?"

<details>
<summary>정답 보기</summary>

1 순차 (요약이 번역 결과를 입력으로 씀), 2 병렬 (같은 리뷰를 각자 씀), 3 순차 뒤 병렬 (4-1 완성 실습 구조).

</details>

### 4-Q2. 출력 예측 — Parallel (4-1)

```python
p = RunnableParallel(
    double=RunnableLambda(lambda x: x * 2),
    square=RunnableLambda(lambda x: x ** 2),
)
r = p.invoke(3)
print(r)
print(type(r).__name__)
```

> 힌트: 두 branch는 같은 3을 각각 받습니다.

<details>
<summary>정답 보기</summary>

`{'double': 6, 'square': 9}` / `dict`. 두 branch 모두 같은 3을 받고, 결과는 branch 이름을 키로 한 dict입니다.

</details>

### 4-Q3. 출력 예측 — 전처리 뒤 병렬 (4-1)

```python
prep = RunnableLambda(lambda s: {"text": s.strip()})
par = RunnableParallel(
    upper=RunnableLambda(lambda d: d["text"].upper()),
    n=RunnableLambda(lambda d: len(d["text"])),
)
print((prep | par).invoke("  lcel  "))
```

> 힌트: 병렬 branch가 받는 것은 원문 문자열일까, prep의 결과일까?

<details>
<summary>정답 보기</summary>

`{'upper': 'LCEL', 'n': 4}`. prep이 먼저 `{"text": "lcel"}`을 만들고, 병렬 branch는 원문이 아니라 이 dict를 받습니다.

</details>

### 4-Q4. API 호출 횟수 (4-1)

`summary_chain`, `keyword_chain`, `translate_chain`이 모두 `Prompt | Model | Parser`입니다.

```python
analysis = RunnableSequence(
    RunnableLambda(prepare_input),
    RunnableParallel(summary=summary_chain, keywords=keyword_chain, en=translate_chain),
)
analysis.invoke("LCEL은 ...")                 # (가)
analysis.batch(["첫 글", "둘째 글"])          # (나)
```

(가)와 (나)에서 모델 API는 각각 몇 번 호출될까요?

> 힌트: 같은 `model` 객체를 써도 branch마다 요청은 따로입니다.

<details>
<summary>정답 보기</summary>

(가) **3회** (모델 branch 3개, 전처리는 API 없음). (나) **6회** (입력 2건 × branch 3개).

</details>

### 4-Q5. 출력 예측 — assign (4-2)

```python
chain = RunnablePassthrough.assign(
    upper=RunnableLambda(lambda d: d["word"].upper())
)
print(chain.invoke({"word": "chain", "lang": "en"}))
print(RunnablePassthrough().invoke({"word": "chain"}))
```

> 힌트: assign은 기존 필드를 지우지 않습니다.

<details>
<summary>정답 보기</summary>

`{'word': 'chain', 'lang': 'en', 'upper': 'CHAIN'}` 그리고 `{'word': 'chain'}`. assign은 기존 필드를 유지하고 새 필드를 덧붙이며, Passthrough 단독은 받은 그대로 돌려줍니다.

</details>

### 4-Q6. Parallel과 assign 비교 (4-1, 4-2)

같은 입력 `d = {"question": " LCEL ", "level": "입문"}`과 같은 함수 `f = RunnableLambda(lambda x: x["question"].strip())`를 씁니다. (A), (B)의 출력을 각각 쓰고 차이를 한 문장으로 설명하세요.

```python
RunnableParallel(clean=f).invoke(d)             # (A)
RunnablePassthrough.assign(clean=f).invoke(d)   # (B)
```

> 힌트: 둘 다 dict를 돌려주지만, 원래 있던 키가 남는 쪽은 하나뿐입니다.

<details>
<summary>정답 보기</summary>

(A) `{'clean': 'LCEL'}` (B) `{'question': ' LCEL ', 'level': '입문', 'clean': 'LCEL'}`. Parallel은 branch 결과만으로 **새 dict**를 만들어 원래 키가 사라지고, assign은 **입력 dict에** 결과를 합쳐 원래 키가 남습니다. 간단히 말해 assign ≈ 입력 보존 + Parallel 결과 병합.

</details>

### 4-Q7. 버그 찾기 — 한 번에 두 필드 (4-2)

아래 코드는 `KeyError: 'clean'`이 납니다. 이유를 쓰고 고치세요.

```python
step = RunnablePassthrough.assign(
    clean=RunnableLambda(lambda d: d["name"].strip()),
    length=RunnableLambda(lambda d: len(d["clean"])),
)
step.invoke({"name": "  LangChain  "})
```

> 힌트: 같은 assign 안의 계산들은 서로가 방금 만든 값을 볼 수 있을까요?

<details>
<summary>정답 보기</summary>

같은 assign 안의 `clean`과 `length`는 **같은 원본 입력**을 동시에 받습니다. 그 입력에는 아직 `clean` 키가 없으므로 `KeyError`. 의존성이 있으면 assign을 두 단계로 나눕니다.

```python
step = (
    RunnablePassthrough.assign(clean=RunnableLambda(lambda d: d["name"].strip()))
    | RunnablePassthrough.assign(length=RunnableLambda(lambda d: len(d["clean"])))
)
step.invoke({"name": "  LangChain  "})
# → {'name': '  LangChain  ', 'clean': 'LangChain', 'length': 9}
```

</details>

### 4-Q8. 코드 작성 — 주문 합계 (4-2)

입력 `{"price": 12000, "qty": 3}`에 `total`(price × qty)을 먼저 추가하고, 그다음 `grade`(total이 30000 이상이면 `"big"`, 아니면 `"small"`)를 추가하는 체인을 만드세요. 원본 필드는 남아 있어야 합니다. 최종 출력도 쓰세요.

> 힌트: 함수 두 개 + `RunnablePassthrough.assign` 두 개 + `|`. 순서를 생각하세요.

<details>
<summary>정답 보기</summary>

```python
def calc_total(data: dict) -> int:
    return data["price"] * data["qty"]

def calc_grade(data: dict) -> str:
    return "big" if data["total"] >= 30000 else "small"

add_total = RunnablePassthrough.assign(total=RunnableLambda(calc_total))
add_grade = RunnablePassthrough.assign(grade=RunnableLambda(calc_grade))
chain = add_total | add_grade          # grade가 total을 읽으므로 이 순서

print(chain.invoke({"price": 12000, "qty": 3}))
# → {'price': 12000, 'qty': 3, 'total': 36000, 'grade': 'big'}
```

</details>

### 4-Q9. 종합 출력 예측 (3장 + 4장)

```python
prep = RunnableLambda(lambda s: {"text": s.strip()})
chain = prep | RunnableParallel(
    original=RunnablePassthrough(),
    length=RunnableLambda(lambda d: len(d["text"])),
)
print(chain.invoke("  hi  "))
print(chain.batch(["a", " bb "]))
```

> 힌트: Passthrough가 branch 안에 있으면, 그 branch의 결과는 "branch가 받은 입력 그대로"입니다.

<details>
<summary>정답 보기</summary>

```text
{'original': {'text': 'hi'}, 'length': 2}
[{'original': {'text': 'a'}, 'length': 1}, {'original': {'text': 'bb'}, 'length': 2}]
```

Passthrough branch는 prep이 넘긴 dict를 그대로 담으므로 `original` 값이 문자열이 아니라 `{'text': ...}`입니다. batch는 입력마다 전처리와 병렬을 따로 적용해 결과 리스트를 돌려줍니다.

</details>
