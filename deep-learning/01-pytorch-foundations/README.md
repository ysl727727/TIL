# PyTorch Foundations: Training Flow, Tensor, Dtype, and Shape

규칙 기반·머신러닝·딥러닝의 적용 기준에서 시작해,
PyTorch 학습 흐름과 Tensor의 dtype·shape·batch·broadcasting을 실습했습니다.

> 진행 상태: 1-2~2-2 기본 실습 모두 완료. 별도 심화 실습은 1-2만 완료했습니다.

## Practice Status

| Notebook label | Topic | Basic | Separate advanced |
| --- | --- | --- | --- |
| 1-2 | 규칙 기반·ML·DL 선택 | Completed | Completed |
| 1-3 | 데이터→모델→손실→최적화→평가 | Completed | Pending |
| 1-4 | 문제 유형·출력·Loss 연결 | Completed | Pending |
| 1-5 | PyTorch 코드 구조 읽기 | Completed | Pending |
| 2-1 | Tensor dtype·shape·ndim | Completed | Pending |
| 2-2 | Batch dimension·broadcasting | Completed | Pending |

강의 원문이나 제공된 정답 셀 대신, 공개 노트북에는 작성하고 실행한 코드와 결과만 남겼습니다.

## What I Learned

### Choosing an Approach

- 공식이 명확하고 자주 바뀌지 않으면 규칙 기반을 먼저 검토합니다.
- 구조화된 특징과 라벨이 있으면 전통적인 머신러닝 baseline을 만들 수 있습니다.
- 텍스트·이미지처럼 사람이 특징을 전부 정의하기 어려운 데이터와 충분한 라벨이 있을 때 딥러닝을 후보로 검토합니다.
- 딥러닝이 가능하다는 사실과 가장 먼저 쓰어야 한다는 판단은 다릅니다.

### Training Flow

```text
DataLoader에서 batch 꺼내기
→ model(x) forward
→ loss 계산
→ optimizer.zero_grad()
→ loss.backward()
→ optimizer.step()
→ validation 평가
```

`zero_grad()`는 이전 gradient 누적을 초기화하고, `backward()`는 gradient를 계산하며,
`step()`은 그 gradient를 사용해 parameter를 업데이트합니다.

### Problem, Output, and Loss

| Problem | Typical output | Loss candidate | Target |
| --- | --- | --- | --- |
| 회귀 | `[B, 1]` | `MSELoss` | float 실수 |
| 이진 분류 | `[B, 1]` logits | `BCEWithLogitsLoss` | 0/1 float |
| 다중 분류 | `[B, C]` logits | `CrossEntropyLoss` | class index `int64` |

`CrossEntropyLoss`에는 class index를 넘기므로 target의 dtype이 `torch.int64`여야 합니다.

### Tensor Checks

Tensor를 만나면 다음 순서로 확인합니다.

```python
print(tensor.shape)
print(tensor.dtype)
print(tensor.ndim)
print(tensor.device)
```

| Expression | Meaning |
| --- | --- |
| `tensor.long()` | Tensor를 `torch.int64` dtype으로 변환 |
| `torch.int64` | 64-bit 정수 dtype, `torch.long`과 같은 의미 |
| `tensor.to(torch.int64)` | 목표 dtype을 지정해 변환 |
| `tensor.dtype` | 현재 Tensor의 dtype 확인 |

### `zip()` and `*case`

`zip()`은 여러 iterable의 같은 위치 값을 짝으로 묶어 반복합니다.

```python
for block, stage in zip(code_blocks, stage_names):
    print(block, stage)
```

다음 코드에서 `case`는 함수의 매개변수 이름이 아니라 현재 반복에서 꺼낸 tuple 변수입니다.
`*`가 tuple을 풀어서 함수의 위치 인자로 나누어 전달합니다.

```python
cases = [(False, 400, True), (True, 28000, False)]

for case in cases:
    recommend_start(*case)
    # recommend_start(case[0], case[1], case[2])와 같은 의미
```

반면 함수 정의에서 `def func(*args):`라고 쓰면 여러 위치 인자를 tuple로 모으는 반대 동작입니다.

### Batch and Broadcasting

- `unsqueeze(0)`는 맨 앞에 batch 차원을 추가합니다.
- `[4, 3] + [3]`에서 `[3]`은 각 batch 행에 반복 적용되어 결과가 `[4, 3]`이 됩니다.
- `pred=[4, 1]`, `target=[4]`를 그대로 연산하면 의도하지 않은 broadcasting이 발생할 수 있습니다.
- Loss 계산 전에 `pred.shape == target.shape`를 확인하는 습관이 필요합니다.

## Learning Reflection

기본 실습을 통해 학습 코드를 위에서 아래로 읽는 순서와 Tensor의
shape·dtype을 먼저 확인하는 디버깅 순서를 연결했습니다.

특히 `.long()`, `torch.int64`, `.to(torch.int64)`가 결국 다중 분류 target을
class index용 64-bit 정수로 맞추는 여러 표현이라는 점을 새로 알게 됐습니다.
`zip()`과 `recommend_start(*case)`를 통해 여러 값을 짝지어 반복하고
tuple을 인자로 풀어 전달하는 방법도 학습했습니다.

모든 기본 실습은 완료했지만, 별도 심화 실습은 1-2만 진행했습니다.
완료한 코드와 참고 없이 재작성할 수 있는 코드를 구분하며 다음 심화 실습을 진행할 계획입니다.

## Next Steps

- [x] 1-2~2-2 기본 실습
- [x] 1-2 심화 실습
- [ ] 1-3~2-2 별도 심화 실습
- [ ] dtype 변환 코드를 참고 없이 재작성
- [ ] `zip()`과 tuple unpacking을 작은 함수에 직접 적용
- [ ] broadcasting 전에 예상 shape을 먼저 적고 실행 결과와 비교

## Files

```text
01-pytorch-foundations/
├── README.md
├── 01-ml-vs-dl-basic.ipynb
├── 02-ml-vs-dl-advanced.ipynb
├── 03-training-flow-basic.ipynb
├── 04-problem-io-basic.ipynb
├── 05-pytorch-code-reading-basic.ipynb
├── 06-tensor-dtype-shape-basic.ipynb
├── 07-batch-broadcasting-basic.ipynb
└── requirements.txt
```
