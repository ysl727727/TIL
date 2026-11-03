# 3장. 운영 지표 분석과 개선 — 분모 · 누락값 · 토큰과 지연 · 피드백 · 비용 판단

> 2026-11-03 학습 기록. LLMOps 3일차 수업이에요. 2장이 "프롬프트를 바꿨을 때 품질이 좋아졌나"였다면, 3장은 **"그 변화가 비용 · 속도 · 사용자 반응에서는 어떤가"**를 숫자로 읽는 장이에요. 모의 요청으로 지표의 분모와 누락값을 정하고(3-1), 같은 질문에 문맥 길이만 바꿔 토큰과 지연을 쟀어요(3-2). 실제 Trace에 피드백을 붙여 응답률과 긍정 비율을 나눠 봤고(3-3), 서버에서 비용을 채워 버전별로 집계한 뒤 판정했어요(3-4).
>
> 3장의 한 문장: **숫자를 보기 전에 분모부터 확인한다. 모르는 값은 0으로 채우지 않는다.**

## 학습 목표

- 지표마다 **분모가 다르다**는 걸 알고, 숫자와 함께 분모를 밝힌다.
- 지연 · 비용을 모르는 요청을 0으로 채우지 않는다(**None = 모름, 0 = 확인된 무료**).
- 한 가지(문맥 길이)만 바꿔서 토큰 · 지연을 재고, 실행 순서가 결과를 한쪽으로 몰지 않게 한다.
- 사용자 피드백은 질문 문장이 아니라 그 실행의 `trace_id`에 붙이고, 응답률과 긍정 비율을 따로 본다.
- 비용은 모델 구간(GENERATION)만 더하고, 판정은 **표본 → 비용 확인 → 비용 비교** 순서로 한다.

## 실습 환경

| 항목 | 내용 |
| --- | --- |
| 키트 | `llmops_ch03` (강의별 파일 + `course.py` · `metrics.py`), `uv sync --locked` → `uv run --locked 파일.py` |
| 패키지 | langchain 1.4.5 · langchain-openai 1.7.1 · langfuse 4.17.0 · python-dotenv 1.2.4 · pydantic 2.14.1 (1 · 2장과 같음) |
| 관측 | Langfuse Cloud, 프로젝트 `policy-qa` (Tracing · Scores 화면) |
| 모델 | OpenAI `gpt-5.6-luna` |
| `.env` | 1 · 2장과 같은 키 4개. 3장 폴더에도 따로 있어야 해요 |

## 실습 파일

| 파일 | 강 | 모델 호출 | 실습 상태 |
| --- | --- | --- | --- |
| `01_metrics.py` + `metrics.py` | 3-1 지표 정의와 누락값 | 0회 | ✅ 실행 · q1\_hard 통과 |
| `02_measure.py` | 3-2 토큰과 지연 측정 | 4회 | ✅ 실행 · q2\_hard 통과 |
| `03_feedback.py` | 3-3 오류율과 사용자 피드백 | 0회 | ✅ 실행 · q3\_hard 통과 |
| `04_diagnose.py` | 3-4 지표 기반 개선 판단 | 0회 (Langfuse 조회만) | ✅ 실행 · q4\_hard 통과 |

## 전체 흐름

```text
3-1 정의        01_metrics.py   모의 요청 5개로 지표 계산 — 분모와 누락값            (API 없음)
3-2 측정        02_measure.py   같은 질문에 문맥 길이만 바꿔 토큰·지연 측정          (모델 4회 = 질문 2 × 버전 2)
3-3 사용자 신호  03_feedback.py  실제 Trace에 모의 피드백 기록 — 응답률 vs 긍정 비율   (모델 없음)
3-4 판단        04_diagnose.py  서버에서 비용 채우기 → 버전별 집계 → REVIEW          (Langfuse 조회만)
               → 4장: 기록에 개인정보가 남는다면? 모델이 형식을 어기거나 권한 밖 문서를 읽는다면?
```

```text
01 ── result_01.json (모의 집계, 독립)
02 ── result_02.json (실제 요청 4개: trace_id · usage · latency, cost는 None) ──┬──▶ 03 ── result_03.json (피드백)
                                                                             └──▶ 04 ── result_04.json (비용 채움 + 버전별 요약)
```

- 02를 다시 실행하면 03 · 04도 다시 실행해야 해요. 둘 다 02의 실행 기록(trace\_id)을 읽어요.
- 1 · 2 · 3장을 관통하는 원칙: **모르는 상태 ≠ 성공(1장) → 오류 ≠ 0점(2장) → 모르는 비용 ≠ 0원(3장)**

