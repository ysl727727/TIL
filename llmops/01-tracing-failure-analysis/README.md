# 1장. 실행 관측과 실패 원인 분석 — Trace · observation · 재조회 · 도구 추적 · 실패 분류

> 2026-10-30 학습 기록. LLMOps 1일차 수업이에요. 가상 규정 QA 한 건을 Langfuse Trace 하나로 기록했고(1-1), 같은 Trace를 서버에서 다시 조회해 GENERATION이 끝났는지 확인했어요(1-2). 업무 도구 조회를 따로 기록해 부모·자식 시간을 읽었고(1-3), 모의 실패 6개를 정해진 순서로 분류해 Trace 점수로 붙였어요(1-4).

## 학습 목표

- 같은 오답이라도 **검색 · 입력 조립 · 생성** 중 어디서 처음 근거가 사라졌는지에 따라 고칠 곳이 다르다는 것을 안다.
- Trace(요청 전체)와 observation(그 안의 단계: span · chain · GENERATION · tool)을 구분한다.
- 호출 성공(HTTP 200) ≠ 응답 완료(`status=completed`) ≠ 품질 성공(내용이 맞음)을 구분한다.
- 답변 출력 · `flush()` 전송 · 서버 재조회가 서로 다른 단계라는 것을 알고, 질문 문장이 아니라 **Trace ID와 시간 범위**로 다시 찾는다.
- 부모 구간 시간에는 자식 시간이 포함되어 있어 더하면 중복이고, 병목은 자식 중 가장 긴 구간에서 찾는다.
- 실패 판정 순서(형식 → 실행 실패 → 검색 없음)를 지키고, 모르는 상태를 성공으로 채우지 않는다.

## 실습 환경

| 항목 | 내용 |
| --- | --- |
| 키트 | `llmops_ch01` (강의별 파일 + 공통 함수 `course.py`), `uv sync --locked` → `uv run --locked 파일.py` |
| 패키지 | langchain 1.4.5 · langchain-openai 1.7.1 · langfuse 4.17.0 · python-dotenv 1.2.4 · pydantic 2.14.1 (+ `printsection` 직접 추가) |
| 관측 | Langfuse Cloud, 프로젝트 `policy-qa`, 환경 이름 `llmops-course` |
| 모델 | OpenAI `gpt-5.6-luna`, Responses API, `max_tokens=400`, `max_retries=0` |
| `.env` | `OPENAI_API_KEY` · `LANGFUSE_PUBLIC_KEY` · `LANGFUSE_SECRET_KEY` · `LANGFUSE_BASE_URL`(가입한 지역 주소) · `OPENAI_MODEL`(비우면 gpt-5.6-luna) |

## 실습 파일

| 파일 | 강 | 호출 | 실습 상태 |
| --- | --- | --- | --- |
| `00_start.py` | 준비 | 모델 1회 + `response_completed` 점수 | ✅ 실행 |
| `01_trace.py` | 1-1 요청 단위 관측 | 모델 1회 | ✅ 실행 · q1\_hard ⏳ |
| `02_read_trace.py` | 1-2 Trace 재조회 | 조회만 | ✅ 실행(observation 5개) · q2\_hard 통과 |
| `03_steps.py` | 1-3 업무 도구 추적 | 모델 1회 · 업무는 모의 DB | ✅ 실행 · q3\_hard 통과 |
| `04_failures.py` | 1-4 실패 분류 | 모델 없음 · 모의 사례 6개 | ✅ 실행 · q4\_hard 통과 |

## 전체 흐름

```text
준비   .env → connect() → auth_check() → answer() → create_score(response_completed) → finish()
1-1   기록하고   질문 1개 = Trace 1개 (policy-qa → retrieve / generate-answer → ChatOpenAI)
1-2   다시 찾고  result_01.json의 trace_id + 시작 시각 ±1분 → observation 5개, GENERATION 종료 확인
1-3   나누고     qa-with-business-lookup → lookup-approval(tool) + policy-qa, 규정 10만원 ≠ 승인 8만원
1-4   분류하고   status → 시각 → failed → 문서 → completed, failure_category 점수
                → 2장: 고친 게 정말 좋아졌는지는 Golden Dataset으로
```

