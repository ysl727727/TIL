# 9장. 고급 RAG — Parent-Child · Agentic RAG · GraphRAG · Multimodal(ColPali)

> 2026-10-27 학습 기록. RAG 5일차 오후 수업이자 RAG 과목의 마지막 장입니다. 8장 평가에서 찾은 빈틈을 하나씩 메웠습니다. 잘린 조건은 Parent로 넓혀 읽고(9-1), 표현 때문에 못 찾으면 다시 검색하되 멈출 조건을 두고(9-2), 여러 규정에 흩어진 관계는 그래프로 따라가고(9-3), 표·이미지 속 숫자는 값·단위·출처를 함께 다루고 페이지 이미지로 검색했습니다(9-4).

## 학습 목표

- "작게 찾고 넓게 읽기"(Child로 검색, Parent로 답변)와 Context 압축을 구현하고, 압축할 때 **예외 조건이 먼저 사라지는** 위험을 확인한다.
- 재검색 루프의 세 가지 종료 이유(`candidates_ready` · `repeated_query` · `search_limit`)를 구분하고, 모델이 다음 행동을 고를 때 필요한 검사(인용 확인)를 설명한다.
- 관계를 노드·간선으로 저장하고 간선을 따라 "영수증을 내는 규정 → 각 규정의 승인자"를 찾는다. GraphRAG Local · Global · DRIFT의 차이를 안다.
- 원문 값을 단위·출처와 함께 추출하고, 계산과 승인 판단을 분리한다. ColPali의 MaxSim 점수를 손으로 계산한다.

## 실습 파일

| 강 | 주제 | 실습 상태 |
| --- | --- | --- |
| 9-1 | Parent-Child와 Context Compression — 80자 Child → 148자 Parent, 문장 추출, 예산 70·140 | ✅ `main.py` · q\_hard 통과 · ⏳ `--generate`·`compare_contexts.py` |
| 9-2 | Corrective / Agentic RAG — `search_loop` 세 종료 상태, (선택) `agent.py`의 `route` | 🧪 `main.py` 실행 · `agent.py`는 `KeyError: 'OLLAMA_MODEL'` → 설정법 확인 · ⏳ q\_hard |
| 9-3 | GraphRAG — NetworkX 노드 10·간선 8, 영수증 → 규정 → 승인자, GraphRAG 입력 10개 | 🧪 `main.py` 실행 · **선택 실습 GraphRAG 색인·질의 실행** · ⏳ q\_hard |
| 9-4 | Multimodal RAG와 ColPali — 금액 추출, 2박 계산, MaxSim 모형, 페이지 PNG | ⏳ 실행 기록 없음 (ColPali 모델·패키지만 미리 받아 둠) |

`rag_day5` 키트로 진행했습니다. 기본 실행(`main.py`)은 모델 없이 돌고, 강마다 선택 실습이 따로 있습니다(9-1·9-2 Ollama, 9-3 GraphRAG API, 9-4 ColPali). 키트 코드는 올리지 않고 직접 바꾸거나 추가한 부분만 기록합니다.

## 전체 흐름

### 한 문장

**8장에서 "어디가 비었는지" 찾았다면, 9장은 빈틈의 종류에 맞는 확장을 고르는 시간입니다.**

```text
관찰한 빈틈                  확장                     오늘 확인한 것
문장 중간에 조건이 끊김   →  Parent · 인접 구간 (9-1)  →  80자 → 148자, 예산 70이면 승인 조건 누락
질문 표현 때문에 못 찾음  →  재검색 · 질의 변형 (9-2)  →  q10 [] → education@60, 반복 · 제한 종료
여러 규정의 관계가 필요   →  그래프 (9-3)             →  영수증 ← 3개 규정 → 승인자 · 조건
표 · 이미지가 답에 중요   →  구조 추출 · 시각 검색 (9-4) → 값 + 단위 + 출처, MaxSim, PNG
```

**확장을 더하기 전에 "어느 단계에서 정보가 처음 사라졌나"부터 찾아요.**

### RAG 과목 마무리: q10 하나를 끝까지 따라가기

| 단계 | 무슨 일이 있었나 |
| --- | --- |
| 7-1 BM25 | 토큰 불일치로 빈 목록 (자료가 없는 게 아님) |
| 7-4 · 9-2 재검색 | "수강 완료 후 제출" 표현으로 education@60 확보 |
| 8-4 Hybrid | 문서 Recall 1.0 — 하지만 증빙 청크가 들어왔는지는 따로 확인 |
| 9-1 Parent | 원문 전체로 수료증과 영수증 문장까지 Context에 |

## 핵심 이론

### 1. Parent-Child와 Context Compression (9-1강)

**문제:** 80자 Child `travel@0`은 `…한도 초과 숙박은 예약 전에 담당 임원의 서면 `에서 끊겨요. "승인을 받아야 합니다"가 빠져요.

