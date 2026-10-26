# 6장. Context · 2-Step RAG · Citation · 답변 보류 — 근거로 답하고, 출처를 보이고, 모르면 보류하기

> 2026-10-26 학습 기록. RAG 4일차 오전 수업입니다. 5장 Qdrant 검색 결과를 모델에 넣을 Context로 묶고(6-1), 검색 → 생성 → 검사를 세 함수로 나눠 Ollama로 실제 답을 받아 보고(6-2), 답 문장을 원문 발췌와 URL에 연결하고(6-3), 근거가 모자랄 때 무엇이 부족한지 적고 보류하는 방법(6-4)을 실습했습니다.

## 학습 목표

- 검색 결과를 `[S1] 제목 + 본문` 조각으로 묶고, `chunk_id`로 중복을 지우고, 문자 예산 안에 들어가는 근거만 Context에 넣는다.
- 검색 단계(k)에서 빠진 근거와 Context 예산(max\_chars)에서 빠진 근거를 구분한다.
- `prepare → invoke_model → finish` 세 단계로 2-Step RAG를 만들고, 모델 응답을 JSON Schema와 `validate_answer`로 검사한다.
- 답 문장의 `S1`을 이번 요청의 출처 목록으로 원문·URL에 연결하고, 코드가 잡는 오류와 사람이 봐야 하는 오류를 나눈다.
- "검색 결과가 있다 ≠ 답할 수 있다"를 다섯 가지 상황으로 구분하고, 보류(`insufficient`)와 앱 오류(`system_error`·`invalid_output`)를 다르게 처리한다.

## 실습 파일

| 강 | 주제 | 실습 상태 |
| --- | --- | --- |
| 6-1 | Retriever 결과와 Context 구성 — `chunk_id` 중복 제거, S1 라벨, 예산 120·200·300 | ✅ `main.py` · q\_hard 통과 |
| 6-2 | 기본 2-Step RAG 체인 — `prepare` → `invoke_model` → `finish`, JSON Schema, `--generate` | ✅ `main.py` · q\_hard 통과 · `--generate` 실행(아래 오류 기록) |
| 6-3 | 출처가 보이는 Citation 응답 — `lookup`, `bind_claim`, 단위가 바뀐 문장 | ✅ `main.py` · q\_hard 통과 |
| 6-4 | 근거 부족 시 답변 보류 — 여섯 질문, `insufficient` vs 오류 상태 | ✅ `main.py` · q\_hard 통과 |

수업에서 받은 `rag_day4` 키트(6·7장 8개 강의 + 공통 uv 환경)로 진행했습니다. 강마다 `uv run prepare.py`로 벡터를 먼저 만들고 `main.py` → `q_hard.py` 순서로 확인했습니다(q\_easy는 같은 문제의 빈칸 버전이라 q\_hard로 바로 풀었습니다). 키트 코드는 올리지 않고, **원본 ZIP과 비교해 직접 바꾸거나 추가한 부분**만 아래에 기록합니다.

## 전체 흐름

### 한 문장

**검색됐다고 답할 수 있는 게 아닙니다. Context에 실제로 무엇이 들어갔는지 확인하고, 모델 답을 검사하고, 출처를 원문에 연결하고, 근거가 모자라면 보류합니다.**

### 그림으로 보기

```text
질문 → 검색(5장 open_saved_index)
   │  6-1  chunk_id 중복 제거 → [S1] 제목+본문 → 예산 안에 들어가는 것만 → context + sources
   ▼
prepare(검색 + Context) → invoke_model(Ollama, JSON Schema) → finish(validate_answer)   ← 6-2
   │  6-3  답 문장 S1 → lookup → 원문 발췌(quote)가 있나 → URL 형식 → extractive_match / review_meaning
   │  6-4  근거 충분이면 answered, 모자라면 insufficient + "무엇이 부족한지" + citations []
   ▼
답 + 출처 (또는 보류)   →  7장: 보류만 하지 말고 검색 자체를 더 잘할 수는 없을까?
```

