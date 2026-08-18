# Class Imbalance, Cross-Validation, and Leakage Prevention

불균형 분류에서 Accuracy 하나만으로 모델을 판단할 때 생기는 문제와,
데이터의 독립 단위와 시간 구조에 맞게 교차검증을 선택하고 누수를 막는 원칙을 학습했습니다.

> 진행 상태: 개념 학습 완료. 4-1과 4-2 실습은 아직 진행하지 못했습니다.

## What I Learned

### Metrics for Imbalanced Classification

- 양성이 드물면 모든 행을 음성으로 예측해도 Accuracy가 높을 수 있습니다.
- Precision은 양성 예측의 신뢰도, Recall은 실제 양성을 놓치지 않는 정도를 봅니다.
- F1은 Precision과 Recall의 조화평균이지만 업무 비용을 자동으로 정해 주지는 않습니다.
- 희소 양성 문제에서는 ROC-AUC뿐 아니라 AP, PR 곡선, FP와 FN의 실제 개수를 함께 확인합니다.
- Threshold는 모델의 순위 능력을 바꾸는 학습 파라미터가 아니라 점수를 운영 행동으로 바꾸는 정책입니다.

### Imbalance Handling

| Method | Main idea | Main caution |
| --- | --- | --- |
| Class weight | 소수 클래스 오류에 더 큰 가중치 부여 | 모든 모델에서 같은 효과를 보장하지 않음 |
| Undersampling | 다수 클래스 행 일부 제거 | 유용한 정보가 사라질 수 있음 |
| SMOTE | 소수 클래스 이웃 사이에 합성 표본 생성 | 분할 전에 적용하면 validation 누수 발생 |

리샘플링은 개발 데이터 전체가 아니라 각 CV의 train fold 안에서만 수행해야 합니다.

### Choosing a CV Splitter

| Data structure | Splitter candidate | What it protects |
| --- | --- | --- |
| 독립적인 일반 행 | `KFold` | 반복 분할을 통한 평균과 변동 확인 |
| 불균형 분류 | `StratifiedKFold` | fold별 클래스 비율의 큰 흔들림 완화 |
| 사용자·문서·대화가 반복됨 | `GroupKFold` | 같은 group이 train과 validation에 겹치는 문제 방지 |
| 시간 순서가 중요함 | `TimeSeriesSplit` | 미래로 학습해 과거를 평가하는 오류 방지 |

`StratifiedKFold`는 클래스 비율 문제를 줄일 뿐, 같은 원문의 chunk나 같은 사용자가
양쪽에 들어가는 group 누수까지 막지는 못합니다.

### Leakage Prevention

이번 강의에서 구분한 주요 누수는 다음과 같습니다.

- 분할 누수: 같은 독립 단위의 복제·반복 기록이 train과 validation에 함께 들어감
- 전처리 누수: 전체 데이터로 imputer, scaler, encoder를 먼저 학습함
- target 누수: 예측 시점에 알 수 없는 정답 관련 정보를 특성으로 사용함
- 미래 누수: 과거 예측에 미래 정보를 사용함
- 리샘플링 누수: 분할 전에 oversampling 또는 SMOTE를 적용함
- 선택 누수: test 결과를 보고 모델이나 threshold를 다시 바꿈

Pipeline은 전처리와 리샘플링의 `fit` 경계를 CV train fold 안으로 넣는 데 도움을 줍니다.
하지만 잘못된 group이나 시간 분할, target 특성 설계까지 자동으로 해결하지는 않습니다.

## Learning Reflection

강의에서 지표·분할·누수의 판단 원칙은 학습했지만, 직접 코드를 작성하고 결과를 해석하는
실습은 하지 못했습니다. 따라서 이 기록은 개념을 정리한 상태이며, 구현 능력을 검증한 완료 기록은 아닙니다.

## Next Steps

- [ ] 불균형 데이터에서 Accuracy와 AP 기준선 비교
- [ ] 같은 validation에서 class weight, undersampling, SMOTE 비교
- [ ] 리샘플링을 CV train fold 안에 두는 `imblearn` Pipeline 구성
- [ ] `KFold`, `StratifiedKFold`, `GroupKFold` 결과 비교
- [ ] 전체 데이터 전처리와 Pipeline 전처리의 누수 차이 확인
- [ ] 후보 선택을 Dev에서 끝내고 sealed Test를 한 번만 평가

## Files

```text
04-class-imbalance-cv-leakage/
└── README.md
```

실습을 진행하지 않았으므로 강의 원본, 노트북과 `requirements.txt`는 추가하지 않았습니다.
