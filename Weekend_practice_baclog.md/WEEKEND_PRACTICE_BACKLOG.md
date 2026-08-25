# Weekend Practice Backlog

> Updated on 2026-08-25 after Deep Learning lessons 6-1~7-2.

다음 주말인 2026-08-29~30에는 오늘 미실행으로 확인된 6-1·6-4 심화와
이전 5-2 심화를 먼저 마칩니다. 체크박스는 코드를 작성했다는 뜻이 아니라
**직접 실행하고 결과를 설명할 수 있는지**를 기준으로 갱신합니다.

## 1. Latest Deep Learning Progress

### Completed on 2026-08-25

- [x] 6-1 기본: 계산 그래프와 Chain Rule을 수식·Autograd로 비교
- [x] 6-2 기본·심화: `requires_grad`, `detach()`, layer freeze와 gradient 연결 진단
- [x] 6-3 기본·심화: scalar Loss, `.grad` shape·finite·norm 감사
- [x] 6-4 기본: gradient 누적과 표준 mini-batch step 확인
- [x] 6-5 기본·심화: 안전한 validation, metric 분리와 Autograd 디버깅
- [x] 7-1·7-2 이론 및 코드 흐름 확인: `Dataset`, `DataLoader`, `TensorDataset`, Custom Dataset

### Partially Completed

- [ ] 6-1 심화 2번 셀 재실행: 현재 문법 오류 수정 후 실행 확인 필요
- [ ] 6-4 심화 2·3번: parameter update 검증과 잘못된 누적 흐름 비교
- [ ] 5-2 심화 `compute_loss` 셀: 회귀·이진·다중 분류 입력으로 최종 실행

7-1·7-2는 이론과 실습 코드를 눈으로 진행했으므로 미완료 주말 과제로 추가하지 않습니다.

## 2. Questions and Newly Learned Points

- [x] `nn.Linear(2, 1)`의 weight는 scalar가 아니라 `[1, 2]`이며 두 feature에 각각 곱해짐
- [x] `.reshape(-1, 1)`로 `[N]`을 `[N, 1]`로 바꿔 Linear·Loss의 2차원 계약을 맞춤
- [x] `torch.zeros_like(x)`는 `x`와 shape·dtype이 같고 값만 0인 Tensor를 생성
- [x] `param.grad is None`은 그래프 단절 가능성, `grad.norm()==0`은 계산된 gradient가 0인 상태
- [x] MSE에서 입력 scale 증가가 gradient를 크게 키울 수 있어 clipping 전에 전처리를 점검
- [x] `.backward()`가 gradient를 누적하므로 각 일반 mini-batch 전에 `zero_grad()` 필요
- [x] `model.eval()`은 layer 모드, `torch.no_grad()`는 graph 기록을 제어하며 평가에는 둘 다 필요
- [x] 학습 Loss 이전의 `.detach()`는 역전파를 끊으므로 metric·로그 경로에만 사용
- [x] `argmax(dim=1)`은 batch 각 행에서 가장 큰 class index를 반환
- [x] `loss.item()`은 graph가 없는 기록용 Python 숫자를 반환

## 3. Highest Priority: Autograd Reinforcement

### Graph and Gradient State

- [ ] 6-1 심화 미실행 셀을 실행하고 수기 gradient와 Autograd 결과 비교
- [ ] 같은 parameter가 두 경로에 쓰일 때 gradient 기여를 경로별로 설명
- [ ] `grad is None` 사례와 값이 0인 gradient 사례를 각각 재현
- [ ] leaf와 non-leaf Tensor의 `.grad` 저장 차이를 `retain_grad()` 전후로 확인
- [ ] 같은 graph에 backward를 두 번 호출한 오류와 재-forward 해결 비교

### Scale, Accumulation, and Step

