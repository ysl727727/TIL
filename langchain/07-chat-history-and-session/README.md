# 7장. 대화 기억 — 메시지 · session별 history

> 2026-10-01 학습 기록. 모델은 호출마다 기억이 없으므로, 앱이 대화를 역할이 있는 메시지로 저장하고 session_id로 사람별로 나눈 뒤, 다음 호출 때 Prompt에 다시 넣어 주는 흐름을 정리했습니다.

## 학습 목표

- 질문은 `HumanMessage`, 답변은 `AIMessage`로 저장해 역할 정보를 남긴다.
- `session_id`를 키로 한 dict에 `InMemoryChatMessageHistory`를 나눠 두고, 없을 때만 새로 만든다.
- 저장과 주입을 구분하고, `MessagesPlaceholder("history")`에 메시지 **목록**을 넣는다.
- 현재 질문은 모델 호출 **후에** 답변과 한 쌍으로 저장한다.
- Retriever(외부 문서)와 history(이 세션의 앞 대화)가 서로를 대신할 수 없음을 설명한다.

## 실습 파일

| 강 | 주제 | 실습 상태 |
| --- | --- | --- |
| 7-1 | 대화 메시지 구조와 session별 history | 📘 이론 정리 |
| 7-2 | RunnableWithMessageHistory와 Retriever/Memory 비교 | 📘 이론 정리 |

실습 노트북은 이번 기록에 포함하지 않았습니다. 6\~10장은 이론 분량이 많아, 실습은 10장 통합 실습(`starter.py`) 하나로 정리했습니다. 아래 확인 문제는 API 없이 풀 수 있는 복습용 문제입니다.

## 전체 흐름

### 한 문장

**모델은 기억력이 없습니다. 그래서 앱이 대화를 대신 적어 두었다가, 질문할 때마다 앞 대화를 같이 보여 줍니다.**

### 왜 필요한가

```text
1번째 호출: "제 이름은 민지입니다."      → 답변
2번째 호출: "제 이름이 뭐였나요?"        → 모델은 1번째 호출을 모름 (호출마다 완전히 새것)
```

**비유:** 매번 기억을 잃는 상담원이 있다고 생각해 보세요. 고객별 **상담 일지**를 따로 두고(history, session_id), 상담 시작 전에 일지를 읽어 주고(Prompt에 넣기), 상담이 끝나면 오늘 대화를 일지에 적습니다(저장). 상담원(모델)은 그대로인데, 일지 덕분에 기억하는 것처럼 보입니다.

### 그림으로 보기

```text
store (dict) ─ 상담 일지 보관함
 ├─ "student-a" → history: [Human("제 이름은 민지입니다"), AI("민지님, 반갑습니다")]
 └─ "student-b" → history: [Human("LCEL은 무엇인가요?"), AI("...")]   ← 서로 섞이지 않음

한 번의 질문 처리 (7-2 ask_session)
 ① 조회   history = get_session_history(store, "student-a")       ← 모델 호출 전
 ② 주입   chain.invoke({"history": list(history.messages),          ← 모델 호출 전
                         "question": "제 이름이 뭐였나요?"})
          Prompt: system → [이전 메시지들] → human(현재 질문)
 ③ 저장   history.add_messages([Human(질문), AI(답변)])              ← 모델 호출 후
```

### 강의 흐름

1. **7-1 저장하기** — 질문은 `HumanMessage`, 답변은 `AIMessage`. 한 번의 대화 = Human → AI 두 메시지. `InMemoryChatMessageHistory().add_messages([...])`로 순서대로 보관.
2. **7-1 나누기** — `store: dict[str, InMemoryChatMessageHistory]`. `get_session_history(store, session_id)`는 처음 보는 ID면 새 history를 만들고, 있으면 **같은 객체**를 돌려줌.
3. **7-2 넣고 다시 저장하기** — Prompt를 `system → MessagesPlaceholder("history") → human {question}` 순서로 만들고, `ask_session()`이 ① history 조회 ② `{"history": list(history.messages), "question": ...}`로 체인 실행 ③ 질문+답변을 history에 추가.

