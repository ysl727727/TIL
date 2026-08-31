# Chapter 12: CNN Design, Training, and Reporting

> 2026-08-31 학습 기록. 12-1~12-8 이론과 기본 실습을 정리했습니다.

## Learning Goals

- 입력이 grayscale인지 RGB인지에 따라 첫 `Conv2d`의 `in_channels`를 맞추고, filter progression으로 Conv block을 쌓는다.
- dummy 입력을 통과시켜 classifier의 `in_features`를 자동 계산해 Linear dimension mismatch를 방지한다.
- `TensorDataset`·`DataLoader`로 학습 파이프라인을 구성하고, train/evaluate 함수를 `model.eval()`·`torch.no_grad()`와 함께 작성한다.
- Tensor 메모리 사용량을 `numel()`·`element_size()`로 계산하고 batch size·CPU/GPU 환경에 따른 변화를 확인한다.
- filter 수·kernel size를 바꿔 CNN variant를 비교하되, one-step loss만으로 모델을 선택하지 않는다.
- MLP baseline과 CNN을 같은 seed·DataLoader generator로 공정하게 비교한다.
- 실험 설정(config)과 결과(metric)를 하나의 row로 합치고, best epoch·loss gap을 계산해 리포트 문장을 자동 생성한다.
- `nn.Module`을 상속한 CNN 클래스를 직접 작성하고, 학습·검증·추론(softmax·argmax·confidence)까지 종합적으로 실행한다.

## Practice Files

| Lesson | File | Basic practice status |
| --- | --- | --- |
| 12-1 | `01-cnn-input-channel-basic.ipynb` | grayscale/RGB `in_channels`, filter progression, classifier 입력 차원 자동 계산 확인 |
| 12-2 | `02-training-pipeline-basic.ipynb` | `TensorDataset`/`DataLoader` 구성, 학습 loop와 validation accuracy 계산 확인 |
| 12-3 | `03-gpu-memory-basic.ipynb` | Tensor 메모리 계산, batch size별 메모리 표, CPU/GPU 공통 리포트 함수 확인 |
| 12-4 | `04-filter-kernel-experiment-basic.ipynb` | filter 수/kernel size 변경 실험, one-step loss 비교 확인 |
| 12-5 | `05-mlp-baseline-basic.ipynb` | 이미지 flatten, MLP baseline 모델과 한 epoch 학습 확인 |
| 12-6 | `06-mlp-vs-cnn-basic.ipynb` | 동일 조건에서 MLP·CNN 비교, best 모델 선정 확인 |
| 12-7 | `07-experiment-reporting-basic.ipynb` | 실험 로그 row 생성, best epoch·loss gap 계산, 리포트 문장 생성 확인 |
| 12-8 | `08-cnn-submission-basic.ipynb` | CNN 클래스 작성, 종합 학습/검증 루프, batch inference confidence 정리 확인 |

12-4의 `loss_value` 변수는 어디에서도 정의되지 않은 채 `round(loss_value, 4)`에 사용되어 `NameError`가 발생합니다. `loss.item()`으로 고쳐야 하며 아직 재실행하지 못했습니다. 12-8 문제 3의 첫 시도는 `with torch.no_grad:`처럼 괄호가 빠진 채 작성되어 실행되지 않았고, 이어지는 셀에서 `torch.no_grad()`로 고친 뒤 `torch.allclose`로 softmax 행 합까지 확인해 재검증했습니다.

## Core Theory

### 1. PyTorch 기초 표기

- `requires_grad=True`: 텐서 연산 과정을 자동으로 추적해 `.backward()`로 gradient를 계산할 수 있게 함. 학습 대상 파라미터에는 자동 설정된다.
- `torch.ones_like(x)`: x와 같은 shape·dtype·device를 가지되 값은 전부 1인 텐서 생성. `zeros_like`, `randn_like`도 같은 패턴.
- `atol` (절대 허용 오차): 부동소수점 비교 시 오차 허용 기준. `torch.allclose(a, b, atol=...)`처럼 gradient·확률 검증에 활용.
- `/` vs `//`: `/`는 실수 나눗셈(7/2=3.5), `//`는 몫 나눗셈(내림 처리). 음수는 "버림"이 아니라 "내림"이라 `-7//2=-4`.

### 2. Conv2d 채널과 공간 크기

