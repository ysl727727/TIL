# 2장. 평가 데이터와 변경 전후 검증 — Golden Dataset · 프롬프트 버전 · Python 평가 · 회귀 판정

> 2026-11-02 학습 기록. LLMOps 2일차 수업이에요. 기대 행동을 담은 질문 6개를 검사해 Langfuse에 dev 4 · holdout 2 데이터셋으로 올렸고(2-1), 같은 이름에 기준선 v1 · 후보 v2 프롬프트를 버전 번호로 고정했어요(2-2). dev 4개를 두 버전으로 실행해 Python 규칙 4개로 채점했고(2-3), 질문 ID로 짝지어 비교해 통과한 후보만 holdout으로 확인했어요(2-4).

## 학습 목표

- 정답 문장 하나가 아니라 **기대 행동**(꼭 들어갈 표현 · 붙어야 할 출처 · 보류 여부)으로 평가 질문을 만든다.
- 질문 · 문서 · 검색 · 모델 · 평가기를 고정하고 **프롬프트 하나만** 바꿔서 비교한다.
- 프롬프트는 `latest`가 아니라 **정확한 버전 번호**로 가리킨다.
- 완료됐는데 틀린 답(0점)과 평가할 답이 없는 실패(오류)를 구분한다.
- 평균이 아니라 **질문 ID별로** 변경 전후를 비교하고, 하나라도 나빠지면 막는다.

## 실습 환경

| 항목 | 내용 |
| --- | --- |
| 키트 | `llmops_ch02` (강의별 파일 + `course.py` · `evaluation.py` · `golden.json`), 폴더마다 `uv sync --locked` → `uv run --locked 파일.py` |
| 패키지 | langchain 1.4.5 · langchain-openai 1.7.1 · langfuse 4.17.0 · python-dotenv 1.2.4 · pydantic 2.14.1 (1장과 같음) |
| 관측 | Langfuse Cloud, 프로젝트 `policy-qa` (Datasets · Prompt Management · Experiments 화면) |
| 모델 | OpenAI `gpt-5.6-luna` |
| `.env` | 1장과 같은 키 4개. 2장 · 3장 폴더 **각각**에 `.env`가 있어야 해요 |

## 실습 파일

| 파일 | 강 | 모델 호출 | 실습 상태 |
| --- | --- | --- | --- |
| `01_dataset.py` | 2-1 Golden Dataset 설계와 등록 | 0회 | ✅ 실행 · q1\_hard 통과 |
| `02_prompts.py` | 2-2 프롬프트 버전과 비교 조건 고정 | 0회 | ✅ 실행 · q2\_hard 통과 |
| `03_evaluate.py` + `evaluation.py` | 2-3 Python 평가와 Langfuse 실험 | 8회 | ✅ 실행 · q3\_hard 선택(안 함) |
| `04_compare.py` | 2-4 변경 전후 비교와 회귀 판정 | 0 또는 2회 | ✅ 실행 · q4\_hard 선택(안 함) |

## 전체 흐름

```text
2-1 질문 고정   golden.json 6개 검사 → dev 4 · holdout 2 데이터셋 등록            (모델 0회)
2-2 변경 하나   같은 이름에 기준선 v1 · 후보 v2 등록, 버전 번호 저장              (모델 0회)
2-3 채점        dev 4개 × 두 버전 실행 → evaluate()로 점수 4개                    (모델 8회)
2-4 판정        질문 ID로 짝지어 비교 → 통과한 후보만 holdout → BLOCK / REVIEW     (모델 0 또는 2회)
               → 3장: 점수는 같은데 더 비싸고 느려졌다면?
```

```text
01_dataset ──result_01.json(데이터셋 이름 2개 + 해시)──▶ 03_evaluate ──result_03.json──▶ 04_compare
02_prompts ──result_02.json(프롬프트 이름 + 버전 1·2)──▶      ▲                              │
                                                         evaluation.py                  holdout
                                                    (evaluate · experiment)          (result_01)
```

## 핵심 이론

### 1. 정답 문장보다 기대 행동 (2-1)

