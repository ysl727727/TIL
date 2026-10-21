# 📚 TIL · Private LLM 엔지니어 학습 기록

![KANT](https://img.shields.io/badge/KANT-Private%20LLM%20%EC%97%94%EC%A7%80%EB%8B%88%EC%96%B4%20%EA%B3%BC%EC%A0%95-4B32C3?style=flat-square)
![Last commit](https://img.shields.io/github/last-commit/ysl727727/TIL?style=flat-square&label=%EB%A7%88%EC%A7%80%EB%A7%89%20%EC%BB%A4%EB%B0%8B&color=2EA44F)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=flat-square&logo=pytorch&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=flat-square&logo=langchain&logoColor=white)

> KANT Private LLM 엔지니어 교육과정에서 배우고 직접 실험한 내용을 기록합니다.
> 강의 원문을 옮기지 않고, **무엇을 이해했고 코드로 무엇을 확인했는지**를 제 말로 정리합니다.
> 실습은 직접 실행하고 설명할 수 있을 때만 완료로 표시합니다.

## 📌 현재 진행 상황

| 항목 | 내용 |
| --- | --- |
| 현재 단계 | RAG 3일차 5장(Vector Store) 완료 → 6장 2-Step RAG 예정 |
| 최근 학습 | **2026-10-21** · [RAG 5장](./rag/05-vector-store-qdrant/) — Qdrant Point·필터·갱신, Qdrant Cloud(Strict Mode)와 FAISS(정확·HNSW) 추가 과제 |
| 다음 할 일 | RAG 6장 Retriever → Context → 2-Step RAG · Citation · 답변 보류 |
| 밀린 실습 | [주말 실습 백로그](./WEEKEND_PRACTICE_BACKLOG.md)에서 관리 |
| 목표 | 평가와 운영까지 고려하는 LLM 엔지니어 |

## 🗺️ 학습 로드맵

```mermaid
flowchart LR
    ML[머신러닝] --> DLB[딥러닝 기초] --> DLA[딥러닝 심화] --> LLM[LLM 실전]
    LLM --> DE[데이터 엔지니어링] --> LC[LangChain] --> RAG[RAG] --> AG[AI Agent] --> OPS[LLMOps·서빙]

    classDef done fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef now fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef next fill:#f3f4f6,stroke:#9ca3af,color:#374151
    class ML,DLB,DLA done
    class LLM,DE,LC,RAG now
    class AG,OPS next
```

<sub>초록: 이론 진도를 마친 구간 · 노랑: 진행 중 · 회색: 예정 (실습 완료 여부는 아래 목차의 상태를 기준으로 봅니다)</sub>

## 📖 학습 목차

**상태 표시** ✅ 완료 · 🧪 실습 일부 완료 · 📘 이론 정리 · ⏳ 실습 대기 · 📭 실습 자료 없음 · ⬜ 미수강

### 머신러닝 · [`machine-learning/`](./machine-learning/)

| 장 | 주제 | 상태 |
| --- | --- | --- |
| [1](./machine-learning/01-model-evaluation/) | 모델 평가와 임계값 선택 — baseline 비교, Recall 정책, test는 마지막 한 번 | ✅ 완료 |
| [2](./machine-learning/02-tree-ensembles/) | 트리 앙상블 — 배깅·랜덤포레스트·부스팅, 후보 모델 비교 | 🧪 2-1 문제 1-1만 완료 |
| [3](./machine-learning/03-bias-variance-regularization/) | 편향·분산 진단과 Ridge·Lasso·ElasticNet 규제 | 📘 이론 정리 |
| [4](./machine-learning/04-class-imbalance-cv-leakage/) | 클래스 불균형, 교차검증 선택, 데이터 누수 방지 | 📘 이론 정리 · ⏳ 4-1·4-2 |
| [5](./machine-learning/05-cv-tuning-end-to-end-pipeline/) | CV 기반 하이퍼파라미터 탐색, End-to-End Pipeline과 스키마 검증 | ✅ 완료 (5-2 심화는 재구현 필요) |

### 딥러닝 기초 · [`deep-learning-basics/`](./deep-learning-basics/)

> 폴더 번호는 올린 순서이고, **장 번호는 강의 기준**입니다. (예: `08-cnn-foundations` = 12장)

| 장 | 주제 | 상태 | 폴더 |
| --- | --- | --- | --- |
| 1\~2 | ML과 DL, 학습 흐름, Tensor dtype·shape·broadcasting, CPU/GPU 디버깅 | ✅ 완료 | [01](./deep-learning-basics/01-pytorch-foundations/) |
| 3 | 퍼셉트론, MLP, `nn.Linear`, flatten, `forward` | ✅ 완료 | [02](./deep-learning-basics/02-mlp-foundations/) |
| 4 | 비선형성, ReLU·Sigmoid·Softmax와 출력층 계약 | ✅ 완료 | [03](./deep-learning-basics/03-activation-output-layers/) |
| 5 | 손실 함수, optimizer, learning rate와 parameter 갱신 | ✅ 완료 (재실행 1건) | [04](./deep-learning-basics/04-loss-optimization-training-loop/) |
| 6\~7 | 계산 그래프·Autograd, Transform·DataLoader·split | 🧪 심화 일부 대기 | [05](./deep-learning-basics/05-autograd-data-pipeline/) |
| 8 | MLP 학습·검증·metric·history 종합 흐름 | 🧪 8-8만 완료 | [06](./deep-learning-basics/06-mlp-training-validation/) |
| 9 | Seed, 로깅, `state_dict`, checkpoint, 재개, 실험 폴더 | 🧪 기본 완료 · 수정 셀 재실행 필요 | [07](./deep-learning-basics/07-experiment-reproducibility/) |
| 10 | 학습 곡선과 과적합·과소적합 진단 | ⬜ 건강 문제로 이월 | — |
| 12 | CNN 설계, 학습 파이프라인, GPU 메모리, MLP-CNN 비교, 실험 리포트 | ✅ 기본 완료 (12-4 수정 필요) | [08](./deep-learning-basics/08-cnn-foundations/) |
| 13 | 시퀀스 데이터, RNN forward shape, 경사 소실과 clipping | ✅ 기본 완료 | [09](./deep-learning-basics/09-rnn-foundations/) |

### 딥러닝 심화 · [`deep-learning-advanced/`](./deep-learning-advanced/)

| 장 | 주제 | 상태 |
| --- | --- | --- |
| [1](./deep-learning-advanced/01-transformer-motivation/) | RNN/LSTM의 한계와 Transformer 등장 배경, config hash 재현성 | ✅ 완료 |
| [2](./deep-learning-advanced/02-data-schema-and-tokenization/) | 데이터 스키마 감사, subword tokenizer, 동적 padding, offset mapping | ✅ 완료 |
| [3](./deep-learning-advanced/03-attention-and-multihead/) | Q·K·V, Scaled Dot-Product Attention, mask, Multi-Head, GQA KV Cache | ✅ 완료 |
| [4](./deep-learning-advanced/04-pretrained-language-models/) | 사전학습 LM — Masked LM(BERT) vs Causal LM(GPT) | 📘 이론 정리 · ⏳ 실습 대기 |
| [5](./deep-learning-advanced/05-huggingface-hub-and-automodel/) | Hugging Face Hub, Model Card, AutoClass, 저장·재로드 재현성 | 📘 이론 정리 · ⏳ 실습 대기 |
| [6](./deep-learning-advanced/06-text-classification-finetuning/) | 텍스트 분류 Fine-tuning — 데이터 감사부터 Trainer, Error Analysis까지 | 🧪 7-1만 실습 완료 |
| [7](./deep-learning-advanced/07-prompt-engineering-and-peft/) | Prompt Engineering → Prompt-tuning → PEFT(LoRA) → Full Fine-tuning | 📘 이론 정리 · 📭 |
| [8](./deep-learning-advanced/08-generation-and-chat-template/) | `generate()`, Greedy·Sampling·Beam, Temperature·Top-k·Top-p, Chat Template | 📘 이론 정리 · 📭 |

### LLM 실전 · [`llm-practical-foundations/`](./llm-practical-foundations/)

| 장 | 주제 | 상태 |
| --- | --- | --- |
| [1](./llm-practical-foundations/01-logits-softmax-and-optimizers/) | Logit·Softmax 수치 안정성, MSE·BCE·CE, Gradient Descent, SGD·Momentum·Adam | 📘 이론 정리 · ⏳ 실습 TODO 미완 |
| 2\~9 | Attention NumPy 실습, RLHF, LLM API와 Prompt 설계, Structured Output, Tool Calling, 멀티모달 | ⬜ 미수강 |
| [10](./llm-practical-foundations/10-stable-llm-api-calls/) | 안정적인 LLM API 호출 — 오류 분류, Backoff + Full Jitter, Fallback Ladder (10-1강 보강) | 📘 이론 정리 · 📭 |

### 데이터 엔지니어링 · [`data-engineering/`](./data-engineering/)

| 장 | 주제 | 상태 |
| --- | --- | --- |
| [1](./data-engineering/01-collection-strategy-and-risk/) | 수집 경로와 데이터 형식, 수집 전 5단계 리스크 게이트 | ✅ 완료 |
| [2](./data-engineering/02-http-and-python-api-calls/) | HTTP 요청·응답 계약, 환경 변수 인증, HTTPX Client, 실패 위치 구분 | ✅ 완료 |
| [3](./data-engineering/03-pagination-and-raw-storage/) | Pagination, 429 재시도, 원본·가공 파일 분리와 수집 로그 | 📘 이론 정리 · ⏳ 실습 대기 |
| [4](./data-engineering/04-data-cleaning-and-rag-documents/) | 데이터 정제 순서와 집계 등식, RAG 문서 계약과 `document_id` | 📘 이론 정리 · 📭 |
| [5](./data-engineering/05-fastapi-server-and-request-response/) | FastAPI·Uvicorn 역할, path·query·body, 404 vs 422, `TestClient` | 📘 이론 정리 · 📭 |
| [6](./data-engineering/06-pydantic-schema-and-document-api/) | Pydantic 스키마, 필드·모델 검증, 요청·응답 모델 분리 | 📘 이론 정리 · 📭 |
| [7](./data-engineering/07-query-api-and-llm-integration/) | Query API 계약, 프롬프트 조립, mock·external·ollama 모드, 502·503 변환 | 📘 이론 정리 · 📭 |
| [8](./data-engineering/08-async-calls-and-stability/) | `async`/`await`, `AsyncClient` 공유, 단계별 timeout, 제한된 재시도 | 📘 이론 정리 · 📭 |

### LangChain · [`langchain/`](./langchain/)

| 장 | 주제 | 상태 |
| --- | --- | --- |
| [1](./langchain/01-app-structure-and-environment/) | SDK 직접 호출 vs LangChain, Prompt → Model → Parser, uv + Python 3.12 환경 | 📘 이론 정리 · ⏳ 실습 TODO 미완 |
| [2](./langchain/02-prompt-template-and-output-parser/) | `PromptTemplate`·`ChatPromptTemplate`, Str·List·JSON Output Parser | 📘 이론 정리 · 📭 |
| [3](./langchain/03-lcel-pipe-and-execution/) | LCEL pipe 연산자, `invoke`·`batch`·`stream`, 단계별 자료형 디버깅과 체인 재사용 | 📘 이론 정리 |
| [4](./langchain/04-runnable-sequence-parallel-assign/) | `RunnableSequence`·`RunnableParallel`, `RunnablePassthrough`·`RunnableLambda`·`.assign()` | 📘 이론 정리 |
| [5](./langchain/05-structured-output-and-validation/) | Pydantic 스키마와 `with_structured_output()`, Parser 검증과 오류 읽기, 1회 복구 | 📘 이론 정리 |
| [6](./langchain/06-document-and-retriever/) | `Document`·metadata, 키워드 Retriever(`str → list[Document]`), 기본 retrieval chain | 📘 이론 정리 |
| [7](./langchain/07-chat-history-and-session/) | `HumanMessage`·`AIMessage`, session별 history, `MessagesPlaceholder`, Retriever vs history | 📘 이론 정리 |
| [8](./langchain/08-streaming-callback-and-tracing/) | `stream()` 출력, `BaseCallbackHandler` 이벤트, 실행 시간·토큰 기록, Langfuse trace | 📘 이론 정리 |
| [9](./langchain/09-retry-fallback-and-degradation/) | `with_retry`와 예외 유형별 처리, `with_fallbacks`, graceful degradation | 📘 이론 정리 |
| [10](./langchain/10-integrated-document-qa-app/) | 통합 문서 Q&A 앱 설계·구현, 출처 검증, `RunRecord` 관측, LCEL vs LangGraph | 📘 이론 정리 · 🧪 통합 실습 진행 |

### RAG · [`rag/`](./rag/)

| 장 | 주제 | 상태 |
| --- | --- | --- |
| [1](./rag/01-why-rag-and-basic-pipeline/) | RAG가 필요한 이유, Indexing·Query와 역색인, 2-Step RAG 기준선(검색 후보 vs Context), RAG·Long Context·CAG 선택 | ✅ 완료 |
| [2](./rag/02-document-loading-and-cleaning/) | TXT·HTML·PDF 로딩과 `Document`, 출처 metadata, 중복·Boilerplate 정제, JSONL 저장·검수 | ✅ 완료 |
| [3](./rag/03-chunking-strategies/) | Chunk Size·Overlap, Fixed·Recursive·Token 청킹, Markdown 제목 기반 청킹, 근거 보존 비교와 `chunks.json` | ✅ 완료 |
| [4](./rag/04-embedding-dense-retrieval/) | E5 임베딩·pooling·정규화, 코사인 Top-k, k·threshold, Hit@k·Recall Dense 기준선 | ✅ 완료 |
| [5](./rag/05-vector-store-qdrant/) | Qdrant Point·Collection·Upsert·Query, Metadata Filter, 갱신과 ANN, Qdrant Cloud·FAISS 추가 과제 | ✅ 완료 |

### 프로젝트 전 복습 · [`private-llm-review/`](./private-llm-review/)

> 목요일 프로젝트 시작 전, 그동안 배운 내용을 `project2-kit`으로 다시 실행해 보는 복습 수업입니다. 일차 단위로 정리합니다.

| 일차 | 주제 | 상태 |
| --- | --- | --- |
| [1](./private-llm-review/day01-data-baseline-bert/) | 환경 준비, 데이터 읽기·점검, TF-IDF 기준 모델, BERT 분류기 학습과 gradient accumulation | ✅ 완료 |
| [2](./private-llm-review/day02-model-select-generate-api/) | 모델 선택과 동점 처리, checkpoint 복원·예측, 생성 호출, 기록·비교, FastAPI 서버(422·502) | ✅ 완료 |

### 프로젝트 · [`projects/`](./projects/)

| 번호 | 프로젝트 | 내 담당 | 결과 |
| --- | --- | --- | --- |
| [1](./projects/01-lovecode-couple-type-classifier/) | 러브코드 — 사주·MBTI로 커플 관계 스타일 16유형 분류 + LLM 해설 (2026-10-09 ~ 10-16) | BERT 분류 모델, LangChain 해설·생성 모델 비교 | test macro-F1 0.831, 해설 위반 0/24 |

### Python 보강 · [`python-basics/`](./python-basics/)

| 장 | 주제 | 상태 |
| --- | --- | --- |
| [1](./python-basics/01-syntax-conditionals-collections/) | 변수·자료형·f-string, 조건문, 리스트·딕셔너리 메서드, 중첩 반복문 | ✅ 완료 |
| [2](./python-basics/02-class-lambda-decorator/) | 클래스·`self`, 람다와 `sorted(key=…)`, 데코레이터, `@app.get("/")` | ✅ 완료 |

### 종합 과제 · [`assignments/`](./assignments/)

정규 강의 실습과 분리해 채점용 과제를 보관합니다.

| 과제 | 내용 | 상태 |
| --- | --- | --- |
| [기초 수학](./assignments/basic-math-assignment/) | 문서 임베딩·Cosine 검색, PCA, SVD 압축, Causal Attention + autograd | ✅ 제출 |
| [딥러닝 기초](./assignments/deep-learning-basic-assignment/) | DataLoader 검사, MLP·CNN 비교, checkpoint 저장·복원·재개 | ✅ 제출 |

## 📝 최근 학습 기록

> 전체 기록은 [LEARNING_LOG.md](./LEARNING_LOG.md)에 날짜순으로 모아 두었습니다.

### 2026-10-21 · RAG 3일차: Vector Store(Qdrant)와 Cloud·FAISS 추가 과제(5장)

- RAG 3일차 오전 5장을 `rag_day3` 키트로 실행하고 강마다 q\_easy·q\_hard까지 확인. 수업 뒤 추가 과제로 5-2·5-3을 **Qdrant Cloud**로, 같은 검색을 **FAISS**로 다시 해 봄 → [5장](./rag/05-vector-store-qdrant/)
- Point = `id + vector + payload`. `uuid5(chunk_id)`라 같은 청크는 항상 같은 ID → Upsert 두 번에도 1개. `chunks[i]`와 `vectors[i]`는 같은 인덱스로 꺼내야 짝이 맞음
- 28개 Upsert 후 current 필터로 Top-3 = 4장 NumPy와 같은 `0.8945 · 0.875 · 0.8444`. 필터는 점수를 바꾸지 않고 **후보 자격**만 정함("8만원인가요?"에서 travel-old 0.9003이 빠짐)
- 다시 청킹하면 청크 ID가 모두 바뀌어 이전 Point가 남음 → `old_ids - new_ids` 삭제(3 → 5 → 2). ANN은 일부만 탐색해서 놓칠 수 있음(겹침 0.5)
- Qdrant Cloud: `:memory:`와 달리 데이터가 남고 **Strict Mode**라 필터 필드에 `create_payload_index`가 필수. 5-2는 `metadata.status`, 5-3은 status·category·start 인덱스 → 결과는 메모리와 같음
- FAISS: `IndexFlatIP`(정규화 벡터라 내적 = 코사인)와 `IndexHNSWFlat`(ANN) 모두 같은 Top-3. 벡터만 저장해서 원문은 `chunks[i]`, 현행 필터는 직접 처리
- 클래스·객체(속성은 `.이름`, 메서드는 `.이름()`), `query_points(...).points`·`count(...).count`처럼 Qdrant 결과는 "상자 → 점으로 꺼내기", `.tolist()`는 JSON으로 보내려고

### 2026-10-20 · RAG 2일차: 청킹(3장)과 임베딩·Dense 검색(4장)

- RAG 2일차(오전 3장·오후 4장)를 `rag_day2` 키트로 실행. 3·4장 강마다 q\_easy·q\_hard까지 풀어 정답 확인 → [3장](./rag/03-chunking-strategies/) · [4장](./rag/04-embedding-dense-retrieval/)
- 청킹: 이동 간격 = `size − overlap`(80/20 → 0·60·120). 겹침을 늘려도 승인 문장 `[54:92]`는 80/20의 어느 청크에도 통째로 없고, 100/20에서만 온전함. 공통 기준은 최적값이 아니라 비교 출발점으로 80/20 `chunks.json`(28개)
- Recursive는 `". "` → `" "` → `""` 순서로 문장 경계부터 자르고, 모델 한도는 문자가 아니라 **토큰**(문자÷토큰 1.41\~1.75). 토큰 50으로 잘라도 `passage:`를 붙이면 51 → 최종 입력을 다시 잼. Truncation은 오류 없이 조용히 조건을 지움
- 문서 구조 청킹: `## 제목`으로 먼저 나누고 `metadata.update`로 원문 정보를 붙인 뒤 `split_documents`로 절 안에서만 다시 자름. metadata의 제목은 임베딩에 자동으로 안 들어감
- 임베딩: 청크 28개 → `(28, 384)`, 정규화했으니 `vectors @ query` = 코사인. **공식을 NumPy 코드로 옮겨 값을 찍어 보니**(mask pooling, `axis`, norm, 코사인) 이해가 빨라짐
- k·threshold: q06은 k=3에서 세 근거 완성, 하한 0.88이면 숙박 금액, 0.90(직접 실험)이면 식비 금액까지 사라짐. 점수 ≠ 답의 존재(매출 목표 질문도 0.7986)
- 기준선: E5 small Hit@3·Recall@3 = 1.0이지만 base와 비교하면 5개 질문의 검색 문서가 다름 → 평균 뒤 질문별 결과와 원문을 같이 봄
- 퀴즈에서 리스트 컴프리헨션 ↔ for문 변환, `setdefault`, `small_rows = {r["question_id"]: r …}`처럼 ID로 짝 맞추기를 정리. 4-2 `main.py`에 넣은 for문이 `cosines`를 리스트로 덮어써 `.tolist()` 오류

### 2026-10-19 · RAG 1일차: RAG 기본 파이프라인(1장)과 문서 준비(2장)

- RAG 1일차(오전 1장·오후 2장) 8개 강의를 `rag_day1` 키트로 실행하고 강마다 q\_easy·q\_hard까지 풀어 정답 확인 → [1장](./rag/01-why-rag-and-basic-pipeline/) · [2장](./rag/02-document-loading-and-cleaning/)
- **검색 성공 ≠ 답변 가능**: `호텔비`는 표현이 달라 검색 실패, `개인 취미`는 검색은 됐지만 문서에 답이 없음 → 원인이 다르니 대응도 다름(임베딩 검색 vs "확인 불가" 안내)
- 역색인은 단어 → 문서 ID 집합. OR = 합집합, AND = 교집합이고, `intersection_update`는 집합을 직접 고치므로 첫 집합을 `set()`으로 복사해야 원본 색인이 안 망가짐. 문서가 바뀌면 인덱스도 다시 만들어야 함
- **오늘 배운 점: 검색 후보와 실제 입력은 다르다.** `retrieve`의 `rows`(후보 3개)와 `build_context`의 `context`/`sources`(예산 260 안에 들어간 2개)를 따로 보고, 출처는 Context에 실제로 들어간 것만 연결
- 문서 예산 = 한도 − 지시문 − 질문·이력 − 출력 예약 − 여유(8192 → 6000). RAG(검색)·Long Context(긴 입력 능력)·CAG(계산 상태 재사용)는 같은 축이 아니고, KV cache는 답변이 아니라 입력 계산을 재사용
- 2장: HTML은 태그 삭제보다 본문 범위 선택이 먼저, PDF 줄바꿈은 페이지 폭 때문. 현행은 게시일이 아니라 `status`로 고르고, 중복 키(version, category, 본문 해시)로 복사본만 빼고 구버전은 유지. 정제는 뜻(금액·부정 표현)을 바꾸지 않음
- JSONL은 한 줄에 객체 하나, 본문 줄바꿈은 `\n`으로 이스케이프돼 한 행 유지. 저장 후 다시 읽어 문법 오류와 스키마 오류를 행 번호와 함께 구분
- 실습 실수: `row`/`rows` 이름 불일치로 다른 검색 결과 사용, `assert`는 반환 문자열 글자까지 비교, `"category"`(글자) vs `category`(변수), `split()` vs `strip()`

## 📂 폴더 구조

<details>
<summary>펼쳐 보기</summary>

```text
TIL/
├── README.md                      # 목차 (이 문서)
├── LEARNING_LOG.md                # 전체 학습 기록
├── WEEKEND_PRACTICE_BACKLOG.md    # 밀린 실습과 주말 계획
├── machine-learning/              # 1~5장
├── deep-learning-basics/          # 강의 1~9, 12, 13장
├── deep-learning-advanced/        # 1~8장
├── llm-practical-foundations/     # 1장, 10장
├── data-engineering/              # 1~8장
├── langchain/                     # 1~10장
├── rag/                           # 1~5장
├── private-llm-review/            # 프로젝트 전 복습 (일차별)
├── projects/                      # 팀 프로젝트 회고
├── python-basics/                 # Python 보강
└── assignments/                   # 채점용 종합 과제
```

각 장 폴더는 같은 규칙을 따릅니다.

```text
NN-주제-kebab-case/
├── README.md               # 학습 목표 · 실습 파일 · 핵심 이론 · 질문과 새로 알게 된 점
├── NN-topic-basic.ipynb    # 기본 실습 (있을 때만)
├── NN-topic-advanced.ipynb # 심화 실습 (있을 때만)
└── requirements.txt        # 실행 환경 (실습이 있을 때만)
```

실습 파일을 받지 못한 장은 `README.md`만 둡니다.

</details>

## 🧭 기록 원칙

- 교육자료 원본(강의 PDF, 확인문제) 대신 직접 작성한 코드와 해석만 공개합니다.
- 실행 환경, 데이터, random seed와 평가 지표를 기록합니다.
- 성공한 결과뿐 아니라 오류와 개선 방향도 남깁니다.
- 실행 기록이 없는 실습은 완료로 표시하지 않습니다.
- API key, 개인정보, 사용 권한이 불분명한 데이터는 올리지 않습니다.
- 폴더·파일 이름은 영어, 본문은 한국어로 씁니다. 기술 용어는 원어를 그대로 씁니다.
