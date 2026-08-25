# TIL: Private LLM Engineer Journey

> Repository structure through Deep Learning Chapter 7, updated on 2026-08-25.

KANT Private LLM 엔지니어 교육과정에서 학습하고 직접 실험한 내용을 기록합니다.
강의 원문을 옮기기보다 이해한 내용, 코드로 검증한 결과, 다음에 보완할 점을 중심으로 정리합니다.

## Current Status

- 과정: KANT Private LLM 엔지니어 교육과정
- 현재 단계: Deep Learning Foundations
- 현재 주제: Autograd, 안전한 평가, Dataset과 DataLoader
- 목표: 평가와 운영까지 고려하는 LLM 엔지니어

## Contents

| Area | Topics | Status |
| --- | --- | --- |
| Math Foundations | Vector, matrix, similarity, softmax, cross-entropy | Review |
| Machine Learning | Evaluation, ensembles, regularization, CV, leakage, pipeline | In progress |
| Deep Learning | Tensor, MLP, loss, optimizer, Autograd, data pipeline | In progress |
| LLM · RAG · Agent · Serving | Fine-tuning, retrieval, tool use, deployment | Planned |

## Repository Structure

머신러닝 이전 기록은 폴더 단위로만 간단히 표시하고, 현재 학습 중인 딥러닝은 실제 파일까지 표시합니다.

```text
TIL/
├── README.md
├── WEEKEND_PRACTICE_BACKLOG.md
├── machine-learning/
│   ├── 01-model-evaluation/
│   ├── 02-tree-ensembles/
│   ├── 03-bias-variance-regularization/
│   ├── 04-class-imbalance-cv-leakage/
│   └── 05-cv-tuning-end-to-end-pipeline/
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
    ├── 04-loss-optimization-training-loop/
    │   ├── README.md
    │   ├── 01-loss-function-basic.ipynb
    │   ├── 02-loss-function-advanced.ipynb
    │   ├── 03-task-loss-selection-basic.ipynb
    │   ├── 04-task-loss-selection-advanced.ipynb
    │   ├── 05-optimizer-learning-rate-basic.ipynb
    │   ├── 06-optimizer-learning-rate-advanced.ipynb
    │   ├── 07-parameter-update-flow-basic.ipynb
    │   ├── 08-parameter-update-flow-advanced.ipynb
    │   └── requirements.txt
    └── 05-autograd-data-pipeline/
        ├── README.md
        ├── 01-computation-graph-chain-rule-basic.ipynb
        ├── 02-computation-graph-chain-rule-advanced.ipynb
        ├── 03-requires-grad-basic.ipynb
        ├── 04-requires-grad-advanced.ipynb
        ├── 05-backward-grad-basic.ipynb
        ├── 06-backward-grad-advanced.ipynb
        ├── 07-training-step-order-basic.ipynb
        ├── 08-training-step-order-advanced.ipynb
        ├── 09-autograd-debugging-basic.ipynb
        ├── 10-autograd-debugging-advanced.ipynb
        └── requirements.txt
```

## Recent Learning Log

### 2026-08-25

- 계산 그래프와 Chain Rule, leaf·non-leaf Tensor와 gradient 저장 위치
- `requires_grad`, `backward()`, gradient 누적과 표준 step 순서
- `grad is None`과 값이 0인 gradient의 의미 구분
- `model.eval()`과 `torch.no_grad()`, 학습 Loss 경로와 metric용 `detach()` 구분
- 입력 scale과 gradient norm, `isfinite` 기반 Autograd 점검
- `Dataset → DataLoader → batch`와 `TensorDataset`·Custom Dataset 역할

### Earlier in 2026-08

- 머신러닝: 평가·ensemble·regularization·CV·leakage·end-to-end pipeline
- 딥러닝: Tensor·device·MLP·activation·분류 출력층·Loss·optimizer·training loop
- Python: `set()`, `zip()`, `next()`, `all()`, `p.numel()`, class와 `forward`

## Recording Principles

- 교육자료 원본 대신 직접 작성한 코드와 해석을 공개합니다.
- 실행 환경, seed, shape·dtype·device와 평가 기준을 기록합니다.
- 성공한 결과뿐 아니라 미실행 셀, 오류 원인과 다음 검증 계획도 남깁니다.
- API key, 개인정보 및 사용 권한이 불분명한 데이터는 올리지 않습니다.
