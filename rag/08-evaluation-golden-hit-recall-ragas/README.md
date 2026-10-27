# 8장. 평가 — Golden Dataset · Hit@k·Recall@k · RAGAS · 개선 전후 비교

> 2026-10-27 학습 기록. RAG 5일차 오전 수업입니다. "좋아졌다"고 말하려면 같은 기준으로 재야 한다는 주제로, 정답지(Golden Dataset)를 만들고(8-1), 검색을 문서 ID로 채점하고(8-2), 답변을 주장 단위와 RAGAS로 채점하고(8-3), BM25·Dense·Hybrid를 같은 정답지로 비교했습니다(8-4).

## 학습 목표

- Golden Dataset의 필드(질문·참고 답변·근거 문서 ID·답 가능 여부·dev/test)와 각 필드를 **어디에 쓰는지**(시스템 입력 vs 평가 전용) 구분한다.
- Hit@k와 Recall@k를 직접 계산하고, 평균 아래에 숨은 실패 질문(q10)을 질문별 결과에서 찾는다.
- 검색은 청크로 하지만 채점은 `document_id`로 한다는 것과, 청크를 먼저 자르느냐 문서를 먼저 중복 제거하느냐에 따라 Recall이 달라지는 것을 확인한다.
- RAGAS 네 지표(Faithfulness·Answer Relevancy·Context Precision·Context Recall)가 무엇과 무엇을 비교하는지 설명한다.
- 한 번에 하나만 바꾸고, dev로 고르고, test는 마지막에 한 번만 보는 비교 절차를 지킨다.

## 실습 파일

| 강 | 주제 | 실습 상태 |
| --- | --- | --- |
| 8-1 | 소규모 Golden Dataset — 필드, q06 정답을 원문까지, 답 없는 질문, dev ∩ test = `[]` | ✅ `main.py` · q\_hard 통과 |
| 8-2 | 검색 평가 Hit@k·Recall@k — q06 k=1·3·5, dev 10개 평균, 청크 먼저 vs 문서 먼저 | ✅ `main.py` · q\_hard 통과 |
| 8-3 | 답변 평가 RAGAS — 답변 A·B·C, 주장 단위 수동 라벨, 네 지표 | ✅ `main.py` · q\_hard 통과 · **선택 실습 `run_ragas.py --execute`까지 실행** |
| 8-4 | 오류 분류와 개선 전후 비교 — BM25·Dense·Hybrid, wins/losses, test 확인 | 🧪 `main.py` 실행 · ⏳ q\_hard 미완 |

`rag_day5` 키트로 진행했습니다. 5일차는 `prepare.py` 없이 강마다 `main.py`를 바로 실행합니다. 8-3 선택 실습을 위해 `uv add ragas==0.4.3 openai==2.54.0 langchain-community==0.3.31`로 패키지를 추가했고(README는 `uv run --with …` 방식을 권장), API 키는 `configure_api.py`로 직접 입력해 `.env`에 두었습니다(올리지 않음). 키트 코드는 올리지 않고 직접 바꾸거나 추가한 부분만 기록합니다.

## 전체 흐름

### 한 문장

**4일차까지 RAG를 만들었다면, 오늘 오전은 그걸 채점합니다. 정답지 → 검색 점수 → 답변 점수 → 바꾸기 전후 비교.**

```text
8-1 무엇이 정답인가  →  8-2 근거를 찾았나  →  8-3 답이 근거에 맞나  →  8-4 바꿔서 좋아졌나
   golden.jsonl         Hit@k · Recall@k        수동 라벨 · RAGAS        BM25 → Dense → Hybrid
```

### 오늘 쓴 자료

| 파일 | 내용 |
| --- | --- |
| `documents.json` | 규정 원문 12개 (현행 10 · 구버전 2), `content`·`metadata` |
| `chunks.json` | 80자 · overlap 20 청크 28개 (현행 24), `chunk_id`·`text` |
| `golden.jsonl` | 질문 20개: `question` · `reference` · `relevant_document_ids` · `answerable` · `split` |

## 핵심 이론

### 1. Golden Dataset (8-1강)

"출장비는 얼마까지 받을 수 있나요?"처럼 질문이 모호하면 무엇이 정답인지부터 정해야 해요. 그래서 질문마다 **정답 문서와 참고 답변을 사람이 미리 적어 둔 정답지**를 만들어요.

