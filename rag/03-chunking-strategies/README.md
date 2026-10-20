# 3장. 청킹 — Chunk Size·Overlap, Fixed·Recursive·Token, 문서 구조 기반

> 2026-10-20 학습 기록. RAG 2일차 오전 수업입니다. 같은 travel 규정(148자)의 **승인 문장**("한도 초과 숙박은 예약 전에 담당 임원의 서면 승인을 받아야 합니다")이 청크 경계에서 끊기지 않게 하려면 어떻게 잘라야 하는지를, 크기·겹침 → 경계·길이 단위 → 문서 구조 → 같은 기준 비교 순서로 바꿔 가며 확인했습니다. 네 강의 실습 문제(q\_easy·q\_hard)를 모두 직접 풀어 통과했습니다.

## 학습 목표

- 청크 크기·겹침·이동 간격(`size − overlap`)을 원문 위치와 연결해 계산하고, 위치와 본문을 함께 반환하는 청커를 만든다.
- 고정 문자 분할과 Recursive(문장 우선) 분할의 경계를 비교하고, 모델 입력 한도는 문자가 아니라 **토큰**으로 재야 한다는 점을 확인한다.
- Markdown 제목으로 먼저 나누고 metadata를 끝까지 전달하며, 긴 절만 다시 나눈다.
- 근거 문장을 고정해 세 설정을 비교하고, 4장의 입력이 될 `chunks.json`(80/20, 28개)을 저장한다.

## 실습 파일

| 강 | 주제 | 실습 상태 |
| --- | --- | --- |
| 3-1 | Chunk Size와 Overlap — `windows` 청커, 저장량 비교, `checked_windows` | ✅ 완료 |
| 3-2 | Fixed / Recursive / Token 청킹 — E5 Tokenizer, Truncation, `measure_chunks` | ✅ 완료 |
| 3-3 | 한국어 / 문서 구조 기반 청킹 — Markdown 제목 분할, metadata 연결, `tagged_text` | ✅ 완료 |
| 3-4 | 청킹 전략 비교와 선택 — 근거 보존 비교, `chunks.json` 저장, `coverage_by_document` | ✅ 완료 |

수업에서 받은 `rag_day2` 키트(3·4장 8개 강의 + 공통 uv 환경)로 진행했습니다. 강마다 `main.py`를 실행하고 `q_easy.py`(빈칸)·`q_hard.py`(직접 구현)를 풀어 `✅ 정답이에요!`까지 확인했습니다. 키트 코드는 올리지 않고, **원본 ZIP과 비교해 직접 바꾸거나 추가한 부분**만 아래에 기록합니다.

## 전체 흐름

### 한 문장

**문서를 통째로 넣으면 필요 없는 내용까지 가고, 아무 데서나 자르면 조건 문장이 끊깁니다. 그래서 "어디서 자를지"와 "무엇으로 길이를 셀지"를 바꿔 가며 근거가 온전히 남는 방법을 비교합니다.**

### 왜 필요한가

```text
travel 148자를 80자씩 자르면
[0:80]   … 한도 초과 숙박은 예약 전에 담당 임원의 서면
[80:148] 승인을 받아야 합니다. …
         ↑ 앞 조각만 검색되면 "무엇을 서면으로?"를 알 수 없음
```

**비유:** 교과서를 낱장으로 찢어 검색 카드로 만드는 일과 같습니다. 문장 중간에서 찢으면 카드 한 장으로는 뜻이 안 통하고(Fixed), 단원 제목 없이 찢으면 무슨 단원 내용인지 모르고(3-3), 카드마다 "몇 쪽, 어느 책"을 적어 두지 않으면 원문으로 돌아갈 수 없습니다(metadata).

### 그림으로 보기