```text
7-1   store (dict)
      ├─ "student-a" → InMemoryChatMessageHistory
      │                 ├─ HumanMessage("LCEL은 무엇인가요?")
      │                 ├─ AIMessage("구성 요소를 연결하는 표현 방식입니다.")
      │                 ├─ HumanMessage("기본 예시를 알려 주세요.")
      │                 └─ AIMessage("prompt | model | parser처럼 연결합니다.")
      └─ "student-b" → 별도의 InMemoryChatMessageHistory (메시지 2개)

7-2   ask_session(chain, store, "student-a", question)
        ① get_session_history(store, "student-a")            ← 모델 호출 전: 조회
        ② chain.invoke({"history": list(history.messages),   ← 모델 호출 전: 주입
                        "question": question})
              Prompt: system → [이전 메시지들] → human(question) → Model → Parser → str
        ③ history.add_messages([Human(question), AI(answer)]) ← 모델 호출 후: 갱신
```

6장 → 7장 연결고리: 6장의 Retriever는 **외부 문서**를 찾아 `{context}`에 넣었고, 7장의 history는 **현재 세션의 이전 메시지**를 찾아 `history` 자리에 넣습니다. 둘 다 "모델에 추가 문맥을 준다"는 점은 같지만 가져오는 정보가 다릅니다.

## 핵심 이론

### 1. 대화 메시지 구조와 session별 history (7-1강)

6장까지의 체인은 호출마다 독립적이라, 두 번째 호출에서 "제 이름이 뭐였나요?"라고 물으면 첫 호출 내용을 알 수 없습니다. 이전 대화를 쓰려면 **애플리케이션이 메시지를 저장하고 다음 호출에 다시 전달**해야 합니다.

| 클래스 | 역할 | 이번 강의 |
| --- | --- | --- |
| `HumanMessage` | 사용자가 보낸 질문·요청 | 질문 저장 |
| `AIMessage` | 모델이 생성한 답변 | 답변 저장 |
| `SystemMessage` | 모델의 역할·답변 원칙 | 개념만 확인 |
| `BaseMessage` | 메시지 클래스들의 공통 부모 | 타입 표시 |

```python
from langchain_core.messages import AIMessage, HumanMessage

user_message = HumanMessage(content="LCEL은 무엇인가요?")
ai_message = AIMessage(content="LangChain 구성 요소를 연결하는 표현 방식입니다.")
print(type(user_message).__name__, user_message.content)   # HumanMessage LCEL은 무엇인가요?
print(user_message.type, ai_message.type)                   # human ai
```

- `content`에는 메시지 본문(이번 강의에서는 문자열)이 들어갑니다.
- `"LCEL은 무엇인가요?"`는 `str`(본문만), `HumanMessage(...)`는 본문 + **사용자 역할**. 대화 기록에는 역할 정보가 필요하므로 메시지 객체로 저장합니다.
- `message.type`은 `human` / `ai` / `system` 같은 역할 이름입니다.

**InMemoryChatMessageHistory**

```python
from langchain_core.chat_history import InMemoryChatMessageHistory

history = InMemoryChatMessageHistory()
print(len(history.messages))                                # 0
history.add_messages([
    HumanMessage(content="Parser는 무엇인가요?"),
    AIMessage(content="모델 출력을 사용할 형태로 바꾸는 구성 요소입니다."),
])
for message in history.messages:
    print(f"{message.type}: {message.content}")             # human: ... / ai: ...
```

- history는 답변을 **스스로 만들지 않습니다.** 이미 일어난 대화를 순서대로 보관할 뿐입니다.
- 현재 Python 프로세스의 **메모리에만** 저장 → 프로그램을 끄면 사라지고, 다른 프로세스와 공유되지 않습니다 (영구 저장소 아님).
- 참고: 강의 기준 버전(`langchain-core` 1.5.1)보다 새 버전(1.6.4 이상)을 설치하면 `InMemoryChatMessageHistory`에도 폐기 예정 경고가 뜹니다. 동작은 같으니 실습은 그대로 진행하면 됩니다.

**session_id와 세션 저장소**

history 하나만 쓰면 모든 사용자의 대화가 한 목록에 섞입니다. 그래서 `session_id` 문자열을 키로 하는 dict에 history를 나눠 둡니다.

```python
HistoryStore = dict[str, InMemoryChatMessageHistory]

def get_session_history(store: HistoryStore, session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in store:                     # 처음 보는 ID만
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]                        # 같은 ID → 항상 같은 객체

def add_turn(store, session_id, user_text, ai_text) -> None:
    history = get_session_history(store, session_id)
    history.add_messages([HumanMessage(content=user_text), AIMessage(content=ai_text)])
```

