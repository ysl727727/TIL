# Weekend Practice Backlog

> Updated on 2026-08-24 after Deep Learning lessons 5-1~5-4.

다음 주말인 2026-08-29~30에는 5장의 Loss·Optimizer·학습 루프를 먼저 재작성하고,
이전에 남은 딥러닝·기초수학·머신러닝 실습은 우선순위에 따라 이어서 진행합니다.

체크박스는 강의를 들었거나 코드를 작성했다는 뜻이 아니라,
**직접 실행하고 결과를 설명할 수 있는지**를 기준으로 갱신합니다.

## 1. Latest Deep Learning Progress

### Completed on 2026-08-24

- [x] 5-1 기본·별도 심화: MSE 직접 계산, reduction과 후보 비교
- [x] 5-2 기본: 문제 유형별 Loss와 target shape·dtype 수정
- [x] 5-2 별도 심화 1·3번: 계약 오류 진단과 다중 레이블 문제 정의
- [x] 5-3 기본·별도 심화: SGD·Adam, learning rate curve와 후보 승인
- [x] 5-4 기본·별도 심화: 표준 train step, 호출 순서와 업데이트 계약 감사

### Written but Execution Still Pending

- [ ] 5-2 별도 심화 2번 `compute_loss` 셀 실행
- [ ] 회귀·이진·다중 분류 입력 각각으로 출력값 검증

### Questions and Newly Learned Points

- [x] `not all(math.isfinite(...))`로 `nan`·`inf`가 하나라도 있는지 검사
- [x] `zip(values, values[1:])`으로 연속된 이전·다음 값을 묶음
- [x] `all(b > a ...)`로 Loss가 계속 증가하는지 검사
- [x] 호출 이름별 index 딕셔너리 `pos`로 선후 관계 비교
- [x] `next()`로 첫 실패 원인 하나를 찾고 검색 종료
- [x] 승인 후보가 정확히 1개일 때만 자동 선택하는 운영 규칙
- [x] 같은 조건에서도 SGD와 Adam의 첫 update가 다른 이유
- [x] `loss` Tensor 누적과 `loss.item()` 숫자 누적의 메모리 차이
- [x] `backward()`는 gradient 계산, `step()`은 실제 parameter 변경

## 2. Highest Priority: Chapter 5 Reinforcement

### First: Finish the Partial Practice

- [ ] 5-2 심화 `compute_loss(task, output, target)` 셀 실행
- [ ] 회귀: `[B,1]` float output·target과 `MSELoss` 확인
- [ ] 이진: `[B,1]` logits·float target과 `BCEWithLogitsLoss` 확인
- [ ] 다중: `[B,C]` logits·`[B]` long target과 `CrossEntropyLoss` 확인
- [ ] 잘못된 shape·dtype 입력 하나씩 넣어 assertion 실패 확인

### Loss and Reduction

- [ ] MSE를 `오차 → 제곱 → 평균` 순서로 손계산
- [ ] `reduction='none'`, `'sum'`, `'mean'` 결과 비교
- [ ] `[B,1] - [B]` broadcasting이 만든 잘못된 diff shape 확인
- [ ] 서로 다른 Loss 절대값을 직접 비교하면 안 되는 이유 설명

### Optimizer and Learning Rate

- [ ] `new = old - lr * grad`로 SGD 한 step 손계산
- [ ] 같은 초기 parameter로 SGD·Adam 첫 step 비교
- [ ] 작은·적절한·큰 learning rate curve를 직접 분류
- [ ] 모든 Loss 값이 finite인지 먼저 검사한 뒤 후보 선택
- [ ] 후보 0개·1개·2개일 때 선택 결과가 다른 승인 규칙 재작성

### Training Loop and Audit

- [ ] 표준 5단계 학습 루프를 보지 않고 작성
- [ ] `zero_grad`, `forward`, `loss`, `backward`, `step` 역할 설명
- [ ] 호출 순서 목록을 `pos` 딕셔너리로 바꾸고 의존 관계 검사
- [ ] 첫 실패 원인을 `next(..., None)`으로 반환
- [ ] update 전 weight·gradient·예상 weight·실제 weight 비교
- [ ] `total_loss += loss`와 `total_loss += loss.item()` 차이 확인

완료 기준:

```text
입력 / target 계약:
Loss와 reduction:
호출 순서:
gradient 상태:
parameter update 전·후:
검증 결과:
```

## 3. Earlier Deep Learning Practice Still Pending

### Python Class and MLP

- [ ] `TinyMLP`의 `__init__`과 `forward`를 보지 않고 다시 작성
- [ ] `self.fc1`, 입력 `x`, `model(x)`의 역할 설명
- [ ] `nn.Linear(5, 10)`의 weight·bias shape와 parameter 수 손계산
- [ ] 이미지 `[12, 3, 32, 32]`를 flatten해 `[12, 10]` logits 생성
- [ ] MLP flatten과 CNN의 공간 정보 처리 차이 설명

### Activation and Output Contracts

- [ ] ReLU·LeakyReLU·Tanh·GELU 출력과 gradient 비교
- [ ] 이진 분류에서 Sigmoid 중복 적용 오류 수정
- [ ] 다중 분류에서 Softmax 중복 적용과 `dim=0` 오류 수정
- [ ] Softmax 전후 `argmax` 결과가 같은지 검증

### Device and Debugging

- [ ] 모델·입력·target을 같은 device로 옮기는 helper 재작성
- [ ] shape·dtype·device 오류를 각각 하나씩 만들고 수정
- [ ] `[B,1]` prediction과 `[B]` target의 broadcasting 오류 수정

### Separate Advanced Notebooks

- [ ] 1-3 별도 심화 실습
- [ ] 1-4 별도 심화 실습
- [ ] 1-5 별도 심화 실습
- [ ] 2-1 별도 심화 실습
- [ ] 2-2 별도 심화 실습

## 4. Previous Unfinished Practice

### Math Foundations

- [ ] 벡터·행렬과 shape 핵심 개념을 말로 설명
- [ ] 손계산 예제를 NumPy 결과로 검산
- [ ] 미완료 기초수학 실습을 한 문제씩 작은 단계로 분해
- [ ] 막힌 원인을 수식·shape·Python 문법·문제 분해 중 하나로 표시

### Tree Ensembles

- [ ] Dummy·Tree·Random Forest 비교 함수를 보지 않고 다시 작성
- [ ] OOB와 validation 점수 역할 비교
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

## 5. Next Weekend Order

### Saturday, 2026-08-29

1. 5-2 별도 심화 `compute_loss` 실행 완료
2. 문제 유형별 output·target·dtype·Loss 계약 재작성
3. MSE와 reduction 손계산 및 PyTorch 검산
4. SGD 한 step 예상값과 실제 update 비교
5. `isfinite`·연속 증가·유일 승인 후보 검사 재작성
6. 시간이 남으면 Python class와 `TinyMLP` 복습

### Sunday, 2026-08-30

1. 표준 train step을 보지 않고 작성
2. 잘못된 호출 순서를 `pos`와 의존 관계로 진단
3. `next()`로 첫 실패 원인 반환
4. `loss.item()`을 이용한 안전한 epoch Loss 기록
5. 1-3~2-2 별도 심화 중 가능한 만큼 진행
6. 시간이 남으면 기초수학 또는 머신러닝 미완료 실습 1개

다음 주말에는 5장의 미실행 셀을 먼저 끝낸 뒤, Loss 계산에서 실제 parameter 변경까지
한 흐름으로 다시 작성하는 것을 최우선으로 합니다.

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
