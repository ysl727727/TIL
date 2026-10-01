# 10장. 통합 문서 Q&A 앱 — 설계 · 구현 · 관측과 경계

> 2026-10-01 학습 기록. 3\~9장에서 따로 배운 기능을 하나의 문서 Q&A 앱으로 묶는 마무리 장입니다. 단계별 계약을 먼저 설계하고, 검색 → Prompt → 구조화 검증 → 출처 검증 → 대화 저장 순서로 구현한 뒤, 오류 경로를 관측 기록으로 확인하고 LCEL과 LangGraph의 경계를 정리했습니다. 통합 실습(`starter.py`)의 TODO 1\~3도 함께 기록합니다.

## 학습 목표

- 기능을 필수 7개 / 선택 2개로 나누고, 단계마다 `name·input·output·responsibility` 계약을 적는다.
- "검색은 모델보다 먼저, 구조화 검증은 저장보다 먼저" 두 순서를 지킨다.
- 검색 0건이면 모델을 부르지 않고 `not_found`로 끝낸다.
- Parser 통과와 별개로 `sources`를 실제 검색 문서 ID와 대조하고, 모든 검증 뒤에만 대화를 저장한다.
- 제어(Retry·Fallback)와 관찰(`RunRecord`·Langfuse)을 나누고, 반복·재개·승인·영속 상태가 필요할 때만 LangGraph를 검토한다.

## 실습 파일

| 강 | 주제 | 실습 상태 |
| --- | --- | --- |
| 10-1 | 통합 앱 아키텍처 설계 | 📘 이론 정리 |
| 10-2 | 미니 챗봇 또는 문서 Q&A 앱 구현 | 📘 이론 정리 |
| 10-3 | 관측/오류 대응/LangGraph 연결 한계 정리 | 📘 이론 정리 |
| 통합 실습 | `starter.py` TODO 1\~3 (Prompt · 실행 · 출처 검증 후 저장) | 🧪 실습 진행 |

6\~10장은 이론 분량이 많아, 실습은 이 장의 통합 실습(`starter.py`) 하나로 진행했습니다. 실습 코드 파일은 이번 기록에 포함하지 않았고, 아래 "통합 실습" 절에 TODO 1\~3의 정답 코드와 해설을 정리했습니다.

## 전체 흐름

### 7\~10장 큰 그림

6장까지 만든 것은 **질문 하나를 넣으면 문서를 찾아 답 하나를 돌려주는 체인**이었습니다. 수업 예제로는 충분하지만, 실제 사람이 쓰는 서비스로 내놓으려면 문제가 네 가지 생깁니다. 7\~10장은 그 네 문제를 하나씩 푸는 이야기입니다.

| 실제로 써 보니 생긴 문제 | 해결하는 장 | 한마디로 |
| --- | --- | --- |
| "아까 제 이름 뭐라고 했죠?"에 답하지 못한다 | **7장 기억** | 대화를 저장해 두었다가, 다음 질문 때 **다시 넣어 준다** |
| 답이 다 만들어질 때까지 멍하니 기다린다. 안에서 무슨 일이 일어나는지도 모른다 | **8장 관찰** | 답은 **조각으로 바로 보여 주고**, 실행 과정은 **옆에서 기록**한다 |
| 모델이 잠깐만 멈춰도 앱 전체가 실패한다 | **9장 실패 대응** | **다시 하거나**(Retry) **다른 길로 가거나**(Fallback) **바로 멈춘다** |
| 배운 기능들이 전부 따로 논다 | **10장 통합** | **순서와 계약**을 먼저 설계하고 하나의 앱으로 잇는다 |

10장에서 완성되는 문서 Q&A 앱에 각 장이 어디를 담당하는지 표시하면 이렇습니다.

```text
                                       [9장] 모델이 실패하면 → 다시 하기(Retry) → 그래도 안 되면 대체 경로(Fallback)
                                                    │
질문 → 입력 확인 → 문서 검색 → 대화 기록 꺼내기 → Prompt 만들기 → 모델 호출 → 구조화 검증 → 출처 검증 → 대화 저장 → 화면 표시
              (6장)        (7장)          (질문+기록+문서)              (5장)        (10장)       (7장)     (8장 스트리밍)
   └──────────────────────────── [8장] 처음부터 끝까지 옆에서 관찰: 시작·완료·시간·토큰·trace ───────────────────────────┘

[10장] 이 순서 전체를 설계(10-1) → 구현(10-2) → 관찰하고 한계 정하기(10-3)
```

**한 문장으로:** 7장은 **기억**, 8장은 **관찰**, 9장은 **실패 대응**, 10장은 그 셋을 **조립**하는 장입니다.

### 모든 장에 반복되는 원칙 5가지

7\~10장은 새 클래스가 많이 나와서 어려워 보이지만, 밑에 깔린 생각은 몇 가지뿐입니다. 이 다섯 가지를 먼저 잡아 두면 디테일이 그 위에 붙습니다.

| 원칙 | 뜻 | 7\~10장에서 나오는 곳 |
| --- | --- | --- |
| ① 계약을 맞춘다 | 앞 단계의 출력(자료형·키 이름)이 다음 단계의 입력과 맞아야 한다 | 7-2 Placeholder 이름 = 입력 키 `history`, 10-1 `Stage`의 input/output |
| ② 반복에는 상한이 있다 | 다시 하는 횟수는 반드시 정해 둔다 | 9-1 `stop_after_attempt=2`, 8-2·9-1 `max_retries=0` |
| ③ 관찰자는 결과를 바꾸지 않는다 | 기록·관찰 도구는 보기만 하고, 답이나 실행 경로를 바꾸지 않는다 | 8-1 Callback, 8-2·10-3 Langfuse |
| ④ 검증된 것만 저장·표시한다 | 검사를 모두 통과한 답만 기록하고 보여 준다 | 7-2 호출 **후** 저장, 10-2 출처 검증 뒤 저장 |
| ⑤ 없는 값은 "없다"고 쓴다 | 모르는 값을 0이나 그럴듯한 값으로 채우지 않는다 | 8-2 토큰 "제공되지 않음", 10-2 `not_found`, 10-3 `not_available` |

이 원칙들은 3\~6장에서도 이미 나왔습니다. 3장의 "자료형 확인", 5-3의 "수정 요청 1회", 6-3의 "검색된 문서가 없습니다."가 같은 생각입니다.

### 한 문장

**지금까지 배운 부품을 "어떤 순서로, 무엇을 주고받으며" 잇는지 먼저 설계하고(10-1), 그대로 문서 Q&A 앱을 만들고(10-2), 오류 경로를 기록으로 확인한 뒤 LCEL로 충분한 범위를 정합니다(10-3).**

### 왜 필요한가

기능을 한 함수에 다 넣으면 돌아가기는 해도, 문제가 생겼을 때 **어느 단계가 무엇을 받아 무엇을 내보냈는지** 알 수 없습니다. 그래서 집을 짓기 전에 설계도부터 그립니다.

**비유:** 집 짓기. 설계도(10-1: 방 목록, 공사 순서, 점검표) → 시공(10-2: 실제로 짓기) → 준공 검사와 확장 판단(10-3: 하자 기록, "이 집을 더 키우려면 다른 공법이 필요한가?").

### 그림으로 보기 — 10-2 앱의 한 질문 처리

```text
app.ask(session_id, question)
 ① 입력 확인        공백이면 ValueError
 ② 문서 검색        ─┬─ 0건  → QAResponse(status="not_found", sources=[]) 로 즉시 끝  (모델 호출 X, 저장 X)
                     └─ 1건 이상 ↓
 ③ 대화 기록 꺼내기  최근 4개만 "사용자: … / 도우미: …" (없으면 "이전 대화 없음")
 ④ Prompt 만들기     이전 대화 + 문서 근거 + 현재 질문
 ⑤ 모델 + Parser     → QAResponse(status, answer, sources)
 ⑥ 출처 검증        sources가 실제로 검색한 문서 ID 안에 있나?  아니면 ValueError
 ⑦ 대화 저장        모든 검증을 통과한 뒤에만
 ⑧ 화면 표시        완성된 답을 단어 단위로 나눠 보여 주기 (모델 스트리밍 아님)
```

