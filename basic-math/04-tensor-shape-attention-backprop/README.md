# 5~7장. 텐서 shape · Attention 수식과 Softmax · 미분과 역전파

> 2026-08-10 학습 기록. 기초 수학 마지막 날 수업입니다. 텐서의 축(배치·시퀀스·특징)을 읽고 reshape·transpose·broadcasting의 shape을 추론하는 법(5장), Attention score `QKᵀ/√d_k`와 Softmax·Cross Entropy(6장), 미분·체인룰과 역전파의 직관(7장)을 다뤘습니다. 실습은 사내 IT 헬프데스크 문의 "사내 비밀번호 재설정 방법"으로 Attention을 진단하는 6-1을 했습니다.

## 학습 목표

- rank(축 개수)와 shape을 구분하고 `[B, T, D]`처럼 축 이름을 붙여 연산마다 shape을 추적한다.
- `Q = XW_Q`, `K = XW_K`, `QKᵀ`, `√d_k` scaling의 shape과 의미를 설명한다.
- 3차원 배치 텐서에서 `.T`가 아니라 **마지막 두 축만** 바꿔야 하는 이유를 안다.
- logit → softmax → 확률 → cross entropy 흐름과 log-sum-exp 안정화를 설명한다.
- 미분·편미분·그래디언트와 경사하강법, 체인룰로 기울기가 뒤로 전달되는 원리를 안다.

## 실습 파일

| 강 | 주제 | 실습 상태 |
| --- | --- | --- |
| 5-1 · 5-2 | 텐서 shape 표기, reshape·transpose·broadcasting, matmul shape 추론 | 📘 이론 |
| 6-1 | Attention score — 내적과 `QKᵀ` shape | ✅ 필수 1-1 실행 · 필수 2-1 함수 작성 · 심화 미완 |
| 6-2 | Softmax · 로그확률 · Cross Entropy | 📘 이론 |
| 7-1 · 7-2 | 미분·Gradient·경사하강법, Chain Rule과 Backpropagation | 📘 이론 |

## 전체 흐름

```text
X (L, D)  ── @W_Q ──> Q (L, d_k)
          ── @W_K ──> K (L, d_k)       QKᵀ (L, L)  ── /√d_k ── softmax(행마다) ──> 가중치
          ── @W_V ──> V (L, d_v)                                                  │
                                                         가중치 @ V ──> 출력 (L, d_v)
배치면 (B, L, D) → QKᵀ 대신 Q @ swapaxes(K, -1, -2) → (B, L, L)

분류: logits → softmax → 확률 → −log p(정답) = Cross Entropy → 미분 → 경사하강법
역전파: dL/dw = dL/dz · dz/dw (체인룰을 뒤에서부터 곱해 감)
```

## 핵심 이론

### 1. 텐서 shape (5장)

- 스칼라 0축, 벡터 1축, 행렬 2축, 그 이상은 텐서. 딥러닝은 보통 `[B(배치), T(시퀀스), D(특징)]`, 이미지는 `[B, C, H, W]`.
- **reshape**는 원소 순서를 그대로 두고 모양만 바꾸고, **transpose**는 축 순서를 바꿔요. 다른 연산이라 섞어 쓰면 값이 뒤섞여요.
- broadcasting: 뒤쪽 축부터 비교해서 같거나 한쪽이 1이면 늘려서 계산.
- matmul은 마지막 두 축끼리 곱하고 앞쪽 축(배치)은 그대로: `(B, T, d)(B, d, T) = (B, T, T)`.
- 연산 옆에 입력·출력 shape을 주석으로 적는 습관이 디버깅의 절반.

### 2. Attention score (6-1)

```text
Q = X W_Q,  K = X W_K,  V = X W_V
score = Q Kᵀ / √d_k          (L, L): 행 = Query 위치, 열 = Key 위치
weight = softmax(score, 행마다)
out = weight V
```

- `QKᵀ`의 (i, j) = i번째 토큰이 j번째 토큰을 얼마나 참고할지의 원점수(내적).
- `√d_k`로 나누면 점수의 퍼짐(표준편차)이 줄어서 softmax가 한 곳에 쏠리지 않아요.
- 자기 자신을 빼고 가장 많이 참고하는 토큰을 볼 땐, 복사본에서 자기 위치를 `-inf`로 바꾼 뒤 `argmax`.

### 3. Softmax · Cross Entropy (6-2)

```text
softmax(zᵢ) = e^{zᵢ} / Σ e^{zⱼ}
안정화: z − max(z)를 먼저 빼도 결과가 같다 (log-sum-exp)
CE = −log p(정답 클래스)
```

- logit은 확률이 아니에요(음수 가능, 합이 1 아님). softmax를 거쳐야 확률.
- 라이브러리의 CE는 logits를 바로 받아 내부에서 log-softmax를 안정적으로 계산해요 → softmax를 미리 두 번 적용하지 않기(딥러닝 기초 4장, LLM 실전 1장으로 이어짐).

### 4. 미분 · 체인룰 · 역전파 (7장)

```text
경사하강법: θ ← θ − η ∇L
체인룰:     dL/dx = dL/dy · dy/dx
```

- 그래디언트는 손실이 가장 빨리 **커지는** 방향이라 반대로 이동해요.
- 순전파 때 중간값을 저장해 두고, 역전파 때 뒤에서부터 local gradient를 곱해 각 파라미터의 기울기를 구해요. Autograd가 이 계산을 대신해요(딥러닝 기초 6장).

