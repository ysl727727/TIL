# 10장. 내적과 행렬곱 — 행마다 내적 (보강 3주 2회차)

> 2026-11-17 학습 기록. Python 보강 3주 2회차 수업이에요. 1회차에서 NumPy 배열 · shape · axis · 브로드캐스팅을 했다면, 2회차는 **내적 하나로 길이 · 유사도 · 행렬곱 · 선형 예측까지 잇기**예요. 같은 날 파인튜닝 2장과 이어서, 모델 안의 계산(`W·x`)이 결국 "행마다 내적"이라는 걸 손으로 확인했어요.
>
> 오늘의 한 문장: 행렬곱은 결국 **"행마다 내적"**이고, 내적 하나만 제대로 이해하면 길이 · 유사도 · 선형 예측까지 전부 연결된다.

## 진행 상황

> 문제 파일을 직접 실행한 결과 기준이에요.

| 단계 | 문제 | 상태 |
|---|---|---|
| 기초 1 | `dot` 내적 | ✅ 통과 |
| 기초 2 | `norm` 벡터의 길이 | ✅ 통과 |
| 기초 3 | `result_shape` 곱의 모양 | ✅ 통과 |
| 응용 1 | `cosine_similarity` 코사인 유사도 | ✅ 통과 |
| 응용 2 | `mat_vec` 행렬 × 벡터 (`@` 없이) | ✅ 통과 |
| 응용 3 | `linear_predict` 선형 모델 예측 | ✅ 통과 |
| 심화 1 | `mat_mul` 행렬곱 직접 구현 | ⬜ 남음 |
| 심화 2 | `similarity_matrix` 유사도 행렬 | ⬜ 남음 |
| 심화 3 | `soft_lookup` | ⬜ 남음 |

## 큰 흐름

```text
내적 (a·b)
 ├─ 자기 자신과 내적 + 루트 → 길이 (norm)
 ├─ 내적 ÷ 길이들의 곱      → 코사인 유사도
 └─ 행마다 내적             → 행렬 × 벡터 → 선형 모델 예측 (X @ w + b)
```

---

## 기초 1. 내적 `dot(a, b)`
같은 자리끼리 곱해서 전부 더한다.

```python
def dot(a, b):
    a = np.array(a)
    b = np.array(b)
    return (a * b).sum()
```

- `a * b` 는 numpy에서 **칸끼리 곱** (element-wise)
- `.sum()` 으로 다 더하면 내적
- `[1,2,3]·[4,5,6] = 4 + 10 + 18 = 32`

## 기초 2. 벡터의 길이 `norm(a)`
자기 자신과의 내적에 루트 → `√(a·a)`

```python
def norm(a):
    a = np.array(a)
    return np.sqrt((a ** 2).sum())
```

- 순서가 중요: **제곱 → 더하기 → 루트**
- `np.sqrt(a ** 2).sum()` 은 "칸마다 루트 → 더하기"라서 절댓값의 합이 나옴 (틀림)

## 기초 3. 곱의 모양 `result_shape(s1, s2)`
`(m, n) @ (n, k) → (m, k)` — 안쪽 숫자가 같아야 곱할 수 있고, 바깥 숫자가 결과 모양.

```python
def result_shape(s1, s2):
    if s1[1] != s2[0]:
        return None
    return (s1[0], s2[1])
```

---

## 응용 1. 코사인 유사도 `cosine_similarity(a, b)`
`cos θ = (a·b) / (|a| × |b|)` — 방향이 얼마나 같은지 (-1 \~ 1)

```python
def cosine_similarity(a, b):
    a = np.array(a)
    b = np.array(b)
    return (a @ b) / (np.sqrt((a ** 2).sum()) * np.sqrt((b ** 2).sum()))
```

### 내가 틀렸던 부분 ⚠️
| 시도 | 문제 |
|---|---|
| `/ abs(a) * abs(b)` | `abs`는 칸마다 절댓값일 뿐, 벡터 길이가 아님 |
| `np.sqrt(a ** 2).sum()` | 루트를 **먼저** 씌움 → 절댓값의 합 |
| `x / (A) * (B)` | `(x / A) * B` 로 계산됨 → 분모는 **한 괄호로** `x / (A * B)` |

> 괄호를 늘리는 게 아니라 **괄호의 위치**가 계산 순서를 바꾼다.

## 응용 2. 행렬 × 벡터 `mat_vec(A, x)` (@ 없이)
A의 **각 행과 x를 내적**해서 모은다.

```python
def mat_vec(A, x):
    A = np.asarray(A, dtype=float)
    x = np.asarray(x, dtype=float)
    out = []
    for row in A:                     # 2차원 배열을 for로 돌리면 한 행씩
        out.append((row * x).sum())   # 행 · x = 숫자 하나
    return np.array(out)              # 리스트 → 배열 (.shape 쓰려면 필요)
```

- 예: 학생별 [중간, 기말] 점수 `A`, 반영 비율 `x = [0.4, 0.6]` → 학생별 최종 점수 `[86, 84, 78]`
- x의 길이 = A의 열 개수
- 반복문 없이: `(A * x).sum(axis=1)` (브로드캐스팅 + 행마다 합)

### 매개변수 개념 정리
`def mat_vec(A, x)` 의 A, x는 **이름표**일 뿐, 값은 **호출할 때** 정해진다.
`mat_vec(A, [1, 1])` → 함수 안에서 x = [1, 1]. 수학의 `f(x) = 2x` 와 같은 것.

## 응용 3. 선형 모델 예측 `linear_predict(X, w, b)`
데이터마다 `x · w + b` → 행렬로 한 번에 `X @ w + b`

```python
def linear_predict(X, w, b):
    X = np.asarray(X, dtype=float)
    w = np.asarray(w, dtype=float)
    return X @ w + b
```

- `X @ w` 가 응용 2의 mat\_vec 그 자체
- `+ b` 는 브로드캐스팅으로 모든 칸에 더해짐
- 모양: `(5, 3) @ (3,) → (5,)`

---

## 이어지는 부분
- 파인튜닝에서 모델의 한 층은 `출력 = W·x`(4장 LoRA는 `W·x + B·A·x`) — 응용 2 · 3의 "행마다 내적"이 그대로 커진 것.
- 코사인 유사도는 RAG 4장 임베딩 Dense 검색 점수와 같은 계산.

## 다음 할 것
- 심화 1 \~ 3 (행렬곱 직접 구현, 유사도 행렬, soft lookup)