- `session_id` 자체가 대화를 저장하는 게 아니라, 알맞은 history를 **찾는 키**입니다.
- `get_session_history(store, "student-a") is get_session_history(store, "student-a")` → `True`. `store["student-a"] is not store["student-b"]` → `True`.
- `validate_session_id()`로 공백뿐인 session_id는 `ValueError("session_id는 비어 있을 수 없습니다.")` — 빈 키 하나에 여러 대화가 섞이는 실수를 막습니다.
- 저장 순서: 첫 질문 → 첫 답변 → 두 번째 질문 → 두 번째 답변. 한쪽만 저장하거나 순서가 바뀌면 실제 대화와 달라집니다.
- 완성 실습: student-a 대화 2회 → 메시지 **4개**, student-b 대화 1회 → **2개**, 같은 세션 재사용 `True`, 다른 세션 분리 `True`. 외부 API 호출 없음.

| 자주 나는 오류 | 원인 → 해결 |
| --- | --- |
| `ModuleNotFoundError: langchain_core` | 1-2강 가상환경 선택, `uv pip show langchain-core` |
| 문자열을 history에 바로 추가 | `add_messages()`에는 **메시지 객체 목록** 전달 |
| 질문과 답변 순서가 바뀜 | Human → AI 순서로 추가 |
| 모든 사용자가 같은 history 사용 | 전역 history 하나 대신 session_id 키 저장소 |
| 같은 session_id 기록이 매번 초기화 | 무조건 새로 만들지 말고 `if session_id not in store:`일 때만 생성 |
| 재실행하니 기록이 사라짐 | 메모리 저장이라 정상. 영구 저장은 범위 밖 |

### 2. RunnableWithMessageHistory와 Retriever/Memory 비교 (7-2강)

**저장 ≠ 주입.** 기록을 저장해도 다음 호출의 Prompt에 넣지 않으면 모델은 과거를 모릅니다.

| 동작 | 목적 | 시점 |
| --- | --- | --- |
| history 조회 | 현재 세션의 이전 메시지 찾기 | 모델 호출 전 |
| history 주입 | 이전 메시지를 Prompt에 포함 | 모델 호출 전 |
| 현재 질문 전달 | 이번에 답할 질문 추가 | 모델 호출 시 |
| 새 대화 저장 | 다음 호출용 기록 갱신 | 모델 호출 **후** |

**MessagesPlaceholder** — 이미 만들어진 메시지 **목록**을 Chat Prompt의 지정 위치에 펼쳐 넣습니다.

```python
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages([
    ("system", "당신은 LangChain 입문 수강생을 돕는 튜터입니다."),
    MessagesPlaceholder(variable_name="history"),   # 이전 메시지 목록이 여기 펼쳐짐
    ("human", "{question}"),                        # 이번 질문
])
messages = prompt.format_messages(
    history=[HumanMessage(content="제 이름은 민지입니다."), AIMessage(content="민지님, 반갑습니다.")],
    question="제 이름이 뭐였나요?",
)
# system: 당신은 ... 튜터입니다. / human: 제 이름은 민지입니다. / ai: 민지님, 반갑습니다. / human: 제 이름이 뭐였나요?
```

- 순서는 **system → history → human** 고정. 현재 질문 뒤에 이전 대화를 넣으면 시간 순서를 읽기 어렵습니다.
- `history`에는 문자열이 아니라 `HumanMessage`·`AIMessage` 목록을 넣습니다.

**현재 입문용 세션 대화 흐름 (완성 실습 방식)**

```python
chain = prompt | model | StrOutputParser()

def ask_session(chain, store, session_id: str, question: str) -> str:
    history = get_session_history(store, session_id)             # ① 조회
    raw_answer = chain.invoke({
        "history": list(history.messages),                       # ② 이전 메시지만 주입
        "question": question,
    })
    answer = str(raw_answer)
    history.add_messages([HumanMessage(content=question),        # ③ 호출 후 한 쌍으로 저장
                          AIMessage(content=answer)])
    return answer
```

