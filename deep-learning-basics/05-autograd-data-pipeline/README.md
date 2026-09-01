# Autograd and Data Pipeline Foundations

계산 그래프와 Chain Rule에서 시작해 `requires_grad`, `backward()`, gradient 누적,
안전한 평가 코드까지 연결했습니다. 이어서 `Dataset`과 `DataLoader`의 역할,
`TensorDataset`과 Custom Dataset의 차이를 눈으로 따라가며 데이터 입력 흐름을 확인했습니다.

> 진행 상태: 6-1~6-5 기본 완료. 6-2·6-3·6-5 심화 완료. 6-1 심화는 2/3,
> 6-4 심화는 1/3 실행 확인. 7-1·7-2는 이론·코드 흐름 확인,
> 7-3·7-4·7-5는 심화 실습을 모두 실행했습니다.

## Practice Status

| Lesson | Topic | Basic | Advanced |
| --- | --- | --- | --- |
| 6-1 | 계산 그래프와 Chain Rule | Completed | In progress: 2/3 |
| 6-2 | `requires_grad`와 Tensor gradient | Completed | Completed |
| 6-3 | `loss.backward()`와 `.grad` | Completed | Completed |
| 6-4 | `zero_grad → backward → step` | Completed | In progress: 1/3 |
| 6-5 | Autograd 디버깅과 안전한 평가 | Completed | Completed |
| 7-1 | `Dataset`과 `DataLoader` | Visual walkthrough | 별도 실습 없음 |
| 7-2 | `TensorDataset`과 Custom Dataset | Visual walkthrough | 별도 실습 없음 |
| 7-3 | Transform과 전처리 흐름 | 이론 확인 | Completed |
| 7-4 | Batch, shuffle, train/valid/test split | 이론 확인 | Completed |
| 7-5 | 데이터 파이프라인 디버깅 | 이론 확인 | Completed |

7-1·7-2는 코드를 눈으로 따라가며 sample과 batch의 shape·dtype 흐름을 확인했습니다.
따라서 미완료 과제로 분류하지 않았습니다.

7-3~7-5 심화는 각 노트북의 코드 셀 3개를 모두 실행해 transform 격리,
재현 가능한 split과 첫 batch 계약 검사를 확인했습니다.

## 6-1. Computation Graph and Chain Rule

forward는 입력에서 Loss 방향으로 값을 계산하고, backward는 Loss에서 parameter 방향으로
local gradient를 곱해 갑니다.

```text
x, w, b → z = xw + b → loss = z²
```

예를 들어 `x=2`, `w=3`, `b=1`이면 `z=7`이고 다음과 같이 계산됩니다.

```text
d(loss)/dw = d(loss)/dz × dz/dw
            = 2z × x
            = 14 × 2
            = 28
```

`backward()`를 바로 호출하려면 일반적으로 최종 Loss가 scalar여야 합니다.

## 6-2. `requires_grad`, Leaf Tensor, and Graph Separation

- `requires_grad=True`인 Tensor에서 시작한 연산은 계산 그래프에 기록됩니다.
- 모델의 weight와 bias 같은 leaf parameter는 `backward()` 후 `.grad`를 저장합니다.
- 중간 결과인 non-leaf Tensor는 기본적으로 `.grad`를 보관하지 않습니다.
  필요한 경우에만 `retain_grad()`를 사용합니다.
- `torch.no_grad()`는 블록 전체의 그래프 기록을 끄고, `.detach()`는 특정 Tensor를
  현재 그래프에서 분리합니다.

## 6-3. `backward()` and Gradient Inspection

`backward()`는 parameter를 바꾸지 않고 gradient만 계산합니다. parameter shape와
`.grad` shape는 같으며 실제 값 변경은 `optimizer.step()`에서 일어납니다.

```python
loss.backward()

for name, param in model.named_parameters():
    if param.grad is None:
        print(name, "graph disconnected")
    else:
        print(name, param.grad.shape, param.grad.norm().item())
```

같은 계산 그래프에 두 번 `backward()`하는 대신 일반적인 학습에서는 다시 forward하여
새 그래프를 만드는 것이 기본입니다.

## 6-4. Gradient Accumulation and Step Order

`.backward()`는 기존 `.grad`에 값을 더합니다. mini-batch마다 독립적인 gradient를
사용하려면 다음 순서를 지킵니다.

```python
optimizer.zero_grad(set_to_none=True)
pred = model(x)
loss = loss_fn(pred, y)
loss.backward()
optimizer.step()
```

`set_to_none=True`를 사용하면 gradient가 0 Tensor가 아니라 `None`으로 초기화됩니다.
두 방식 모두 다음 backward 전에 이전 batch의 gradient를 제거하려는 목적은 같습니다.

## 6-5. Safe Evaluation and Autograd Debugging

`model.eval()`과 `torch.no_grad()`는 서로 대체할 수 없습니다.

