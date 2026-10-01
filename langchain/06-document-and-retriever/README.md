# 6장. Document · Retriever · 기본 retrieval chain

> 2026-09-30(6-1)·2026-10-01(6-2, 6-3) 학습 기록. 외부 자료를 Document로 담고, 질문에 맞는 문서를 찾아 목록으로 돌려주고, 찾은 문서를 context로 Prompt에 넣어 문서 기반 답변까지 연결하는 흐름을 정리했습니다.

## 학습 목표

- 외부 자료를 `Document(page_content=..., metadata={...})` 모양으로 담고, 같은 의미의 metadata는 같은 키로 저장한다.
- Retriever의 계약 `str → list[Document]`를 지키고, 0건도 빈 목록이라는 정상 결과로 다룬다.
- 키워드 점수 → 0점 제외 → 점수순(동점은 원래 순서) → 상위 k개 순서로 결정적인 검색을 만든다.
- Prompt에는 문서 목록이 아니라 formatter가 만든 context 문자열을 넣고, 원본 목록은 출처 확인용으로 함께 남긴다.
- 청킹·임베딩·Vector DB는 후속 RAG 과목 범위라는 경계를 구분한다.

## 실습 파일

| 강 | 주제 | 실습 상태 |
| --- | --- | --- |
| 6-1 | Document 구조와 metadata 활용 | 📘 이론 정리 |
| 6-2 | Retriever 인터페이스와 검색 질의 | 📘 이론 정리 |
| 6-3 | 기본 retrieval chain과 RAG 과목 경계 | 📘 이론 정리 |

실습 노트북은 이번 기록에 포함하지 않았습니다. 6\~10장은 이론 분량이 많아, 실습은 10장 통합 실습(`starter.py`) 하나로 정리했습니다. 아래 확인 문제는 API 없이 풀 수 있는 복습용 문제입니다.

## 전체 흐름

1. **6-1 담기** — 원본 문장을 `Document(page_content=..., metadata={...})`로 변환. `document_id`·`title`·`source`·`keywords` 같은 metadata 키를 모든 문서에 **같은 이름으로** 저장. formatter로 `[ID | 제목 | 출처]\n본문` 문자열 생성.
2. **6-2 찾기** — 질의 문자열을 받아 metadata `keywords`가 질의에 몇 개 포함됐는지로 점수 계산 → 0점 제외 → 점수 높은 순(동점은 원래 순서) → `max_results`개 반환. `source_filter`로 후보를 먼저 좁힐 수 있음. `RunnableLambda`로 감싸 `retriever.invoke(질의)`.
3. **6-3 근거로 답하기** — 검색 결과를 context 문자열로 바꿔 Prompt에 넣고 Model이 답변. `RunnablePassthrough.assign`으로 `question`·`documents`·`context`·`answer`를 한 dict에 남김.

```text
6-1   원본 문장 ──→ Document
                    ├─ page_content : 실제 본문 (str)       ← 답변의 근거
                    └─ metadata     : document_id · title · source · keywords (dict) ← 식별·표시·검색 단서

6-2   질의 str ─→ [source_filter] ─→ keyword_score ─→ 0점 제외 ─→ 정렬(-점수, 원래 순서) ─→ 상위 max_results
                                                                                         └→ list[Document] (없으면 [])

6-3   질문 str
        │  prepare_step = RunnableLambda(retrieve_and_prepare)
        ▼
      {question, documents: list[Document], context: str}
        │  RunnablePassthrough.assign(answer = prompt | model | StrOutputParser())
        ▼
      {question, documents, context, answer}        ← OpenAI 호출은 answer 만들 때 1회
```

3\~4장 → 6장 연결고리: 6-2의 Retriever는 3장의 Runnable 계약(`invoke`)을 따르고, 6-3의 체인은 4-2의 `RunnableLambda | RunnablePassthrough.assign(...)` 구조를 그대로 씁니다. 4-2의 `clean_question` 자리에 이번엔 `answer`가 추가될 뿐입니다.

## 핵심 이론