- **현재 질문은 모델 호출 뒤에 저장**합니다. 호출 전에 history에 넣고 `{question}`에도 넣으면 같은 질문이 **두 번** 들어갑니다.
- `list(history.messages)`로 복사해 이번 호출에 쓸 이전 메시지를 명확히 전달하고, 호출 후 원래 history 객체에 새 대화를 추가합니다.
- student-a가 "제 이름은 민지입니다" → 같은 세션에서 "제가 말한 이름은?" 하면 두 번째 호출에 첫 질문·답변이 history로 들어가 "민지"를 답할 수 있습니다. student-b의 history에는 그 이름이 없습니다.
- 완성 실습 호출 순서: ① student-a 이름 전달 ② student-a 이름 참조 ③ student-b 별도 질문 → **API 3회**. 결과: student-a 대화 2회·메시지 4개, student-b 대화 1회·메시지 2개 (모델 문장과 무관하게 고정).
- API Key가 없으면 모델 객체를 만들기 전에 `OPENAI_API_KEY가 없습니다...`를 출력하고 정상 종료 (네트워크 요청 없음).

**RunnableWithMessageHistory — 기존 계약만 확인**

체인을 감싸 history 조회·갱신을 대신 해 주던 래퍼입니다. `langchain-core` 1.5.1 기준 **1.3.3부터 폐기 예정**, **2.0.0에서 제거 예정**이며, 대체 방향은 LangGraph의 내장 persistence(후속 과정)입니다. 완성 실습에서는 쓰지 않습니다.

| 기존 래퍼가 요구한 4요소 | 예 |
| --- | --- |
| 감쌀 기본 Runnable | `base_chain` (Prompt \| Model \| Parser) |
| session_id → history를 반환하는 함수 | `history_factory(session_id)` |
| 현재 질문이 든 입력 키 | `input_messages_key="question"` |
| 과거 메시지가 들어갈 키 | `history_messages_key="history"` |

```python
legacy_chain.invoke(
    {"question": question},                                  # 입력 dict에는 질문만
    config={"configurable": {"session_id": session_id}},     # session_id는 config에
)
```

**Retriever vs 대화 history**

| 비교 | Retriever (6장) | 대화 history (7장) |
| --- | --- | --- |
| 가져오는 정보 | 외부 문서 | 현재 세션의 이전 메시지 |
| 대표 입력 | 검색 질의 | `session_id` |
| 대표 결과 | `Document` 목록 | `BaseMessage` 목록 |
| 주요 목적 | 질문 관련 근거 찾기 | 대화 흐름 이어가기 |

- "교육 운영 문서에서 환불 기준을 찾아 주세요." → Retriever. "제가 앞에서 말한 이름이 뭐였나요?" → history.
- 서로 대신할 수 없습니다: Retriever는 사용자가 앞에서 한 말을 기억하지 않고, history는 외부 문서 검색 도구가 아닙니다. 실제 앱에서는 함께 쓸 수 있지만 이번 강의에서는 결합하지 않습니다.

| 자주 나는 오류 | 원인 → 해결 |
| --- | --- |
| `OPENAI_API_KEY`가 없음 | `.env` 확인, 코드에 키를 적거나 출력하지 않기 |
| history 입력 변수가 없다는 오류 | Placeholder 이름과 같은 `history` 키를 입력 dict에 넣기 |
| history **객체**를 Placeholder에 전달 | `list(history.messages)` 메시지 목록 전달 |
| 현재 질문이 두 번 들어감 | 이전 history로 먼저 호출하고, 호출 후 질문·답변 저장 |
| 다른 사용자가 같은 session_id | 분리할 대화에는 서로 다른 session_id |
| 재실행하니 history가 사라짐 | dict + InMemory 저장이라 정상 |
| RunnableWithMessageHistory 폐기 예정 경고 | 현재 버전의 정상 경고. 명시적 조회·주입·갱신으로 연습 |

## 확인 문제

모두 API 없이 풀 수 있습니다. `from langchain_core.messages import AIMessage, HumanMessage`, `from langchain_core.chat_history import InMemoryChatMessageHistory`, `from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder`가 되어 있고, `get_session_history`, `add_turn`은 위 요약의 코드 그대로라고 가정합니다. 각 문제 바로 아래에 정답과 해설이 있습니다. 먼저 풀어 본 뒤 확인하세요.

### 7-Q1. 메시지 객체와 문자열 (7-1)