### 오전 내내 쓴 두 질문

| 이름 | 질문 | 필요한 사실 |
| --- | --- | --- |
| 숙박 | 출장 숙박 비용 한도와 필요한 증빙은? | 1박당 12만원 · 숙박 영수증 (travel 한 문서) |
| 복합 | 출장 식비와 숙박비의 한도는 각각 얼마이고 두 한도를 합쳐 쓸 수 있나요? | 식비 1일 3만원(meal 0) · 숙박 1박당 12만원(travel 0) · 합산 금지(meal 60) |

## 핵심 이론

### 1. Context 구성 (6-1강)

**복합 질문의 1위 청크에는 금액이 하나도 없어요.** 1위 `meal 60`(55자)은 "합산하지 않는다"만 있고, 금액은 2위 `meal 0`(식비)과 3위 `travel 0`(숙박)에 있어요. 여러 문서가 필요한 질문은 1위 하나로 답이 완성되지 않아요.

**중복 제거는 `document_id`가 아니라 `chunk_id`로**

```python
repeated = rows + [rows[0]]                                         # 첫 청크를 일부러 한 번 더 → 4개
unique = list({row["chunk_id"]: row for row in repeated}.values())  # chunk_id를 키로 → 3개
# 입력 4 중복 제거 3
# [('meal', 60), ('meal', 0), ('travel', 0)]
```

- 딕셔너리 키는 한 번만 들어가요. 같은 `chunk_id`가 다시 나오면 **새 칸이 생기지 않고 값만 덮어써요**.
- `.values()`로 청크만 꺼내 `list()`로 바꿔요. 순서는 키가 처음 들어간 자리를 유지해요.
- `document_id`로 지우면 `meal 0`과 `meal 60`이 하나로 합쳐져 **식비 금액이 사라져요**. 같은 문서라도 청크마다 담은 사실이 달라요.

for문으로 풀면:

```python
d = {}
for row in repeated:
    d[row["chunk_id"]] = row
unique = list(d.values())
```

**S1 라벨과 제목까지 길이에 들어가요**

```python
piece = f'[{label}] {row["metadata"]["title"]}\n{row["text"]}'
# 본문 55자 → 라벨·제목 포함 69자
```

**`pack_context`: 예산을 넘는 청크는 통째로 건너뛰어요**

```python
def pack_context(rows, max_chars):
    pieces, sources = [], []
    used = 0
    for row in rows:
        label = f"S{len(sources) + 1}"          # 실제로 넣은 개수로 번호 → 건너뛴 청크엔 번호 없음
        piece = f'[{label}] {row["metadata"]["title"]}\n{row["text"]}'
        if used + len(piece) + 2 > max_chars:   # +2 = 조각 사이에 들어갈 "\n\n"
            continue
        pieces.append(piece)
        sources.append({"id": label, "chunk_id": row["chunk_id"],
                        "document_id": row["document_id"],
                        "source_url": row["metadata"]["source_url"]})
        used += len(piece) + 2
    return "\n\n".join(pieces), sources
```

| 반환값 | 들어 있는 것 | 쓰는 곳 |
| --- | --- | --- |
| `context` | 라벨 · 제목 · 본문 | 모델 입력 |
| `sources` | 라벨 · chunk\_id · 문서 ID · URL | 답의 S1을 원문에 연결 |

**같은 검색, 다른 예산**

```text
120 실제 길이 69  [('S1', 'meal')]                                  ← 식비·숙박 금액 빠짐
200 실제 길이 165 [('S1', 'meal'), ('S2', 'meal')]                  ← 숙박 금액 빠짐
300 실제 길이 261 [('S1', 'meal'), ('S2', 'meal'), ('S3', 'travel')] ← 세 항목 모두
```

