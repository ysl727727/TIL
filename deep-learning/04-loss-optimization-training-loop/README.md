# Loss, Optimizer, and Parameter Update Flow

손실 함수가 예측 오차를 scalar로 만드는 과정부터 문제별 Loss 선택,
SGD·Adam과 learning rate, `backward()`와 `optimizer.step()`의 역할까지 실습했습니다.

> 진행 상태: 5-1·5-3·5-4 기본·별도 심화 완료. 5-2 기본 완료, 별도 심화는 3문제 중 2문제 실행 완료이며 `compute_loss` 재실행이 남았습니다.

## Practice Status

| Lesson | Topic | Basic | Separate advanced |
| --- | --- | --- | --- |
| 5-1 | 손실 함수의 역할과 목표 함수 | Completed | Completed |
| 5-2 | 문제 유형별 손실 함수 선택 | Completed | In progress: 2/3 executed |
| 5-3 | SGD·Adam과 learning rate | Completed | Completed |
| 5-4 | 파라미터 업데이트 코드 흐름 | Completed | Completed |

강의 원문과 제공된 해설 대신 직접 작성한 코드와 실행 결과를 공개 노트북에 남겼습니다.

## Chapter Map

```text
입력
→ model(inputs)로 예측
→ criterion(outputs, targets)로 scalar loss 계산
→ loss.backward()로 parameter별 gradient 계산
→ optimizer.step()으로 weight와 bias 변경
```

가장 중요한 기준 흐름은 다음 다섯 줄입니다.

```python
optimizer.zero_grad()
outputs = model(inputs)
loss = criterion(outputs, targets)
loss.backward()
optimizer.step()
```

말로 바꾸면 `이전 gradient 제거 → 예측 → 채점 → 수정 방향 계산 → 실제 수정`입니다.

## 5-1. Loss Function

손실 함수는 단순히 정답·오답을 나누는 것이 아니라 예측이 정답에서 얼마나 벗어났는지를
미분 가능한 숫자로 표현합니다.

### MSE by hand

```python
error = pred - target
squared_error = error ** 2
manual_mse = squared_error.mean()
torch_mse = nn.MSELoss()(pred, target)

assert torch.allclose(manual_mse, torch_mse)
```

MSE가 오차를 제곱하는 이유는 양수·음수 오차의 상쇄를 막고 큰 오차에 더 큰 벌점을 주기 위해서입니다.

### Reduction

| Option | Result | Use |
| --- | --- | --- |
| `none` | 원소별 Loss 유지 | 샘플별 오류 분석·가중치 적용 |
| `sum` | Loss 합계 | 합 자체가 필요한 경우 |
| `mean` | Loss 평균 | 일반적인 batch 학습 기본값 |

일반적인 `backward()`에서는 `mean`이나 `sum`으로 scalar Loss를 만듭니다.
Loss 숫자는 같은 문제·데이터·함수·reduction 조건 안에서 비교해야 하며,
MSE와 Cross Entropy의 절대값을 서로 직접 비교하면 안 됩니다.

## 5-2. Match the Task Contract

Loss 이름만 외우지 않고 다음을 한 세트로 확인합니다.

```text
문제 유형 → 출력 shape → target shape → target dtype → Loss
```

| Task | Model output | Target | Target dtype | Loss |
| --- | --- | --- | --- | --- |
| 회귀 | `[B, 1]` 실수 | `[B, 1]` 실수 | float | `MSELoss` |
| 이진 분류 | `[B, 1]` logit | `[B, 1]` 0/1 | float | `BCEWithLogitsLoss` |
| 다중 분류 | `[B, C]` logits | `[B]` class index | long | `CrossEntropyLoss` |
| 다중 레이블 | `[B, L]` logits | `[B, L]` multi-hot | float | `BCEWithLogitsLoss` |

`view_as(logits)`는 회귀·이진 분류 target을 모델 출력과 같은 shape로 맞출 때 사용할 수 있습니다.
다중 분류 target은 `[B]`의 class index여야 하므로 같은 방식으로 `[B, C]`에 맞추면 안 됩니다.

```python
def compute_loss(task, output, target):
    if task == "regression":
        target = target.float().view_as(output)
        return nn.MSELoss()(output, target)
    if task == "binary":
        target = target.float().view_as(output)
        return nn.BCEWithLogitsLoss()(output, target)
    if task == "multiclass":
        target = target.long().view(-1)
        return nn.CrossEntropyLoss()(output, target)
    raise ValueError(f"unknown task: {task}")
```