## 핵심 이론

### 0. 준비 — 누가 무엇을 하나

```text
내 PC (Python + uv)                       OpenAI API          Langfuse Cloud
course.py · 강의 파일                     답변 생성            Trace · 데이터셋 · 점수 보관
LangChain: prompt | model  ── 요청 ──▶    OPENAI_API_KEY
CallbackHandler            ── 기록 ─────────────────────▶     Public/Secret Key 쌍 + 지역 주소
```

- 키 네 개는 발급처와 용도가 달라요. Public/Secret은 **같은 프로젝트의 한 쌍**이어야 하고, `LANGFUSE_BASE_URL`은 프로젝트 상세 URL이 아니라 지역 주소예요(EU `https://cloud.langfuse.com` · US `us.` · Japan `jp.`). 지역을 바꾸면 프로젝트가 따라오지 않아요.
- `00_start.py`의 완료 점수(`response_completed=1`)는 **정답 점수가 아니에요.** "평가할 답이 생겼다"는 표시이고, 판정은 Python 코드가 하고 Langfuse는 그 점수를 같은 Trace ID에 붙여 보관만 해요.

### 1. `connect()` — 연결 객체 두 개

```text
.env 읽기 → 다른 추적 끄기 → 키 4개 확인 → lf 만들기 → model 만들기 → (lf, model) 반환
```

| 부분 | 하는 일 |
| --- | --- |
| `load_dotenv(HERE / ".env", encoding="utf-8-sig")` | 이 장 폴더의 `.env`를 읽음. `utf-8-sig`는 메모장이 붙이는 BOM을 무시 |
| `LANGSMITH_TRACING = "false"` 등 | LangSmith로 기록이 새지 않게, Langfuse 하나만 |
| `missing = [...]` → `ValueError` | 빈 키가 있으면 "`.env`에 값을 입력하세요: …" (처음 실행 때 실제로 본 오류) |
| `Langfuse(environment="llmops-course", sample_rate=1.0, mask_otel_spans=...)` | **lf** = 기록과 조회. environment는 화면 필터, sample\_rate 1.0은 100% 기록, 마스킹 함수는 4장에서 |
| `atexit.register(lf.shutdown)` | 프로그램이 끝날 때 남은 기록을 마저 전송 |
| `ChatOpenAI(...)` | **model** = 답변 생성 |

- `max_retries=0`: 실패를 다시 시도해서 숨기지 않아요. `use_responses_api=True`: 응답에 `status`가 와서 완료 검사에 써요. `store=False`: OpenAI 쪽에 대화를 저장하지 않아요.
- 실행 실패는 `run()`이 오류 **종류와 HTTP 상태만** 보여 줘요(오류 원문에 인증 정보가 섞일 수 있어서). 다른 모델로 바꾸거나 이전 성공 데이터로 대체하지 않고 종료 코드 1로 남겨요.

### 2. 같은 오답, 다른 고칠 곳 (1-1)

| 관측한 증거 | 실패가 처음 드러난 위치 | 다음에 바꿀 대상 |
| --- | --- | --- |
| 검색 문서 목록이 비어 있음 | 검색 | 질문 표현 · 키워드 · 검색 조건 |
| training은 찾았지만 모델 입력에 증빙 문장이 없음 | 입력 조립 | context 구성 코드 |
| 입력에 두 증빙이 다 있는데 답에는 하나만 | 생성 이후 | 응답 지시 · 필수 사실 검사 |

- **모델을 바꾸기 전에, 근거가 처음 사라진 단계부터 찾아요.** 앞 단계가 실패하면 뒤 단계는 보지 않아요(q1의 A 검색 · B 입력 조립 · C 생성 · D 정상).

### 3. `answer()` — 질문 1개 = Trace 1개 (1-1)

```text
policy-qa              span   ← 바깥 with (root)
├─ retrieve            span   ← 직접 감싼 구간 (step)
└─ generate-answer     chain  ← CallbackHandler가 invoke 때 자동 생성
   ├─ ChatPromptTemplate chain   메시지 구성만
   └─ ChatOpenAI       GENERATION  실제 모델 호출은 이것 하나
```

