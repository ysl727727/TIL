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
| 현재 단계 | 파인튜닝 — 5장 QLoRA 수업 · 양자화 정리 → 6장 DPO |
| 최근 학습 | **2026-11-23** · [파인튜닝 5장](./fine-tuning/05-qlora-quantization-resources/) 양자화 = 번호 + scale · NF4 16칸 · 4.5 → 4.127비트 · 저장 NF4 / 계산 BF16 / 임베딩 · A · B FP32 · prepare → LoRA · 0.5B는 메모리 이득 없음 · Unsloth · [Python 11장](./python-basics/11-derivatives-chain-rule/) 미분 · 연쇄법칙 |
| 다음 할 일 | 파인튜닝 5장 `qlora.ipynb` L4 실행 · `qlora_result.zip` 내려받기 · 5장 통합 실습 TODO 1\~8 · 6장 DPO · 4장 `lora_report.json` config 고치고 `lora_adapter` 내려받기 · 4장 통합 실습 · 3장 `sft_model.zip` 내려받기 · 1장 `manual_reviews` 채우기 · 보강 심화(NumPy 심화 1\~3 · 실무 1, 내적 심화 1\~3) · RAG 프로젝트 Hybrid · Reranker · 3종 비교 · CE 마무리 과제 · RAG 남은 q\_hard(7-4 · 8-4 · 9-2 · 9-3 · 9-4) · Python 보강 q 문제 |
| 밀린 실습 | [주말 실습 백로그](./WEEKEND_PRACTICE_BACKLOG.md)에서 관리 |
| 날짜별 TIL | [`daily/`](./daily/) — 같은 내용을 하루 단위(오늘 배운 것 · 왜 중요한가 · 코드 · 헷갈린 점 · 내일 할 것)로 정리 |
| 목표 | 평가와 운영까지 고려하는 LLM 엔지니어 |

## 🗺️ 학습 로드맵

```mermaid
flowchart LR
    PY[파이썬 베이직] --> BM[기초 수학] --> ML[머신러닝] --> DLB[딥러닝 기초] --> DLA[딥러닝 심화] --> LLM[LLM 실전]
    LLM --> DE[데이터 엔지니어링] --> LC[LangChain] --> RAG[RAG] --> CE[Context Engineering] --> AG[AI Agent] --> OPS[LLMOps·서빙] --> FT[파인튜닝]

    classDef done fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef now fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef next fill:#f3f4f6,stroke:#9ca3af,color:#374151
    class PY,BM,ML,DLB,DLA done
    class LLM,DE,LC,RAG,CE,OPS,FT now
    class AG next
```

<sub>초록: 이론 진도를 마친 구간 · 노랑: 진행 중 · 회색: 예정 (실습 완료 여부는 아래 목차의 상태를 기준으로 봅니다)</sub>

## 📖 학습 목차

**상태 표시** ✅ 완료 · 🧪 실습 일부 완료 · 📘 이론 정리 · ⏳ 실습 대기 · 📭 실습 자료 없음 · ⬜ 미수강

### 기초 수학 · [`basic-math/`](./basic-math/)

| 장 | 주제 | 상태 |
| --- | --- | --- |
| [1](./basic-math/01-vectors-norms-dot-cosine/) | 벡터·행렬, 노름과 정규화, 내적과 코사인 유사도, 행렬곱과 선형층 (08-05) | 🧪 1-1·1-2 실습 |
| [2](./basic-math/02-span-rank-linear-systems/) | 선형 변환, span·rank·영공간, `Ax = b`, `solve` vs `inv`, 조건수 (08-06) | 🧪 2-2 완료 · 2-3 일부 |
| [3·4](./basic-math/03-eigen-pca-svd/) | 고유값·PCA, 직교성과 최소제곱, SVD와 저랭크 근사 (08-07) | 🧪 4-1 실습 · PCA 미실행 |
| [5\~7](./basic-math/04-tensor-shape-attention-backprop/) | 텐서 shape, Attention `QKᵀ/√d_k`, Softmax·CE, 미분·역전파 (08-10) | 🧪 6-1 필수 실습 |

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
| [4강](./deep-learning-advanced/09-transformer-architecture/) | Transformer 전체 구조 — Encoder·Decoder 계열, 위치 정보, Causal Mask, FFN·Residual·LayerNorm, KV Cache (폴더 09) | 📘 이론 정리 |
| [4](./deep-learning-advanced/04-pretrained-language-models/) | 사전학습 LM — Masked LM(BERT) vs Causal LM(GPT) | 📘 이론 정리 · ⏳ 실습 대기 |
| [5](./deep-learning-advanced/05-huggingface-hub-and-automodel/) | Hugging Face Hub, Model Card, AutoClass, 저장·재로드 재현성 | 📘 이론 정리 · ⏳ 실습 대기 |
| [6](./deep-learning-advanced/06-text-classification-finetuning/) | 텍스트 분류 Fine-tuning — 데이터 감사부터 Trainer, Error Analysis까지 | 🧪 7-1만 실습 완료 |
| [7](./deep-learning-advanced/07-prompt-engineering-and-peft/) | Prompt Engineering → Prompt-tuning → PEFT(LoRA) → Full Fine-tuning | 📘 이론 정리 · 📭 |
| [8](./deep-learning-advanced/08-generation-and-chat-template/) | `generate()`, Greedy·Sampling·Beam, Temperature·Top-k·Top-p, Chat Template | 📘 이론 정리 · 📭 |