| id | split | kind | 질문 | terms | citations | abstain |
| --- | --- | --- | --- | --- | --- | --- |
| d01 | dev | normal | 식비 한도와 필요한 서류는? | 2만원 · 영수증 | meal | false |
| d02 | dev | normal | 출장 숙박비 한도는? | 10만원 | travel | false |
| d03 | dev | boundary | 교육비를 받으려면 어떤 서류가? | 영수증 · 수료증 | training | false |
| d04 | dev | unanswerable | 재택근무 지원금은? | — | — | **true** |
| t01 | holdout | normal | 교육비 지원 한도는? | 20만원 | training | false |
| t02 | holdout | unanswerable | 반려동물 의료비도 지원되나요? | — | — | **true** |

- d03(경계)은 1장의 "수료증 누락"이, d04 · t02는 1장의 "검색 없음 = 보류가 맞는 행동"이 평가 질문이 된 것이에요.
- `validate(rows)`가 등록 전에 막는 것: ID 중복(ID가 두 실험을 잇는 키), split · 질문 형식, expected 칸이 정확히 `{terms, citations, abstain}`인지, abstain이 진짜 bool인지(`type(...) is not bool`), 없는 문서 ID(`set(...) <= allowed`), 보류인데 terms · citations가 있는 모순.

**`main()`: 한 번 실행에 두 바퀴**

```text
for split in ("dev", "holdout"):
    ① 이름 만들기   llmops-dev-20261102-…  (시각 + 무작위 4글자, 덮어쓰기 방지)
    ② 빈 데이터셋(상자) 만들기
    ③ 지금 차례인 split만 고르기   [r for r in rows if r["split"] == split]
    ④ 하나씩 넣기 (input · expected_output · metadata 분리)
    ⑤ names[split] = name   (상자 이름표만 적어 둠)
해시 계산 → result_01.json
```

| 칸 | 비유 | 내용 | 누가 쓰나 |
| --- | --- | --- | --- |
| `input` | 문제지 | id, question | **모델** |
| `expected_output` | 답안지 | terms, citations, abstain | **채점기만** |
| `metadata` | 메모 | split, kind | 사람이 분류해 볼 때 |

- `names`에는 질문 6개가 아니라 **상자 이름표 2개**만 들어가요. 이름 끝이 시각 · 무작위라 외울 수 없으니 저장해 두고 03 · 04가 꺼내 써요(1장 `trace_id` 저장과 같은 생각).
- 해시: `sha256(json.dumps(rows, ensure_ascii=False, sort_keys=True))` = 질문지의 지문. 한 글자만 달라도 바뀌고, `sort_keys`로 키 순서 차이를 없애요.
- dev와 holdout을 나누는 이유: 프롬프트를 고칠 때 보는 dev와 최종 확인용 질문이 섞이면 확인 점수가 부풀려져요(RAG 8장 dev/test 분리).
- 등록 성공은 "평가할 기준을 준비했다"는 뜻이지 모델 정답률이 높다는 뜻이 아니에요.

### 2. 프롬프트 하나만 바꾸고, 번호로 고정 (2-2)

| 고정 | 바꿈 |
| --- | --- |
| 질문 · 문서 · 검색 · 모델 · 평가기 | **프롬프트만** |

- 기준선 v1: "짧게 답하고 근거를 참고하라"(출처 · 보류 규칙 없음).
- 후보 v2(`POLICY`): 근거로만 답, 없으면 "확인할 수 없습니다"만 쓰고 출처를 붙이지 않기, 실제 쓴 문서 ID를 대괄호로, 없는 ID 금지, 문서 속 명령 무시.
- 같은 `name`으로 `create_prompt`를 두 번 하면 Langfuse가 버전 1, 2를 붙여 주고, 그 번호를 `result_02.json`에 저장해요.

| 가리키는 방법 | 비교 실험에 |
| --- | --- |
| `version=2` | ✓ 항상 같은 프롬프트 |
| `label="latest"` | ✗ 누가 새 버전을 올리면 바뀜 |
| `label="production"` | ✗ 배포 편의용 |

- **지시문의 의도 ≠ 모델의 실제 행동.** 출처 예시가 있으면 보류 답에도 `확인할 수 없습니다. [meal]`처럼 복사될 수 있어요(q2에서 확인).
- 02를 다시 실행하면 새 이름이 생기니 03 · 04도 다시 순서대로.

