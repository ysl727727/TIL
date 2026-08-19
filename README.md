# TIL: Private LLM Engineer Journey

> Target repository structure through Deep Learning Chapter 2, updated on 2026-08-19.

KANT Private LLM 엔지니어 교육과정에서 학습하고 직접 실험한 내용을 기록하는 저장소입니다.

강의 내용을 그대로 옮기기보다 다음 세 가지를 중심으로 정리합니다.

1. 무엇을 이해했는가
2. 코드로 무엇을 검증했는가
3. 실험 결과에서 어떤 결론을 얻었는가

## Current Status

- 과정: KANT Private LLM 엔지니어 교육과정
- 현재 단계: Deep Learning Foundations
- 현재 주제: PyTorch training flow, tensor dtype, shape, batch, and broadcasting
- 목표: 평가와 운영까지 고려하는 LLM 엔지니어

## Contents

| Area | Topics | Status |
| --- | --- | --- |
| Math Foundations | Vector, matrix, cosine similarity, softmax, cross-entropy | In progress (review) |
| Machine Learning | Evaluation, ensembles, regularization, CV, leakage prevention, pipeline | In progress |
| Deep Learning | Training flow, problem I/O, PyTorch tensor, dtype, shape, batch | In progress |
| LLM | Hugging Face, fine-tuning, evaluation | Planned |
| RAG | Retrieval, reranking, RAG evaluation | Planned |
| AI Agent | Tool calling, LangGraph, MCP | Planned |
| LLMOps & Serving | Monitoring, vLLM, container and cloud deployment | Planned |

## Repository Structure

```text
TIL/
├── README.md
├── WEEKEND_PRACTICE_BACKLOG.md
├── machine-learning/
│   ├── 01-model-evaluation/
│   │   ├── README.md
│   │   ├── model-evaluation-and-thresholding.ipynb
│   │   └── requirements.txt
│   ├── 02-tree-ensembles/
│   │   ├── README.md
│   │   ├── ensemble-candidate-comparison.ipynb
│   │   └── requirements.txt
│   ├── 03-bias-variance-regularization/
│   │   └── README.md
│   ├── 04-class-imbalance-cv-leakage/
│   │   └── README.md
│   └── 05-cv-tuning-end-to-end-pipeline/
│       ├── README.md
│       ├── cv-search-basic.ipynb
│       ├── cv-search-advanced.ipynb
│       ├── end-to-end-pipeline-basic.ipynb
│       ├── artifact-schema-guard-advanced.ipynb
│       └── requirements.txt
└── deep-learning/
    └── 01-pytorch-foundations/
        ├── README.md
        ├── 01-ml-vs-dl-basic.ipynb
        ├── 02-ml-vs-dl-advanced.ipynb
        ├── 03-training-flow-basic.ipynb
        ├── 04-problem-io-basic.ipynb
        ├── 05-pytorch-code-reading-basic.ipynb
        ├── 06-tensor-dtype-shape-basic.ipynb
        ├── 07-batch-broadcasting-basic.ipynb
        └── requirements.txt
```

아직 생성하지 않은 Math Foundations, LLM, RAG, Agent와
LLMOps·Serving 폴더는 위의 실제 파일 구조에 포함하지 않았습니다.

## Learning Log

### 2026-08

- Linear algebra fundamentals and cosine similarity
- Regression baseline comparison
- Classification metrics for imbalanced and high-cost errors
- Validation-based threshold selection
- Preventing data leakage and test-set reuse
- Bagging, Random Forest, Boosting, and model interpretation
- First ensemble candidate comparison and coding improvement plan
- Bias-variance diagnosis with learning and validation curves
- Ridge, Lasso, and ElasticNet comparison principles
- Mathematics review and weekend study plan after the AI competency assessment
- Class imbalance metrics, CV splitters, and leakage prevention principles
- Fair Grid and Random Search under the same CV budget
- End-to-end preprocessing, resampling, tuning, persistence, and schema guards
- Consolidated weekend backlog for unfinished and guided practices
- Rule-based, machine-learning, and deep-learning approach selection
- PyTorch training flow, problem-output-loss mapping, and code structure reading
- Tensor dtype conversion, batch dimension, and broadcasting practice

## Recording Principles

- 교육자료 원본 대신 직접 작성한 코드와 해석만 공개합니다.
- 실행 환경, 데이터, random seed와 평가 지표를 기록합니다.
- 성공한 결과뿐 아니라 오류와 개선 방향도 남깁니다.
- API key, 개인정보 및 사용 권한이 불분명한 데이터는 올리지 않습니다.
