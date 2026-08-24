# TIL: Private LLM Engineer Journey

> Target repository structure through Deep Learning Chapter 5, updated on 2026-08-24.

KANT Private LLM 엔지니어 교육과정에서 학습하고 직접 실험한 내용을 기록하는 저장소입니다.

강의 내용을 그대로 옮기기보다 다음 세 가지를 중심으로 정리합니다.

1. 무엇을 이해했는가
2. 코드로 무엇을 검증했는가
3. 실험 결과에서 어떤 결론을 얻었는가

## Current Status

- 과정: KANT Private LLM 엔지니어 교육과정
- 현재 단계: Deep Learning Foundations
- 현재 주제: Loss function, optimizer, learning rate와 parameter update flow
- 목표: 평가와 운영까지 고려하는 LLM 엔지니어

## Contents

| Area | Topics | Status |
| --- | --- | --- |
| Math Foundations | Vector, matrix, cosine similarity, softmax, cross-entropy | In progress (review) |
| Machine Learning | Evaluation, ensembles, regularization, CV, leakage prevention, pipeline | In progress |
| Deep Learning | Tensor, MLP, activation, loss, optimizer, learning rate, training loop | In progress |
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
    ├── 01-pytorch-foundations/
    │   ├── README.md
    │   ├── 01-ml-vs-dl-basic.ipynb
    │   ├── 02-ml-vs-dl-advanced.ipynb
    │   ├── 03-training-flow-basic.ipynb
    │   ├── 04-problem-io-basic.ipynb
    │   ├── 05-pytorch-code-reading-basic.ipynb
    │   ├── 06-tensor-dtype-shape-basic.ipynb
    │   ├── 07-batch-broadcasting-basic.ipynb
    │   ├── 08-device-basic.ipynb
    │   ├── 09-device-advanced.ipynb
    │   ├── 10-shape-device-debugging-basic.ipynb
    │   └── requirements.txt
    ├── 02-mlp-foundations/
    │   ├── README.md
    │   ├── 01-perceptron-linear-boundary-basic.ipynb
    │   ├── 02-mlp-layers-basic.ipynb
    │   ├── 03-linear-weight-bias-basic.ipynb
    │   ├── 04-image-flatten-basic.ipynb
    │   ├── 05-mlp-forward-basic.ipynb
    │   └── requirements.txt
    ├── 03-activation-output-layers/
    │   ├── README.md
    │   ├── 01-nonlinearity-basic.ipynb
    │   ├── 02-nonlinearity-advanced.ipynb
    │   ├── 03-relu-basic.ipynb
    │   ├── 04-relu-advanced.ipynb
    │   ├── 05-sigmoid-binary-basic.ipynb
    │   ├── 06-sigmoid-binary-advanced.ipynb
    │   ├── 07-softmax-multiclass-basic.ipynb
    │   ├── 08-softmax-multiclass-advanced.ipynb
    │   └── requirements.txt
    └── 04-loss-optimization-training-loop/
        ├── README.md
        ├── 01-loss-function-basic.ipynb
        ├── 02-loss-function-advanced.ipynb
        ├── 03-task-loss-selection-basic.ipynb
        ├── 04-task-loss-selection-advanced.ipynb
        ├── 05-optimizer-learning-rate-basic.ipynb
        ├── 06-optimizer-learning-rate-advanced.ipynb
        ├── 07-parameter-update-flow-basic.ipynb
        ├── 08-parameter-update-flow-advanced.ipynb
        └── requirements.txt
```

아직 생성하지 않은 Math Foundations, LLM, RAG, Agent와 LLMOps·Serving 폴더는
위의 실제 파일 구조에 포함하지 않았습니다.

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
- CPU/GPU device placement and shape·dtype·device error debugging
- Perceptron, linear decision boundary, MLP layers, and `nn.Linear` parameters
- Image flattening, MLP `forward`, parameter counting, and the motivation for CNNs
- Python practice with `set()`, `zip()`, `next()`, and `p.numel()`
- Non-linearity, ReLU placement, and Dead ReLU diagnostics
- Binary classification with raw logits, Sigmoid inference, and `BCEWithLogitsLoss`
- Multiclass classification with class logits, Softmax axes, and `CrossEntropyLoss`
- Tensor utilities and contracts with `linspace`, `cat`, `dim=-1`, and element-wise `&`
- Loss calculation, scalar reduction, and task-specific output-target-loss contracts
- SGD and Adam behavior, learning-rate experiments, and non-finite loss checks
- Standard five-step training flow from `zero_grad()` to `optimizer.step()`
- Training audit logic with `all()`, `zip()`, `next()`, call-order indexes, and unique approval rules
- Safe metric logging with `loss.item()` to avoid retaining computation graphs

## Recording Principles

- 교육자료 원본 대신 직접 작성한 코드와 해석만 공개합니다.
- 실행 환경, 데이터, random seed와 평가 지표를 기록합니다.
- 성공한 결과뿐 아니라 오류와 개선 방향도 남깁니다.
- API key, 개인정보 및 사용 권한이 불분명한 데이터는 올리지 않습니다.
