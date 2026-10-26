# 7장. BM25 · Hybrid(RRF) · Re-ranking · Query Rewrite — 보류만 하지 말고 검색 자체를 개선하기

> 2026-10-26 학습 기록. RAG 4일차 오후 수업입니다. 같은 질문을 토큰 일치(BM25)와 의미(Dense)로 검색해 결과가 갈리는 지점을 보고(7-1), 두 순위를 RRF로 합치고(7-2), Cross-Encoder로 (질문, 청크) 쌍을 다시 점수 매기고(7-3), 질문 표현을 늘려 여러 번 검색해 합치는(7-4) 방법을 실습했습니다.

## 학습 목표

- BM25가 토큰 일치로 점수를 매기는 방식(IDF, 빈도 포화, 길이 보정)을 설명하고, 조사 하나로 결과가 달라지는 한계를 확인한다.
- "문서를 찾았다 ≠ 답이 든 청크를 찾았다"를 Dense 검색 결과로 구분한다.
- 척도가 다른 BM25·Dense 점수를 더하지 않고 순위로 합치는 RRF `1 / (60 + rank)`를 직접 계산한다.
- Bi-Encoder(따로 읽기)와 Cross-Encoder(함께 읽기)의 차이를 설명하고, 재정렬은 **받은 후보 안에서 순서만** 바꾼다는 한계를 확인한다.
- Query Rewrite / Multi-Query / 질문 분해를 구분하고, 검색 전(질문)과 검색 후(청크) 중복 제거를 따로 처리한다.

## 실습 파일

| 강 | 주제 | 실습 상태 |
| --- | --- | --- |
| 7-1 | BM25와 Dense 검색 비교 — 토큰화, IDF, 문서 찾기 vs 답이 든 청크 찾기, `search_runs_07.json` | ✅ `main.py` · q\_hard 통과 |
| 7-2 | Hybrid Search와 RRF — 점수 대신 순위, `1 / (60 + rank)`, 문서 다양성 | ✅ `main.py` · q\_hard 통과 |
| 7-3 | Cross-Encoder Re-ranking — 질문-청크 쌍 점수, logit, 후보의 한계 | ✅ `main.py` · q\_hard 통과 |
| 7-4 | Query Rewrite와 Multi-Query — 의도는 유지·표현만 추가, `chunk_id`로 합치기 | 🧪 `main.py` 실행 · ⏳ q\_hard 미완 |

`rag_day4` 키트로 진행했습니다. 7-1·7-4는 `main.py`를 바로, 7-2·7-3은 `uv run prepare.py`(→ `search_runs_07.json`) 다음에 `main.py`를 실행했습니다. 7-3은 Cross-Encoder `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1`을 수업 전에 받아 두어 `--skip-model` 없이 돌렸습니다(HF 캐시 470MB, 오프라인 로드 OK, 테스트 쌍 점수 `6.76`). 키트 코드는 올리지 않고 직접 바꾸거나 추가한 부분만 기록합니다.

## 전체 흐름

### 한 문장

**오전(6장)이 "찾은 근거로 제대로 답하기"였다면, 오후(7장)는 "근거를 더 잘 찾기"입니다. 찾고(BM25·Dense) → 합치고(RRF) → 다시 매기고(Re-ranking) → 질문을 바꿔 다시 찾기(Rewrite).**

```text
질문 → [7장: 검색을 더 잘하기] → 검색 결과 → [6장: 근거로 답하기] → 답 + 출처 (또는 보류)
```

### 그림으로 보기

```text
질문
 ├─ BM25 (토큰 일치)  → 순위 1..6 ┐
 └─ Dense (E5 의미)   → 순위 1..6 ┘ 7-1
        │ 7-2  RRF: Σ 1/(60 + rank)  → 합집합 9 → 최종 3   (점수 대신 순위)
        ▼
   후보 8개 → (질문, 본문) 쌍 8개 → Cross-Encoder logit → 새 순서            7-3
        │      ※ 후보에 없는 청크는 되살릴 수 없음
        ▼
   질문이 BM25에서 [] → 같은 뜻의 검색 표현 2개 추가 → 각각 검색 → chunk_id 합집합   7-4
        │      ※ 최종 답변·재정렬에는 사용자의 원질문을 씀
        ▼
   6장 Context → 답
```

### 오후 내내 쓴 질문