- 이번 예산은 **문자 수**예요. 실제 서비스는 모델 tokenizer로 **토큰**을 세고, 시스템·질문·대화 기록·출력 공간까지 남겨야 해요.
- 근거가 빠졌으면 먼저 구분해요: ① 검색 단계에서 안 나왔나(k) ② Context 예산 때문에 빠졌나(max\_chars).

### 2. 2-Step RAG 체인 (6-2강)

세 함수가 `state` 딕셔너리를 이어받아요.

| 함수 | state에 추가되는 값 | 확인할 것 |
| --- | --- | --- |
| `prepare` | `rows` · `context` · `sources` | 질문에 필요한 원문이 있나 |
| `invoke_model` | `draft` | 모델이 실제로 낸 출력 |
| `finish` | 검사된 응답 · `trace` | 출처 연결 · 보류 설명 유지 |

**모델 입력은 두 메시지: 규칙(system)과 데이터(user)**

```python
[{"role": "system", "content": "제공된 Context만 근거로 사용 … 부족하면 insufficient, citations는 빈 배열"},
 {"role": "user", "content": json.dumps({"question": q, "context": context}, ensure_ascii=False)}]
```

**응답 모양부터 정해요 — JSON Schema**

```python
{"type": "object", "properties": {
    "status": {"type": "string", "enum": ["answered", "insufficient"]},
    "answer": {"type": "string"},
    "citations": {"type": "array", "items": {"type": "string"}}},
 "required": ["status", "answer", "citations"], "additionalProperties": False}
```

- `enum`: status는 두 값 중 하나만. `additionalProperties: False`: 정한 필드 말고는 못 넣게.
- JSON 형식을 지정하는 건 **형식 제약**이지 **사실성 보장**이 아니에요.

**Ollama 응답은 JSON 두 겹**

```python
response = httpx.post(base + "/api/chat", json={"model": model, "messages": messages,
    "format": schema, "stream": False, "options": {"temperature": 0}}, timeout=120)
raw = response.json()["message"]["content"]   # 바깥 층: HTTP 응답 전체 → 모델이 쓴 JSON "문자열"
draft = json.loads(raw)                        # 안쪽 층: 문자열 → status · answer · citations 딕셔너리
```

**`validate_answer`: 출처는 저장된 값으로, 보류 사유는 그대로**

```python
allowed = {s["id"] for s in sources}
if not set(citations) <= allowed:                          raise ValueError("검색 근거에 없는 출처")   # S99 차단
if payload["status"] == "answered" and not citations:      raise ValueError("답변에 출처가 없음")
if payload["status"] == "insufficient" and citations:      raise ValueError("보류 응답의 출처는 빈 배열로 반환")
return {**payload, "sources": [s for s in sources if s["id"] in citations]}
```

- URL은 모델에게 쓰게 하지 않아요(없는 주소를 지어낼 수 있음). 앱이 `S1 → sources → source_url`로 붙여요.
- 이 검사를 통과해도 **답 문장이 원문 뜻과 같은지는 따로** 봐야 해요.

**세 함수를 체인 하나로**

```python
chain = (RunnableLambda(lambda request: prepare(index, request))
         | RunnableLambda(invoke_model) | RunnableLambda(finish))
result = chain.invoke({"question": q, "k": 3})
# = finish(invoke_model(prepare(index, {"question": q, "k": 3})))  같은 결과
```

`|`는 앞 함수의 반환값을 다음 함수의 입력으로 넘겨요(LangChain 3장 LCEL 파이프).

### 3. Citation 응답 (6-3강)

"출장 전체의 숙박비는 최대 12만원이에요. [S1]" — 숫자는 같은데 **원문은 "1박당"**이에요. 출처가 붙어 있다고 맞는 답은 아니에요.

**라벨 → 실제 청크: 이번 요청의 sources로만 연결**

```python
by_chunk = {r["chunk_id"]: r for r in state["rows"]}
lookup = {source["id"]: by_chunk[source["chunk_id"]] for source in state["sources"]}
# 숙박 질문: S1 → travel:0, S2 → meal:0, S3 → meal:60
```