## 핵심 이론

### 1. 같은 5행이라도 지표마다 들어가는 행이 달라요 (3-1)

| 요청 | status | latency\_ms | cost\_usd |
| --- | --- | --- | --- |
| 1 | completed | 100 | 0.001 |
| 2 | completed | 200 | 0.002 |
| 3 | completed | 900 | **None** |
| 4 | failed | 300 | 0.001 |
| 5 | unknown | **None** | **None** |

| 지표 | 값 | 분모 / 계산 대상 |
| --- | --- | --- |
| error\_rate | 0.2 | 실패 1 ÷ **전체 요청 5** |
| completed · errors · unknown | 3 · 1 · 1 | 미확인은 성공도 실패도 아님 |
| p50 / p95 | 200 / 900 ms | **완료 + 지연 값 있는 3건**만 정렬 |
| known\_cost\_usd | 0.004 | 비용을 아는 3건 (실패한 요청도 과금될 수 있어서 포함) |
| cost\_coverage | 0.6 | 비용을 아는 요청 3 ÷ 전체 5 |
| total\_cost\_usd | **None** | 모르는 비용이 있으면 합계를 확정하지 않음 |

```python
# metrics.py summarize의 핵심 줄
"error_rate": errors / len(rows) if rows else None,               # 분모 = 전체 요청
"p95_ms": times[ceil(0.95 * len(times)) - 1] if times else None,  # nearest-rank
"cost_coverage": len(costs) / len(rows) if rows else None,
"total_cost_usd": sum(costs) if rows and len(costs) == len(rows) else None,  # 전부 알 때만
```

- 지연 값이 없는 요청을 0ms로 채우지 않아요. 0ms는 "아주 빨랐다"라는 거짓 정보예요.
- **None = 모름, 0 = 확인된 무료.** 둘을 섞으면 비용이 실제보다 싸 보여요.
- p95(nearest-rank): 정렬한 뒤 `ceil(0.95 × 개수) − 1`번째. 3건이면 `ceil(2.85) − 1 = 2` → 가장 느린 값. "느린 쪽 5%가 시작되는 지점".
- `if rows else None`: 요청이 0건이면 나눗셈에서 `ZeroDivisionError`가 나니까 먼저 막아요.

#### q1: p95가 좋아진 장애 찾아내기

```python
out.append({**r, "status": "timeout", "latency_ms": None})
```

| | 완료 | 오류율 | 미확인 | p95 |
| --- | --- | --- | --- | --- |
| 평소 | 20/20 | 0.0 | 0 | 900 |
| 장애 (느린 2건 timeout) | 18/20 | 0.0 | 2 | **200** |
| 실제 개선 (900 → 500) | 20/20 | 0.0 | 0 | 500 |

- 장애인데 p95가 **좋아져 보여요.** 느린 요청이 timeout으로 바뀌면서 지연 표본에서 빠졌기 때문이에요. timeout은 failed가 아니라서 오류율도 0이에요.
- 판독 규칙: **p95가 줄었는데 완료율(completed ÷ requests)도 떨어졌으면 "장애 의심"**, 완료율이 그대로면 실제 개선일 수 있어요.

### 2. 한 가지만 바꿔서 비교: 문맥 길이 (3-2)

```python
for index, question in enumerate(questions):          # (0, "식비…"), (1, "숙박…")
    for version in ("before", "after"):
        padding = "\n참고: 회사 정원에는 나무가 있습니다." * 60 if version == "before" else ""
        row = answer(lf, model, question, extra_context=padding, version=version)
        row["case_id"] = f"q{index + 1}"
        row["cost_usd"] = None
        rows.append(row)
```

- 질문 2 × 버전 2 = 모델 4회. 순서는 q1-before → q1-after → q2-before → q2-after로 **번갈아** 돌려요. before를 몰아서 돌리면 그 사이 서버 상태 변화가 한 버전에만 실려요.
- `문자열 * 60` = 60번 반복, `A if 조건 else B` = 한 줄 if.
- before = 관계없는 문장 60줄 추가, after = 깔끔. 근거 문서는 같아요 → **문맥 길이 하나만 바꾼 실험**.
- `extra_context`는 `answer()` 안에서 `context = 문서들 + extra_context`로 붙어서 입력 토큰과 지연이 늘어요.
- `case_id`: before / after 짝짓기용. enumerate는 0부터라서 사람이 읽기 좋게 +1.
- `cost_usd = None`: 비용을 아직 몰라요. 임의 단가를 넣지 않고 3-4에서 서버 값으로 채워요.
- 마무리: `lf.flush()` → `save("result_02.json", rows)` → 첫 Trace URL 출력.