| ID | 질문 | 특징 |
| --- | --- | --- |
| q05 | 출장 숙박 비용 한도와 필요한 증빙은? | travel 0 하나로 답 |
| q06 | 출장 식비와 숙박비의 한도는 각각 얼마이고 두 한도를 합쳐 쓸 수 있나요? | meal 0 · travel 0 · meal 60 세 청크 필요 |
| q10 | 교육비 정산 증빙은 무엇인가요? | 답(수료증·영수증)은 education 60, BM25는 `[]` |
| q11 | 회사의 올해 매출 목표는 얼마인가요? | 자료에 답 없음 |

표에서는 긴 `chunk_id` 대신 `문서 ID@시작 위치`(예: `education@60`)로 줄여 씁니다.

## 핵심 이론

### 1. BM25 vs Dense (7-1강)

**"교육비 정산 증빙은?" — 원문엔 답이 있는데 BM25는 `[]`**

```text
질문 토큰:  교육비 | 정산 | 증빙은 | 무엇인가요
원문 토큰:  수강 | 완료 | 후 | 수료증과 | 영수증을 | 제출합니다      ← 겹치는 토큰 0개
BM25 → []          Dense → education 청크를 찾음
```

자료가 없어서가 아니라 **있는 내용을 토큰 일치로 못 찾은** 경우예요. "검색 결과 없음"을 보면 먼저 이 둘을 구분해요.

**조사 하나로 다른 토큰이 돼요**

```python
def tokenize(text):
    return re.findall(r"[가-힣a-zA-Z0-9]+", text.lower())   # 공백·기호로만 자름 (형태소 분석 아님)

print(tokenize("영수증 영수증을 영수증으로"))   # ['영수증', '영수증을', '영수증으로']
# 영수증     []
# 영수증을   [('education', 60), ('travel', 0)]
# 영수증으로 [('meal', 0)]
```

"영수증 검색이 비었다" ≠ "영수증 규정이 없다" — 토큰화가 만든 실패예요.

**IDF: 드문 토큰일수록 큰 가중치**

```text
IDF(t) = log(1 + (N − df + 0.5) / (df + 0.5))
N = 24 (현행 청크),  df(숙박) = 1  →  IDF = log(1 + 23.5 / 1.5) = 2.8134
```

- `df`는 토큰이 **등장한 청크 수**(한 청크 안에서 두 번 나와도 1번).
- "숙박비"·"숙박은"은 "숙박"과 **다른 토큰**이라 세지 않아요.

**BM25 한 항: 빈도는 오르되 점점 덜, 긴 청크는 깎아서**

```text
score(q, d) = Σ IDF(t) · f(t,d)·(k1+1) / ( f(t,d) + k1·(1 − b + b·|d|/avgdl) )
k1 = 1.5 (빈도 포화)   b = 0.75 (길이 보정)   |d|/avgdl = 이 청크 길이 / 평균 길이
```

```python
score += idf * tf * 2.5 / (tf + 1.5 * (.25 + .75 * dl / avgdl))   # 키트 코드: k1+1 = 2.5, 1-b = .25
```

**네 질문, 두 검색기**

| 질문 | BM25 상위 | Dense 상위 3 (점수) |
| --- | --- | --- |
| q05 숙박 한도·증빙 | travel@0 8.3718, meal@0 | travel@0 0.8945, meal@0 0.875, meal@60 0.8444 |
| q06 식비·숙박·합산 | meal@60 8.3049, travel@0, meal@0 | meal@60 0.9134, meal@0 0.8858, travel@0 0.8768 |
| q10 교육비 증빙 | `[]` | education@0 0.8398, meal@0 0.818, travel@60 0.815 |
| q11 올해 매출 목표 | `[]` | leave@0 0.7986, leave@60 0.7982, education@0 0.7842 |

- q11처럼 **자료에 없는 질문에도 Dense는 항상 Top-k를 돌려줘요**. BM25는 겹치는 토큰이 없으면 0점이라 빈 목록.
- q10: Dense 1위 education@0(한도·신청 조건)과 정답 서류 education@60(4위 0.8144)은 **같은 문서의 다른 청크**예요. 문서를 찾았다 ≠ 답이 든 청크를 찾았다.
- 결과는 `search_runs_07.json`(질문 12개 × BM25·Dense 상위 6개)으로 저장해 7-2·7-3에서 다시 써요.