- [ ] 입력 scale 1배·10배에서 MSE gradient norm 비교
- [ ] `zero_grad()`를 생략한 두 번째 batch의 누적 gradient 확인
- [ ] 6-4 심화 2번: update 전·예상·실제 weight 비교
- [ ] 6-4 심화 3번: 올바른 후보와 누적 오류 후보를 같은 초기값에서 비교
- [ ] `zero_grad(set_to_none=True)`와 `False`의 `.grad` 상태 비교

### Safe Evaluation

- [ ] `eval()`만 사용한 출력과 `eval()+no_grad()` 출력의 `grad_fn` 비교
- [ ] 학습 prediction을 Loss 전에 detach해 오류를 재현하고 수정
- [ ] metric용 `logits.detach().argmax(dim=1)`을 다시 작성
- [ ] validation 후 `model.train()` 복귀 여부를 확인하는 작은 검사 추가
- [ ] Loss·gradient에 `torch.isfinite()` 검사 추가

완료 기록 형식:

```text
graph 연결:
grad 상태(None / zero / non-zero):
입력 scale:
parameter update 전·후:
train/eval mode:
검증 결과:
```

## 4. Carry-over Practice

### Chapter 5 Contract

- [ ] `compute_loss(task, output, target)` 셀 실행
- [ ] 회귀 `[B,1]` float + `MSELoss` 검증
- [ ] 이진 `[B,1]` logits·float target + `BCEWithLogitsLoss` 검증
- [ ] 다중 `[B,C]` logits·`[B]` long target + `CrossEntropyLoss` 검증
- [ ] shape·dtype 오류를 하나씩 넣고 assertion 실패 확인

### Earlier Deep Learning

- [ ] `TinyMLP`의 `__init__`과 `forward`를 보지 않고 작성
- [ ] 이미지 flatten과 CNN의 공간 정보 처리 차이 설명
- [ ] ReLU·LeakyReLU·Tanh·GELU 출력과 gradient 비교
- [ ] 이진·다중 분류의 Sigmoid·Softmax 중복 적용 오류 수정
- [ ] shape·dtype·device 오류를 각각 하나씩 만들고 수정
- [ ] 1-3·1-4·1-5·2-1·2-2 별도 심화 실습

### Math and Machine Learning

- [ ] 기초수학 미완료 문제를 수식·shape·문법·문제 분해 기준으로 재시도
- [ ] Tree ensemble 비교, OOB·validation, permutation importance 복습
- [ ] learning·validation curve와 Ridge·Lasso·ElasticNet 비교
- [ ] class weight·sampling·SMOTE를 같은 CV와 Pipeline 안에서 비교
- [ ] end-to-end schema guard의 열·dtype·null·finite 검사 재작성

## 5. Next Weekend Order

### Saturday, 2026-08-29

1. 6-1 심화 미실행 셀 재실행과 Chain Rule 손계산
2. `grad is None`과 0 gradient 재현
3. 입력 scale별 gradient norm 비교
4. 6-4 심화 2·3번 실행과 weight update 검증
5. `zero_grad(set_to_none=True/False)` 비교
6. 시간이 남으면 5-2 `compute_loss` 실행

### Sunday, 2026-08-30

1. 5-2 문제 유형별 output·target·dtype·Loss 계약 완료
2. `eval()`과 `no_grad()` 역할을 분리한 validation 함수 작성
3. 잘못된 `.detach()` 위치를 찾아 수정
4. `isfinite`, gradient norm, mode 복귀 검사를 train/valid 함수에 추가
5. 이전 딥러닝 별도 심화 중 가능한 만큼 진행
6. 시간이 남으면 기초수학 또는 머신러닝 미완료 실습 1개

## 6. Working Rule

각 문제는 정답을 보기 전에 다음 네 줄을 먼저 작성합니다.

```text
입력:
출력:
작업 순서:
첫 번째로 작성할 코드:
```

막히면 전체 정답 대신 첫 단계 힌트만 확인합니다. 완료한 문제는 다음 날 코드 없이
핵심 함수나 학습 흐름을 다시 작성해 실제로 기억에 남았는지 점검합니다.