### 강의 흐름

1. **10-1 설계하기** — 기능을 "로컬에서 반드시 확인할 필수"와 "외부 설정이 필요한 선택"으로 나누고, 8단계를 `name / input / output / responsibility`로 적어 앞 단계 출력 = 다음 단계 입력인지 검토. **검색은 모델보다 먼저, 구조화 검증은 저장보다 먼저.** 정상·검색 0건·Retry 복구·Fallback의 기대 `status/route`를 구현 전에 고정.
2. **10-2 구현하기** — `DocumentQAApp.ask()` 안에서 입력 확인 → 검색 → (0건이면 `not_found`로 즉시 종료) → History 조회 → Prompt(`history`, `context`, `question`) → Model·Parser → `QAResponse` → 출처 검증(`issubset`) → 저장 → UI 표시용 조각.
3. **10-3 관측하고 경계 정하기** — 같은 Retry+Fallback 체인을 normal / temporary / persistent로 실행해 `RunRecord`로 기록. Langfuse는 선택, 실패해도 로컬 결과 유지. 반복·재개·사람 승인·영속 상태가 없으면 LCEL 유지.

```text
10-2  DocumentQAApp.ask(session_id, question)

  ① 입력 확인 ─ 공백이면 ValueError
  ② 문서 검색 (search_documents, top_k=2) ─┬─ 0건 → QAResponse(status="not_found", sources=[])  ← 모델 호출 X, 저장 X
                                          └─ 1건 이상 ↓
  ③ History 조회 (session_id별, 최근 4개 → "사용자: … / 도우미: …", 없으면 "이전 대화 없음")
  ④ Prompt: system(형식 안내) + human("이전 대화 / 문서 근거 / 현재 질문")
  ⑤ Model(offline 또는 live, max_retries=0) → PydanticOutputParser → QAResponse
  ⑥ 출처 검증: set(result.sources) ⊆ {실제 검색 문서 ID}  ─ 아니면 ValueError
  ⑦ History 저장 (Human 질문 + AI 답변)                     ← 모든 검증 뒤에만
  ⑧ UI 표시: 완성된 답을 단어 단위 조각으로 출력           ← 모델 토큰 스트리밍 아님

10-3  primary.with_retry(stop_after_attempt=2).with_fallbacks([fallback])
        normal     → ok / primary / attempts=1
        temporary  → ok / primary / attempts=2
        persistent → degraded / fallback / attempts=2
      관측(RunRecord, Langfuse)은 옆에서 기록만 ─ status·route·attempts를 바꾸지 않음
```

장 연결 정리: 6장 Retriever → `context`, 7장 History → `history`, 5장 구조화 출력 → `QAResponse`, 8장 관측 → `RunRecord`·Langfuse, 9장 Retry·Fallback → 모델 정책 단계. 10장은 새 기능보다 **이것들을 어떤 순서와 계약으로 잇는지**가 핵심입니다.

## 핵심 이론

### 1. 통합 앱 아키텍처 설계 (10-1강)

기능을 한 함수에 다 넣으면 실행은 돼도 어느 단계가 무엇을 받아 무엇을 돌려주는지 확인하기 어렵습니다. 그래서 책임을 나눕니다.

| 책임 | 받는 값 | 내보내는 값 |
| --- | --- | --- |
| 입력 확인 | 질문, session_id | 검증된 요청 |
| 대화 조회 | session_id | 이전 메시지 목록 |
| 문서 검색 | 질문 | Document 목록 |
| Prompt 구성 | 질문, 대화, 문서 | 모델 메시지 |
| 모델 정책 | 모델 메시지 | 모델 응답 |
| 구조화 검증 | 모델 응답 | `QAResponse` |
| 로컬 관측 | 실행 정보 | trace 레코드 |
| 대화 저장 | 검증된 질문과 답변 | 갱신된 메시지 목록 |

책임을 나누면 검색 방식을 바꿔도 대화 저장 코드는 그대로, 모델 응답 형식이 바뀌어도 입력 확인 코드는 그대로 둘 수 있습니다.

**필수 기능과 선택 기능**

| 필수 (7) — 로컬·오프라인으로 확인 | 선택 (2) — 외부 서비스·영구 저장 필요 |
| --- | --- |
| `question_input`, `retriever`, `prompt_model_parser`, `structured_output`, `session_history`, `retry_fallback`, `local_trace` | `langfuse_trace`, `persistent_storage` |

- `build_requirements()` → `{"app_type": "document_qa", "required": [...7개], "optional": [...2개]}` → 출력 `document_qa 7 2`.
- 개수는 중요도가 아니라 **범위가 섞이지 않았는지** 확인하는 값입니다. `required`는 구현 범위 목록이지 **실행 순서가 아닙니다**.
- `langfuse_trace` 같은 외부 전송 기능은 패키지·키가 있다는 이유만으로 자동 활성화하지 않고, 업로드 동의·지역·인증·전송 범위를 따로 확인합니다. 연결 실패가 필수 앱 결과를 바꾸지 않게 경계를 둡니다.

**단계별 데이터 계약 (`Stage`)**

```python
from typing import TypedDict

class Stage(TypedDict):
    name: str             # 실행 순서·오류 위치를 식별할 이름
    input: str            # 받기로 약속한 값
    output: str           # 다음 단계에 줄 값
    responsibility: str   # 이 단계만 담당할 작업
```

`TypedDict`는 실행 객체를 만들지 않고, 단계 설명 dict에 필요한 키를 코드에 드러냅니다.

| 순서 | name | input | output |
| --- | --- | --- | --- |
| 1 | `input_check` | question + session_id | validated request |
| 2 | `history_read` | session_id | message list |
| 3 | `retrieve` | question | `list[Document]` |
| 4 | `prompt` | 질문·대화·문서 | 모델 메시지 |
| 5 | `model_policy` | 모델 메시지 | 모델 응답 |
| 6 | `structured_parser` | 모델 응답 | `QAResponse` |
| 7 | `local_trace` | 실행 정보 | trace 레코드 |
| 8 | `history_save` | 검증된 질문·답변 | 갱신된 메시지 목록 |

**단계 순서 검증 (`validate_stage_plan`)**

```python
names = [stage["name"] for stage in stages]
if set(names) != required_names:                                     # 존재 여부 (집합)
    raise ValueError("필수 단계 구성이 올바르지 않습니다.")
if names.index("retrieve") > names.index("model_policy"):            # 순서 ①
    raise ValueError("Retriever는 Model보다 먼저 실행되어야 합니다.")
if names.index("structured_parser") > names.index("history_save"):   # 순서 ②
    raise ValueError("Structured Parser는 History 저장보다 먼저 실행되어야 합니다.")
```

- 집합 검사 = 빠지거나 추가된 단계, `index()` 비교 = 실행 순서.
- ① 모델이 검색 근거를 읽게 하고, ② 검증되지 않은 답이 대화 기록에 저장되지 않게 합니다.

**정상 경로와 실패 경로**

| 사례 | 모델 호출 | 기대 status | 기대 route |
| --- | --- | --- | --- |
| `normal` (정상 검색) | 실행 | `grounded` | `primary` |
| `no_document` (검색 0건) | **생략** | `not_found` | `local` |
| `retry_recovered` (일시 오류 뒤 복구) | 다시 실행 | `grounded` | `primary` |
| `fallback` (Primary 지속 실패) | Fallback 실행 | `degraded` | `fallback` |

