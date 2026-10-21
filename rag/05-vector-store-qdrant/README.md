# 5장. Vector Store — Qdrant에 저장하고, 거르고, 갱신하기

> 2026-10-21 학습 기록. RAG 3일차 오전 수업입니다. 4장에서 만든 E5 벡터 28개를 원문과 함께 Qdrant Point로 저장하고(5-1·5-2), metadata 필터로 검색 범위를 정하고(5-3), 청킹이 바뀌었을 때 이전 Point를 정리하는 방법과 ANN을 살펴봤습니다(5-4). 수업 뒤 추가 과제로 같은 실습을 **Qdrant Cloud**로 옮기고(Strict Mode 대응), **FAISS**로 정확 검색과 HNSW 검색도 해 봤습니다.

## 학습 목표

- 청크 하나가 `id + vector + payload` Point로 저장되는 구조를 설명하고, `uuid5`로 같은 청크에 항상 같은 ID를 만든다.
- Collection을 만들고 Point 28개를 Upsert한 뒤, 질문 벡터와 metadata 필터로 Top-k를 검색해 4장 NumPy 결과와 비교한다.
- 필터는 점수를 바꾸지 않고 **후보 자격**을 정한다는 점을 구분하고, `must`·`Range`·`scroll`과 빈 결과의 원인을 설명한다.
- 청킹이 바뀌면 이전 Point가 남는 이유를 ID 집합으로 설명하고(`old_ids - new_ids`), 전수 검색과 ANN의 차이를 계산한다.
- `:memory:`와 Qdrant Cloud의 차이(데이터 유지, Strict Mode 인덱스)를 직접 겪고 정리한다.

## 실습 파일

| 강 | 주제 | 실습 상태 |
| --- | --- | --- |
| 5-1 | Vector Store와 Qdrant 데이터 모델 — Point, `uuid5`, Upsert 두 번, `retrieve` | ✅ 완료 |
| 5-2 | Collection 생성 / Upsert / Query — 28개 등록, current 필터, `SavedDenseIndex` | ✅ 완료 (Qdrant Cloud로도 실행) |
| 5-3 | Metadata Filter와 검색 범위 제어 — 구버전 혼입, `must`, `Range`, `scroll`, 빈 결과 | ✅ 완료 (Qdrant Cloud로도 실행) |
| 5-4 | 데이터 갱신과 ANN 검색 개요 — 3 → 5 → 2, stale ID 삭제, ANN 겹침 | ✅ 완료 |
| 추가 과제 1 | Qdrant Cloud로 5-2·5-3 실행 (Strict Mode 인덱스) | ✅ 완료 |
| 추가 과제 2 | FAISS로 같은 검색 — `IndexFlatIP`(정확) / `IndexHNSWFlat`(ANN) | ✅ 완료 |

수업에서 받은 `rag_day3` 키트(5·6장 8개 강의 + 공통 uv 환경)로 진행했습니다. 강마다 `prepare.py`로 벡터를 먼저 만들고 `main.py` → `q_easy.py`·`q_hard.py` 순서로 확인했습니다. 키트 코드는 올리지 않고, **원본 ZIP과 비교해 직접 바꾸거나 추가한 부분**만 아래에 기록합니다. Qdrant Cloud의 URL·API 키(`.env`)는 올리지 않습니다.

## 전체 흐름

### 한 문장

**4장의 검색 결과는 "7번 행, 0.89점"뿐이라 무슨 규정인지 읽을 수 없었습니다. Qdrant는 벡터와 원문·출처를 Point로 함께 저장해서, 검색하면 점수와 본문이 같이 돌아옵니다.**

### 왜 필요한가

```text
4장 NumPy 검색:  scores = vectors @ query  → 7번 행 0.8945   ← 원문은 chunks[7]로 따로 찾아야 함
5장 Qdrant 검색: query_points(...)          → score 0.8945 + payload(본문·출처·status)
                 + 필터(현행만)도 검색할 때 같이
```

**비유:** 4장은 번호표만 붙은 사물함이라 번호를 받으면 장부를 다시 뒤져야 했고, 5장은 **물건(원문)까지 함께 들어 있는 사물함**이에요. 사물함 문에는 라벨(metadata)이 붙어 있어서 "현행 규정 칸만 열어 줘"처럼 고를 수도 있어요.

### 그림으로 보기

```text
4장 결과: chunks.json(28) + vectors.npy(28×384)
   │  5-1  PointStruct(id=uuid5(chunk_id), vector=vectors[i].tolist(), payload=chunks[i])
   ▼
Collection "campus_saved_e5"  (VectorParams(size=384, distance=COSINE))
   │  5-2  upsert(28개) → query_points(query, limit=3, query_filter=current) → .points
   ▼
결과 = score + payload   (4장과 같은 순서: 0.8945 · 0.875 · 0.8444)
   │  5-3  Filter(must=[status=current, category=출장]) · Range(start ≥ 60) · scroll
   │  5-4  다시 청킹: upsert(3 → 5) → delete(old_ids − new_ids) → 2 · ANN은 일부만 탐색
   ▼
6장: 검색 결과를 Context로
```