### LLM 실전 · [`llm-practical-foundations/`](./llm-practical-foundations/)

| 장 | 주제 | 상태 |
| --- | --- | --- |
| [1](./llm-practical-foundations/01-logits-softmax-and-optimizers/) | Logit·Softmax 수치 안정성, MSE·BCE·CE, Gradient Descent, SGD·Momentum·Adam | 📘 이론 정리 · ⏳ 실습 TODO 미완 |
| [3\~5](./llm-practical-foundations/03-attention-alignment-api-policy/) | Attention 복습, SFT·RLHF(PPO)·DPO, Responses API와 Developer Prompt | 📘 이론 정리 · 🧪 API 첫 요청 |
| 6\~9 | Few-shot·Self-Consistency, JSON Schema·Pydantic 구조화 출력, Tool Calling, 멀티모달 | ⬜ 미정리 (받은 이론 PDF 본문이 비어 있음) |
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
| [6](./rag/06-context-2step-rag-citation/) | Context 구성(`chunk_id` 중복 제거·문자 예산), 2-Step RAG 체인과 `validate_answer`, Citation `bind_claim`, 답변 보류 | ✅ 완료 |
| [7](./rag/07-hybrid-search-rerank-rewrite/) | BM25 vs Dense, Hybrid·RRF, Cross-Encoder Re-ranking, Query Rewrite·Multi-Query | 🧪 진행 (7-4 q\_hard 남음) |
| [8](./rag/08-evaluation-golden-hit-recall-ragas/) | Golden Dataset·dev/test, Hit@k·Recall@k(청크 vs 문서), RAGAS 네 지표(실행까지), BM25·Dense·Hybrid 전후 비교 | 🧪 진행 (8-4 q\_hard 남음) |
| [9](./rag/09-advanced-rag-parent-agentic-graph-multimodal/) | Parent-Child·Context 압축, Agentic RAG 재검색과 종료, GraphRAG(NetworkX·색인 실행), Multimodal·ColPali MaxSim | 🧪 진행 (9-2~9-4 q\_hard·9-4 남음) |
| [10](./rag/10-project-starter-pipeline-review/) | 프로젝트 대비 스타터 파이프라인 복습(자습) — PII·세션·캐시, 쿼리 재작성 vs 후속 질문 풀기, Context와 S 번호, 간접 인젝션·문서 가드, 출력 검증 kind, canary·근거 없는 숫자, 에스컬레이션 route, LLM judge·RAGAS | 📘 정리 |

### Context Engineering · [`context-engineering/`](./context-engineering/)

| 장 | 주제 | 상태 |
| --- | --- | --- |
| [1](./context-engineering/01-context-types-priority-skills/) | 컨텍스트 종류와 역할 분리(`kind` vs `role`), 출처 표지, 범위 → 유효성 → 관련성 우선순위, Skills | ✅ 완료 |
| [2](./context-engineering/02-short-long-term-memory-mem0/) | 단기·장기 메모리 설계(`decide_memory`, 만료), Mem0 저장·조회·ID로 수정·삭제 | ✅ 완료 |
| [3](./context-engineering/03-token-budget-summary-compression/) | chat template 토큰 세기, 입력 예산과 Sliding Window, 구조화 상태·원문 추출 압축, Map/Reduce | ✅ 완료 |
| [4](./context-engineering/04-prompt-caching-injection-filtering/) | Prompt Caching과 정적 Prefix, 캐시 지표, 컨텍스트 오염·Prompt Injection, 오탐·미탐, 실행 전 도구 검사 | ✅ 완료 |

### LLMOps · [`llmops/`](./llmops/)

