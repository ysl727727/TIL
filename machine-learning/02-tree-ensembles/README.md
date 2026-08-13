# Tree Ensembles: Bagging, Boosting, and Model Interpretation

배깅·랜덤포레스트·부스팅의 학습 구조와 모델 비교 원칙을 학습하고,
현재는 첫 실습인 Dummy·Decision Tree·Random Forest 비교까지 구현했습니다.

> 진행 상태: 2-1 실습의 문제 1-1 완료. 나머지 실습은 아직 진행하지 않았습니다.

## What I Learned

### Bagging and Random Forest

- 배깅은 서로 다른 bootstrap 표본으로 여러 모델을 독립적으로 학습하고 예측을 결합합니다.
- 랜덤포레스트는 행 표본과 분할 후보 특성에 무작위성을 추가해 나무 사이의 상관을 낮춥니다.
- OOB 평가는 빠른 내부 점검에 유용하지만 별도의 validation을 대신하지 않습니다.

### Boosting

- 부스팅은 현재 앙상블이 부족한 부분을 다음 약한 모델이 순차적으로 보완합니다.
- Gradient Boosting은 일반적으로 선택한 손실 함수의 negative gradient를 학습합니다.
- `learning_rate`와 반복 수는 함께 조정해야 합니다.
- best iteration과 early stopping으로 실제 계산을 멈춘 iteration은 다를 수 있습니다.

### Model Selection and Interpretation

- 후보는 같은 fold, 전처리 경계, 평가 지표와 계산 조건에서 비교해야 합니다.
- 평균 점수뿐 아니라 fold별 차이, 변동, 학습 시간과 운영 비용도 함께 확인합니다.
- MDI, permutation importance, SHAP은 서로 다른 질문에 답합니다.

| Method | Question |
| --- | --- |
| MDI | 트리 분할에서 불순도를 얼마나 줄였는가? |
| Permutation importance | validation 피처를 섞었을 때 성능이 얼마나 떨어지는가? |
| SHAP | 기준값에서 모델 출력까지 피처별 기여를 어떻게 나눌 수 있는가? |

SHAP bar는 전역 기여 크기, beeswarm은 전역 기여 방향과 분포,
waterfall은 한 행의 지역 설명을 보여 줍니다. SHAP은 모델 출력을 설명할 뿐 인과관계를 증명하지 않습니다.

## Completed Experiment: Candidate Comparison

Wisconsin Breast Cancer 데이터를 사용하고 악성 종양을 양성 클래스 `1`로 변환했습니다.
동일한 train과 validation에서 세 후보를 AP, F1, Recall로 비교했습니다.

| Item | Setting |
| --- | --- |
| Data | `sklearn.datasets.load_breast_cancer` |
| Split | train 341 / validation 114 / test 114 |
| Positive class | malignant = 1 |
| Primary metric | validation Average Precision |
| Random seed | 42 |
| Random Forest | 300 trees, balanced class weight, `max_features="sqrt"` |

### Result

| Model | AP | F1 | Recall |
| --- | ---: | ---: | ---: |
| Random Forest | 0.9968 | 0.9524 | 0.9302 |
| Decision Tree | 0.8834 | 0.9157 | 0.8837 |
| Dummy | 0.3772 | 0.0000 | 0.0000 |

이 분할에서는 Random Forest의 validation AP가 가장 높았습니다.
여러 나무의 확률을 평균한 Random Forest가 단일 Decision Tree보다 높은 AP를 기록했습니다.
Dummy를 함께 비교해 복잡한 후보가 단순 기준선보다 실제로 나은지도 확인했습니다.

이 결과는 하나의 고정된 분할에서 얻었으므로 Random Forest가 모든 데이터에서 항상 우수하다는 뜻은 아닙니다.
남은 실습에서 OOB, 특성 중요도, cross-validation 안정성을 추가로 확인할 예정입니다.

## Learning Process and Current Difficulty

앙상블의 개념은 설명을 따라가며 이해했지만, 문제만 보고 코드를 처음부터 설계할 때는
무엇을 먼저 작성해야 하는지 막혔습니다. 현재 문제 1-1 코드를 보지 않고 다시 작성할 수 있는 정도는
약 10%정도입니다.

AI가 만든 코드를 그대로 제출하지 않고, 질문과 답변을 통해 각 줄의 역할을 확인한 뒤
이해할 수 있는 범위까지 직접 작성하고 실행했습니다. 이 과정에서 단순 문법 부족만이 아니라
`문제 분석 → 작업 순서 결정 → 필요한 함수 선택 → 코드 작성`의 연결 훈련이 부족하다는 점을 확인했습니다.

## Improvement Plan

앞으로 실습 문제를 다음 순서로 진행합니다.

1. 정답 코드를 보기 전에 입력과 출력을 적습니다.
2. 필요한 중간 작업을 한국어 순서로 나눕니다.
3. 각 단계에 필요한 Python·NumPy·scikit-learn 함수를 연결합니다.
4. 전체 정답 대신 첫 단계 힌트부터 받아 직접 작성합니다.
5. shape와 중간 출력을 확인하며 오류 위치를 좁힙니다.
6. 다음 날 코드를 보지 않고 함수의 뼈대를 다시 작성합니다.

Python·NumPy 기초 문제와 머신러닝 실습을 병행하되, 문법만 따로 외우지 않고
현재 실습에서 필요한 반복문, 딕셔너리, 함수 반환, 배열 shape를 연결해서 복습합니다.

## Next Steps

- [x] Dummy, Decision Tree, Random Forest를 같은 validation에서 비교
- [ ] 문제 1-1을 보지 않고 다시 작성
- [ ] OOB와 validation 결과의 역할 비교
- [ ] MDI와 permutation importance 계산 및 해석
- [ ] Random Forest 설정별 cross-validation 안정성 비교
- [ ] 배깅과 부스팅을 동일 fold에서 비교
- [ ] SHAP bar, beeswarm, waterfall 해석 실습

## Files

```text
02-tree-ensembles/
├── README.md
├── ensemble-candidate-comparison.ipynb
└── requirements.txt
```

## Run

```bash
python -m pip install -r requirements.txt
jupyter notebook ensemble-candidate-comparison.ipynb
```

> 이 실습은 scikit-learn 예제 데이터를 사용한 학습 목적의 실험이며 실제 의료 판단에 사용할 수 없습니다.