1. `started`(UTC 시작 시각)와 `perf_counter()`(지연 측정)를 먼저 잡아요.
2. `handler = CallbackHandler()` — LangChain 실행을 Langfuse에 적는 **기록 담당자**. `invoke(config={"callbacks": [handler]})`로 넘겨야 작동해요.
3. 바깥 `with lf.start_as_current_observation(name="policy-qa", ...) as root` 범위 전체가 한 번의 질의응답이에요. input에 질문, metadata에 `app_version`·`synthetic`.
4. 안쪽 `with ... name="retrieve" ... as step` — 일반 Python 함수는 콜백이 자동으로 못 잡아서 직접 구간을 열고 `step.update(output={"document_ids": [...]})`.
5. context는 `[training] 교육비는…`처럼 **ID와 본문을 같이** 넣어요. 그래야 답변 끝의 `[training]`이 진짜 받은 문서인지 대조할 수 있어요.
6. 지시는 `SystemMessage`, 근거와 질문은 `human`으로 분리(CE 1장 role 분리와 같은 원리).
7. 완료 검사: `status != "completed"`이거나 답이 비면 `MODEL_RESPONSE_INCOMPLETE`. HTTP 성공만으로 성공이라 하지 않고, 출력 한도로 잘린 답도 실패.
8. `result` dict(`answer` · `document_ids` · `trace_id` · `started_at` · `usage` · `latency_ms`)가 다음 강의로 넘어가는 공통 데이터. 2장은 평가, 3장은 집계에 써요.

- **트리 항목 수 ≠ 모델 호출 횟수.** 5개 observation 중 모델 호출은 ChatOpenAI GENERATION 하나예요.
- 남기는 값: `app_version`(어느 버전), `document_ids`(실제 전달한 출처 범위), `synthetic`(수업용 가상 자료). Trace를 많이 모으는 게 아니라 **이번 요청에 무엇이 들어가고 무엇이 나왔는지 설명할 수 있는 것**이 목적이에요.

### 4. 실행 · 전송 · 조회는 다른 단계 (1-2)

| 보이는 현상 | 알 수 있는 사실 | 아직 모르는 사실 |
| --- | --- | --- |
| 터미널에 답변 | 로컬 코드가 응답을 받음 | Langfuse 저장 여부 |
| Trace 주소 출력 (`flush()` 후) | 연결할 Trace ID가 있음 | 서버 검색 반영 여부 |
| GENERATION 재조회 | 서버에 모델 실행 기록이 있음 | 응답 내용의 정답 여부 |

```python
observations = lf.api.observations.get_many(
    trace_id=row["trace_id"], limit=30, fields="core,basic,usage,model,io",
    from_start_time=datetime.fromisoformat(row["started_at"]) - timedelta(minutes=1),
    to_start_time=datetime.now(timezone.utc) + timedelta(minutes=1),
).data
generations = [x for x in observations if x.type.upper() == "GENERATION"]
```

- 질문 문장이 아니라 **Trace ID + 시작 시각 ±1분**으로 같은 실행만, 필요한 필드만 작게 조회해요. `result_01.json`은 관측 저장소가 아니라 다시 찾기 위한 ID·시각만 담은 작은 파일이에요.
- 관측 0개면 "저장 실패"로 단정하지 않고 지역 · 프로젝트 · 기간 · 반영 지연을 확인해요. **조회가 비었다고 모델을 다시 부르지 않아요** — `02_read_trace.py`만 다시 돌리면 생성 토큰이 안 들어요.
- span만 있으면 모델 실행 미확인, GENERATION에 `end_time`이 있어야 실행 구간이 끝난 것. 그래도 내용 평가는 따로예요.

### 5. 규정 vs 업무 결과, 부모·자식 시간 (1-3)

| 출처 | 예시 | 답변에서 구분할 뜻 |
| --- | --- | --- |
| `travel` (규정 문서) | 1박 10만원, 영수증 필요 | 누구에게나 적용되는 일반 한도 |
| `approval` (업무 조회) | REQ-DEMO-01, 승인, 8만원 | 이 요청에서 승인된 금액 |