| 필드 | 쓰는 곳 |
| --- | --- |
| `question` | 시스템에 보내는 입력 (**이것만** 보내요) |
| `reference` · `relevant_document_ids` | 평가에만 사용 — 검색 입력에 붙이면 정답을 넣어 주는 셈 |
| `answerable` · `split` | 답 가능 여부 · dev(개발용) / test(최종 확인) |

```text
STEP1 문서 12 질문 20
split {'dev': 12, 'test': 8}
answerable {True: 16, False: 4}
```

- **q06 정답을 원문까지 따라가기:** 숙박비 1박당 12만원(travel) · 식비 1일 3만원(meal) · 남은 숙박비 한도를 식비에 합산하지 않음(meal). "출장비는 15만원"은 12+3을 더해 **단위(1박·1일)와 합산 금지**를 지워 버린 오답이에요.
- 청크 크기를 바꾸면 `chunk_id`는 바뀌지만 `document_id`는 그대로예요. 그래서 정답지의 근거는 **문서 ID**로 적어요.
- **답이 없는 질문:** q11(매출 목표)은 자료에 정보가 없고, q12(개인 취미 강좌)는 교육비 문서가 지원 여부를 정하지 않아요. "정보 없음"을 "아니다"로 바꾸면 안 되고 "현재 자료에서 확인할 수 없어요"가 정답이에요. 6장 `insufficient`와 같은 이야기예요.
- **dev와 test는 근거 문서가 겹치지 않게** 나눴어요. dev = education·incident·leave·meal·travel·vpn, test = equipment·meeting·remote·retention, 교집합 `[]`. 질문을 추가할 때는 같은 원문의 의역 질문을 한 묶음(`group_id`)으로 같이 나눠요.
- 질문 20개는 작은 평가셋이라 여기서 나온 숫자를 서비스 전체 성공률로 확대하지 않아요.

### 2. Hit@k · Recall@k (8-2강)

```text
Hit@k    = 1(|R ∩ S| > 0)     정답 문서를 하나라도 찾았나
Recall@k = |R ∩ S| / |R|      정답 문서 중 몇 개를 찾았나
R: 필요한 문서 집합 · S: 상위 k개 청크의 문서 ID 집합
```

q06 BM25 순위: `1 meal@60 · 2 travel@0 · 3 meal@0 · 4 meeting@60 · 5 vpn@60`

```python
for k in [1, 3, 5]:
    found = {r["document_id"] for r in ranked[:k]}   # 청크 k개 → 문서 ID 집합
    hit = int(bool(found & expected))
    recall = len(found & expected) / len(expected)
```

| k | 찾은 문서 | Hit@k | Recall@k |
| --- | --- | --- | --- |
| 1 | meal | 1 | 0.5 |
| 3 | meal, travel | 1 | 1.0 |
| 5 | meal, meeting, travel, vpn | 1 | 1.0 |

- k=1은 Hit 1인데 숙박비 근거(travel)가 없어요. **Hit만 보면 이 차이를 놓쳐요.**
- k를 늘려 Recall을 올리면 관련 없는 Context, 길이, 처리 시간도 같이 늘어요.

**답 있는 dev 10개 평균** (dev 12개 − 답 없는 q11·q12)

| k | 분모 | Hit | Recall |
| --- | --- | --- | --- |
| 1 | 10 | 0.9 | 0.85 |
| 3 | 10 | 0.9 | 0.9 |
| 5 | 10 | 0.9 | 0.9 |

- k=3 질문별 Recall은 q01~q09 전부 1.0, **q10만 0.0**이에요. 평균 0.9의 정체는 q10 하나예요.
- q10 "교육비 정산 증빙은 무엇인가요?"가 0인 이유: BM25는 단어가 똑같아야 점수를 주는데, 원문은 `교육비는`·`수료증과`처럼 조사가 붙어 있어 겹치는 토큰이 하나도 없어요(7-1과 같은 한계). 문서가 없는 게 아니라 **검색 실패**예요.
- `STEP3 검색평가 제외 ['q11', 'q12']` — 답 없는 질문은 Recall 분모가 0이라 빼요. 보류를 잘하는지는 따로 평가해야 해요.

**청크 먼저 vs 문서 먼저 중복 제거** (순서: meal@60, meal@0, travel@0)

