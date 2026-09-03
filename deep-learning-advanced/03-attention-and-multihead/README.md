# Chapter 3: Attention and Multi-Head Shape

> 2026-09-03 학습 기록. 3-1~3-5 실습을 모두 완료하고 Q&A를 정리했습니다.

## Learning Goals

- Query·Key·Value가 입력에 서로 다른 학습된 projection을 곱해 만들어진다는 것을 이해하고, `Q=K=V=X`가 "값이 같다"가 아니라 "입력 출처가 같다"는 뜻임을 구분한다.
- Q·K 내적으로 token 간 관련도를 구하고, 자기 자신을 제외한 최상위 관계를 찾는다.
- `softmax(QKᵀ/√d_k + M)V` 수식의 연산 순서(scale → mask → softmax → weighted sum)를 정확히 따르고, `[B,T,D]` batch 입력으로 확장한다.
- Attention weight를 Value에 대한 가중합으로 분해해 context vector에 각 token이 기여한 정도를 계산한다.
- Shannon entropy로 attention 분포의 집중도를 측정하고, 여러 head의 최상위 관계가 일치(unanimous)하는지 확인한다.
- `nn.Module`로 Q/K/V/출력 projection을 등록한 학습 가능한 `SelfAttention`을 작성하고, padding mask를 지원하도록 확장한다.
- Hidden 차원을 여러 head로 나누고(`split_heads`) 다시 합치는(`merge_heads`) shape 변환을 구현하고 `MultiHeadSelfAttention` 전체를 작성한다.
- MHA/GQA의 Query/KV head 수 차이와 KV Cache 메모리 절감 배수를 계산한다.
- Shape trace로 `view`·`transpose` 순서 오류가 발생한 첫 단계를 찾는다.

## Practice Files

| Lesson | File | Practice status |
| --- | --- | --- |
| 3-1 | `01-qkv-projection-and-relevance.ipynb` | Q·K·V projection 함수, Query별 최상위 Key 찾기(`find_top_keys`), softmax+threshold 기반 관계 리포트(`build_relation_report`) 확인 |
| 3-2 | `02-scaled-dot-product-attention.ipynb` | Scaled Dot-Product Attention 전체 구현, padding mask 적용, `[B,T,D]` batch attention 확장 확인 |
| 3-3 | `03-attention-weight-and-context-interpretation.ipynb` | Context vector 기여도 분해(`decompose_context`), attention entropy 계산, 여러 head 최상위 관계 일치 확인(`summarize_heads`) 확인 |
| 3-4 | `04-self-attention-module.ipynb` | Tensor 기반 `self_attention` 함수, `nn.Module` 기반 `SelfAttention`, padding mask를 지원하는 `MaskedSelfAttention` 확인 |
| 3-5 | `05-multihead-attention-and-debugging.ipynb` | `split_heads`/`merge_heads` shape 변환, `MultiHeadSelfAttention` 전체 구현, GQA KV Cache 절감 배수 계산, shape trace 디버거(`audit_mha_trace`) 확인 |

다섯 파일 모두 첫 실행에서 assert 검증을 통과했고 별도 수정 셀은 없었습니다.

## Core Theory

### 1. Query · Key · Value

- Query(Q): 지금 찾는 정보 / Key(K): 각 위치가 가진 정보를 비교할 표지 / Value(V): 최종적으로 섞어 가져올 내용.
- Q/K/V는 고정된 의미 벡터가 아니라 입력 `X`에 서로 다른 학습된 projection(`W_Q`, `W_K`, `W_V`)을 곱해 만든 결과물이다. `Q=K=V=X`는 입력 출처가 같다는 뜻이지 값이 같다는 뜻이 아니다.
- 모든 token에 **동일한** `W_q`, **동일한** `W_k`가 각각 적용된다(token마다 다른 Linear를 쓰는 게 아니다). 다만 `W_q`와 `W_k` 자체는 서로 다른 변환이라 같은 입력이라도 통과하는 weight에 따라 Q 또는 K가 나온다.
- 행렬곱 `X @ W`가 성립하려면 `X`의 마지막 차원과 `W`의 첫 번째 차원(행 개수)이 같아야 한다 — 구멍 개수(X의 차원)와 핀 개수(W의 입력 차원)가 맞아야 결합되는 레고 블록과 같다.