### 2. Hybrid Search와 RRF (7-2강)

**점수를 그대로 더하면 안 되는 이유**: BM25 meal@60은 `8.3049`, Dense meal@60은 `0.9134`. 척도가 달라서 더하면 BM25가 거의 전부가 돼요. 그래서 **점수 대신 순위**를 써요.

```text
RRF(d) = Σ_s 1 / (c + rank_s(d))     s = 검색기, rank는 1부터, c = 60
순위:        1         2         3         4         5         6
1/(60+순위): 0.016393  0.016129  0.015873  0.015625  0.015385  0.015152
```

**q06 직접 계산 — 양쪽 1위, 2·3위 교차는 동점**

| 청크 | 어디서 몇 위 | 계산 | RRF |
| --- | --- | --- | --- |
| meal@60 | BM25 1위 + Dense 1위 | 1/61 + 1/61 | 0.032787 |
| meal@0 | BM25 3위 + Dense 2위 | 1/63 + 1/62 | 0.032002 |
| travel@0 | BM25 2위 + Dense 3위 | 1/62 + 1/63 | 0.032002 |
| meeting@60 | BM25 4위만 | 1/64 | 0.015625 |
| travel@120 | Dense 4위만 | 1/64 | 0.015625 |

```python
def reciprocal_rank_fusion(rankings, k=5, rank_constant=60):
    scores, rows = defaultdict(float), {}
    for ranking in rankings:
        seen = set()
        for rank, row in enumerate(ranking, 1):
            cid = row["chunk_id"]
            if cid in seen:            # 한 목록 안에서는 한 번만 투표
                continue
            seen.add(cid)
            scores[cid] += 1 / (rank_constant + rank)
            rows[cid] = row
    order = sorted(scores, key=lambda cid: (-scores[cid], cid))[:k]   # 점수 내림차순, 동점은 chunk_id
    return [{**rows[cid], "score": scores[cid]} for cid in order]
```

- **`chunk_id`로 합쳐요.** `document_id`로 합치면 금액 청크(meal@0)와 합산 금지 청크(meal@60)가 하나로 뭉개져요.
- 여러 검색기에서 상위에 나온 후보가 올라가요. 단, 두 검색기가 **같은 무관한 청크**를 높게 주면 그것도 올라가요.

**후보 수와 최종 개수는 다른 설정**

| 설정 | 영향 |
| --- | --- |
| 후보 수 (검색기별 6 + 6 → 합집합 9) | 정답을 찾을 기회 |
| 최종 개수 (3) | 모델에 줄 정보량 |
| c = 60 | 순위별 점수 차이 |

후보를 일찍 잘라 버리면 RRF가 필요한 청크를 되살릴 수 없어요. RRF는 **들어온 후보를 합치고 순서만** 정해요.

### 3. Cross-Encoder Re-ranking (7-3강)

| | Bi-Encoder (Dense 검색) | Cross-Encoder (재정렬) |
| --- | --- | --- |
| 읽는 방식 | 질문·청크를 **따로** 벡터로 → 코사인 | `[질문] + [청크]`를 **한 입력**으로 함께 읽음 |
| 미리 계산 | 문서 벡터 저장 가능 | 불가 (질문마다 쌍을 다시 계산) |
| 쓰는 범위 | 전체 청크 검색 | 검색된 **후보 몇 개** |

```python
candidates = reciprocal_rank_fusion([run["bm25"], run["dense"]], k=8)   # RRF 후보 8개
pairs = [(run["question"], c["text"]) for c in candidates]               # (질문, 본문) 쌍 8개

model = CrossEncoder("cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
                     device="cpu", max_length=256,
                     activation_fn=torch.nn.Identity())     # logit(원시 점수) 그대로
values = model.predict(pairs, batch_size=4)                 # 4쌍씩 묶어 계산 (전체 쌍 수는 그대로 8)
```

| 설정 | 뜻 |
| --- | --- |
| `max_length=256` | 질문 + 본문 + 특수 토큰 한도 |
| `activation_fn=Identity()` | 시그모이드 등을 거치지 않은 logit 그대로 (그래서 `6.76`, `-0.346` 같은 값) |
| `batch_size=4` | 한 번에 처리할 쌍 수 |

**재정렬 결과 — Top-3 구성은 같고 순서만 바뀜**