### 강의 흐름

1. **5-1 Point 하나** — 같은 행 번호로 `chunks[7]`과 `vectors[7]`을 꺼내 Point로 묶고, Collection에 두 번 Upsert해도 1개(같은 ID), ID로 `retrieve`.
2. **5-2 28개와 검색** — `zip`으로 28쌍을 Point로 만들어 Upsert, 질문을 `query:`로 임베딩, current 필터로 Top-3. 같은 절차를 `SavedDenseIndex` 클래스로 묶어도 결과가 같음(`True`).
3. **5-3 필터** — "8만원인가요?"에 구버전이 2위로 올라오는 것을 current 필터로 제외, status AND category, `Range(gte=60)`, `scroll`, 없는 분류로 생긴 `[]`.
4. **5-4 갱신과 ANN** — 80/20 → 100/20으로 다시 청킹하면 ID가 모두 바뀌어 이전 3개가 남음 → 새 2개 Upsert(5) → stale 3개 삭제(2). ANN은 일부만 탐색해서 가까운 점을 놓칠 수 있음.

## 핵심 이론

### 1. Point = id + vector + payload (5-1강)

| Point 항목 | 이번 데이터 | 검색 후 용도 |
| --- | --- | --- |
| `id` | 청크 ID에서 만든 UUID | 조회, 교체, 삭제 |
| `vector` | `vectors.npy`의 해당 행 (384개 실수) | 질문과 유사도 계산 |
| `payload` | 청크 dict 전체 (본문, 문서 ID, 범위, metadata) | 본문 반환, 필터, 출처 표시 |

```python
number = next(i for i, c in enumerate(chunks) if c["document_id"] == "travel")   # 7
chunk, vector = chunks[number], vectors[number]          # 같은 번호로 꺼내야 짝이 맞음

point_id = str(uuid5(NAMESPACE_URL, chunk["chunk_id"]))  # 같은 chunk_id → 항상 같은 UUID
point = models.PointStruct(id=point_id, vector=vector.tolist(), payload=chunk)

client = QdrantClient(":memory:")
client.create_collection("point_demo",
    vectors_config=models.VectorParams(size=int(vectors.shape[1]), distance=models.Distance.COSINE))
for repeat in range(2):
    client.upsert("point_demo", points=[point], wait=True)    # 등록 1 → 1개, 등록 2 → 1개
saved = client.retrieve("point_demo", ids=[point_id], with_payload=True)[0]
```

- Qdrant Point ID는 정수나 UUID만 돼서, 문자열 `chunk_id`(`travel:46fb…:80:20:0`)를 `uuid5`로 바꿔요. 무작위 `uuid4`면 다시 넣을 때마다 Point가 하나씩 늘어나요.
- **Upsert는 ID로만 판단**해요. 본문이 같아도 ID가 다르면 2개가 돼요.
- `size`는 벡터 길이 384예요(Point 개수 28이 아님). `size`와 `distance`는 만든 뒤 바꿀 수 없어요.
- payload의 `category` 같은 값은 **임베딩에 들어가지 않아요.** 임베딩은 4장에서 `"passage: " + 본문`으로만 만들었고, metadata는 필터로 써요.
- 퀴즈: 교육비 청크를 추가할 때 `vector=vectors[number]`(출장 벡터)를 잘못 쓰면 **둘 다 384차원이라 오류 없이** 교육비 본문에 출장 벡터가 붙어요.

| 조회 방법 | 기준 | 질문 벡터 |
| --- | --- | --- |
| `retrieve` | Point ID 일치 | 필요 없음 |
| `query_points` | 벡터 유사도 | 필요 |
| `scroll` | 조건(필터)에 맞는 목록 | 필요 없음 |

### 2. Collection / Upsert / Query (5-2강)

```python
points = []
for chunk, vector in zip(chunks, vectors):          # 같은 위치끼리 짝 (번호 대신 zip)
    points.append(models.PointStruct(id=str(uuid5(NAMESPACE_URL, chunk["chunk_id"])),
                                     vector=vector.tolist(), payload=chunk))
client.upsert(collection, points=points, wait=True)     # 28

query = model.encode("query: " + question, normalize_embeddings=True)   # (384,)
current_filter = models.Filter(must=[
    models.FieldCondition(key="metadata.status", match=models.MatchValue(value="current"))])
hits = client.query_points(collection, query=query.tolist(), limit=3,
                           query_filter=current_filter, with_payload=True).points
rows = [{**hit.payload, "score": float(hit.score)} for hit in hits]
# 1 travel 0 0.8945 / 2 meal 0 0.875 / 3 meal 60 0.8444   ← 4장 NumPy 검색과 같은 순서
```

