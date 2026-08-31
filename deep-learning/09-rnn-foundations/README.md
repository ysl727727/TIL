# Chapter 13: RNN Sequence Modeling and Gradient Stability

> 2026-08-31 학습 기록. 13-1~13-3 이론과 기본 실습을 정리했습니다.

## Learning Goals

- sequence 데이터를 `[batch, seq_len, input_size]` 형태로 구성하고 `nn.RNN`의 `output`·`h_n` shape를 해석한다.
- `batch_first` 설정에 따라 입력 축 순서를 맞추고, 마지막 time step output과 `h_n[-1]`이 값까지 동일함을 확인한다.
- `num_layers`를 늘렸을 때 `h_n`의 첫 차원이 layer 수가 됨을 확인하고 마지막 layer hidden을 분류기에 연결한다.
- 반복 `tanh` 연산으로 경사 소실을 직관적으로 확인한다.
- 전체 파라미터 gradient의 global L2 norm을 계산해 학습 신호 크기를 모니터링한다.
- `clip_grad_norm_`으로 gradient clipping을 적용하고 clipping 전후 norm을 비교한다.

## Practice Files

| Lesson | File | Basic practice status |
| --- | --- | --- |
| 13-1 | `01-sequence-hidden-state-basic.ipynb` | sequence batch 구성, RNN `output`/`h_n` shape 확인, 마지막 hidden으로 분류 확인 |
| 13-2 | `02-rnn-forward-shape-basic.ipynb` | `batch_first` 변환, 마지막 time step 선택, 2-layer RNN hidden 해석 확인 |
| 13-3 | `03-vanishing-gradient-clipping-basic.ipynb` | 반복 tanh gradient 감소, RNN global grad norm, gradient clipping 전후 비교 확인 |

13-3의 두 문제는 첫 실행 셀과 동일한 코드를 다시 실행해 값을 재확인한 셀이며, 별도의 코드 수정은 없었습니다.

## Core Theory

### 1. RNN output과 h_n shape

입력 `(batch, seq_len, input_size)` 기준:

- `output`: `(batch, seq_len, hidden_size)` — 모든 시점의 은닉상태를 모은 것.
- `h_n`: `(num_layers, batch, hidden_size)` — 마지막 시점의 은닉상태만.

단층·단방향 RNN에서는 `output[:, -1, :]`와 `h_n[-1]`이 shape뿐 아니라 값까지 같다.

### 2. 시점(seq_len)과 hidden_size의 독립성

- 시점 개수(`seq_len`)는 입력 데이터의 시퀀스 길이에서 자동 결정된다.
- `hidden_size`는 `nn.RNN(input_size, hidden_size)` 생성 시 사람이 직접 지정하는 하이퍼파라미터로, "각 시점을 몇 개의 숫자로 요약할지"를 정한다.
- 두 값은 서로 완전히 독립적이다.

### 3. 다층 RNN과 마지막 layer hidden

`num_layers=2`처럼 층을 쌓으면 1층의 출력이 2층의 입력으로 다시 들어가 한 번 더 요약된다. `h_n`의 첫 차원이 층 개수만큼 늘어나며(`(2, batch, hidden)`), 보통 가장 정제된 마지막 층(`h_n[-1]`)을 분류기에 사용한다.

### 4. 경사 소실 직관 (반복 tanh)

같은 `tanh` 연산을 반복 적용할수록(step 수가 늘어날수록) 시작 텐서의 gradient가 점점 작아진다. 이는 긴 sequence에서 초기 정보 학습이 어려워지는 경사 소실 문제와 직접 연결된다.

### 5. Gradient Global L2 Norm

`loss.backward()` 후 모든 파라미터의 `.grad`가 채워진다. 이를 제곱해서 다 더한 뒤 제곱근을 취하면 `sqrt(sum(grad ** 2))`, 즉 전체 gradient 크기(global L2 norm)를 계산할 수 있다. 값이 너무 작으면 학습 신호가 약하고, 너무 크면 학습이 불안정해질 수 있다.

### 6. Gradient Clipping

`torch.nn.utils.clip_grad_norm_(params, max_norm)`은 clipping 전의 global L2 norm을 반환하면서, gradient가 `max_norm`보다 클 때 update 크기를 제한한다. RNN/LSTM처럼 sequence 길이에 영향을 받는 모델에서 학습 안정화에 자주 쓰인다.

## Questions and Newly Learned Points

- RNN `output`/`h_n` shape 해석: `output`은 모든 시점, `h_n`은 마지막 시점만 담는다는 점을 12장의 CNN feature map shape 계산과 비교하며 재확인했다.
- `hidden_size=5`처럼 hidden 차원 수는 seq_len과 무관하게 임의로 정할 수 있는 설계값이라는 점.
- gradient norm 계산과 clipping은 RNN처럼 긴 시퀀스를 반복 통과하는 구조에서 특히 중요하다는 점 — 12장 학습 루프(`loss.backward()` → `optimizer.step()`)에 이어지는 확장으로 정리했다.

## Environment

```bash
pip install -r requirements.txt
```