**사용자가 기다린 시간 ≠ 모델 시간**

- `latency_ms`는 `answer()` 전체(검색 + 프롬프트 조립 + 모델 호출) 시간이라 사용자가 기다린 시간에 가까워요.
- 모델 구간 시간은 Trace의 GENERATION에서 따로 봐요. 어느 구간의 시간인지 먼저 확인해요.
- 표본 2개짜리 결과는 **원인을 찾는 단서**이지 결론이 아니에요.

#### q2: "일단 전체 규정을 다 넣자" 제안 검증

```python
padding = ALL_DOCS if version == "all_docs" else ""     # ✅ 변수 값 (규정 전체 문자열)
padding = "ALL_DOCS" if version == "all_docs" else ""   # ❌ 글자 8개 "ALL_DOCS" 그대로

def cites(row):
    return set(re.findall(r"\[(\w+)\]", row["answer"]))  # 답변 문장의 [출처]만, document_ids가 아님
```

- 따옴표가 있으면 문자열 그 자체, 없으면 변수 값이에요(CE `state["field"]` vs `state[field]`와 같은 원리).
- 전체 규정을 넣으면 입력 토큰이 늘고, 관계없는 규정까지 출처로 붙어요. 규정 밖 질문(재택근무)은 **검색은 비었는데 답에 출처가 생겨요.** `document_ids`만 보면 모르고 답변 문장까지 읽어야 해요.

### 3. 피드백은 trace\_id에, 두 비율은 분모가 달라요 (3-3)

```python
lf.create_score(
    trace_id=row["trace_id"],      # 질문 문장이 아니라 그 실행에
    name="demo_feedback",
    value=value,                   # 0 = 싫음, 1 = 좋음
    data_type="BOOLEAN",
    ...
)
```

- 오류 코드에 안 나타나는 실패가 있어요. 답은 완료됐는데 틀리거나, 너무 길거나, 불친절한 경우 → 사용자 피드백으로 보완해요.
- 4개 요청 중 2개에만 피드백 → 응답하지 않은 2건을 만족으로 치지 않아요.
- 모의 피드백이라 `simulation: True`로 저장해서 실제 사용자 평가로 오해하지 않게 해요.

| 지표 | 분모 | 내 결과 |
| --- | --- | --- |
| 피드백 응답률 | **전체 요청** (4) | 2 ÷ 4 = 0.5 |
| 응답자 중 긍정 비율 | **피드백을 준 요청** (2) | 1 ÷ 2 = 0.5 |

- 낮은 점수가 달린 Trace → 답변과 근거를 직접 읽기 → 반복되는 문제면 **2장 golden 평가 데이터로** 추가해요.

#### q3: 중복 클릭 피드백 정리

```python
known = {r["trace_id"] for r in rows}
for c in clicks:
    if c["trace_id"] not in known:        # 지난주 Trace 클릭은 건너뜀
        continue
    lf.create_score(trace_id=c["trace_id"], name="user_feedback", value=c["value"],
                    data_type="BOOLEAN", score_id=f'{c["trace_id"]}-{c["user"]}')
```

- `score_id`를 **trace\_id + user**로 정하면 같은 사람이 같은 답을 다시 누를 때 새 점수가 쌓이지 않고 **덮어써요**(더블 클릭 · 마음 바꿈).
- trace\_id만 쓰면 "한 답변에 두 사람"이 누른 경우 뒤 사람 점수가 앞 사람 점수를 지워요.
- 응답률 = 점수가 있는 **Trace 수**(set) ÷ 전체 요청, 긍정 비율 = 긍정 수 ÷ 점수 수(점수가 없으면 None).

### 4. 서버에서 비용을 채우고, 순서대로 판정해요 (3-4)

```text
① result_02.json 읽기 → ② 요청마다 서버에서 GENERATION 비용 합산 → ③ before / after 각각 summarize → ④ 저장, 판정 REVIEW
```

```python
observations = lf.api.observations.get_many(
    trace_id=row["trace_id"], limit=30, fields="core,basic,usage,model",
    from_start_time=시작 - 1분, to_start_time=지금 + 1분,
).data
generations = [o for o in observations if o.type.upper() == "GENERATION"]
costs = [o.total_cost for o in generations]
row["cost_usd"] = sum(costs) if costs and all(c is not None for c in costs) else None
```

