# 4장. 임베딩과 Dense 검색 — 벡터, 코사인 Top-k, k·Threshold, 모델 비교 기준선

> 2026-10-20 학습 기록. RAG 2일차 오후 수업입니다. 3장에서 만든 `chunks.json`(28개, 80/20)을 E5 small로 384차원 벡터로 바꾸고, 질문 벡터와의 코사인 점수로 Top-k를 뽑고, k와 점수 하한이 남기고 거르는 근거를 비교한 뒤, 개발 질문 12개로 Dense 기준선을 저장했습니다. **공식을 NumPy 코드로 옮겨 보는 것**이 이해에 가장 도움이 됐습니다. 네 강의 실습 문제(q\_easy·q\_hard)를 모두 직접 풀어 확인했습니다.

## 학습 목표

- 토큰 벡터를 문장 벡터로 모으는 pooling과 길이 1 정규화를 수치로 설명하고, 청크 28개를 `(28, 384)` 벡터로 저장한다.
- 내적과 코사인 유사도의 차이를 손계산과 NumPy 코드로 맞추고, 행 번호로 원문을 연결해 Top-k를 구한다.
- k(최대 개수)와 threshold(점수 하한)가 어떤 근거를 추가하고 없애는지 순위표로 설명한다.
- 모델만 바꾸고 나머지를 고정해 Hit@k·문서 Recall로 기준선을 기록하고, 평균 뒤의 질문별 차이를 읽는다.

## 실습 파일

| 강 | 주제 | 실습 상태 |
| --- | --- | --- |
| 4-1 | 텍스트 임베딩과 벡터 표현 — pooling, 정규화, E5 `passage:`, `vectors.npy` | ✅ 완료 |
| 4-2 | 코사인 유사도와 Top-k — 내적 vs 코사인, `vectors @ query`, 행 번호 정렬 | ✅ 완료 |
| 4-3 | Dense Retriever의 Top-k / Threshold — k·하한 비교, 근거 누락 | ✅ 완료 |
| 4-4 | 임베딩 모델 비교와 Dense 기준선 — Golden dev 12, Hit@3·Recall@3 | ✅ 완료 |

3장과 같은 `rag_day2` 키트로 진행했습니다. E5 모델은 수업 전에 `check_embedding.py`로 미리 받아 두었고(`"shape": [2, 384]`), 4-2\~4-4는 `prepare.py`로 벡터를 먼저 만든 뒤 `main.py`를 실행하고, 강마다 `q_easy.py`·`q_hard.py`를 풀어 정답을 확인했습니다. 외부 임베딩 API 비교와 E5 base 직접 실행은 선택 실습이라 하지 않았습니다(base 결과는 키트의 기록 파일로 확인).

## 전체 흐름

### 한 문장

**청크와 질문을 같은 모델로 숫자 벡터로 바꾸고, 방향이 가까운(코사인이 큰) 청크부터 고르되, 점수가 높다는 것과 답이 있다는 것은 원문을 읽어 따로 확인합니다.**

### 왜 필요한가

```text
1장의 단어 일치 검색:  "호텔비" → []        ← 본문엔 "숙박 비용"이라서 못 찾음
4장의 Dense 검색:     "출장 호텔비는 얼마까지인가요?" → 뜻이 가까운 travel 청크를 찾음
```

**비유:** 도서관 책마다 "내용 좌표"를 찍어 두고(임베딩), 질문도 같은 지도에 좌표를 찍은 다음, **방향이 가장 비슷한** 책부터 꺼내 오는 것과 같습니다. 다만 지도에서 가깝다고 그 책에 답이 있다는 보장은 없어서, 꺼낸 책은 직접 펼쳐 봐야 합니다.

### 그림으로 보기

```text
chunks.json (28개, 3-4)
   │  "passage: " + text        ← 문서 접두사 (질문은 "query: ")
   ▼
4-1  model.encode(normalize_embeddings=True)   → vectors (28, 384), 각 행 길이 1
     np.save + embedding_config.json(모델·차원·지문)
   ▼
4-2  query = encode("query: " + 질문)          → (384,)
     scores = vectors @ query                  → (28,)  정규화했으니 내적 = 코사인
     현행 필터 → 점수순 정렬(행 번호) → 원문 연결
   ▼
4-3  score >= threshold → 앞에서 k개           → 근거가 추가/누락되는지 순위표로 확인
   ▼
4-4  dev 12문항 × k=3 → Hit@3, Recall@3        → dense_baseline.json (5장 이후 비교 기준)
```

