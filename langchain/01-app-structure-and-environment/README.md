# Chapter 1: 단순 API 호출과 LangChain 앱 구조, 그리고 개발 환경

> 2026-09-29 학습 기록. 1-1강(단순 API 호출과 LangChain 앱 구조 비교), 1-2강(패키지 구조와 개발 환경 설정) 이론을 정리했습니다. 1장 통합 실습 노트북은 받았지만 TODO 1~3이 아직 `NotImplementedError` 상태로 **미완료**이며 주말 backlog로 이월했습니다.

## Learning Goals

- OpenAI SDK 직접 호출과 LangChain 호출의 공통점·차이점을 설명한다.
- LangChain 기본 흐름 `Prompt → Model → Parser`를 순서대로 설명한다.
- `langchain` / `langchain-core` / `langchain-openai`의 역할 차이를 구분한다.
- uv로 Python 3.12 프로젝트 환경을 만들고 올바른 인터프리터를 선택한다.
- API Key를 `.env`로 분리하고 `.gitignore`로 추적에서 제외한다.
- `ChatOpenAI`의 기본 호출로 `AIMessage`를 받아 본문을 확인한다.
- 앱의 복잡도에 따라 직접 호출과 LangChain 중 무엇이 적합한지 판단한다.

## Practice Files

| Lesson | File | Practice status |
| --- | --- | --- |
| 1장 통합 | `01-direct-call-vs-langchain-starter.ipynb` | **미완료** — 모든 코드 셀의 `execution_count`가 비어 있고 출력이 없음. TODO 1~3(`ask_direct`, `ask_langchain`, `check_answers`)이 `raise NotImplementedError` 상태 |

노트북은 같은 사내 안내문·질문을 **두 방식으로 처리해 결과를 비교**하는 구조다. 고정 입력은 `DOCUMENT`, `QUESTION`, `SYSTEM`, `USER_TEMPLATE = "안내문: {document}\n질문: {question}"`이며 채워야 할 부분은 세 군데다.

1. `ask_direct(client, document, question)` — OpenAI SDK용 메시지 목록을 만들고 첫 응답 후보의 본문을 반환
2. `ask_langchain(model, document, question)` — 역할별 메시지 → 모델 응답 → 문자열 순으로 만들고 마지막 두 값을 반환
3. `check_answers(direct_answer, chain_answer)` — 두 값의 문자열 여부와 빈 값을 확인해 `direct`/`langchain` 딕셔너리로 반환

## Core Theory

### 1. LangChain이 필요해지는 지점 (1-1강)

질문 하나를 보내고 문자열 하나를 받는 프로그램은 OpenAI SDK만으로 충분하다. 문제는 프로그램이 커질 때다 — 프롬프트를 바꾸거나, 모델을 교체하거나, 답변을 리스트·딕셔너리로 바꿔야 할 때 모든 로직이 한 함수에 섞여 있으면 작은 변경에도 전체를 다시 읽어야 한다.

LangChain은 모델을 대신하는 또 다른 AI가 아니다. **LLM 애플리케이션의 여러 작업을 역할별 구성 요소로 나누어 연결하는 프레임워크**다. 같은 모델을 쓰므로 답변 품질이 저절로 좋아지지는 않는다. 달라지는 것은 코드를 구성하는 방식이다.

### 2. 직접 호출이 한 번에 맡는 세 가지 일

```python
messages = [system_message, user_message]                  # 입력 준비
response = client.chat.completions.create(model=..., messages=messages)  # 모델 실행
answer = response.choices[0].message.content               # 출력 정리
```

작은 프로그램에서는 이 구성이 가장 읽기 쉽다. 대신 프롬프트 방식이나 응답 구조가 바뀌면 메시지 생성 코드와 응답 추출 코드를 **직접 찾아** 고쳐야 한다.

### 3. LangChain의 세 단계