```text
Child  travel@0 (0~80)   … 한도 초과 숙박은 예약 전에 담당 임원의 서면
Parent travel  (0~148)   … 서면 승인을 받아야 합니다. 승인 없이 초과 지출한 금액은 자동 정산되지 않습니다. …
```

**해결 1 — Parent 확장:** 검색은 작은 Child로 위치를 찾고, 답변에는 그 Child가 속한 원문(Parent)을 넘겨요.

```python
current = [c for c in chunks if c["metadata"]["status"] == "current"]           # 현행 청크만
parents = {d["document_id"]: d for d in docs if d["metadata"]["status"] == "current"}
hits = bm25(question, current, k=3)
child = next(c for c in hits if c["document_id"] == "travel")
parent = parents[child["document_id"]]        # 같은 document_id로 원문 찾기
```

- 현행 규정만 대상으로 해서 구버전 Parent 본문이 섞이지 않게 해요.
- 같은 문서의 Child가 여러 개 검색돼도 Parent는 **한 번만** 넣어요(`seen` 집합). 새 행은 `{**c, …}`로 Child를 복사한 뒤 `chunk_id`(`travel:parent:버전`), `text`(원문 전체), `start`/`end`(0 ~ 원문 길이), `retrieved_child_ids`(어떤 Child 때문에 확장했는지 추적용)를 덮어써요.

```text
STEP1 child 0 80 80
parent 148 국내 출장 숙박 비용 한도는 1박당 12만원입니다. … 이 규정은 교통비와 식비를 정하지 않습니다.
STEP2 검색청크 3 부모본문 2          ← 청크 3개 중 2개가 같은 문서
```

**해결 2 — Context 압축:** Parent를 계속 늘리면 Context도 길어지니 질문에 필요한 문장만 남겨요.

```python
spans = [(m.start(), m.end(), m.group().strip())
         for m in re.finditer(r"[^.]+\.", parent["content"])]   # 마침표까지 = 문장 하나
terms = ["한도", "초과", "승인", "영수증"]
selected = [s for s in spans if any(t in s[2] for t in terms)]   # 네 단어 중 하나라도
```

| 위치 | 남은 정보 |
| --- | --- |
| 0 ~ 28 | 1박당 12만원 |
| 28 ~ 53 | 숙박 영수증 첨부 |
| 53 ~ 92 | 초과는 예약 전 담당 임원 서면 승인 |
| 92 ~ 123 | 승인 없는 초과는 자동 정산 안 됨 |

마지막 문장(교통비와 식비를 정하지 않음)은 네 단어가 없어서 빠져요. 이 정규식은 교육용 단순 규칙이라 마침표 없는 문장이나 약어는 처리하지 못해요.

**예산 70자 vs 140자** (6-1 `pack_context`와 같은 구조, `+1`은 문장 사이 공백)

```text
budget 70  남은문장 2 chars 54   1박당 12만원 · 숙박 영수증            → 초과 승인 조건 누락
budget 140 남은문장 4 chars 124  + 예약 전 서면 승인 · 승인 없는 초과 불가
```

- 예산 70에서는 3번째 문장(39자)을 넣으면 94자가 돼서 탈락해요.
- `--generate` 질문 "13만원짜리 숙박도 정산할 수 있나요?"는 한도를 넘는 경우라 **바로 그 예외 조건**이 있어야 답할 수 있어요. 교안 기록(gemma3 1회)에서 짧은 추출문은 "정산할 수 없습니다"로, Parent 전체는 "예약 전에 담당 임원의 서면 승인이 필요합니다"로 답했어요. 두 답 모두 출처는 `S1`인데 **같은 ID가 가리키는 본문 범위가 달라요.**
- 기본 실행의 추출 문장은 LLM 요약이 아니라 원문을 그대로 잘라 낸 거예요.

### 2. Corrective / Agentic RAG (9-2강)

| 접근 | 추가하는 판단 | 이 수업의 범위 |
| --- | --- | --- |
| 기본 RAG | 정해진 검색 후 생성 | 6장의 한 번 검색 흐름 |
| Agentic RAG | 다음 질의 · 도구 · 종료 선택 | 최대 두 번의 사내 자료 검색 |
| CRAG | 검색 결과 품질 평가 후 보정 | 근거 검토 후 재검색하는 발상 |
| Self-RAG | 검색 필요성 · 생성 내용을 모델이 비평 | 학습된 비평 토큰 — 연구 구조 소개 |

참고 논문: CRAG (arXiv 2401.15884), Self-RAG (arXiv 2310.11511)

**`search_loop` (main.py) — 사람이 정한 검색문과 규칙으로 재검색**

```python
def search_loop(queries, topic, max_searches=2):
    trace, seen = [], set()
    for query in queries[:max_searches]:          # ① 최대 횟수만큼만
        if query in seen:                         # ② 같은 검색문 반복 → 중단
            return [], trace, "repeated_query"
        seen.add(query)
        candidates = bm25(query, current, k=3)
        on_topic = [c for c in candidates if topic in c["metadata"]["title"]]   # ③ 제목 필터
        trace.append({...})
        if on_topic:
            return on_topic, trace, "candidates_ready"
    return [], trace, "search_limit"
```

