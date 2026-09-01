# PyTorch Foundations: Tensor, Device, and Debugging

규칙 기반·머신러닝·딥러닝의 적용 기준에서 시작해 PyTorch 학습 흐름과
Tensor의 dtype·shape·batch·broadcasting·device 및 오류 디버깅을 실습했습니다.

> 진행 상태: 1-2~2-4 기본 실습 완료. 별도 심화 실습은 1-2와 2-3을 완료했습니다.

## Practice Status

| Notebook label | Topic | Basic | Separate advanced |
| --- | --- | --- | --- |
| 1-2 | 규칙 기반·ML·DL 선택 | Completed | Completed |
| 1-3 | 데이터→모델→손실→최적화→평가 | Completed | Pending |
| 1-4 | 문제 유형·출력·Loss 연결 | Completed | Pending |
| 1-5 | PyTorch 코드 구조 읽기 | Completed | Pending |
| 2-1 | Tensor dtype·shape·ndim | Completed | Pending |
| 2-2 | Batch dimension·broadcasting | Completed | Pending |
| 2-3 | CPU/GPU device와 `.to(device)` | Completed | Completed |
| 2-4 | Shape·dtype·device 오류 디버깅 | Completed | Not provided |

기본 노트북 안에 포함된 심화 항목도 직접 작성하고 실행했습니다. 공개 노트북에는
강의 원문이나 제공 정답 대신 작성한 코드와 실행 결과만 남겼습니다.

## What I Learned

### Tensor and Device Contract

Tensor를 만나면 다음 네 항목부터 확인합니다.

```python
print(tensor.shape)
print(tensor.dtype)
print(tensor.ndim)
print(tensor.device)
```

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)
x = x.to(device)
y = y.to(device)
```

모델과 입력 Tensor가 서로 다른 device에 있으면 연산할 수 없습니다. 학습 루프에서는
모델을 한 번 옮기고, DataLoader에서 꺼낸 각 batch의 입력과 target을 같은 device로 옮깁니다.

### Shape·Dtype·Device Debugging Order

```text
오류 메시지의 마지막 줄 확인
→ shape / dtype / device 중 하나로 분류
→ 오류 직전 Tensor 정보 출력
→ 모델·loss가 기대하는 조건과 비교
→ 수정 후 다시 출력하고 검증
```

- `nn.Linear` 입력의 마지막 차원은 `in_features`와 같아야 합니다.
- 샘플 하나 `[F]`는 필요할 때 `unsqueeze(0)`으로 `[1, F]` batch로 만듭니다.
- `CrossEntropyLoss` target은 class index 형태의 `torch.int64`여야 합니다.
- prediction과 target shape이 다르면 의도하지 않은 broadcasting부터 확인합니다.

### Useful Python and PyTorch Syntax

| Expression | Meaning |
| --- | --- |
| `tensor.long()` | Tensor를 `torch.int64`로 변환 |
| `tensor.to(torch.int64)` | 목표 dtype을 지정해 변환 |
| `tensor.to(device)` | Tensor를 지정 device로 이동 |
| `zip(a, b)` | 같은 위치의 항목을 1:1로 묶어 반복 |
| `set(values)` | 중복 값을 제거한 집합 생성 |
| `next(iterator)` | iterator의 다음 항목 하나 반환 |

조건을 만족하는 첫 항목을 찾을 때는 generator expression과 `next()`를 함께 사용할 수 있습니다.

```python
first_cuda_run = next(
    (run for run in runs if run["device"] == "cuda:0"),
    None,
)
```

두 번째 인자 `None`은 조건을 만족하는 항목이 없을 때 `StopIteration` 대신 반환할 기본값입니다.

## Learning Reflection

dtype와 shape뿐 아니라 device도 연산 전에 맞춰야 하는 Tensor의 계약이라는 점을 확인했습니다.
오류가 길어도 마지막 줄에서 종류를 분류하고, 연산 직전의 shape·dtype·device를 출력하면
확인 범위를 줄일 수 있었습니다.

## Next Steps

- [x] 1-2~2-4 기본 실습
- [x] 1-2·2-3 별도 심화 실습
- [ ] 1-3~2-2 별도 심화 실습
- [ ] dtype·shape·device 오류를 각각 하나씩 다시 만들고 수정
- [ ] batch 이동 helper를 참고 없이 재작성

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
├── 08-device-basic.ipynb
├── 09-device-advanced.ipynb
├── 10-shape-device-debugging-basic.ipynb
└── requirements.txt
```