- **8만원 승인 ≠ 숙박 한도 8만원.** 두 사실의 출처가 달라서 따로 기록해요.
- `lookup-approval`은 `as_type="tool"`로 입력·출력 경계를 직접 기록해요. tool은 관측 기록의 **유형 표시**일 뿐, 실제 외부 도구를 불렀다는 뜻은 아니에요(여기선 모의 DB dict).
- 부모 시간에는 자식 시간이 이미 들어 있어요. `1.5 + 0.1 + 1.3 = 2.9초`는 중복이고, 사용자가 기다린 시간은 root의 1.5초. 병목은 가장 긴 자식(policy-qa 1.3초) **안에서** 다시 찾아요.

### 6. 판정 순서와 실패 분류 (1-4)

```text
status 유효? ─아니면→ incomplete
시각 유효?   ─아니면→ invalid_time      (파싱 실패 · 시간대 없음 · 끝 < 시작)
failed?      ─맞으면→ model_error
문서 있음?   ─아니면→ retrieval_empty
모두 통과    ────────→ completed
```

| 모의 사례 (base에서 필드 하나만 변경) | 판정 |
| --- | --- |
| 정상 | completed |
| 모델 실패 `status=failed` | model\_error |
| 검색 없음 `document_ids=[]` | retrieval\_empty |
| 상태 누락 `status=None` | incomplete |
| 날짜 오류 `ended_at="not-a-date"` | invalid\_time |
| 시간 역전 (끝 < 시작) | invalid\_time |

- 시각은 문자열 모양이 아니라 `datetime.fromisoformat`으로 **파싱해서** 검사해요. 잘못된 시각은 오류율 근거로 쓰지 않아요.
- **모르는 상태를 성공으로 채우지 않아요.** 버리면 품질이 실제보다 좋아 보여요.
- 분류값은 `create_score(name="failure_category", data_type="CATEGORICAL")`로 **그 사례의 Trace에** 붙여요. 분류값만 따로 쌓으면 어떤 입력을 보고 내린 판단인지 찾기 어려워요. 모의 실패는 `simulation: True`, 정상 아니면 `level="WARNING"`으로 운영 오류율과 분리해요.
- 검색 없음이 꼭 실패는 아니에요. "재택근무 지원금"처럼 규정 밖이면 **보류가 맞는 행동**이고, 표현 차이로 training을 못 찾은 거면 실패. 기대 행동을 붙여야 알 수 있고, 이게 2장 Golden Dataset으로 이어져요.

## 실행 결과

```text
00_start   응답 상태: completed / 식비 2만원 · 영수증 [meal] / response_completed 점수
01_trace   검색한 문서: ['training'] / 연간 20만 원 · 영수증과 수료증 [training]
           usage 입력 144 · 출력 32 토큰, latency 2426.5 ms
02_read    observation 5개, generation_complete: true
03_steps   1박 10만원 · 영수증, REQ-DEMO-01 8만원 승인 [travel] [approval]
           document_ids: ['travel'] (approval은 extra_context로 들어가서 검색 목록엔 없음)
04_fail    completed · model_error · retrieval_empty · incomplete · invalid_time · invalid_time
```

- 03에서 답변은 `[approval]`을 인용했는데 `document_ids`에는 travel만 있어요. approval은 검색이 아니라 `extra_context`로 붙었기 때문이에요. **출처 범위를 대조할 때 검색 문서만 보면 approval 인용이 "없는 출처"처럼 보일 수 있다** → 2장에서 출처 범위 검사를 할 때 주의할 점.

## 질문과 새로 알게 된 점

### `.env` 작성

- 값에 따옴표는 필요 없고 `=` 앞뒤에 띄어쓰기도 넣지 않아요(`KEY=값`). 모델은 `gpt-5.6-luna` 그대로 두거나 비워도 같아요.
- 처음 실행 때 "`.env`에 값을 입력하세요: LANGFUSE\_PUBLIC\_KEY, …"가 나온 건 `connect()`의 `missing` 검사였어요. Langfuse에서 조직 → 프로젝트 `policy-qa` → API Keys로 키 쌍을 만들어 넣었어요.
- **키 값은 채팅·화면·터미널에 붙이지 않아요.** 확인이 필요하면 `pk-lf-…`처럼 앞부분만, 이미 붙였다면 Revoke 후 재발급. `.env` 전체를 출력할 필요도 없어요(PPT 준비 페이지에도 나온 내용).