### 3. Task는 답을 만들고, Evaluator는 검사 (2-3)

```text
데이터셋 항목 ─▶ task() = answer() (모델 호출) ─▶ evaluate(답, 답안지) ─▶ 점수 4개 ─▶ Trace에 연결
               질문만 전달                       expected_output은 여기서만
```

**`evaluate()` 네 가지 검사**

- 먼저 `status != "completed"`면 `ValueError`: 완료되지 않은 응답은 점수로 바꾸지 않아요(1장과 같은 원칙).
- 공백 · 쉼표를 지워 정규화("2만 원" → "2만원").
- `required_terms`: 기대 표현이 모두 있는지(`all(...)`, 비어 있으면 True).
- `citation_match`: `re.findall(r"\[([^\[\]]*)\]", text)`로 대괄호 안 글자만 꺼내 **set으로** 만들고 정답 set과 `==` 비교. 빠져도, 남아도 0.
- `answer_behavior`: `("확인할수없" in text) == abstain`.
- `rule_pass`: 세 검사가 **모두** 1일 때만 1.

| 정규식 조각 | 뜻 |
| --- | --- |
| `\[` · `\]` | 진짜 글자 `[`, `]` |
| `( … )` | 이 안에 걸린 부분만 꺼내기 |
| `[^\[\]]*` | `[`·`]`가 **아닌** 글자 0개 이상 |

| 질문 | 정답 출처 | 모델 답 | citation\_match |
| --- | --- | --- | --- |
| d01 | meal | `… [meal]` | 1 |
| d01 | meal | `… [meal] [travel]` | 0 (남음) |
| d01 | meal | 출처 없음 | 0 (빠짐) |
| d04 | — | `확인할 수 없습니다.` | 1 |
| d04 | — | `확인할 수 없습니다. [meal]` | 0 |

- 반환값은 Langfuse의 `Evaluation(name, value, data_type, comment)` 4개. 이 양식으로 돌려주면 SDK가 그 질문의 Trace에 점수로 붙여 줘요(1장 `create_score`를 대신).
- 문자열 규칙의 한계: terms가 있어도 부정 · 모순일 수 있고, 출처가 맞아도 문장이 그 근거를 지지하는지는 몰라요 → 사람 검토가 남아요.

**`experiment()` = 시험 한 번 치르기**

```text
시험지 4장(d01~d04) → 학생(모델)이 풀기 → 선생님(evaluate)이 채점 → 성적표(rows)
```

- `task(*, item, **kwargs)`: 시험지 한 장을 받으면 질문만 꺼내 `answer()`를 부르는 **푸는 법**. 정의만 한 것이지 아직 푼 게 아니에요.
- `instruction=prompt.prompt`: `get_prompt`로 받은 프롬프트 **객체(봉투)**에서 실제 지시 문장만 꺼내 system 메시지로 넣어요.
- `dataset.run_experiment(task=task, evaluators=[evaluate], max_concurrency=1)`: 함수를 괄호 없이 넘기면 **SDK(감독)가 for문을 대신 돌려** 항목마다 task → evaluate를 불러 줘요.
- rows: `{id, output, scores, error, trace_id}`. 답이 없거나 점수가 4개가 아니면 `error = "INCOMPLETE_EVALUATION"`.
- 03 메인: `for label in ("baseline", "candidate")`, `get_prompt(name, version=번호, cache_ttl_seconds=0)` → 같은 시험지 · 같은 채점기로 두 번. 오류가 있으면 결과는 저장하고 `EXPERIMENT_HAS_ERRORS`.

| 상황 | 처리 |
| --- | --- |
| 완료됐는데 출처가 틀림 | **0점** (정상 평가 결과, 비교에 포함) |
| API 실패 · 응답 미완료 | **오류** (평가할 답이 없음, 0점으로 채우지 않음) |
| 평가기를 바꿈 | 기준선과 후보를 **둘 다** 다시 채점 |

### 4. 질문 ID로 짝짓고, 하나라도 나빠지면 BLOCK (2-4)