```python
Q = X @ W_q   # [B, L, d_k]
K = X @ W_k   # [B, L, d_k]
V = X @ W_v   # [B, L, d_v]
scores = Q @ K.transpose(-2, -1)   # [B, L_q, L_k]
```

- `d_k`와 `d_v`는 같을 필요가 없다 — Q, K는 내적으로 비교해야 해서 차원이 같아야 하지만, V는 가중합될 뿐이라 차원이 달라도 된다.
- Self-Attention은 Q/K/V가 모두 같은 sequence에서 나오고(`L_q = L_k`), Cross-Attention은 Q가 decoder 상태, K/V가 encoder 출력에서 나온다(`L_q ≠ L_k`일 수 있음). K와 V는 항상 같은 원천에서 나오므로 토큰 개수가 자동으로 항상 같다.
- `QKᵀ` raw score는 아직 확률이 아니다 — 음수가 가능하고 행 합이 1일 필요가 없다.

### 2. Query별 최상위 Key 찾기와 관계 리포트

- `scores = Q @ K.T` 후 `fill_diagonal_(float("-inf"))`로 자기 자신과의 유사도(보통 가장 큼)를 후보에서 제외하고 `argmax(dim=-1)`로 각 행(Query)의 최댓값 열(Key) 인덱스를 찾는다. `dim=-1`은 "각 행 안에서" 최댓값을 찾는다는 뜻이고, `dim=0`이면 반대로 "각 열 안에서"가 된다.
- `Q.size(0) != len(tokens)` 같은 사전 검사는 Q/K의 "몇 번째 위치"가 실제 몇 번째 토큰인지 어긋나지 않게 하는 안전장치다 — 개수가 안 맞으면 top-k 결과가 엉뚱한 토큰 이름과 매칭되는 조용한 버그가 생길 수 있다.
- softmax 기반 리포트(`build_relation_report`)는 `j != i` 조건으로 자기 자신을 제외하고, `threshold` 미만이면 "확신 있는 관계"로 보지 않고 결과에서 제외한다.

### 3. Scaled Dot-Product Attention과 Mask

연산 순서는 항상 고정된다: `score → scale → mask → softmax → weighted sum`.

```python
scores = (Q @ K.transpose(-2, -1)) / math.sqrt(Q.size(-1))
weights = torch.softmax(scores, dim=-1)
output = weights @ V
```

- Softmax는 마지막 축(Key 축, `dim=-1`)에 적용한다 — 각 Query가 여러 Key에게 나눠주는 "관심의 합"이 1이 되어야 하기 때문이다. `dim=-2`(Query 축)에 적용하면 "각 Key가 여러 Query로부터 얼마나 주목받는지"가 되어 의도와 반대가 된다.
- `math.sqrt(Q.size(-1))`로 나누는 이유: 차원이 클수록 내적 값이 자연스럽게 커져 softmax가 한 곳에 쏠리고 gradient가 작아질 수 있다(분산이 차원에 비례하므로 표준편차인 제곱근으로 나눈다). head 분리 전에는 `hidden_size`, head 분리 후에는 `head_dim`(=`d_k`)을 사용해야 한다.
- Mask는 반드시 softmax 이전에 적용한다. `masked_fill(~key_mask, -inf)`로 padding Key의 score를 `-inf`로 만들면 `e^(-inf)=0`이 되어 나머지가 자동으로 재분배되며 행 합이 정확히 1로 유지된다. softmax 이후에 0을 곱하면 남은 weight 합이 1보다 작아진다.
- `key_mask.unsqueeze(0)`(또는 batch 버전 `unsqueeze(1)`)으로 Query 축에 크기 1을 넣어 broadcasting하면 모든 Query 행에 동일한 mask가 열 방향으로 적용된다. 반대로 Query 축을 마스킹(`unsqueeze(-1)`)하면 "그 Query 자체가 가짜라 결과 전체를 무시"하는 다른 의미가 된다. `unsqueeze`는 값을 선택·삭제하는 연산이 아니라 차원을 추가하는 연산일 뿐이라, 배치별 mask 값은 각각 그대로 유지된다.
- 모든 Key가 mask된 입력은 `softmax([-inf,...])`가 `0/0`(NaN)이 될 수 있어 명시적으로 오류 처리해야 한다.
- Q-K 사전 검사는 **차원**(`Q.size(-1) == K.size(-1)`, 내적 성립 조건)을 확인하고, K-V 사전 검사는 **토큰 개수**(`K.size(-2) == V.size(-2)`, `weights @ V` 성립 조건)를 확인한다 — 서로 다른 것을 검증한다는 점에 주의한다.