### Trace 트리 — 부모를 정하는 건 "열려 있는 with"

```python
with lf.start_as_current_observation(name="policy-qa", as_type="span", ...) as root:
    with lf.start_as_current_observation(name="retrieve", as_type="span", ...) as step:
        docs = retrieve(question)
        step.update(output={"document_ids": [...]})
    reply = (prompt | model).invoke(..., config={"callbacks": [handler], "run_name": "generate-answer"})
    root.update(output={"answer": ..., "status": "completed"})
```

- `root`, `step`은 `as` 뒤에 붙인 **변수 이름**일 뿐이에요. 둘 다 같은 함수로 만든 span이라 "root 아래는 무조건 step" 같은 규칙은 없어요.
- 부모를 정하는 건 이름도 실행 순서도 아니고, **기록이 생기는 순간 열려 있는 with**예요. invoke는 retrieve의 with가 이미 닫힌 뒤 root 안에서 실행돼서 retrieve의 자식이 아니라 **형제**. invoke를 step 블록 안으로 들여쓰면 retrieve의 자식이 돼요.
- 그래서 답이 이상하거나 느릴 때 **검색 문제인지 모델 문제인지** 트리에서 바로 갈라 볼 수 있어요.

| 이름 | 하는 일 | 기록 내용 |
| --- | --- | --- |
| policy-qa | 질문 1번 전체 | 질문, 최종 답, 상태, app\_version, trace\_id |
| retrieve | 문서 검색 | 질문 → 찾은 문서 ID |
| generate-answer | 모델 답변 생성 | 프롬프트, 답변, 토큰, 시간 |

### `ChatPromptTemplate.from_messages` — 정해진 이름 vs 내가 정한 이름

```python
prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content=instruction),                 # 고정 메시지 객체
    ("human", "근거:\n{context}\n질문: {question}"),      # (역할, 글) 튜플, {}는 빈칸
])
(prompt | model).invoke({"context": context, "question": question})  # 빈칸 채우기
```

- `ChatPromptTemplate`, `from_messages`, `SystemMessage`, 역할 `"human"`·`"system"`은 **LangChain이 정한 이름**이라 못 바꿔요.
- `{context}`, `{question}`은 **우리가 정한 빈칸 이름**이라 바꿔도 되지만 invoke dict의 키와 맞춰야 해요.
- `from_~`는 "~로부터 만든다"는 관례예요(Mem0 `Memory.from_config`와 같은 모양).

### 정의 vs 호출, import

- **호출(사용)**: 라이브러리가 정한 이름을 그대로 써야 해요 (`from_messages`, `from_config`, `start_as_current_observation`).
- **정의**: 내가 만드는 class·def 이름은 자유예요. `answer`, `retrieve`, `classify`는 강사님이 붙인 이름일 뿐. 예외는 `__init__`, `self`(관례), 키워드(`def` · `class` · `return`).
- 흐름: LangChain 개발자가 **정의** → uv가 `.venv\Lib\site-packages`에 **설치** → `from langchain_core.prompts import ChatPromptTemplate`로 **import** → **호출**.

### q3\_hard: root · 전체 시간 · 병목

```python
def children(name):
    return [s for s in spans if s["parent"] == name]

root = [s for s in spans if s["parent"] is None][0]
total_ms = root["ms"]
bottleneck = max(children(root["name"]), key=lambda s: s["ms"])
inner = max(children(bottleneck["name"]), key=lambda s: s["ms"])
# 모든 구간을 더한 값: 4185 ms <- 중복 계산 / 사용자가 기다린 시간: 1500 ms
# 병목: policy-qa → generate-answer
```