S1은 요청마다 가리키는 청크가 달라요(복합 질문의 S1은 meal 60). 앞 질문의 매핑을 재사용하면 엉뚱한 문서에 출처가 붙어요.

**`bind_claim`: 출처 → 발췌 → URL 순서로 검사, 그다음 문장 비교**

```python
def bind_claim(claim, lookup):
    source = lookup.get(claim["source_id"])
    if source is None:                         return "unknown_source", None
    if claim["quote"] not in source["text"] or not claim["quote"].strip():
                                               return "quote_not_found", None
    url = source["metadata"]["source_url"]
    if urlparse(url).scheme not in {"http", "https"} or not urlparse(url).netloc:
                                               return "invalid_url", None
    status = "extractive_match" if claim["text"] == claim["quote"] else "review_meaning"
    return status, {"text": claim["text"], "url": url, "quote": claim["quote"]}
```

| 바꾼 것 | 결과 | 누가 잡나 |
| --- | --- | --- |
| S1 → S99 | `unknown_source` | 코드 |
| 발췌를 "20만원"으로 | `quote_not_found` | 코드 |
| "1박당" → "출장 전체" | `review_meaning` | **사람** (발췌는 맞고 답 문장만 다름) |

- `extractive_match`는 "원문 그대로"라는 뜻일 뿐, 질문의 모든 항목에 답했는지는 따로 확인해요.
- URL은 형식만 검사하고 실제로 접속되는지는 확인하지 않아요.

### 4. 답변 보류 (6-4강)

"해외 출장 항공 좌석 등급은?"에도 청크 세 개가 나와요(국내 식비·숙박). 이걸로 답하면 안 돼요.

**여섯 질문, 같은 검색기 — 모두 결과는 있지만 답할 수 있는 건 두 사례뿐**

| 사례 | 질문 | k | 상황 | 대응 |
| --- | --- | --- | --- | --- |
| 한도와 증빙 | 출장 숙박 비용 한도와 필요한 증빙은? | 3 | 필요 사실 모두 포함 | 원문 범위에서 답 |
| 일부 근거 | 복합 질문 | 1 | 일부 사실 누락(합산 금지만) | 금액 추가 검색 또는 부족 항목 안내 |
| 두 문서 확보 | 복합 질문 | 3 | 필요 사실 모두 포함 | 원문 범위에서 답 |
| 범위 밖 | 해외 출장 항공 좌석 등급은? | 3 | 적용 범위 다름 | 해외 항공 규정 필요 안내 |
| 규정 미정 | 개인 취미 강좌도 지원하나요? | 3 | 규정에 명시 안 됨 | 지원 여부 확인 필요 안내 |
| 대상 모호 | 지원 한도는 얼마인가요? | 3 | 질문 대상 모호 | 어떤 비용 항목인지 되묻기 |

**보류 응답에는 무엇이 부족한지 적어요**

```python
{"status": "insufficient",
 "answer": "현재 자료에서 해외 출장 항공 좌석 등급을 확인할 수 없습니다. 해외 항공 이용 규정이 필요합니다.",
 "citations": []}
```

국내 숙박 12만원을 끌어오거나, 일반 회사 관행으로 추측하지 않아요.

**`insufficient ≠ 오류`**

| 상태 | 종류 | 언제 |
| --- | --- | --- |
| `insufficient` | 정상 응답 | Context에 필요한 사실이 없음 (빈 sources면 모델 호출 없이 바로) |
| `system_error` | 앱 오류 | 서버 연결 · HTTP 실패 (`httpx.HTTPError`) |
| `invalid_output` | 앱 오류 | 응답 파싱 · 검사 실패 (`ValueError`) |

```python
try:
    result = finish(invoke_model(state))
except httpx.HTTPError as error:
    result = {"status": "system_error", "error_type": type(error).__name__}
except ValueError as error:
    result = {"status": "invalid_output", "reason": str(error)}
```

