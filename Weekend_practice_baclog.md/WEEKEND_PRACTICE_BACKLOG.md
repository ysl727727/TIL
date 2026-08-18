# Weekend Practice Backlog

2026-08-22~23 주말에 진행할 미완료 실습과 독립 재작성 과제를 한곳에 모았습니다.
체크박스는 강의 수강 여부가 아니라 **직접 구현하거나 다시 풀었는지**를 기준으로 갱신합니다.

## Status Summary

| Area | Current state | Weekend goal |
| --- | --- | --- |
| Math foundations | 개념 복습 중, 실습 미완료 | 손계산과 NumPy 결과 연결 |
| Model evaluation | 실습 완료 | 필요할 때만 복습 |
| Tree ensembles | 첫 후보 비교만 완료 | OOB·중요도·CV 실습 |
| Bias-variance / regularization | 개념 완료, 실습 미완료 | 곡선과 규제 CV 구현 |
| Imbalance / CV / leakage | 개념 완료, 실습 미완료 | Pipeline 안에서 비교 |
| CV tuning / end-to-end pipeline | 전체 실습 완료 | 5-2 심화 독립 재작성 |

## 1. Must Do

### Math Foundations

- [ ] 벡터·행렬과 shape 핵심 개념을 말로 설명
- [ ] 손계산 예제 뒤 NumPy 결과로 검산
- [ ] 아직 해결하지 못한 기초수학 실습을 작은 단계로 나눠 다시 시도
- [ ] 막힌 원인을 수식, shape, Python 문법, 문제 분해 중 하나로 표시

완료 기준: 정답을 보는 것이 아니라 최소 한 문제를 `입력 → 계산 순서 → 결과`로 직접 설명합니다.

### Tree Ensembles

- [ ] Dummy·Tree·Random Forest 비교 함수의 뼈대를 보지 않고 다시 작성
- [ ] OOB 점수와 validation 점수의 역할 비교
- [ ] MDI와 validation permutation importance 계산 및 해석
- [ ] Random Forest 설정별 CV 평균과 fold 변동 비교

완료 기준: 지표표와 중요도표를 만들고, 두 중요도가 다른 질문에 답한다는 해석을 작성합니다.

## 2. Next Priority

### Bias-Variance and Regularization

- [ ] 학습 데이터 크기에 따른 learning curve 작성
- [ ] 모델 복잡도에 따른 validation curve 작성
- [ ] Ridge·Lasso·ElasticNet을 같은 Dev CV에서 비교
- [ ] alpha 선택을 Dev에서 끝내고 한 후보만 sealed Test에서 평가

완료 기준: `train 점수 → validation 점수 → gap → 다음 실험` 순서로 진단 문장을 작성합니다.

### Class Imbalance, CV, and Leakage

- [ ] 불균형 데이터에서 Accuracy와 AP 기준선 비교
- [ ] class weight, undersampling, SMOTE를 같은 CV에서 비교
- [ ] sampler가 CV train fold 안에서만 실행되도록 Pipeline 구성
- [ ] `StratifiedKFold`와 `GroupKFold`가 해결하는 문제 비교
- [ ] 잘못된 전체 전처리와 올바른 Pipeline 전처리 결과 비교

완료 기준: 어떤 누수를 막기 위해 어떤 분할과 Pipeline을 사용했는지 코드 아래에 한 문장으로 기록합니다.

## 3. Reinforcement

### 5-2 Advanced: Artifact and Schema Guard

- [ ] 정답을 닫고 artifact dictionary의 필수 key를 먼저 작성
- [ ] DataFrame 여부와 열 누락·추가 검사 구현
- [ ] 열 순서, dtype, null, finite, domain 검사 구현
- [ ] 범주와 source mode, online 행 수 검사 구현
- [ ] 정상 입력 1개와 실패 입력 3개부터 테스트
- [ ] 이후 실패 입력을 10종으로 확장

완료 기준: 전체 코드를 외워 쓰는 것이 아니라, 각 검사가 필요한 운영 사고를 설명하고 작은 guard부터 통과시킵니다.

## Suggested Weekend Order

### Saturday, 2026-08-22

1. 기초수학 손계산과 NumPy 검산
2. 앙상블 후보 비교 함수 재작성
3. OOB·MDI·permutation importance 실습

### Sunday, 2026-08-23

1. 학습곡선·검증곡선과 규제 CV 실습
2. 불균형 처리와 누수 방지 Pipeline 실습
3. 시간이 남으면 5-2 schema guard를 작은 단계부터 재작성

## Working Rule

각 문제는 정답을 보기 전에 다음 네 줄을 먼저 작성합니다.

```text
입력:
출력:
작업 순서:
첫 번째로 작성할 코드:
```

전체 정답이 필요해질 때도 먼저 첫 단계 힌트만 사용하고, 완료한 문제는 다음 날 코드 없이
함수 뼈대를 다시 작성해 실제로 기억에 남았는지 확인합니다.