- root = `parent`가 None인 span(맨 위 부모). **전체 시간 = root의 ms**(합계 아님).
- `key`에는 **각 후보 자신의 값**(`s["ms"]`)을 줘야 해요. `key=lambda s: root["ms"]`로 쓰면 모든 후보가 같은 값이라 동점 → 첫 자식이 **조용히** 반환돼요(오류도 안 남).
- `key`에 넘긴 lambda는 `max`가 후보마다 대신 불러 주는 함수예요. 그래서 내 주석에 "일종의 callback"이라고 적었어요(함수를 넘겨서 상대가 호출하게 한다는 점이 같아요).
- 부모는 상대적이에요. generate는 request의 자식이면서 prefill/decode의 부모.

### q4\_hard: `classify(row)`에 cancelled 추가

```python
def classify(row):
    if row.get("status") not in {"completed", "failed", "cancelled"}:
        return "incomplete"
    try:
        start, end = [datetime.fromisoformat(row[k]) for k in ("started_at", "ended_at")]
        if start.tzinfo is None or end.tzinfo is None or end < start:
            return "invalid_time"
    except (KeyError, TypeError, ValueError):
        return "invalid_time"
    if row["status"] == "failed":
        return "model_error"
    if row["status"] == "cancelled":
        return "cancelled"
    if not row.get("document_ids"):
        return "retrieval_empty"
    return "completed"
```

- **`.get()`**: row가 dict라서 dict의 `.get()` 메서드를 쓸 수 있어요. `row["status"]`는 키가 없으면 KeyError, `.get("status")`는 None → 자연스럽게 `"incomplete"`로 떨어져요. 메서드 호출이라 `( )`, 키는 `[ ]`든 `.get( )`이든 따옴표 문자열.
- **`{"completed", "failed", "cancelled"}`는 set**이에요(콜론이 없으니 dict 아님). `.get`이 값을 돌려주는 것과는 상관없어요. `not in`은 튜플 `( )`·리스트 `[ ]`로 써도 결과가 같고, set은 "허용 값 모음"이라는 뜻이 분명하고 검사가 빨라요(3개라 속도 차이는 거의 없음). CE 4장 `set(args) != {"query"}`와 같은 생각.
- **`if status ...`로 쓰고 싶다면** 먼저 `status = row.get("status")`로 꺼내 이름을 붙여야 해요. 함수가 받은 건 `row`뿐이라 맨 `status`는 NameError. 코드 시작 순서: 입력(row)은? → 필요한 값은? → 어디서 꺼내나(row) → 하나씩 꺼내 이름 붙이기.
- **try/except 흐름**
  - try는 `started_at`·`ended_at` 파싱만 해요. KeyError(키 없음) · TypeError(None이나 숫자, 문자열 아님) · ValueError(날짜 형식 틀림)는 모두 "시간 데이터 고장" → except → `invalid_time`.
  - try 안에서 오류가 나면 바로 except로 점프해요.
  - try 안의 `if`(시간대 없음, 끝 < 시작)는 오류가 아니라서 except를 거치지 않고 **바로 return**.
  - 둘 다 아니면 try를 빠져나와 아래 status 검사로 내려가요. **위에서부터 처음 걸리는 return이 결과**(incomplete → invalid\_time → model\_error → cancelled → retrieval\_empty → completed).
  - 그래서 "취소 + 시간 역전"은 cancelled가 아니라 invalid\_time(형식 검사가 먼저), "취소 + 문서 없음"은 retrieval\_empty가 아니라 cancelled.
- **`if not row.get("document_ids")` → `"retrieval_empty"`**: 키 없음 · None · `[]`를 한 번에 걸러요. 따로 나눈 이유는 "완료"됐는데 문서가 없으면 **근거 없이 답한 것**이라 RAG의 가장 흔한 실패이기 때문이에요(RAG 7-1 q10 BM25 `[]`와 같은 상황). 문서 ID가 **틀렸는지**는 정답 데이터(RAG 8장 Hit/Recall)나 카탈로그가 있어야 알 수 있어서, 로그 한 줄만 보는 이 함수는 확인하지 않아요.

### q2\_hard: GENERATION 완료 판정

