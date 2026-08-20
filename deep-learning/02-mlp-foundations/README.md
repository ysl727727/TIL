# MLP Foundations: Perceptron, Linear Layers, Flatten, and Forward

퍼셉트론의 선형 결정 경계에서 시작해 MLP의 층 구조, `nn.Linear`의 가중치와 편향,
이미지 flatten, `nn.Module` 클래스와 `forward` 구현까지 실습했습니다.

> 진행 상태: 3-1~3-5 기본 실습과 각 노트북 안의 심화 항목을 완료했습니다.

## Practice Status

| Notebook label | Topic | Status |
| --- | --- | --- |
| 3-1 | 퍼셉트론과 선형 결정 경계 | Completed |
| 3-2 | MLP 입력층·은닉층·출력층 | Completed |
| 3-3 | 가중치·편향과 `nn.Linear` | Completed |
| 3-4 | 입출력 차원 계산과 flatten | Completed |
| 3-5 | `nn.Module`과 MLP `forward` 구현 | Completed |

## What I Learned

### Perceptron and MLP

퍼셉트론은 입력의 가중합으로 하나의 logit을 만듭니다.

```text
z = x @ w + b
```

하나의 선형 경계로 XOR 같은 비선형 패턴을 나눌 수 없기 때문에, MLP는 여러
`Linear` 층 사이에 `ReLU` 같은 비선형 활성화 함수를 넣습니다.

```text
[B, input_dim]
→ Linear(input_dim, hidden_dim)
→ ReLU
→ Linear(hidden_dim, num_classes)
→ [B, num_classes] logits
```

### `nn.Linear` Shape and Parameters

`nn.Linear(in_features, out_features)`의 parameter shape은 다음과 같습니다.

```text
weight: [out_features, in_features]
bias:   [out_features]
output: X @ weight.T + bias
```

`p.numel()`은 parameter Tensor 안의 원소 수를 셉니다. 모델 전체 parameter 수는 다음처럼 계산합니다.

```python
total_params = sum(p.numel() for p in model.parameters())
```

### Image Flatten and the Link to CNN

이미지 batch `[B, C, H, W]`를 MLP에 넣으려면 batch 축은 유지하고 나머지를 펼칩니다.

```python
flat = torch.flatten(images, start_dim=1)
# [B, C, H, W] -> [B, C * H * W]
```

MLP는 flatten 과정에서 이미지의 가로·세로 이웃 관계를 긴 벡터로 바꿉니다. 이 지점에서
공간 구조를 유지하며 지역 패턴을 학습하는 CNN이 왜 필요한지 연결해서 생각하게 됐습니다.

### `nn.Module` Class and `forward`

```python
class TinyMLP(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu(x)
        return self.fc2(x)
```

- `__init__`: 모델이 사용할 layer를 준비하고 `self`에 등록합니다.
- `forward`: 입력 `x`가 layer를 통과하는 순서를 정의합니다.
- `model(x)`: `nn.Module`의 호출 과정을 거쳐 `forward(x)`를 실행합니다.
- `self`: 입력 데이터가 아니라 만들어진 모델 객체 자신을 가리킵니다.

### Python Helpers

- `set(values)`: 중복 항목을 제거합니다. 원래 순서를 보존해야 한다면 별도 처리가 필요합니다.
- `zip(a, b)`: 같은 위치의 항목을 1:1로 묶으며, 짧은 iterable이 끝나면 함께 멈춥니다.
- `next(generator, default)`: 조건을 만족하는 항목 중 첫 번째를 반환하고, 없으면 `default`를 반환합니다.
- `p.numel()`: parameter Tensor에 들어 있는 전체 원소 수를 반환합니다.

## Learning Reflection

이미지를 MLP에 넣기 위해 flatten하는 과정에서, 이미지의 공간 정보를 더 잘 활용하는 CNN으로
다음 학습 내용이 이어지는 이유를 생각하게 됐습니다. 또한 3-5의 MLP 구현을 통해
`class`, `self`, `__init__`, `forward` 같은 Python 클래스 문법을 더 공부할 필요성을 느꼈습니다.

## Next Steps

- [x] 3-1~3-5 기본 및 노트북 내 심화 실습
- [ ] `TinyMLP`를 보지 않고 다시 작성
- [ ] `self`와 입력 `x`의 역할을 코드 한 줄씩 설명
- [ ] MLP의 flatten과 CNN의 공간 정보 처리 차이 정리
- [ ] hidden size 변경 전후 parameter 수를 손계산하고 `p.numel()`로 검산

## Files

```text
02-mlp-foundations/
├── README.md
├── 01-perceptron-linear-boundary-basic.ipynb
├── 02-mlp-layers-basic.ipynb
├── 03-linear-weight-bias-basic.ipynb
├── 04-image-flatten-basic.ipynb
├── 05-mlp-forward-basic.ipynb
└── requirements.txt
```
