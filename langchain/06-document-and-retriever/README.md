# 6장. Document와 Retriever (6-1까지)

> 2026-09-30 학습 기록. 6-1강(Document 구조와 metadata 활용)까지 정리했습니다. 6-2강(Retriever)과 6-3강(기본 retrieval chain)은 다음 회차에 이어서 진행합니다.

## 학습 목표

- 외부 자료를 `Document(page_content=..., metadata={...})` 모양으로 담는다.
- 본문은 `page_content`(str), 출처·ID 같은 부가 정보는 `metadata`(dict)로 분리한다.
- 모든 문서에서 같은 의미의 metadata는 같은 키 이름으로 저장한다.
- 없을 수도 있는 키는 `.get(키, 대체값)`으로 읽는다.
- formatter로 Document를 바꾸지 않고 표시·Prompt용 문자열을 만든다.

## 실습 파일

| 강 | 주제 | 실습 상태 |
| --- | --- | --- |
| 6-1 | Document 구조와 metadata 활용 | 📘 이론 정리 |
| 6-2 | Retriever 인터페이스와 검색 질의 | ⬜ 다음 회차 |
| 6-3 | 기본 retrieval chain과 RAG 과목 경계 | ⬜ 다음 회차 |

실습 노트북은 이번 기록에 포함하지 않았습니다. 아래 확인 문제는 API 없이 풀 수 있도록 만든 복습용 문제입니다.

## 전체 흐름

```text
6-1   원본 문장 ──→ Document
                    ├─ page_content : 실제 본문 (str)       ← Prompt에 들어갈 본문
                    └─ metadata     : document_id · title · source · keywords (dict) ← 식별·표시·검색 단서

      Document 목록 ──→ formatter ──→ "[ID | 제목 | 출처]\n본문" 문자열 (문서 사이는 빈 줄)
```

6장은 **담기(6-1) → 찾기(6-2) → 문서를 넣어 답하기(6-3)** 순서로 진행됩니다. 이번 기록은 6-1까지이며, 6-2 Retriever와 6-3 retrieval chain은 다음 회차에 이어서 정리합니다.

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

## 확인 문제

모두 API 없이 풀 수 있습니다. `from langchain_core.documents import Document`와 `from langchain_core.runnables import RunnableLambda, RunnablePassthrough`가 되어 있고, 각 문제 바로 아래에 정답과 해설이 있습니다. 먼저 풀어 본 뒤 확인하세요.

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