| Point 칸 | 5-1 (하나씩) | 5-2 (`zip` 반복) | 들어가는 것 |
| --- | --- | --- | --- |
| `id` | `chunk["chunk_id"]` | `chunk["chunk_id"]` | 청크 dict의 `"chunk_id"` 값 → uuid5 |
| `vector` | `vectors[number]` | `vector` (zip이 꺼내 줌) | 같은 번호의 벡터 한 행 |
| `payload` | `chunk` | `chunk` | 청크 dict 통째로 |

- 비슷한 문서를 고르는 기준은 **벡터**, 지금 유효한지는 **metadata**예요. 둘을 `query_points` 한 번에 같이 써요.
- `SavedDenseIndex(chunks, vectors, model)`는 방금 한 생성 → 등록(`__init__`)과 임베딩 → 필터 → 검색(`search`)을 묶은 클래스예요. 결과 순서가 직접 짠 검색과 같아요(`True`).
- 저장된 Point 수(28) ≠ 검색 결과 수(`limit`, 필터에 따라 달라짐).
- 퀴즈(q06): k=1이면 meal:60(합산 금지만)이고, k=3이어야 식비 3만원·숙박 12만원까지 나와요. **문서 하나 찾기 ≠ 모든 항목의 근거 찾기.**

### 3. Metadata Filter와 검색 범위 (5-3강)

```python
index = open_saved_index()
question = "출장 숙박 비용 한도는 8만원인가요?"
index.search(question, k=3, current_only=False)
# travel current 0.9185 / travel-old retired 0.9003 / meal current 0.8716   ← 구버전이 2위
index.search(question, k=3)
# travel current 0.9185 / meal current 0.8716 / meal current 60 0.8596     ← 점수는 그대로, 자격만 걸러짐
```

- 필터는 **가산점이 아니라 후보 자격**이에요. travel 점수는 0.9185 그대로이고, 빠진 travel-old 자리에 다음 후보가 들어와요.
- 질문에 "현행만"이라고 적는 것과 다르게, 필터는 **검색 단계에서** 구버전을 빼서 Context에도 안 들어가요.

| 조합 | 의미 | 예 |
| --- | --- | --- |
| `must` | 모두 만족 (AND) | 현행 **이면서** 출장 → 28개 중 5개(travel 3 + meal 2) |
| `should` | 하나 이상 (OR) | 출장 또는 교육 |
| `must_not` | 제외 | 특정 문서 ID 빼기 |

```python
after_first = models.Filter(must=must + [
    models.FieldCondition(key="start", range=models.Range(gte=60))])        # 숫자는 Range
records, next_offset = index.client.scroll(index.collection, scroll_filter=after_first, limit=100)
# [('meal', 60), ('travel', 60), ('travel', 120)]
index.search(question, k=3, category="해외항공")    # []  ← 규정이 없는 게 아니라 없는 분류로 막아서
```

- `metadata.version`은 `"v2"` 같은 문자열이라 `Range`가 안 돼요(`"v10" < "v2"` 문제). 숫자 순서가 필요하면 숫자 필드를 따로 만들어요.
- 교육비 질문에 출장 필터를 걸면 education이 **검색 전에 빠져서** k를 늘려도 안 나와요. 필터가 좁다고 좋은 게 아니에요.
- 실제 서비스의 접근 권한은 클라이언트가 보낸 category 값만 믿지 말고 서버에서 확인해요.

### 4. 데이터 갱신과 ANN (5-4강)

```python
old = [c for c in chunks if c["document_id"] == "travel"]     # 80/20: (0,80) (60,140) (120,148)
new = chunk_documents([travel], size=100, overlap=20)         # 100/20: (0,100) (80,148)
old_ids = {str(uuid5(NAMESPACE_URL, c["chunk_id"])) for c in old}
new_ids = {str(uuid5(NAMESPACE_URL, c["chunk_id"])) for c in new}
stale_ids = old_ids - new_ids          # 3 2 3  ← 지울 것은 1개가 아니라 3개
# upsert(old) 3 → upsert(new) 5 → delete(stale) 2
```

- 청크 ID에 size·overlap·위치가 들어 있어서 다시 청킹하면 **ID가 모두 바뀌어요.** Upsert는 새 ID를 추가만 해서 이전 3개가 남아요.
- `document_id=travel`로 통째로 지우면 방금 넣은 새 청크까지 사라져요. `old_ids | new_ids`(합집합)를 지워도 마찬가지예요.
- 새 본문은 **다시 임베딩**해요. 이전 벡터를 잘라 쓰면 본문과 벡터가 어긋나요.
- 등록과 삭제는 별도 호출이라 5개인 순간에는 두 청킹 결과가 같이 검색될 수 있어요.

```python
scores = np.array([0.95, 0.93, 0.87, 0.55, 0.20])       # 가상 점수
exact = set(np.argsort(-scores)[:2].tolist())           # 전수 Top-2 {0, 1}
visited = np.array([0, 2, 4])                            # ANN이 탐색한 후보만
approx = set(visited[np.argsort(-scores[visited])[:2]].tolist())   # {0, 2}
len(exact & approx) / 2                                  # 0.5  (visited=[0,1,2,4]면 1.0)
```