- 크기 감소: Pooling·stride로 공간 정보를 압축 → 계산량 감소, receptive field 확장, 위치 불변성 확보.
- 채널 증가: 채널마다 서로 다른 특징을 감지 → 뒤로 갈수록 더 추상적이고 다양한 특징을 담기 위함.
- `Conv2d(in_channels, out_channels, kernel_size)`: `in_channels`는 데이터가 결정, `out_channels`(필터 개수)와 `kernel_size`는 설계값. `Sequential`로 쌓을 때 앞 레이어의 `out_channels` = 다음 레이어의 `in_channels`가 반드시 일치해야 한다.
- `padding = kernel_size // 2`: 입출력 크기를 동일하게 유지하는 "same padding" 공식. 홀수 커널일 때 `(kernel_size-1)/2`와 결과가 같다.

### 3. Conv2d 출력 shape 계산

```text
출력크기 = (입력크기 - kernel_size + 2×padding) / stride + 1
```

`batch_size`와 `out_channels`는 서로 무관한 별개의 차원이며, `/stride`와 `+1`은 분리된 연산이다.

### 4. Flatten과 Linear 연결

`nn.Linear`의 `in_features`는 반드시 Conv 출력의 채널×높이×너비(flatten 후 벡터 길이)와 일치해야 한다. `feat.view(feat.size(0), -1)`는 배치 크기(`size(0)`)는 유지하고 나머지는 `-1`로 자동 계산해 1차원으로 펼친다. dummy 입력을 실제로 통과시켜 이 길이를 계산하면 이미지 크기가 바뀌어도 mismatch를 줄일 수 있다.

### 5. MLP vs CNN 파라미터 수 차이

- MLP: 완전연결이라 입력 크기에 비례해 파라미터가 폭증한다.
- CNN: 지역 연결(작은 영역만 봄) + 가중치 공유(필터를 전체에 재사용) → 이미지 크기와 무관하게 파라미터 수가 고정된다.

### 6. 활성화 함수와 경사 소실

- `tanh`: 출력 범위 -1~1, zero-centered. sigmoid(0~1)보다 학습에 유리하지만 기울기 소실 문제는 여전히 존재한다.
- 기울기 소실: sigmoid/tanh는 미분값이 항상 1보다 작아(sigmoid 최대 0.25) 레이어를 거슬러 곱해질수록 기울기가 기하급수적으로 작아진다 → 앞쪽 레이어 학습이 어려워진다.
- ReLU: 양수 구간 미분값이 항상 1이라 기울기가 줄어들지 않아 깊은 네트워크 학습에 유리하다. 단점은 Dying ReLU(음수 영역 뉴런이 영원히 죽을 수 있음).

### 7. 학습 루프 패턴

`optimizer.zero_grad()` → forward → loss 계산 → `loss.backward()` → `optimizer.step()`. 1 epoch은 전체 데이터를 한 번 다 통과시키는 것이며, `for epoch in range(N)`은 이를 N번 반복한다는 뜻이다.

### 8. 실습 코드 패턴

- `nn.Module` 작성 시 `__init__`에는 레이어 정의만, `forward`에는 실제 데이터가 레이어를 통과하는 흐름(flatten 포함)만 넣는다.
- `{**config, **metric}`: 두 딕셔너리를 병합하며 겹치는 key는 뒤 딕셔너리 값이 우선한다. 실험 설정+결과를 한 줄(row)로 만들어 표로 정리할 때 유용하다.
- `tensor_mb`: `tensor.numel() * tensor.element_size() / (1024 ** 2)`. 총 원소 수 × 원소당 바이트를 MB로 변환한다.

## Questions and Newly Learned Points

### Design Choices

- one-step loss는 초기화 영향이 커서 모델 선택 기준으로 쓰지 않으며, 실제 비교는 같은 학습 조건의 validation metric으로 판단해야 한다.
- validation loss가 가장 낮은 epoch를 best epoch로 고르고, 그 epoch의 `train_loss - valid_loss`(loss gap)로 과적합 신호를 살핀다. accuracy gap과 혼동하지 않도록 metric 종류를 이름에 명시한다.
- 리포트는 숫자 나열이 아니라 선택 기준·결론·한계까지 함께 적어야 한다.

### Inference

- 추론에서는 `model.eval()`과 `torch.no_grad()`를 함께 사용한다.
- `F.softmax(logits, dim=1)` 결과의 행 합이 1인지 `torch.allclose`로 확인한 뒤, `argmax` index를 미리 정의한 class mapping(`idx_to_class`)으로 되돌려 사람이 읽을 class 이름과 confidence를 함께 남긴다.

## Environment

```bash
pip install -r requirements.txt
```