## 시작 전 환경 확인

- `uv sync`로 `rag_day4\.venv` 준비. `printsection`은 `pyproject.toml`에 있어서 `uv sync`로 같이 설치됨(새 프로젝트에 넣을 땐 `uv add printsection`)
- Ollama 0.40.7, `gemma3:4b-it-q4_K_M` 이미 받아 둠, 서버 켜짐
- `--generate` 전에 **터미널마다** `$env:OLLAMA_MODEL = "gemma3:4b-it-q4_K_M"` 필요 → 없으면 `OLLAMA_MODEL에 설치된 모델 이름을 지정하세요` 오류. `OLLAMA_BASE_URL`은 코드 기본값이 `http://localhost:11434`라 생략 가능
- 7장 3강용 Cross-Encoder도 미리 받아 둠 → [7장](../07-hybrid-search-rerank-rewrite/)

## 실행 중 만난 오류

### 6-2 `--generate`: `ValueError: 보류 응답의 출처는 빈 배열로 반환`

- **코드 문제가 아니었어요.** gemma3 4b가 `"status": "insufficient"`로 보류해 놓고 `citations`에 출처를 넣어 보냈고, `validate_answer`가 막은 거예요.
- 같은 질문으로 다시 돌리니 이번엔 `citations: []`라 통과했지만, 답(12만원·영수증)을 다 말해 놓고 `insufficient`라고 했어요. 작은 모델은 "답함/보류" 판단이 흔들려요.

```json
{"status": "insufficient",
 "answer": "출장 숙박 비용 한도는 1박당 12만원이며, 숙박 영수증을 첨부해야 합니다. … 추가적으로 필요한 정보가 부족합니다.",
 "citations": []}
```

- PPT 기록과 같은 현상이에요: **형식 검사는 통과, 품질은 불통과**(답할 수 있는데 보류, 잘린 문장을 이어 씀).
- 배운 점: LLM 결과를 그대로 믿지 않고 형식·출처를 검사하는 게 6장의 핵심. 4번에서 일부러 넣어 본 "잘못된 출처"를 5번에서 실제 모델이 저질렀어요.

## 질문과 새로 알게 된 점

### `pack_context(found, maxchars=budget)` → `TypeError`

함수 정의가 `def pack_context(rows, max_chars)`라서 **키워드 이름이 한 글자라도 다르면** `unexpected keyword argument` 오류가 나요. `max_chars=budget`으로 고쳤어요.

### f-string 중괄호 안의 쉼표는 튜플

```python
print(f"예산: {budget, results[(k, budget)]}")   # 예산: (300, ['meal'])   ← 둘이 튜플 하나로 묶임
print(f"예산: {budget}, {results[(k, budget)]}") # 예산: 300, ['meal']     ← 값마다 { } 따로
```

### `results`는 키가 튜플인 딕셔너리

```python
results = {
    (1, 300): ["meal"],                     # 1개만 검색 → 검색 단계에서 travel이 없음
    (3, 200): ["meal", "meal"],             # 3개 검색했지만 예산 200이라 travel이 안 들어감
    (3, 300): ["meal", "meal", "travel"],   # 예산이 넉넉해서 3개 다
}
```

`meal`이 두 번인 건 같은 식비 문서의 청크 2개(meal 60, meal 0)라서예요. `document_id`는 원문 문서 이름이라 같은 문서의 청크끼리는 값이 같아요.

### `row`와 `piece`의 모양

```python
row = {"chunk_id": "travel:46fb3976b5b2:80:20:0", "document_id": "travel", "start": 0,
       "text": "국내 출장 숙박 비용 한도는 1박당 12만원입니다. …",
       "metadata": {"title": "출장 숙박 정산", "source_url": "https://example.invalid/rag40/travel",
                    "status": "current", "category": "travel"}, "score": 0.89}
piece = "[S1] 출장 숙박 정산\n국내 출장 숙박 비용 한도는 1박당 12만원입니다. …"
```