| 단계 | 받는 값 | 내보내는 값 | 한 문장 역할 |
| --- | --- | --- | --- |
| Prompt | 질문이 담긴 입력값 | 역할별 메시지 | 모델에게 보낼 내용을 만든다 |
| Model | 역할별 메시지 | `AIMessage` | LLM을 호출해 응답을 만든다 |
| Parser | `AIMessage` | 문자열 | 앱에서 쓰기 쉬운 값으로 바꾼다 |

```python
prompt = ChatPromptTemplate.from_messages([("system", "..."), ("human", "{question}")])
messages = prompt.format_messages(question="...")
ai_message = model.invoke(messages)
answer = StrOutputParser().invoke(ai_message)
```

`model.invoke()`의 결과는 문자열이 아니라 **`AIMessage`** 다. 본문 외에 모델 호출에 관한 부가 정보가 함께 들어갈 수 있다.

이 강의에서는 `prompt | model | parser` 파이프 문법을 쓰지 않고 한 단계씩 실행한다(LCEL과 `|`는 3장).

### 4. 두 방식 비교

| 비교 항목 | OpenAI SDK 직접 호출 | LangChain |
| --- | --- | --- |
| 메시지 구성 | 딕셔너리 목록을 직접 작성 | Prompt 객체가 생성 |
| 모델 호출 | SDK 클라이언트 직접 호출 | ChatModel의 `invoke()` |
| 결과 추출 | 응답 객체에서 직접 탐색 | Parser가 자료형 변환 |
| 코드 규모 | 작은 기능에서 짧다 | 단계가 많아질수록 구조가 선명 |
| 변경 범위 | 관련 코드를 찾아 수정 | 바뀌는 단계만 교체 |

두 방식의 답변 문장이 글자 단위로 같을 필요는 없다. 확인할 것은 **두 답변 모두 질문에 맞는가**, 그리고 **LangChain 코드에서 Prompt/Model/Parser 역할이 분리되어 있는가** 두 가지다.

### 5. 선택 기준

LangChain 쪽이 유리해지는 질문 세 가지 — 프롬프트가 여러 개이고 같은 형식으로 관리해야 하는가? 모델이나 출력 형식을 교체할 가능성이 있는가? 검색(Retriever)·대화 이력(Memory) 같은 단계를 연결할 계획이 있는가? 대부분 "예"라면 구조를 나누는 편이 낫고, 단순한 한 번의 호출이라면 직접 SDK가 더 읽기 쉽다.

`user`(OpenAI SDK)와 `human`(LangChain)은 같은 자리를 가리키는 서로 다른 이름이다.

### 6. 나중에 연결할 구성 요소

| 구성 요소 | 하는 일 | 다루는 시점 |
| --- | --- | --- |
| Retriever | 질문과 관련된 외부 문서를 찾는다 | 6장 |
| Memory | 같은 대화의 이전 메시지를 반영한다 | 7장 |
| Callback | 실행 중 이벤트를 관찰한다 | 8장 |

기본 흐름은 `사용자 입력 → Prompt → Model → Parser → 애플리케이션 결과`이고, 추가 요소는 이 흐름의 앞이나 바깥에 붙는다. 처음부터 전부 넣지 않고 세 단계가 정확히 도는지 먼저 확인한다.

### 7. 패키지 구조 (1-2강)

| 설치 이름 | 역할 | 대표 import |
| --- | --- | --- |
| `langchain` | 상위 수준 기능 | 후속 장에서 사용 |
| `langchain-core` | Prompt·Message·Parser 등 공통 구성 요소 | `from langchain_core...` |
| `langchain-openai` | OpenAI 모델을 ChatModel로 연결 | `from langchain_openai import ChatOpenAI` |
| `openai` | OpenAI 공식 Python SDK | `from openai import OpenAI` |
| `python-dotenv` | 로컬 `.env`를 환경변수로 로드 | `from dotenv import load_dotenv` |

`langchain-core`가 공통 연결 규격이라면 `langchain-openai`는 그 규격에 맞춘 OpenAI용 어댑터다. `python-dotenv`는 LangChain 패키지가 아니라 키를 코드 밖에 두기 위한 별도 도구다.

