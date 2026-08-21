# Weekend Practice Backlog

> Updated on 2026-08-21 after Deep Learning lessons 4-1~4-4.

2026-08-22~23 주말에는 이번 주 딥러닝 진도 중 MLP 클래스와 분류 출력층 계약을 먼저 복습하고,
이전에 남은 기초수학·머신러닝 실습은 우선순위에 따라 이어서 진행합니다.

체크박스는 강의를 들었거나 정답 코드를 읽었다는 뜻이 아니라,
**직접 작성하고 실행 결과를 설명할 수 있는지**를 기준으로 갱신합니다.

## 1. Today: Deep Learning Progress

### Completed

- [x] 4-1 기본·별도 심화: 선형층 중첩의 한계와 XOR 비선형성
- [x] 4-2 기본·별도 심화: ReLU 적용 위치, 활성 비율과 Dead ReLU
- [x] 4-3 기본·별도 심화: Sigmoid, 이진 출력 계약과 threshold 비용 비교
- [x] 4-4 기본·별도 심화: Softmax 축, 다중 분류 계약과 후보 검증

### Newly Learned

- [x] 활성화 함수가 없으면 여러 `Linear` 층도 하나의 아핀 변환으로 축약됨
- [x] ReLU는 shape을 유지하면서 음수를 0으로 만들고 비선형성을 추가함
- [x] `BCEWithLogitsLoss`에는 Sigmoid 전 raw logits를 전달함
- [x] `CrossEntropyLoss`에는 Softmax 전 raw logits와 `[B]` long target을 전달함
- [x] `[B, C]`에서 `dim=1`과 `dim=-1`은 class 축을 의미함
- [x] class index만 필요하면 Softmax 없이 logits에 바로 `argmax` 가능
- [x] `criterion`은 Loss 객체에 흔히 사용하는 변수 이름임
- [x] `torch.linspace()`로 일정 간격 Tensor 생성
- [x] `torch.cat()`으로 Tensor를 지정 축에 연결
- [x] Tensor 원소별 조건은 `and`가 아니라 괄호를 포함한 `&` 사용
- [x] ReLU·LeakyReLU·Tanh·GELU의 특징 비교

## 2. Highest Priority: Activation and Output Contracts

### Binary Classification

- [ ] `[B, 1]` logits와 `[B, 1]` float target을 직접 생성
- [ ] 모델 마지막 Sigmoid를 제거하고 `BCEWithLogitsLoss` 적용
- [ ] `sigmoid → threshold → long label` 추론 함수 재작성
- [ ] 확률 threshold `0.5`와 logit threshold `0.0`이 같은 이유 설명
- [ ] threshold `0.5`와 `0.7`의 FP·FN 비용 비교

### Multiclass Classification

- [ ] `[B, C]` logits와 `[B]` long target을 직접 생성
- [ ] 모델 마지막 Softmax를 제거하고 `CrossEntropyLoss` 적용
- [ ] target 범위 `0 <= target < C` assertion 작성
- [ ] `dim=0`과 `dim=-1` Softmax를 비교하고 각 행의 합 확인
- [ ] Softmax 전후 `argmax` 결과가 같은지 검증

### Activation Functions

- [ ] `Linear → Linear`과 `Linear → ReLU → Linear` 출력 곡선 비교
- [ ] ReLU 전후 min·max와 shape 기록
- [ ] 음수 입력에서 ReLU gradient가 0이 되는 예제 확인
- [ ] ReLU·LeakyReLU·Tanh·GELU 출력 그래프 비교

### Short Syntax Drills

- [ ] `torch.linspace(-3, 3, steps=7)`을 다시 작성하고 간격 설명
- [ ] `torch.cat()`으로 XOR에 `x1*x2` feature 추가
- [ ] `(target >= 0) & (target < C)` mask 작성
- [ ] `criterion = ...`과 `loss = criterion(...)` 두 줄의 역할 구분

완료 기준:

```text
문제 유형:
logits shape:
target shape / dtype / range:
Loss 입력:
추론 변환:
실행 결과:
```

## 3. Earlier Deep Learning Practice Still Pending

### Python Class and MLP