- `len(piece)` = `[S1]`의 `[`부터 본문 끝까지 글자 수(띄어쓰기, 제목 뒤 `\n` 포함)
- `+2` = 조각과 조각 사이에 들어갈 `\n\n` 두 글자 (`"\n\n".join(pieces)`)

### `{**checked, "trace": {...}}`의 `**`

딕셔너리를 **펼쳐서 안의 칸을 그대로 옮겨 담는** 기호예요.

```python
checked = {"status": "answered", "answer": "…", "citations": ["S1"], "sources": [...]}
{**checked, "trace": {...}}
# = {"status": …, "answer": …, "citations": …, "sources": …, "trace": {...}}   ← 칸 복사 + trace 추가
```

- `**` 없이 `{checked, "trace": …}`는 문법 오류(딕셔너리 안에는 `키: 값` 쌍만).
- 5장 `{**hit.payload, "score": …}`와 같은 패턴. 같은 키가 있으면 **뒤에 쓴 값이 이겨요** → `{**claim, "source_id": "S99"}`는 claim을 복사하되 source\_id만 바꾼 것.

### `bind_claim(candidate, lookup)[0]`과 `statuses[-1]`

```python
statuses.append(bind_claim(candidate, lookup)[0])   # (status, linked) 튜플에서 [0] = 상태 글자만
print(statuses[-1], text)                            # [-1] = 리스트 마지막 칸 = 방금 붙인 값
```

| 반복 | text | 반환 | `[0]` | statuses |
| --- | --- | --- | --- | --- |
| 1 | …1박 기준 12만원입니다. | `("review_meaning", {...})` | `review_meaning` | `["review_meaning"]` |
| 2 | …전체 일정 기준 12만원입니다. | `("review_meaning", {...})` | `review_meaning` | `["review_meaning", "review_meaning"]` |

둘 다 `review_meaning`이지만 둘째는 **단위가 틀린 문장**이에요. 글자 비교로는 의미 오류를 못 잡아요 → 코드는 "다르다"까지, 맞고 틀림은 사람이 판단.

### 오전 흐름 한 줄씩 (PPT 41장 "정리")

| 강 | 하는 일 | 핵심 |
| --- | --- | --- |
| 6-1 Context | 검색 결과를 모델에 넣을 한 덩어리로 | `chunk_id` 중복 제거, `[S1] 제목+본문`, 예산 넘으면 건너뜀 |
| 6-2 2-Step RAG | 검색과 생성을 단계로 나누기 | `prepare` → 모델 → `finish`, JSON 두 겹, `validate_answer` |
| 6-3 Citation | 답 문장에 출처 붙이기 | `bind_claim`, `extractive_match` / `review_meaning` |
| 6-4 보류 | 모르면 모른다고 하기 | 다섯 가지 상황, `insufficient ≠ 오류`, 부족한 내용 + `citations: []` |

### 6장 요약 ↔ 키트 코드 위치 (`rag_day4/ch06/` 기준)

- **6-1** 검색 결과 3개 받기 `rag_ch06_01/main.py:10` · `chunk_id`로 중복 제거 `:20` · `[S1] 제목 + 본문` 조각 `:41` · 예산 넘으면 건너뛰기 `:44` · 출처 목록 담기 `:48` · 예산 120/200/300 비교 `:60`
- **6-2** `prepare` 검색 + Context `rag_steps.py:10` · system/user 메시지 `:34` · Ollama 호출 `invoke_model` `:48` · JSON 두 겹 풀기 `:62` · `finish` `:68` · `validate_answer` `rag_core.py:215`(S99 차단 `:230`, 보류인데 출처 있음 `:236`) · 세 단계 체인 `main.py:66`
- **6-3** S1 → 원문 `lookup` `main.py:20` · claim 만들기 `:32` · `bind_claim` `:46` · `review_meaning` 판단 `:57` · 실패 사례 비교 `:70`
- **6-4** 다섯 상황 질문 목록 `main.py:16` · 보류 예시 `:41` · 근거 없으면 모델 생략 `rag_steps.py:48` · `system_error`/`invalid_output` 구분 `main.py:64`