```python
order = sorted(range(len(values)), key=lambda i: (-float(values[i]), candidates[i]["chunk_id"]))
# 1 travel 0  이전 3  logit -0.346
# 2 meal 60   이전 1  logit -0.6454
# 3 meal 0    이전 2  logit -0.8013
# 4 travel 120 이전 5 … 8 vpn 60 이전 7 logit -8.3309
```

- 기준은 "순위가 바뀌었나"가 아니라 **필요한 세 사실이 Top-3에 남았나**예요.
- 후보가 2 → 4 → 8개면 점수화할 쌍도 2 → 4 → 8개, 추론 시간도 그만큼 늘어요.

### 4. Query Rewrite와 Multi-Query (7-4강)

| | Query Rewrite | Multi-Query | 질문 분해 |
| --- | --- | --- | --- |
| 검색 문장 수 | 1 → 1 (바꿈) | 1 → 여러 개 (같은 뜻) | 1 → 여러 개 (다른 뜻) |
| 원질문 | 검색에선 대체 | 함께 검색 | 하위 질문으로 쪼갬 |
| 결과 처리 | 그대로 | `chunk_id`로 합치기 | 하위 질문별 근거를 모음 |

**문장을 바꾸기 전에 유지할 의도부터**

```text
원질문 (항상 유지)   교육비 정산 증빙은 무엇인가요?
변형 1 (사람이 작성) 교육비 지원 수강 완료 후 제출합니다
변형 2 (사람이 작성) 직무 교육비 정산 제출합니다
✗ 교육비 30만원을 받으려면?   ← 금액을 넣어 의도가 바뀜
```

문서 용어를 찾아 넣기 ≠ 답을 추측해 넣기. "수료증과 영수증"은 질문에 넣지 않았는데도 찾을 수 있어야 해요.

**세 문장으로 각각 검색 → `chunk_id`로 합치기**

```python
union = {}
for q in variants:
    for row in bm25(q, current, k=3):
        union.setdefault(row["chunk_id"], row)   # 없으면 넣고, 있으면 그대로(처음 것 유지)
# 교육비 정산 증빙은 무엇인가요? []
# 교육비 지원 수강 완료 후 제출합니다 [('education', 60), ('education', 0), ('retention', 120)]
# 직무 교육비 정산 제출합니다 [('education', 0), ('education', 60)]
# STEP2 합집합 3 [('education', 60), ('education', 0), ('retention', 120)]
```

- 합집합 순서는 **발견 순서**지 관련도 순서가 아니에요. `retention@120`은 잡음.
- 최종 답변 요청에는 **원질문 q10**을 넘겨요. 변형 문장을 질문으로 쓰면 묻지 않은 신청 절차·지원 한도까지 답할 수 있어요.

| 중복 제거 | 대상 | 도구 |
| --- | --- | --- |
| 검색 전 | 같은 검색 문장 | `dict.fromkeys` |
| 검색 후 | 같은 청크 | `chunk_id` + `setdefault` |

선택 실습 `rewrite.py`는 Ollama(gemma3)가 검색 표현을 만들게 해요. LLM 재작성은 질문마다 모델 호출이 한 번 더 들고, 검색도 문장 수만큼 늘어요. 효과가 있는지는 8장 평가로 확인해요.

## 내가 직접 적은 메모

- Dense 검색(시맨틱 검색)은 전혀 상관없는 질문에도 청크가 나온다(항상 Top-k를 돌려줌).
- BM25는 조사 하나에 따라 전혀 다른 결과로 이어질 수 있다(한계점).
- BM25와 TF-IDF의 차이: 문서 길이가 들어간다(현재 문서 길이를 전체 문서 평균과 비교해서 점수를 보정).
- 실무에서는 BM25·Dense의 k값을 조금 높게 설정해서 합산한다(Hybrid).
- Cross-Encoder `activation_fn=torch.nn.Identity()` = 소프트맥스(시그모이드) 없이 logit 값 그대로.
- Cross-Encoder 대신 실무에서는 Re-ranking 전용 상용 모델(API)을 쓸 수도 있다.

**생각해 두기:** 하이브리드 서치에서 왜 하필 이 두 기준(토큰 일치 BM25 + 의미 Dense)을 골랐을까? 두 검색의 속도·비용 차이는?

## 질문과 새로 알게 된 점