```python
plain = "Runnable은 무엇인가요?"
q = HumanMessage(content="Runnable은 무엇인가요?")
a = AIMessage(content="공통 실행 인터페이스입니다.")
print(type(plain).__name__, type(q).__name__, type(a).__name__)
print(q.type, a.type)
print(q.content == plain)
```

세 줄의 출력을 쓰세요. 그리고 대화 기록에 `plain` 대신 `q`를 저장해야 하는 이유를 한 문장으로 쓰세요.

> 힌트: `type(x).__name__`은 클래스 이름, `.type`은 역할 이름입니다.

<details>
<summary>정답 보기</summary>

```text
str HumanMessage AIMessage
human ai
True
```

본문(`content`)은 같지만 문자열에는 **누가 말했는지(역할)** 정보가 없습니다. 대화 기록은 사용자 발화와 AI 답변을 구분해야 하므로 역할을 가진 메시지 객체로 저장합니다.

</details>

### 7-Q2. 메시지 수 추적 (7-1)

```python
store = {}
add_turn(store, "s1", "질문1", "답변1")
add_turn(store, "s1", "질문2", "답변2")
add_turn(store, "s2", "질문A", "답변A")
h = get_session_history(store, "s3")
print(len(store["s1"].messages), len(store["s2"].messages), len(h.messages))
print(sorted(store.keys()))
print(store["s1"].messages[2].content, store["s1"].messages[-1].type)
```

> 힌트: 대화 1회 = 메시지 2개. `get_session_history`는 처음 보는 ID도 저장소에 등록합니다.

<details>
<summary>정답 보기</summary>

```text
4 2 0
['s1', 's2', 's3']
질문2 ai
```

s1은 대화 2회라 4개, s2는 2개입니다. s3은 조회만 했지만 처음 보는 ID라 **빈 history가 새로 만들어져 저장소에 등록**됩니다. s1의 인덱스 2는 두 번째 질문, 마지막(-1)은 두 번째 답변(`ai`)입니다.

</details>

### 7-Q3. 버그 찾기 — 기록이 계속 사라짐 (7-1)

```python
def get_session_history_bad(store, session_id):
    store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

store = {}
get_session_history_bad(store, "u1").add_messages(
    [HumanMessage(content="안녕"), AIMessage(content="안녕하세요")]
)
print(len(get_session_history_bad(store, "u1").messages))
```

출력은 무엇이고, 왜 그런가요? 고친 코드를 쓰세요.

> 힌트: 두 번째 호출에서 `store["u1"]`에 무슨 일이 일어나나요?

<details>
<summary>정답 보기</summary>

출력은 `0`입니다. 호출할 때마다 **무조건 새 history로 덮어쓰기** 때문에 앞에서 저장한 두 메시지가 사라집니다 (7-1 오류 5).

```python
def get_session_history(store, session_id):
    if session_id not in store:                  # 처음 보는 ID일 때만 생성
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]                     # 있으면 기존 객체 반환
```

</details>

### 7-Q4. 같은 객체인가? (7-1)

```python
store = {}
x = get_session_history(store, "team-a")
y = get_session_history(store, "team-a")
z = get_session_history(store, "team-b")
x.add_messages([HumanMessage(content="Q"), AIMessage(content="A")])
print(x is y, x is z)
print(len(y.messages), len(z.messages))
```

> 힌트: `y`에는 직접 아무것도 추가하지 않았습니다.

<details>
<summary>정답 보기</summary>

```text
True False
2 0
```

`x`와 `y`는 **같은 history 객체**를 가리키므로 `x`에 추가한 메시지가 `y`에서도 보입니다. `team-b`는 별도 객체라 0개입니다. 같은 session_id가 같은 객체를 돌려줘야 앞선 대화가 이어집니다.

</details>

### 7-Q5. Prompt 메시지 순서 (7-2)

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "간단히 답하세요."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{question}"),
])
msgs = prompt.format_messages(
    history=[HumanMessage(content="제 이름은 수진입니다."), AIMessage(content="수진님, 반갑습니다.")],
    question="제 이름이 뭐였나요?",
)
for m in msgs:
    print(f"{m.type}: {m.content}")