## 실습 코드에서 직접 바꾼 점

원본 키트(`rag_day4` ZIP)와 비교한 내용입니다.

| 파일 | 바꾼 점 / 추가한 주석 |
| --- | --- |
| 네 강의 `main.py` | `from printsection import print_section` + 구역마다 `print_section("1번")` … 출력 추가 |
| 6-1 `main.py` | `print_section("3번") # 실제 실무 컨텍스트 짜는 코드` |
| 6-1 `q_hard.py` | `found = index.search(question, k=k)` → `pack_context(found, max_chars=budget)` → `results[(k, budget)] = [s["document_id"] for s in source_map]` → `print(f"k: {k}, 예산: {budget}, {results[(k, budget)]}, ")` (처음엔 `maxchars`, `{budget, results[...]}`로 썼다가 고침) |
| 6-2 `q_hard.py` | `state = prepare(index, {"question": question, "k": k})` → `document_ids = {s["document_id"] for s in state["sources"]}` → `results[k], contexts[k] = sorted(document_ids), state["context"] #순서강제` |
| 6-2 `rag_core.py` | `validate_answer`에 주석: `# status강제 오류`, `# enum으로 둘중하나 지정했는데 오류.(아예없거나 ed가없거나 etc..)` |
| 6-2 `rag_steps.py` | `response_schema` 아래 주석: `# additionalProperties = 지정한 pro 아니면 안나오게. 대답을 강제하기위해서.` |
| 6-3 `q_hard.py` | `candidate = {"source_id": "S1", "text": text, "quote": quote}` → `statuses.append(bind_claim(candidate, lookup)[0])` → `print(statuses[-1], text)`, 끝에 `# 퀄리티 높이기` 메모 |
| 6-4 `main.py` | 복합 질문 줄에 `# POC가 끝나면 난이도 높은 질문 해보기.` |
| 6-4 `q_hard.py` | `draft = {"status": "insufficient", "answer": "현재 자료에서 해외 출장 항공 좌석 등급을 확인할 수 없습니다. 해외 항공 이용 규정이 필요합니다.", "citations": []}` |

## 확인 문제

강의 내용을 바탕으로 직접 만든 복습 문제입니다. 객관식 4문제, 서술형 2문제이고 각 문제 바로 아래에 정답이 있습니다.

### 6-Q1. 예산 200에서 travel이 빠진 이유 (6-1)

복합 질문을 k=3으로 검색하면 meal 60, meal 0, travel 0이 나온다. `max_chars=200`으로 `pack_context`를 했더니 sources가 meal, meal뿐이었다. 이유는?

① 검색 단계에서 travel이 Top-3에 들지 못해서  
② `chunk_id` 중복 제거에서 travel이 지워져서  
③ 앞의 두 조각을 넣고 나니 travel 조각까지 넣으면 200자를 넘어서 건너뛰어서  
④ travel 청크의 `status`가 current가 아니어서

<details>
<summary>정답 보기</summary>

**③** — 검색에는 나왔지만 **Context 예산 단계**에서 빠진 경우예요. `used + len(piece) + 2 > max_chars`면 `continue`로 건너뛰어요. k=1일 때는 ①처럼 검색 단계에서 빠진 경우라 원인이 달라요.

</details>

### 6-Q2. `draft = json.loads(response.json()["message"]["content"])` (6-2)

이 줄에서 `json`을 두 번 푸는 이유는?

① Ollama HTTP 응답이 JSON이고, 그 안 `message.content`에 모델이 쓴 답이 **JSON 문자열**로 들어 있어서  
② 한 번 풀면 한글이 깨져서 두 번 풀어 복원하려고  
③ `temperature: 0`이면 응답이 두 번 반복돼서  
④ `stream: False`면 JSON이 두 조각으로 나뉘어 와서

