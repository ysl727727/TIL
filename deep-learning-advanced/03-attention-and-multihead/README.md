# Chapter 3: Attention and Multi-Head Shape

> 2026-09-02 학습 기록. 3-1~3-3 이론을 정리했습니다. 아직 실습 노트북은 없고 이론만 정리된 상태입니다.

## Learning Goals

- Query·Key·Value가 입력에 서로 다른 학습된 projection을 곱해 만들어진다는 것을 이해하고, `Q=K=V=X`가 "값이 같다"가 아니라 "입력 출처가 같다"는 뜻임을 구분한다.
- Self-Attention과 Cross-Attention의 Q/K/V 출처 차이를 구분한다.
- `softmax(QKᵀ/√d_k + M)V` 수식의 연산 순서(scale → mask → softmax → weighted sum)를 정확히 따른다.
- `√d_k`로 나누는 이유와, mask를 반드시 softmax 이전에 적용해야 하는 이유를 설명한다.
- Padding mask와 Causal mask의 목적·shape 차이를 구분하고, 서로 다른 라이브러리의 boolean 의미 차이(True=사용 가능 vs True=차단)에 주의한다.
- Multi-Head Attention의 `split_heads`/`merge_heads` 축 변환과, `transpose` 뒤 `contiguous()`가 필요한 이유를 설명한다.
- `W_O`가 head 간 정보를 실제로 섞어주는 역할을 한다는 것을 이해한다.

## Practice Files

아직 실습 노트북이 없습니다. 아래 Core Theory는 `260902_3강_총정리_상세.md` 정리 내용을 기반으로 합니다. 3-1~3-3 기본·심화 실습은 추후 진행 예정입니다.

## Core Theory

### 1. Query · Key · Value (3-1강)

- Query(Q): 지금 찾는 정보 / Key(K): 각 위치가 가진 정보를 비교할 표지 / Value(V): 최종적으로 섞어 가져올 내용.
- Q/K/V는 고정된 의미 벡터가 아니라 입력 `X`에 서로 다른 학습된 projection(`W_Q`, `W_K`, `W_V`)을 곱해 만든 결과물이다. `Q=K=V=X`는 입력 출처가 같다는 뜻이지 값이 같다는 뜻이 아니다.

```python
Q = X @ W_Q   # [B, L, d_k]
K = X @ W_K   # [B, L, d_k]
V = X @ W_V   # [B, L, d_v]
scores = Q @ K.transpose(-2, -1)   # [B, L_q, L_k]
```

- `d_k`와 `d_v`는 같을 필요가 없다 — Q, K는 서로 내적으로 비교해야 해서 차원이 같아야 하지만, V는 마지막에 가중합될 뿐이라 차원이 달라도 된다.
- Self-Attention은 Q/K/V가 모두 같은 sequence에서 나오고(보통 `L_q = L_k`), Cross-Attention은 Q가 decoder 상태, K/V가 encoder 출력에서 나온다(`L_q ≠ L_k`일 수 있음).
- `QKᵀ` raw score는 아직 확률이 아니다 — 음수가 가능하고 행 합이 1일 필요가 없다.
- Parameter(`W_Q`, `W_K`, `W_V`)는 문장 길이와 무관하게 크기가 고정되지만, Activation(Q, K, V, scores)은 입력마다 새로 계산되며 문장 길이에 따라 크기가 변한다. 같은 feature 계약이면 길이가 다른 입력(32, 128)에도 같은 projection을 그대로 적용할 수 있다.

### 2. Scaled Dot-Product Attention과 Mask (3-2강)

연산 순서는 항상 고정된다:

```text
Attention(Q,K,V) = softmax( QKᵀ/√d_k + M ) V

1) Q @ Kᵀ       → score [B, L_q, L_k]
2) / √d_k       → scaled score
3) mask 적용    → 사용할 수 없는 key를 -inf로
4) softmax(-1)  → weight, 각 query 행 합 1
5) weight @ V   → context [B, L_q, d_v]
```

- `√d_k`로 나누는 이유: `d_k`가 커지면 dot product의 분산이 커져 softmax가 한쪽으로 쏠리고(포화) gradient가 작아질 수 있다 — sequence 길이나 `d_v`가 아니라 반드시 `d_k`로 나눈다.
- Mask는 반드시 softmax 이전에 적용해야 한다. softmax를 먼저 하고 마스크를 0으로 곱하면(post-hoc) 이미 합이 1이던 확률에서 일부를 0으로 만들어 행 합이 1보다 작아진다. 반대로 `-inf`를 먼저 넣고 softmax를 하면 `e^(-inf)=0`이 되고 나머지가 자동으로 재분배되어 합이 정확히 1이 된다.
- Padding mask(`[B, L_k]`, 샘플마다 다름)는 PAD 위치를 차단하고, Causal mask(`[L_q, L_k]`, 길이만 정해지면 항상 동일)는 현재 query보다 미래인 key를 차단한다. Causal keep mask는 `torch.tril()`로 만드는 하삼각 행렬이다.
- 두 mask는 `causal_keep[None,:,:] & padding_keep[:,None,:]`처럼 broadcasting으로 결합한다.
- 라이브러리마다 boolean의 의미가 다르다 — 이 강의의 교육용 mask는 True=사용 가능이지만, PyTorch `nn.MultiheadAttention`의 `key_padding_mask`는 True=차단(반대)이다. 이름과 문서를 항상 확인해야 한다.
- 한 query 행의 score가 전부 `-inf`이면 `softmax`가 `0/0`이 되어 NaN이 발생할 수 있다 — 전처리 단계에서 각 샘플에 최소 한 개 유효 token이 있는지 검증해야 한다.