```text
STEP1 [{"query": "교육비 정산 증빙은 무엇인가요?", "hits": [], "on_topic": 0},
       {"query": "교육비 지원 수강 완료 후 제출합니다",
        "hits": [["education", 60], ["education", 0], ["retention", 120]], "on_topic": 2}] candidates_ready
STEP2 장에게 제출해 승인을 받아야 합니다. 수강 완료 후 수료증과 영수증을 제출합니다. …
STEP3 repeated_query      ← [question, question]
STEP4 search_limit        ← max_searches=1이라 변형까지 못 감
```

- 반환값은 `(찾은 청크, 기록, 종료 이유)` 튜플이라 STEP3·4는 `[2]`로 종료 이유만 꺼내요.
- 7-4는 여러 표현을 **한꺼번에** 검색했고, 9-2는 결과를 **보고 나서** 다음 검색을 할지 정해요.
- `candidates_ready`는 "검토할 후보가 생김"이지 정답 확정이 아니에요. education@0은 제목 검사를 통과하지만 증빙 문장이 없어요 → 잘못된 통과 조건의 예.

**`route` (agent.py, 선택) — 다음 행동을 LLM이 고름**

| 필드 | 사용 방법 |
| --- | --- |
| `action` | `answer` / `rewrite` / `abstain` (JSON Schema enum) |
| `reason` | 판단 이유 |
| `next_query` | rewrite일 때 새 검색 문장 |
| `evidence_quotes` | answer일 때 원문 인용 |

- `route(query, rows)`는 검색 결과를 `build_context`로 묶어서 **원질문 + 지금 검색문 + Context**를 함께 Ollama에 보내요. 검색문이 바뀌어도 원래 무엇을 묻는지 잊지 않게 하려는 거예요.
- 아래 루프는 `search_loop`와 뼈대가 같아요(`range(2)`, `seen`). answer를 골라도 **인용문이 Context에 없으면 중단**(6장 `quote_not_found`와 같은 생각), abstain이나 빈 `next_query`도 중단, 통과했을 때만 `generate_ollama(question, …)`로 **원질문**에 대한 최종 답을 따로 만들어요 → Ollama 호출이 최소 2번(판단 + 답변).
- 교안 기록(gemma3 1회): 첫 검색이 빈 목록인데 answer를 골랐고, 인용 검사가 막았어요. → 모델이 다음 행동을 고르면 검사가 더 필요해요.

### 3. GraphRAG (9-3강)

**문제:** "영수증을 내는 규정과 각 규정의 승인자는?"처럼 **여러 문서를 이어 봐야 하는** 질문. 일반 RAG는 비슷한 조각을 찾을 뿐이라 이런 질문에 약해요.

**해결:** 원문에서 확인한 관계를 `(규정, 대상, 관계, 조건)`으로 적고 방향 그래프에 넣어요.

```text
   규정(did)                         대상(entity)
  [travel]    ───── 제출 ─────▶   [영수증] ◀── STEP2 시작점
     ╲······ 승인자 ·······▶  [담당 임원]
  [education] ───── 제출 ─────▶   [영수증]
              ───── 제출 ─────▶   [수료증]
              ······ 승인자 ······▶ [팀장]
  [meal]      ───── 제출 ─────▶   [영수증]
  [leave]     ······ 승인자 ······▶ [팀장]
  [vpn]       ······ 승인자 ······▶ [관리자]
```

```python
graph = nx.DiGraph()
for did, ent, rel, cond in relations:                 # 튜플 4칸을 나눠 담기
    graph.add_edge(did, ent, relation=rel, condition=cond,
                   source_document_id=did, source_url=…)   # A → B 화살표 + 메모
# STEP1 10 8
```

- 화살표는 줄 수와 같아서 8개, 점은 겹치는 이름을 한 번만 세서 10개(규정 5 + 대상 5)예요. 하나도 안 겹쳤다면 16개였을 거예요. 줄 수만 보고는 짐작하기 어려워서 `number_of_nodes()`로 확인해요.

```text
STEP2 영수증 제출 규정 ['education', 'meal', 'travel']        ← sorted(graph.predecessors("영수증"))
education [('팀장', '수강 전')]
meal 승인자 규정 없음
travel [('담당 임원', '한도 초과 숙박 예약 전 서면 승인')]
STEP3 원문확인 국내 출장 숙박 비용 한도는 1박당 12만원입니다. …
STEP4 GraphRAG 입력 10 개
```

- STEP3에서 그래프 내용이 원문에 진짜 있는지 사람이 다시 확인해요.
- 문서 연결 수가 많아도 답이 정확하다는 뜻은 아니에요. "한도 초과면 승인 필요"를 "한도 안이면 승인 불필요"로 뒤집지 않는지 봐요.