| name | type | total\_cost |
| --- | --- | --- |
| policy-qa | SPAN (부모) | 0.00042 ← 자식 비용이 합쳐 보일 수 있음 |
| retrieve | SPAN | None |
| generate-answer | **GENERATION** | 0.00042 ← 실제 모델 호출 |

- observation = Trace 안의 기록 하나하나(policy-qa, retrieve, generate-answer). `.data`는 응답 `{data: [...], meta: {...}}`에서 목록만 꺼내요.
- 앞뒤 1분 여유: 시계 오차는 허용하고 다른 실행은 섞이지 않게(1장 재조회와 같은 생각).
- 전부 더하면 0.00084로 **두 배** → GENERATION만 더해야 정확해요(1장 "부모 시간에 자식 포함"과 같은 함정).
- 모델 구간이 없거나(`sum([])`은 0이라 `costs and`로 막음) 하나라도 None이면 None이에요.
- `sleep(2.1)`: 무료 계정 조회 API 제한 때문이에요.

```python
summary = {v: summarize([r for r in rows if r["app_version"] == v]) for v in ("before", "after")}
```

- dict 컴프리헨션 → `{"before": {...}, "after": {...}}`. 2장 `[r for r in rows if r["split"] == split]` 고르기와 같은 패턴이에요.
- 판정은 **REVIEW**: 버전당 2건뿐이라 단정할 수 없고, 답 내용 · 출처도 사람이 확인해야 해요.

#### q4: 가격을 모르는 모델로 바꾼 상황 판정

```python
b, a = [summarize([r for r in rows if r["app_version"] == v]) for v in ("before", "after")]
if a["completed"] < min_samples:               return "REVIEW: 표본 부족", b, a
if a["cost_coverage"] < 1.0:                   return "REVIEW: 비용 미확인", b, a
if a["total_cost_usd"] > b["total_cost_usd"]:  return "REVIEW: 비용 증가", b, a
return "유지 후보", b, a
```

- `b, a = [두 개짜리 리스트]` → 순서대로 나눠 담아요.
- **순서가 중요해요.** 비용 미확인을 먼저 거르지 않으면 `None > 숫자` 비교에서 TypeError가 나요. 1장 `classify`처럼 "처음 걸리는 return이 결과".
- 가격을 모르는 후보는 비용이 None → "싸졌다"가 아니라 **비용 미확인**이에요.
- 이 판정기엔 품질 조건이 없어요 → 실제로는 2장 rule\_pass 같은 품질 검사와 **함께** 봐야 해요.

## `course.py` 다시 보기 (1장과 같은 코드)

### `connect()`

```text
① .env 읽기 → ② LangSmith 추적 끔 → ③ 필수 키 4개 확인(없으면 ValueError)
→ ④ Langfuse(lf) 생성 → ⑤ atexit로 lf.shutdown 예약 → ⑥ ChatOpenAI(model) 생성 → return lf, model
```

- `missing = [key for key in required if not os.getenv(key, "").strip()]`: 비었거나 공백뿐인 키만 골라요.
- Langfuse: `environment="llmops-course"`(화면 필터), `sample_rate=1.0`(100% 기록), `mask_otel_spans`.
- ChatOpenAI: `model=os.getenv("OPENAI_MODEL") or 기본값`, `max_retries=0`(실패를 숨기지 않음), `timeout=60`, `max_tokens=400`, `use_responses_api=True`(응답 status 확인), `store=False`.

### `answer()`

```text
① 시작 시각 · 타이머
② policy-qa(root) 열기
   ③ retrieve(step): 키워드로 문서 찾기 → document_ids 기록
   ④ context = 문서들 + extra_context          ← 3장에서 길이를 바꾸는 자리
   ⑤ prompt = [system: instruction] + [human: 근거 + 질문]
   ⑥ 모델 호출 (generate-answer, handler가 자동 기록)
   ⑦ 미완성 · 빈 답 → RuntimeError
   ⑧ result dict, root에 답 · 상태 기록
return result  (question, answer, status, trace_id, started_at, app_version, document_ids, usage, latency_ms)
```

- 3장 연결: `extra_context`로 길이를 바꿔 usage · latency를 비교하고, `version` → `app_version`으로 그룹을 나눠요.

## 실행 결과

| case | 버전 | 입력 토큰 | 출력 토큰 | 지연 (ms) | 비용 (USD, 04에서 채움) |
| --- | --- | --- | --- | --- | --- |
| q1 식비 | before | 858 | 25 | 2018.5 | 0.0002016 |
| q1 식비 | after | 138 | 27 | 1178.2 | 0.0000600 |
| q2 숙박 | before | 860 | 23 | 1050.7 | 0.0001996 |
| q2 숙박 | after | 140 | 22 | 1207.3 | 0.0000544 |