### 3. Self-Attention 구현과 Multi-Head Shape (3-3강)

- 함수 계약: `q [B, L_q, d_k]`, `k [B, L_k, d_k]`, `v [B, L_k, d_v]`, `key_keep_mask [B, L_k]`(bool, True=사용) → `context [B, L_q, d_v]`, `weights [B, L_q, L_k]`.
- Multi-Head는 한 번의 Attention으로는 한 가지 관점만 볼 수 있는 한계를 해결하기 위해 `D_model`을 `H`개의 head로 나눠 병렬로 attention을 계산한다.
- `H`(head 개수)와 `D_head`(head 하나의 차원)는 `D_model = H × D_head` 관계를 가지며 `D_model % H == 0`이어야 한다.

축 변환 전체 흐름:

```text
[B, L, D_model]
→ view       [B, L, H, D_head]      (split)
→ transpose  [B, H, L, D_head]
→ (head별로 독립적으로 Attention 계산)
→ transpose  [B, L, H, D_head]
→ reshape    [B, L, D_model]        (merge)
→ W_O 통과   [B, L, D_model]
```

```python
def split_heads(x, num_heads):
    batch, length, d_model = x.shape
    d_head = d_model // num_heads
    return x.reshape(batch, length, num_heads, d_head).transpose(1, 2)

def merge_heads(x):
    batch, heads, length, d_head = x.shape
    return x.transpose(1, 2).contiguous().reshape(batch, length, heads * d_head)
```

- `transpose`는 실제 메모리를 옮기지 않고 "읽는 순서표"만 바꾸는 연산이라, 그 직후 바로 `reshape`/`view`를 하면 stride 오류나 잘못된 결과가 나올 수 있다. `contiguous()`는 순서표대로 메모리를 실제로 재정렬해 그 뒤의 `reshape`를 안전하게 만든다.
- Head가 있을 때 score shape는 `[B, H, L_q, L_k]`이다. Mask 내용(PAD 여부, 미래 여부)은 head와 무관하므로 하나만 만들고 broadcasting으로 재사용한다.
- Broadcasting은 행렬곱과 다른 규칙이다 — 두 텐서의 shape가 완전히 같을 필요 없이 각 축이 "같거나 하나가 1"이면 계산할 수 있다. 반면 행렬곱은 안쪽 차원이 정확히 같아야 하는 엄격한 규칙을 따른다.
- `W_O`는 Multi-Head를 쓸 때만 필요하다. Concat만으로는 head끼리 정보가 섞이지 않는다 — `W_O`(행렬곱)를 곱해야 각 출력 값이 모든 head의 정보를 어느 정도씩 섞어 계산된 새로운 값이 된다. Head가 1개(Single-Head)라면 섞을 대상이 없으므로 `W_O` 없이 context가 곧 최종 결과다.
- PyTorch 실전 API: `torch.nn.MultiheadAttention(embed_dim, num_heads, batch_first=True)`에서 `x, x, x`를 넣으면 Self-Attention이고, `key_padding_mask`는 True=차단(교육용 keep_mask와 반대)이며, `average_attn_weights=False`를 꺼야 head별 weight를 각각 볼 수 있다(기본값은 head 평균).

### 4. 디버깅 체크리스트

1. `B, L_q, L_k, D_model, H, D_head` 값을 먼저 적는다.
2. Q/K 마지막 차원과 K/V 길이를 확인한다.
3. Split 뒤 `[B,H,L,D_head]`인지 확인한다.
4. Score가 `[B,H,L_q,L_k]`인지 확인한다.
5. Mask가 key 축을 제대로 차단하는지 작은 예제로 확인한다.
6. Weight 마지막 축 합이 1인지 확인한다.
7. 차단 weight가 0이고 context가 finite인지 확인한다.
8. Merge 뒤 원래 토큰 순서와 `D_model`이 복원되는지 확인한다.

## Environment

이 챕터는 아직 실습 코드가 없어 별도 `requirements.txt`를 두지 않았습니다. 실습을 추가하면 `torch`가 필요합니다.
