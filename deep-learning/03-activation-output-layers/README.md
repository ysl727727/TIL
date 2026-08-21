# Activation Functions and Classification Output Layers

선형층만 쌓았을 때의 한계에서 시작해 ReLU가 만드는 비선형성,
이진 분류의 Sigmoid·`BCEWithLogitsLoss`, 다중 분류의 Softmax·`CrossEntropyLoss` 계약을 실습했습니다.

> 진행 상태: 4-1~4-4 기본 실습과 별도 심화 실습을 모두 완료했습니다.

## Practice Status

| Lesson | Topic | Basic | Separate advanced |
| --- | --- | --- | --- |
| 4-1 | 비선형성과 활성화 함수의 필요성 | Completed | Completed |
| 4-2 | ReLU의 역할과 사용 위치 | Completed | Completed |
| 4-3 | Sigmoid와 이진 분류 출력층 | Completed | Completed |
| 4-4 | Softmax와 다중 분류 출력층 | Completed | Completed |

## Why Non-linearity Is Necessary

활성화 함수 없이 `Linear` 층만 여러 개 연결하면 전체 연산은 결국 하나의 아핀 변환으로 합쳐집니다.

```text
Linear → Linear → Linear
= 하나의 Linear로 축약 가능
```

중간에 ReLU 같은 비선형 활성화 함수를 넣으면 입력 구간에 따라 다른 선형식이 적용되어
공간을 꺾을 수 있습니다. 이 때문에 단일 직선으로 분리할 수 없는 XOR 같은 패턴도 표현할 수 있습니다.

## ReLU

```text
ReLU(x) = max(0, x)
```

- 음수는 0, 양수는 그대로 통과시킵니다.
- Tensor의 shape은 바꾸지 않고 값만 바꿉니다.
- 보통 은닉층의 `Linear` 뒤에 배치합니다.
- 음수 구간의 gradient가 0이므로 뉴런이 계속 음수만 출력하면 Dead ReLU가 생길 수 있습니다.
- 출력층 뒤에는 문제 유형과 Loss를 확인하지 않고 습관적으로 ReLU를 붙이면 안 됩니다.

```text
입력 → Linear → ReLU → Linear → raw logits
```

활성화 함수의 대표적인 차이도 함께 정리했습니다.

| Function | Output or behavior | Main note |
| --- | --- | --- |
| ReLU | 음수 0, 양수 유지 | 빠르지만 Dead ReLU 가능 |
| LeakyReLU | 음수에도 작은 기울기 유지 | Dead ReLU 완화 |
| Tanh | `-1~1` | 양 끝에서 vanishing gradient 가능 |
| GELU | 입력을 부드럽게 조절 | Transformer에서 널리 사용 |

## Binary Classification Contract

이진 분류에서는 샘플마다 class 1에 대한 raw logit 하나를 출력합니다.

```text
logits: [B, 1]
target: [B, 1], torch.float32
loss:   nn.BCEWithLogitsLoss()
```

`BCEWithLogitsLoss`가 내부에서 Sigmoid와 BCE를 안정적으로 결합하므로 모델 마지막에
`nn.Sigmoid()`를 넣지 않습니다. 확률과 label은 추론할 때 만듭니다.

```python
loss = criterion(logits, target)
probs = torch.sigmoid(logits)
preds = (probs >= 0.5).long()
```

확률 `0.5`는 raw logit `0.0`과 같은 결정 경계입니다.

## Multiclass Classification Contract

다중 분류에서는 샘플마다 class 수만큼 raw logits를 출력합니다.

```text
logits: [B, C]
target: [B], torch.long
loss:   nn.CrossEntropyLoss()
target range: 0 <= target < C
```

`CrossEntropyLoss`가 내부에서 `log_softmax`와 NLLLoss를 처리하므로 모델 마지막에
Softmax를 넣지 않습니다.

```python
loss = criterion(logits, target)
probs = torch.softmax(logits, dim=-1)
preds = torch.argmax(logits, dim=-1)
```

Softmax는 값의 순서를 바꾸지 않으므로 class index만 필요할 때는 raw logits에서 바로
`argmax`를 적용해도 같은 class가 선택됩니다.

## `dim=1` and `dim=-1`

- `[B, C]`에서 `dim=1`과 `dim=-1`은 모두 class 축입니다.
- `[B, L, C]`처럼 차원이 늘어나도 `dim=-1`은 마지막 class·feature 축을 가리킵니다.
- Softmax를 `dim=0`에 적용하면 sample 사이를 정규화하므로 의도한 class 확률이 아닙니다.

검증할 때는 각 sample의 class 확률 합을 확인합니다.

```python
assert torch.allclose(probs.sum(dim=-1), torch.ones(probs.shape[0]))
```

## Newly Learned PyTorch and Python Syntax

### `criterion`

`criterion`은 Loss 객체에 흔히 붙이는 변수 이름입니다.

```python
criterion = nn.CrossEntropyLoss()
loss = criterion(logits, target)
```

첫 줄은 설정을 가진 Loss 객체를 만들고, 두 번째 줄은 그 객체를 호출해 실제 Loss를 계산합니다.

### `torch.linspace`

범위 안에서 일정한 간격의 값을 만듭니다.

```python
x = torch.linspace(-3, 3, steps=7)
```

### `torch.cat`

Tensor들을 지정한 축으로 이어 붙입니다.

```python
expanded = torch.cat([x, nonlinear_feature], dim=1)
```

### Tensor condition: `&` versus `and`

Tensor의 각 원소에 조건을 적용할 때는 `and`가 아니라 `&`를 사용하고 각 비교식을 괄호로 묶습니다.

```python
mask = (target >= 0) & (target < logits.shape[1])
```

## Learning Reflection

활성화 함수는 단순히 값을 바꾸는 함수가 아니라 여러 선형층이 하나의 선형 변환으로 합쳐지는 것을 막고,
모델이 비선형 패턴을 표현할 수 있게 한다는 점을 확인했습니다. 또한 출력층 활성화는 습관적으로 선택하는 것이 아니라
문제 유형, logits shape, target shape·dtype, Loss 함수의 계약을 한 묶음으로 설계해야 한다는 점을 배웠습니다.

## Next Steps

- [x] 4-1~4-4 기본 실습
- [x] 4-1~4-4 별도 심화 실습
- [ ] 이진·다중 분류 계약을 보지 않고 다시 작성
- [ ] 잘못된 Sigmoid·Softmax 중복 적용을 직접 만들고 수정
- [ ] `dim=0`과 `dim=-1` Softmax 결과를 행 합으로 비교
- [ ] ReLU·LeakyReLU·Tanh·GELU의 출력과 gradient 차이 실험
- [ ] threshold를 고정값으로만 보지 않고 Validation 정책과 연결해 복습

## Files

```text
03-activation-output-layers/
├── README.md
├── 01-nonlinearity-basic.ipynb
├── 02-nonlinearity-advanced.ipynb
├── 03-relu-basic.ipynb
├── 04-relu-advanced.ipynb
├── 05-sigmoid-binary-basic.ipynb
├── 06-sigmoid-binary-advanced.ipynb
├── 07-softmax-multiclass-basic.ipynb
├── 08-softmax-multiclass-advanced.ipynb
└── requirements.txt
```