- 검색 결과가 없는데 모델을 부르면 제공 문서가 아닌 **일반 지식으로 답할 수 있어서**, 0건은 모델 정책 단계로 가지 않고 로컬 안내로 끝냅니다. Retry·Fallback은 검색 결과가 있고 모델 단계에 도달했을 때만 적용됩니다.
- Retry 안에서 Primary가 성공했으면 최종 경로는 여전히 **`primary`**입니다. 시도를 모두 실패해 대체 체인이 실행된 경우에만 `fallback`.
- 테스트 행렬(`TestCase`: `name`, `expected_status`, `expected_route`)을 구현 전에 고정하고, 각 테스트는 **새 앱 상태**에서 시작합니다 (이전 대화 기록·호출 횟수가 남으면 비교가 틀어짐).
- 완성 실습 출력: `app=document_qa required=7 optional=2` / `stages=8 first=input_check last=history_save` / `cases=4 names=normal,no_document,retry_recovered,fallback` / `architecture_contracts_passed=True`. API Key 불필요.

| 자주 발생하는 오류 | 원인 → 해결 |
| --- | --- |
| 필수 기능 목록을 실행 순서로 생각 | 순서는 `build_stage_plan()`의 단계 목록 |
| 검색을 모델 뒤에 배치 | `retrieve`가 `model_policy`보다 먼저 |
| 모델 응답을 검증 전에 저장 | `structured_parser` 뒤에 `history_save` |
| 검색 0건도 모델 실패로 분류 | 모델 예외가 아님 → `not_found` / `local` |
| Retry 복구를 Fallback 성공으로 기록 | Primary가 성공했으면 `primary` |
| 선택 기능이 없으면 실행 불가라고 생각 | 로컬 관측 + 인메모리 History로 핵심 흐름 실행 가능 |

### 2. 미니 챗봇 또는 문서 Q&A 앱 구현 (10-2강)

| 순서 | 단계 | 핵심 결과 |
| --- | --- | --- |
| 1 | 입력 확인 | 비어 있지 않은 질문과 session_id |
| 2 | 문서 검색 | 관련 Document 목록 |
| 3 | 검색 0건 확인 | 모델 호출 또는 `not_found` 종료 |
| 4 | 대화 조회 | 현재 세션의 최근 메시지 |
| 5 | Prompt 구성 | 질문, History, context |
| 6 | Model·Parser | `QAResponse` |
| 7 | 출처 검증 | 검색 결과 안의 문서 ID |
| 8 | 대화 저장 | 검증된 질문과 답변 |
| 9 | UI 표시 | 답변 문자열 조각 |

**QAResponse — 모든 종료 경로가 쓰는 하나의 계약**

```python
from typing import Literal
from pydantic import BaseModel, model_validator

class QAResponse(BaseModel):
    status: Literal["grounded", "not_found"]   # 검색 근거 사용 여부
    answer: str                                # 사용자에게 보여 줄 최종 답변
    sources: list[str]                         # 사용한 문서 ID

    @model_validator(mode="after")
    def validate_sources(self) -> "QAResponse":
        if self.status == "grounded" and not self.sources:
            raise ValueError("grounded 결과에는 하나 이상의 출처가 필요합니다.")
        if self.status == "not_found" and self.sources:
            raise ValueError("not_found 결과에는 출처를 넣을 수 없습니다.")
        return self
```

- 정상 조합은 두 가지뿐: `grounded` + 출처 1개 이상, `not_found` + 빈 목록.
- `@model_validator(mode="after")`는 필드 하나가 아니라 **필드 사이의 관계**(상태 ↔ 출처)를 검사합니다. Pydantic 검증이 JSON 모양만이 아니라 앱의 업무 규칙까지 확인하는 예입니다.

**제공 뼈대로 검색 준비** — 문서 3개(LCEL, Memory, Retriever)가 코드 안에 있고, `search_documents(question, documents, top_k=2)`는 질문에 포함된 metadata 키워드 수로 점수 → 1점 이상만 점수순(동점은 원래 순서) 반환 (6-2와 같은 규칙). `"Retriever는 문서를 어떻게 검색하나요?"` → `['doc-003']`. `format_context()`는 ID·제목·본문을 Prompt용 문자열로 만듭니다.

**제공 뼈대로 Prompt·Model·Parser 연결**

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "문서 근거 안에서 답하고 사용한 문서 ID를 sources에 넣으세요. "
               "다음 출력 형식을 지키세요.\n{format_instructions}"),
    ("human", "이전 대화:\n{history}\n\n문서 근거:\n{context}\n\n현재 질문:\n{question}"),
]).partial(format_instructions=parser.get_format_instructions())   # 안 바뀌는 값은 미리 고정
```

- `.partial()`로 실행마다 바뀌지 않는 스키마 안내를 미리 채워 두면, 실행 때는 `history`, `context`, `question`만 넘기면 됩니다.
- `history` = 현재 세션의 앞선 대화, `context` = 현재 질문으로 검색한 외부 문서. **서로 대신할 수 없습니다** (7-2의 Retriever vs history).

| 조건 | 선택 체인 | 모델 호출 |
| --- | --- | --- |
| `OPENAI_API_KEY` 없음 | `build_offline_chain()` — Prompt 속 문서 ID를 읽어 결정적 JSON 생성 | 없음 |
| `OPENAI_API_KEY` 있음 | `build_live_chain()` — `ChatOpenAI(timeout=20, max_retries=0, use_responses_api=True)` | 실제 호출 시도 |

두 체인 모두 `dict[str, str]`을 받아 `QAResponse`를 반환하므로 `DocumentQAApp`은 어느 쪽인지 알 필요가 없습니다. 오프라인 체인은 계약·연결 순서 확인용이지 **답변 품질 평가용이 아닙니다**.

**세션 History와 검색 근거 구분**

- `histories: dict[str, InMemoryChatMessageHistory]` + `get_history(session_id)` (7-1과 같은 패턴). 세션 A의 History는 세션 B의 Prompt에 들어가지 않지만, 문서 목록은 모든 세션이 함께 씁니다.
- `format_history()`: 메시지가 없으면 `"이전 대화 없음"`, 있으면 **최근 4개**(`messages[-4:]`)만 `"사용자: …"` / `"도우미: …"` 줄로 만듭니다.

**출처 검증 뒤 대화 저장**

```python
allowed_sources = {str(d.metadata["document_id"]) for d in found_documents}
if not set(result.sources).issubset(allowed_sources):
    raise ValueError("응답 출처가 실제 검색 결과와 일치하지 않습니다.")