```text
documents.jsonl (12개 문서)
   │  json.loads + next(...)                                      ← 3-1~3-4 공통
   ▼
3-1  windows(text, 80, 20)          → [(0,80,…), (60,140,…), (120,148,…)]   직접 만든 청커
   ▼
3-2  chunk_documents(...)           → 고정 문자 청크 (단어 중간에서 끊김)
     splitter.split_text(...)       → ". " → " " → "" 순서로 문장 경계부터
     tokenizer("passage: " + text)  → 토큰 수 측정 (한도는 토큰 단위)
     from_huggingface_tokenizer     → 길이를 토큰으로 세는 splitter
   ▼
3-3  MarkdownHeaderTextSplitter     → ## 제목별 Document (section)
     metadata.update                → 원문 ID·상태·URL 연결
     splitter.split_documents       → 절 안에서만 다시 자르고 metadata 복사
   ▼
3-4  any(phrase in c["text"] …)     → 근거 문장 보존 True/False 비교
     write_text("chunks.json")      → 80/20 공통 기준 28개 ──→ 4장 임베딩 입력
```

### 강의 흐름

1. **3-1 크기와 겹침** — `json.loads`로 읽고 → 직접 만든 `windows`로 시작 위치를 `size − overlap`(60)씩 옮기며 80자씩 잘라 `(start, end, 본문)`으로 돌려줌 → 80/0·80/20·100/20 저장량 비교.
2. **3-2 경계와 길이 단위** — `chunk_documents`는 같은 원리의 **고정 문자 청커**(단어 중간에서도 끊김) → `splitter.split_text`는 `". "` → `" "` → `""` 순서로 **문장 경계부터** 잘라 승인 문장이 한 조각에 남음 → `tokenizer`로 `passage:`를 붙인 최종 **토큰 수**를 재고 → 30토큰으로 강제로 잘라 조건이 사라지는 것 확인.
3. **3-3 문서 구조** — `## 제목`으로 먼저 나눠 규정끼리 섞이지 않게 → `update`로 원문 정보를 붙이고 → `split_documents`로 각 절 **안에서만** 다시 자르며 metadata 복사 → 검색용 `제목 + 본문` 입력 구성.
4. **3-4 비교와 저장** — 근거 문장 3개를 고정하고 `any`로 한 청크에 통째로 들어 있는지 비교 → `write_text`로 80/20 `chunks.json`(28개) 저장. 최적이라서가 아니라 4장 비교의 공통 기준선.

## 핵심 이론

### 1. Chunk Size와 Overlap (3-1강)

| 값 | 의미 | 이번 설정 |
| --- | --- | --- |
| `size` | 한 조각의 최대 문자 수 | 80 |
| `overlap` | 인접 조각이 공유할 문자 수 | 20 |
| `size − overlap` | 시작 위치 이동 간격 | 60 |

- `range(0, 148, 60)` → start `0, 60, 120` / `end = min(start + 80, 148)` → `80, 140, 148`. 마지막에 `end == len(text)`이면 `break`.
- `text[start:end]`는 **start번 글자부터 end 바로 앞까지**(끝 위치 미포함). `[0:80]`은 0\~79번 글자 80개.
- `result.append((start, end, text[start:end]))` — 바깥 괄호는 `append` 호출, 안쪽 괄호는 세 값을 묶는 **튜플**. `append`는 값을 하나만 받아서 먼저 묶어 넘김. 위치를 함께 저장해야 나중에 원문의 어디였는지 다시 찾을 수 있음.

| 설정 | 청크 | 저장 문자 | 비고 |
| --- | --- | --- | --- |
| 80 / 0 | 2 | 148 | 승인 문장이 `서면` / `승인을`로 갈라짐 |
| 80 / 20 | 3 | 188 | 겹침 20자 × 2 = 40자 중복 |
| 100 / 20 | 2 | 168 | `[0:100]`에 승인 문장 전체 포함 |

- **겹침을 늘려도 조건 문장이 온전해진다는 보장은 없음.** 80/20의 두 번째 조각은 `숙박은`부터 시작해서 `한도 초과`가 빠짐.
- 겹침은 경계의 맥락을 지키지만 같은 글자를 반복 저장해서 저장량(나중엔 임베딩 비용)이 늘어남.
- `len(text)`는 문자 수(유니코드 코드 포인트)이지 토큰 수가 아님.

### 2. Fixed · Recursive · Token (3-2강)