| 장 | 주제 | 상태 |
| --- | --- | --- |
| [1](./llmops/01-tracing-failure-analysis/) | 실행 관측과 실패 원인 분석 — Langfuse Trace·observation, 완료 ≠ 정답, Trace ID 재조회, 도구 추적과 부모·자식 시간, 실패 판정 순서·`failure_category` | ✅ 완료 (q1\_hard·마무리 과제는 선택) |
| [2](./llmops/02-golden-dataset-prompt-regression/) | 평가 데이터와 변경 전후 검증 — Golden Dataset(dev·holdout), 프롬프트 버전 고정, `evaluate()` 규칙 점수 4개·오류 ≠ 0점, 질문 ID별 회귀 판정 BLOCK·REVIEW | ✅ 완료 (q3·q4\_hard·마무리 과제는 선택) |
| [3](./llmops/03-operational-metrics-cost-feedback/) | 운영 지표 분석과 개선 — 지표별 분모·None ≠ 0, p95와 timeout 장애, 문맥 길이 측정(토큰·지연), Trace 피드백 응답률 vs 긍정 비율, GENERATION 비용·판정 순서 | ✅ 완료 (q1\~q4\_hard 통과) |
| [4](./llmops/04-trust-boundary-privacy-output-security/) | 신뢰 경계와 권한 통제·개인정보 마스킹·출력 검증·보안 평가 — `principal`·`read_ids` 읽기 전 차단, `redact`·`mask_spans`, pydantic `Answer`·출처 범위, 직접·간접 주입과 정상 대조군, `run_tool` 도구 통제 | ✅ 완료 (q2·q3\_hard 통과) |

### 파인튜닝 · [`fine-tuning/`](./fine-tuning/)

| 장 | 주제 | 상태 |
| --- | --- | --- |
| [1](./fine-tuning/01-baseline-behavior-definition/) | 학습할 행동과 기준 응답 정의 — 지식은 문서로 · 행동은 학습으로, `cases` vs `review_criteria`, SFT · LoRA · QLoRA · DPO 지도, 채팅 템플릿 · 기울기 `p − y`, greedy 기준 응답 8개, 형식 ≠ 의미, `baseline.json` · 직접 구현(BPE · 템플릿 · `train_step` · `generate`) | ✅ 완료 (통합 실습 `manual_reviews` 남음 · 직접 구현 Hard는 선택) |
| [2](./fine-tuning/02-training-data-quality-split/) | 학습 데이터 구성과 품질 검증 — 규칙 함수 모범답안 72개(12그룹 × 6사례), 메타데이터 vs messages, 두 번 토큰화로 답변 경계 299 · 길이 512, `validate_record` 5단계 · 의도한 오류 2/2, 그룹 단위 분할 48/12/12 · SHA-256 · `training_data.zip` | ✅ 완료 |
| [3](./fine-tuning/03-full-sft-and-resume/) | 전체 가중치 SFT와 학습 재개 — `encode_example` labels −100 마스킹(370 = 299 + 71), `collate` 패딩 세 값 · (2, 379), shift는 모델 내부에서 한 번, 전체 = 학습 대상 4.94억 개, `TrainingArguments` 유효 배치 4 · 24갱신 · `StopAtTwelve`, 손실 ≠ 업무 정답, `resume_from_checkpoint` 12 → 24, 체크포인트 vs 추론용 모델 · `sft_model.zip` | ✅ 수업 노트북 (Colab T4 · FP32, ZIP 내려받기 남음) |
| [4](./fine-tuning/04-lora-adapter-restore/) | LoRA 어댑터 학습과 모델 복원 — h = Wx + (α/r)·BAx, W · A · B 모양 · 파라미터 r × (입력 + 출력), B = 0 시작과 첫 기울기, `LoraConfig` · `get_peft_model` · `lora_`만 학습 검사, `save_pretrained` · `PeftModel.from_pretrained` · `allclose` · `merge_and_unload`, `check_comparison_inputs`, 보강 lr 2e-4 · all-linear | ✅ 수업 노트북 (Colab T4 · FP32, 보강 설정까지 · 통합 실습 남음) |
| [5](./fine-tuning/05-qlora-quantization-resources/) | QLoRA 학습과 자원 비교 — 양자화 = 대표값 번호 + scale(2비트 [0, 1, 2, 2, 3] · 오차 0.633), NF4 16칸, 블록 64 · 이중 양자화 4.5 → 4.127비트, 저장 NF4 · 계산 BF16/FP32 · 임베딩 · A · B FP32, `BitsAndBytesConfig` · `prepare_model_for_kbit_training` → `get_peft_model`, 451 → 726 MB, 0.5B LoRA 1.615 vs QLoRA 1.637 GiB, 새 세션 복원, Unsloth | 📘 수업 · 양자화 질문 정리 (`qlora.ipynb` · 통합 실습 실행 기록 남음) |