| 버전 | p50 | p95 | 전체 비용 | 비용 파악률 |
| --- | --- | --- | --- | --- |
| before | 1534.6 ms | 2018.5 ms | 0.0004012 | 1.0 |
| after | 1192.75 ms | 1207.3 ms | 0.0001144 | 1.0 |

- 입력 토큰 약 **84% 감소**(858 → 138), 비용 약 **71% 감소**. 출력 토큰은 거의 같아요.
- 지연은 q1은 줄었는데 q2는 오히려 after가 조금 느렸어요(1050.7 → 1207.3) → **표본 2개로는 지연을 단정할 수 없는** 좋은 예.
- 03 피드백: before q1에 0("설명이 길다"), after q1에 1("간결하다") → 응답률 0.5, 긍정 비율 0.5.
- 04 판정: **REVIEW** (버전당 2건).

## 질문과 새로 알게 된 점

### `{**r, ...}` — dict 풀기와 덮어쓰기

```python
r = {"q": "식비", "status": "completed", "latency_ms": 900}
new = {**r, "status": "timeout", "latency_ms": None}
```

```text
① **r 풀기     → q: 식비 / status: completed / latency_ms: 900
② "status"     → completed → timeout     (덮어씀)
③ "latency_ms" → 900 → None              (덮어씀)
결과: {"q": "식비", "status": "timeout", "latency_ms": None}
```

- `**r`은 r 안의 키 · 값을 그 자리에 그대로 펼쳐 놓아요. 새 dict라서 원본 r은 그대로예요(`.copy()` 후 수정과 같은 효과).
- dict는 **왼쪽부터 차례로** 채우고, 같은 키가 다시 나오면 **나중 값이 이겨요.**
- `latency_ms: None` = 시간 모름. 0이면 "0ms 걸림"이라 뜻이 달라요.

**순서를 바꾸면** — `**r` 뒤에 아무것도 없어도, 이번엔 `**r` 자체가 맨 뒤라서 덮어쓰는 쪽이 돼요.

| 코드 | 펼치면 | 마지막 status |
| --- | --- | --- |
| `{**r, "status": "timeout"}` | `{"q": "식비", "status": "completed", "status": "timeout"}` | **timeout** ✅ |
| `{"status": "timeout", **r}` | `{"status": "timeout", "q": "식비", "status": "completed"}` | **completed** ❌ |

→ 바꿀 값은 항상 `**r` **뒤에** 써요.

### `*args` vs `**kwargs`

```python
def f(*args):        # 이름표 없는 값 → 튜플
    print(args)
f(1, 2, 3)           # (1, 2, 3)

def g(**kwargs):     # 이름표 있는 값 → dict
    print(kwargs)
g(x=1, y=2)          # {'x': 1, 'y': 2}

f(x=1)               # ❌ TypeError — *args는 이름표 있는 값을 못 받음
g(1, 2)              # ❌ TypeError — **kwargs는 이름표 없는 값을 못 받음

def h(a, *args, **kwargs): ...
h(1, 2, 3, x=10, y=20)   # a=1, args=(2, 3), kwargs={'x': 10, 'y': 20}
```

| | `*args` | `**kwargs` |
| --- | --- | --- |
| 받는 것 | 이름표 **없는** 값 `f(1, 2)` | 이름표 **있는** 값 `f(x=1)` |
| 모이는 모양 | 튜플 `(1, 2)` | dict `{'x': 1}` |
| 값 자리에 쓰면 (풀기) | `[*[1, 2], 3]` → `[1, 2, 3]` | `{**{'x': 1}, 'y': 2}` → `{'x': 1, 'y': 2}` |

- `def` 안에 쓰면 **모으고**, 값 자리(dict · list 안, 함수 호출)에 쓰면 **풀어요**. 3장 `{**r}`은 푸는 쪽이에요.
- 별 하나는 줄 세운 값(순서), 별 두 개는 이름표 붙은 값(키:값)을 다뤄요.

### `get_many`는 누가 정한 이름?

- `lf.api.observations.get_many(...).data`에서 우리가 정한 건 `lf`(변수)뿐이에요. `.api` · `.observations` · `.get_many` · 이름표 인자(`trace_id`, `fields` …) · `.data`는 전부 **Langfuse가 정한 이름**이에요. 키트의 `.venv` 안 Langfuse 코드에서 `def get_many(`를 직접 찾아 확인했어요.
- 2장 `create_prompt` · `get_prompt`, 3장 `create_score` · `get_many`처럼 **Langfuse 메서드 이름을 기억해 두기.**