| 평가 | 비교 기준 | 확인하는 것 |
| --- | --- | --- |
| ANN Recall@k | **전수 검색**의 Top-k | 근사 탐색의 누락 |
| 정답 문서 Recall@k (4장) | **사람이 정한 정답** | 질문에 필요한 문서 포함 여부 |

## 추가 과제 1 — Qdrant Cloud로 옮기기 (Strict Mode)

### 메모리 vs 클라우드

| | `QdrantClient(":memory:")` | `QdrantClient(url, api_key)` |
| --- | --- | --- |
| 저장 위치 | 내 PC 파이썬 프로그램 안 | Qdrant 서버 |
| 프로그램이 끝나면 | 사라짐 | **남음** |
| 다시 실행 | 그냥 됨 | 같은 Collection이 있으면 `already exists` → 먼저 지워야 함 |
| 키 | 필요 없음 | URL·API 키 (`.env`) |
| 필터 | 그냥 됨 | **Strict Mode** → 필터에 쓰는 필드에 인덱스 필수 |
| 검색만 다시 | 불가 (매번 다시 올려야 함) | 가능 (연결 → 임베딩 → `query_points`) |

### 바꾼 곳

**5-2 `main.py`** (클라우드용, 원래 줄은 주석으로 남김)

```python
import os
# client = QdrantClient(":memory:") #:memory: <이건 약속
client = QdrantClient(url=os.environ["QDRANT_URL"], api_key=os.environ["QDRANT_API_KEY"])
collection = "campus_saved_e5"
client.create_collection(...)                                  # 그대로
client.create_payload_index(                                   # 강사님 공지 코드 그대로
    collection_name=collection,
    field_name="metadata.status",
    field_schema=models.PayloadSchemaType.KEYWORD,
    wait=True,
)
```

**5-3 `saved_index.py`** (5-3 `main.py`는 이 클래스를 쓰기만 해서, 연결을 만드는 클래스 쪽을 고쳐요)

```python
# self.client = QdrantClient(":memory:")
self.client = QdrantClient(url=os.environ["QDRANT_URL"], api_key=os.environ["QDRANT_API_KEY"])
self.client.create_collection(...)                             # 그대로
for field, schema in [                                         # 5-3은 필터를 세 칸에 걸어서 인덱스도 3개
    ("metadata.status", models.PayloadSchemaType.KEYWORD),     # current_only
    ("metadata.category", models.PayloadSchemaType.KEYWORD),   # category="출장"
    ("start", models.PayloadSchemaType.INTEGER),               # Range(gte=60)
]:
    self.client.create_payload_index(collection_name=self.collection, field_name=field,
                                     field_schema=schema, wait=True)
```

- `create_payload_index`는 "이 칸으로 거를 거니 **찾아보기(색인)**를 먼저 만들어 둬"라는 명령이에요. `field_name`은 필터의 `key`와 **글자까지 같아야** 하고(`status` ≠ `metadata.status`), `field_schema`는 그 칸 값의 종류예요(글자 → `KEYWORD`, 정수 → `INTEGER`).
- `models.PayloadSchemaType.KEYWORD`는 `models.Distance.COSINE`과 같은 모양의 **메뉴판**이에요. 라이브러리가 정해 둔 선택지 중 하나를 점으로 골라요. 문자열 `"keyword"`로 써도 같은 뜻이에요.
- 5-2 폴더의 `saved_index.py`는 고치지 않아요. 5-2의 7번은 메모리 모드로 비교하는 부분이라 그대로 둬야 `True`가 나와요.

### 결과 — 저장 장소만 바뀌어서 메모리와 숫자가 같음

```text
5-2 클라우드: 3번 28 / 6번 travel 0 0.8945 · meal 0 0.875 · meal 60 0.8444 / 7번 True
5-3 클라우드: travel-old 0.9003 2위 → current 필터 / 28 → 5 / scroll [('meal',60),('travel',60),('travel',120)] / []
```

데이터가 남아 있어서 다시 올리지 않고 **질문만 바꿔** 검색해 봤어요.

| 질문 | 1위 | 점수 | 본문 |
| --- | --- | --- | --- |
| 재택근무는 주 몇 회까지 가능한가요? | remote 0 | 0.9081 | 재택근무는 **주 2회**까지 운영하며 … |
| 직무 교육비는 얼마까지 지원되나요? | education 0 | 0.9349 | 직무 교육비는 **분기 1회, 1인당 30만원**까지 … |

공식 Quickstart 방식(`cloud_inference=True` + `Document(text="passage: …", model="intfloat/multilingual-e5-small")`, 서버가 임베딩)으로도 같은 28개를 올려 봤는데, 결과가 내 PC E5와 똑같이 `0.8945 · 0.875 · 0.8444`였어요. 확인 후 테스트용 Collection은 지웠어요.