### 1. Document 구조와 metadata 활용 (6-1강)

| 영역 | 자료형 | 저장하는 값 | 예시 |
| --- | --- | --- | --- |
| `page_content` | `str` | 문서의 실제 본문 (Prompt 참고 문맥이 됨) | `"Retriever는 ... 검색 인터페이스입니다."` |
| `metadata` | `dict` | 본문을 설명하는 부가 정보 | ID, 제목, 출처, 검색 키워드 |

```python
from langchain_core.documents import Document

document = Document(
    page_content="LCEL은 Prompt, Model, Parser 같은 Runnable 단계를 pipe 연산자로 연결하는 표현식입니다.",
    metadata={
        "document_id": "doc-001",          # 중복 없는 식별자
        "title": "LCEL 기초",              # 사람이 읽는 제목
        "source": "langchain_intro.md",    # 원본 파일/시스템
        "keywords": ["lcel", "pipe", "runnable"],   # 6-2 단순 검색 단서
    },
)
document.page_content              # 본문 → 점 표기법
document.metadata["document_id"]   # 'doc-001' → dict 키
```

- `Document(...)`는 dict가 아니라 **Document 객체**를 만듭니다.
- metadata 키 이름은 앱이 정하지만, **같은 의미는 모든 문서에서 같은 키**로(`source`/`file`/`origin` 섞지 않기). 그래야 formatter 하나로 처리됩니다.
- 반드시 있는 키는 `metadata["title"]`, 없을 수도 있는 키는 `metadata.get("author", "작성자 없음")`.
- 본문에 `"출처: ..."`를 붙이지 말고 출처는 `metadata["source"]`로 분리합니다.
- 여러 문서는 `Document`를 여러 개 만들어 리스트에 담습니다: `documents[0].metadata["title"]`.
- metadata는 검색 정확도를 자동으로 높여 주는 것이 아니라, 다음 단계가 읽을 필드를 일관되게 저장하는 것입니다.

**formatter** — Document 자체는 바꾸지 않고, 표시·Prompt용 문자열을 새로 만듭니다.

```python
def format_document(document: Document) -> str:
    document_id = str(document.metadata.get("document_id", "ID 없음"))
    title = str(document.metadata.get("title", "제목 없음"))
    source = str(document.metadata.get("source", "출처 없음"))
    return f"[{document_id} | {title} | {source}]\n{document.page_content}"

def format_documents(documents: list[Document]) -> str:
    return "\n\n".join(format_document(d) for d in documents)   # 빈 줄로 문서 경계
```

| 자주 나는 오류 | 원인 → 해결 |
| --- | --- |
| import 경로 혼동 | `from langchain_core.documents import Document` |
| `page_content`에 리스트 | 본문은 문자열 하나, 여러 문서는 Document 여러 개 |
| `metadata`에 문자열 | 키-값 dict로 |
| 없는 키를 대괄호로 → `KeyError` | 선택 필드는 `.get(키, 대체값)` |
| 본문과 출처를 한 문자열에 | 본문 `page_content`, 출처 `metadata["source"]` |
| 문서마다 다른 키 이름 | metadata 규칙을 먼저 정하기 |

### 2. Retriever 인터페이스와 검색 질의 (6-2강)

Retriever는 답변을 쓰는 Model이 아니라, 질문과 관련된 자료를 **찾아 다음 단계로 넘기는** 역할입니다.

| 구분 | 값 | 자료형 |
| --- | --- | --- |
| 입력 | `"Retriever는 어떤 역할을 하나요?"` | `str` |
| 출력 | 관련 문서 목록 (없으면 `[]`) | `list[Document]` |

한 건이어도 목록으로 반환하면 0건·1건·여러 건을 같은 코드로 다룰 수 있습니다.

**키워드 점수** = metadata `keywords` 중 (casefold한) 질의에 **포함된** 개수.

```python
def keyword_score(query: str, document: Document) -> int:
    normalized_query = query.casefold()                      # 대소문자 무시
    keywords = document.metadata.get("keywords", [])         # 없으면 0점
    return sum(1 for k in keywords if str(k).casefold() in normalized_query)
```