history.add_messages([HumanMessage(content=question), AIMessage(content=result.answer)])
```

- 모델이 `sources=["doc-999"]`를 돌려줘도 Parser는 "문자열 목록"이라 통과시킵니다. **실제로 검색한 문서인지**는 앱이 `issubset()`으로 따로 대조합니다.
- 모든 검증을 통과한 뒤에만 저장합니다. 잘못된 답을 먼저 저장하면 다음 질문의 History에 섞입니다. `not_found` 경로는 History를 만들거나 저장하지 않습니다.

**UI 표시용 조각** — `stream_validated_answer(answer)`는 `answer.split()`의 각 단어 뒤에 공백을 붙여 `yield`합니다. Model·Parser·검증이 **모두 끝난 완성 문자열**을 터미널에 점진적으로 보여 줄 뿐, 8장의 모델 토큰 스트리밍과는 실행 시점이 다릅니다.

- 오프라인 예상 출력: `mode=offline` / `status=grounded` / `sources=doc-003` / `answer=Retriever는 질문과 관련된 외부 문서를 찾습니다.`
- API Key 문자열이 있다 ≠ live 성공. 인증·결제·사용 한도·모델 권한·네트워크가 모두 준비되고, 구조화 응답과 출처 검증까지 통과해야 성공입니다. ChatGPT 구독과 API 과금은 별도.
- 과금 없이 반복하려면 **터미널 환경변수와 `.env` 양쪽**에서 키를 없애야 합니다. 터미널에서만 지우면 `load_dotenv()`가 `.env`를 다시 읽어 live가 선택됩니다.
- 같은 대화를 이어 가려면 **같은 `DocumentQAApp` 객체 + 같은 session_id**. 독립 테스트할 때만 새 앱을 만듭니다.

| 자주 발생하는 오류 | 원인 → 해결 |
| --- | --- |
| 검색 결과가 없는데 모델 호출 | `QAResponse(status="not_found", sources=[])` 즉시 반환 |
| History와 검색 문서를 같은 값으로 생각 | Prompt의 다른 영역으로 전달 |
| Parser 통과 = 출처가 맞다 | `allowed_sources`와 별도 대조 |
| 검증 전에 History 저장 | 모든 검증 뒤에 질문+답변 함께 저장 |
| UI 조각을 모델 토큰 스트리밍이라 설명 | 완성·검증된 문자열을 나눈 것 |
| 오프라인 체인으로 답변 품질 평가 | 계약 확인용일 뿐 |
| 질문마다 새 앱을 만들어 History 유실 | 같은 앱 객체 + 같은 session_id |
| 키 문자열이 있으면 live도 성공 | 인증·결제·권한·출처 검증까지 끝나야 성공 |
| ChatGPT 구독에 API 사용량 포함 | 별도 과금 |

### 3. 관측/오류 대응/LangGraph 연결 한계 정리 (10-3강)

| 구성 요소 | 역할 | 앱 결과를 결정하는가 |
| --- | --- | --- |
| `with_retry()` | 지정 오류에서 Primary를 제한적으로 다시 실행 | 예 |
| `with_fallbacks()` | Retry 소진 시 대체 결과 반환 | 예 |
| `RunRecord` | 최종 경로와 Primary 시도 횟수를 로컬에 기록 | 아니요 |
| Langfuse Callback | 같은 실행 이벤트를 선택적으로 관찰 | 아니요 |
| `choose_orchestration()` | 요구사항을 LCEL / LangGraph 경계에 대조 | 실행 전 설계 판단 |

오류 대응(Retry·Fallback)은 **실행을 제어**하고, 관측은 **실행을 바라봅니다**. Langfuse를 붙여도 최대 시도 횟수나 Fallback 이동 조건은 바뀌지 않습니다.

**최소 관측 레코드**

```python
class ObservedAnswer(BaseModel):          # 사용자에게 전달할 결과
    status: Literal["ok", "degraded"]
    route: Literal["primary", "fallback"]
    answer: str

class RunRecord(BaseModel):               # 실행을 설명하는 최소 관측 정보
    case: Literal["normal", "temporary", "persistent"]
    status: Literal["ok", "degraded"]
    route: Literal["primary", "fallback"]
    attempts: int                          # Primary 실제 호출 횟수
    latency_ms: float                      # 시작~최종 결과 경과 시간
    token_usage: Literal["not_available"]  # 로컬 Runnable엔 토큰 정보 없음
```

- 질문 원문·답변 원문·비밀 키·상세 오류 메시지는 레코드에 **넣지 않습니다**. 목적(오류 정책 경로 확인)에 필요한 필드만 저장.

**세 사례 비교** — `RunnableLambda(primary).with_retry(retry_if_exception_type=(TemporaryRunError,), stop_after_attempt=2, wait_exponential_jitter=False).with_fallbacks([RunnableLambda(fallback)], exceptions_to_handle=(TemporaryRunError,))`, 사례마다 **새 체인**(호출 횟수 누적 방지).

| 사례 | Primary 동작 | 최종 경로 | attempts | Fallback 호출 |
| --- | --- | --- | --- | --- |
| `normal` | 첫 시도 성공 | primary | 1 | 0 |
| `temporary` | 첫 시도 실패, 둘째 성공 | primary | 2 | 0 |
| `persistent` | 두 시도 모두 실패 | fallback | 2 | 1 |

temporary와 persistent는 같은 오류 타입이고 발생 횟수만 다릅니다. 비교 포인트는 "허용한 시도 안에서 회복했는가"입니다.

**실행 시간과 토큰 정보**

| 값 | 해석 |
| --- | --- |
| `attempts` | 사례별 1 또는 2가 되어야 하는 **결정적인** 정책 값 |
| `route` | 실제 결과를 만든 경로 |
| `latency_ms` | 실행마다 달라지는 측정값 → 0 이상인지만 확인, 특정 숫자 고정 X |
| `token_usage` | 로컬 Runnable은 `not_available` |

토큰 정보가 없다는 사실을 0으로 바꾸면 "토큰을 전혀 쓰지 않았다"는 **다른 뜻**이 됩니다. 문자 수로 추측하지도 않습니다.

**Langfuse 선택 연결과 관측 실패에서 앱 결과 지키기**

- 8-2와 같은 조건: `ENABLE_LANGFUSE_UPLOAD=1` + 세 설정 + 패키지 + `auth_check()`. 하나라도 없으면 `(None, None)`으로 로컬 관측 계속. 동의가 없으면 키가 남아 있어도 원격 Handler를 만들지 않습니다.
- Callback이 있을 때만 `config={"callbacks": [callback]}`, 없으면 `config=None`. Callback은 Runnable을 한 번 더 호출하지 않고, 연결 여부가 `status/route/attempts`를 정하지 않습니다.
- `flush_langfuse(client)`: `client is None`이면 `False`, `flush()` 예외는 잡아서 종류만 출력하고 `False`, 성공하면 `True`. **넓은 `except Exception`은 관측 도구 경계에만** 둡니다. `chain.invoke()`까지 같은 `try`로 감싸면 Primary의 실제 오류가 관측 실패처럼 숨겨집니다.
- 각 `run_case()` 직후 `last_trace_id`를 저장 → 세 실행 뒤 `flush()` → trace별 observation 재조회(2초 간격 최대 31회, 약 60초). 조회 전에 normal/temporary/persistent가 정확히 한 번씩, trace ID 세 개가 서로 다른지도 확인합니다.
- 10-3은 ChatModel이 아니라 로컬 `RunnableLambda`를 관찰하므로 `type="GENERATION"`으로 제한하지 않고 observation이 한 건 이상 있는지 확인합니다. 원격 조회가 실패해도 로컬 `RunRecord`와 앱 결과는 유지됩니다.

**LCEL로 충분한 흐름 vs LangGraph를 검토할 경계**

다음을 모두 만족하면 LCEL Runnable 조합으로 유지합니다: 한 요청 안에서 시작·종료 / 앞에서 뒤로 진행 / Retry 횟수가 작고 명확히 제한 / 사람 승인을 기다리며 멈추지 않음 / 프로세스가 끝난 뒤 중간 상태를 복원할 필요 없음.

| 요구 | False인 현재 경량 앱 | True가 되는 예 |
| --- | --- | --- |
| `needs_loop` | 한 번의 Retry 정책 뒤 종료 | 검색 결과를 평가해 질문을 바꾸고 다시 검색 |
| `needs_resume` | 한 요청 안에서 완료 | 실행을 중단하고 나중에 이어서 처리 |
| `needs_human_approval` | 자동으로 결과 반환 | 담당자 승인 뒤 다음 단계 실행 |
| `needs_persistent_state` | 프로세스 안의 임시 상태 | 재시작 뒤에도 중간 상태 복원 |

```python
def choose_orchestration(*, needs_loop, needs_resume, needs_human_approval, needs_persistent_state):
    if any((needs_loop, needs_resume, needs_human_approval, needs_persistent_state)):
        return "LangGraph"
    return "LCEL"