### 클라우드에서 겪은 오류

| 오류 | 원인 | 해결 |
| --- | --- | --- |
| `Index required but not found for "metadata.status"` | Strict Mode — 인덱스 없는 필드로 필터 | `create_payload_index` 추가 |
| `Collection ... already exists` | 클라우드는 데이터가 남음 | 다시 실행 전 Collection 삭제 (`client.delete_collection`) |
| `KeyError: 'QDRANT_URL'` | `.env`를 안 읽고 실행 | `uv run --env-file ..\..\.env main.py` |
| `No environment file found at 3일차/rag_day3/...` | `UV_ENV_FILE`은 공백으로 파일을 나눠서 `RAG 3일차`에서 잘림 | 상대 경로 `$env:UV_ENV_FILE = "../../.env"` 후 `uv run main.py` |
| 5-2 7번 `SyntaxError` | 5-2 폴더의 `saved_index.py`를 고치다 만 상태 | 원본으로 되돌림 (클라우드 수정은 5-3 폴더에서) |

## 추가 과제 2 — FAISS로 같은 검색

`uv add faiss-cpu`로 추가하고, 5-2 `main.py`를 `faiss_test.py`로 복사해서 저장소 부분만 FAISS로 바꿨어요. 파일 이름을 `faiss.py`로 하면 `import faiss`가 라이브러리 대신 자기 자신을 불러와서 안 돼요.

```python
index = faiss.IndexFlatIP(vectors.shape[1])          # 정확 검색: 384차원, 내적(정규화 벡터라 = 코사인)
# index = faiss.IndexHNSWFlat(vectors.shape[1], 32, faiss.METRIC_INNER_PRODUCT)   # ANN(HNSW): 이웃 32개, 기본은 L2라 내적 지정
index.add(vectors.astype("float32"))                  # (28, 384)를 통째로 — id·payload 없음, 넣은 순서 0~27이 번호
print(index.ntotal)                                   # 28

scores, ids = index.search(query.reshape(1, -1).astype("float32"), 6)   # 질문 1개 → (1, 384), 필터로 빠질 걸 대비해 넉넉히
rows = []
for score, i in zip(scores[0], ids[0]):
    chunk = chunks[i]                                 # payload가 없어서 번호로 원문 찾기 (4장 방식)
    if chunk["metadata"]["status"] != "current":      # 현행 필터를 검색 뒤에 직접
        continue
    rows.append({**chunk, "score": float(score)})
rows = rows[:3]
# 1 travel 0 0.8945 / 2 meal 0 0.875 / 3 meal 60 0.8444   ← Qdrant와 같음
```

- `IndexHNSWFlat`도 같은 결과였어요. 벡터가 28개뿐이라 ANN이 놓친 게 없었어요(ANN Recall@3 = 1.0). 데이터가 많아지면 `index.hnsw.efSearch`(탐색 범위)를 키울수록 정확해지고 느려져요.

### 5-2 세 가지 버전 비교 (print\_section 단계별)

| 단계 | 메모리 `main.py` | 클라우드 `main.py` | `faiss_test.py` |
| --- | --- | --- | --- |
| 2번 저장소 | `QdrantClient(":memory:")` + `create_collection(384, COSINE)` | `QdrantClient(url, api_key)` + 같은 `create_collection` + `create_payload_index` | `faiss.IndexFlatIP(384)` (또는 `IndexHNSWFlat`) |
| 개수 | `client.count(col).count` | 같음 | `index.ntotal` |
| 3번 넣기 | for문 `PointStruct(id, vector.tolist(), payload)` + `upsert` | 같음 | `index.add(vectors)` 한 번 (id·payload 없음) |
| 4번 ID 조회 | `retrieve(...)[0].payload` | 같음 | 없음 (`chunks[i]`) |
| 5번 질문 임베딩 | `model.encode("query: " + q, normalize_embeddings=True)` | 같음 | 같음 |
| 6번 검색 | `query_points(..., query_filter=…).points` → `{**hit.payload, "score"}` | 같음 | `index.search(…, 6)` → `(scores, ids)` → `chunks[i]`, 필터는 직접, `[:3]` |
| 키 | 없음 | `.env` (URL·API 키) | 없음 |
| 끝나면 | 사라짐 | 남음 | 사라짐 |
| 결과 | 0.8945 · 0.875 · 0.8444 | 같음 | 같음 |

**Qdrant vs FAISS 한 줄:** Qdrant는 **Point(벡터 + payload)를 저장하고 필터를 검색 안에서** 처리하는 DB이고, FAISS는 **벡터만** 빠르게 비교하는 라이브러리라 원문 연결과 필터를 내가 직접 해야 해요.

## 질문과 새로 알게 된 점

### 글 → Qdrant Point까지 (오늘 질문을 한 줄로)

