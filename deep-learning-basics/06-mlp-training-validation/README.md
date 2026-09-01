# End-to-End MLP Training and Validation

`nn.Module` 모델 정의부터 Loss·optimizer 연결, train/validation loop, metric 누적,
epoch 기록과 validation 기반 best model 선택까지 하나의 MLP 파이프라인으로 연결했습니다.

> 진행 상태: 시간상 8-1~8-7 개별 실습 대신 그 내용을 한 번에 모은 8-8 종합 심화 실습을 완료했습니다.
> 8-1~8-7 개별 실습은 미완료이며, 주말에 각 흐름을 눈으로 다시 살펴볼 예정입니다.

## Practice Status

| Lesson | Topic | Status |
| --- | --- | --- |
| 8-1 | `nn.Module` 구조와 `forward` 설계 | Not completed individually |
| 8-2 | MLP 모델 클래스 완성 | Not completed individually |
| 8-3 | Loss와 optimizer 연결 | Not completed individually |
| 8-4 | Train loop 작성 | Not completed individually |
| 8-5 | Validation loop 작성 | Not completed individually |
| 8-6 | Accuracy와 metric 누적 | Not completed individually |
| 8-7 | Epoch 로그와 시각화 | Not completed individually |
| 8-8 | 8-1~8-7을 연결한 MLP 종합 실습 | Completed |

8-8이 앞의 내용을 합친 종합 실습이어서 제한된 시간에는 전체 연결을 우선 확인했습니다.
다만 종합 코드를 실행한 것과 각 단계를 독립적으로 설명할 수 있는 것은 다르므로,
8-1~8-7은 완료로 표시하지 않았습니다.

## End-to-End Flow

```text
Dataset과 split
→ DataLoader
→ nn.Module MLP
→ Loss와 optimizer
→ train loop
→ validation loop
→ sample 수 기준 Loss·accuracy 누적
→ epoch history와 best validation epoch
→ best state 복원
→ test 한 번 평가
```

`nn.Module`에서는 layer를 `__init__()`에 등록하고 계산 순서를 `forward()`에 작성합니다.
`model(x)`를 호출하면 PyTorch가 내부적으로 `forward(x)`를 실행합니다.

## Train and Validation Contract

학습과 검증은 비슷한 반복 구조를 갖지만 parameter 업데이트 여부가 다릅니다.

```python
def run_epoch(training, loader):
    model.train(training)
    total_loss = seen = 0
    context = torch.enable_grad() if training else torch.no_grad()

    with context:
        for x, y in loader:
            if training:
                optimizer.zero_grad()

            loss = criterion(model(x), y)

            if training:
                loss.backward()
                optimizer.step()

            total_loss += loss.item() * y.shape[0]
            seen += y.shape[0]

    return total_loss / seen
```

실습 결과 3 epoch 동안 train loss가 감소했고, 모든 validation 전후에 model parameter가 변하지 않았습니다.

## Questions I Asked and What I Learned

### 1. `total_loss = seen = 0`

파이썬의 다중 할당입니다. `total_loss`와 `seen`을 모두 `0`으로 초기화합니다.
하나는 Loss 합계, 다른 하나는 실제 처리한 sample 수를 누적합니다.

### 2. `torch.enable_grad() if training else torch.no_grad()`

학습 모드에서는 gradient 계산을 켜고 검증 모드에서는 끄는 가변 context입니다.
이를 사용하면 공통 `run_epoch()` 안에서도 train과 validation의 역할을 분리할 수 있습니다.

### 3. `valid_unchanged &= condition`

```python
valid_unchanged = valid_unchanged and condition
```

의 축약형입니다. validation 중 parameter가 한 번이라도 바뀌면 `False`가 되고,
이후 epoch에서도 계속 `False`를 유지하므로 전체 검증 과정의 불변성을 감사할 수 있습니다.

### 4. `min(range(len(valid_loss)), key=valid_loss.__getitem__)`

validation loss의 값이 아니라 최솟값이 있는 **index**를 찾습니다.

```python
best_index = min(range(len(valid_loss)), key=lambda i: valid_loss[i])
```

와 같은 의미입니다. 실습 report에서는 validation loss `[0.80, 0.62, 0.67]` 중
두 번째 epoch를 best epoch로 선택하고 test는 그 뒤 한 번만 확인했습니다.

### 5. 왜 `y.shape[0]`을 사용하는가?

`y.shape[0]`은 현재 batch의 sample 수입니다. `CrossEntropyLoss`의 기본 결과는 batch 평균이므로,
`loss.item() * y.shape[0]`으로 batch Loss 합계를 복원한 뒤 전체 sample 수로 나눕니다.
마지막 batch가 더 작을 수 있어 batch 평균들을 동일한 비중으로 다시 평균 내면 안 됩니다.

`x.shape`은 `torch.Size([4, 6])` 같은 전체 shape tuple이어서 곱셈에 쓸 수 없고,
현재 batch 수가 필요할 때는 `x.shape[0]` 또는 `y.shape[0]`을 사용합니다.

## Metric and Model Selection

```text
epoch_loss = total_loss / total_samples
epoch_accuracy = total_correct / total_samples
```

accuracy도 batch별 accuracy의 단순 평균 대신 전체 정답 수를 전체 sample 수로 나눕니다.
불균형 분류에서는 accuracy만으로 충분하지 않을 수 있으므로 precision·recall·F1 등도 함께 봐야 합니다.

모델과 hyperparameter는 validation으로 선택하고 test는 선택을 마친 뒤 한 번만 평가합니다.
test 결과를 보고 다시 설정을 바꾸면 test가 사실상 validation 역할을 하게 되어 leakage가 발생합니다.

## Weekend Review

- [ ] 8-1~8-7 개별 실습을 순서대로 눈으로 살펴보기
- [ ] 각 실습이 8-8 종합 코드의 어느 부분에 해당하는지 표시하기
- [ ] `nn.Module → loss/optimizer → train → validation → metric → history`를 말로 설명하기
- [ ] 시간이 되면 공통 `run_epoch()`의 뼈대를 보지 않고 다시 작성하기

## Files

- `01-mlp-end-to-end-advanced.ipynb`: 파이프라인 오류 진단, 3 epoch MLP baseline, validation 기반 report
- `requirements.txt`: 최소 실행 환경