| 점수 | 처리 |
| --- | --- |
| 0 | 관련 없음 → 제외 |
| 1 이상 | 후보 |
| 높을수록 | 앞에 배치 |

**검색 함수** — 순서: (source filter) → 점수 → 0점 제외 → 정렬 → 상위 `max_results`.

```python
def search_documents(query, documents, max_results=2):
    if not query.strip():
        return []                                            # 빈 질의 → 빈 목록
    scored = []
    for index, document in enumerate(documents):
        score = keyword_score(query, document)
        if score > 0:
            scored.append((score, index, document))          # 원래 위치도 저장
    scored.sort(key=lambda item: (-item[0], item[1]))        # 점수 내림차순, 동점은 원래 순서
    return [document for _s, _i, document in scored[:max_results]]
```

- `(점수, 원래 위치, 문서)`를 함께 저장하는 이유: 동점일 때 결과 순서가 흔들리지 않게(결정적).
- `max_results`를 줄이면 Prompt에 들어갈 문서가 줄지만, 검색 품질이 자동으로 좋아지는 건 아닙니다.
- `source_filter`가 있으면 `document.metadata.get("source") != source_filter`인 문서를 점수 계산 **전에** 제외. `None`이면 전체 검색. 필터 뒤 빈 목록은 **정상 결과**입니다 (권한 검사 기능 아님).

**Runnable Retriever**

```python
def build_keyword_retriever(documents):
    def retrieve(query: str) -> list[Document]:
        return search_documents(query, documents)            # 바깥 documents 사용
    return RunnableLambda(retrieve)

retriever = build_keyword_retriever(documents)
results = retriever.invoke("Retriever는 어떤 역할을 하나요?")   # 1건, doc-003
```

- 검색 규칙은 `search_documents()`가 정하고, `RunnableLambda`는 `invoke()`와 `|`를 쓸 수 있게 감쌀 뿐입니다.
- 이것은 `BaseRetriever`를 상속한 정식 구현이 아니라 `str → list[Document]` 계약을 연습하는 Runnable입니다. Vector Store Retriever는 후속 RAG 과정.
- 키워드 검색은 **문자열 포함 여부**만 봅니다. 뜻이 비슷한 다른 단어는 못 찾습니다 (의미 기반 검색 아님).

완성 실습 결과 요약: "Retriever는 어떤 역할을 하나요?" → doc-003 · "API Key와 환경변수는..." → doc-002 · "메모리는 어디에 저장하나요?" → 0건 · source filter `retriever_note.md` → doc-003만.

| 자주 나는 오류 | 원인 → 해결 |
| --- | --- |
| Retriever에 dict 전달 | 입력 계약은 문자열: `retriever.invoke("...")` |
| 결과를 Document 한 개로 착각 | `list[Document]` → `results[0].page_content` |
| 결과가 없는데 `results[0]` | `if results:`로 먼저 확인 |
| 대소문자 때문에 결과가 다름 | 질의·키워드 모두 `casefold()` |
| 0점 문서도 반환 | `score > 0`인 문서만 후보 |
| 필터 후 빈 결과를 오류로 판단 | 빈 목록은 유효한 결과 |
| 키워드 검색을 의미 검색이라 설명 | 포함 여부만 확인 |

### 3. 기본 retrieval chain과 RAG 과목 경계 (6-3강)

| 단계 | 입력 | 출력 |
| --- | --- | --- |
| 1. 검색 | 질문 `str` | `list[Document]` |
| 2. context 구성 | 검색된 문서 목록 | 문서 ID·제목·본문이 있는 `str` |
| 3. Prompt 구성 | `question` + `context` | 역할별 메시지 (`PromptValue`) |
| 4. Model 호출 | 메시지 | `AIMessage` |
| 5. Parser | `AIMessage` | 답변 `str` |

자료형 흐름: `str → list[Document] → dict → PromptValue → AIMessage → str`

**context formatter (6-3판)** — 문서가 없으면 빈 문자열 대신 **분명한 문구**.