| 방식 | 도구 | 결과 |
| --- | --- | --- |
| Fixed 80/20 | `rag_core.chunk_documents` | `… 서면` / `… 식비를 정` / `니다. …` — 단어 중간에서 끊김 |
| Recursive 80/20 | `RecursiveCharacterTextSplitter` | 금액·영수증 / 초과 승인·미승인 지출 / 비용 범위 — 문장 단위로 3조각 |
| Token 50/10 | `.from_huggingface_tokenizer(tokenizer, …)` | 3문장(51토큰) / 2문장(33토큰) |

- Recursive는 `separators=[". ", " ", ""]` 순서로 **큰 경계부터** 시도하고, 80자를 넘는 부분만 다음 구분자로 더 잘게 나눔. `keep_separator="end"`는 구분자를 앞 조각 끝에 남김.
- `chunk_overlap=20`은 **목표값**. 이 샘플은 넘길 문장 조각이 20자 이하가 아니라서 실제 겹침이 없었음 → 설정값만 믿지 말고 결과를 읽어 확인.
- 3-2 폴더에 `rag_core.py`가 있는 이유: Fixed 청커(`chunk_documents`)를 다시 짜지 않고 수업 공통 함수 모음에서 가져다 쓰기 위해서. 3-2에서 실제로 쓰는 건 이 함수 하나.
- E5 Tokenizer(`intfloat/multilingual-e5-small`)로 `"passage: " + text`의 `input_ids` 길이를 재면 54자→32, 70자→40, 24자→17토큰. **문자÷토큰 = 1.69 · 1.75 · 1.41**로 일정하지 않음 → 한도는 실제 Tokenizer로 재야 함.
- 토큰 기준 50으로 잘라도 `passage:` + 특수 토큰을 붙인 **최종 입력은 51**토큰 → 분할 후 최종 입력을 다시 측정.
- "50이 80보다 작으니 더 잘게 잘린다"가 아님. 이번엔 **토큰 50 조각이 문자 80 조각보다 문장을 더 많이** 담음. 최대 토큰도 fixed 45 vs token 51 — 작다고 조건이 더 잘 보존되는 건 아님.
- **Truncation**: `max_length=30, truncation=True`로 79토큰 입력을 자르고 `decode`로 다시 읽으면 영수증 문장까지만 남고 승인 문장이 사라짐. **오류 없이 조용히** 잘림.

### 3. 문서 구조 기반 청킹 (3-3강)

education + remote 두 규정을 한 파일로 받은 상황에서 5단계로 처리합니다.

| 단계 | 하는 일 | 안 하면 생기는 문제 |
| --- | --- | --- |
| ① 제목 붙이기 | `## 교육비 지원\n본문` 형식으로 합침 | 어디서 주제가 바뀌는지 모름 |
| ② 제목으로 자르기 | `MarkdownHeaderTextSplitter(headers_to_split_on=[("##", "section")])` → Document 2개, 제목은 `metadata["section"]` | 교육비 끝 + 재택근무 첫 문장이 한 조각에 섞임 |
| ③ 원문 정보 붙이기 | `by_title`로 원래 문서를 찾아 `metadata.update(...)`, `document_id` 추가 | splitter는 제목만 알아서 출처 표시·현행 필터가 안 됨 |
| ④ 긴 것만 다시 자르기 | `splitter.split_documents(sections)` → education 3, remote 2 | 조각이 너무 길거나 경계를 넘어 섞임 |
| ⑤ 제목 + 본문 | `embedding_text = metadata["title"] + "\n" + page_content` | "무슨 신청인지" 모르는 조각은 검색이 약함 |