print(len(msgs))
```

그리고 `history=[]`로 바꾸면 메시지는 몇 개가 되나요?

> 힌트: Placeholder 자리에 목록이 "펼쳐져" 들어갑니다.

<details>
<summary>정답 보기</summary>

```text
system: 간단히 답하세요.
human: 제 이름은 수진입니다.
ai: 수진님, 반갑습니다.
human: 제 이름이 뭐였나요?
4
```

`history=[]`이면 Placeholder 자리가 비어 system + human 두 개가 됩니다. 첫 대화(이전 기록 없음)에서 이렇게 동작합니다.

</details>

### 7-Q6. 버그 찾기 — Placeholder 입력 (7-2)

`history = get_session_history(store, "student-a")`일 때, 아래 두 호출이 왜 잘못인지 각각 쓰고 고치세요.

```python
chain.invoke({"question": "제 이름이 뭐였나요?"})                        # (가)
chain.invoke({"history": history, "question": "제 이름이 뭐였나요?"})    # (나)
```

> 힌트: Prompt에 `MessagesPlaceholder(variable_name="history")`가 있습니다. Placeholder는 무엇의 목록을 받나요?

<details>
<summary>정답 보기</summary>

(가) Prompt에 `history` 변수가 있는데 입력에 `history` 키가 없어 `KeyError: Input to ChatPromptTemplate is missing variables {'history'}`가 납니다 (7-2 오류 2). (나) history **객체**를 넘겨 `ValueError: variable history should be a list of base messages`가 납니다. Placeholder에는 메시지 **목록**이 들어가야 합니다 (7-2 오류 3).

```python
chain.invoke({
    "history": list(history.messages),     # 메시지 목록, 키 이름은 Placeholder와 동일
    "question": "제 이름이 뭐였나요?",
})
```

</details>

### 7-Q7. 질문이 두 번 들어가는 경우 (7-2)

모델 대신 Prompt만 확인합니다. `history`에는 이미 대화 1회(메시지 2개)가 있습니다.

```python
question = "두 번째 질문"
history.add_messages([HumanMessage(content=question)])          # 호출 전에 미리 저장
msgs = prompt.format_messages(history=list(history.messages), question=question)
print(len(msgs))
print([m.type for m in msgs])
```

7-Q5의 Prompt를 쓴다고 할 때 출력은? 무엇이 문제이고 어떻게 고쳐야 하나요?

> 힌트: 현재 질문이 history 안에도, `{question}`에도 있습니다.

<details>
<summary>정답 보기</summary>

```text
5
['system', 'human', 'ai', 'human', 'human']
```

현재 질문 `"두 번째 질문"`이 history 끝과 human 템플릿에 **두 번** 들어갑니다. 해결: 호출 전에는 저장하지 말고 **이전 history로 먼저 모델을 호출한 뒤**, 질문과 답변을 한 쌍으로 저장합니다 (7-2 오류 4).

</details>

### 7-Q8. 오프라인 대화 흐름 추적 (7-2)

모델 대신 고정 답변 함수를 씁니다.

```python
def ask_offline(history, question):
    previous_count = len(history.messages)
    answer = f"이전 메시지 {previous_count}개 · 질문: {question}"
    history.add_messages([HumanMessage(content=question), AIMessage(content=answer)])
    return answer