| 방식 | 코드 | 결과 |
| --- | --- | --- |
| A 청크 2개 먼저 | `{r["document_id"] for r in ordered[:2]}` | `{'meal'}` → Recall 0.5 |
| B 문서 먼저 중복 제거 | `list(dict.fromkeys(ids))[:2]` | `{'meal', 'travel'}` → Recall 1.0 |

이번 수업의 정의는 **A**(청크 k개를 검색한 뒤 `document_id`로 비교)예요. 같은 "Recall@2"라도 정의가 다르면 숫자가 달라지니 결과 표에 평가 단위를 같이 적어요.

### 3. RAGAS (8-3강)

q05 "출장 숙박 비용 한도와 필요한 증빙은?"에 대한 연습 답변 세 개(모델 출력이 아니라 평가 연습용으로 작성한 것):

| 답변 | 내용 | 특징 |
| --- | --- | --- |
| A | 숙박비는 1박당 12만원까지이며 숙박 영수증을 첨부해야 해요 | 정답 |
| B | 숙박비는 1박당 **30만원**까지이며 숙박 영수증을 첨부해야 해요 | 금액 오류 |
| C | 국내 출장 **식비**는 1일 3만원까지 영수증으로 정산해요 | 주제가 다름 |

- 평가에는 **실제로 모델에 전달한 Context**를 써요. `main.py`가 BM25 k=3 → `build_context`로 만든 Context(travel@0, meal@0)와 답변 A~C를 `answer_review_08.json`에 저장하고, 선택 실습 RAGAS도 이 파일을 그대로 읽어요 → 수동 검토와 자동 평가가 같은 입력을 봐요.
- **주장 단위 수동 라벨:** `{"A": [True, True], "B": [False, True], "C": [True]}` → 근거 일치 비율 A 1.0 · B 0.5 · C 1.0
- C는 근거에는 맞지만(1.0) 질문에는 답하지 않았어요. **근거에 맞다(Faithfulness)와 질문에 답한다(Relevancy)는 다른 축**이에요.

| 지표 | 비교하는 것 | 입력 | 이 실습에서 볼 점 |
| --- | --- | --- | --- |
| Faithfulness | 답변 주장 ↔ Context | 답변 · Context | B의 30만원을 근거가 뒷받침하나 |
| Answer Relevancy | 답변 ↔ 사용자 질문 | 질문 · 답변 · 임베딩 | C가 숙박 질문에 맞는 답인가 |
| Context Precision | 검색 순서 ↔ 유용한 Context | Context · 참고 답변 | 숙박 근거가 앞에 있나 |
| Context Recall | 참고 답변 사실 ↔ Context | Context · 참고 답변 | 필요한 사실이 Context에 있나 |

**선택 실습: 로컬 E5 + 평가 LLM으로 실제 RAGAS** — 직접 실행했어요.

```text
준비 모드 (API 호출 없음)   "local_embedding_check": {"shape": [2, 384], "unit_norm": true}
                            "generation_requests": 0, "completed": false
실행 모드 --execute         "generation_requests": 18 (상한 20), "completed": true
```

| 답변 | Faithfulness | Answer Relevancy (내 실행) | Answer Relevancy (교안 기록) |
| --- | --- | --- | --- |
| A | 1.0 | 0.8863 | 0.8705 |
| B | 0.5 | 0.8910 | 0.8705 |
| C | 1.0 | 0.8646 | 0.8570 |

Context Recall 1.0 · Context Precision ≈ 1.0 (`0.9999999999`)

- Faithfulness는 수동 라벨과 같아요(A 1.0 · B 0.5 · C 1.0).
- Answer Relevancy는 **교안 기록과 내 실행이 조금 달라요.** 채점자도 LLM이라 실행마다 흔들려요. 그리고 금액이 틀린 B가 A보다 오히려 높게 나왔어요. Relevancy는 "질문 주제에 맞나"만 보고 금액이 맞는지는 보지 않기 때문이에요.
- 결론: C는 Faithfulness 1.0인데 질문에 답하지 않았고, B는 Relevancy가 높은데 금액이 틀렸어요 → **정확성 판정을 지표 하나에 맡기면 안 되고**, 네 점수를 평균 내기 전에 낮아진 지표의 입력과 실제 답변을 같이 읽어요.

### 4. 오류 분류와 개선 전후 비교 (8-4강)