### 프로젝트 전 복습 · [`private-llm-review/`](./private-llm-review/)

> 목요일 프로젝트 시작 전, 그동안 배운 내용을 `project2-kit`으로 다시 실행해 보는 복습 수업입니다. 일차 단위로 정리합니다.

| 일차 | 주제 | 상태 |
| --- | --- | --- |
| [1](./private-llm-review/day01-data-baseline-bert/) | 환경 준비, 데이터 읽기·점검, TF-IDF 기준 모델, BERT 분류기 학습과 gradient accumulation | ✅ 완료 |
| [2](./private-llm-review/day02-model-select-generate-api/) | 모델 선택과 동점 처리, checkpoint 복원·예측, 생성 호출, 기록·비교, FastAPI 서버(422·502) | ✅ 완료 |

### 프로젝트 · [`projects/`](./projects/)

| 번호 | 프로젝트 | 내 담당 | 결과 |
| --- | --- | --- | --- |
| [프로젝트(1)](./projects/02-open-source-llm-selection/) | 오픈소스 LLM 선정 — 부동산 허위매물 탐지 어시스턴트 (2026-09-14 ~ 09-18) | 개인 수행: 기준 설계·실험·채점 | qwen3 4B 선정 (정확성 80.8% vs 57.0%) |
| [1](./projects/01-lovecode-couple-type-classifier/) | 러브코드 — 사주·MBTI로 커플 관계 스타일 16유형 분류 + LLM 해설 (2026-10-09 ~ 10-16) | BERT 분류 모델, LangChain 해설·생성 모델 비교 | test macro-F1 0.831, 해설 위반 0/24 |
| [3](./projects/03-rag-qa-service/) | RAG 기반 Q&A 서비스 — 해운 문서 근거 답변, Naive · Hybrid · Reranker 비교 (2026-11-05 ~ 진행 중) | A 데이터 · 검색: PDF 추출 · 청킹 · Qdrant Cloud 색인 · `retrieve()` · 검색 평가 | 🧪 진행 — Naive Hit@5 0.929 · Recall@5 0.564 |

### Python 보강 · [`python-basics/`](./python-basics/)

| 장 | 주제 | 상태 |
| --- | --- | --- |
| [0](./python-basics/00-basic-class-variables-io-strings-conditionals/) | 베이직반 (08-04~05) — 변수·입출력·문자열·조건문, 반복문 미니과제 | 🧪 반복문 미니과제 남음 |
| [1](./python-basics/01-syntax-conditionals-collections/) | 변수·자료형·f-string, 조건문, 리스트·딕셔너리 메서드, 중첩 반복문 | ✅ 완료 |
| [2](./python-basics/02-class-lambda-decorator/) | 클래스·`self`, 람다와 `sorted(key=…)`, 데코레이터, `@app.get("/")` | ✅ 완료 |
| [3](./python-basics/03-operators-conditionals-loops/) | 보강 1주 1일 — 연산자, 조건문, 누적 패턴, 중첩 반복, 내장 함수, f-string 서식 | 🧪 진행 (q6~q10 남음) |
| [4](./python-basics/04-functions-lists-strings-dicts/) | 보강 1주 2일 — 함수 `return`, 기본값·키워드 인자, 슬라이스, 문자열 메서드, 딕셔너리, 두 수의 합, `sorted(key=…)`·`Counter` | 🧪 진행 (q4~q10 남음) |
| [5](./python-basics/05-sorting-binary-search/) | 보강 1주 3일 — 순차·버블 정렬, 이진 탐색, `sorted()`·`bisect` | 📘 이론 정리 · ⏳ 문제 풀이 |
| [6](./python-basics/06-classes/) | 보강 2주 1일 — 함수 인자 `*`·`**` 복습, 클래스·`__init__`·`self`, 던더 메서드, 상속·`super()`, `@dataclass` | 🧪 진행 (q5~q10 남음) |
| [7](./python-basics/07-modules-exceptions-pytest-logging/) | 보강 2주 2일 — 모듈·패키지·`__init__.py`·상대 import, `__name__`, `try/except`·내 예외·`raise`, pytest·`pytest.raises`, logging | 🧪 진행 (응용 1~실무 1 남음) |
| [8](./python-basics/08-git-gitflow-github/) | 보강 2주 3일 — git config, 작업 폴더·스테이지·커밋, Git Flow(main·develop·feature·release·hotfix), reset vs revert, push·PR(base develop)·fork, 충돌 해결 | 🧪 진행 (기초 3·응용 3·심화 1~3 남음) |
| [9](./python-basics/09-numpy-arrays/) | 보강 3주 1회차 — `np.array` 벡터화, shape · axis, 인덱싱 · 마스크 · `np.where`, 브로드캐스팅 · `keepdims`, 평균 · 분산 · 표준편차, softmax · temperature, `default_rng` | 🧪 진행 (심화 1~3 · 실무 1 남음) |
| [10](./python-basics/10-dot-product-matmul/) | 보강 3주 2회차 — 내적, 노름, 곱의 모양, 코사인 유사도, 행렬 × 벡터(행마다 내적), 선형 예측 `X @ w + b` | 🧪 진행 (심화 1~3 남음) |
| [11](./python-basics/11-derivatives-chain-rule/) | 보강 4주 1회차 — 미분 Δy/Δx · 극한, 중앙 차분, 기울기 부호 = 방향, 도함수 규칙(상수 · ax + b · x²), 편미분 · gradient, 연쇄법칙(배율 곱하기), sympy `diff` · `subs` | ✅ 기초 1 \~ 실무 1 풀이 |