```python
if not observations:
    return "조회 결과 없음"
generations = [x for x in observations if x.type.upper() == "GENERATION"]
if not generations or any(x.end_time is None for x in generations):
    return "GENERATION_NOT_CONFIRMED"
return "서버 기록 확인"
```

- 0개는 "조회 결과 없음"이지 저장 실패로 단정하지 않아요. type은 서버·SDK에 따라 소문자로 올 수 있어서 `.upper()`로 맞춰 비교해요.
- "서버 기록 확인"이 나와도 **답이 맞다는 뜻은 아니에요.** 실행 기록이 끝났다는 것뿐이고, 정답 여부는 모델 입력과 최종 답을 기대 답과 비교해야 알 수 있어요(2장).

## 실습 코드에서 직접 바꾼 점

원본 `llmops_ch01.zip`과 비교한 결과예요. 키트 코드 자체는 올리지 않고 바꾼 부분만 적어요.

| 파일 | 바꾼 점 / 추가한 주석 |
| --- | --- |
| `pyproject.toml` | `uv add printsection`으로 `printsection>=0.5.0` 추가(의존성 목록이 여러 줄로 바뀜) |
| `.env.example` | 이름을 `.env`로 바꿔 키 입력(폴더에 `.env.example`은 없음, `.env`는 공개하지 않음) |
| `q2_hard.py` | 위 `judge` 세 단계 구현 |
| `q3_hard.py` | 위 `children`·root·total\_ms·bottleneck·inner, `# 일종의 callback임` 주석 |
| `q4_hard.py` | 위 `classify` cancelled 추가 |
| `04_failures.py` | `def classify(row): # 운영단계에서 중요도가 떨어지는 것들은 try except로 구현할수도있음.` 주석 |
| `course.py` · `04_failures.py` | 줄 끝 공백만 생김(동작 변화 없음) |
| `practice.py` | 연습용 빈 파일 새로 만듦 |

`q1_hard.py`(`locate`)는 아직 원본 그대로예요.

## 하루 정리 (PPT)

- 1장 결과물: **한 요청의 증거를 남기고 읽는 법.** 1-1 요청 단위 관측(policy-qa → retrieve → ChatOpenAI), 1-2 재조회(observation 5개, GENERATION 완료), 1-3 도구 추적(10만원 한도 ≠ 8만원 승인), 1-4 실패 분류(6개 사례, failure\_category).
- 완료 검사 = 평가할 답이 있는가 / 내용 평가 = 업무 조건을 지켰는가.
- 2장으로 이어지는 질문: 프롬프트를 고쳤더니 좋아진 것 같을 때, 정말 좋아졌는지·다른 질문이 나빠지지 않았는지 어떻게 알까? → Golden Dataset · 프롬프트 버전 고정 · Python 평가 · 변경 전후 회귀 판정.

## 마무리 과제

- [ ] `01_trace.py` 질문을 "출장 숙박비 증빙"으로 바꿔 실행
- [ ] Trace에서 retrieve의 `document_ids`와 ChatOpenAI 입력을 대조
- [ ] Tracing에서 `simulated-failure-case` 열기
- [ ] `failure_category`와 입력을 사례별로 대응
- [ ] q1\_hard `locate` 완성 (A 검색 · B 입력 조립 · C 생성 · D 정상)

## 확인 문제

### OPS1-Q1. 고칠 곳 찾기 (1-1)

교육비 질문에 training 문서는 검색됐고 모델 입력에도 "영수증과 수료증"이 있었는데, 답변에는 영수증만 나왔다. 먼저 손볼 곳은?

① 검색 키워드  
② context 구성 코드  
③ 응답 지시와 필수 사실 검사  
④ 임베딩 모델 교체

<details>
<summary>정답 보기</summary>

**③** — 입력에는 두 증빙이 다 있었으니 근거가 처음 사라진 곳은 생성 이후예요. 검색(①)과 입력 조립(②)은 통과했어요. 모델을 바꾸기 전에 근거가 처음 사라진 단계부터 봐요.

</details>

### OPS1-Q2. 재조회 (1-2)

`01_trace.py` 실행 직후 `02_read_trace.py`를 돌렸더니 관측이 0개였다. 맞는 대응은?