### 강의 흐름

1. **4-1 벡터 만들기** — 청크 28개 → 패딩을 뺀 평균 pooling과 길이 1 정규화를 손계산 → E5에 `passage:`를 붙여 인코딩 → `(28, 384)`와 설정 파일 저장.
2. **4-2 점수 매기기** — 2차원 손계산으로 내적과 코사인 차이 확인 → 정규화하면 내적 = 코사인 → `vectors @ query`로 28개를 한 번에 계산 → 행 번호로 원문을 찾고, 점수와 답의 존재를 구분.
3. **4-3 몇 개를, 어디까지** — q06을 세 항목으로 나눠 k를 늘리며 추가되는 정보, 하한을 높이며 사라지는 근거를 확인.
4. **4-4 기준선** — 모델 말고 전부 고정하고 개발 질문 12개로 Hit@3·Recall@3을 기록, 질문별 결과까지 저장.

## 핵심 이론

### 1. 텍스트 임베딩과 벡터 표현 (4-1강)

- **임베딩** = 텍스트를 비교 가능한 숫자 벡터로 바꾼 것. 관련 문장 쌍은 가깝게 학습된 모델을 검색에 씀.
- 문서는 12개지만 검색 단위가 청크라서 벡터도 **28개**. `(28, 384)` = 28행(청크) × 384열(벡터 성분). `vectors[i]` ↔ `chunks[i]`가 같은 청크.
- 모델: `intfloat/multilingual-e5-small` — 384차원, 한국어 지원, **입력 한도 512토큰**, CPU. 384(출력 차원)와 512(입력 한도)는 다른 숫자.
- 문서 `"passage: "`, 질문 `"query: "`. 원문 `text`에는 저장하지 않고 인코딩할 때만 붙임.
- `load_model()`은 `SentenceTransformer(model_id, device="cpu", cache_folder=…)`를 돌려주는 보조 함수. SentenceTransformer는 토크나이저 + 모델 + pooling(+ 정규화)을 한 번에 처리해서, 손계산 pooling을 실제 출력에 다시 적용하지 않음.
- 이번 28개 입력의 최대 길이는 49토큰. 첫 청크를 30번 반복하면 1234토큰 → 한도 초과라 인코딩하지 말고 다시 청킹.
- 벡터의 특정 성분 하나를 "숙박"처럼 해석하지 않음. 여러 성분이 함께 의미를 표현.
- 저장: `vectors.npy` + `embedding_config.json`(`model_id`, `dimension`, `normalized`, `input_format`, `chunk_fingerprint`). fingerprint는 청크 ID·본문·**순서**를 묶은 해시라서, 청크가 바뀌면 `load_vectors`가 "다시 임베딩하라"고 오류를 냄.

### 2. 코사인 유사도와 Top-k (4-2강)

| 후보 | 벡터 | 내적 q·d | 길이 | 코사인 | 뜻 |
| --- | --- | --- | --- | --- | --- |
| d₁ | [6, 8] | 3×6 + 4×8 = 50 | 10 | 50/(5×10) = **1** | 같은 방향 (q보다 2배 길어도 1) |
| d₂ | [4, −3] | 12 − 12 = 0 | 5 | **0** | 직각 |
| d₃ | [−3, −4] | −9 − 16 = −25 | 5 | **−1** | 반대 방향 |

(q = [3, 4], 길이 5)

- 내적은 길이의 영향을 받고, 코사인은 길이로 나눠 **방향만** 비교.
- E5 벡터는 정규화돼 있어서 `scores = vectors @ query` 한 번으로 28개 코사인이 나옴: `(28, 384) @ (384,) → (28,)`.
- 점수 배열만 정렬하면 어느 청크 점수인지 잃어버림 → **행 번호를 정렬**: 현행 필터 후 `key=lambda i: (-score, chunk_id)`.
- q05 "출장 숙박 비용 한도와 필요한 증빙은?" → 1 travel:0(0.8945) · 2 meal:0 · 3 meal:60 · 4 travel:60. 2위 meal의 1일 3만원은 **식비**라서 금액과 단위는 원문으로 구별.
- **점수 ≠ 답의 존재.** 자료에 없는 "매출 목표" 질문에도 leave:0(0.7986)이 1위. 0.7986은 정답 확률 79.86%가 아님.
- 거리 = 1 − 유사도는 **작을수록** 가까움. 저장소 API의 `score`가 유사도인지 거리인지 확인(Qdrant Cosine 점수는 클수록 유사).