```

- 제한된 Retry는 곧바로 "상태 그래프의 반복"으로 볼 필요가 없습니다 (최대 횟수가 정해져 있고, 멈췄다 이어가지 않음).
- 단계 **개수**가 아니라 **제어 흐름과 상태 수명**이 기준입니다. 열 단계라도 한 방향으로 끝나면 LCEL, 단계가 적어도 승인을 기다리며 멈추고 재시작 뒤 이어가야 하면 LangGraph 검토.
- 이번 강의는 판단 함수만 쓰고 실제 그래프는 만들지 않습니다. 완성 실습: `linear_document_qa=LCEL`, `stateful_long_running_flow=LangGraph`.

## 통합 실습 — `starter.py` TODO 1\~3

6\~10장에서 배운 검색·대화 기억·구조화 출력·Retry/Fallback·관찰을 하나의 `ask()` 함수로 묶는 실습입니다. 이미 작성된 뼈대에서 **TODO 세 곳(약 12줄)**을 채웁니다.

### 0. `ask()` 한 번의 흐름

`ask()` 한 번이 하는 일입니다. **굵은 단계**가 직접 채우는 TODO입니다.

```text
ask(session_id, question, failures)
 ① 입력 확인 (빈 값이면 ValueError)                                 [이미 작성됨]
 ② 문서 검색 retriever.invoke(question)                              [이미 작성됨] 6장
     └─ 0건 → QAResponse(not_found, local) 로 끝 (기록 안 만듦)        [이미 작성됨] 10-2
 ③ 이 세션의 기록 가져오기 histories.setdefault(...)                 [이미 작성됨] 7-1
 ④ context 문자열 만들기 "[it-01] VPN은 ..."                         [이미 작성됨] 6-3
 ⑤ primary / fallback / policy(Retry 2번 → Fallback) 준비            [이미 작성됨] 9장
 ⑥ **Prompt에 최근 대화 4개 + context + 질문을 넣고 policy 1번 실행**  TODO 2  (Prompt 자체는 TODO 1)
 ⑦ **grounded면 출처 검증 → 통과하면 질문·답변 함께 저장**           TODO 3
 ⑧ record(status, route, attempts, 시간, 토큰)를 observer로 출력       [이미 작성됨] 8장·10-3
```

### 1. TODO 1 — Prompt 만들기

#### 정답 코드

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", "검색 근거 안에서만 답하고 사용한 문서 ID를 sources에 넣으세요.\n{format_instructions}"),
    MessagesPlaceholder(variable_name="history"),
    ("human", "검색 근거:\n{context}\n\n질문: {question}"),
]).partial(format_instructions=parser.get_format_instructions())
```

#### 해설

- **순서는 system → history → human**입니다 (7-2). 이전 대화가 현재 질문보다 앞에 있어야 시간 순서대로 읽힙니다.
- **`MessagesPlaceholder(variable_name="history")`** 자리에는 나중에 `HumanMessage`·`AIMessage` 목록이 펼쳐집니다. 이름 `"history"`는 TODO 2에서 넣는 키 이름과 같아야 합니다.
- **`{format_instructions}`**에는 `SourceAnswer`의 JSON 형식 안내(answer, sources)가 들어갑니다. 모델이 이 형식으로 답해야 `primary` 안의 `parser.invoke(message)`가 통과합니다 (5-2).
- **`.partial(...)`**은 실행마다 바뀌지 않는 값을 미리 채워 둡니다. 그래서 실행 때는 `history`, `context`, `question` 세 개만 넘기면 됩니다 (10-2).
- system 문장은 자유롭게 써도 됩니다. 핵심은 ① 근거 안에서만 답하기 ② 사용한 문서 ID를 `sources`에 넣기, 이 두 규칙입니다. ②가 없으면 모델이 sources를 비우거나 엉뚱하게 채워서 TODO 3에서 걸립니다.

#### 자주 하는 실수

| 실수 | 결과 |
| --- | --- |
| `.partial()` 없이 `{format_instructions}`만 씀 | 실행 때 `KeyError: Input to ChatPromptTemplate is missing variables {'format_instructions'}` |
| Placeholder 이름을 `"chat_history"`로 쓰고 TODO 2에서는 `"history"` 키를 넣음 | 입력 변수 누락 오류 |
| history를 human 뒤에 둠 | 오류는 안 나지만 대화 순서가 뒤집혀 모델이 헷갈림 |

### 2. TODO 2 — 최근 대화와 검색 근거로 실행

#### 정답 코드

```python
messages = prompt.invoke({
    "history": history.messages[-4:],
    "context": context,
    "question": question,
})
result = policy.invoke(messages)
```

#### 해설

- **`history.messages[-4:]`** = 이 세션의 **끝에서 4개**, 즉 최근 대화 2번입니다. 목록 슬라이싱이라 메시지가 0개나 2개여도 오류 없이 있는 만큼만 들어갑니다.
- **history 객체가 아니라 메시지 목록**을 넣어야 합니다. 객체를 넣으면 `ValueError: variable history should be a list of base messages`가 납니다 (7-2 오류 3).
- `prompt.invoke(...)`의 결과는 `ChatPromptValue`(역할별 메시지)입니다. `primary(messages)`가 이것을 받아 `model.invoke(messages)`에 그대로 넘깁니다. 그래서 Prompt는 **policy 바깥에서 한 번** 만들고 그 결과를 policy에 넣습니다.
- **`policy.invoke`는 한 번만** 호출합니다. 다시 하기(Retry 최대 2번)와 대체 경로(Fallback)는 policy 안에서 알아서 일어납니다. 바깥에서 또 반복하면 9장의 "상한" 원칙이 깨집니다.
- 지금 질문은 **아직 history에 없습니다.** 저장은 TODO 3에서 답을 검증한 뒤에 합니다. 그래서 질문이 두 번 들어가지 않습니다 (7-2).

**실제로 들어가는 메시지 (가짜 모델로 확인)**

| 호출 | Prompt 메시지 역할 |
| --- | --- |
| a 세션 1번째 질문 | `system, human` (이전 대화 없음) |
| a 세션 2번째 질문 | `system, human, ai, human` (첫 질문·답변 + 현재 질문) |

#### 자주 하는 실수

| 실수 | 결과 |
| --- | --- |
| `"history": history` (객체) | `ValueError` |
| `history.messages[:4]` | 오래된 4개가 들어감. 대화가 길어지면 최근 대화가 빠짐 |
| `primary(messages)`를 직접 호출 | Retry·Fallback이 동작하지 않음. c(1번 실패)도 d(3번 실패)도 오류로 멈춤 |
| 실행 전에 현재 질문을 history에 추가 | 질문이 history와 `{question}`에 두 번 들어감 |

### 3. TODO 3 — 출처 검증 후 저장

#### 정답 코드

```python
allowed = {d.metadata["id"] for d in found}
if not result.sources or not set(result.sources) <= allowed:
    raise ValueError("응답 출처가 실제 검색 결과와 일치하지 않습니다.")
history.add_messages([
    HumanMessage(content=question),
    AIMessage(content=result.answer),
])
```

#### 해설

- **`allowed`** = 이번 질문으로 실제로 찾은 문서들의 ID 집합입니다. 예: VPN 질문이면 `{"it-01"}`.
- **`set(result.sources) <= allowed`**는 `issubset()`과 같습니다. 모델이 말한 출처가 모두 실제로 찾은 문서 안에 있는지 봅니다. Parser는 "문자열 목록이다"까지만 확인하므로, 모델이 `"hr-99"` 같은 ID를 지어내도 통과시킵니다. 그래서 앱이 따로 대조합니다 (10-2).
- **`not result.sources`** 검사도 넣습니다. 이 과제의 `QAResponse`에는 10-2처럼 "grounded면 출처가 1개 이상" 검증기가 없습니다. 빈 목록은 `issubset`을 항상 통과(공집합 ⊆ 무엇이든)하므로 직접 막아야 합니다.
- `answer`가 비어 있지 않은지는 `SourceAnswer`의 `Field(min_length=1)`가 이미 검사했습니다 ("형식 확인"은 Parser가, "실제 출처 확인"은 여기서).
- **검증을 통과한 뒤에만** 질문과 답변을 **함께** 저장합니다 (7-2, 10-2). 한쪽만 저장하거나 검증 전에 저장하면 다음 질문의 history가 틀어집니다.
- 이 코드는 `if result.status == "grounded":` 안에 있어서 **Fallback(degraded) 결과는 저장되지 않습니다.** 그래서 d 세션은 기록이 있지만 비어 있습니다.

> 출처가 맞지 않을 때 `ValueError`로 멈추는 것은 10-2 방식입니다. 이 경우 observer 기록도 남지 않습니다. 서비스에서는 not_found나 degraded 결과로 바꿔 돌려주는 설계도 가능하지만, 이 과제의 `assert`는 정상 경로만 확인하므로 10-2 방식으로 충분합니다.