### 그 밖에

- **같은 자료인지 확인:** 강의 자료를 두 번 받았을 때 ZIP은 md5가 같아서 완전히 동일했고, PPT는 표지 부제와 쪽 번호만 바뀐 재저장본이었어요.
- **0과 1로 피드백을 받는 이유:** 좋다 / 싫다(BOOLEAN)가 가장 단순해서예요. 5점 rating 같은 NUMERIC 점수도 가능해요.
- **p95를 보는 이유:** 평균은 느린 요청 몇 개가 묻혀요. 이상치 · 분산까지 같이 생각해야 해요.
- **metrics.py처럼 지표 계산을 모듈로 빼 두는 이유:** 실무에서도 지표 함수를 한곳에 모아 두고 여러 스크립트가 같은 정의를 쓰게 해요. 그래야 "오류율"이 파일마다 다르게 계산되지 않아요.
- **생각해 볼 것:** 피드백 · 비용 판단이 실제 서비스나 내 프로젝트에서는 어떻게 이어질까?

## 실습 코드에서 직접 바꾼 점

원본 `llmops_ch03.zip`과 비교한 결과예요. 키트 코드는 올리지 않고 바꾼 부분만 적어요.

| 파일 | 바꾼 점 / 추가한 주석 |
| --- | --- |
| `metrics.py` | `summarize`에 `# 실무에서도 다양한 지표들을 모듈화해서 만들어놓음.`, p95 줄에 `#올림. 3이나옴. -1 == 2 ceil은 int임. 평균이 많이쓰이지만 이상치 확인필수.분산.표준편차고려`, cost\_coverage 줄에 `#else None은 나누기 에러발생 막기위해서.` |
| `03_feedback.py` | `# 0과 1인 이유: 싫은지 좋은지 or rating (ex.5점까지~) 등등`, `# create.score langfuse 매서드`, `# 나중에 실제서비스상황이나 내 프로젝트에서 어떻게 이어질까? 생각해보기` |
| `q1_easy.py` | 빈칸 채우기 (`limit_ms`, `"timeout"`, 이전 완료율) |
| `q1_hard.py` | `incident` · `read_dashboard` 구현, `# 딕셔너리 풀어서 넣기 키값이 같으면 벨류값 덮어씌움.` |
| `q2_hard.py` | narrow / all\_docs 번갈아 실행, `cites`를 `re.findall(r"\[(\w+)\]", ...)` + set으로 구현 |
| `q3_hard.py` | 모르는 Trace 건너뛰기, `score_id=f'{trace_id}-{user}'`, 응답률 · 긍정 비율, `# numeric: 0,1,2 rating도 가능하고 boolean도 가능.` |
| `q4_hard.py` | GENERATION 비용 채우기 → `b, a` 집계 → 표본 · 비용 미확인 · 비용 증가 순서로 판정 |
| `.env.example` | `.env`로 만들어 키 입력 (`.env`는 공개하지 않음) |

- `q1_easy`의 이전 완료율을 `before["completed"] / after["requests"]`로 썼어요. 두 쪽 요청 수가 20으로 같아서 통과했지만, 분모는 `before["requests"]`가 맞아요(`q1_hard`에서는 맞게 씀). 3장 주제 그대로 **분모 확인**.

## 하루 정리 (PPT)

- 3장 결과물: **분모를 밝힌 지표와 근거 있는 판단.** 3-1 지표 정의(분모 · None, p50 / p95), 3-2 실제 측정(usage · latency\_ms, 같은 case\_id), 3-3 사용자 신호(Trace에 피드백, 응답률 ≠ 긍정 비율), 3-4 개선 판단(확인된 비용, 경보 · 복원).
- 4장으로 이어지는 질문: 기록에 개인정보가 남는다면? 모델이 형식을 어기거나 권한 밖 문서를 읽는다면? → 신뢰 경계와 권한 통제 · 마스킹 · 출력 검증 · 지시 주입 평가.

## 마무리 과제 (선택)

> 필수가 아니라서 참고용으로만 남겨요.

- `result_04.json`에서 같은 case\_id의 before · after 토큰 · 지연 · 비용을 나란히 읽기
- q1 before와 after의 답변을 읽고 금액 · 서류 · 출처가 유지됐는지 직접 확인

## 확인 문제

> 객관식 6 · 단답형 6, 섞어서 배치했어요. **정답 보기**를 누르면 열려요.