### 7-2 q\_hard: 문서 다양성 — 원문마다 한 청크씩

```python
fused = reciprocal_rank_fusion(rankings, k=6)
selected, seen_documents = [], set()
for row in fused:
    did = row["document_id"]
    if did not in seen_documents:
        selected.append(row)
        seen_documents.add(did)
    if len(selected) == 2: break
print("문서 다양성 실습:", [(r["document_id"], r["start"]) for r in selected])
# 문서 다양성 실습: [('meal', 60), ('travel', 0)]
# 그냥 상위 2개:    [('meal', 60), ('meal', 0)]
```

- `selected`는 결과물이라 청크 통째(`row`), `seen_documents`는 체크리스트라 이름만(`did`). 세트라 `.add`.
- 2개는 이 문제가 정한 최종 개수일 뿐이고, 포인트는 두 결과의 비교예요.
- meal 두 개가 **합쳐지는 게 아니라** `fused`(RRF 높은 순)에서 **먼저 나온 것**이 남고 나머지는 버려져요 → 점수 높은 `meal 60`.
- 대가: 식비 금액이 있는 `meal 0`이 빠져요. 그래서 "생각해 보기"에서 q06의 세 항목을 다 담으려면 몇 개를 어떻게 골라야 하는지 물어요.

### 7-3 q\_hard: 후보에서 빼고 다시 재정렬

```python
reduced = [row for row in candidates if row["document_id"] != "travel"]
new_pairs = [(run["question"], row["text"]) for row in reduced]
new_values = model.predict(new_pairs, batch_size=4, show_progress_bar=False)
# 후보 제거 실습: ['meal', 'meal', 'meeting', 'vpn', 'leave'] 5   → 새 1위 meal 60
```

- `row for row in …`: 앞 `row` = 담을 값, 뒤 `for row in` = 꺼낼 것. for문 + `append`와 결과가 같아요.
- Cross-Encoder는 (질문, 본문) **쌍**을 받아 점수를 매겨요.
- 남은 후보 어디에도 "1박당 12만원"이 없어요 → **Re-ranking은 받은 후보 안에서 순서만** 바꿔서 travel을 되살릴 수 없어요. 고칠 곳은 재정렬이 아니라 검색 단계.

### 7-4 `union.setdefault` vs `d[key] = value`

- `setdefault(키, 값)` = 키가 없으면 넣고, **있으면 아무것도 안 함**(처음 것 유지).
- 6-1의 `{row["chunk_id"]: row for …}`는 같은 키가 오면 **덮어써서 나중 것**이 남아요(같은 청크라 내용은 같음).
- `union.values()`로 청크만 꺼내 `(document_id, start)`로 짧게 출력.

### 7-4 `dict.fromkeys` — 질문 중복 제거

```python
queries = [question, variants[1], variants[1], variants[2]]
unique_queries = list(dict.fromkeys(queries))   # [question, variants[1], variants[2]]
```

- 리스트 값을 **키로만** 쓰는 딕셔너리(값은 전부 `None`)를 만들어요. 만드는 순간 중복이 빠지고, 순서는 처음 나온 자리를 유지해요.
- `list(딕셔너리)`는 **키만** 꺼내요(`list(d.values())`는 값만).
- `extend` vs `append`: `[1, 2].extend([3, 4])` → `[1, 2, 3, 4]`, `append` → `[1, 2, [3, 4]]`. 검색 결과 리스트를 이어 붙일 땐 `extend`.
- PPT 기준 기대 결과: 검색 횟수 3, 반환 청크 수 5(0 + 3 + 2), `chunk_id` 중복 제거 후 3. 검색 **전에** 질문 중복부터 빼서 같은 검색을 두 번 하지 않아요(시간·비용).

### 오늘 나온 중복 제거 4가지

| | 코드 | 대상 | 기준 | 남는 것 | 목적 |
| --- | --- | --- | --- | --- | --- |
| ① 6-1 | `list({row["chunk_id"]: row for row in repeated}.values())` | 청크 | `chunk_id` | 나중 것(덮어씀) | 같은 내용 두 번 안 넣기 |
| ② 7-4 합집합 | `union.setdefault(row["chunk_id"], row)` | 청크 | `chunk_id` | 처음 것 | 여러 질문 결과를 겹치지 않게 합치기 |
| ③ 7-4 질문 | `list(dict.fromkeys(queries))` | 질문 | 질문 글자 | 처음 것 | 같은 검색 두 번 안 하기(속도·비용) |
| ④ 7-2 다양성 | `if did not in seen_documents` | 청크 | `document_id` | 문서마다 첫 청크 | 한 문서가 자리를 다 차지하지 않게 (엄밀히는 중복 제거 아님) |