- `page_content` = Document의 **본문(str)**, `metadata` = 출처·제목·상태(dict). metadata는 `["키"]`로, 본문은 `piece.page_content`로 꺼냄.
- `split_text`는 **문자열**을 받고, `split_documents`는 **Document**를 받아 자르면서 metadata도 각 조각에 복사.
- Recursive는 두 덩어리 모두에 적용하지만 80자를 넘는 부분만 쪼개고, 크기·겹침은 각 절 **안에서만** 적용(절 사이엔 겹침 없음).
- **metadata의 제목은 임베딩에 자동으로 들어가지 않음.** ⑤는 임베딩 직전에 모델에 넣을 문자열을 정하는 단계이고 `page_content`는 바꾸지 않음. 수업 공통 `chunks.json`은 3-4의 고정 80/20이고 4장은 `"passage: " + text`만 쓰므로, 제목 붙이기는 별도 실험으로 비교.
- "개인 취미 강좌의 지원 여부는 규정되어 있지 않습니다" 같은 **예외·미규정 문장도 원문**. 빠지면 "취미 강좌도 30만원 지원" 같은 틀린 답으로 이어짐.
- 표는 행을 나눌 때 열 이름을 붙이고, 번호 목록은 상위 제목과 함께 둠. 제목 기반 분할은 Semantic Chunking(임베딩 유사도로 경계 찾기)과 다른 방법.

### 4. 청킹 전략 비교와 저장 (3-4강)

- 비교 기준 고정: travel 앞 세 문장(금액 28자, 영수증 24자, 승인 38자). 알고리즘은 Fixed로 두고 size·overlap만 변경.

| 설정 | 전체 청크 | travel 청크 | travel 저장 문자 | 근거 보존 (금액, 영수증, 승인) |
| --- | --- | --- | --- | --- |
| 80 / 0 | 24 | 2 | 148 | T, T, **F** |
| 80 / 20 | 28 | 3 | 188 | T, T, **F** |
| 100 / 20 | 22 | 2 | 168 | T, T, T |

- `any(phrase in c["text"] for c in selected)` — 문장 전체가 **어느 한 청크 안에** 있으면 True. 검색 성공이나 답변 정확도가 아님.
- 80/20에서 승인 문장은 원문 `[54:92]`. `0:80`은 `서면`에서 끊기고 `60:140`은 `숙박은`부터라 **어느 청크에도 통째로 없음**.
- 개선 후보: 크기 늘리기 / 문장 경계 우선 분할 / 검색 후 인접 청크도 가져오기.
- **80/20을 공통 기준으로 `chunks.json`(28개) 저장.** `chunk_id` = `문서ID:본문해시12자리:size:overlap:번호`(예: `leave:5a1ba9d2dd70:80:20:0`). 청킹이 바뀌면 임베딩·인덱스도 다시 만들어야 하고, 대안 설정은 `chunks_candidate.json`처럼 따로 저장.
- `coverage_by_document`: 문서별 `(start, end)` 구간을 모아 빠진 구간이 없는지, 마지막 `end`가 원문 길이와 같은지 확인. 구버전(travel-old)도 저장돼 있고, 현행 선택은 검색 단계의 필터가 담당.

## 질문과 새로 알게 된 점

### 흐름 한 줄

`json.loads`로 읽고(3-1\~3-4 공통) → `windows`(3-1)·`chunk_documents`(3-2, 3-4)·`split_text`(3-2, 3-3)·`split_documents`(3-3)로 자르고 → `tokenizer`로 재고(3-2) → `any`로 비교하고(3-4) → `write_text`로 `chunks.json`을 남긴다(3-4).

### 퀴즈 3-2 `measure_chunks` — for문 버전과 리스트 컴프리헨션 버전

결과는 같고 쓰는 방식만 다릅니다.

```python
# for문 버전 — 중간값을 print로 찍어 보기 쉬움
def measure_chunks(pieces, tokenizer):
    rows = []
    for text in pieces:
        chars = len(text)
        input_tokens = len(tokenizer("passage: " + text)["input_ids"])
        rows.append({"text": text, "chars": chars, "input_tokens": input_tokens})
    return rows

# 리스트 컴프리헨션 버전 — 짧지만 안에 계산이 많으면 읽기 어려움
def measure_chunks(pieces, tokenizer):
    return [{"text": text, "chars": len(text),
             "input_tokens": len(tokenizer("passage: " + text)["input_ids"])}
            for text in pieces]
```