h = InMemoryChatMessageHistory()
print(ask_offline(h, "첫 질문"))
print(ask_offline(h, "두 번째 질문"))
print(ask_offline(h, "세 번째 질문"))
print(len(h.messages))
```

> 힌트: `previous_count`는 새 질문을 저장하기 **전에** 셉니다.

<details>
<summary>정답 보기</summary>

```text
이전 메시지 0개 · 질문: 첫 질문
이전 메시지 2개 · 질문: 두 번째 질문
이전 메시지 4개 · 질문: 세 번째 질문
6
```

매 호출에서 "이전 기록 조회 → 답변 생성 → 한 쌍 저장" 순서가 지켜져서, 다음 호출이 볼 수 있는 이전 메시지가 2개씩 늘어납니다. 실제 `ask_session()`도 같은 순서입니다.

</details>

### 7-Q9. 호출 횟수와 결과 (7-2)

7-2 완성 실습처럼 `ask_session()`을 아래 순서로 호출합니다.

```python
ask_session(chain, store, "student-a", "제 이름은 민지입니다. 기억해 주세요.")
ask_session(chain, store, "student-b", "LCEL은 무엇인가요?")
ask_session(chain, store, "student-a", "제가 앞에서 말한 이름은 무엇인가요?")
ask_session(chain, store, "student-b", "제 이름이 뭐였나요?")
```

(1) OpenAI API는 몇 번 호출되나요? (2) 마지막에 student-a, student-b의 메시지 수는? (3) 세 번째 호출의 Prompt에 들어가는 메시지 수는? (4) 네 번째 호출에서 모델이 "민지"라고 답할 근거가 있나요?

> 힌트: 세 번째 호출 시점의 student-a history에는 대화 1회가 있습니다.

<details>
<summary>정답 보기</summary>

(1) `ask_session` 1회 = 모델 1회 → **4회**. (2) student-a **4개**, student-b **4개** (각 대화 2회). (3) system 1 + 이전 메시지 2 + 현재 질문 1 = **4개**. (4) **없습니다.** student-b의 history에는 student-a가 말한 이름이 없습니다. session_id가 다르면 기록이 섞이지 않습니다.

</details>

### 7-Q10. RunnableWithMessageHistory 계약 (7-2)

(1) 기존 래퍼가 요구한 4요소를 쓰세요. (2) 아래 호출에서 빈칸을 채우세요. (3) 이번 강의 완성 실습이 이 래퍼를 쓰지 않은 이유는?

```python
legacy_chain.invoke(
    {"____": "제 이름이 뭐였나요?"},
    config={"____": {"____": "student-a"}},
)
```

> 힌트: session_id는 입력 dict가 아니라 config에 들어갑니다.

<details>
<summary>정답 보기</summary>

(1) 감쌀 기본 Runnable · session_id로 history를 반환하는 함수 · 현재 질문이 든 입력 키(`input_messages_key`) · 과거 메시지가 들어갈 키(`history_messages_key`). (2) `{"question": ...}`, `config={"configurable": {"session_id": "student-a"}}`. (3) `langchain-core`에서 **1.3.3부터 폐기 예정, 2.0.0에서 제거 예정**이고, 입문 단계에서는 history가 언제 조회·주입·갱신되는지 코드로 직접 보는 것이 목표이기 때문입니다. 대체 방식(LangGraph persistence)은 후속 과정입니다.

</details>

### 7-Q11. Retriever? history? (7-2)

각 요청에 필요한 것이 Retriever인지 대화 history인지 고르세요.

1. "사내 휴가 규정 문서에서 연차 이월 기준을 알려 주세요."
2. "아까 제가 말한 프로젝트 마감일이 언제였죠?"
3. "방금 설명한 내용을 한 줄로 다시 요약해 주세요."
4. "LangChain 공식 문서 중 Parser 관련 부분을 찾아 주세요."

> 힌트: 외부 문서 vs 현재 세션의 이전 발화.

<details>
<summary>정답 보기</summary>

1 Retriever (외부 문서 검색) · 2 history (현재 세션의 앞선 발화) · 3 history (직전 AI 답변을 읽어야 함) · 4 Retriever (외부 문서 검색). Retriever의 결과는 `Document` 목록, history의 결과는 `BaseMessage` 목록입니다.

</details>

### 7-Q12. 개념 O/X (7장 전체)

1. history에 대화를 저장해 두기만 하면 다음 호출에서 모델이 자동으로 이전 대화를 안다.
2. `InMemoryChatMessageHistory`의 기록은 프로그램을 다시 실행해도 남아 있다.
3. `session_id`는 대화 내용을 저장하는 객체다.
4. Prompt 순서는 system → history → 현재 질문으로 고정한다.
5. 7-2 완성 실습에서 현재 질문은 모델 호출 **전에** history에 저장한다.
6. Retriever는 사용자가 앞에서 한 말을 기억해 준다.
7. 7-1 실습은 OpenAI API Key 없이 실행된다.

> 힌트: 저장 vs 주입, 메모리 저장의 한계, 저장 시점을 떠올려 보세요.

<details>
<summary>정답 보기</summary>

1 X (매 호출마다 Prompt에 직접 넣어야 함) · 2 X (프로세스 메모리에만 있음) · 3 X (history를 찾는 **키**) · 4 O · 5 X (호출 **후** 질문·답변을 한 쌍으로 저장) · 6 X (외부 문서 검색용) · 7 O (모델 호출 없음)

</details>