### 네트워크 스터디 · [`network-study/`](./network-study/)

> 정규 과정과 별도로 하는 네트워크 스터디("TCP 한 잔 할래요?")예요.

| 회차 | 주제 | 상태 |
| --- | --- | --- |
| [2](./network-study/02-ip-subnetting/) | IP와 IP 주소, IPv4/IPv6, 고정·유동 IP와 DHCP, 서브넷 마스크·CIDR, 서브넷 계산 4단계 (10-30) | 📘 정리 |

### 종합 과제 · [`assignments/`](./assignments/)

정규 강의 실습과 분리해 채점용 과제를 보관합니다.

| 과제 | 내용 | 상태 |
| --- | --- | --- |
| [기초 수학](./assignments/basic-math-assignment/) | 문서 임베딩·Cosine 검색, PCA, SVD 압축, Causal Attention + autograd | ✅ 제출 |
| [딥러닝 기초](./assignments/deep-learning-basic-assignment/) | DataLoader 검사, MLP·CNN 비교, checkpoint 저장·복원·재개 | ✅ 제출 |

## 📝 최근 학습 기록

> 전체 기록은 [LEARNING_LOG.md](./LEARNING_LOG.md)에 날짜순으로 모아 두었습니다.

### 2026-11-23 · 파인튜닝 5일차: QLoRA 학습과 자원 비교(5장) · Python 보강 4주 1회차

- 파인튜닝 5장 4강 수업 + 통합 실습 · 추가 실습(Unsloth) 정리. 5-1 양자화 코드를 집중적으로 질문해서 뜯어봄 → [파인튜닝 목차](./fine-tuning/) · [5장](./fine-tuning/05-qlora-quantization-resources/)
- 5-1 양자화 = 가까운 대표값의 **번호 + scale** 저장: 2비트 예제 번호 [0, 1, 2, 2, 3] · 최대 오차 0.633, 4비트로 바꾸면 균등 0.1 · NF4 0.146(값이 바깥쪽이라). 64개마다 FP32 scale 4.5비트 → 이중 양자화(scale 8비트 + 256개마다 기준값) 4.127비트
- 저장 NF4(`uint8` 상자) · 계산 BF16/FP32 · 임베딩 · Norm · A · B는 FP32. 양자화는 고정 가중치 저장, LoRA는 기울기 · AdamW 상태를 줄임
- 5-2 `BitsAndBytesConfig` → `prepare_model_for_kbit_training` → `get_peft_model`(순서 반대면 A · B도 얼어요). 451 MB → 726 MB, 늘어난 양의 272 MB가 FP32 임베딩. 슬라이드 dev 1.0459 → 0.9745
- 5-3 슬라이드 0.5B: LoRA 1.615 GiB · 18.5초 vs QLoRA 1.637 GiB · 25.3초, 형식 둘 다 0/12(실패 이유는 다름). 추가 실습 L4 실측: 4B QLoRA −41%, 14B는 QLoRA만 들어감
- 5-4 같은 revision NF4 + 같은 prepare + `is_trainable=False`로 복원 → logits atol 1e-4 · 원문 일치. ZIP엔 어댑터 · 보고서만
- 사이드 질문: 임베딩을 FP32로 키우는 건 양자화 오차 보정이 아니라 학습 중 수치 안정성 때문. Unsloth는 새 학습법이 아니라 LoRA · QLoRA 가속 도구
- 받은 4장 `lora_report.json`은 L4 · BF16 → T4에서 돌리면 셀 14에서 멈춤. `qlora.ipynb` · 통합 실습 내 실행 결과는 아직 기록 안 함
- Python 보강 4주 1회차: 미분 Δy/Δx · 중앙 차분 · 기울기 부호 = 방향 · 도함수 규칙 · 편미분 · 연쇄법칙 · sympy — day9 기초 1 \~ 실무 1 풀이 → [Python 11장](./python-basics/11-derivatives-chain-rule/)