**Microsoft GraphRAG: Local · Global · DRIFT**

| 방식 | 시작점과 사용하는 자료 | 질문 예 |
| --- | --- | --- |
| Local | 질문과 관련된 개체, 주변 관계와 원문 | 교육비 신청과 증빙에는 어떤 절차가 연결되나 |
| Global | 여러 커뮤니티 보고서를 종합 | 전체 규정에서 반복되는 비용 정산 원칙은 |
| DRIFT | 관련 보고서로 시작 → 후속 질문 → Local 탐색 | 전체 흐름을 본 뒤 구체 절차를 더 확인 |

**선택 실습 — 직접 실행했어요.** `check_setup.py`(로컬 E5 준비 확인, API 호출 0) → `configure_api.py`(키 입력) → `graph_local.py index` → 질의.

```text
check_setup   document_shape [10, 384] · query_top3 ['travel', 'meal', 'education'] · generation_requests 0
색인 결과     문서 10 · 엔티티 67 · 관계 57 · 커뮤니티 17 · 커뮤니티 보고서 17 · all_documents_represented: true
              (색인 약 90초, LLM 요청 31회)
질의          Local 검색 로그에 "Reached token limit - reverting to previous context state" 경고
```

- 교안 기록은 엔티티 69 · 관계 62였는데 내 색인은 67 · 57이었어요. **관계를 LLM이 자동으로 뽑아서 실행마다 달라져요.** 사람이 원문을 보고 적은 기본 실습의 `relations` 8줄과 다른 점이에요.
- 처음엔 `DLL load failed while importing _epoch` 오류가 났어요(아래 질문 정리 참고). 그 뒤에 색인과 질의까지 실행됐어요.

### 4. Multimodal RAG와 ColPali (9-4강)

**같은 "12만원"도 어느 행의 값인지 알아야 해요.**

| 원문 | 한도 | 적용 단위 | 증빙 |
| --- | --- | --- | --- |
| travel | 12만원 | 국내 출장, 1박당 | 숙박 영수증 |
| education | 30만원 | 분기 1회, 1인당 | 수강 완료 후 수료증, 영수증 |

```python
match = re.search(r"(\d+)만원", by_id[did]["content"])     # 처음 나온 "숫자+만원"
rows.append({"document_id": did, "limit_won": int(match.group(1)) * 10000, "source_url": …})
# [('travel', 120000), ('education', 300000)]
```

**계산은 계산, 승인 판단은 따로**

- `120000 × 2박 = 240,000원` (숙박 기본 한도, 산술)
- ✗ `240000 + 300000 = 540,000원` — 다른 규정 예산을 합칠 근거가 없어요(8-1의 "출장비 15만원" 오답과 같은 실수).
- 숫자를 계산해도 원문 조건(영수증 첨부, 12만원 초과면 예약 전 서면 승인)은 따로 확인해요.

**ColPali의 MaxSim:** 페이지를 이미지 그대로 여러 조각 벡터로 바꾸고, 질문 벡터마다 가장 잘 맞는 페이지 조각을 하나씩 골라 더해요.

```text
score(Q, D) = Σ_i  max_j  q_iᵀ d_j
```

| 페이지 | q1 = [1, 0]의 최대 | q2 = [0, 1]의 최대 | 합 |
| --- | --- | --- | --- |
| A `[1,0], [0,1]` | 1.0 | 1.0 | **2.0** |
| B `[0.71, 0.71]` | 0.7071 | 0.7071 | 1.4142 |

```python
def maxsim(query_vectors, page_vectors):
    return sum(max(sum(a*b for a, b in zip(q, p)) for p in page_vectors) for q in query_vectors)
# STEP3 MaxSim 수치모형 {'A': 2.0, 'B': 1.4142}
```

- 4장 mean pooling은 토큰 벡터를 **평균 하나로** 뭉갰다면, MaxSim은 **여러 벡터를 그대로** 두고 비교해요.
- 위 2차원 벡터는 계산 원리를 보기 위한 가상 값이고 ColPali 출력이 아니에요(`MODEL_NOT_RUN`).
- STEP4는 Pillow로 같은 원문을 페이지 PNG(`visual_pages/travel.png`, `education.png`)로 그려 선택 실습 입력을 만들어요. OCR이나 검색 모델 추론이 아니에요.
- 선택 실습 `visual_search.py`는 ColPali(PaliGemma 3B 기반)로 진짜 페이지 검색을 해요. `scores[0].argmax()`는 최고 점수 페이지의 **인덱스**예요(확률 아님).

## 질문과 새로 알게 된 점

### 9-1 q\_hard: 승인 조건 문장만 고르기