```python
def format_documents(documents):
    if not documents:
        return "검색된 문서가 없습니다."
    return "\n\n".join(
        f"[{d.metadata['document_id']} | {d.metadata['title']}]\n{d.page_content}"
        for d in documents
    )
```

**Prompt 규칙** (system): 검색 문서만 사용해 두 문장 이하로 답하기 · 문서가 없으면 `'제공된 문서에서 확인할 수 없습니다.'`라고만 답하기 · 답변 끝에 `[근거: 문서 ID]` 표시. human 메시지: `"검색 문서:\n{context}\n\n질문:{question}"`.

**연결**

```python
def retrieve_and_prepare(question: str) -> dict:
    retrieved = search_documents(question, documents)
    return {
        "question": question,                   # Prompt 변수
        "documents": retrieved,                 # 원본 목록 (근거 ID 확인용)
        "context": format_documents(retrieved), # Prompt 변수
    }

answer_chain = prompt | model | StrOutputParser()
retrieval_chain = RunnableLambda(retrieve_and_prepare) | RunnablePassthrough.assign(answer=answer_chain)
# 결과: {"question", "documents", "context", "answer"}
```

- `documents`(원본 목록)와 `context`(문자열)를 **둘 다** 유지: context는 Model용, documents는 어떤 문서가 검색됐는지·metadata 확인용.
- Prompt 변수 `{question}`, `{context}`와 앞 단계 dict의 키 이름이 같아야 합니다 (3-1, 3-3과 같은 규칙).
- `assign`을 썼기 때문에 답변만이 아니라 검색 결과와 context도 함께 남습니다.
- 키워드 검색은 로컬 Python, OpenAI 호출은 답변 생성에서 **1회**.
- 근거 ID 표시나 "문서에서 확인할 수 없음" 규칙이 잘못된 답변을 **완전히** 막지는 못합니다. 표시된 ID가 실제 `result["documents"]`에 있는지 확인하고, 테스트·평가가 필요합니다.
- API Key는 코드에 적지 않고 `.env`에서 읽으며, 없으면 `ChatOpenAI`를 만들기 **전에** 안내하고 종료.

**과목 경계**

| 이번 LangChain 6장 | 후속 RAG 과목 |
| --- | --- |
| `Document`의 `page_content`·`metadata` | 청킹 (긴 문서 나누기) |
| 질의 문자열을 받는 작은 Retriever | 임베딩 (텍스트 → 벡터) |
| 검색 결과 → context 문자열 | Vector DB 저장·검색 |
| Retriever → Prompt → Model → Parser 연결 | 검색 방식·파라미터 조정, reranking |
| 문서 ID를 포함한 기본 문서 Q&A | 검색 품질·답변 품질 평가 |

한 번에 다 넣으면 결과가 틀렸을 때 어느 단계가 원인인지 알기 어렵기 때문에, 고정 문서 + 결정적 검색으로 **데이터 흐름**부터 익힙니다. 이번 키워드 Retriever는 실제 RAG의 최종 검색기가 아닙니다.

| 자주 나는 오류 | 원인 → 해결 |
| --- | --- |
| Document 목록을 `{context}`에 그대로 | formatter 문자열을 넣고 원본은 `documents`에 |
| 질문/context 키 이름 불일치 | Prompt 변수와 dict 키 맞추기 |
| 검색 결과 없음에 빈 문자열 | `"검색된 문서가 없습니다."` |
| API Key를 코드에 직접 입력 | `.env`의 `OPENAI_API_KEY` |
| Key가 없는데 Model부터 생성 | 환경변수 먼저 확인 |
| 검색·Model 호출 횟수 혼동 | 검색은 로컬, OpenAI는 1회 |
| 근거 ID가 있으면 정확하다고 판단 | 실제 `documents`와 대조 |
| 이번 체인에 Vector DB·임베딩 추가 | 후속 RAG 범위 |

## 확인 문제