① 잠시 뒤 `02_read_trace.py`만 다시 실행하고, 지역·프로젝트·기간을 확인한다  
② 바로 `01_trace.py`를 다시 실행해 새 답을 만든다  
③ 저장 실패로 판정하고 결과를 지운다  
④ 질문 문장으로 Trace를 검색한다

<details>
<summary>정답 보기</summary>

**①** — 전송(`flush`)과 서버 검색 반영은 다른 단계라 늦게 보일 수 있어요. ②는 생성 토큰이 또 들고, ③은 단정이고, ④는 같은 질문의 다른 실행과 섞여요. Trace ID + 시간 범위로 찾아요.

</details>

### OPS1-Q3. 부모·자식 시간 (1-3)

`qa-with-business-lookup` 1.5초, 그 자식 `lookup-approval` 0.1초, `policy-qa` 1.3초. 사용자가 기다린 시간은?

① 2.9초  
② 1.5초  
③ 1.4초  
④ 1.3초

<details>
<summary>정답 보기</summary>

**②** — 부모 시간에 자식 시간이 이미 들어 있어서 더하면(①) 중복이에요. 전체 시간은 root의 ms이고, 병목은 가장 긴 자식 policy-qa 안에서 다시 찾아요.

</details>

### OPS1-Q4. 판정 순서 (1-4 · q4)

`status="cancelled"`, `ended_at`이 `started_at`보다 빠르고, `document_ids=[]`인 기록의 분류는?

① cancelled  
② retrieval\_empty  
③ incomplete  
④ invalid\_time

<details>
<summary>정답 보기</summary>

**④** — cancelled는 허용 상태라 incomplete(③)는 아니고, 그다음 시각 검사에서 끝 < 시작이라 바로 `invalid_time`을 반환해요. 위에서부터 처음 걸리는 return이 결과라 cancelled(①)·retrieval\_empty(②) 검사까지 내려가지 않아요.

</details>

### OPS1-Q5. 서술형 — 호출 성공 · 응답 완료 · 품질 성공

세 가지가 각각 무엇을 뜻하고 이 키트에서 어디서 확인하는지 설명하라.

<details>
<summary>예시 답안</summary>

호출 성공은 HTTP 요청이 오류 없이 돌아온 것이에요. 응답 완료는 `reply.response_metadata["status"] == "completed"`이고 답이 비어 있지 않은 것으로, `answer()`가 확인하고 아니면 `MODEL_RESPONSE_INCOMPLETE`를 내요. 길이 한도로 잘린 답은 HTTP가 성공이어도 여기서 걸려요. 서버 쪽에서는 02에서 GENERATION의 `end_time`으로 실행 구간이 끝났는지 봐요. 품질 성공은 답이 업무 조건(교육비 20만원 · 영수증과 수료증 · 실제 받은 출처)을 지켰는지로, 완료 점수(`response_completed`)나 "서버 기록 확인"으로는 알 수 없고 기대 답과 비교하는 평가(2장 Golden Dataset)가 필요해요.

</details>

### OPS1-Q6. 서술형 — 검색 없음은 언제 실패인가

`retrieval_empty`로 분류된 기록이 실패인지 아닌지 어떻게 판단하는지, 그리고 `classify`가 문서 ID가 맞는지까지 확인하지 않는 이유를 설명하라.

<details>
<summary>예시 답안</summary>

질문에 기대 행동을 붙여야 알 수 있어요. "재택근무 지원금"처럼 규정 밖 질문이면 검색이 비고 "확인할 수 없습니다"라고 보류하는 게 맞는 행동이고, "자기계발 지원을 받으려면 뭘 내나요?"처럼 표현 차이로 training을 못 찾았다면 검색 실패예요. 이 기대 행동을 질문과 함께 모은 게 Golden Dataset이에요. `classify`는 로그 한 줄만 보기 때문에 문서 목록이 비었는지만 알 수 있고, 들어 있는 ID가 정답 문서인지는 정답 데이터(RAG 8장 Hit/Recall)나 카탈로그가 있어야 판단할 수 있어요.

</details>