**고정(통제 조건):** 질문 dev 12 · test 8, 80/20 청크 · 현행 필터, 정답 `golden.jsonl` · k=3
**바꾼 것 하나:** 검색 방법 BM25 → Dense → Hybrid

```python
for method in ["bm25", "dense", "hybrid"]:
    search = lambda q, cat=None, m=method: retrieve(q, chunks, m, dense, k=3, category=cat)
    reports[method] = evaluate(dev, search)        # m=method: 이번 반복의 방법을 고정
```

- `evaluate(golden, search)`는 검색 함수를 **인수로** 받아요. 그래서 같은 정답지·같은 채점 함수에 검색기만 갈아 끼울 수 있어요.
- `m=method`는 lambda가 만들어질 때의 `method` 값을 기본값으로 붙잡아 두는 장치예요.

```text
STEP1 dev bm25   10 0.9 0.9
STEP1 dev dense  10 1.0 1.0
STEP1 dev hybrid 10 1.0 1.0
STEP2 dev wins ['q10'] losses []
q10 [] -> ['education', 'meal', 'travel']
STEP2 test wins [] losses []        (test는 세 방법 모두 Hit@3·Recall@3 1.0)
```

- **wins/losses:** BM25 → Hybrid로 바꿨을 때 Recall이 좋아진 질문과 나빠진 질문. 평균 상승 0.1 = q10 한 질문이에요.
- 이 숫자는 생성 답변의 정확도나 RAGAS 점수가 아니에요. 그리고 **문서 Recall 1.0이어도 답(수료증과 영수증)이 든 청크까지 들어왔는지는 본문을 읽어서** 따로 확인해야 해요.
- test 결과는 "dev의 개선이 test에서도 확인됐다"나 "검색 성공률 100%"가 아니라 **"test 6개 질문의 근거 문서는 Top-3에 있었다"**까지만 말할 수 있어요.

**다음에 바꿔 볼 후보 (한 번에 하나씩)**

| 관찰 | 다음에 시험할 변경 | 함께 볼 결과 |
| --- | --- | --- |
| BM25 q10 후보 없음 | 질의 재작성 · 토큰 처리 | education@60 회수와 무관한 후보 |
| 올바른 문서의 앞 청크만 검색 | Parent 확장 · 인접 청크 추가 | 증빙 포함 여부와 Context 길이 |
| 후보는 있지만 순위가 낮음 | 재정렬 | 정답 청크 순위와 추가 처리 시간 |

세 변경을 한꺼번에 넣으면 어떤 변경이 효과를 냈는지 알 수 없어요. 그래서 하나씩 바꾸고 같은 dev로 다시 재요. 이 표의 앞 두 줄이 그대로 오후 9-2(재검색)·9-1(Parent 확장)로 이어져요.

## 내가 직접 적은 메모

- `@`는 at이라고 읽는다. `Hit@3` = 3개 안에서 맞췄나. (행렬곱 연산자 `vectors @ query`의 `@`와 같은 기호)
- 원래 실무에서는 `chunk_id`를 기준으로 평가하지만, 외부 데이터나 벤치마크 같은 경우에는 `document_id`를 기준으로 하기도 한다. 사용자 입장에서도 마찬가지로 `document_id` 기준.
- 8-4: `for model in ["gemini", "openai"]`처럼 한 번에 여러 개를 돌릴 수도 있지만, 한 번에 하나만 보는 게 꼬이지 않는다.
- 8-4: 실제로 할 때는 dev·test를 한 번에 보기보다 dev를 먼저 보고 문제가 없으면 test를 보는 파이프라인을 짜는 게 좋다.

### RAGAS 정리 (수업 중 메모)

- **RAGAS란:** RAG 답변·검색 품질을 LLM이 채점하는 평가 라이브러리(Retrieval-Augmented Generation Assessment). 사람이 정답을 다 매기지 않아도 지표 점수(0~1)로 비교할 수 있다. 채점 자체도 LLM이라 비용이 들고 점수가 흔들릴 수 있다(작은 표본은 참고용).
- **입력:** `user_input`(질문), `response`(RAG 답변), `retrieved_contexts`(검색된 근거 청크 본문 목록), `reference`(참고 정답, Recall·Precision용). 그리고 채점용 LLM(평가 모델, API 키), Answer Relevancy용 임베딩(여기서는 로컬 E5).
  - Faithfulness = 질문 + 답변 + 근거
  - Answer Relevancy = 질문 + 답변 + 임베딩
  - Context Recall · Context Precision = 질문 + 참고 정답 + 근거