모두 API 없이 풀 수 있습니다. `from langchain_core.documents import Document`와 `from langchain_core.runnables import RunnableLambda, RunnablePassthrough`가 되어 있고, 6-2의 `keyword_score`, `search_documents`가 위 요약의 코드 그대로라고 가정합니다. 각 문제 바로 아래에 정답과 해설이 있습니다. 먼저 풀어 본 뒤 확인하세요.

### 6-Q1. Document 만들기 오류 찾기 (6-1)

각 줄이 잘못된 이유를 쓰고 고치세요.

```python
d1 = Document(page_content=["LCEL 설명", "Runnable 설명"])      # (가)
d2 = Document(page_content="LCEL 설명", metadata="lcel.md")      # (나)
d3 = Document(page_content="LCEL 설명", metadata={"source": "lcel.md"})
print(d3.metadata["title"])                                      # (다)
```

> 힌트: `page_content`와 `metadata`에 각각 어떤 자료형이 들어가나요? (다)는 없는 키입니다.

<details>
<summary>정답 보기</summary>

(가) `page_content`는 본문 **문자열 하나**입니다. 두 본문이면 Document를 두 개 만들어 리스트에 담습니다: `[Document(page_content="LCEL 설명"), Document(page_content="Runnable 설명")]`. (나) `metadata`는 **dict**여야 합니다: `metadata={"source": "lcel.md"}`. (다) `title` 키가 없어 `KeyError`. 선택 필드는 `d3.metadata.get("title", "제목 없음")`.

</details>

### 6-Q2. formatter 출력 예측 (6-1)

6-1의 `format_document`, `format_documents`를 사용합니다. 출력을 정확히 쓰세요.

```python
docs = [
    Document(page_content="Parser는 모델 응답을 바꿉니다.",
             metadata={"document_id": "doc-010", "title": "Parser", "source": "parser.md"}),
    Document(page_content="FAQ 본문입니다.",
             metadata={"document_id": "doc-011", "source": "faq.md"}),
]
print(format_documents(docs))
```

> 힌트: 두 번째 문서에는 `title`이 없습니다. 문서 사이 구분자는 무엇이었나요?

<details>
<summary>정답 보기</summary>

```text
[doc-010 | Parser | parser.md]
Parser는 모델 응답을 바꿉니다.

[doc-011 | 제목 없음 | faq.md]
FAQ 본문입니다.
```

`title`이 없으면 `.get()`의 대체값이 쓰이고, 문서 사이에는 `"\n\n"`(빈 줄 하나)이 들어갑니다.

</details>

### 6-Q3. 키워드 점수 계산 (6-2)

문서의 keywords가 `["retriever", "검색", "질의", "문서"]`일 때, 각 질의의 `keyword_score`를 쓰세요.

1. `"Retriever 검색 방법"`
2. `"RETRIEVER가 뭐예요?"`
3. `"검색된 문서 목록"`
4. `"리트리버는 무엇인가요?"`

> 힌트: `casefold()` 뒤에 **포함 여부(`in`)**로 비교합니다. 단어가 정확히 따로 떨어져 있을 필요는 없습니다.

<details>
<summary>정답 보기</summary>

1 → **2** (`retriever`, `검색`) · 2 → **1** (casefold로 `retriever` 일치) · 3 → **2** (`"검색"`이 `"검색된"` 안에 포함, `"문서"` 포함) · 4 → **0** (한글 "리트리버"는 영문 키워드와 문자열이 달라 못 찾음 — 의미 검색이 아님).

</details>

### 6-Q4. 검색 결과 순서 예측 (6-2)

아래 순서로 저장된 세 문서가 있습니다. 각 질의의 결과를 문서 이름 목록으로 쓰세요 (`max_results=2`).

| 순서 | 문서 | keywords |
| --- | --- | --- |
| 0 | A | `["lcel", "pipe"]` |
| 1 | B | `["pipe", "runnable"]` |
| 2 | C | `["lcel", "pipe", "runnable"]` |

1. `"LCEL pipe runnable 설명"`
2. `"pipe 연산자"`
3. `"   "`
4. `"memory 저장"`

> 힌트: 점수 내림차순, 동점이면 원래 순서, 0점 제외, 앞의 2개만.