#### 자주 하는 실수

| 실수 | 결과 |
| --- | --- |
| 출처 검증 없이 바로 저장 | 지어낸 출처를 가진 답이 기록에 섞임 |
| `not result.sources` 검사를 빠뜨림 | sources가 빈 grounded 답도 통과 |
| `AIMessage(content=result)` | `content`는 문자열이어야 해서 `ValidationError` → `result.answer`를 넣어야 함 |
| 질문만 저장하거나, 저장을 `if` 바깥에 둠 | 메시지 수가 assert와 달라짐 (a=4, c=2 실패) |

### 4. 5개 사례로 확인

`main()`의 `cases`를 위 코드로 실행하면 이렇게 흘러갑니다.

| 세션 | 질문 | failures | 검색 | primary 시도 | 모델 호출 | 결과 | 저장 후 메시지 수 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| a | VPN이 계속 실패하면… | 0 | it-01 | 1 | 1 | grounded / primary | 2 |
| a | VPN 문의 대상을 다시… | 0 | it-01 | 1 | 1 | grounded / primary | **4** |
| b | 주차 등록 방법은? | 0 | **0건** | 0 | 0 | not_found / local | **기록 없음** |
| c | 교육비는 어떻게… | 1 | hr-01 | 2 (1번 실패 → Retry 성공) | 1 | grounded / primary | **2** |
| d | 교육비 신청 방법은? | 3 | hr-01 | 2 (둘 다 실패 → Fallback) | 0 | degraded / fallback | **0 (빈 기록)** |

- **실제 API 호출은 3번**입니다 (a 두 번, c 한 번). b는 검색 0건이라 모델 정책에 들어가지 않고, d는 두 시도 모두 계획된 오류가 `model.invoke` **전에** 나서 모델까지 가지 않습니다.
- **c의 route가 primary인 이유:** Retry 안에서 Primary가 결과를 만들었기 때문입니다 (10-1 오류 5).
- **d가 "기록은 있지만 비어 있는" 이유:** 검색이 성공해서 ③ `setdefault`로 기록은 만들어졌지만, 결과가 degraded라 TODO 3 저장을 건너뜁니다. b는 ③까지 가지 않아 `histories`에 키 자체가 없습니다. 마지막 `assert "b" not in histories and not histories["d"].messages`가 바로 이 차이를 확인합니다.
- `failures`는 수업용 장치입니다. `count["attempts"] <= failures`이면 모델을 부르기 전에 `TemporaryModelError`를 일부러 냅니다. 실제 서비스에서는 `APIConnectionError`, `InternalServerError`가 같은 자리에 해당하고, 그래서 `recoverable`에 셋이 함께 들어 있습니다.

### 5. 실행 결과 모양

observer가 사례마다 기록을 먼저 출력하고, 그다음 `main()`이 `[답변]`을 출력합니다. `latency_ms`, 토큰 수, 답변 문장은 실행마다 달라집니다.

```text
{'session': 'a', 'status': 'grounded', 'route': 'primary', 'attempts': 1, 'latency_ms': …, 'token_usage': {'input_tokens': …, 'output_tokens': …, 'total_tokens': …}}
[답변] {'answer': '…IT 지원팀에 문의…', 'sources': ['it-01'], 'status': 'grounded', 'route': 'primary'}
…
{'session': 'b', 'status': 'not_found', 'route': 'local', 'attempts': 0, 'latency_ms': …, 'token_usage': 'not_available'}
…
{'session': 'c', 'status': 'grounded', 'route': 'primary', 'attempts': 2, …}
…
{'session': 'd', 'status': 'degraded', 'route': 'fallback', 'attempts': 2, 'latency_ms': …, 'token_usage': 'not_available'}
[답변] {'answer': '현재 답변을 만들 수 없습니다. 담당 부서에 문의해 주세요.', 'sources': [], 'status': 'degraded', 'route': 'fallback'}
[확인] 세션 분리 및 검증 후 저장 완료
```

- b와 d의 `token_usage`가 `not_available`인 이유: 모델을 호출하지 않아 사용량 정보가 없기 때문입니다. 0으로 적지 않습니다 (8-2, 10-3).
- 실제 모델이 sources를 비우거나 다른 ID를 넣으면 TODO 3의 `ValueError`로 멈출 수 있습니다. 그때는 TODO 1의 system 문장에 "사용한 문서 ID를 sources에 넣으세요"가 분명히 들어갔는지 먼저 확인하세요.

## 확인 문제

모두 API 없이 풀 수 있습니다. `from langchain_core.runnables import RunnableLambda`, `from langchain_core.messages import HumanMessage, AIMessage`, 위 요약의 `QAResponse`, `choose_orchestration`이 준비되어 있다고 가정합니다. 각 문제 바로 아래에 정답과 해설이 있습니다. 먼저 풀어 본 뒤 확인하세요.

### 10-Q1. 필수? 선택? (10-1)

아래 기능을 이번 통합 앱의 필수 / 선택으로 나누고, `build_requirements()`를 출력한 결과(`app_type`, 필수 개수, 선택 개수)를 쓰세요.

`retriever`, `langfuse_trace`, `session_history`, `structured_output`, `persistent_storage`, `question_input`, `retry_fallback`, `prompt_model_parser`, `local_trace`

> 힌트: 외부 서비스나 프로세스 종료 뒤에도 남는 저장소가 필요한 기능이 선택입니다.

<details>
<summary>정답 보기</summary>

필수(7): `question_input`, `retriever`, `prompt_model_parser`, `structured_output`, `session_history`, `retry_fallback`, `local_trace` · 선택(2): `langfuse_trace`, `persistent_storage`. 출력: `document_qa 7 2`. 필수는 다음 강의의 오프라인 실행만으로 확인할 수 있는 기능이고, 선택은 핵심 앱이 동작한 뒤 붙이는 기능입니다. 이 목록은 실행 순서가 아닙니다.

</details>

### 10-Q2. 단계 순서 채우기 (10-1)

8단계를 실행 순서대로 쓰고, 각 단계의 output을 쓰세요.

`history_save`, `retrieve`, `local_trace`, `input_check`, `structured_parser`, `prompt`, `history_read`, `model_policy`

> 힌트: 첫 단계는 외부 입력을 앱 내부 요청으로 바꾸고, 마지막은 검증된 대화를 저장합니다.

<details>
<summary>정답 보기</summary>

| 순서 | 단계 | output |
| --- | --- | --- |
| 1 | `input_check` | validated request |
| 2 | `history_read` | message list |
| 3 | `retrieve` | `list[Document]` |
| 4 | `prompt` | 모델 메시지 |
| 5 | `model_policy` | 모델 응답 |
| 6 | `structured_parser` | `QAResponse` |
| 7 | `local_trace` | trace 레코드 |
| 8 | `history_save` | 갱신된 메시지 목록 |

반드시 지켜야 할 두 순서는 **retrieve → model_policy**, **structured_parser → history_save**입니다. (10-2 구현에서는 검색 0건이면 일찍 끝내려고 검색을 History 조회보다 먼저 하지만, 두 핵심 순서는 같습니다.)

</details>

### 10-Q3. 순서 검증 오류 (10-1)

`validate_stage_plan()`에 아래 두 계획을 넣으면 각각 어떤 오류 메시지가 나나요?

```python
plan_a = ["input_check", "history_read", "prompt", "model_policy", "retrieve",
          "structured_parser", "local_trace", "history_save"]
plan_b = ["input_check", "history_read", "retrieve", "prompt", "model_policy",
          "history_save", "local_trace", "structured_parser"]
```

그리고 각 순서가 실제 앱에서 어떤 문제를 일으키는지 한 줄씩 쓰세요.

> 힌트: `names.index("A") > names.index("B")`이면 A가 B보다 뒤에 있다는 뜻입니다.