<details>
<summary>정답 보기</summary>

**①** — 바깥 층 `response.json()`은 HTTP 응답 전체, 안쪽 `content`는 아직 글자(str)라서 `json.loads`로 한 번 더 풀어야 `draft["status"]`처럼 쓸 수 있어요.

</details>

### 6-Q3. 코드가 못 잡는 오류 (6-3)

원문 S1이 "국내 출장 숙박 비용 한도는 1박당 12만원입니다."일 때, `bind_claim`이 `review_meaning`을 내고 **사람이 확인해야 하는** 경우는?

① `source_id`를 S99로 적은 답  
② 발췌(quote)를 "숙박비는 20만원입니다."로 적은 답  
③ URL이 `ftp://`로 시작하는 출처  
④ 발췌는 원문 그대로인데 답 문장을 "출장 전체의 숙박비는 최대 12만원입니다."로 바꾼 답

<details>
<summary>정답 보기</summary>

**④** — 발췌는 원문에 있어서 통과하고, 답 문장 ≠ 발췌라 `review_meaning`이 나와요. "1박당 → 출장 전체" 단위 오류는 글자 비교로는 못 잡아요. ①은 `unknown_source`, ②는 `quote_not_found`, ③은 `invalid_url`로 코드가 잡아요.

</details>

### 6-Q4. 보류와 오류 (6-4)

6-4 `main.py --generate`에서 서버 연결이 끊겨 `httpx.HTTPError`가 났다. 결과 상태로 맞는 것은?

① `insufficient` — 답을 못 했으니까  
② `system_error` — 앱이 모델과 통신하지 못한 오류라서  
③ `invalid_output` — 응답이 비었으니까  
④ `answered` — 검색 결과는 있었으니까

<details>
<summary>정답 보기</summary>

**②** — `insufficient`는 "문서에 답이 없다"는 **정상 응답**이에요. 통신 실패는 `system_error`, 형식·검사 실패(`ValueError`)는 `invalid_output`으로 따로 기록해야 원인을 구분할 수 있어요.

</details>

### 6-Q5. 서술형 — `chunk_id` vs `document_id` 중복 제거 (6-1)

6-1에서 중복 제거를 `document_id`가 아니라 `chunk_id`로 한 이유를 복합 질문 예로 쓰세요.

<details>
<summary>예시 답안</summary>

같은 식비 문서(meal)라도 meal 0에는 "1일 3만원" 금액이, meal 60에는 "숙박비 한도와 합산하지 않는다"가 들어 있어요. `document_id`로 지우면 둘 중 하나만 남아서 복합 질문에 필요한 사실이 빠져요. 그래서 완전히 같은 청크(같은 `chunk_id`)가 반복된 것만 지워요. 딕셔너리 키는 한 번만 들어가니까 `{row["chunk_id"]: row for row in repeated}`로 쉽게 지울 수 있어요.

</details>

### 6-Q6. 서술형 — `--generate`에서 난 ValueError (6-2)

`uv run main.py --generate`에서 `ValueError: 보류 응답의 출처는 빈 배열로 반환`이 났다. 왜 났고, 이게 코드 버그가 아닌 이유를 쓰세요.

<details>
<summary>예시 답안</summary>

gemma3 4b가 `status`를 `insufficient`(보류)로 해 놓고 `citations`에 S1 같은 출처를 넣어 보냈어요. "모른다"면서 근거를 단 셈이라 앞뒤가 안 맞고, `validate_answer`가 "보류면 출처는 빈 배열" 규칙으로 막았어요. 검사 함수가 일부러 넣은 안전장치가 제대로 작동한 거라 버그가 아니에요. 작은 모델은 같은 질문에도 판단이 흔들려서, 모델 결과를 그대로 믿지 않고 형식·출처를 검사하는 단계가 필요해요.

</details>