| | for문 버전 | 리스트 컴프리헨션 버전 |
| --- | --- | --- |
| 빈 리스트 | `rows = []`로 직접 만듦 | `[ ... ]`가 알아서 만듦 |
| 하나씩 넣기 | `rows.append({...})` | 맨 앞의 `{...}`가 자동으로 들어감 |
| 반환 | 마지막에 `return rows` | 만든 리스트를 바로 `return` |
| 중간 변수 | `chars`, `input_tokens`에 먼저 담음 | dict 안에서 바로 계산 |

처음 직접 쓴 컴프리헨션에서 고친 4곳:

| 처음 쓴 코드 | 문제 | 고친 코드 |
| --- | --- | --- |
| 맨 앞에 `return` 없음 | 리스트를 만들고 버려서 `None` 반환 | `return [...]` |
| `"chars": chars` | 컴프리헨션엔 중간 변수가 없음 → `NameError` | `"chars": len(text)` |
| `"passage: " text` | 문자열 사이 `+` 누락 → `SyntaxError` | `"passage: " + text` |
| `text["input_ids"]` | `["input_ids"]`는 **tokenizer 결과**에 붙임 | `tokenizer(...)["input_ids"]` |

- 반환값은 **dict**여야 함. f-string을 쓰면 결과가 문자열(str)이라 `r["input_tokens"]`처럼 값을 꺼낼 수 없음. f-string은 화면 출력용으로만.

### 퀴즈 3-3 `tagged_text`에서 고친 것

| 처음 쓴 코드 | 문제 | 고친 코드 |
| --- | --- | --- |
| `piece.metadata("title")` | metadata는 dict라 소괄호가 아니라 대괄호 → `TypeError` | `piece.metadata["title"]` |
| `f"{id} {title}…"` | 문제 형식 `[ID]`의 대괄호 누락 | `f"[{did}] {title}\n…"` |
| `piece.metadata(page_content)` | 본문은 metadata 안이 아니라 따로 있음 | `piece.page_content` |

- `did`는 **d**ocument **id**의 줄임말일 뿐. `id`는 Python 내장 함수 이름이라 `doc_id`처럼 다른 이름이 더 안전.

### 퀴즈 3-4 `setdefault`

```python
result.setdefault(c["document_id"], []).append((c["start"], c["end"]))

# if문으로 풀면
if c["document_id"] not in result:
    result[c["document_id"]] = []
result[c["document_id"]].append((c["start"], c["end"]))
```

- `dict.setdefault(키, 기본값)`은 dict 기본 메서드(import 불필요). 키가 없으면 기본값을 넣고 돌려주고, 있으면 기존 값을 돌려줌.
- 1-2강의 `defaultdict(list)`와 같은 일을 함(처음에 "없는 키는 빈 리스트"로 정해 두는 방식).

### 함수별 입력 → 출력 정리

| 강 | 함수 / 클래스 | 입력 → 출력 |
| --- | --- | --- |
| 공통 | `json.loads(line)` | JSONL 한 줄 → 문서 dict |
| 3-1 | `windows(text, size, overlap)` | 문자열 → `[(start, end, 본문), …]` |
| 3-2 | `chunk_documents(docs, size, overlap)` | 문서 리스트 → 청크 dict 리스트 |
| 3-2 | `splitter.split_text(문자열)` | 문자열 → 문자열 리스트 |
| 3-2 | `tokenizer("passage: " + text)["input_ids"]` | 문자열 → 토큰 번호 리스트 |
| 3-2 | `tokenizer.decode(ids, skip_special_tokens=True)` | 토큰 번호 → 문자열 |
| 3-3 | `header_splitter.split_text(markdown)` | 문자열 → `Document` 리스트 |
| 3-3 | `splitter.split_documents(sections)` | `Document` 리스트 → 더 작은 `Document` 리스트(metadata 복사) |
| 3-4 | `any(phrase in c["text"] for c in selected)` | → True / False |
| 3-4 | `Path("chunks.json").write_text(json.dumps(...))` | 청크 리스트 → 파일 |

## 실습 코드에서 직접 바꾼 점

원본 키트(`rag_day2` ZIP)와 비교한 내용입니다. 키트 코드 자체는 올리지 않습니다.

### 공통