<details>
<summary>정답 보기</summary>

plan_a → `Retriever는 Model보다 먼저 실행되어야 합니다.` (검색 근거를 모델 입력에 쓸 수 없음 → 일반 지식으로 답함). plan_b → `Structured Parser는 History 저장보다 먼저 실행되어야 합니다.` (검증 안 된 답이 대화 기록에 저장돼 다음 질문의 History에 섞임). 두 계획 모두 단계 **집합**은 맞아서 첫 번째 집합 검사는 통과하고, 위치 검사에서 걸립니다.

</details>

### 10-Q4. 기대 status와 route (10-1)

각 상황의 기대 `status`, `route`와 모델 호출 여부를 쓰세요.

1. 질문과 관련된 문서가 검색되고 Primary가 첫 시도에 답했다.
2. 검색 결과가 0건이다.
3. Primary가 첫 시도에서 일시 오류, 두 번째 시도에서 성공했다.
4. Primary가 허용된 시도를 모두 실패했다.

그리고 3번을 `route=fallback`으로 기록하면 왜 틀렸는지 쓰세요.

> 힌트: 결과를 실제로 만든 경로가 route입니다.

<details>
<summary>정답 보기</summary>

1 `grounded` / `primary` / 호출 · 2 `not_found` / `local` / **호출 안 함** · 3 `grounded` / `primary` / 다시 호출 · 4 `degraded` / `fallback` / Fallback 실행. 3번은 Retry 안에서 **Primary가 결과를 만들었으므로** 최종 경로는 `primary`입니다. `fallback`은 Primary가 시도를 모두 실패해 대체 체인이 실행된 경우에만 씁니다 (10-1 오류 5).

</details>

### 10-Q5. QAResponse 검증 (10-2)

각 줄은 객체가 만들어지나요, `ValidationError`가 나나요? 실패하면 이유를 쓰세요.

```python
QAResponse(status="grounded",  answer="a", sources=["doc-003"])   # (a)
QAResponse(status="grounded",  answer="a", sources=[])            # (b)
QAResponse(status="not_found", answer="a", sources=["doc-003"])   # (c)
QAResponse(status="not_found", answer="a", sources=[])            # (d)
QAResponse(status="error",     answer="a", sources=[])            # (e)
QAResponse(status="grounded",  answer="a", sources=["doc-999"])   # (f)
```

(f)가 통과한다면, 그게 왜 문제인가요?

> 힌트: `model_validator`는 상태와 출처 개수의 관계만 봅니다.

<details>
<summary>정답 보기</summary>

(a) 성공 · (b) 실패 — grounded인데 출처 없음 · (c) 실패 — not_found인데 출처 있음 · (d) 성공 · (e) 실패 — `status`가 `Literal["grounded", "not_found"]`에 없음(`literal_error`) · (f) **성공**. Pydantic은 `doc-999`가 실제로 검색된 문서인지 알 수 없습니다. 그래서 앱이 `set(result.sources).issubset(allowed_sources)`로 **실제 검색 결과와 따로 대조**해야 합니다 (10-2 오류 3).

</details>

### 10-Q6. 출처 대조 (10-2)

이번 질문의 검색 결과는 `doc-001`, `doc-003`입니다. 모델이 돌려준 `sources`가 아래와 같을 때 출처 검증을 통과하나요?

1. `["doc-003"]`
2. `["doc-003", "doc-001"]`
3. `["doc-003", "doc-999"]`
4. `["DOC-003"]`

검증에 실패하면 History에는 무엇이 저장되나요?

> 힌트: `issubset()`은 하나라도 밖에 있으면 `False`, 문자열 비교는 대소문자를 구분합니다.

<details>
<summary>정답 보기</summary>

1 통과 · 2 통과 · 3 실패 (`doc-999`는 검색하지 않은 문서) · 4 실패 (`"DOC-003"`과 `"doc-003"`은 다른 문자열). 실패하면 `ValueError("응답 출처가 실제 검색 결과와 일치하지 않습니다.")`가 나고 저장 단계까지 가지 않으므로 **History에는 아무것도 저장되지 않습니다.** 저장은 모든 검증 뒤에만 합니다.

</details>

### 10-Q7. History 문자열 만들기 (10-2)

```python
def format_history(messages):
    if not messages:
        return "이전 대화 없음"
    return "\n".join(
        f"{'사용자' if isinstance(m, HumanMessage) else '도우미'}: {m.content}"
        for m in messages[-4:]
    )

msgs = [HumanMessage(content="Q1"), AIMessage(content="A1"),
        HumanMessage(content="Q2"), AIMessage(content="A2"),
        HumanMessage(content="Q3"), AIMessage(content="A3")]
print(format_history(msgs))
print(format_history([]))
```

> 힌트: `messages[-4:]`는 끝에서 4개입니다.

<details>
<summary>정답 보기</summary>

```text
사용자: Q2
도우미: A2
사용자: Q3
도우미: A3
이전 대화 없음
```

가장 오래된 Q1·A1은 빠지고 최근 두 번의 대화만 들어갑니다. 대화가 없을 때 빈 문자열 대신 분명한 문구를 넣는 것은 6-3의 `"검색된 문서가 없습니다."`와 같은 원리입니다.

</details>

### 10-Q8. UI 표시용 조각 (10-2)

```python
def stream_validated_answer(answer: str):
    for word in answer.split():
        yield f"{word} "

chunks = list(stream_validated_answer("Retriever는 관련 문서를 찾습니다."))
print(len(chunks))
print(repr("".join(chunks)))
```

(1) 출력은? (2) 이 함수가 8장의 모델 토큰 스트리밍과 다른 점은?

> 힌트: `split()`은 공백 기준으로 나눕니다. 마지막 단어 뒤에도 공백이 붙습니다.

<details>
<summary>정답 보기</summary>

(1)

```text
4
'Retriever는 관련 문서를 찾습니다. '
```

단어 4개(`Retriever는`, `관련`, `문서를`, `찾습니다.`)이고, 합치면 끝에 공백이 하나 남습니다(필요하면 `.strip()`). (2) 8장은 모델이 답을 **생성하는 동안** 조각을 받는 것이고, 이 함수는 Model·Parser·출처 검증이 **모두 끝난 완성 문자열**을 화면에 점진적으로 보여 주는 UI 처리입니다 (10-2 오류 5).

</details>

### 10-Q9. 앱 실행 시나리오 (10-2)

1. `"메모리는 어디에 저장하나요?"`에서 검색이 0건이었다. 모델 호출 횟수, 반환되는 `QAResponse`, 이 세션 History의 변화는?
2. 과금 없이 테스트하려고 터미널에서만 `OPENAI_API_KEY`를 지웠는데 `mode=live`가 나왔다. 왜일까요?
3. 같은 사용자의 두 번째 질문을 처리하려고 `DocumentQAApp`을 새로 만들었더니 첫 대화를 기억하지 못했다. 왜일까요?

> 힌트: `load_dotenv()`, 앱 객체가 들고 있는 `histories`.

<details>
<summary>정답 보기</summary>

1. 모델 호출 **0회**, `QAResponse(status="not_found", sources=[])`, History는 **새로 만들지도 저장하지도 않음**. 근거 없이 모델을 부르면 일반 지식으로 답할 수 있어서 로컬 안내로 끝냅니다.
2. `load_dotenv()`가 `.env` 파일의 키를 다시 읽었기 때문입니다. 터미널 환경변수와 `.env` **양쪽** 모두에서 키를 없애야 `mode=offline`이 됩니다.
3. History 저장소(`histories`)가 앱 객체 안에 있어서, 새 앱은 빈 저장소로 시작합니다. 대화를 이어 가려면 **같은 앱 객체 + 같은 session_id**를 씁니다 (10-2 오류 7).

</details>

### 10-Q10. 관측 레코드에 무엇을 넣을까? (10-3)

다음 중 `RunRecord`에 넣는 것과 넣지 않는 것을 고르세요.