### 4. Context Vector 분해와 Attention 해석

- `contributions = weights.unsqueeze(-1) * V`; `context = contributions.sum(dim=0)`: token별 weight를 그 token의 Value 벡터 전체에 곱한(원소별 곱, broadcasting) "기여분"을 만든 뒤, 토큰 축(`dim=0`)을 없앨 때까지 합쳐 하나의 context 벡터로 만든다. 이는 `weights @ V`(행렬곱)와 수학적으로 동일하지만 "누가 얼마나 기여했는지" 중간 과정을 들여다볼 수 있다.
- weight가 큰 token이 항상 모든 차원에서 가장 큰 기여를 만드는 것은 아니다 — 실제 기여는 weight와 Value 벡터 값이 함께 결정한다.
- Attention entropy(`-Σ(p·log p)`)는 분포가 골고루 퍼져 있을수록 크고 한 곳에 몰릴수록 작다. `clamp_min(eps)`로 0에 로그를 취해 `-inf`가 되는 것을 방지하고, `log(Key 개수)`로 나눈 normalized entropy로 Key 개수가 다른 경우끼리도 비교할 수 있게 한다. 집중도가 높다고 항상 좋은 attention은 아니며 task와 layer 역할에 따라 해석해야 한다.
- 여러 head의 최상위 관계가 일치하는지(`unanimous`) 확인할 때, head 평균(`mean(dim=0)`)은 전체 경향을 빠르게 보여주지만 서로 다른 역할을 가진 head를 평균내면 중요한 차이가 사라질 수 있어 평균과 head별 결과를 함께 봐야 한다.

### 5. 학습 가능한 SelfAttention 모듈

- Weight를 함수 밖 임의 Tensor로 두는 대신 `nn.Linear`로 등록해야 optimizer가 해당 parameter를 찾아 갱신할 수 있다. `out_proj`는 attention context를 다시 hidden space에서 조합하는 역할을 한다.
- self-attention은 입력과 출력 차원이 유지되어야 하므로(이후 여러 층을 쌓기 위해) `nn.Linear(hidden_size, hidden_size)`처럼 입력=출력 차원의 정사각형 projection을 사용한다. `weight.size(0)`(입력 차원)만 맞아도 행렬곱 자체는 가능하지만, self-attention에서는 출력 차원도 `hidden_size`와 같아야 이후 `Q @ K.T` 등에서 차원 불일치가 나지 않는다.
- `nn.Linear(hidden_size, hidden_size, bias=False)` 하나당 parameter 수는 `hidden_size²`이며, q/k/v/out 4개를 합치면 `4 × hidden_size²`이다(예: `hidden_size=6`이면 `4×36=144`).
- Padding mask를 지원하는 `MaskedSelfAttention`은 `attention_mask.shape != x.shape[:2]`로 `[B, T]` 계약을 사전 검증한 뒤, `.to(torch.bool)`로 타입을 맞추고 `.unsqueeze(1)`로 broadcasting을 준비해 `masked_fill`로 padding을 차단한다. Padding 위치가 Key로 선택되지 않도록만 처리했으며, Padding Query의 output까지 제거하려면 forward 마지막에 query mask를 별도로 곱해야 한다.

### 6. Multi-Head Attention

- 여러 head를 쓰는 이유는 같은 문장을 여러 관점(전문가)이 동시에 보기 위해서다 — 각 head의 역할은 미리 정해지지 않고 학습으로 결정된다.
- `D_head = D_model / num_heads`이며 `D_model % num_heads == 0`이어야 한다.
- Head 분리는 선형 투영 **다음에** 이루어진다: 먼저 하나의 큰 `W_q`로 전체를 투영한 뒤(`self.q_proj(x)`), 그 결과를 head 개수만큼 나눈다(`self._split(...)`). 원본을 먼저 조각내 각기 다른 작은 투영을 적용하는 것이 아니다.