```python
chosen = [(start, end, text) for start, end, text in selected if "승인" in text]
for row in chosen:
    print(row)
# (53, 92, '한도 초과 숙박은 예약 전에 담당 임원의 서면 승인을 받아야 합니다.')
# (92, 123, '승인 없이 초과 지출한 금액은 자동 정산되지 않습니다.')
```

- `for start, end, text in selected`: 튜플 3칸을 나눠 받고, `(start, end, text)`로 다시 묶어 원문 위치를 유지해요.
- 70자 예산이면 이 두 문장이 **모두** 빠져요.

### 9-1 `main.py` 읽기에서 짚은 것

- `next(c for c in hits if …)`: 조건에 맞는 첫 번째 하나만 꺼내요.
- `{**c, "text": …}`: Child를 복사한 뒤 일부 키만 덮어써요(뒤에 쓴 키가 이김, 4일차에 배운 `**`).
- `any(t in s[2] for t in terms)`: `s[2]`는 튜플의 세 번째 값(문장). 단어 중 **하나라도** 있으면 True.

### 6-1 `build_context` 형태 다시 보기

- 조각 하나는 `[S번호] 제목\n본문`, 조각 사이는 `\n\n`. 이 2글자도 예산에 넣어서 `+2`.
- 같은 `chunk_id`는 한 번만, `max_chars`를 넘는 조각은 건너뜀.
- 돌려주는 값 두 개: `context`(LLM에 넣을 글), `sources`(S번호가 어느 청크·문서인지).

### 9-2 원질문이 BM25에서 0건인 이유

질문 토큰은 `교육비`, `정산`, `증빙은`, `무엇인가요`인데 education 원문은 `교육비는`, `수료증과`, `영수증을`처럼 조사가 붙어 있어요. 일치하는 토큰이 하나도 없어서 점수가 전부 0이 되고, 0점은 결과에서 빠져요. 7장의 "형태소 분석기 없는 토크나이저" 한계가 그대로 드러난 거라 표현을 바꿔 다시 찾는(rewrite) 게 필요해요.

### 9-2 `search_loop` vs `route`

| | `search_loop` (main.py) | `route` (agent.py) |
| --- | --- | --- |
| 다음 검색문 | 사람이 미리 써 둔 목록 | LLM이 직접 만듦 (`next_query`) |
| 충분한지 판단 | 제목에 "교육비"가 있는지 (규칙) | LLM이 근거를 읽고 판단 |
| Ollama | 마지막 답변 생성만 (`if args.generate:`) | 매번 필요 (파일을 실행하는 것 자체가 LLM을 쓰겠다는 뜻이라 플래그가 없음) |

- 둘 다 `def`(함수)예요. 시도마다 반복해서 쓰니까 함수로 묶었어요.
- `args.generate` = 모델을 부를지 말지 고르는 스위치, `def` = 반복해서 쓰는 코드 묶음.

### 9-2 `agent.py` 오류: `KeyError: 'OLLAMA_MODEL'`

- `agent.py`는 `os.environ["OLLAMA_MODEL"]`처럼 `[ ]`로 꺼내서, 값이 없으면 바로 `KeyError`가 나요. 다른 파일(`rag_core.py`)은 `os.environ.get(...)` 뒤에 안내 문구가 있는 `ValueError`를 내요. 딕셔너리 `d["키"]` vs `d.get("키")`와 같은 차이예요.
- 해결: 터미널마다 먼저 모델 이름을 지정해요(4일차에 받은 모델). 터미널을 닫으면 사라져요.

```powershell
$env:OLLAMA_MODEL="gemma3:4b-it-q4_K_M"
uv run agent.py
```

### 파라미터 vs 아규먼트

- 같은 분야의 말이고 보는 쪽만 달라요.
  - **파라미터:** 함수를 만들 때 정해 둔 빈칸 — `def search_loop(queries, topic, max_searches=2)`
  - **아규먼트:** 함수를 부를 때 실제로 넣는 값 — `search_loop(queries, "교육비", max_searches=1)`
  - 비유: 서류의 칸 이름(파라미터)과 거기에 적은 값(아규먼트)