- 결과가 d04 · d03 · d02 · d01처럼 섞여 와요. `{r["id"]: r for r in rows}`로 ID 사전을 만들어 짝지어요(CE 4장 `bodies[meta["id"]]`와 같은 교훈).
- `delta = 후보 rule_pass − 기준선 rule_pass` (질문마다), `accepted = passed == 4 and min(delta) >= 0`.

| 질문 | 기준선 | 후보 | 차이 |
| --- | --- | --- | --- |
| d01 | 0 | 1 | +1 |
| d02 | 0 | 1 | +1 |
| d03 | 1 | 1 | 0 |
| d04 | 1 | 0 | **−1** |
| 평균 | 50% | 75% | |

→ 평균은 +25%p인데 보류해야 하는 d04가 나빠져서 **BLOCK**.

| 판정 | 다음 행동 |
| --- | --- |
| BLOCK | 해당 질문 Trace와 기대값 검토 |
| CHECK\_HOLDOUT | 후보만 처음 보는 질문(holdout 2개)으로 확인 → 모델 2회 |
| REVIEW | 통과해도 자동 배포가 아니라 사람이 답변 · 넓은 표본 · 운영 조건 검토 |

- 실패하면 프롬프트만이 아니라 검증된 조합(모델 · 코드 · 검색 설정 · 문서 버전)으로 돌아가요. 이 코드는 판정까지만 하고 production 라벨은 건드리지 않아요.

## 실행 결과

```text
01  dev llmops-dev-20261102-002821-1a02 · holdout llmops-holdout-20261102-002824-19cb
02  llmops-policy-20261102-011327-e91e  기준선 1 · 후보 2
03  gpt-5.6-luna, 모델 8회
04  CHECK_HOLDOUT (후보 4/4, delta d01 +1 · d02 +1 · d03 +1 · d04 0)
    holdout t01 "연간 20만원입니다. [training]" · t02 "확인할 수 없습니다." 모두 통과 → 최종 REVIEW
```

| 질문 | 기준선 rule\_pass | 후보 rule\_pass | 비고 |
| --- | --- | --- | --- |
| d01 | 0 | 1 | 기준선은 내용은 맞았지만 출처 없음 |
| d02 | 0 | 1 | 〃 |
| d03 | 0 | 1 | 〃 |
| d04 | 1 | 1 | 표현만 다름("제공된 근거만으로는 … 확인할 수 없습니다" vs "확인할 수 없습니다") |

- 프롬프트에 출처 규칙을 넣은 효과가 citation\_match로 바로 보였어요. "2만 원"처럼 띄어 써도 정규화 덕분에 통과.
- 토큰: 기준선 72\~98 → 후보 125\~165. 후보 프롬프트가 길어서 질문마다 입력 토큰이 늘었어요 → 3장 "점수는 같은데 더 비싸졌다면?"

## 질문과 새로 알게 된 점

### 환경

- **`uv run` vs `uv run --locked`:** `--locked`는 `uv.lock`과 `pyproject.toml`이 안 맞으면 고치지 않고 멈춰서 강사님 버전을 보장해요.
- **폴더마다 `.env` · `.venv`:** 2장 · 3장 키트가 따로라서 각 폴더에서 `uv sync --locked`. `.env.example`은 양식이라 지우지 않아도 돼요.
- **Langfuse Secret Key는 만들 때 한 번만 보여 줘요.** 다시 못 보니 기존 `.env`에서 복사하거나 새 키 쌍을 만들어 바로 복사.

### 괄호 안 `=`는 이름표, 괄호 밖 `=`는 대입

```python
lf, _ = connect()                            # 괄호 밖 = → 결과를 변수에 대입
name = new_name("llmops-policy")             # 괄호 밖 = → 대입 (new_name엔 * 없어서 순서로 넘김)
baseline = lf.create_prompt(name=name, ...)  # 괄호 안 = → 이름표
```

- `create_prompt(name=name)`: 왼쪽 `name`은 Langfuse가 정한 매개변수 이름, 오른쪽 `name`은 바로 위에서 만든 변수의 값이에요.

### `*` · `*args` · `**kwargs`