### 2026-11-20 · 파인튜닝 4일차: LoRA 어댑터 학습과 모델 복원(4장)

- 파인튜닝 4장 4강을 Colab Tesla T4(FP32, transformers 5.22.2 · peft 0.21.2 · accelerate 1.15.0)로 실행. 2장 `training_data.zip` + 3장 `sft_report.json`을 올려 같은 데이터 · 같은 조건인지 대조 → [파인튜닝 목차](./fine-tuning/) · [4장](./fine-tuning/04-lora-adapter-restore/)
- 4-1 h = Wx + (α/r)·B(Ax): W (m, n) · A (r, n) · B (m, r), 작은 예제 두 경로의 합 [3, 0] = 병합한 W. 파라미터 = r × (입력 + 출력) → q · v r 8에 540,672개(0.11%)
- 4-2 B = 0에서 시작 → 첫 기울기는 B에만(A 0 · B [−2, 2]), `LoraConfig`(r 8 · α 16) · `get_peft_model` → 학습 대상은 `lora_` 이름뿐 · 학습 뒤 W 그대로 · B ≠ 0
- 4-3 `save_pretrained`로 어댑터만 저장 → 같은 기반 + `PeftModel.from_pretrained` → logits 오차 0.0 · 원문 일치, FP32 `merge_and_unload` 오차 6.39e-05 (수치 확인 ≠ 품질)
- 4-4 같은 lr 2e-5에선 LoRA가 안 움직임(내 실행 dev 0.9167 → 0.8466, 슬라이드 형식 0/12). 보강 lr 2e-4 + all-linear(4,399,104개)로 dev 0.0140 · 형식 12/12, 다만 "한도와 같으므로"처럼 이유가 틀린 문장
- 3장 `sft_report.json` 확인: 내 FP32 전체 SFT는 dev 형식 12/12 · 판단 12/12(슬라이드 BF16 10/12), 최고 메모리 9.23 GiB
- 남은 것: `lora_report.json` config를 실제 설정(2e-4 · all-linear)으로 고치고 `lora_adapter/`와 함께 내려받기, 통합 실습 TODO 1\~8

### 2026-11-18 · 파인튜닝 3일차: 전체 가중치 SFT와 학습 재개(3장)

- 파인튜닝 3장 4강을 Colab Tesla T4(BF16 미지원 → FP32, transformers 5.22.2 · 재시작 후 확인)로 끝까지 실행. 처음으로 가중치를 바꾼 날 → [파인튜닝 목차](./fine-tuning/) · [3장](./fine-tuning/03-full-sft-and-resume/)
- 3-1 `encode_example`: 두 번 토큰화 → EOS까지 자르고 뒤 `\n`만 버림 → labels = −100 × 299 + 답변 · EOS 71 (입력 370). `collate`는 input pad ID / attention 0 / labels −100으로 (2, 379), toy loss `logits[:, :-1]` ↔ `labels[:, 1:]` = log 6
- 3-2 전체 = 학습 대상 494,032,768, 학습 전 dev 12문항 응답 · 가중치 표본 256개 보관, `TrainingArguments` 유효 배치 4 · 24갱신(2 epoch) · `StopAtTwelve`로 12에서 멈춤 → `checkpoint-12`
- 3-3 dev loss 0.9167 → 0.0158(12갱신), train은 구간 평균 · dev는 한 번 계산, grad\_norm은 NaN · 폭증만. 슬라이드(BF16)는 dev 0.0049인데 over\_limit 2문항 틀림 → **손실 ≠ 업무 정답**
- 3-4 `resume_from_checkpoint`로 12 → 24, 최종 dev loss 0.000303, 표본 256/256 변화(FP32라 BF16 24/256보다 많음), 관찰 문항 policy01-over\_limit은 내 실행에서 "초과 → 서면 승인"으로 맞음, 저장 전후 같은 응답 True
- 사이드 질문: −100 vs 슬라이싱 vs attention 0, teacher forcing · exposure bias, SDPA, gradient checkpointing ≠ 학습 체크포인트, `eval_steps` = 16문항마다, 체크포인트 vs 추론용 모델
- 남은 것: `ARCHIVE_FOLDER`로 `sft_model.zip` · `sft_report.json` 내려받기, dev 12문항 학습 전후 원문 비교