| Code | Role |
| --- | --- |
| `model.eval()` | Dropout·BatchNorm 등 layer 동작을 평가 모드로 전환 |
| `torch.no_grad()` | gradient graph 기록을 중지하고 메모리 사용을 줄임 |

```python
model.eval()
with torch.no_grad():
    logits = model(x)
    loss = loss_fn(logits, y)
    pred = logits.argmax(dim=1)

model.train()
```

학습이 불안정할 때는 Loss와 gradient의 유한성, gradient norm, 입력 scale을 함께 확인합니다.
`torch.autograd.detect_anomaly()`는 원인 추적용으로 잠시 사용하고 상시 학습 코드에는 두지 않습니다.

## 7-1~7-2. Dataset and DataLoader

`Dataset`은 한 sample을 어떻게 가져올지 정의하고, `DataLoader`는 이를 batch로 묶어
shuffle과 반복을 담당합니다.

```python
dataset = TensorDataset(X, y)
loader = DataLoader(dataset, batch_size=32, shuffle=True)
xb, yb = next(iter(loader))
```

Tensor가 이미 준비된 경우 `TensorDataset`이 간단합니다. 파일 읽기, transform,
tokenization처럼 sample별 로직이 필요하면 `__len__()`과 `__getitem__()`을 구현한
Custom Dataset을 사용합니다. 분류 label의 dtype은 일반적으로 `torch.long`인지 확인합니다.

## 7-3. Transform and Preprocessing Flow

기본 흐름은 `원본 sample → transform → Dataset 반환 → DataLoader가 batch 구성`입니다.
transform은 resize·tensor 변환·normalize를 포함하는 전체 전처리이고,
augmentation은 random crop·flip처럼 train 데이터를 다양하게 만드는 transform의 일부입니다.
Validation과 test에는 무작위 augmentation을 적용하지 않습니다.

정규화의 평균과 표준편차는 train에서 한 번 계산하고 모든 split에 동일하게 적용합니다.
Validation 자체 통계를 사용하면 평가 데이터의 분포 정보를 미리 사용하고 분포 이동도 숨길 수 있습니다.
실습에서는 train `[1, 2, 3]`의 통계를 validation `[9, 10, 11]`에 적용해 이 차이를 확인했습니다.

```python
mean = train.mean(dim=0)
std = train.std(dim=0, unbiased=False)
normalized = (x - mean) / (std + 1e-7)
```

- `unbiased=False`는 분산 계산에서 `N-1` 대신 `N`으로 나눕니다.
- epsilon은 표준편차가 0일 때 0으로 나누는 오류를 막습니다.

### Why use `SubsetWithTransform`?

`random_split()`의 `Subset`들은 같은 원본 Dataset을 공유합니다. 원본 transform을 train용으로
바꾸면 validation·test에도 무작위 augmentation이 섞일 수 있으므로 index와 transform을
따로 가진 wrapper로 분리합니다.

```python
class SubsetWithTransform(Dataset):
    def __init__(self, base_dataset, indices, transform=None):
        self.base_dataset = base_dataset
        self.indices = list(indices)
        self.transform = transform

    def __len__(self):
        return len(self.indices)

    def __getitem__(self, idx):
        x, y = self.base_dataset[self.indices[idx]]
        if self.transform is not None:
            x = self.transform(x)
        return x, y
```

이 wrapper의 목적은 learning rate 최적화가 아니라 **split별 transform 격리와 평가 무결성 유지**입니다.

## 7-4. Reproducible Split and DataLoader

| Split | Purpose | Update weights? | Shuffle |
| --- | --- | --- | --- |
| Train | 모델 parameter 학습 | Yes | Usually `True` |
| Validation | 설정·best epoch 선택 | No | `False` |
| Test | 최종 모델을 한 번 확인 | No | `False` |

분할 generator와 train shuffle generator를 분리하면 데이터 소속과 epoch 순서를 독립적으로
재현할 수 있습니다. 실습에서는 같은 seed의 split이 같고, split 간 교집합이 없으며,
합집합이 원본 index 전체를 덮는지 확인했습니다.

Validation·test에서 `drop_last=True`를 쓰면 마지막 sample이 평가에서 빠집니다.
10개 중 8개만 본 후보는 거부하고 10개 전체를 본 후보를 승인했습니다.

## 7-5. Data Pipeline Debugging

학습을 오래 돌리기 전에 첫 batch와 한 번의 forward로 다음 계약을 확인합니다.

```text
input shape·dtype·finite 값
target shape·dtype·class 범위
model·input·target device 일치
logits shape
scalar loss 생성 여부
```

다중 분류 실습에서는 입력을 `[2, 2, 2] → [2, 4]`로 flatten하고,
target을 `[2, 1] float32 → [2] int64`로 고쳐 `CrossEntropyLoss` 계약을 맞췄습니다.
Batch audit에서는 평가 전 mode를 저장하고 `finally`에서 복원해 검사 함수가 호출자의
train/eval 상태를 바꾸지 않도록 했습니다.