```text
① repeated = [meal 60, meal 0, travel 0, meal 60] → [('meal', 60), ('meal', 0), ('travel', 0)]
② STEP2 합집합 3 [('education', 60), ('education', 0), ('retention', 120)]
③ 검색 횟수 3 (질문 4개 중 중복 1개)
④ 문서 다양성: [('meal', 60), ('travel', 0)]  /  그냥 상위 2개: [('meal', 60), ('meal', 0)]
```

원리는 모두 **"딕셔너리 키(세트 원소)는 한 번만 들어간다"**. ①은 똑같은 청크만 지워서 meal 0이 남고, ④는 같은 문서면 다 지워서 meal 0까지 빠져요.

### 오늘 반복해서 나온 것

**앞 단계에서 빠진 건 뒤에서 못 살린다.**

- Context 예산에서 빠지면 출처가 될 수 없어요 (6-1)
- 검색 후보에 없으면 RRF도 Re-ranking도 못 살려요 (7-2·7-3)
- 그래서 실무에서는 앞 단계(검색기별 k)를 넉넉하게 잡고 뒤에서 줄여요.

## 실습 코드에서 직접 바꾼 점

원본 키트(`rag_day4` ZIP)와 비교한 내용입니다.

| 파일 | 바꾼 점 / 추가한 주석 |
| --- | --- |
| 7-1·7-2·7-4 `main.py` | `from printsection import print_section` + 구역마다 `print_section("1번")` … 출력 추가 |
| 7-1 `q_hard.py` | `for row in dense.search(question, k=6):` → `if row["document_id"] == "education":` → `found.append(row["start"])`, `print(row["start"], row["text"])` |
| 7-2 `q_hard.py` | 위 문서 다양성 코드 (`seen_documents.add(did)`, `if len(selected) == 2: break`) |
| 7-2 `rag_core.py` | `reciprocal_rank_fusion` 줄에 주석: `# 분모 상수 디폴트값. 순위에따라 점수차이를 크지않게 보정.` |
| 7-3 `q_hard.py` | `reduced = [row for row in candidates if row["document_id"] != "travel"]` → `new_repairs = [(run["question"], row["text"]) for row in reduced]` → `model.predict(new_repairs, batch_size=4, show_progress_bar=False)` → 출력 |
| 7-4 `rewrite.py` | 빈 줄 두 개만 추가 (내용 변경 없음) |

## 확인 문제

강의 내용을 바탕으로 직접 만든 복습 문제입니다. 객관식 4문제, 서술형 2문제이고 각 문제 바로 아래에 정답이 있습니다.

### 7-Q1. "영수증" BM25가 `[]` (7-1)

BM25로 "영수증"을 검색하면 `[]`, "영수증을"로 검색하면 education@60과 travel@0이 나왔다. 이유는?

① "영수증" 규정이 자료에 없어서  
② 토큰화가 공백·기호로만 잘라서 원문의 "영수증을"과 질문의 "영수증"이 다른 토큰이 돼서  
③ IDF가 0이 돼서 점수가 음수가 나와서  
④ Dense 검색이 먼저 실행돼 BM25 후보를 가져가서

<details>
<summary>정답 보기</summary>

**②** — `re.findall(r"[가-힣a-zA-Z0-9]+", …)`는 조사를 떼지 않아요. "영수증 검색이 비었다" ≠ "영수증 규정이 없다". 형태소 분석기로 바꾸는 게 개선 과제예요.

</details>

### 7-Q2. BM25 점수와 Dense 점수를 바로 더하지 않는 이유 (7-2)

q06에서 BM25 meal@60은 8.3049, Dense meal@60은 0.9134였다. RRF로 합치는 이유는?

① Dense 점수가 음수일 수 있어서  
② BM25 점수가 항상 정답이라서  
③ 두 점수를 더하면 chunk\_id가 바뀌어서  
④ 두 점수의 척도가 달라 그대로 더하면 BM25가 결과를 거의 다 정해서, 점수 대신 순위를 쓰려고