- `pyproject.toml`에 `printsection>=0.2.0` 추가(`uv add printsection`). 네 강의 `main.py` 모두 `from printsection import print_section`을 넣고 구역마다 `print_section("1번")`, `print_section("2번")`…으로 출력을 나눔.

### 3-1 `main.py`

- 원본 `windows` 함수를 주석으로 남겨 두고, 그 아래에 **직접 다시 작성**함.
- 추가한 주석: `# step을 지정. size - overlap`
- `q_easy.py`는 조건을 `0 <= overlap < size-overlap`으로 써서 통과했지만, 문제의 허용 범위는 `0 <= overlap < size`(q\_hard에서는 이렇게 씀). 예를 들어 80/50처럼 올바른 입력도 `50 < 30`이 거짓이라 오류로 막힘 → 테스트 값(100/20, 80/80, 80/−1)으로는 드러나지 않은 차이.

### 3-2 `main.py`에 추가한 주석

| 위치 | 추가한 주석 |
| --- | --- |
| `RecursiveCharacterTextSplitter(` | `# 청크사이즈, 오버랩지정.` |
| `separators=…, keep_separator="end"` | `# sep에 우선순위 기준넣기.` / `# 짤릴때 ". "이 없어지기 떄문에 구분자를 끝(end)에 유지.` |
| `split_text(...)` | `# recursive~에 있는거.` |
| `AutoTokenizer.from_pretrained(...)` | `# 문자를 벡터로 바꿔주는 모델. pretrained 사전에 훈련된.` / `# cache_dir 지정하는 이유: 한번 받은거면 불러오기위해.` |
| `for text in recursive:` | `# 청킹한게 하나씩들어감.` |
| `tokenizer("passage: " + text …)` | `#토큰화 해서 어떤 값(ids)로 바꾸는 과정.` / `# text 들어갈때마다 passage입력.(임베딩모델이 이해하기 위해) + 나중에 llm넣을때도.` / `# 학습할때 저렇게 데이터가 구축되어서(passage + ~)` / `# 다른모델은 passage가 아닐수도있음. HGface안의 model config에서 확인가능` |
| `print(ids)` 추가 | `# 쪼갠 문장들이 벡터들로 바뀜. 각각의 값들이 토큰임.` / `# max 토큰고려해서 짤라야할수도있음.` |
| 토큰 분할 앞 | `# 문자열보단 쪼갤때부터 토큰기준으로 쪼개는게 맞음.` / `#청킹을 할건데, 문자열기준이 아니라 토큰기준으로.` |
| `total = len(tokenizer(...))` | `# passage붙으면 토큰수 바뀌는지 확인하기 위해 len 체킹` |
| Truncation 앞 | `#임베딩같은경우 벡터차원이 정해져있음. 512 등등 맞게 짤라줘야할수도있음.` |

- `q_hard.py`: for문 버전을 주석으로 남기고 리스트 컴프리헨션 버전으로 제출.

### 3-3 `main.py`에 추가한 주석

| 위치 | 추가한 주석 |
| --- | --- |
| `print(markdown)` | `# 일종의 markdown문서를 만든것.` |
| `print_section("2번")` | `#카멜형태(보통 클래스선언할떄) or _로 구분` — `MarkdownHeaderTextSplitter`(클래스) vs `header_splitter`(변수) |
| `header_splitter = …` | `# 헤더스플리터라는 객체를 생성해서 >>` |
| 1차 분할 반복문 끝 | `# 청킹을할때도 metadata를 끌고와야됨.` |

### 3-4

- `print_section`만 추가. 퀴즈 두 개 모두 `setdefault`로 작성.

## 확인 문제

강의 내용을 바탕으로 직접 만든 복습 문제입니다. 객관식 4문제, 서술형 2문제이고 각 문제 바로 아래에 정답이 있습니다.

### 3-Q1. 구간 계산 (3-1)

길이 148자인 travel 본문을 size=80, overlap=20으로 자르면 구간은?

① `[0:80]`, `[80:148]`  
② `[0:80]`, `[80:160]`  
③ `[0:60]`, `[60:120]`, `[120:148]`  
④ `[0:80]`, `[60:140]`, `[120:148]`

