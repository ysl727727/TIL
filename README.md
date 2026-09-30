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
| 현재 단계 | 데이터 엔지니어링 → LLM 애플리케이션(LangChain) |
| 최근 학습 | **2026-09-29** · 밀린 3회차 정리 — 데이터 엔지니어링 4\~8장, LLM 실전 10-1강(보강), LangChain 1\~2장, Python 보강 드릴 |
| 이번 주말 | **10/03\~04** · LangChain 1장 통합 실습 TODO 1\~3 → 10-1강 retry 함수 직접 작성 → 데이터 엔지니어링 3장 실습 |
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
    class LLM,DE,LC now
    class RAG,AG,OPS next
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

### Python 보강 · [`python-basics/`](./python-basics/)

| 장 | 주제 | 상태 |
| --- | --- | --- |
| [1](./python-basics/01-syntax-conditionals-collections/) | 변수·자료형·f-string, 조건문, 리스트·딕셔너리 메서드, 중첩 반복문 | ✅ 완료 |

### 종합 과제 · [`assignments/`](./assignments/)

정규 강의 실습과 분리해 채점용 과제를 보관합니다.

| 과제 | 내용 | 상태 |
| --- | --- | --- |
| [기초 수학](./assignments/basic-math-assignment/) | 문서 임베딩·Cosine 검색, PCA, SVD 압축, Causal Attention + autograd | ✅ 제출 |
| [딥러닝 기초](./assignments/deep-learning-basic-assignment/) | DataLoader 검사, MLP·CNN 비교, checkpoint 저장·복원·재개 | ✅ 제출 |

## 📝 최근 학습 기록

> 전체 기록은 [LEARNING_LOG.md](./LEARNING_LOG.md)에 날짜순으로 모아 두었습니다.

### 2026-09-29 · LangChain 기초와 Python 보강 드릴

- SDK 직접 호출과 LangChain은 모델이 같아 답변 품질이 아니라 **코드 구성 방식**이 다름 — LangChain은 `Prompt → Model → Parser` 세 역할로 나눔
- `model.invoke()`는 문자열이 아니라 `AIMessage`를 반환, 본문만 쓰려면 Parser가 필요
- `.gitignore`는 앞으로의 추적만 막을 뿐, 이미 올라간 키를 무효화하지 않음
- Parser는 형식을 **강제하지 않음** — `get_format_instructions()`를 Prompt에 넣는 단계가 따로 필요
- 통합 실습 노트북은 TODO 1\~3이 `NotImplementedError` 상태로 **미완료**, 주말로 이월

### 2026-09-23 · 데이터 엔지니어링: Query API, 비동기 호출, API 안정성

- 질문 요청은 `document_id`와 `context` 중 **하나만** 허용 — 근거가 무엇인지 분명하게 하기 위함
- 외부 실패는 그대로 흘리지 않고 422 / 404 / 502 / 503으로 우리 API 코드로 변환
- 비동기는 **대기 시간이 겹칠 때만** 빨라지고, `asyncio.gather()` 결과는 입력 순서를 따름
- 재시도 계층을 겹치면 최대 27회까지 늘어남 — retry 책임은 한 계층에만 둠 (LLM 실전 10-1강 보강)

### 2026-09-22 · 데이터 엔지니어링: 정제, FastAPI, Pydantic

- 정제는 원본을 덮어쓰지 않고 별도 산출물을 만드는 일, `입력 = 정상 + 중복 제외 + 규칙 제외` 등식으로 1차 검증
- FastAPI는 경로·함수를 **선언**하고 Uvicorn이 포트를 열어 **실행** — 코드에 포트가 없는 이유
- 요청 모델과 응답 모델을 나누고 `response_model`로 응답 필드를 고정
- 4\~8장은 강의 교안만 받아 이론만 정리

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
├── langchain/                     # 1~2장
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