```text
① 문서 → ② 청크 ("passage: " 붙임)
→ ③ 토크나이저: input_ids + attention_mask(진짜 1 / 패딩 0)      ← mask 생성
→ ④ Lookup Table: (토큰 수, 384)  토큰마다 벡터, 문맥 없음
→ ⑤ Self-Attention × 12층: (토큰 수, 384)  개수 그대로, 문맥 반영   ← mask 1번째 사용
→ ⑥ 풀링(axis=0 평균): (384,)  청크 하나 = 벡터 하나              ← mask 2번째 사용
→ ⑦ 정규화: 길이 1  ★ vectors.npy의 한 행
→ ⑧ Point(id, vector=⑦, payload=청크)
```

- Point의 `vector` 384개는 **④~⑦을 다 거친 마지막 벡터**예요. 중간 벡터는 모델 안에서만 쓰이고 사라져요. 코드로는 `model.encode(..., normalize_embeddings=True)` 한 줄 안에서 전부 일어나요.
- **풀링 `axis=0`**: 위에서 아래로(세로로), 같은 칸끼리 토큰들을 평균내요. 384칸은 그대로이고 토큰 수만 1로 줄어요.
- **mask가 쓰이는 곳**: 여러 청크를 한 번에 처리하려고 짧은 쪽에 패딩을 채우면서 생기고 → Attention에서 패딩 자리 점수를 −∞로 바꿔 softmax 비중을 0으로 만들고(`e^(−∞) = 0`) → 풀링에서 평균에서 빼요. 벡터 1개가 된 뒤에는 필요 없어서 버려요.
- **softmax는 Self-Attention 안에** 있어요: `softmax(QKᵀ/√d + mask)·V`. 점수를 "몇 %씩 참고할지"로 바꿔요.
- **정규화하는 이유**: 코사인 = 내적 ÷ (두 벡터 길이의 곱)인데, 길이를 1로 맞춰 두면 분모가 1 × 1 = 1이라 **내적만으로 코사인**이 나와요. 그래서 Collection도 `COSINE`, FAISS도 `IndexFlatIP`(내적)를 써요.

### 클래스와 객체

- **클래스 = 틀(설계도), 객체 = 그 틀로 만든 실제 값.** 사실 파이썬의 모든 값(list, str, `SentenceTransformer`, `QdrantClient`)이 객체예요.
- **속성** = 객체가 들고 있는 값 → `obj.이름` (괄호 없음). **메서드** = 시키는 일 → `obj.이름()`.
- `index = open_saved_index()`를 따라가면: 청크·벡터·모델을 읽고 → `SavedDenseIndex(chunks, load_vectors(chunks), load_model())` → 세 값이 순서대로 `__init__(self, chunks, vectors, model)`에 들어가고 → `self`가 새 객체가 되어 `index`로 돌아와요.
- `index`의 속성: `chunks`(리스트), `model`(SentenceTransformer), `collection`(문자열 이름표 `"campus_saved_e5"`), `client`(QdrantClient 객체). **`vectors`는 `self`에 저장하지 않아요.** `zip`으로 Point를 만들어 Upsert하는 데만 쓰고, 그 뒤엔 Qdrant 안에 있어요. `model`은 `search`에서 질문을 임베딩해야 해서 저장해요.
- `index.client.count(index.collection)` = client 속성(객체)을 꺼내서 그 메서드를 부르고 Collection 이름을 넘기는 것. `index.collection.count`는 문자열의 count라 틀려요. Qdrant 작업은 항상 `client.메서드(이름, …)` 모양이에요.
- 무엇인지 모르겠으면 `print(type(x))`, VS Code에서 `.` 뒤 자동완성, F12로 정의 보기.

### 꺼내는 규칙

| 모양 | 꺼내는 법 | 예 |
| --- | --- | --- |
| 리스트 / NumPy 배열 | `[번호]` | `chunks[7]`, `vectors[7]`, `points[0]` |
| dict | `["키"]` | `chunk["chunk_id"]`, `payload["metadata"]["status"]` |
| 객체 | `.이름` | `hit.score`, `point.id`, `index.client` |

- `chunks[i]`와 `vectors[i]`는 **같은 인덱스**로 꺼내야 같은 청크예요. `vectors[i]`가 `chunks[i]` 본문으로 만든 벡터라서요.
- `vectors`는 `(28, 384)`(28개 전부), `vectors[7]`은 `(384,)`(하나). `vectors.shape[1]`은 열 수 384.
- `metadata.status`는 청크 dict의 `{"metadata": {"status": "current", …}}`에서 왔고, payload로 그대로 들어가서 Qdrant에서는 점으로 이어 부르는 거예요(2장에서 붙인 현행/구버전 표시).

### `.points`는 왜 붙이나

```python
hits = client.query_points(...).points       # 직접 단 주석: #<<points?이건왜하지
```