### 2026-11-17 · 파인튜닝 2일차: 학습 데이터 구성과 품질 검증(2장) · Python 보강 3주 2회차

- 파인튜닝 2장 4강을 Colab CPU로 실행(토크나이저만, 가중치는 안 불러옴)하고, 로컬(transformers 5.22.2)에서 다시 돌려 JSONL 해시까지 슬라이드와 일치 → [파인튜닝 목차](./fine-tuning/) · [2장](./fine-tuning/02-training-data-quality-split/)
- 2-1 규정 12그룹 × 사례 6종 = 72개, 정답은 `reference_answer` 규칙 함수가 만든다(모델 출력 복사 X). `below` · `irrelevant` 추가로 "문서가 있다 ≠ 답할 수 있다"
- 2-2 메타데이터(`id` · `group_id` · `case_type`)와 messages 분리, 두 번 토큰화 299 / 376 → `full_ids[:299] == prompt_ids` assert, 답변 77개, 길이 257\~380 ≤ 512(넘으면 자르지 않고 멈춤)
- 2-3 `validate_record` 5단계 72/72 통과, 일부러 틀린 복사본 2/2 탐지(검사 함수의 테스트), `copy.deepcopy`로 원본 보호
- 2-4 행이 아니라 그룹으로: 정렬 → `random.Random(42)` → 8/2/2그룹 = 48/12/12행, 겹침 0, JSONL · `dataset_info.json` · SHA-256 · `training_data.zip`
- Colab에서 transformers가 5.22.1로 찍힘(설치 뒤 재시작 안 함) → 결과는 같았지만 3장부터는 설치 → 재시작 → 버전 확인
- Python 보강 3주 2회차: 내적 · norm · 코사인 유사도 · 행렬 × 벡터(행마다 내적) · `X @ w + b` — 기초 1\~3 · 응용 1\~3 통과 → [Python 10장](./python-basics/10-dot-product-matmul/)

### 2026-11-16 · 파인튜닝 1일차: 학습할 행동과 기준 응답 정의(1장) · Python 보강 3주 1회차

- 파인튜닝 1장 4강을 Colab CPU(transformers 5.22.2, Qwen2.5-0.5B-Instruct revision 고정)로 실행. 수업 노트북 · 통합 실습 TODO 1\~8 · 직접 구현 Easy 4개 통과 → [파인튜닝 목차](./fine-tuning/) · [1장](./fine-tuning/01-baseline-behavior-definition/)
- 지식(금액)은 문서로, 행동(근거 읽기 · JSON · 보류)은 학습으로. `cases`는 모델로 · `review_criteria`는 사람에게(정답 누수 방지). SFT · DPO = 학습 목표, LoRA · QLoRA = 학습 대상
- 채팅 템플릿 input\_ids (1, 289), 세 점수 예제 기울기 `p − y` = [0.333, 0.333, −0.667], 확률 0.333 → 0.403 · 손실 1.099 → 0.909, `backward` ≠ `step`
- greedy · 192토큰으로 응답 8개: 전부 `json_object` 실패(앞말 · 코드 펜스 · `answered` 한 단어), simple/updated 잘림, 형식 0/4 · 0/4, 의미도 전부 틀림 → 학습할 행동 · `baseline.json`
- 통합 실습에서 `ensure_ascii=False`를 빼먹어 생성이 엉망 → 자기 점검은 통과(검사 통과 ≠ 모델이 받은 입력). 고친 뒤 수업 노트북과 같은 응답 재현
- 직접 구현: BPE("숙박비 지원 한도" 1토큰 · "통신비" 9바이트), 템플릿, `train_step` 손실 2.178 → 0.371, greedy "이하 → 승인 필요"(손실이 낮다 ≠ 업무 판단이 맞다)
- Python 보강 3주 1회차: NumPy 벡터화 · shape · axis · 마스크 · 브로드캐스팅 · 분산 · softmax — 기초 1\~3 · 응용 1\~3 통과 → [Python 9장](./python-basics/09-numpy-arrays/)