```python
def split_heads(x, num_heads):
    batch, length, d_model = x.shape
    d_head = d_model // num_heads
    return x.reshape(batch, length, num_heads, d_head).transpose(1, 2)

def merge_heads(x):
    batch, heads, length, d_head = x.shape
    return x.transpose(1, 2).contiguous().reshape(batch, length, heads * d_head)
```

- `transpose`는 메모리를 실제로 옮기지 않고 "읽는 순서표"만 바꾸는 연산이라, 그 직후 바로 `reshape`를 하면 stride 오류가 날 수 있다. `contiguous()`가 순서표대로 메모리를 실제로 재정렬해 그 뒤의 `reshape`를 안전하게 만든다.
- shape 흐름: `[B,L,D_model] → [B,L,H,D_head] → [B,H,L,D_head]`(head별 계산) `→ [B,L,H,D_head] → [B,L,D_model]`. Concat만으로는 head끼리 정보가 섞이지 않으므로 `W_O`(행렬곱)를 곱해야 head 정보가 실제로 섞인 새로운 표현이 된다.
- MHA/MQA/GQA는 Query head 수(`H_q`)와 K/V head 수(`H_kv`)의 관계로 구분된다: MHA는 `H_q = H_kv`(직원마다 전용 폴더), MQA는 `H_kv = 1`(전원 폴더 1개 공유), GQA는 `1 < H_kv < H_q`(그룹별 폴더 공유). KV Cache 크기는 `H_kv`에 비례하므로 GQA/MQA는 긴 문맥 추론에서 메모리를 절약한다(예: `H_q=32, H_kv=8`이면 cache가 MHA의 1/4).
- "K/V가 Q와 다를 수 있다"는 두 가지 서로 다른 축의 이야기다 — ① Self vs Cross-Attention: **토큰 개수**(`L_query` vs `L_key`)가 다를 수 있음, ② MHA/MQA/GQA: **head 개수**(`H_q` vs `H_kv`)가 다를 수 있음. 두 축은 동시에 적용될 수 있다(`Q:[B,32,L_query,D_head]`, `K/V:[B,8,L_key,D_head]`).
- Shape trace 디버거는 `input → qkv → split → scores → merged` 각 단계의 기대 shape를 미리 계산해두고, 실제 값과 처음 어긋나는 단계를 찾는다 — 오류가 마지막 matmul에서 발생하더라도 원인은 그 앞의 head 분리일 수 있기 때문이다.

## Questions and Newly Learned Points

- `torch.matmul`과 `@`는 완전히 동일하며, 3차원 이상(배치 포함) 입력에서는 앞쪽 배치 차원을 유지한 채 마지막 두 차원끼리만 행렬곱한다.
- `d_k`와 `D_head`는 논문/강의 표기만 다를 뿐 같은 개념이다.
- `numel()`(원소 총 개수)과 `size(0)`(0번째 축의 크기)은 다른 값을 가리킨다 — `size(0)`의 "0"은 값이 아니라 "몇 번째 축을 볼지"를 가리키는 인덱스다.
- `sum(dim=0)`은 "가로로 더한다"가 아니라 "0번째 축(행)을 없앨 때까지 여러 행을 세로로 합친다"는 뜻이다. `dim=1`이 오히려 한 행 안에서 가로로 더하는 연산에 해당한다.
- `X.size(-1)`은 입력 `[B, L, D_model]`의 마지막 차원(`D_model`)을 가리키며, projection 가능 여부 검증이나 스케일링 계수 계산에 쓰인다.
- Self-Attention에서는 입력 `X`가 하나이고 `W_q`/`W_k`/`W_v`가 서로 달라 Q/K/V가 달라지는 것이지, `X` 자체가 세 개로 나뉘는 것이 아니다(`X_query`, `X_key`로 나누는 것은 Cross-Attention의 별도 예시).

## Environment

```bash
pip install -r requirements.txt
```
