# TIL: Private LLM Engineer Journey

KANT Private LLM 엔지니어 교육과정에서 학습하고 직접 실험한 내용을 기록하는 저장소입니다.

강의 내용을 그대로 옮기기보다 다음 세 가지를 중심으로 정리합니다.

1. 무엇을 이해했는가
2. 코드로 무엇을 검증했는가
3. 실험 결과에서 어떤 결론을 얻었는가

## Current Status

- 과정: KANT Private LLM 엔지니어 교육과정
- 현재 단계: Machine Learning
- 현재 주제: baseline, evaluation metrics, data split, threshold policy
- 목표: 평가와 운영까지 고려하는 LLM 엔지니어

## Contents

| Area | Topics | Status |
| --- | --- | --- |
| Math Foundations | Vector, matrix, cosine similarity, softmax, cross-entropy | Completed |
| Machine Learning | Baseline, metrics, cross-validation, error analysis | In progress |
| Deep Learning | PyTorch, training loop, Transformer | Planned |
| LLM | Hugging Face, fine-tuning, evaluation | Planned |
| RAG | Retrieval, reranking, RAG evaluation | Planned |
| AI Agent | Tool calling, LangGraph, MCP | Planned |
| LLMOps & Serving | Monitoring, vLLM, container and cloud deployment | Planned |

## Repository Structure

```text
TIL/
├── README.md
├── math-foundations/
├── machine-learning/
│   └── 01-model-evaluation/
├── deep-learning/
├── llm/
├── rag/
├── agents/
└── llmops-serving/
```

## Learning Log

### 2026-08

- Linear algebra fundamentals and cosine similarity
- Regression baseline comparison
- Classification metrics for imbalanced and high-cost errors
- Validation-based threshold selection
- Preventing data leakage and test-set reuse

## Recording Principles

- 교육자료 원본 대신 직접 작성한 코드와 해석만 공개합니다.
- 실행 환경, 데이터, random seed와 평가 지표를 기록합니다.
- 성공한 결과뿐 아니라 오류와 개선 방향도 남깁니다.
- API key, 개인정보 및 사용 권한이 불분명한 데이터는 올리지 않습니다.