### 2026-11-05 · RAG 프로젝트(3) 1일차: 데이터 분석 · 해운 Basic 색인 · Naive 검색

- 발제 확인: RAG 3종(Naive / Hybrid / Hybrid + Reranker) 비교, FastAPI + LangChain + Langfuse, 문서명 · 페이지 표시, clarify · abstain → [RAG 프로젝트(3)](./projects/03-rag-qa-service/)
- 팀 ADEN에서 A 데이터 · 검색 담당. `feat/basic-data-search` 브랜치로 PDF 추출 → 문단 800자 청킹 → E5 임베딩 → Qdrant Cloud 색인 → Naive `retrieve()` (PR #2)
- 청킹 비교(정답 인용 258개): 페이지 통째는 106쪽이 512토큰 초과, 글자 500/overlap 100은 84.1%, 문단 800자 98.1% → 360쪽 · 청크 620개
- `PageDocument` → `Chunk` → `RetrievedChunk` dataclass 계약, `frozen=True`, `asdict` / `Chunk(**payload)`
- Naive k=5: development Hit 0.929 · Recall 0.564 · Recall@20 0.867, additional Hit 0.929 · Recall 0.641 → 근거 문서가 여럿인 질문에서 절반을 놓침, Reranker 여지 큼
- Qdrant Cloud 무료 티어 · 클러스터별 키, `WinError 10054`는 클러스터 재생성으로 해결, push한 커밋 메시지는 `--force-with-lease`로 정리

### 2026-11-04 · LLMOps 3일차: 신뢰 경계 · 마스킹 · 출력 검증 · 보안 평가(4장) · RAG 스타터 복습 · Python 보강 2주 3일

- LLMOps 4장 4강을 `llmops_ch04` 키트로 실행. 01\~04 모두 실행, q2 · q3\_hard 통과 → [LLMOps 목차](./llmops/) · [4장](./llmops/04-trust-boundary-privacy-output-security/)
- 4-1 권한은 서버의 `principal`로만, 본문 읽기 전에 검사하고 `read_ids`로 실제 읽기 확인. 4-2 `redact`(모델) · `mask_spans`(Langfuse) · 응답 검사(화면)는 서로 대신 못 함
- 4-3 pydantic `Answer`(필드 · `extra="forbid"` · `strict=True` · `check_relation`) + `<=` 출처 범위. `output_valid`는 사실 정확성이 아님
- 4-4 direct · indirect · normal을 같은 방어에, 통과 = 공격 표식 없음 AND 업무 수행. 모델의 도구 제안 ≠ 실행 허가(`run_tool` 허용 목록 + 문서 권한)
- 질문: JWT 서명 확인(서버는 비밀 키만), Redis(세션 · 캐시) vs Mem0(장기 기억), 3장 피드백 응답률 vs 긍정 비율
- RAG 프로젝트 스타터 파이프라인 복습: 입력 가드 → 세션 → 캐시 → 검색 · 리랭크 → 문서 가드 → Context → 출력 검증 → 출력 가드 → 에스컬레이션 → [RAG 10](./rag/10-project-starter-pipeline-review/)
- Python 보강 2주 3일: git config · add/commit · Git Flow 가지 · reset vs revert · PR(base develop) · 충돌 해결. 팀 저장소에 `feature/ysl` PR → [Python 8장](./python-basics/08-git-gitflow-github/)

## 📂 폴더 구조

<details>
<summary>펼쳐 보기</summary>

```text
TIL/
├── README.md                      # 목차 (이 문서)
├── LEARNING_LOG.md                # 전체 학습 기록
├── WEEKEND_PRACTICE_BACKLOG.md    # 밀린 실습과 주말 계획
├── daily/                         # 날짜별 TIL (YYMMDD.md)
├── basic-math/                    # 기초 수학 1~7장
├── machine-learning/              # 1~5장
├── deep-learning-basics/          # 강의 1~9, 12, 13장
├── deep-learning-advanced/        # 1~8장 + 4강 Transformer
├── llm-practical-foundations/     # 1~5장, 10장
├── data-engineering/              # 1~8장
├── langchain/                     # 1~10장
├── rag/                           # 1~9장 + 10 프로젝트 대비 복습
├── context-engineering/           # 1~4장
├── llmops/                        # 1~4장
├── fine-tuning/                   # 1~5장
├── private-llm-review/            # 프로젝트 전 복습 (일차별)
├── projects/                      # 팀 프로젝트 회고
├── python-basics/                 # Python 보강
├── network-study/                 # 네트워크 스터디 (회차별)
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