### 3. Top-k와 Threshold (4-3강)

- 검색 순서: **현행 필터 → 점수순 정렬 → 하한(`score >= threshold`) → 앞에서 k개.** k는 최대 개수라 통과 후보가 2개면 k=5여도 2개. `threshold=None`은 하한만 생략(현행 필터는 유지).
- q06 "출장 식비와 숙박비의 한도는 각각 얼마이고 두 한도를 합쳐 쓸 수 있나요?" → 필요한 근거 3개가 서로 다른 청크에 있음.

| 순위 | 청크 | 점수 | 담긴 내용 |
| --- | --- | --- | --- |
| 1 | meal:60 | 0.9134 | 한도 합산 금지 |
| 2 | meal:0 | 0.8858 | 식비 1일 3만원 |
| 3 | travel:0 | 0.8768 | 숙박 1박당 12만원 |
| 4 | travel:120 | 0.8601 | 교통비·식비 미규정 문장 일부 |
| 5 | travel:60 | 0.8557 | 초과 숙박 사전 승인 |

| k | 찾은 문서 | 문서 Recall | 원문 문자 |
| --- | --- | --- | --- |
| 1 | meal | 0.5 | 55 |
| 2 | meal | 0.5 | 135 |
| **3** | meal, travel | **1.0** | 215 |
| 5 | meal, travel | 1.0 | 323 |

- k=1과 k=2는 **문서 Recall이 같아도 읽을 수 있는 정보가 다름**(k=2에서 식비 금액 추가). k=3에서 세 항목 완성.

| threshold (k=5) | 남은 수 | 문서 | 잃은 것 |
| --- | --- | --- | --- |
| None · 0.80 · 0.84 | 5 | meal, travel | — |
| 0.88 | 2 | meal만 | travel:0(0.8768) → **숙박 금액** |
| 0.90 (직접 바꿔 실험) | 1 | meal만 | 식비 금액까지 → **합산 금지 문장만** 남음 |

- 결과가 줄었다고 검색이 좋아진 게 아님. 답 있는 질문 `[0.91, 0.89, 0.88]` vs 답 없는 질문 `[0.80, 0.80, 0.78]`만 보면 0.80으로 나눌 수 있을 것 같지만, 용어가 겹치는 질문은 답이 없어도 점수가 높을 수 있어서 점수 하나로 답변 보류를 정하기 어려움(6장에서 다룸).

### 4. 모델 비교와 Dense 기준선 (4-4강)

- **모델 말고 전부 고정**: 12문서, 28청크(80/20), `status=current`, `passage:`/`query:`, 정규화 코사인, k=3, dev 12개(최종 확인 8개 보관).
- Golden dev 12개 = 답 있는 질문 10 + 답 없는 질문 2. `reference`는 채점용이라 생성 모델에 넘기지 않음.
- **Hit@k** = 상위 k에 정답 문서가 하나라도 있으면 1. **문서 Recall@k** = 필요한 정답 문서 중 찾은 비율. 같은 문서의 청크 여러 개는 문서 하나로 셈. 답 없는 질문은 분모 0이라 평균에서 분리.
- E5 small: Hit@3 = 1.0, Recall@3 = 1.0. 하지만 q10은 education 외에 meal·travel도 반환, q12(취미 강좌)는 "규정되어 있지 않다" 문장 때문에 education이 상위 → **지표 1.0 ≠ 모든 후보가 관련 있음 ≠ 답해도 됨**.
- 모델을 바꾸면 **문서와 질문을 모두 다시 임베딩**(base는 768차원). small 문서 벡터 + base 질문 벡터는 섞을 수 없음.
- small·base 둘 다 1.0이라 평균으로는 구분 불가. 그런데 검색된 문서 목록은 5개 질문에서 다름:

| 질문 | E5 small | E5 base |
| --- | --- | --- |
| q04 | incident, equipment | incident |
| q09 | education | education, incident |
| q10 | education, meal, travel | education, travel, retention |
| q11 (답 없음) | leave, education | retention, vpn, incident |
| q12 (답 없음) | education, meeting | education, meeting, retention |