- **8-2 Recall과의 차이:** 8-2는 문서 ID 교집합으로 계산하고, RAGAS Context Recall은 LLM이 "참고 답변의 사실이 근거에 있나"를 판단한다.
- **팀 프로젝트에서 쓰는 법**
  1. golden 세트(질문 + 정답 문서 + 참고 답변, dev/test 분리)를 팀이 먼저 만든다.
  2. 청킹 크기·k·BM25/Dense/Hybrid·Re-ranking·프롬프트를 바꿀 때마다 같은 세트로 RAGAS를 돌려 "감"이 아니라 숫자로 비교한다(실험표).
  3. 점수가 낮은 지표로 원인 위치를 찾는다. Recall·Precision이 낮으면 검색 문제, Faithfulness가 낮으면 생성·프롬프트 문제.
  4. 발표·보고서에 개선 전후 점수로 근거를 댄다.
  5. 비용 관리: 요청 수 제한(`--max-requests`), 작은 dev 세트로 자주·test는 마지막에, 키는 `.env`(깃 제외), 결과 파일의 `completed` 확인.

## 질문과 새로 알게 된 점

### 8-1 q\_hard: q09 정답 근거를 원문에서 읽기

```python
target = next(g for g in golden if g["question_id"] == target_id)
for did in target["relevant_document_ids"]:
    source = by_id[did]
    print(source["metadata"]["title"])
    print(source["content"])
# 교육비 지원 … 직무 교육비는 분기 1회, 1인당 30만원까지 지원합니다. …
```

- golden의 정답 문서 ID(`relevant_document_ids`)로 `by_id`(`{document_id: 문서}` 딕셔너리)에서 원문을 꺼내 제목과 본문을 확인해요.
- `next(…)`는 조건에 맞는 것 중 **첫 번째 하나만** 꺼내요(`[…][0]`과 같은 결과).
- 원문 정보는 문서의 `metadata.title`과 `content`에 있어요.
- 금액(30만원)만 맞고 횟수가 "월 1회"로 바뀌면 오답이라 금액과 횟수를 함께 적어요.

### 8-2 q\_hard: 청크 Top-2로 Recall

```python
found = {r["document_id"] for r in ordered[:2]}   # {'meal'}
recall = len(found & expected) / len(expected)    # 0.5
```

### 8-3 q\_hard: 단위가 바뀐 답변 D

```python
answers["D"] = "숙박비는 1일당 12만원까지이며 숙박 영수증을 첨부해야 합니다."
d_labels = [False, True]                 # 금액·단위 ✗ (원문은 1박당) / 증빙 ✓
print(sum(d_labels) / len(d_labels))     # 0.5
```

- `sum([False, True])` = 1 — True는 1, False는 0으로 더해져요.
- B(30만원)와 똑같이 0.5지만 **틀린 이유가 달라요**(B는 금액, D는 단위). 점수만 보면 구분이 안 되니 이유를 같이 적어요.

### "k=3인데 왜 문서가 3개가 아니지?"

청크 3개를 가져와도 같은 문서에서 나온 청크가 있으면 **문서 ID 집합**으로 줄어들어요. q06 k=3은 청크 3개(meal@60, travel@0, meal@0)지만 문서는 `{meal, travel}` 2개예요.

### 질문이 왜 10개?

golden 20개 중 dev 12개를 쓰고, 그중 답할 수 없는 q11·q12 2개를 빼서 10개예요. row 하나는 `(qid, hit, recall)` 튜플이에요.

### 청크 결과를 `r["document_id"]`로 바꾸는 이유

검색은 청크 단위지만 채점은 문서 단위라서, 각 청크에 들어 있는 문서 ID를 **읽어 오는** 거예요. 값을 바꾸는 게 아니라 읽기만 해요.

### `chunks.json` vs `documents.json`

| | `chunks.json` | `documents.json` |
| --- | --- | --- |
| 개수 | 자른 조각 28개 | 원문 12개 |
| 주요 필드 | `chunk_id`, `document_id`, `text`, `start`/`end` | `document_id`, `content`, `metadata` |
| 쓰는 곳 | 검색 | 정답 확인, (9-1) Parent 확장 |