<details>
<summary>정답 보기</summary>

| 질의 | 점수 (A, B, C) | 결과 |
| --- | --- | --- |
| 1 | 2, 2, 3 | `[C, A]` — C가 최고점, A·B 동점은 원래 순서로 A 먼저, 2개만 |
| 2 | 1, 1, 1 | `[A, B]` — 전부 동점 → 원래 순서 |
| 3 | - | `[]` — 공백만 있는 질의 |
| 4 | 0, 0, 0 | `[]` — 0점 제외 |

</details>

### 6-Q5. 버그 찾기 — Retriever 사용 (6-2)

두 곳에서 오류가 납니다. 각각 어떤 오류인지와 고치는 방법을 쓰세요.

```python
retriever = build_keyword_retriever(documents)
results = retriever.invoke({"query": "Retriever는 어떤 역할을 하나요?"})   # (가)

results = retriever.invoke("메모리는 어디에 저장하나요?")
print(results[0].page_content)                                          # (나)
```

> 힌트: (가) `search_documents` 첫 줄에서 `query.strip()`을 호출합니다. (나) 이 질의는 0건입니다.

<details>
<summary>정답 보기</summary>

(가) Retriever 입력 계약은 문자열인데 dict를 넣어 `retrieve()` → `search_documents()`에서 `query.strip()`이 실패 → `AttributeError: 'dict' object has no attribute 'strip'`. 고치기: `retriever.invoke("Retriever는 어떤 역할을 하나요?")`. (나) 결과가 빈 목록이라 `results[0]`이 `IndexError`. 고치기:

```python
if results:
    print(results[0].page_content)
else:
    print("검색 결과가 없습니다.")
```

</details>

### 6-Q6. source filter 결과 (6-2)

```python
docs = [
    Document(page_content="LCEL 설명", metadata={"source": "intro.md", "keywords": ["lcel"]}),
    Document(page_content="API Key 설명", metadata={"source": "env.md", "keywords": ["api"]}),
    Document(page_content="Retriever 설명", metadata={"source": "retriever.md", "keywords": ["retriever"]}),
]
```

질의 `"Retriever와 API"`에 대해 (1) filter 없음 (2) `source_filter="retriever.md"` (3) `source_filter="faq.md"`일 때 각각 결과 문서의 source 목록을 쓰세요. (3)이 오류인지도 답하세요. (`max_results=2`)

> 힌트: filter는 점수 계산 **전에** 후보를 줄입니다.

<details>
<summary>정답 보기</summary>

질의를 casefold하면 `"retriever와 api"`이므로 `retriever`, `api` 키워드가 포함됩니다. (1) 점수: intro 0, env 1, retriever 1 → 동점은 원래 순서 → `["env.md", "retriever.md"]`. (2) filter로 retriever.md만 남음 → `["retriever.md"]`. (3) 남는 후보가 없어 `[]` — **오류가 아니라 정상 결과**입니다.

</details>

### 6-Q7. 자료형 흐름 빈칸 (6-3)

`retrieval_chain.invoke("Retriever는 어떤 역할을 하나요?")`의 흐름에서 빈칸을 채우세요.

`str` → search → ( ① ) → format → `context`: ( ② ) → prepare 결과: ( ③ , 키 3개: ___ ) → Prompt → ( ④ ) → Model → ( ⑤ ) → Parser → `str` → 최종 결과: `dict` (키 4개: ___ )

> 힌트: 4-2의 assign은 기존 키를 지우지 않습니다.

<details>
<summary>정답 보기</summary>

① `list[Document]` ② `str` ③ `dict` (`question`, `documents`, `context`) ④ `ChatPromptValue`(PromptValue) ⑤ `AIMessage` · 최종 dict 키 4개: `question`, `documents`, `context`, `answer`.

</details>

### 6-Q8. context 예측 (6-3)

