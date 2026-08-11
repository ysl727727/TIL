# Model Evaluation and Threshold Selection

회귀와 분류 문제에서 높은 점수 하나만 보는 대신, baseline과 여러 평가 지표를 함께 사용하고
validation에서 선택한 정책을 test에 그대로 적용하는 과정을 실습했습니다.

## Questions

1. 회귀 모델은 train 평균을 예측하는 baseline보다 실제로 나은가?
2. 악성 종양을 놓치는 비용이 클 때 Accuracy 외에 어떤 지표를 봐야 하는가?
3. Recall 정책을 만족하는 임계값은 어느 데이터에서 결정해야 하는가?

## Datasets

| Task | Dataset | Split | Positive class |
| --- | --- | --- | --- |
| Regression | scikit-learn Diabetes | 265 / 88 / 89 | - |
| Classification | Wisconsin Breast Cancer | 341 / 114 / 114 | Malignant = 1 |

- train / validation / test = 60% / 20% / 20%
- `random_state=42`
- 분류 데이터는 `stratify` 적용
- 원본 인덱스 교집합 검사를 통해 분할 중복 확인

## Experiment 1: Regression Baseline

`StandardScaler → LinearRegression` pipeline을 train에서 학습하고,
train target 평균을 반복 예측하는 baseline과 동일한 validation set에서 비교했습니다.

| Candidate | MAE | RMSE | R² |
| --- | ---: | ---: | ---: |
| Linear Regression | 38.22 | 49.15 | 0.5810 |
| Train-mean baseline | 67.52 | 76.16 | -0.0062 |

Linear Regression의 RMSE는 baseline보다 약 27.01 낮았습니다. R²는 약 0.581로,
validation target 변동의 약 58.1%를 설명했습니다.

## Experiment 2: Classification Metrics

`StandardScaler → LogisticRegression` pipeline의 validation 결과입니다.

| Accuracy | Precision | Recall | F1 | ROC-AUC | AP |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.9737 | 1.0000 | 0.9302 | 0.9639 | 1.0000 | 1.0000 |

Accuracy가 높더라도 일부 악성 사례를 놓칠 수 있으므로 Recall을 함께 확인했습니다.
ROC-AUC와 AP에는 이진 예측값이 아니라 연속 확률을 사용해 순위 능력을 평가했습니다.

## Experiment 3: Recall Policy

validation Recall이 0.90 이상인 후보 중 F1이 가장 높은 임계값을 선택했습니다.
동률일 때는 Precision과 임계값 순으로 결정했습니다.

선택한 임계값과 fitted model을 함께 고정한 뒤 test set을 한 번만 평가했습니다.

| Test AP | Test Precision | Test Recall | Test F1 |
| ---: | ---: | ---: | ---: |
| 0.9920 | 0.9756 | 0.9524 | 0.9639 |

test 결과를 보고 모델이나 임계값을 다시 고르면 test가 선택 과정에 포함되어 최종 평가의
독립성이 깨집니다. 따라서 test 결과는 최종 성능 보고에만 사용했습니다.

## Key Takeaways

- 모델 성능은 반드시 의미 있는 baseline과 비교한다.
- 지표는 문제의 비용과 positive class 정의에 맞춰 선택한다.
- 전처리는 train에서만 학습하고 validation과 test에는 변환만 적용한다.
- 모델과 임계값 선택은 validation에서 끝낸다.
- test는 모든 선택을 고정한 뒤 마지막에 한 번만 확인한다.

## Files

```text
01-model-evaluation/
├── README.md
├── model-evaluation-and-thresholding.ipynb
└── requirements.txt
```

## Run

```bash
python -m pip install -r requirements.txt
jupyter notebook model-evaluation-and-thresholding.ipynb
```

> 이 실습은 scikit-learn 예제 데이터를 사용한 학습 목적의 실험이며 실제 의료 판단에 사용할 수 없습니다.