`case`, 사용자 질문 원문, `status`, `route`, 모델 답변 원문, `attempts`, `OPENAI_API_KEY`, `latency_ms`, 예외의 상세 메시지 전체, `token_usage`

그리고 `ObservedAnswer`와 `RunRecord`를 따로 두는 이유를 한 문장으로 쓰세요.

> 힌트: 이번 레코드의 목적은 "오류 정책이 어떤 경로로 동작했는가"입니다.

<details>
<summary>정답 보기</summary>

넣는 것: `case`, `status`, `route`, `attempts`, `latency_ms`, `token_usage` · 넣지 않는 것: 질문 원문, 답변 원문, API Key, 상세 오류 메시지. `ObservedAnswer`는 **사용자에게 전달할 결과**이고 `RunRecord`는 **실행에서 어떤 정책이 동작했는지 설명하는 관측 정보**라서, 목적이 다른 데이터를 섞지 않고 필요한 필드만 남기기 위해 분리합니다.

</details>

### 10-Q11. 세 사례 관측 결과 (10-3)

`primary`는 `case`에 따라 동작하고(temporary는 첫 시도만 실패, persistent는 항상 실패), 체인은 `with_retry(stop_after_attempt=2)` 뒤 `with_fallbacks(...)`입니다. 사례마다 **새 체인**을 만들어 실행할 때 표를 채우세요.

| case | status | route | attempts | fallback 호출 |
| --- | --- | --- | --- | --- |
| normal | ? | ? | ? | ? |
| temporary | ? | ? | ? | ? |
| persistent | ? | ? | ? | ? |

세 사례를 **한 체인·한 호출 횟수 dict**로 연달아 실행하면 무엇이 잘못되나요?

> 힌트: `stop_after_attempt=2`는 최초 포함 2번입니다.

<details>
<summary>정답 보기</summary>

| case | status | route | attempts | fallback 호출 |
| --- | --- | --- | --- | --- |
| normal | ok | primary | 1 | 0 |
| temporary | ok | primary | 2 | 0 |
| persistent | degraded | fallback | 2 | 1 |

같은 dict를 공유하면 이전 사례의 호출 횟수가 누적되어 `attempts`가 1, 2로 나오지 않고, temporary의 "첫 시도 실패" 조건(`calls == 1`)도 재현되지 않습니다 (9-Q5와 같은 원리). 그래서 사례마다 새 체인과 새 `calls`를 만듭니다.

</details>

### 10-Q12. latency와 token_usage (10-3)

(1) 완성 실습을 두 번 돌렸더니 normal의 `latency_ms`가 0.41과 0.37로 달랐습니다. 버그인가요? (2) 로컬 Runnable 실행의 토큰 사용량을 `0`으로 기록하면 안 되는 이유는? (3) `attempts`는 실행할 때마다 달라져도 되나요?

> 힌트: 결정적인 값과 측정값을 구분하세요.

<details>
<summary>정답 보기</summary>

(1) 버그가 아닙니다. `latency_ms`는 컴퓨터 상태와 실행 시점에 따라 달라지는 **측정값**이라 0 이상인지만 확인하고 특정 숫자를 정답으로 고정하지 않습니다. (2) 0은 "토큰을 전혀 쓰지 않았다"는 **다른 사실**을 주장합니다. 정보가 없으면 `not_available`로 명시하고, 문자 수로 추측하지도 않습니다. (3) 안 됩니다. `attempts`는 사례별로 1 또는 2가 되어야 하는 **결정적인 정책 값**입니다. 달라진다면 상태 공유 같은 버그를 의심합니다.

</details>

### 10-Q13. 관측 실패에서 앱 결과 지키기 (10-3)

```python
class BrokenObserver:
    def flush(self) -> None:
        raise RuntimeError("계획된 관측 전송 오류")

def flush_langfuse(client) -> bool:
    if client is None:
        return False
    try:
        client.flush()
    except Exception:
        return False
    return True

app_result = {"status": "ok", "route": "primary"}
print(flush_langfuse(None), flush_langfuse(BrokenObserver()))
print(app_result)
```

(1) 출력은? (2) 편하게 하려고 `chain.invoke()`와 `client.flush()`를 **같은** `try/except Exception` 안에 넣으면 무엇이 문제인가요? (3) `flush_langfuse()`가 `True`를 반환하면 Langfuse에서 trace 조회까지 성공한 것인가요?

> 힌트: 넓은 예외 처리는 어디에만 두기로 했나요?

<details>
<summary>정답 보기</summary>

(1)

```text
False False
{'status': 'ok', 'route': 'primary'}
```

관측 전송이 실패해도 이미 만든 앱 결과는 그대로입니다. (2) Primary의 실제 오류(예: 코드 버그)까지 "관측 실패"처럼 삼켜져 숨겨집니다. 넓은 예외 처리는 **선택적 관측 도구의 초기화·전송 경계에만** 둡니다. (3) 아닙니다. ingestion API **전송 완료**일 뿐이고, 저장해 둔 `last_trace_id`로 제한 시간(약 60초) 안에 observation을 다시 조회해 세 case가 모두 보여야 조회 가능 상태까지 확인한 것입니다.

</details>

### 10-Q14. LCEL? LangGraph? (10-3)

`choose_orchestration()`의 결과를 쓰고, 어떤 요구 때문인지 쓰세요.

1. 질문 → 검색 → 답변 → 저장으로 한 요청 안에서 끝나는 문서 Q&A (10단계, Retry 최대 2회)
2. 환불 요청을 분석한 뒤 담당자 승인을 받으면 다음 단계를 실행
3. 검색 결과가 부족하면 질문을 고쳐 다시 검색하기를 반복
4. 긴 보고서 작업을 서버가 재시작돼도 중간부터 이어서 처리
5. 3단계뿐이지만, 사용자가 내일 다시 와서 멈춘 지점부터 이어 가야 함

> 힌트: 기준은 단계 개수가 아니라 제어 흐름과 상태 수명입니다.

<details>
<summary>정답 보기</summary>

1 **LCEL** — 네 요구 모두 없음. 단계가 많고 Retry가 있어도 한 방향으로 끝나고 횟수가 제한됨 · 2 **LangGraph** — `needs_human_approval` · 3 **LangGraph** — `needs_loop` · 4 **LangGraph** — `needs_persistent_state`(+ `needs_resume`) · 5 **LangGraph** — `needs_resume`(+ 영속 상태). 5번처럼 단계가 적어도 멈췄다 이어가야 하면 상태 기반 오케스트레이션을 검토할 이유가 생깁니다.

</details>

### 10-Q15. 10장 전체 O/X

1. 필수 기능 목록 `required`의 순서가 곧 실행 순서다.
2. 검색 결과가 0건이면 모델 예외로 분류해 Fallback으로 보낸다.
3. Parser를 통과한 `QAResponse`의 `sources`는 실제 검색 문서라고 믿어도 된다.
4. `not_found` 경로에서는 History에 질문과 답변을 저장하지 않는다.
5. `OPENAI_API_KEY` 문자열이 환경변수에 있으면 live 호출 성공이 보장된다.
6. Langfuse Callback을 붙이면 `with_retry()`의 최대 시도 횟수가 바뀔 수 있다.
7. 단계가 10개를 넘으면 LangGraph로 바꿔야 한다.
8. 각 테스트 사례는 새 앱 상태에서 시작해야 한다.

> 힌트: 10-1 오류, 10-2 오류, 10-3의 역할 표를 떠올려 보세요.

<details>
<summary>정답 보기</summary>

1 X (구현 범위일 뿐, 순서는 단계 계획) · 2 X (모델 예외가 아님 → `not_found`/`local`로 종료) · 3 X (`allowed_sources`와 `issubset()`으로 대조) · 4 O · 5 X (인증·결제·권한·네트워크·출처 검증까지 끝나야 성공) · 6 X (관측은 실행을 바라볼 뿐 제어하지 않음) · 7 X (단계 개수가 아니라 반복·재개·승인·영속 상태 요구가 기준) · 8 O

</details>