### OPS3-Q1. 객관식 — 모르는 비용

`01_metrics.py`의 5행(비용 None이 2개)을 `summarize`했을 때 `total_cost_usd`는?

① 0.004  
② 0  
③ None  
④ 0.0024

<details>
<summary>정답 보기</summary>
<p><b>③ None</b> — 비용을 아는 건 5건 중 3건뿐이라(cost_coverage 0.6) 합계를 확정하지 않아요. 아는 것만 더한 0.004는 <code>known_cost_usd</code>로 따로 남겨요. None을 0으로 채우면 비용이 실제보다 싸 보여요.</p>
</details>

### OPS3-Q2. 단답형 — dict 풀기

`r = {"status": "completed", "latency_ms": 900, "cost_usd": 0.001}`일 때 `{**r, "status": "timeout", "latency_ms": None}`의 결과는? 순서를 바꿔 `{"status": "timeout", **r}`로 쓰면 status는?

<details>
<summary>정답 보기</summary>
<p><code>{"status": "timeout", "latency_ms": None, "cost_usd": 0.001}</code> — <code>**r</code>로 전부 펼친 뒤 뒤에 쓴 같은 키가 덮어써요. 원본 r은 그대로예요.</p>
<p>순서를 바꾸면 <code>**r</code>이 맨 뒤라서 r의 값이 나중에 덮어써요. status는 다시 <b>"completed"</b>가 돼요.</p>
</details>

### OPS3-Q3. 객관식 — 오류율의 분모

`summarize`에서 `error_rate`의 분모는?

① 전체 요청 수  
② 완료된 요청 수  
③ 완료 + 실패 요청 수  
④ 지연 값이 있는 요청 수

<details>
<summary>정답 보기</summary>
<p><b>①</b> — 실패율은 "들어온 요청 중 얼마나 실패했나"라서 전체 요청(미확인 포함)이 분모예요. 반면 p50·p95는 완료 + 지연 값 있는 요청만 써요. 지표마다 분모가 달라요.</p>
</details>

### OPS3-Q4. 단답형 — 좋아 보이는 장애

q1에서 평소 p95는 900ms였는데 장애 때는 200ms로 "좋아졌다". 왜 그렇게 보였고, 장애를 알아채려면 무엇을 같이 봐야 하나?

<details>
<summary>정답 보기</summary>
<p>느린 요청 2개가 timeout이 되면서 <code>latency_ms</code>가 None이 되어 <b>지연 표본에서 빠졌기</b> 때문이에요. 빠른 요청만 남으니 p95가 내려갔어요.</p>
<p><b>완료율</b>(completed ÷ requests, 20/20 → 18/20)을 같이 봐요. p95가 줄었는데 완료율도 떨어졌으면 "장애 의심"이에요. timeout은 failed가 아니라 오류율도 0이라 오류율만 봐서는 못 잡아요.</p>
</details>

### OPS3-Q5. 객관식 — 번갈아 실행

`02_measure.py`가 q1-before → q1-after → q2-before → q2-after처럼 번갈아 실행하는 이유는?

① 모델 호출 비용을 줄이려고  
② case_id를 만들려고  
③ 프롬프트 캐시를 쓰려고  
④ 시간에 따른 변화(서버 상태 등)가 한 버전에만 몰리지 않게 하려고

<details>
<summary>정답 보기</summary>
<p><b>④</b> — before를 다 돌리고 after를 몰아서 돌리면, 그 사이 서버가 느려지거나 빨라진 효과가 한 버전에만 실려요. 번갈아 돌리면 그 영향이 양쪽에 고르게 퍼져요.</p>
</details>

### OPS3-Q6. 단답형 — 따옴표 하나 차이

q2에서 `padding = ALL_DOCS if version == "all_docs" else ""`와 `padding = "ALL_DOCS" if ...`의 차이는?

<details>
<summary>정답 보기</summary>
<p>따옴표가 없으면 <b>변수 ALL_DOCS의 값</b>(규정 전체 문자열)이 들어가고, 따옴표가 있으면 <b>"ALL_DOCS"라는 글자 8개</b>가 그대로 들어가요. CE의 <code>state["field"]</code>(글자 키) vs <code>state[field]</code>(변수 값)와 같은 원리예요.</p>
</details>

### OPS3-Q7. 객관식 — 피드백 두 비율

요청 4건 중 2건에 피드백이 달렸고 값이 0, 1이다. 응답률 / 긍정 비율은?