| 표기 | 받는 것 | 형태 |
| --- | --- | --- |
| `*` 단독 | 없음 (뒤는 이름표 필수라는 표시) | — |
| `*args` | 이름표 **없이** 넘긴 나머지 | 튜플 |
| `**kwargs` | 이름표를 붙였는데 **그 이름의 자리가 없는** 나머지 | dict |

```python
def f(a, *args, **kwargs): ...
f(1, 2, 3, x=10, y=20)     # a=1, args=(2, 3), kwargs={'x': 10, 'y': 20}

evaluate(output="12만원", expected_output="12만원", input="숙박 한도?", metadata={"id": 1})
# def evaluate(*, output, expected_output, **kwargs) → kwargs = {"input": …, "metadata": …}
```

- Langfuse SDK가 평가 함수를 부를 때 `input` · `metadata` 등도 함께 넘겨요. `**kwargs`가 없으면 모르는 이름표라서 오류. 꺼낼 땐 `kwargs.get("input")`.
- `item` · `output` · `expected_output`은 SDK가 정한 이름이라 못 바꾸고, `task`라는 함수 이름은 우리가 정한 것이라 바꿔도 돼요.

### 이름표 필수 vs 기본값

| 무엇이 정하나 | 정하는 것 |
| --- | --- |
| `*` 뒤에 있는지 | 넘길 때 **이름표가 필요한지** |
| `=기본값`이 있는지 | **생략해도 되는지** |

```python
def connect(*, mask_otel_spans=True): ...
connect()                        # ✅ 생략 → 기본값
connect(mask_otel_spans=False)   # ✅ 넘길 땐 이름표 필수
connect(False)                   # ❌ TypeError
```

- `mask_otel_spans`는 라이브러리 이름이 아니라 강사님이 `course.py`에서 정한 이름이에요. 다만 부를 때는 **정의한 쪽이 정한 이름표만** 쓸 수 있어요(`connect(boom=False)`는 TypeError).

### 리스트 컴프리헨션 풀어 쓰기

```python
picked = []
for r in rows:
    if r["split"] == split:   # "split"(따옴표) = dict 키 이름, split = 바깥 for 변수
        picked.append(r)
```

- "dev만 가져온다"가 아니라 **"지금 차례인 split만 가져온다"**. 한 번 실행에 dev 4개 · holdout 2개 데이터셋이 둘 다 생겨요.

### q2\_hard: pinned vs latest

```python
pinned = lf.get_prompt(name, version=saved["candidate"], cache_ttl_seconds=0)  # 버전 2 = POLICY
latest = lf.get_prompt(name, label="latest", cache_ttl_seconds=0)              # 버전 3 = TEAMMATE
```

- 팀원이 비교 중에 v3을 올린 상황. 번호 고정은 d04 통과, latest는 `확인할 수 없습니다. [meal]`로 citation\_match 0.
- `version`과 `label`은 같이 못 써요. `cache_ttl_seconds=0` = 예전에 읽어 둔 것 말고 매번 새로.
- 처음에 `prompt=baseline`(소문자)으로 써서 `UnboundLocalError` → 등록할 문장은 대문자 상수 `BASELINE`. 대소문자가 다르면 다른 이름이에요.

### q1\_hard: 경조사비 규정 추가

- d05(dev, normal): terms `10만원`, citations `family`, abstain False.
- t03(holdout, unanswerable): 규정에 금액만 있고 휴가 일수는 없어서 빈 기대값 + abstain True. 검색은 되지만 답할 근거가 없는 경우예요.

## 실습 코드에서 직접 바꾼 점

원본 `llmops_ch02.zip`과 비교한 결과예요. 키트 코드는 올리지 않고 바꾼 부분만 적어요.

