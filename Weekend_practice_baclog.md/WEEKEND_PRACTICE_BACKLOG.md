# Weekend Practice Backlog

> Updated on 2026-08-19 after Deep Learning lessons 1-2~2-2.

2026-08-22~23 주말에는 현재 딥러닝 진도를 따라가기 위한 실습을 먼저 처리하고,
이전에 남은 기초수학과 머신러닝 실습은 우선순위에 따라 이어서 진행합니다.

체크박스는 강의를 들었거나 정답 코드를 읽었다는 뜻이 아니라,
**직접 작성하고 실행 결과를 설명할 수 있는지**를 기준으로 갱신합니다.

## 1. Today: Deep Learning Progress

### Completed

- [x] 1-2 기본: 규칙 기반·머신러닝·딥러닝 적용 방식 비교
- [x] 1-2 심화: 데이터와 운영 조건에 따른 적용 판단
- [x] 1-3 기본: DataLoader→forward→loss→backward→step 흐름
- [x] 1-4 기본: 회귀·이진 분류·다중 분류의 출력과 loss 연결
- [x] 1-5 기본: PyTorch 코드를 import·data·model·loss·optimizer·loop로 구분
- [x] 2-1 기본: Tensor의 shape·dtype·ndim 확인과 dtype 변환
- [x] 2-2 기본: batch dimension과 broadcasting

### Newly Learned Syntax

- [x] `tensor.long()`은 Tensor를 `torch.int64`로 변환
- [x] `torch.int64`와 `torch.long`은 같은 64-bit 정수 dtype
- [x] `tensor.to(torch.int64)`로 목표 dtype을 지정해 변환
- [x] `tensor.dtype`으로 현재 dtype 확인
- [x] `zip(a, b)`로 같은 위치의 값을 짝지어 반복
- [x] 함수 호출의 `func(*case)`에서 `*`는 tuple을 여러 위치 인자로 풀어 전달

`func(*case)`의 `case`는 현재 반복에서 꺼낸 tuple 변수입니다.
함수 정의의 `def func(*args)`처럼 여러 인자를 tuple로 모으는 문법과 방향이 반대입니다.

## 2. Highest Priority: Remaining Deep Learning Practice

- [ ] 1-3 심화 실습
- [ ] 1-4 심화 실습
- [ ] 1-5 심화 실습
- [ ] 2-1 심화 실습
- [ ] 2-2 심화 실습

### Short Rewriting Drills

- [ ] `.long()`과 `.to(torch.int64)`를 각각 사용해 같은 dtype 결과 확인
- [ ] 회귀 target과 다중 분류 target의 dtype을 직접 만들고 비교
- [ ] `zip()`으로 코드 블록과 단계 이름을 짝지어 출력
- [ ] tuple 하나를 `func(*case)`로 풀어서 함수에 전달
- [ ] `[4, 3] + [3]`의 결과 shape을 실행 전에 먼저 적기
- [ ] `[4, 1]` prediction과 `[4]` target의 위험한 broadcasting 수정

완료 기준:

```text
입력 shape / dtype:
필요한 변환:
예상 출력 shape / dtype:
실행 결과:
```

위 네 항목을 코드 위에 먼저 작성하고 실제 결과와 비교합니다.

## 3. Previous Unfinished Practice

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

## 4. Weekend Order

### Saturday, 2026-08-22

1. 기초수학 손계산 1문제와 NumPy 검산
2. 딥러닝 1-3·1-4 심화 실습
3. 딥러닝 1-5 심화 실습
4. `.long()`·`dtype`·`zip()`·`func(*case)` 재작성 문제
5. 시간이 남으면 Tree Ensemble의 OOB와 중요도 실습

### Sunday, 2026-08-23

1. 기초수학 미완료 문제 1개 재도전
2. 딥러닝 2-1·2-2 심화 실습
3. broadcasting shape 예측과 dtype 오류 디버깅 복습
4. learning curve·validation curve 또는 규제 CV 중 하나 완료
5. 시간이 남으면 불균형 처리와 누수 방지 Pipeline 실습

주말에 모든 과거 실습을 억지로 끝내는 것보다 다음 주 진도에 직접 연결되는
딥러닝 심화와 dtype·shape를 먼저 완료합니다. 남은 머신러닝 실습은 체크박스를 유지해
다음 복습일에 이어서 진행합니다.

## 5. Working Rule

각 문제는 정답을 보기 전에 다음 네 줄을 먼저 작성합니다.

```text
입력:
출력:
작업 순서:
첫 번째로 작성할 코드:
```

막히면 전체 정답 대신 첫 단계 힌트만 확인합니다. 완료한 문제는 다음 날 코드 없이
함수 또는 학습 흐름의 뼈대를 다시 작성해 실제로 기억에 남았는지 점검합니다.