① 0.5 / 0.25  
② 0.5 / 0.5  
③ 0.25 / 0.5  
④ 1.0 / 0.5

<details>
<summary>정답 보기</summary>
<p><b>②</b> — 응답률은 분모가 <b>전체 요청</b>(2 ÷ 4 = 0.5), 긍정 비율은 분모가 <b>피드백을 준 요청</b>(1 ÷ 2 = 0.5)이에요. ①은 긍정 수를 전체 요청으로 나눈 실수예요. 응답 안 한 2건을 만족으로 치면 안 돼요.</p>
</details>

### OPS3-Q8. 단답형 — score\_id

q3에서 `score_id`를 `f'{trace_id}-{user}'`로 만든 이유는? trace\_id만으로 만들면 어떤 경우가 틀어지나?

<details>
<summary>정답 보기</summary>
<p>같은 사람이 같은 답을 다시 누르면(더블 클릭, 마음 바꿈) 점수가 새로 쌓이지 않고 <b>같은 ID로 덮어쓰게</b> 하려고요.</p>
<p>trace_id만 쓰면 <b>한 답변에 두 사람</b>이 누른 경우 뒤 사람 점수가 앞 사람 점수를 덮어써서 한 명의 의견이 사라져요.</p>
</details>

### OPS3-Q9. 객관식 — GENERATION만 더하기

`04_diagnose.py`가 비용을 합칠 때 GENERATION 구간만 고르는 이유는?

① 조회가 더 빨라서  
② SPAN에는 비용 칸이 아예 없어서  
③ 부모 SPAN에 자식 비용이 합쳐 보일 수 있어서, 다 더하면 두 배가 되어서  
④ retrieve 구간 비용이 더 비싸서

<details>
<summary>정답 보기</summary>
<p><b>③</b> — policy-qa(부모)가 0.00042, generate-answer(GENERATION)도 0.00042이면 전부 더해 0.00084로 두 배가 돼요. 실제 모델 호출은 GENERATION이라 거기만 더해요. 1장 "부모 시간에 자식 시간이 포함"과 같은 함정이에요.</p>
</details>

### OPS3-Q10. 단답형 — 비용 채우기 규칙

`row["cost_usd"] = sum(costs) if costs and all(c is not None for c in costs) else None`에서 `costs = [0.0002, None]`일 때와 `costs = []`일 때의 결과와 이유는?

<details>
<summary>정답 보기</summary>
<p>둘 다 <b>None</b>이에요.</p>
<p><code>[0.0002, None]</code>: 하나라도 모르면 합계를 확정할 수 없어요. 아는 것만 더하면 비용을 적게 잡게 돼요.</p>
<p><code>[]</code>: 모델 구간을 못 찾았다는 뜻이라 "0원"이 아니라 "모름"이에요. <code>sum([])</code>은 0이라서 <code>costs and</code> 조건으로 먼저 막아요.</p>
</details>

### OPS3-Q11. 객관식 — 판정 순서

q4 판정기에서 `cost_coverage < 1.0` 검사를 `total_cost_usd` 비교보다 **먼저** 해야 하는 이유는?

① 비용을 모르면 total_cost_usd가 None이라 `None > 숫자` 비교에서 TypeError가 나서  
② 표본 수 검사보다 중요해서  
③ cost_coverage가 계산이 더 빨라서  
④ 순서는 상관없고 보기 좋게 쓴 것

<details>
<summary>정답 보기</summary>
<p><b>①</b> — 비용 미확인이 있으면 total_cost_usd가 None이에요. 이걸 먼저 걸러 "REVIEW: 비용 미확인"으로 돌려주지 않으면 다음 줄의 크기 비교에서 오류가 나요. 1장 <code>classify</code>처럼 위에서부터 처음 걸리는 return이 결과예요.</p>
</details>

### OPS3-Q12. 단답형 — 내 결과 해석

내 실행에서 after는 입력 토큰이 858 → 138로, 비용이 0.000401 → 0.000114로 줄었다. 그런데도 04의 판정이 "유지"가 아니라 REVIEW인 이유 두 가지는?

<details>
<summary>정답 보기</summary>
<p>① <b>표본이 버전당 2건뿐</b>이라 단정할 수 없어요. 실제로 지연은 q1은 줄었는데 q2는 오히려 늘었어요(1050.7 → 1207.3).</p>
<p>② 비용 · 지연 지표에는 <b>답변 품질이 없어요</b>. 답 내용과 출처가 여전히 맞는지 사람이 확인하거나 2장 같은 품질 평가를 함께 봐야 해요.</p>
</details>