## 내가 작성한 코드

### 6-1 필수 1 · "재설정"은 무엇을 참고하나

```python
def build_attention_diagnostics(X, W_Q, W_K, tokens, query_index):
    Q = X @ W_Q                        # (5, 3)
    K = X @ W_K                        # (5, 3)
    raw_scores = Q @ K.T               # (5, 5)
    d_k = Q.shape[-1]
    scaled_scores = raw_scores / np.sqrt(d_k)
    query_scores = scaled_scores[query_index]
    ranking = np.argsort(query_scores)[::-1]
    non_self_scores = query_scores.copy()          # 원본은 그대로 두고
    non_self_scores[query_index] = -np.inf         # 자기 자신만 제외
    top_key_index = np.argmax(non_self_scores)
    return {...}
```

```text
rank | key_index | key_token | raw_score | scaled_score
0    | 3         | 재설정    | 1.6088    | 0.9288
1    | 2         | 비밀번호  | 1.0904    | 0.6295   ← 자기 자신 제외 1위
2    | 4         | 방법      | 0.9328    | 0.5386
Scaling 전 표준편차 0.3773 → 후 0.2178
```

### 6-1 필수 2 · 배치에서 `.T`를 쓰면 안 되는 이유

```python
def build_batch_attention_scores(X_batch, W_Q, W_K):   # X_batch (2, 5, 4)
    Q_batch = X_batch @ W_Q                             # (2, 5, 3)
    K_batch = X_batch @ W_K                             # (2, 5, 3)
    K_batch_T = np.swapaxes(K_batch, -1, -2)            # (2, 3, 5)  마지막 두 축만
    raw_scores_batch = Q_batch @ K_batch_T              # (2, 5, 5)
    return raw_scores_batch / np.sqrt(Q_batch.shape[-1])
```

## 질문과 새로 알게 된 점

- **3차원 배열의 `.T`는 모든 축 순서를 뒤집어요.** `(2, 5, 3).T`는 `(3, 5, 2)`가 돼서 배치 축이 망가져요. 배치 축은 두고 마지막 두 축만 바꾸려면 `np.swapaxes(K, -1, -2)`(PyTorch는 `K.transpose(-2, -1)`).
- 자기 자신을 제외할 때 원본 배열을 바꾸면 이후 순위표가 틀어져요 → `copy()` 후 `-inf`.
- scaling은 순위를 바꾸지 않아요(모두 같은 수로 나눔). 바뀌는 건 점수의 **퍼짐**이고, 그래서 softmax 결과가 덜 뾰족해져요.
- 이날 배운 Attention은 9월 딥러닝 심화 3장(Multi-Head, mask)과 4강(Transformer 전체 구조)에서 그대로 확장됐어요.

## 확인 문제

### 4-Q1. 배치 전치 (6-1)

`K_batch: (B, L, d_k)`에서 `Q_batch @ K_batch.T`가 실패하는 이유는?

① `.T`는 2차원에서만 실행돼서 오류가 난다  
② 3차원에서 `.T`는 모든 축을 뒤집어 `(d_k, L, B)`가 되므로 배치 축이 어긋난다  
③ `Q_batch`가 정사각행렬이 아니어서  
④ `d_k`가 홀수라서

<details>
<summary>정답 보기</summary>

**②** — 마지막 두 축만 바꿔 `(B, d_k, L)`이 돼야 `(B, L, d_k) @ (B, d_k, L) = (B, L, L)`. `np.swapaxes(K, -1, -2)`를 써요.

</details>

### 4-Q2. √d_k scaling (6-1)

score를 `√d_k`로 나눴을 때 일어나는 일은?

① 토큰 간 순위가 바뀐다  
② 점수의 표준편차가 줄어 softmax가 한 토큰에 지나치게 쏠리는 것을 막는다  
③ 점수가 확률이 된다  
④ 자기 자신 점수가 0이 된다

<details>
<summary>정답 보기</summary>

**②** — 0.3773 → 0.2178. 모든 칸을 같은 수로 나누니 순위는 그대로이고, 확률이 되려면 softmax가 더 필요해요.

</details>

### 4-Q3. Cross Entropy (6-2)

3클래스 분류에서 정답 클래스의 softmax 확률이 0.8이면 CE 손실은?

① −log(0.8) ≈ 0.223  
② 0.8  
③ 1 − 0.8 = 0.2  
④ log(0.8)² 

<details>
<summary>정답 보기</summary>

**①** — CE = −log p(정답). 확률이 1에 가까울수록 손실은 0에 가까워지고, 정답 확률이 낮을수록 손실이 커져요.

</details>

### 4-Q4. 서술형 — 체인룰과 역전파 (7장)

`z = wx + b`, `L = z²`일 때 `x = 2, w = 3, b = 1`에서 `dL/dw`를 체인룰로 구하고, 역전파가 이 계산을 어떻게 일반화하는지 쓰세요.

<details>
<summary>예시 답안</summary>

z = 7. `dL/dz = 2z = 14`, `dz/dw = x = 2`이므로 `dL/dw = 14 × 2 = 28`. 역전파는 순전파 때 각 단계의 중간값(z 등)을 저장해 두고, 손실에서 시작해 뒤로 가며 각 단계의 local gradient를 곱해 모든 파라미터의 기울기를 한 번에 구해요. PyTorch의 `loss.backward()`가 이 일을 자동으로 하고, 결과가 각 파라미터의 `.grad`에 쌓여요(딥러닝 기초 6장).

</details>