- `query_points`는 리스트가 아니라 **결과 상자(`QueryResponse` 객체)**를 돌려줘요. 그 안의 `points` 칸에 실제 검색 결과 리스트가 있어서 `.points`로 꺼내요.
- 상자로 주는 이유: 서버가 JSON을 `{"points": [...]}`처럼 이름 붙은 칸으로 보내고, 파이썬 클라이언트가 그 모양 그대로 객체로 바꿔 줘요. 나중에 정보가 늘어도 칸만 추가하면 돼요.
- `client.count(col).count`도 같은 모양이에요: `CountResult(count=28)` → `.count`. 5-3에서 `print(type(index.client.count(index.collection)))`로 찍어 보니 `<class '…CountResult'>`였어요.
- `points`·`count`는 qdrant-client가 미리 정해 둔 이름이라 다른 이름을 쓰면 `AttributeError`가 나요.
- 리스트 안의 한 칸은 `ScoredPoint(id, score, payload, vector)` 객체예요. 넣을 땐 `PointStruct`, 받을 땐 **score가 붙은** `ScoredPoint`예요.

### 그 밖에

- **`.tolist()`**: Qdrant는 서버와 JSON으로 주고받는데 NumPy 배열은 JSON으로 못 바꿔서, 파이썬 기본 리스트로 바꿔 보내요(`vector=…tolist()`, `query=…tolist()`). FAISS는 반대로 NumPy `float32` 배열을 받아요.
- **`ids=[…]`, `points=[…]`**: 여러 개를 한 번에 다룰 수 있게 만든 메서드라 이름이 복수이고 리스트로 넣어요. `retrieve` 결과도 리스트라 `[0]`으로 꺼내요.
- **`collection_name=collection`**: 왼쪽은 라이브러리가 정한 인자 이름, 오른쪽은 내가 만든 변수(`"campus_saved_e5"`). 교안 `create_collection(collection, …)`처럼 이름표 없이 첫 자리에 넣어도 같아요.
- **`retrieve` 결과에 vector가 없는 이유**: 바뀐 게 아니라 `with_payload=True`만 요청해서예요. `with_vectors=True`를 주면 384개가 와요.
- **`create_collection`에 넣는 것**: 이름 + `VectorParams(size, distance)`. `size`는 모델 차원(E5 small 384, base 768)이라 모델을 바꾸면 Collection을 새로 만들어야 해요.
- **`cloud_inference=True`**: 임베딩을 Qdrant 서버가 대신 하게 하는 스위치. `Document(text, model)`는 "이 글을 이 모델로 임베딩해 줘"라는 요청서라, 이게 켜져 있어야 써요.
- qdrant-client에서 쓰는 이름들(`models.~` 클래스와 메뉴판, `client.~` 메서드, 결과 칸)과 내가 정하는 변수 이름을 나눠 따로 정리해 뒀어요.

### 다음에 다시 볼 것

- 이 벡터를 **어떻게 학습시켰나** — 대조학습(positive/negative), InfoNCE loss, 역전파로 Lookup Table까지 함께 수정
- **밀집 벡터(E5) vs 희소 벡터(BM25)** — 7장 Hybrid Search와 연결

## 실습 코드에서 직접 바꾼 점

원본 키트(`rag_day3` ZIP)와 비교한 내용입니다.

| 파일 | 바꾼 점 / 추가한 주석 |
| --- | --- |
| `pyproject.toml` | `printsection>=0.2.0`, `faiss-cpu>=1.15.1` 추가 (`uv add`) |
| 네 강의 `main.py` | `print_section` 구역 출력 추가 |
| 5-1 `q_easy`·`q_hard` | 교육비 Point: `id=str(uuid5(NAMESPACE_URL, education_chunk["chunk_id"]))`, `vector=vectors[education_no].tolist()` |
| 5-2 `main.py` | 클라우드 연결 + `metadata.status` 인덱스 (위 추가 과제 1). 주석: `#:memory: <이건 약속`, `# 쓰는 모델이 접두사를 붙여서 학습했기 때문에 유사도에 있어 효과가높음.`, `# 필터. 반드시 이 조건 만족해야함.`, `#스테이터스가 current인것만 가져오는 필터.`, `#궁극적으로 RAG에서 해야하는 매서드.`, `.points #<<points?이건왜하지`, `# saved_index.py에 지금까지 한것 모듈화.` |
| 5-2 `q_hard` | `query_points(collection, query=query2.tolist(), limit=k, query_filter=current_filter, with_payload=True).points` → `results[k] = [(document_id, start) …]` |
| 5-2 `faiss_test.py` (새 파일) | 추가 과제 2 |
| 5-3 `saved_index.py` | 클라우드 연결 + 인덱스 3개 (위 추가 과제 1) |
| 5-3 `main.py` | `print(type(index.client.count(index.collection)))` 추가 — count 결과가 객체인지 확인 (처음엔 `print(type)(…)`로 괄호 위치가 틀려 `TypeError`) |
| 5-4 `main.py` | `chunks = load_chunks() #기존 size 80 overlap 20임`, ANN 계산 앞에 `print_section("approx")` |
| 5-4 `q_easy`·`q_hard` | `to_remove = old_ids - new_ids` |

## 확인 문제