## 5-3. Optimizer and Learning Rate

`backward()`는 gradient를 계산해 `.grad`에 저장하고, optimizer는 그 gradient를 사용해 parameter를 바꿉니다.

단순 SGD의 기본 형태는 다음과 같습니다.

```text
new_parameter = old_parameter - learning_rate × gradient
```

- learning rate가 너무 작으면 Loss가 매우 천천히 줄어듭니다.
- 적절하면 비교적 빠르고 안정적으로 감소합니다.
- 너무 크면 최소점을 지나쳐 진동·발산하거나 `inf`·`nan`이 될 수 있습니다.

같은 learning rate에서도 gradient 크기에 따라 실제 이동량은 다릅니다.
학습률 실험은 데이터·초기 parameter·optimizer·step 수를 고정하고 learning rate만 바꿔야 공정합니다.

### SGD and Adam

- SGD는 gradient 크기에 learning rate를 곱해 직접 이동합니다.
- Momentum SGD는 이전 이동 방향을 누적해 진동을 완화합니다.
- Adam은 gradient의 1차 모멘트와 제곱값의 2차 모멘트를 사용해 parameter별 이동 크기를 보정합니다.
- Adam도 전역 learning rate를 사용하며 learning rate가 없어지는 것은 아닙니다.

가상 Loss `(w - 2)²`, `w=0`, `lr=0.1`의 첫 step에서 SGD는 gradient `-4`에 비례해
`w=0.4`로 이동하고, Adam은 초기 보정 결과 약 `w=0.1`로 이동하는 차이를 확인했습니다.

## 5-4. Parameter Update and Verification

각 단계의 역할은 명확히 다릅니다.

| Code | Role | Changes parameter? |
| --- | --- | --- |
| `criterion(outputs, targets)` | 오차 계산 | No |
| `loss.backward()` | gradient 계산 | No |
| `optimizer.step()` | weight·bias 업데이트 | Yes |
| `optimizer.zero_grad()` | 이전 gradient 제거 | No |

`step()`은 parameter를 변경하지만 `.grad`를 자동으로 비우지 않습니다. 다음 step의
`backward()` 전에 `zero_grad()`가 실행되어야 의도하지 않은 gradient 누적을 막을 수 있습니다.

업데이트 전 값을 안전하게 저장할 때는 다음 패턴을 사용합니다.

```python
weight_before = model.weight.detach().clone()
loss.backward()
weight_grad = model.weight.grad.detach().clone()

expected = weight_before - lr * weight_grad
optimizer.step()
weight_after = model.weight.detach().clone()

assert torch.allclose(weight_after, expected)
```

`detach()`는 계산 그래프에서 분리하고, `clone()`은 값이 독립된 새 Tensor를 만듭니다.

## Questions I Asked and What I Learned

### 1. `if not all(math.isfinite(value) for value in values)`는 어떻게 동작하는가?

`math.isfinite(value)`는 각 값이 `nan`이나 `inf`가 아닌 정상 유한수인지 검사합니다.
`all(...)`은 모든 값이 정상일 때만 `True`이고, 앞의 `not`이 결과를 뒤집습니다.
따라서 값 하나라도 `nan`·`inf`이면 조건문 내부가 실행됩니다.

```python
if not all(math.isfinite(value) for value in values):
    status = "non_finite"
```

Loss curve가 그래프로 그려졌다는 사실만으로 정상 실험이라고 판단하지 않고,
후보 선택 전에 non-finite 값을 먼저 제외하는 검증에 사용할 수 있습니다.

### 2. `all(b > a for a, b in zip(values, values[1:]))`는 무엇을 검사하는가?

`values`와 한 칸 이동한 `values[1:]`를 `zip()`으로 묶으면
`(이전 값, 다음 값)` 쌍이 만들어집니다. 모든 쌍에서 `b > a`인지 검사하므로
전체 리스트가 한 번도 멈추거나 감소하지 않고 엄격하게 증가하는지 확인합니다.

```text
values = [4, 9, 40, 250]
pairs  = (4,9), (9,40), (40,250)
result = True
```

Learning rate가 너무 커 Loss가 계속 증가하는 발산 패턴을 분류할 때 사용했습니다.

### 3. 호출 순서 딕셔너리 `pos`는 왜 만드는가?

```python
pos = {call: run["calls"].index(call) for call in run["calls"]}
```