<details>
<summary>정답 보기</summary>

**④** — 이동 간격 80 − 20 = 60이라 시작 위치가 0, 60, 120. 끝은 `min(start + 80, 148)`. ①은 overlap=0일 때.

</details>

### 3-Q2. Recursive splitter (3-2)

옳은 설명은?

① `chunk_overlap=20`이면 인접 청크가 항상 정확히 20자씩 겹친다  
② 큰 구분자(`". "`)부터 시도하고, 너무 긴 부분만 더 작은 구분자(`" "`, `""`)로 나눈다  
③ 임베딩 유사도를 계산해 의미가 바뀌는 지점에서 자른다  
④ 토큰 수를 기준으로만 자를 수 있다

<details>
<summary>정답 보기</summary>

**②** — ①: overlap은 목표값이고 이번 결과엔 겹침이 없었음. ③: Semantic Chunking 설명. ④: 기본은 문자 길이이고 `from_huggingface_tokenizer`로 길이 함수만 토큰으로 바꿀 수 있음.

</details>

### 3-Q3. Truncation (3-2)

`max_length=30, truncation=True`로 travel 전체를 넣으면?

① 길이 초과 오류가 나서 실행이 멈춘다  
② 넘친 부분이 자동으로 다음 청크로 넘어간다  
③ 오류 없이 뒤쪽 토큰이 잘려, '서면 승인' 조건이 모델 입력과 임베딩에서 빠진다  
④ 넘친 부분이 요약되어 30토큰 안에 들어간다

<details>
<summary>정답 보기</summary>

**③** — 79토큰이 30토큰으로 잘려 영수증 문장까지만 남음. 조용히 잘리므로 오류가 없다고 전부 처리된 게 아님.

</details>

### 3-Q4. 근거 보존 True의 의미 (3-4)

'근거 보존 = True'가 뜻하는 것은?

① 그 근거 문장 전체가 어느 한 청크 안에 온전히 들어 있다  
② 검색기가 그 청크를 상위 결과로 찾았다  
③ 그 설정으로 만든 답변이 정확하다  
④ 그 설정이 최적의 청킹 설정이다

<details>
<summary>정답 보기</summary>

**①** — `any(...)`는 문장이 한 청크 안에 있는지만 검사. 그래서 100/20이 더 나았는데도 공통 기준은 80/20으로 저장했음.

</details>

### 3-Q5. 서술형 — 승인 문장 잘림 개선 (3-4)

80/20에서 승인 문장이 잘린다. 개선 방법 하나를 골라 이유와 단점을 쓰세요.

<details>
<summary>예시 답안</summary>

후보: ① size 100 ② 문장 경계 우선 Recursive ③ 검색 후 인접 청크 함께 가져오기.
②를 고른다면: 규정은 문장 하나가 조건 하나라서 문장이 통째로 남는 게 중요함. 단점은 청크 길이가 들쭉날쭉하고, 소수점·약어·목록이 있으면 `". "`가 문장 끝이 아닐 수 있음. ①은 간단하지만 관련 없는 내용이 같이 들어가고, ③은 원문을 그대로 두지만 Context 예산을 더 씀. 어느 방법이든 4장 이후 같은 질문으로 검색 결과를 비교해야 함.

</details>

### 3-Q6. 서술형 — 제목을 metadata에 둘 때 vs 본문에 붙일 때 (3-3)

`metadata["section"]`에 저장하는 것과 `embedding_text = 제목 + 본문`으로 만드는 것은 어떻게 다른가요?

<details>
<summary>예시 답안</summary>

metadata의 제목은 화면 표시·원문 구분·필터에 쓰이지만 **임베딩 입력에는 자동으로 들어가지 않음**. `embedding_text`로 제목을 붙이면 제목 표현도 검색 벡터에 반영됨. "수강 완료 후 수료증과 영수증을 제출합니다"처럼 본문만으로 주제를 알기 어려운 청크에 필요하고, 붙일지 말지는 검색 결과를 비교해서 정함.

</details>