- 이 질문 세트로는 큰 모델의 추가 비용을 정당화할 근거가 부족. 달라진 질문은 원문을 직접 대조하고, 최종 확인 질문과 실제 업무 질문으로도 확인. 속도는 로드·임베딩·질의 시간을 나눠 같은 장비에서 반복 측정.

## 공식을 NumPy 코드로

공식만 볼 때보다 **한 줄씩 NumPy로 옮겨 값을 찍어 보니** 이해가 훨씬 빨랐습니다.

| 개념 | 공식 | NumPy 코드 | 예시 값 |
| --- | --- | --- | --- |
| 마스크 평균 pooling | $\bar{h} = \dfrac{\sum_i m_i h_i}{\sum_i m_i}$ | `(tokens * mask[:, None]).sum(axis=0) / mask.sum()` | `[[1,2],[3,0],[99,99]]`, mask `[1,1,0]` → `[2, 1]` |
| L2 길이(norm) | $\lVert x\rVert = \sqrt{\sum_j x_j^2}$ | `np.linalg.norm(x)` | `[2,1]` → √5 ≈ 2.236 |
| 정규화 | $\hat{x} = x / \lVert x\rVert$ | `x / np.linalg.norm(x)` | `[2,1]/√5` = `[0.8944, 0.4472]` (제곱합이 1, 합은 1.34) |
| 내적 | $q \cdot d = \sum_j q_j d_j$ | `candidates @ q` | `[[6,8],[4,-3],[-3,-4]] @ [3,4]` → `[50, 0, -25]` |
| 후보별 길이 | $\lVert d_i\rVert$ | `np.linalg.norm(candidates, axis=1)` | `[10, 5, 5]` |
| 코사인 | $\cos(q,d) = \dfrac{q \cdot d}{\lVert q\rVert\,\lVert d\rVert}$ | `dots / (np.linalg.norm(candidates, axis=1) * np.linalg.norm(q))` | `[1.0, 0.0, -1.0]` |
| 정규화 후 코사인 | $\cos = \hat{q} \cdot \hat{d}$ | `d_unit @ q_unit` | 위와 같음(`np.allclose` True) |
| 코사인 거리 | $1 - \cos$ | `1 - cosines` | `[0, 1, 2]` (작을수록 가까움) |
| 실제 검색 점수 | 28개 코사인 | `scores = vectors @ query` | `(28, 384) @ (384,) → (28,)` |
| 높은 순 행 번호 | — | `np.argsort(-scores)` | `[1,0,2]` (값이 아니라 **번호**) |

**`axis` 정리** — `axis=n`은 n번 축을 **없애는 방향**으로 계산합니다.

```python
x = np.array([[1, 2],
              [3, 0],
              [0, 0]])          # (3, 2)
x.sum(axis=0)   # [4, 2]  세로로 → (2,)   pooling: 토큰(행)들을 하나로 합칠 때
x.sum(axis=1)   # [3, 3, 0] 가로로 → (3,)
np.linalg.norm(candidates, axis=1)   # 후보(행)마다 길이 하나씩 → (3,)
```

- `mask[:, None]`은 `(3,)` → `(3, 1)`로 세로로 세워서, 마스크 값이 각 행의 모든 칸에 곱해지게 함(브로드캐스팅). 안 세우면 `(3, 2) * (3,)`은 모양이 맞지 않아 오류.
- `np.linalg.norm(q)`(숫자 하나)를 `[10, 5, 5]`에 곱하면 세 칸 모두에 자동으로 곱해지고, 나눗셈도 **같은 자리끼리** 계산됨 → 반복문 없이 후보 3개(실제는 28개)를 한 번에 처리.

## 질문과 새로 알게 된 점

### 코사인 — 후보를 하나씩 vs 한 번에

```python
# 하나씩 (for문)
cosines = []
for d in candidates:
    dot = d @ q
    cosines.append(dot / (np.linalg.norm(d) * np.linalg.norm(q)))

# 한 번에 (NumPy) — 결과 같음
cosines = (candidates @ q) / (np.linalg.norm(candidates, axis=1) * np.linalg.norm(q))
```

후보가 수천\~수만 개가 되면 행렬 계산 한 줄이 반복문보다 훨씬 빠름. 실제 검색의 `vectors @ query`가 같은 방식.

### `exact_rows`의 핵심 부분을 for문으로 풀기

