# 기초 수학 종합 과제 — Private LLM 사내 문서 검색·압축·Attention 진단

> 제출용 채점 과제입니다. 정규 강의 실습(`deep-learning-basics`, `deep-learning-advanced`)과는 별개로, 지난주에 부여되어 마감 기한에 맞춰 제출한 산출물입니다.

## 과제 구성

| 문제 | 주제 | 배점 |
| --- | --- | --- |
| 1 | 사내 문서 임베딩과 Cosine Vector Search | 공식 구현 성취도 5점 |
| 2 | 고유값 분해 기반 PCA | 공식 구현 성취도 5점 |
| 3 | SVD 저랭크 압축 | 공식 구현 성취도 5점 |
| 4 | Causal Attention과 출력 Projection 학습 (Attention Forward → Vocabulary Softmax/Loss → Autograd+SGD 1 step) | 추가 종합 평가 5점 |

각 문제는 필수 구현 + 진단/의사결정 메모(서술형) 세트로 구성되어 있고, 문제별로 공식 점수에 영향 없는 선택 심화(M1~M4)가 붙어 있습니다. 마지막에 문서 검색·PCA·SVD·Attention/다음 토큰 예측·학습 업데이트를 종합한 최종 엔지니어링 요약 보고서와 최종 제출 체크리스트로 마무리됩니다.

## 큰 흐름

1. **문제 1~3 (선형대수 기반)**: 문서를 벡터로 표현하고(임베딩), 유사도 검색(Cosine), 차원 축소(PCA/고유값 분해), 압축(SVD/저랭크 근사)까지 "문서 검색 시스템"을 선형대수 도구로 단계별로 구현
2. **문제 4 (Attention + 학습)**: Causal Attention을 직접 forward pass로 구현하고, vocabulary logits에 softmax+cross entropy를 적용해 loss를 계산한 뒤, PyTorch autograd로 실제 SGD 한 스텝까지 수행 — 3장(Attention)에서 배운 개념을 학습 파이프라인과 연결
3. 각 문제 끝에 결과를 숫자로만 남기지 않고 의사결정 메모(왜 이 방법을 선택했는지, 트레이드오프는 무엇인지)로 정리
4. 노트북 마지막에 AI(Claude 등)를 활용한 부분을 개념/함수·문법/그래프 구현으로 구분해 별도 기록

## Files

| File | 설명 |
| --- | --- |
| `basic_math_assignment_이용석.ipynb` | 문제 1~4 필수 구현 및 심화, 최종 요약 보고서 포함 |

## Environment

```bash
pip install numpy torch matplotlib
```