강의 내용을 바탕으로 직접 만든 복습 문제입니다. 객관식 4문제, 서술형 2문제이고 각 문제 바로 아래에 정답이 있습니다.

### 5-Q1. Upsert 두 번 (5-1)

같은 travel Point를 `client.upsert`로 두 번 넣었더니 `count`가 1이었다. 이유는?

① Qdrant가 본문이 같은 Point를 자동으로 찾아 합쳐서  
② `uuid5`로 만든 Point ID가 같아서, 두 번째 호출이 같은 Point를 갱신해서  
③ `wait=True` 때문에 두 번째 호출이 무시돼서  
④ Collection의 `size`가 1이라서

<details>
<summary>정답 보기</summary>

**②** — Upsert는 **ID로만** 대상을 구분해요. 본문이 같아도 ID가 다르면 2개가 돼요.

</details>

### 5-Q2. `create_collection`의 size (5-1·5-2)

`VectorParams(size=…)`에 넣어야 하는 값은?

① 384 — 각 Point 벡터의 길이(차원)  
② 28 — 저장할 Point 개수  
③ 512 — 모델의 입력 토큰 한도  
④ 12 — 문서 개수

<details>
<summary>정답 보기</summary>

**①** — `vectors.shape[1]`. Point 개수는 넣는 만큼 늘어나고, 512는 입력 한도라 벡터 길이와 무관해요.

</details>

### 5-Q3. current 필터의 효과 (5-3)

"8만원인가요?"에 current 필터를 걸었더니 travel-old가 빠지고 travel 점수는 0.9185 그대로였다. 옳은 설명은?

① 필터가 current 문서에 가산점을 줘서 순위가 바뀌었다  
② 질문에 "현행만"을 붙인 것과 같은 효과다  
③ 필터를 걸면 k를 늘려도 결과가 항상 3개 이하로 고정된다  
④ 필터는 점수를 바꾸지 않고, 검색 후보가 될 수 있는 범위만 정한다

<details>
<summary>정답 보기</summary>

**④** — 필터는 포함 여부를 정해요. 검색 단계에서 빠지니 Context에도 안 들어가요.

</details>

### 5-Q4. 다시 청킹한 뒤 지울 Point (5-4)

travel을 80/20(3청크)에서 100/20(2청크)로 다시 청킹해 새 Point를 upsert했다. 지워야 할 Point는?

① 마지막 청크 하나 — 3개에서 2개로 줄었으니까  
② `document_id`가 travel인 Point 전부  
③ `old_ids - new_ids` — 이번에는 이전 3개 전부  
④ 지울 필요 없다 — Upsert가 이전 Point를 자동으로 바꾼다

<details>
<summary>정답 보기</summary>

**③** — 청크 ID에 size·overlap·위치가 들어 있어 새 ID가 이전과 모두 달라요. ②는 새 청크까지 지우고, ④는 Upsert가 새 ID를 추가만 해서 틀려요.

</details>

### 5-Q5. 서술형 — 클라우드에서만 난 오류 (추가 과제 1)

메모리 모드에선 잘 되던 current 필터 검색이 Qdrant Cloud에서는 `Index required but not found for "metadata.status"`로 막혔다. 왜 그런지, 어떻게 고쳤는지 쓰세요.

<details>
<summary>예시 답안</summary>

`:memory:`는 파이썬 안의 임시 저장소라 서버 제한을 검사하지 않고 필터 때 그냥 전부 훑어요. Qdrant Cloud는 실제 서버라 Strict Mode가 적용돼서, 인덱스가 없는 필드로 필터하면 서버 부담을 막으려고 거부해요. 그래서 `create_payload_index(field_name="metadata.status", field_schema=KEYWORD)`로 필터와 **같은 칸**에 찾아보기를 먼저 만들었어요. 5-3은 status·category·start 세 칸으로 거르니 인덱스도 세 개 만들었어요.

</details>

### 5-Q6. 서술형 — Qdrant vs FAISS (추가 과제 2)

같은 벡터로 Qdrant와 FAISS 모두 `0.8945 · 0.875 · 0.8444`가 나왔다. 그런데 FAISS 코드에서는 원문 연결과 현행 필터를 직접 해야 했다. 이유를 쓰세요.

<details>
<summary>예시 답안</summary>

FAISS는 **벡터만** 저장하고 비교하는 라이브러리라 payload가 없어요. 검색 결과로 점수와 **넣은 순서 번호**만 돌려줘서, 4장처럼 `chunks[i]`로 원문을 찾아야 해요. 필터 기능도 없어서 넉넉히(6개) 검색한 뒤 `status != "current"`인 것을 직접 빼고 앞에서 3개를 잘랐어요. Qdrant는 Point에 payload를 같이 저장하고 `query_filter`로 **검색 안에서** 걸러 줘요. 점수가 같은 건 같은 E5 벡터를 같은 방식(정규화 + 내적 = 코사인)으로 비교했기 때문이에요.

</details>