### 기타

- `round(x, 4)`: 소수 넷째 자리까지 반올림.
- `expected = set(g["relevant_document_ids"])`: 리스트를 집합으로 바꿔 중복을 없애고 교집합(`&`)을 쓸 수 있게 해요.

### RAGAS 설치와 `run_ragas.py` 구조

- `No module named 'ragas'` → 패키지를 먼저 추가해야 해요. 나는 `uv add ragas==0.4.3 openai==2.54.0 langchain-community==0.3.31`로 넣었어요(키트 README는 기본 환경을 건드리지 않는 `uv run --with …`를 권장).
- `main()`은 4블록이에요.
  1. 로컬 E5 검사 — shape `[2, 384]`, 길이(norm) 1
  2. 평가 LLM과 지표 4개 객체 만들기 — `Faithfulness(llm=llm)`, `AnswerRelevancy(llm=llm, embeddings=embeddings, strictness=3)` …
  3. 준비 모드면 여기서 끝 (`completed: false`, 무료)
  4. `--execute`면 점수를 계산해서 report에 저장 (유료 API). `--show-recorded`는 예전 기록 조회
- `async`/`await`: API 응답을 기다리는 동안 프로그램 전체가 멈추지 않게 해요.

### 8-4에 Re-ranking이나 Query Rewrite를 넣으려면? (궁금해서 물어본 것)

- `evaluate`가 검색 함수를 받는 구조라 **`main.py`만** 바꾸면 돼요. `search(q, cat)` 모양의 함수를 하나 더 만들어 비교 목록에 넣으면 끝이에요.
  - Re-ranking: Hybrid로 후보를 넉넉히(k=8) 받고 → Cross-Encoder로 (질문, 본문) 쌍 점수 → 상위 3개 반환
  - Rewrite: 질문별 검색 표현을 준비하고 → 원질문 + 표현들을 각각 Hybrid 검색 → RRF로 합치기
- wins/losses 비교 대상도 `"hybrid"` → 새 방법으로 바꿔야 해요.
- 주의: 검색 표현이나 후보 수는 **dev로만** 고르고, test는 마지막에 한 번.
- 실제로 파일은 바꾸지 않았어요(궁금해서 물어본 것).

### 7장 다시 짚은 것

| 방법 | 한 줄 |
| --- | --- |
| BM25 | 단어가 겹치는 정도로 찾음. 문서 길이를 평균과 비교해 보정. 조사 하나로 결과가 바뀜 |
| Dense | 의미로 찾음. 관련이 없어도 항상 Top-k를 돌려줌 |
| RRF | 두 검색의 **순위**로 점수(Σ 1/(60+rank)) → 점수 단위가 달라도 합칠 수 있음 |
| Cross-Encoder | (질문, 청크)를 한 쌍으로 넣고 다시 채점. 정확하지만 느려서 후보에만 씀. 후보에 없는 청크는 못 살림 |

### RAG 전체 흐름 (1~8장 복습)

```text
준비: 문서 읽기(2) → 자르기(3) → 벡터로(4) → 저장(5)
질문: 검색(3·4·7) → 근거 묶기(6-1) → 답 + 검사(6-2) → 출처(6-3) / 보류(6-4) → 평가(8)
```

- **1장:** Long Context = 문서를 전부 프롬프트에 / CAG = 전부 넣은 것을 캐시해 재사용 / RAG = 필요한 조각만 검색해서
- **3장 청킹:** Fixed(글자 수) · Recursive(문단 → 줄 → 문장 경계) · Token(토큰 수) · 마크다운 헤더(`#` 제목 단위)
- **4장 mean pooling:** 토큰 벡터들의 평균으로 문장 벡터 1개(384차원). 패딩 토큰은 뺌
- **5장 Qdrant:** Collection(테이블 같은 것) · Point(`id` + `vector` + `payload`) · `upsert`(같은 id면 덮어쓰기) · `query_points`(Top-k) · Filter(payload 조건)

**핵심 교훈**

1. 앞 단계에서 빠진 건 뒤에서 못 살린다.
2. 모델 결과는 검사한다.
3. 검색은 청크로, 출처와 채점은 문서로 본다.
4. 바꿨으면 숫자로 비교한다(dev로 고치고, test는 마지막에).

## 실습 코드에서 직접 바꾼 점

원본 키트(`rag_day5` ZIP)와 비교한 내용입니다.