**설치 이름에는 하이픈, import 이름에는 언더스코어**가 들어간다(`langchain-core` → `langchain_core`, `python-dotenv` → `dotenv`). 이 차이를 모르면 설치는 됐는데 import가 실패했다고 오해하기 쉽다.

### 8. uv로 Python 3.12 환경 만들기

```powershell
uv python install 3.12
uv sync --locked --python 3.12
uv run python --version
uv run python -c "import sys; print(sys.executable)"
```

- `pyproject.toml`에는 직접 쓰는 패키지와 Python 조건이, `uv.lock`에는 간접 의존성까지 해석된 버전이 기록된다. `.python-version`과 함께 보관한다.
- 실행 경로가 현재 프로젝트의 `.venv\Scripts\python.exe`인지 확인한다.
- 가상환경 활성화 명령이나 실행 정책 변경은 필수 단계가 아니다.
- `uv pip check`로 의존성 충돌을 확인한다(정상이면 `All installed packages are compatible`).

수업 기준 버전: Python 3.12 / `langchain==1.3.14` / `langchain-core==1.5.1` / `langchain-openai==1.4.1` / `openai==2.48.0` / `python-dotenv==1.2.2` / `pydantic==2.13.5`.

`ModuleNotFoundError`가 나면 패키지 설치보다 **VS Code 인터프리터 선택(`Python: Select Interpreter` → `.venv`)** 을 먼저 확인한다.

### 9. API Key 관리

```text
OPENAI_API_KEY=발급받은_키
OPENAI_MODEL=gpt-5.6-luna
```

```python
load_dotenv()
print(bool(os.getenv("OPENAI_API_KEY")))   # 값이 아니라 존재 여부만 출력
```

- `.gitignore`에 `.env`, `.venv/`, `__pycache__/`를 넣는다.
- `.gitignore`는 **앞으로의 추적만** 막는다. 이미 올라간 키는 자동으로 무효화되지 않으므로 폐기하고 새로 발급해야 한다.
- 키 값을 코드·노트북 본문·실행 결과·캡처·과제 제출물에 넣지 않는다. 일부를 가리는 것으로는 해결되지 않는다.
- 터미널에 이미 설정된 환경변수는 `load_dotenv()` 기본 동작에서 `.env`보다 우선한다.

### 10. 기본 ChatModel 호출

```python
model = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-5.6-luna"),
    reasoning_effort="none",
    use_responses_api=False,
    max_completion_tokens=600,
    timeout=30,
    max_retries=0,
)
response = model.invoke("LangChain을 한 문장으로 소개해 주세요.")
print(response.content)
```

답변 문장은 실행할 때마다 달라진다. 확인할 것은 **인증 오류 없이 문자열 답변이 나오는가**이다. `max_retries=0`은 수업에서 재시도 동작을 숨기지 않기 위한 설정이다.

## Questions and Newly Learned Points

- "LangChain을 쓰면 코드가 더 길어졌다"는 첫 예제에서는 정상이다 — 장점은 한 번의 호출을 짧게 만드는 데 있지 않고, 단계가 늘어날 때 역할과 변경 지점을 분리하는 데 있다.
- 설치 이름과 import 이름이 다른 규칙(하이픈 ↔ 언더스코어)을 처음 명확히 정리했다.
- `.gitignore`가 이미 올라간 키를 지워 주지 않는다는 점 — 노출된 키는 폐기가 유일한 대응이다.
- `model.invoke()`가 문자열이 아니라 `AIMessage`를 돌려준다는 점이 Parser가 필요한 이유였다.
- 자주 하는 오해: "LangChain이 답변을 더 잘하게 만든다"(모델이 같다) / "설치했는데 import가 안 되면 재설치해야 한다"(인터프리터 선택 문제인 경우가 많다) / "두 방식의 답이 다르면 잘못된 것이다"(LLM 응답은 매번 달라질 수 있다).

## Environment

```bash
pip install -r requirements.txt
```