- [ ] `TinyMLP`의 `__init__`과 `forward`를 보지 않고 다시 작성
- [ ] `self.fc1`, 입력 `x`, `model(x)`의 역할을 한 줄씩 설명
- [ ] `nn.Linear(5, 10)`의 weight·bias shape와 parameter 수 손계산
- [ ] 이미지 `[12, 3, 32, 32]`를 flatten해 logits `[12, 10]` 생성
- [ ] MLP flatten과 CNN의 공간 정보 처리 차이를 3문장으로 비교

### Device and Debugging

- [ ] 모델·입력·target을 같은 device로 옮기는 helper 재작성
- [ ] shape·dtype·device 오류를 각각 하나씩 만들고 수정
- [ ] `[B, 1]` prediction과 `[B]` target의 broadcasting 오류 수정

### Separate Advanced Notebooks

- [ ] 1-3 별도 심화 실습
- [ ] 1-4 별도 심화 실습
- [ ] 1-5 별도 심화 실습
- [ ] 2-1 별도 심화 실습
- [ ] 2-2 별도 심화 실습

2-3과 4-1~4-4 별도 심화 실습은 완료했으므로 다시 할 목록에서 제외했습니다.

## 4. Previous Unfinished Practice

### Math Foundations

- [ ] 벡터·행렬과 shape 핵심 개념을 말로 설명
- [ ] 손계산 예제를 NumPy 결과로 검산
- [ ] 미완료 기초수학 실습을 한 문제씩 작은 단계로 분해
- [ ] 막힌 원인을 수식·shape·Python 문법·문제 분해 중 하나로 표시

### Tree Ensembles

- [ ] Dummy·Tree·Random Forest 비교 함수를 보지 않고 다시 작성
- [ ] OOB와 validation 점수의 역할 비교
- [ ] MDI와 validation permutation importance 계산 및 해석
- [ ] 배깅과 부스팅을 같은 fold에서 비교
- [ ] SHAP bar·beeswarm·waterfall 해석 실습

### Bias-Variance and Regularization

- [ ] learning curve 작성 및 train-validation gap 해석
- [ ] validation curve 작성 및 one-SE 후보 선택
- [ ] Ridge·Lasso·ElasticNet을 같은 Dev CV에서 비교
- [ ] alpha 선택 후 한 후보만 sealed Test에서 평가

### Class Imbalance, CV, and Leakage

- [ ] Accuracy와 AP 기준선 비교
- [ ] class weight·undersampling·SMOTE를 같은 CV에서 비교
- [ ] sampler를 CV train fold 안에 두는 Pipeline 구성
- [ ] `StratifiedKFold`와 `GroupKFold` 역할 비교
- [ ] 전체 전처리와 Pipeline 전처리의 누수 차이 확인

### End-to-End Pipeline Reinforcement

- [ ] 5-2 artifact dictionary의 필수 key를 참고 없이 작성
- [ ] 열·dtype·null·finite·domain 검사를 작은 함수로 구현
- [ ] 정상 입력과 실패 입력으로 schema guard 검사

## 5. Weekend Order

### Saturday, 2026-08-22

1. 기초수학 손계산 1문제와 NumPy 검산
2. `TinyMLP`를 보지 않고 다시 작성
3. 이진 분류 모델·target·Loss·추론 전체 계약 재작성
4. 다중 분류 모델·target·Loss·추론 전체 계약 재작성
5. `dim=0`·`dim=-1` Softmax 오류 비교
6. `linspace`·`cat`·Tensor `&` 짧은 문제

### Sunday, 2026-08-23

1. ReLU·LeakyReLU·Tanh·GELU 출력 비교
2. Dead ReLU와 gradient 확인
3. MLP flatten과 CNN 연결 정리
4. 1-3~2-2 별도 심화 중 가능한 만큼 진행
5. learning curve·validation curve 또는 규제 CV 중 하나 완료
6. 시간이 남으면 불균형 처리와 누수 방지 Pipeline 실습

주말에는 과거 실습을 모두 끝내려 하기보다 다음 진도에 직접 연결되는
Python 클래스·MLP·활성화 함수·분류 출력 계약을 먼저 완료합니다.

## 6. Working Rule

각 문제는 정답을 보기 전에 다음 네 줄을 먼저 작성합니다.

```text
입력:
출력:
작업 순서:
첫 번째로 작성할 코드:
```

막히면 전체 정답 대신 첫 단계 힌트만 확인합니다. 완료한 문제는 다음 날 코드 없이
함수 또는 학습 흐름의 뼈대를 다시 작성해 실제로 기억에 남았는지 점검합니다.