6-3의 `format_documents`(source 없는 버전)와 `retrieve_and_prepare`를 사용합니다. 6-3 실습의 `documents`는 doc-001(LCEL 기초, keywords `lcel/pipe/runnable`)과 doc-003(Retriever 역할, keywords `retriever/검색/질의/문서`)입니다. 두 질문의 `documents`에 들어가는 ID 목록과 `context` 값을 쓰세요.

1. `"메모리는 어디에 저장하나요?"`
2. `"LCEL pipe는 Retriever와 어떻게 연결되나요?"`

> 힌트: 2번은 두 문서가 모두 걸립니다. 점수를 세어 순서를 정하세요.

<details>
<summary>정답 보기</summary>

1. `documents`: `[]` · `context`: `"검색된 문서가 없습니다."` (일치 키워드 없음)
2. 점수: doc-001은 `lcel`, `pipe` → 2점 / doc-003은 `retriever` → 1점. `documents`: `["doc-001", "doc-003"]`. `context`:

```text
[doc-001 | LCEL 기초]
LCEL은 Prompt, Model, Parser 같은 Runnable 단계를 pipe 연산자로 연결하는 표현식입니다.

[doc-003 | Retriever 역할]
Retriever는 사용자 질의와 관련된 Document를 찾아 다음 단계에 전달하는 검색 인터페이스입니다.
```

</details>

### 6-Q9. 두 체인 비교 (6-3)

```python
chain_a = RunnableLambda(retrieve_and_prepare) | answer_chain
chain_b = RunnableLambda(retrieve_and_prepare) | RunnablePassthrough.assign(answer=answer_chain)
```

`chain_a.invoke(q)`와 `chain_b.invoke(q)`의 결과 자료형과 담긴 내용은 어떻게 다른가요? 근거 ID를 검증하려면 어느 쪽이 필요한가요? 그리고 `retrieve_and_prepare`가 `"context"` 대신 `"docs"` 키로 반환하면 어떻게 될까요?

> 힌트: `answer_chain` 결과는 `str`입니다. Prompt는 `{context}`를 요구합니다.

<details>
<summary>정답 보기</summary>

`chain_a`는 `answer_chain`의 결과인 **답변 문자열(`str`) 하나만** 반환하고 검색 결과·context는 사라집니다. `chain_b`는 `question`, `documents`, `context`, `answer`가 모두 든 **dict**를 반환합니다. 답변의 `[근거: doc-xxx]`가 실제 검색 문서에 있는지 확인하려면 `documents`가 남는 `chain_b`가 필요합니다. `"docs"` 키로 반환하면 Prompt의 `{context}` 변수를 채울 값이 없어 Prompt 입력 변수 오류(KeyError 계열)가 납니다 — 3-1·3-3의 키 불일치와 같은 원인입니다.

</details>

### 6-Q10. 개념 O/X (6장 전체)

1. 6-2 실습은 OpenAI API Key가 없으면 실행할 수 없다.
2. 6-3 체인을 한 번 invoke하면 검색 1회 + 답변 1회로 OpenAI가 2번 호출된다.
3. 답변 끝에 `[근거: doc-003]`이 붙어 있으면 그 답변은 정확하다고 봐도 된다.
4. 검색 결과가 없으면 context에 빈 문자열 `""`을 넣는 것이 가장 좋다.
5. 청킹·임베딩·Vector DB는 이번 6장의 기본 retrieval chain 범위에 포함된다.
6. `max_results`를 1로 줄이면 검색 품질이 자동으로 좋아진다.
7. metadata `source`를 일관되게 저장하면 formatter 하나로 모든 문서의 출처를 표시할 수 있다.

> 힌트: 6-3의 "호출 횟수", "문서가 없을 때의 규칙", "과목 경계"를 떠올려 보세요.

<details>
<summary>정답 보기</summary>

1 X (모델 호출 없음) · 2 X (검색은 로컬, OpenAI는 답변 생성 1회) · 3 X (표시된 ID를 `documents`와 대조하고 평가해야 함) · 4 X (`"검색된 문서가 없습니다."`처럼 분명한 문구) · 5 X (후속 RAG 과목) · 6 X (문서 수만 줄어듦) · 7 O

</details>