| 파일 | 바꾼 점 / 추가한 주석 |
| --- | --- |
| `01_dataset.py` | `for split in ("dev", "holdout"):`에 핵심 for문이라는 주석 |
| `03_evaluate.py` | `connect() # 모델 씀.`, `get_dataset(...) #클라우드에 올려놓은것 가져오기`, `# 03의 메인 for문`, `#프롬프트만 바꾸는것.` |
| `evaluation.py` | `# 총 4가지 검사.`, `#텍스트 정규식 이용. llm이 준 답변에 대해`, `#기대용어가 잘 들어가있는지.`, `# 대괄호?`, `# Evaluation 객체?`, `run_experiment( ##중요.`, `task=task, #함수가 변수로 들어감.` |
| `q1_hard.py` | `NEW_ROWS`에 d05 · t03 작성 (+ 휴가 일수가 없다는 주석) |
| `q2_hard.py` | pinned · latest 구현, `## create_prompt, get_prompt 등 랭퓨즈 매서드 기억하기.` |
| `.env.example` | `.env`로 만들어 키 입력 (`.env`는 공개하지 않음) |

`q3_hard.py` · `q4_hard.py`는 아직 원본 그대로예요.

## 하루 정리 (PPT)

- 2장 결과물: **같은 질문 · 같은 규칙 · 질문별 판정.** 2-1 Golden Dataset(dev 4 · holdout 2, 기대 행동 고정), 2-2 프롬프트 버전(1 · 2, 나머지는 고정), 2-3 Python 평가(규칙 점수 4개, 오류 ≠ 0점), 2-4 회귀 판정(ID로 비교, BLOCK · REVIEW).
- 3장으로 이어지는 질문: 점수는 같은데 더 비싸고 느려졌다면? 실제 사용자 요청의 오류와 불만은 어떻게 읽을까? → 운영 지표 · 토큰과 지연 측정 · 오류율과 피드백.

## 마무리 과제 (선택)

> 필수가 아니라서 하지 않았어요. 나중에 볼 때 참고용으로만 남겨요.

- `result_03.json`에서 d04 답변 두 개 비교 (기준선과 후보가 보류를 어떻게 표현했는지)
- Experiments **Compare** 화면에서 d04 행을 찾아 기준선과 후보 답변을 나란히 읽기
- Prompt Management에서 버전 #1 · #2를 열어 추가된 지시가 어떤 실패를 줄이려는지 읽기
- q3\_hard (사라진 실패 행 찾기) · q4\_hard (6건 기준 compare: 중요 질문 악화 BLOCK, 통과율 ≥ min\_rate)

## 확인 문제

> 객관식 5 · 단답형 5

### OPS2-Q1. 프롬프트 고정 (2-2)

기준선과 후보를 비교하는 실험에서 프롬프트를 가리키는 가장 알맞은 방법은?

① `lf.get_prompt(name, label="latest")`  
② `lf.get_prompt(name, version=2, cache_ttl_seconds=0)`  
③ `lf.get_prompt(name, label="production")`  
④ `lf.get_prompt(name)` (이름만)

<details>
<summary>정답 보기</summary>

**②** — 번호로 가리키면 누가 새 버전을 올려도 같은 프롬프트예요. `latest`는 팀원이 v3을 올리면 바로 v3으로 바뀌어요(q2). `cache_ttl_seconds=0`은 매번 새로 받기.

</details>

### OPS2-Q2. 보류 질문 채점 (2-3)

d04(기대값: terms 없음, citations 없음, abstain True)에 모델이 `확인할 수 없습니다. [meal]`이라고 답했다. 점수로 맞는 것은?

① 네 점수 모두 1  
② citation\_match 1, answer\_behavior 0 → rule\_pass 0  
③ required\_terms 0이라서 rule\_pass 0  
④ answer\_behavior 1, citation\_match 0 → rule\_pass 0

<details>
<summary>정답 보기</summary>

**④** — "확인할수없"이 있고 abstain이 True라 answer\_behavior는 1. 꺼낸 출처 `{"meal"}`이 정답 `set()`과 달라 citation\_match는 0. terms가 비면 `all([])`이 True라 required\_terms는 1이에요(③ 오답).

</details>

### OPS2-Q3. 별표 인자

```python
def f(a, *args, **kwargs): ...
f(1, 2, 3, x=10)
```

① `a=1`, `args=(2, 3)`, `kwargs={'x': 10}`  
② `a=1`, `args=[2, 3]`, `kwargs={'x': 10}`  
③ `a=(1, 2, 3)`, `args=()`, `kwargs={'x': 10}`  
④ `a=1`, `args=(2, 3, 10)`, `kwargs={}`

<details>
<summary>정답 보기</summary>