| 파일 | 바꾼 점 / 추가한 주석 |
| --- | --- |
| 8-1·8-2 `main.py` | `from printsection import print_section` + 구역마다 `print_section("1번")` … 출력 추가 |
| 8-1 `q_hard.py` | 위 q09 코드 (`next(…)` → `by_id[did]` → 제목·본문 출력) |
| 8-2 `main.py` | `bm25(item["question"], current, k=5)` 옆 `#질문들어오고 현행문서, k는 5개.` / `bm25(...)[:k]` 옆 `# 검색기: bm25` / `expected = set(...)` 옆 `#중복을 없앤형태.` |
| 8-2 `q_hard.py` | `found = {r["document_id"] for r in ordered[:2]}` → `recall = len(found & expected) / len(expected)` → `print(recall)` |
| 8-3 `q_hard.py` | `d_labels = [False, True]` → `print(sum(d_labels) / len(d_labels))` |
| 8-3 `run_ragas.py` | `from ragas.llms import llm_factory` 옆 `#레거시 지표 라이브러리들 >> 밑까지` / 지표 생성 위 `# 4가지 지표` / `AnswerRelevancy(...)` 옆 `# 질문과 답변의 유사도를 보기위해 임배딩.` |
| 8-4 `main.py` | `for method in …` 아래 `# for model in ["gemini", "openai"] 식으로 한번에 할 수도 있음. 하지만 한번에 한개만 보는게 꼬이지않을수 있음.` / `wins` 옆 `# hybrid로 바꿧을때 이긴.좋아진 질문(많을수록 좋음)` / `losses` 옆 `# hybrid로 개선했는데 안좋아지는것.(진것. 적을수록 좋음)` / 파일 끝 `# 실제로 할때는 dev, test 한번에 하기보단 dev먼저 보고 문제가 없다면 test를 보는 파이프라인짜는것이 좋다.` |
| `pyproject.toml` | `uv add`로 `ragas==0.4.3`, `openai==2.54.0`, `langchain-community==0.3.31`, `graphrag==3.2.0` 추가 |
| 실행 결과 파일 | `answer_review_08.json`, `ragas_local_preparation.json`, `ragas_local_result.json`, `comparison_08.json` 생성 (`.env`는 올리지 않음) |

q\_easy 파일은 q\_hard를 풀면서 같은 답을 넣은 8-1·8-2 외에는 채우지 않았습니다.

## 마무리 과제 (PPT)

- [ ] `ch08/rag_ch08_04`에서 Hybrid q10의 Top-3 청크 본문을 읽고 수료증과 영수증이 있는지 표시하기
- [ ] 8-4 q\_hard: 저장된 `comparison_08.json`에서 dev / hybrid의 q10 행 찾기 (`['education', 'meal', 'travel']` · Recall 1.0)
- [x] `ch08/rag_ch08_03`에서 `run_ragas.py` 준비 모드 — 로컬 E5 shape `[2, 384]` 확인 (실행 모드까지 함)

## 확인 문제

강의 내용을 바탕으로 직접 만든 복습 문제입니다. 객관식 4문제, 서술형 2문제이고 각 문제 바로 아래에 정답이 있습니다.

### 8-Q1. Golden Dataset의 필드 (8-1)

RAG 시스템에 실제로 보내는 입력은 무엇일까?

① `question` + `reference`  
② `question` + `relevant_document_ids`  
③ `question` + `answerable`  
④ `question`만

<details>
<summary>정답 보기</summary>

**④** — `reference`·`relevant_document_ids`는 평가에만 써요. 검색 입력에 붙이면 정답을 미리 넣어 주는 셈이 돼서 점수가 의미 없어져요. `answerable`·`split`도 평가용 표시예요.

</details>

### 8-Q2. q06 k=1의 Hit와 Recall (8-2)

q06은 정답 문서가 `{meal, travel}`이고 BM25 1위는 meal@60이다. k=1의 Hit@1과 Recall@1은?

① Hit 1 · Recall 0.5  
② Hit 1 · Recall 1.0  
③ Hit 0 · Recall 0.5  
④ Hit 0 · Recall 0.0

<details>
<summary>정답 보기</summary>

**①** — 정답 문서를 하나(meal) 찾았으니 Hit 1, 두 개 중 하나라 Recall 0.5예요. Hit만 보면 숙박비 근거(travel)가 빠진 걸 놓쳐요.

