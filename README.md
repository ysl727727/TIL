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
| 현재 단계 | RAG 과목 시작 — 1일차(1·2장) 완료 → 3장 청킹 예정 |
| 최근 학습 | **2026-10-19** · [RAG 1장](./rag/01-why-rag-and-basic-pipeline/)·[2장](./rag/02-document-loading-and-cleaning/) — 검색 후보와 실제 Context 구분, 문서 로딩·metadata·정제·JSONL 검수 |
| 다음 할 일 | RAG 3장 청킹(Chunk Size·Overlap, Recursive·Token, 문서 구조 기반) · 복습 2일차 선택 실습은 주말에 |
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

### 2026-10-19 · RAG 1일차: RAG 기본 파이프라인(1장)과 문서 준비(2장)

- RAG 1일차(오전 1장·오후 2장) 8개 강의를 `rag_day1` 키트로 실행하고 강마다 q\_easy·q\_hard까지 풀어 정답 확인 → [1장](./rag/01-why-rag-and-basic-pipeline/) · [2장](./rag/02-document-loading-and-cleaning/)
- **검색 성공 ≠ 답변 가능**: `호텔비`는 표현이 달라 검색 실패, `개인 취미`는 검색은 됐지만 문서에 답이 없음 → 원인이 다르니 대응도 다름(임베딩 검색 vs "확인 불가" 안내)
- 역색인은 단어 → 문서 ID 집합. OR = 합집합, AND = 교집합이고, `intersection_update`는 집합을 직접 고치므로 첫 집합을 `set()`으로 복사해야 원본 색인이 안 망가짐. 문서가 바뀌면 인덱스도 다시 만들어야 함
- **오늘 배운 점: 검색 후보와 실제 입력은 다르다.** `retrieve`의 `rows`(후보 3개)와 `build_context`의 `context`/`sources`(예산 260 안에 들어간 2개)를 따로 보고, 출처는 Context에 실제로 들어간 것만 연결
- 문서 예산 = 한도 − 지시문 − 질문·이력 − 출력 예약 − 여유(8192 → 6000). RAG(검색)·Long Context(긴 입력 능력)·CAG(계산 상태 재사용)는 같은 축이 아니고, KV cache는 답변이 아니라 입력 계산을 재사용
- 2장: HTML은 태그 삭제보다 본문 범위 선택이 먼저, PDF 줄바꿈은 페이지 폭 때문. 현행은 게시일이 아니라 `status`로 고르고, 중복 키(version, category, 본문 해시)로 복사본만 빼고 구버전은 유지. 정제는 뜻(금액·부정 표현)을 바꾸지 않음
- JSONL은 한 줄에 객체 하나, 본문 줄바꿈은 `\n`으로 이스케이프돼 한 행 유지. 저장 후 다시 읽어 문법 오류와 스키마 오류를 행 번호와 함께 구분
- 실습 실수: `row`/`rows` 이름 불일치로 다른 검색 결과 사용, `assert`는 반환 문자열 글자까지 비교, `"category"`(글자) vs `category`(변수), `split()` vs `strip()`

### 2026-10-16 · 2차 프로젝트 러브코드 회고: 16유형 분류(BERT)와 LangChain 해설

- 내 담당: 사주·MBTI 커플 16유형 분류 모델(klue/bert-base 축별)과 LangChain 해설 체인·생성 모델 비교. test macro-F1 **0.831** / 정확도 0.858, 해설 규칙 위반 0/24 → [프로젝트 회고](./projects/01-lovecode-couple-type-classifier/)
- 첫 점수 0.079의 원인은 모델이 아니라 **흔들리는 정답**. 판단 기준을 코드(규칙 라벨러)로 고정하고 판단 재료를 텍스트에 빠짐없이 넣자 데이터를 늘릴수록 점수가 오름(0.165 → 0.757)
- 효과 큰 순서: 규칙 라벨 + 데이터 증가 > **어려운 사례 1,200쌍**(0.744 → 0.802) > 축별 분류(0.714 → 0.744). 규제는 과적합만 줄이고 점수는 유지 → 남은 오차는 과적합이 아님
- 120쌍 validation 1위가 1,200쌍 dev에서 3위 → 작은 평가 세트로는 순위를 믿을 수 없어 dev를 따로 두고 test는 1회만 사용
- TF-IDF(0.428)는 조각 개수만 세서 "중요도가 같으면 태그로 비교" 같은 조건을 못 따라 함. LLM에 규칙만 설명하면 축별 0.8 → 네 축 곱 0.41, 예시로 배운 BERT는 0.95⁴ ≈ 0.81
- LangChain: `prompt | model | parser`로 모델 자리만 바꿔 같은 24건·같은 프롬프트로 비교. 반대 극 언급 3/24는 재작성으로 증상을 막고, 프롬프트에서 원인을 고쳐 첫 초안 0/24·비용 −21%
- 발표 중 "잠시 후 다시 시도" 오류의 원인은 같은 IP 10분 5회 요청 제한. 강의실처럼 한 IP를 여럿이 쓰는 환경을 고려해야 함

### 2026-10-07 · 복습 2일차: 모델 선택, 복원과 예측, 생성 호출, API

- 프로젝트 전 복습 수업 2일차(교안 05\~08): step05 모델 선택 → step06 checkpoint 복원·예측 → step07 생성 호출 → step08 체인 → step09 기록·비교 → step10 API까지 모두 실행. 공통 문의 confidence 0.6360으로 교안 값과 일치
- `selected.json`은 가중치가 아니라 "누구의 어느 실험을 무슨 기준으로 골랐는지"의 기록. `max(key=lambda …)`는 동점이면 **목록 앞 후보**(lr2e5)를 남기므로 점수와 동점 처리 기준을 함께 기록
- confidence는 softmax 확률 중 가장 큰 값일 뿐 정답 확률이 아님. 띄어쓰기 한 칸만 달라도 토큰이 달라져 0.7210 vs 0.7126처럼 점수가 바뀜
- 프롬프트에는 `json.dumps(원문)`으로 경계를 표시하고, Ollama는 `ollama run` 없이 서버만 켜져 있으면 `httpx`로 호출. 성공·실패 모두 같은 모양으로 반환하고 형식 검사는 필드·타입만, 내용은 사람이 판단
- step10: 422는 함수 실행 **전** 요청 모델 검사, 502는 뒤쪽 LLM 실패, 200이어도 답의 정확성은 따로 확인. `/compare`는 분류 한 번 + 같은 프롬프트로 두 LLM을 같은 조건에서 비교
- `if __name__ == "__main__":` 밖의 코드는 import될 때도 실행됨 — step 파일에 붙인 퀴즈가 practice08 실행 때 먼저 출력된 원인. 퀴즈는 별도 파일로 분리
- Python 보강 2장: 클래스(`self`, `return` vs `print`), 람다와 `sorted(key=…)`, 데코레이터(`@wrap` = 포장, `@app.get("/")` = 등록)

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
├── rag/                           # 1~2장
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