```python
eligible = []
for i, c in enumerate(chunks):                       # 1. 현행 청크의 행 번호만
    if c["metadata"]["status"] == "current":
        eligible.append(i)

order = sorted(eligible, key=lambda i: (-float(scores[i]), chunks[i]["chunk_id"]))   # 2. 점수 높은 순

results = []
for i in order:                                      # 3. 하한 통과만
    if threshold is None or scores[i] >= threshold:
        row = dict(chunks[i])
        row["score"] = float(scores[i])
        results.append(row)

return results[:k]                                   # 4. 앞에서 k개
```

`{**chunks[i], "score": …}`는 원래 청크 dict를 복사하고 `score`를 추가하는 표현.

### 퀴즈 4-4 — `small_rows`와 `.items()`

```python
report["rows"]  # 리스트: [{"question_id": "q01", "retrieved_document_ids": ["leave", "travel"], "hit": 1, …}, …]
small_rows = {r["question_id"]: r for r in report["rows"]}
# dict: {"q01": {…q01 결과 전체…}, "q02": {…}, …}  → small_rows["q05"]로 바로 찾기
```

- 리스트 순서(`rows[4]`)끼리 비교하면 두 결과의 순서가 다를 때 엉뚱한 질문끼리 비교됨 → **질문 ID로 짝을 맞춤**(1-2강 `by_id`와 같은 방법).
- `for question_id, before in small_rows.items():`에서 `before`는 문서 목록이 아니라 **그 질문의 결과 dict 전체**. 목록은 `before["retrieved_document_ids"]`로 한 번 더 꺼냄.
- 목록 비교 `!=`는 **순서까지** 봄.

## 실습 코드에서 직접 바꾼 점

원본 키트(`rag_day2` ZIP)와 비교한 내용입니다.

| 강 | 바꾼 점 / 추가한 주석 |
| --- | --- |
| 공통 | 네 강의 `main.py`에 `print_section` 구역 출력 추가 |
| 4-1 `main.py` | 중간값을 직접 확인하려고 `print(f"mask: {mask}")`, `print(f"mask[:, None]: {mask[:, None]}")`, `print(f"pooled: {pooled}")`, `print(f"np.linalg.norm: {np.linalg.norm(pooled)}")` 추가 |
| 4-2 `main.py` | 코사인을 후보 하나씩 계산하는 for문 버전 추가(아래 에러 참고) |
| 4-3 `main.py` | `gold = {"meal", "travel"} #원하는 문서. 식비와 숙박비에 대한 정답지.` / threshold 목록의 0.88을 **0.90으로 바꿔 실험** → 1개(meal:60)만 남아 두 금액 모두 누락 / 끝에 `#질문마다 달라지기때문에 기준정하는것이 어려움.` |
| 4-4 `main.py` | `#sota기준. 더 좋은 base모델찾기. 기준을 높게찍은다음 맞추기 or 상용화된 모델 기준 다른모델은 얼마나 좋아지는지.` |
| 4-4 `q_easy.py` | 빈칸 위에 q\_hard의 TODO 두 줄을 옮겨 적어 두고 풀이 |

## 에러와 원인

| 상황 | 에러 | 원인 | 해결 |
| --- | --- | --- | --- |
| 4-2 `uv run main.py` 첫 실행 | `FileNotFoundError: embedding_config.json` | 4-2\~4-4는 벡터 파일을 먼저 만들어야 함 | `uv run prepare.py` → `uv run main.py` |
| 4-2 for문 버전 추가 후 | `AttributeError: 'list' object has no attribute 'tolist'` | for문이 NumPy 배열 `cosines`를 **파이썬 리스트**로 덮어써서, 아래 `cosines.tolist()`가 실패. `from main import *`를 쓰는 q\_easy·q\_hard도 같이 실패 | for문 결과를 다른 이름(예: `cosines_loop`)에 담거나 `np.array(...)`로 감싸기 |
| `printsection` import에 밑줄 | — | VS Code가 1일차 `rag_day1` 인터프리터를 보고 있었음 | Python: Select Interpreter → `rag_day2\.venv\Scripts\python.exe` |
| 모델 받을 때 경고 | `You are sending unauthenticated requests to the HF Hub` | 로그인 없이 받았다는 안내 | 공개 모델이라 무시해도 됨 |

## 확인 문제

강의 내용을 바탕으로 직접 만든 복습 문제입니다. 객관식 4문제, 서술형 2문제이고 각 문제 바로 아래에 정답이 있습니다.

### 4-Q1. 벡터 shape (4-1)