</details>

### 8-Q3. 답변 C의 점수 (8-3)

q05(숙박 한도와 증빙)에 C "국내 출장 식비는 1일 3만원까지 영수증으로 정산해요"라고 답했다. 맞는 설명은?

① Faithfulness가 0이라 바로 걸러진다  
② Context Recall이 0이 된다  
③ 근거와 일치하니 좋은 답변이다  
④ Faithfulness는 1.0이지만 질문에 답하지 않았으므로 Answer Relevancy와 실제 답을 같이 봐야 한다

<details>
<summary>정답 보기</summary>

**④** — C의 문장은 Context(meal@0)에 있어서 근거 일치는 1.0이에요. 하지만 숙박 질문에 식비로 답했어요. Faithfulness와 Relevancy는 다른 축이라 하나만 보면 안 돼요. Context Recall은 답변이 아니라 검색된 근거를 보는 지표라 C와 상관없이 1.0이에요.

</details>

### 8-Q4. 개선 전후 비교 절차 (8-4)

BM25 → Hybrid로 바꿨더니 dev 평균이 0.9 → 1.0이 됐다. 가장 알맞은 다음 행동은?

① 바로 test를 여러 번 돌려 가장 좋은 설정을 고른다  
② wins/losses로 바뀐 질문(q10)을 찾고 본문까지 읽은 뒤, 고른 설정을 test에서 한 번 기록한다  
③ Re-ranking과 Rewrite를 한꺼번에 추가해 점수를 더 올린다  
④ 평균이 올랐으니 "검색 성공률 100%"라고 보고한다

<details>
<summary>정답 보기</summary>

**②** — 평균 상승 0.1은 q10 한 질문이에요. 문서 Recall 1.0이어도 증빙 청크가 들어왔는지는 본문으로 확인해요. test로 설정을 고르면 test에 맞춘 점수가 되고(①), 한꺼번에 바꾸면 무엇이 효과를 냈는지 모르고(③), 작은 test 결과를 전체 성공률로 확대하면 안 돼요(④).

</details>

### 8-Q5. 서술형 — 청크 먼저 vs 문서 먼저 (8-2)

순서가 meal@60, meal@0, travel@0일 때 "Recall@2"가 0.5와 1.0 두 가지로 나올 수 있다. 왜 그런지, 결과를 보고할 때 무엇을 같이 적어야 하는지 쓰세요.

<details>
<summary>예시 답안</summary>

청크 2개를 먼저 자르면 meal@60·meal@0이라 문서는 `{meal}`뿐이어서 0.5예요. 문서 ID로 먼저 중복을 없애고 2개를 고르면 `{meal, travel}`이라 1.0이에요. k를 청크 개수로 세느냐 문서 개수로 세느냐에 따라 같은 이름의 지표가 다른 값이 돼요. 그래서 결과 표에 **평가 단위(청크 k개 후 document\_id 비교)**를 같이 적어야 다른 실험과 비교할 수 있어요. 이번 수업은 청크 먼저(0.5)가 정의예요.

</details>

### 8-Q6. 서술형 — RAGAS 점수가 교안과 다르게 나온 이유 (8-3)

직접 `--execute`로 돌렸더니 Answer Relevancy가 A 0.8863 · B 0.8910으로 교안 기록(둘 다 0.8705)과 달랐고, 금액이 틀린 B가 A보다 높았다. 이유와 이 점수를 어떻게 써야 하는지 쓰세요.

<details>
<summary>예시 답안</summary>

RAGAS는 채점도 LLM이 해서(답변에서 질문을 다시 만들어 임베딩 유사도를 봄) 실행마다 점수가 조금씩 흔들려요. 또 Answer Relevancy는 "질문 주제에 맞는 답인가"를 보는 지표라 금액이 맞는지는 판단하지 않아요. 그래서 B가 A보다 높을 수도 있어요. 금액 오류는 Faithfulness(B 0.5)에서 잡혀요. 따라서 점수 하나로 좋고 나쁨을 정하지 말고, 작은 표본의 소수점 차이는 참고로만 보고, 네 지표를 따로 읽은 뒤 실제 답변과 근거를 같이 확인해요. 비교할 때는 같은 평가 모델·같은 설정으로 돌린 결과끼리만 비교해요.

</details>