**①** — 이름표 없는 값은 앞에서부터 자리를 채우고(a=1), 남은 2, 3은 **튜플**로 args에(② 리스트 아님). `x=10`은 `x` 자리가 없어서 kwargs dict로.

</details>

### OPS2-Q4. 회귀 판정 (2-4)

기준선 rule\_pass가 d01 0 · d02 0 · d03 1 · d04 1, 후보가 d01 1 · d02 1 · d03 1 · d04 0일 때 `04_compare.py`의 판정은?

① 평균이 50% → 75%로 올랐으니 CHECK\_HOLDOUT  
② 바로 REVIEW  
③ BLOCK  
④ 판정 없이 holdout만 다시 실행

<details>
<summary>정답 보기</summary>

**③** — 후보 통과가 3개이고 d04 delta가 −1이라 `passed == 4 and min(delta) >= 0`이 실패해요. 평균이 올라도 질문 하나가 나빠지면 BLOCK.

</details>

### OPS2-Q5. 이름표 필수

`def connect(*, mask_otel_spans=True)`일 때 **오류가 나는** 호출은?

① `connect()`  
② `connect(False)`  
③ `connect(mask_otel_spans=False)`  
④ `connect(mask_otel_spans=None)`

<details>
<summary>정답 보기</summary>

**②** — `*` 뒤라서 넘길 때는 이름표가 필수. 기본값이 있으니 생략은 괜찮아요(①).

</details>

### OPS2-Q6. 단답형 — 대괄호 정규식

`re.findall(r"\[([^\[\]]*)\]", "근거는 [travel] [approval] [travel]")`의 결과와, 이것을 `set(...)`으로 감싼 결과는?

<details>
<summary>정답 보기</summary>

`['travel', 'approval', 'travel']` → `{'travel', 'approval'}`. 괄호 안에 걸린 대괄호 속 글자만 꺼내고, set으로 중복 · 순서를 없앤 뒤 정답 set과 `==`로 비교해요.

</details>

### OPS2-Q7. 단답형 — 시험지와 답안지

`input` · `expected_output` · `metadata` 중 모델(task)에게 전달되는 것은? `expected_output`은 누가 쓰나?

<details>
<summary>정답 보기</summary>

모델에게는 **`input`**(질문)만 가요. `expected_output`은 **채점기(evaluate)만** 봐요. `metadata`는 사람이 분류해 볼 때 쓰는 메모예요.

</details>

### OPS2-Q8. 단답형 — `name=name`

`lf.create_prompt(name=name, ...)`에서 왼쪽 `name`과 오른쪽 `name`은 각각 무엇인가?

<details>
<summary>정답 보기</summary>

왼쪽 = Langfuse가 정한 **매개변수 이름(이름표)**, 오른쪽 = 위에서 `new_name(...)`으로 만든 **변수의 값**. 괄호 안 `=`는 이름표, 밖 `=`는 대입.

</details>

### OPS2-Q9. 단답형 — dev / holdout

dev와 holdout을 따로 두는 이유와, holdout을 실행하는 조건은?

<details>
<summary>정답 보기</summary>

dev에 맞춰 프롬프트를 고치다 보면 dev에만 잘 맞게 되어 **확인 점수가 부풀려지기** 때문이에요. holdout은 dev 판정이 **CHECK\_HOLDOUT**(4개 모두 통과, 나빠진 질문 없음)인 후보만 실행하고, 통과해도 **REVIEW**예요.

</details>

### OPS2-Q10. 단답형 — 오류 ≠ 0점

API 실패로 답이 없는 행을 0점으로 채우면 안 되는 이유와, 이 코드에서의 표시 방법은?

<details>
<summary>정답 보기</summary>

0점은 "답을 받았는데 틀렸다"는 평가 결과이고, 실패는 평가할 답이 없는 상태라서 섞으면 프롬프트 탓인지 인프라 탓인지 구분할 수 없어요. rows에 `error = "INCOMPLETE_EVALUATION"`, 03은 `EXPERIMENT_HAS_ERRORS`, 04는 오류 · 점수 누락이 있으면 **BLOCK**. `evaluate()`도 completed가 아니면 `ValueError`.

</details>