문서는 12개인데 `vectors.npy`의 shape가 `(28, 384)`인 이유는?

① 검색 단위가 청크라서 청크 28개마다 벡터를 하나씩 만들었고, 384는 한 벡터의 차원이다  
② 문서 12개를 384토큰씩 나눴더니 28개가 됐다  
③ 28은 모델의 입력 토큰 한도이고, 384는 청크 개수다  
④ 구버전 문서를 빼고 현행 문서만 임베딩해서 28개가 됐다

<details>
<summary>정답 보기</summary>

**①** — 행은 청크(28), 열은 벡터 성분(384). 입력 한도는 512토큰으로 별개. 벡터는 구버전 청크까지 모두 만들고 현행 필터는 검색 때 적용.

</details>

### 4-Q2. 내적과 코사인 (4-2)

`q=[3,4]`, `d=[6,8]`일 때 내적과 코사인 유사도는?

① 내적 25, 코사인 0.5  
② 내적 50, 코사인 2  
③ 내적 50, 코사인 1  
④ 내적 100, 코사인 1

<details>
<summary>정답 보기</summary>

**③** — 내적 3×6 + 4×8 = 50, 코사인 50/(5×10) = 1. d가 두 배 길어도 방향이 같으면 1.

</details>

### 4-Q3. threshold 0.88 (4-3)

q06에서 k=5, threshold=0.88로 검색했더니 meal 청크 2개만 남았다. 옳은 해석은?

① 후보가 줄어 깔끔해졌으니 0.88이 가장 좋은 설정이다  
② travel:0(0.8768)이 하한에 걸려 빠지면서 숙박비 금액 근거를 잃었다  
③ k=5인데 2개만 나왔으니 검색 함수에 오류가 있다  
④ threshold=0.88이면 현행 필터가 꺼져서 결과가 바뀐 것이다

<details>
<summary>정답 보기</summary>

**②** — 0.8768 < 0.88. k는 최대 개수라 2개만 나오는 게 정상이고, threshold는 현행 필터와 별개.

</details>

### 4-Q4. Hit와 Recall (4-4)

q06 정답 문서 `{meal, travel}`, 상위 3개가 `meal:60`, `meal:0`, `leave:0`이라면?

① Hit 1, Recall 1.0  
② Hit 0, Recall 0.5  
③ Hit 2, Recall 0.67  
④ Hit 1, Recall 0.5

<details>
<summary>정답 보기</summary>

**④** — 정답 문서가 하나라도 있어서 Hit 1. meal 청크 2개는 문서 하나라 Recall 1/2.

</details>

### 4-Q5. 서술형 — 점수와 답의 존재 (4-2, 4-3)

"회사의 올해 매출 목표는?"에 leave가 0.7986점으로 1위였다. "답변 가능"으로 판단하면 안 되는 이유와, threshold 0.80으로 걸러내는 방식의 한계를 쓰세요.

<details>
<summary>예시 답안</summary>

Top-k는 정답 유무를 판단하지 않고 상대적으로 가까운 청크의 순위만 매겨서, 답이 없어도 항상 무언가가 나옴. 0.7986은 확률이 아니고 휴가 규정에 매출 목표는 없음. 0.80은 이번 두 질문에서만 우연히 나뉜 값이고, 용어가 겹치는 질문(취미 강좌 → education)은 답이 없어도 점수가 높을 수 있음. 반대로 하한을 높이면 q06처럼 필요한 근거까지 잘림. 원문을 읽어 판단하고 여러 질문으로 검증해야 함.

</details>

### 4-Q6. 서술형 — 모델 비교 (4-4)

E5 small에서 base로 바꿔 비교할 때 무엇을 고정하고 무엇을 다시 만들어야 하나요? 둘 다 Hit@3 = 1.0이면 어떻게 해석하나요?

<details>
<summary>예시 답안</summary>

고정: 문서·청크(80/20)·현행 필터·입력 규칙·정규화 코사인·k=3·dev 질문. 다시 만들 것: 문서와 질문 벡터를 **모두** base로 새로 임베딩(768차원). 둘 다 1.0이면 이 질문 세트가 두 모델을 구분하지 못한 것이라 큰 모델의 비용을 정당화할 근거가 없음. 질문별 검색 문서(q04·q09·q10·q11·q12에서 다름)를 원문과 대조하고, 보관한 최종 확인 질문과 실제 업무 질문으로 다시 확인.

</details>