<details>
<summary>정답 보기</summary>

**④** — RRF는 `1 / (60 + rank)`만 더해서 척도와 상관없이 "양쪽에서 상위에 나온 후보"를 올려요. meal@60은 양쪽 1위라 1/61 + 1/61 = 0.032787.

</details>

### 7-Q3. Re-ranking의 한계 (7-3)

RRF 후보 8개에서 travel 청크를 모두 빼고 Cross-Encoder로 다시 점수 매겼다. 맞는 설명은?

① 재정렬은 받은 후보 안에서 순서만 바꾸므로 "1박당 12만원"을 되살릴 수 없다  
② Cross-Encoder는 전체 청크를 다시 검색해서 travel을 찾아온다  
③ `batch_size=4`를 8로 늘리면 travel이 다시 나온다  
④ `activation_fn=Identity()`를 빼면 travel이 다시 나온다

<details>
<summary>정답 보기</summary>

**①** — Cross-Encoder는 (질문, 후보) 쌍에만 점수를 매겨요. 후보에서 빠진 근거는 검색 단계(k, Hybrid)에서 고쳐야 해요. `batch_size`는 계산 묶음 크기, `Identity`는 점수 모양만 바꿔요.

</details>

### 7-Q4. Multi-Query 결과를 합칠 때 (7-4)

세 검색 문장의 결과를 `union.setdefault(row["chunk_id"], row)`로 합쳤다. 최종 답변을 요청할 때 모델에 넘길 질문은?

① 변형 1 "교육비 지원 수강 완료 후 제출합니다" — 검색이 가장 잘 됐으니까  
② 세 문장을 이어 붙인 긴 질문  
③ 사용자의 원질문 "교육비 정산 증빙은 무엇인가요?"  
④ 합집합 1위 청크의 본문

<details>
<summary>정답 보기</summary>

**③** — 변형 문장은 **검색용 표현**이에요. 그대로 질문으로 쓰면 사용자가 묻지 않은 신청 절차나 지원 한도까지 답할 수 있어요. 재정렬할 때도 원질문을 써요.

</details>

### 7-Q5. 서술형 — Dense는 왜 상관없는 질문에도 결과를 낼까 (7-1)

q11 "회사의 올해 매출 목표는 얼마인가요?"는 자료에 답이 없는데 Dense는 leave@0(0.7986) 등 3개를 돌려줬고 BM25는 `[]`였다. 차이를 설명하고, 6장과 연결해 어떻게 처리해야 하는지 쓰세요.

<details>
<summary>예시 답안</summary>

Dense는 모든 청크와의 코사인 유사도를 계산해 **가장 가까운 k개를 항상** 돌려줘요. 상관없는 질문이어도 "그나마 가까운" 청크가 나와요. BM25는 겹치는 토큰이 없으면 0점이라 후보에서 빠져서 빈 목록이 돼요. 그래서 "결과가 있다"만으로 답하면 안 되고, 6-4처럼 Context를 읽어 필요한 사실이 없으면 `insufficient`로 보류하고 무엇이 없는지(매출 목표 자료) 적어야 해요. 4장 threshold처럼 점수 하한을 두는 방법도 있지만, 점수만으로는 관련 여부를 확실히 가를 수 없어요.

</details>

### 7-Q6. 서술형 — 중복 제거 ①과 ④의 차이 (6-1·7-2)

6-1 `chunk_id` 중복 제거와 7-2 문서 다양성(`document_id`마다 하나)은 둘 다 "겹치는 걸 뺀다". q06에서 결과가 어떻게 달라지는지, 각각 언제 쓰는지 쓰세요.

<details>
<summary>예시 답안</summary>

①은 **완전히 같은 청크**(같은 `chunk_id`)만 지워서 meal 60, meal 0, travel 0이 모두 남아요 — 같은 내용을 Context에 두 번 넣지 않으려고 써요. ④는 **같은 문서면 첫 청크만** 남겨서 meal 60, travel 0이 되고 식비 금액(meal 0)이 빠져요 — 한 문서가 자리를 다 차지하지 않게 여러 문서를 고르게 담고 싶을 때 써요. q06처럼 한 문서의 여러 청크가 다 필요한 질문에는 ④가 근거를 잃게 해서, 최종 개수를 늘리거나 ①만 쓰는 게 나아요.

</details>