## Questions I Asked and What I Learned

### Why is `nn.Linear(2, 1).weight` not a scalar?

입력 feature가 두 개이므로 한 출력값도 두 weight를 사용합니다. weight shape는 `[1, 2]`,
bias shape는 `[1]`이며 계산은 `y = w1*x1 + w2*x2 + b`입니다.

```python
with torch.no_grad():
    model.weight.copy_(torch.tensor([[1.0, -1.0]]))
```

### Why use `.reshape(-1, 1)` and `zeros_like()`?

`.reshape(-1, 1)`은 `[N]` 벡터를 `[N, 1]` 열 형태로 바꿔 `Linear` 입력과 target의
2차원 계약을 맞춥니다. `torch.zeros_like(x)`는 `x`와 shape·dtype이 같고 값만 0인
Tensor를 만들어 broadcasting 실수를 줄입니다.

### Is `param.grad is None` the same as a zero gradient?

아닙니다. `grad is None`은 parameter가 그래프에 참여하지 않았거나 `detach()`,
`no_grad()`, `requires_grad=False` 등으로 연결이 끊긴 상태일 수 있습니다.
반면 `grad.norm() == 0`은 backward는 수행됐지만 수학적으로 gradient가 0이라는 뜻입니다.

### Why inspect input scale before gradient clipping?

MSE에서는 입력 scale을 10배 키웠을 때 gradient norm이 약 100배 커질 수 있습니다.
바로 clipping으로 가리기 전에 입력 정규화와 전처리, Loss 식을 먼저 점검해야 합니다.

### Why call `zero_grad()` every step?

PyTorch는 `.backward()` 결과를 `.grad`에 누적합니다. 초기화를 생략하면 이전 batch의
gradient가 다음 update에 섞이는 조용한 오류가 발생합니다.

### Where is `.detach()` safe?

학습 Loss를 만들기 전 prediction에 `.detach()`를 적용하면 역전파 경로가 끊깁니다.
따라서 Loss 경로에는 사용하지 않고 metric·로그·NumPy 변환처럼 보고용 경로에만 사용합니다.

```python
metric_pred = logits.detach().argmax(dim=1)
```

`argmax(dim=1)`은 `[B, C]` 출력의 각 행에서 가장 큰 class index 하나를 반환합니다.
기록에는 `loss.item()`을 사용해 계산 그래프가 epoch 누적 변수에 남지 않게 합니다.

## Learning Reflection

이번에는 학습이 안 될 때 단순히 `backward()`를 다시 호출하는 것이 아니라 계산 그래프의
연결, `.grad`의 상태, 입력 scale, 학습·평가 모드를 순서대로 확인하는 기준을 세웠습니다.
또한 모델 학습 흐름 뒤에 `Dataset → DataLoader → batch`가 연결된다는 점을 확인하면서,
train 통계와 split별 transform을 분리하고 첫 batch의 shape·dtype부터 train step까지
추적하는 기준으로 확장했습니다.

## Next Steps

- [ ] 6-1 심화 미실행 셀을 다시 실행하고 수기 gradient와 비교
- [ ] 6-4 심화 2·3번을 실행해 parameter 변경과 누적 오류 비교
- [ ] `grad is None`과 값이 0인 gradient를 각각 재현
- [ ] 입력 scale을 1배·10배로 바꿔 MSE gradient norm 비교
- [ ] `eval()`만 사용한 경우와 `eval()+no_grad()`의 graph 생성 차이 확인
- [ ] 이전 5-2 심화 `compute_loss`의 문제별 계약 검증 마무리
- [x] 7-3~7-5 심화 실습 실행
- [ ] Train 전용 augmentation과 evaluation transform을 실제 이미지 Dataset에 적용

7-1·7-2는 오늘 이론과 코드 흐름 확인을 마쳤으므로 주말 미완료 목록에 추가하지 않습니다.

## Files

```text
05-autograd-data-pipeline/
├── README.md
├── 01-computation-graph-chain-rule-basic.ipynb
├── 02-computation-graph-chain-rule-advanced.ipynb
├── 03-requires-grad-basic.ipynb
├── 04-requires-grad-advanced.ipynb
├── 05-backward-grad-basic.ipynb
├── 06-backward-grad-advanced.ipynb
├── 07-training-step-order-basic.ipynb
├── 08-training-step-order-advanced.ipynb
├── 09-autograd-debugging-basic.ipynb
├── 10-autograd-debugging-advanced.ipynb
├── 11-transform-advanced.ipynb
├── 12-dataloader-split-advanced.ipynb
├── 13-data-pipeline-debugging-advanced.ipynb
└── requirements.txt
```
