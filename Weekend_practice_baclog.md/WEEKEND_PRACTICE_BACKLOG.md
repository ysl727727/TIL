# Weekend Practice Backlog

> Updated on 2026-08-20 after Deep Learning lessons 2-3~3-5.

2026-08-22~23 주말에는 이번 주 딥러닝 진도를 다시 구현하는 연습을 먼저 처리하고,
이전에 남은 기초수학과 머신러닝 실습은 우선순위에 따라 이어서 진행합니다.

체크박스는 강의를 들었거나 정답 코드를 읽었다는 뜻이 아니라,
**직접 작성하고 실행 결과를 설명할 수 있는지**를 기준으로 갱신합니다.

## 1. Today: Deep Learning Progress

### Completed

- [x] 2-3 기본: CPU/GPU device 선택과 Tensor·모델 이동
- [x] 2-3 별도 심화: device 불일치 진단과 batch 이동 helper
- [x] 2-4 기본: Linear 입력·batch·dtype·device 오류 디버깅
- [x] 3-1 기본: 퍼셉트론 가중합과 선형 결정 경계
- [x] 3-2 기본: MLP 입력층·은닉층·출력층과 parameter 수
- [x] 3-3 기본: `nn.Linear`의 weight·bias shape와 직접 계산
- [x] 3-4 기본: 이미지 batch flatten과 입력 차원 계산
- [x] 3-5 기본: `nn.Module` 클래스와 MLP `forward` 구현
- [x] 오늘 기본 노트북에 포함된 심화 항목 작성 및 실행

### Newly Learned

- [x] 모델과 입력·target을 같은 device로 이동해야 함
- [x] 오류를 shape·dtype·device로 먼저 분류하는 디버깅 순서
- [x] `set()`으로 중복 제거
- [x] `zip()`으로 같은 위치의 항목을 1:1로 묶기
- [x] `next(generator, default)`로 조건에 맞는 첫 항목 찾기
- [x] `p.numel()`로 parameter Tensor의 원소 수 계산
- [x] 이미지 MLP의 flatten에서 CNN의 공간 정보 처리 필요성 연결
- [x] `self`는 입력이 아니라 모델 객체 자신이며, `forward`의 `x`가 입력임

## 2. Highest Priority: Deep Learning Reinforcement

### Python Class and MLP

- [ ] `TinyMLP`의 `__init__`과 `forward`를 보지 않고 다시 작성
- [ ] `self.fc1`, `x`, `model(x)`가 각각 무엇을 가리키는지 한 줄씩 설명
- [ ] `nn.Linear(5, 10)`의 weight·bias shape와 parameter 수 손계산
- [ ] hidden size를 바꾼 뒤 parameter 수 변화를 손계산하고 `p.numel()`로 검산
- [ ] 이미지 `[12, 3, 32, 32]`를 flatten해 logits `[12, 10]`을 만드는 MLP 재작성
- [ ] MLP가 flatten으로 잃는 공간 정보와 CNN이 유지하는 정보를 3문장으로 비교

### Device and Debugging

- [ ] 모델만 device로 옮긴 오류를 직접 만들고 입력 이동으로 수정
- [ ] `CrossEntropyLoss` target dtype 오류를 `.long()`으로 수정
- [ ] `nn.Linear`의 `in_features` 오류를 `x.shape[-1]` 확인 후 수정
- [ ] `[B, 1]` prediction과 `[B]` target의 broadcasting 오류 수정
- [ ] `(x, y)` batch 이동 helper를 참고 없이 작성

### Short Syntax Drills

- [ ] `set()`으로 중복 device 이름 제거
- [ ] `zip()`으로 layer 이름과 output shape 묶어 출력
- [ ] `next(..., None)`으로 CUDA 실행 후보 중 첫 항목 찾기
- [ ] `sum(p.numel() for p in model.parameters())` 다시 작성

완료 기준:

```text
입력 shape / dtype / device:
모델 또는 연산이 기대하는 조건:
필요한 변환:
예상 출력 shape / dtype / device:
실행 결과:
```

## 3. Earlier Deep Learning Practice Still Pending

- [ ] 1-3 별도 심화 실습
- [ ] 1-4 별도 심화 실습
- [ ] 1-5 별도 심화 실습
- [ ] 2-1 별도 심화 실습
- [ ] 2-2 별도 심화 실습

이번에 완료한 2-3 별도 심화는 다시 할 목록에서 제거했습니다.

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
- [ ] Random Forest 설정별 CV 평균과 fold 변동 비교
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
- [ ] `StratifiedKFold`와 `GroupKFold`의 역할 비교
- [ ] 전체 전처리와 Pipeline 전처리의 누수 차이 확인

### End-to-End Pipeline Reinforcement

- [ ] 5-2 artifact dictionary의 필수 key를 참고 없이 작성
- [ ] 열·dtype·null·finite·domain 검사를 작은 함수로 구현
- [ ] 정상 입력과 실패 입력으로 schema guard 검사

## 5. Weekend Order

### Saturday, 2026-08-22

1. 기초수학 손계산 1문제와 NumPy 검산
2. `TinyMLP`를 보지 않고 다시 작성
3. `self`·`__init__`·`forward`·`model(x)` 역할 설명
4. Linear parameter 수 손계산과 `p.numel()` 검산
5. device·dtype·shape 오류를 하나씩 만들고 수정
6. 시간이 남으면 1-3·1-4 별도 심화 실습

### Sunday, 2026-08-23

1. 이미지 MLP 입력·출력 shape 문제 재작성
2. MLP flatten과 CNN의 차이 정리
3. `set()`·`zip()`·`next()` 짧은 재작성 문제
4. 1-5·2-1·2-2 별도 심화 중 가능한 만큼 진행
5. learning curve·validation curve 또는 규제 CV 중 하나 완료
6. 시간이 남으면 불균형 처리와 누수 방지 Pipeline 실습

주말에는 과거 실습을 모두 끝내려 하기보다 다음 CNN 진도와 직접 연결되는
Python 클래스·MLP·shape·device 복습을 먼저 완료합니다. 남은 머신러닝 실습은
체크박스를 유지해 다음 복습일에 이어서 진행합니다.

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