- `max_searches=2`는 기본값. 안 넣으면 2. 같은 날 Python 보강에서 배운 기본값·키워드 인자와 같은 규칙이에요 → [Python 4장](../../python-basics/04-functions-lists-strings-dicts/#2-기본값-매개변수와-키워드-인자)
- 값을 넣는 위치가 두 군데예요.
  - **프로그램 아규먼트:** 파일 밖, 터미널에서 — `uv run main.py --generate`. 실행 방식을 바꿀 때.
  - **함수 아규먼트:** 코드 안에서 — 같은 기능을 다른 값으로 여러 번 쓸 때. 9-2는 `search_loop`를 값만 바꿔 3번 불러서 `candidates_ready` / `repeated_query` / `search_limit`가 나와요.
  - 비유: 손님 주문(프로그램)과 주방에서 넣는 재료(함수)

### argparse

```python
parser = argparse.ArgumentParser()                         # 1. 주문받는 도구 만들기
parser.add_argument("--generate", action="store_true")     # 2. 옵션 등록
args = parser.parse_args()                                 # 3. 터미널 입력 읽기
if args.generate: ...                                      # 4. 꺼내 쓰기
```

- `store_true`: 옵션을 붙이면 True, 안 붙이면 False. 다른 `action`: `store`(값 저장, 기본), `store_false`, `count`. 다른 옵션: `type`, `default`, `choices`.
- 정해진 것: `argparse`, `ArgumentParser`, `add_argument`, `parse_args`, `action`, `store_true`
- 내가 정하는 것: `parser`, `args`, `"--generate"`. 옵션 이름의 `-`는 꺼낼 때 `_`로 바뀌어요(`--run-model` → `args.run_model`).

### 클래스 / 인스턴스 / 메서드

- 클래스는 틀(붕어빵 틀), 인스턴스는 그 틀로 만든 것 하나(붕어빵). `()`를 붙이면 만들어져요.
  - `parser = argparse.ArgumentParser()`, `embeddings = LocalE5()`, `faith = Faithfulness(llm=llm)`, `graph = nx.DiGraph()`
  - `args`도 인스턴스(Namespace 클래스). `list`와 `dict`도 클래스.
- 메서드는 인스턴스가 가진 기능이고 클래스마다 정해져 있어요 — `parser.add_argument`, `rows.append`, `dict.get`. 없는 메서드를 부르면 `AttributeError`. 무엇이 있는지는 `dir()`이나 공식 문서로 확인.
- 보통 클래스 이름은 대문자, 함수 이름은 소문자로 시작해요.

### 9-3 오류: `DLL load failed while importing _epoch`

- Windows **스마트 앱 컨트롤**이 `srsly` 패키지(GraphRAG 쪽 의존성)의 `.pyd` 파일을 막은 거예요. 코드 오류가 아니에요.
- 기본 실습 `uv run main.py`는 networkx만 써서 정상(`STEP1 10 8`). 선택 실습(`check_setup.py`, `graph_local.py`)은 유료 API도 써요.
- 해결 시도: `uv pip install --force-reinstall srsly` 재설치, 안 되면 강사님께 문의.
- 스마트 앱 컨트롤은 한 번 끄면 Windows를 새로 설치하기 전까지 다시 켤 수 없어서 함부로 끄지 않아요.

### 9-3 `main.py` 한 줄씩

- **불러오기:** `json`, `Path`, `networkx`는 정해진 이름, `nx`는 관례로 붙이는 별명.
- **문서 읽기:** `Path().read_text()`로 글자를 읽고 `json.loads()`로 리스트·dict로. `by_id`는 현행 규정만 `{document_id: 문서}`로 만든 dict(딕셔너리 컴프리헨션).
- **STEP1:** `nx.DiGraph()`로 빈 방향 그래프 → `add_edge(A, B, 이름=값…)`로 A → B 화살표와 메모. 점이 없으면 자동으로 생겨요. 메모 이름(`relation`, `condition`, `source_document_id`, `source_url`)은 내가 지은 것.
- **STEP2:**
  - `sorted(graph.predecessors("영수증"))`: 영수증으로 화살표를 **보내는** 점 → `['education', 'meal', 'travel']`
  - `out_edges(did, data=True)`: 그 점에서 나가는 화살표를 `(출발, 도착, 메모)` 3칸으로 돌려줘요(정해진 형식). `_`, `v`, `edge`는 내가 지은 이름이고 `_`는 이미 아는 출발점이라 버리는 값.
  - `if edge["relation"] == "승인자"`는 고르는 기준, `(v, edge["condition"])`은 남기는 값. 남은 게 전부 승인자라 "승인자"는 다시 적지 않아요(넣고 싶으면 `(v, edge["relation"], edge["condition"])`).
  - education의 나가는 화살표 3개(영수증 제출, 수료증 제출, 팀장 승인자) 중 승인자만 남아요 → `[("팀장", "수강 전")]`. "수강 전"은 `relations`의 `("education", "팀장", "승인자", "수강 전")` 줄에서 메모로 저장됐다가 꺼낸 값이에요.
  - `A if 조건 else B`에서 빈 리스트는 거짓 → meal은 "승인자 규정 없음". leave와 vpn은 영수증으로 가는 화살표가 없어서 안 뽑혀요.
- **STEP3:** `by_id["travel"]["content"]`로 원문 출력 → 그래프 내용이 원문에 있는지 사람이 확인.
- **STEP4:**
  - `Path("graphrag_demo/input")`은 경로만 만들고(폴더는 아직 없음), `mkdir(parents=True, exist_ok=True)`로 위 폴더까지 만들되 이미 있어도 오류 없음.
  - `.items()`로 (키, 값), `target / f"{did}.txt"`는 Path에 `/`로 경로를 이어 붙이기, `write_text(..., encoding="utf-8")`로 파일 쓰기.
  - 파일 안은 `document_id: travel` / `출처: …` / `제목: …` / 빈 줄 / 본문. `len(list(target.glob("*.txt")))` = 10개.

### 5일차 환경 준비

- `uv sync` 후 선택 실습 패키지(ragas, openai, langchain-community, graphrag, colpali-engine, accelerate)와 ColPali 모델(`vidore/colpali-v1.3` 어댑터 110MB + `colpaligemma-3b-pt-448-base` 5.5GB)을 수업 전에 미리 받아 뒀어요.
- README는 선택 실습을 `uv add` 대신 `uv run --with 패키지==버전 …`으로 돌리라고 해요. 기본 환경(`pyproject.toml`)을 건드리지 않고 그 실행에만 패키지를 얹는 방식이에요.
- ColPali는 키트 기본 `transformers==5.5.2`(그리고 5.4.0)에서 `KeyError: 'llava'`가 났고, **5.3.0에서 로드됐어요.** 오프라인 모드에서는 processor가 어댑터 저장소의 `config.json`을 찾으러 가서 실패하니 온라인으로 실행해요.

```bash
uv run --with colpali-engine==0.3.18 --with accelerate --with transformers==5.3.0 visual_search.py
```

### 8·9장 큰 흐름에서 정리 (수업 후 질문)

```text
8장 (평가): 고친 게 정말 좋아졌는지 숫자로 확인
  8-1 정답지 만들기 → 8-2 검색 채점 → 8-3 답변 채점 → 8-4 전후 비교
9장 (고급 RAG): 기본 RAG가 못하는 것 보완
  9-1 근거 넓히고 줄이기 → 9-2 다시 검색하기 → 9-3 관계로 찾기 → 9-4 이미지로 찾기
```

**오늘 핵심 교훈**

1. 바꿨으면 숫자로 비교한다 (8장, dev → test).
2. 작게 찾고 크게 답한다 (9-1).
3. 반복에는 종료 조건을 둔다 (9-2).
4. 모델이나 그래프 결과는 원문으로 다시 검사한다 (9-2 인용 검사, 9-3 STEP3, 9-4 예외 조건).

## 실습 코드에서 직접 바꾼 점

원본 키트(`rag_day5` ZIP)와 비교한 내용입니다.

| 파일 | 바꾼 점 / 추가한 주석 |
| --- | --- |
| 9-1 `main.py` | `from printsection import print_section` + 구역마다 `print_section("1번")` … `("4번")` 출력 추가 |
| 9-1 `q_hard.py` | `chosen = [(start, end, text) for start, end, text in selected if "승인" in text]` → `for row in chosen: print(row)` |
| 9-2 `main.py` | `from printsection import print_section` import만 추가 |
| 9-3 | 코드는 그대로. `configure_api.py`로 `.env`를 만들고(올리지 않음) GraphRAG 색인·질의를 실행해 `graph_check.json`, `local_embedding_preparation.json`, `graphrag_demo/output` 생성 |

## 마무리 과제 (PPT)

- [ ] `ch09/rag_ch09_01`에서 `uv run compare_contexts.py` — Ollama로 짧은 추출문과 Parent 전체의 답 비교
- [ ] 질문 하나를 골라 원문 → 청크 → 검색 → Context → 답변 → 평가까지, 단계마다 실제 데이터를 붙여 한 장으로 정리
- [ ] 9-2 q\_hard: `same` → `repeated_query · 검색 1번 · []`, `changed` → `candidates_ready · 검색 2번 · [60, 0]`
- [ ] 9-3 q\_hard: `graph.predecessors("팀장")` → education 수강 전 / leave 휴가 시작 3영업일 전 (`successors("팀장")`은 `[]`)
- [ ] 9-4 `main.py` 실행과 q\_hard: 숙박 행 `120000 travel …`, 선택 실습 `visual_search.py`(ColPali)

## 확인 문제

강의 내용을 바탕으로 직접 만든 복습 문제입니다. 객관식 4문제, 서술형 2문제이고 각 문제 바로 아래에 정답이 있습니다.

### 9-Q1. Parent-Child (9-1)

검색은 80자 Child로 하고 답변에는 148자 Parent를 넘기는 이유로 가장 알맞은 것은?

① Parent로 검색하면 BM25 점수가 항상 0이 돼서  
② 작은 Child가 위치를 정확히 찾고, 답에 필요한 앞뒤 조건(서면 승인)은 Parent에 온전히 있어서  
③ Child와 Parent의 `chunk_id`가 같아서  
④ Parent를 넣으면 Context 예산이 줄어들어서

<details>
<summary>정답 보기</summary>

**②** — 80자 `travel@0`은 "담당 임원의 서면"에서 끊겨요. 큰 조각으로 검색하면 위치가 흐려지고, 작은 조각만 넘기면 조건이 잘려요. 그래서 "작게 찾고 넓게 읽기". Parent는 새 `chunk_id`(`travel:parent:버전`)를 받고, Context는 오히려 길어져서 압축이 필요해요.

</details>

### 9-Q2. 재검색 루프의 종료 이유 (9-2)

`search_loop([question, question], "교육비")`의 결과는?

① `candidates_ready`  
② `search_limit`  
③ `repeated_query`  
④ 무한 반복

<details>
<summary>정답 보기</summary>

**③** — 첫 번째 질문은 0건이라 `seen`에 넣고 다음으로 가요. 두 번째가 같은 질문이라 `if query in seen`에서 바로 멈춰요. 같은 검색문은 결과도 같을 테니 다시 검색할 필요가 없어요. `search_limit`는 `max_searches=1`처럼 횟수를 다 썼을 때예요.

</details>

### 9-Q3. 그래프 탐색 (9-3)

간선 방향이 "규정 → 대상"일 때 `graph.predecessors("영수증")`이 돌려주는 것은?

① 영수증에서 나가는 화살표의 도착점  
② 영수증과 연결된 모든 간선의 메모  
③ 영수증을 승인하는 사람  
④ 영수증으로 화살표를 보내는 규정 `['education', 'meal', 'travel']`

<details>
<summary>정답 보기</summary>

**④** — predecessors는 "나를 가리키는 점"이에요. 화살표가 규정 → 영수증이니 규정들이 나와요. 반대로 `successors("팀장")`처럼 대상에서 나가는 걸 찾으면 `[]`예요. 승인자는 각 규정의 `out_edges`에서 `relation == "승인자"`로 따로 골라요.

</details>

### 9-Q4. 숫자 계산과 판단 (9-4)

travel 12만원(1박당)과 education 30만원(분기 1회, 1인당)을 추출했다. 맞는 것은?

① 2박 숙박 기본 한도는 240,000원이지만, 12만원을 넘는 숙박의 승인 조건은 원문에서 따로 확인한다  
② 출장과 교육을 합친 총 한도는 540,000원이다  
③ 정규식으로 금액을 뽑았으니 단위는 확인하지 않아도 된다  
④ MaxSim 점수가 높은 페이지의 금액이 항상 정답이다

<details>
<summary>정답 보기</summary>

**①** — 계산은 계산이고 승인 판단은 따로예요. 다른 규정 예산을 합칠 근거가 없고(②), 같은 "12만원"도 1박당인지 1일당인지에 따라 뜻이 달라요(③, 8-3의 답변 D). MaxSim은 페이지 검색 점수일 뿐 정답 확률이 아니에요(④).

</details>

### 9-Q5. 서술형 — 압축 예산 70 vs 140 (9-1)

"13만원짜리 숙박도 정산할 수 있나요?"에 예산 70의 추출문과 예산 140의 추출문을 넣었을 때 답이 어떻게 달라질 수 있는지, 그리고 압축할 때 무엇을 확인해야 하는지 쓰세요.

<details>
<summary>예시 답안</summary>

예산 70에는 "1박당 12만원"과 "숙박 영수증 첨부" 두 문장(54자)만 들어가고, "한도 초과는 예약 전 담당 임원 서면 승인", "승인 없는 초과는 자동 정산 안 됨"이 빠져요. 그러면 모델이 "12만원 초과라 정산할 수 없다"처럼 예외를 모른 채 단정할 수 있어요. 예산 140이면 네 문장(124자)이 다 들어가서 "예약 전에 서면 승인을 받아야 한다"고 답할 수 있어요. 두 답 모두 출처는 S1이라 출처만 보면 차이를 몰라요. 그래서 압축할 때는 길이가 얼마나 줄었는지만 보지 말고, 질문에 필요한 **예외 조건(초과·승인)**이 남았는지 확인해야 해요.

</details>

### 9-Q6. 서술형 — `route`가 answer를 골랐는데도 막는 이유 (9-2)

교안 기록에서 gemma3는 첫 검색이 빈 목록인데도 `action: "answer"`를 골랐다. `agent.py`가 이걸 어떻게 막는지, 왜 필요한지 쓰세요.

<details>
<summary>예시 답안</summary>

`answer`일 때 `evidence_quotes`가 비어 있거나, 인용문 중 하나라도 실제 Context 문자열 안에 없으면 "인용을 Context에서 확인할 수 없음"으로 중단해요. 빈 목록에서는 인용할 문장이 없으니 걸려요. 모델이 다음 행동을 고르게 하면 근거 없이 "답할 수 있다"고 판단하거나 인용을 지어낼 수 있어서, 6장 `validate_answer`·`bind_claim`처럼 코드로 한 번 더 검사해야 해요. 다만 문자열 포함 검사는 최소한의 확인이라, 인용이 질문의 모든 조건을 뒷받침하는지까지 증명하지는 못해요. 그리고 재검색 횟수(2번)와 같은 질의 반복 검사로 끝없이 돌지 않게 막아요.

</details>