함수 이름을 key, 호출 위치를 value로 바꿉니다. 그러면 문자열 목록을 계속 탐색하지 않고
`pos["loss"] < pos["backward"] < pos["step"]`처럼 숫자 비교로 선후 관계를 감사할 수 있습니다.
같은 호출이 중복되지 않는다는 계약 아래에서 사용하는 방식입니다.

### 4. `next()`는 승인 검사에서 무엇을 반환하는가?

```python
first_failure = next(
    (key for key, passed in audit.items() if not passed),
    None,
)
```

검증 결과 중 `False`인 첫 실패 원인 하나를 찾는 즉시 반환합니다.
두 번째 인자 `None`을 두면 실패 항목이 없을 때 `StopIteration` 대신 `None`을 반환합니다.

### 5. 왜 `len(approved) == 1`일 때만 자동 선택하는가?

- 승인 후보가 0개면 선택할 모델이 없습니다.
- 1개면 유일한 승인 후보이므로 선택할 수 있습니다.
- 2개 이상이면 둘 다 통과했더라도 추가 기준 없이 임의 선택하면 안 되므로 보류합니다.

```python
selected = approved[0] if len(approved) == 1 else "보류"
```

성능 숫자 하나만 보고 고르는 대신 검증 계약을 통과한 후보의 수까지 운영 정책에 포함한 것입니다.

### 6. SGD와 Adam은 왜 첫 step부터 다르게 움직이는가?

SGD는 현재 gradient 크기에 직접 비례해 이동합니다. Adam은 gradient의 이동 평균과
제곱 이동 평균을 사용해 크기를 정규화하므로 같은 초기값·gradient·learning rate에서도
첫 이동량이 달라집니다. 두 optimizer의 이름만 바꾸는 비교가 아니라 초기 parameter를
동일하게 복사하고 각각 독립된 optimizer state를 사용해야 합니다.

### 7. 왜 `total_loss += loss`가 메모리 누수를 만들 수 있는가?

`loss`는 숫자만 가진 것이 아니라 역전파에 필요한 계산 그래프와 연결된 Tensor입니다.
이를 반복해서 누적하면 이전 batch의 그래프까지 참조가 남아 메모리가 계속 증가할 수 있습니다.

```python
# 기록용 권장 패턴
total_loss += loss.item()
```

`loss.item()`은 계산 그래프와 분리된 Python 숫자를 반환합니다. 따라서 기록에는 `.item()`을 쓰고,
역전파는 Tensor인 `loss.backward()`로 실행합니다. `.item()` 결과에는 `backward()`를 호출할 수 없습니다.

## Learning Reflection

이번 장에서 Loss 계산, gradient 계산, parameter 수정이 서로 다른 단계라는 점을 코드 흐름으로 연결했습니다.
특히 학습이 실행됐다는 사실만 확인하지 않고 non-finite Loss, 호출 순서, 유일한 승인 후보,
예상 SGD update와 실제 weight를 감사하는 방식으로 학습 파이프라인을 검증했습니다.

또한 짧은 Python 표현도 의미를 한 단계씩 분해했습니다. `all()`은 전체 조건 검사,
`zip(values, values[1:])`은 연속 쌍 생성, `next()`는 첫 실패 원인 검색,
`loss.item()`은 기록용 숫자 추출이라는 역할로 구분했습니다.

## Next Steps

- [x] 5-1·5-3·5-4 기본·별도 심화 실습
- [x] 5-2 기본 실습
- [ ] 5-2 별도 심화 `compute_loss` 셀 실행 및 출력 검증
- [ ] 문제 유형별 output·target·dtype·Loss 계약을 보지 않고 재작성
- [ ] SGD update 예상값과 실제 값을 직접 비교
- [ ] `loss.item()` 사용 전후 누적 변수의 type과 graph 연결 비교
- [ ] 호출 순서 audit 함수를 작은 문제로 다시 작성

## Files

```text
04-loss-optimization-training-loop/
├── README.md
├── 01-loss-function-basic.ipynb
├── 02-loss-function-advanced.ipynb
├── 03-task-loss-selection-basic.ipynb
├── 04-task-loss-selection-advanced.ipynb
├── 05-optimizer-learning-rate-basic.ipynb
├── 06-optimizer-learning-rate-advanced.ipynb
├── 07-parameter-update-flow-basic.ipynb
├── 08-parameter-update-flow-advanced.ipynb
└── requirements.txt
```
