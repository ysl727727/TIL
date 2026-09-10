# Chapter 1: Logits, Loss Functions, and Optimizers

> 2026-09-10 학습 기록. 1장(1-1, 1-2강)과 2장(2-1, 2-2강) 이론을 정리했습니다. 아래 Core Theory는 `1장__2장_Logits부터_Optimizer까지_-_딥러닝_학습의_기본기.pdf`를 기반으로 합니다. "딥러닝 실전 & 프롬프트 엔지니어링" 정리자료로, `deep-learning-advanced`의 KANT 강의 번호 체계와는 별개의 자료입니다.

## Learning Goals

- logit(클래스별 원시 점수)과 probability(정규화된 확률)를 구분하고, softmax가 지수화+정규화로 합이 1인 분포를 만드는 과정을 설명한다.
- 큰 logits에서 `exp()`가 overflow(`inf`/`nan`)를 일으키는 이유를 확인하고, max trick으로 수치 안정성을 확보한 stable softmax/log-softmax를 구현한다.
- 문제 유형(회귀/이진 분류/다중 분류)에 따라 MSE/BCE/Cross Entropy 중 어떤 손실 함수를 쓸지 판단하고 각각을 NumPy로 구현한다.
- Gradient Descent 갱신식 `θ ← θ − η·∇L`을 해석하고, `y = wx + b` 선형 모델을 NumPy로 직접 학습시킨다.
- learning rate가 너무 작거나 클 때 각각 어떤 현상(느린 수렴, 진동/발산)이 나타나는지 비교한다.
- SGD/Momentum/Adam이 각각 어떤 정보(현재 gradient만 / velocity / 1차·2차 모멘트)를 기억하는지 구분하고, 같은 문제에서 loss curve로 비교한다.

## Practice Files

| Lesson | File | Practice status |
| --- | --- | --- |
| 1장 통합 | `01-logits-loss-diagnosis-starter.ipynb` | **미완료** — TODO 1(stable softmax/log-softmax), TODO 2(문의별 CE/MSE/BCE), TODO 3(예측·정답·평균·최대 CE 문의 찾기)이 모두 `NotImplementedError`로 남아 있는 시작 템플릿 상태 |

이 노트북은 사내 LLM 출력 화면(담당 부서 분류=CE, 답변 품질=MSE, 민감정보 여부=BCE)을 소재로 세 손실 함수를 한 번에 다루는 통합 실습입니다. 현재는 TODO가 채워지지 않아 실행하면 오류가 발생하는 상태이며, 주말(2026-09-12~13)에 완성해 재업로드할 예정입니다.

## Core Theory

### 1. Logit과 Softmax (1-1강)

- logit은 모델의 마지막 선형층이 출력하는 클래스별 원시 점수다. 음수가 가능하고 합이 1이 아니므로 아직 확률이 아니다. 흐름: `입력 → 마지막 선형층 → logits → softmax → probability(합 1인 분포) → 정답과 비교 → loss`.
- Softmax 계산: ① 각 logit에 `exp()` 적용 ② 지수값의 합을 구함 ③ 각 값을 합으로 나눔. `softmax(z_i) = e^(z_i) / Σⱼ e^(z_j)`.
- 큰 logits(`[1000, 1001, 1002]`)에서는 `exp()`가 `inf`가 되고 `inf/inf`가 `nan`이 되어 계산이 붕괴한다. Softmax는 모든 값에 같은 상수를 더하거나 빼도 결과가 같으므로(분자·분모에 같은 배수가 생겨 약분됨), 각 행의 최댓값을 빼는 max trick(`shifted = x - max(x)`)으로 가장 큰 지수값이 `exp(0)=1`이 되어 overflow를 피한다 — 상대적 차이는 유지되므로 결과는 바뀌지 않는다.
- 배치 입력(`[B, C]`)에서는 클래스가 마지막 축이므로 `axis=-1`로 계산해야 하며, `keepdims=True`로 최댓값·합계의 차원을 유지해야 원본과 broadcasting이 안전하다. `axis=0`으로 계산하면 코드는 실행되지만 "각 클래스의 배치 방향 합이 1"이 되어 의도와 다른 값이 나온다.
- Log-softmax는 `softmax` 후 `log`를 취하는 대신 `shifted - log(Σexp(shifted))`로 안정적인 형태로 한 번에 계산한다(`stable_log_softmax`). Cross Entropy는 다음 강의에서 이 log-probability에 마이너스를 붙여 만든다.
- 실제 프레임워크의 `CrossEntropyLoss`/`BCEWithLogitsLoss`는 logits를 직접 받아 내부적으로 수치 안정적인 계산을 수행하므로, 학습 시에는 사용자가 미리 softmax를 적용하지 않는 것이 일반적이다(추론 시에는 `softmax` 또는 `argmax`로 확률/클래스를 해석).

### 2. MSE / BCE / Cross Entropy (1-2강)

먼저 확인할 두 가지: ① 모델 출력이 값 하나인지 클래스별 점수인지 ② 정답이 실수인지 0/1인지 클래스 번호인지.

| 문제 유형 | 모델 출력 예 | 정답 예 | 대표 손실 |
| --- | --- | --- | --- |
| 회귀 | 실수 하나(23.7) | 24.0 | MSE |
| 이진 분류 | logit 또는 확률 하나 | 0 또는 1 | BCE |
| 다중 분류 | 클래스별 logits | 클래스 인덱스 | Cross Entropy |

- MSE = `(1/N) Σ(ŷ-y)²`. 오차를 제곱하므로 양수/음수가 상쇄되지 않고, 큰 오차에 더 큰 패널티가 붙는다(오차 2 → 제곱오차 4, 오차 4 → 제곱오차 16).
- BCE = `−[y·log(p) + (1−y)·log(1−p)]`. 정답이 1이면 `log(p)`가, 0이면 `log(1-p)`가 중요해진다. `log(0)`은 정의되지 않으므로 `np.clip(p, eps, 1-eps)`로 확률을 아주 작은 양수와 1보다 살짝 작은 값 사이로 제한해야 한다 — clip은 수치 처리일 뿐 틀린 예측을 정답으로 바꾸는 것이 아니다.
- Cross Entropy는 정답 클래스의 log-probability에 마이너스를 붙인다: `L_i = −log p_(i, y_i)`. `log_probs[np.arange(B), targets]`처럼 행 번호와 정답 클래스 인덱스를 함께 사용해 정답 위치의 값만 뽑는다. 클래스 인덱스(정답 번호 하나)와 one-hot(클래스마다 0/1 벡터)은 같은 정보를 담지만 API가 기대하는 형식이 다르다.
- Reduction: 샘플별 loss(`none`, shape `[B]` 유지)를 먼저 만들고 `mean`(평균 하나) 또는 `sum`(합 하나)으로 줄인다. reduction 방식은 결과 표시뿐 아니라 gradient 크기에도 영향을 주므로 배치 크기와 함께 해석해야 한다.
- 손실 함수 선택에서 가장 흔한 오류는 값이 아니라 shape과 정답 표현에서 나온다 — MSE/BCE는 예측과 동일 shape, Cross Entropy는 logits `[B,C]`에 클래스 인덱스 정답 `[B]`가 짝을 이뤄야 한다.

### 3. Gradient Descent (2-1강)

- 학습 흐름: 입력 → 현재 파라미터로 예측 → 정답과 비교해 loss 계산 → loss의 gradient 계산 → 파라미터 갱신 → 반복.
- Gradient는 loss가 가장 빠르게 **증가**하는 방향이므로, loss를 줄이려면 반대 방향으로 이동해야 한다: `θ ← θ − η·∇L`(`η`=learning rate). 부호가 헷갈릴 때는 "gradient가 양수면 그 방향으로 갈수록 loss가 증가하니 반대(음의 방향)로 이동"으로 기억한다.
- 선형 모델(`ŷ = wx + b`)의 MSE gradient: `∂L/∂w = (2/N)Σ(ŷ-y)x`, `∂L/∂b = (2/N)Σ(ŷ-y)`. 코드에서는 `errors = y_pred - y_true` → `grad_w = 2*mean(errors*x)` → `grad_b = 2*mean(errors)` → `w -= lr*grad_w`, `b -= lr*grad_b` 순서로 이어진다.
- Learning rate: 너무 작으면 안정적이지만 매우 느리고, 적절하면 빠르고 안정적으로 수렴하며, 너무 크면 최솟값을 지나치며 진동하거나 발산(`nan`/`inf`)할 수 있다.
- PyTorch의 `optimizer.zero_grad() → y_hat = model(x) → loss = criterion(...) → loss.backward() → optimizer.step()`도 내부 흐름은 동일하다 — `backward()`가 gradient 계산을, `step()`이 파라미터 갱신을 대신한다.

### 4. SGD, Momentum, Adam (2-2강)

| Optimizer | 현재 gradient | 과거 방향 | gradient 크기 정보 | 추가 메모리 |
| --- | --- | --- | --- | --- |
| SGD | 사용 | 저장 안 함 | 저장 안 함 | 거의 없음 |
| Momentum | 사용 | velocity에 누적 | 직접 보정 안 함 | velocity 1개 |
| Adam | 사용 | 1차 모멘트 `m`에 누적 | 2차 모멘트 `v`에 누적 | `m`, `v` 2개 |

- SGD는 현재 step의 gradient만 그대로 사용한다(`parameter -= lr * gradient`). 구조가 단순하고 메모리가 적지만, 좁고 굽은 loss 지형에서 좌우로 흔들릴 수 있다.
- Momentum은 velocity `v_t = β·v_(t-1) + g_t`를 유지해 이전 방향의 관성을 반영한다(`θ_t = θ_(t-1) − η·v_t`). 같은 방향의 gradient가 반복되면 velocity가 누적되어 더 빠르게 진행하고, 방향이 바뀌어도 이전 관성이 일부 남아 급격히 꺾이지 않는다.
- Adam은 gradient의 1차 모멘트(방향의 이동 평균 `m`)와 2차 모멘트(크기 제곱의 이동 평균 `v`)를 함께 사용해 파라미터마다 이동량을 조절한다: `parameter -= lr * m_hat / (sqrt(v_hat) + eps)`. `m_hat`, `v_hat`은 초기값 0에서 시작한 이동평균이 0쪽으로 치우치는 편향을 보정한 값이다(`m/(1-β1^step)` 형태).
- optimizer 선택 기준: 단순하고 통제된 실험엔 SGD, 같은 방향 gradient가 반복되는 구간엔 Momentum, Transformer/LLM 등 빠른 baseline엔 Adam/AdamW가 흔히 쓰인다. optimizer만 바꾸고 learning rate를 그대로 두면 공정한 비교가 아닐 수 있다 — optimizer마다 적절한 learning rate 범위가 다르다.
- checkpoint에는 모델 가중치뿐 아니라 optimizer state(velocity, `m`, `v`)도 함께 저장해야 학습을 정확히 이어갈 수 있다.

### 5. 전체 흐름 (1~2장 통합)

```
logits → softmax(max trick) → probability
→ 손실 함수(MSE/BCE/CE)로 오차를 숫자 하나로 요약
→ gradient 계산(loss가 증가하는 방향)
→ θ ← θ − η∇L로 반대 방향 이동
→ optimizer(SGD/Momentum/Adam)로 gradient 활용 방식 선택
→ 반복 학습 → loss curve로 수렴 확인(발산/진동이면 learning rate·구현 점검)
```

모든 단계에서 shape과 axis(어느 축으로 합/평균을 내는지)를 확인하는 습관이 실수를 막는 핵심 기본기다.

## Environment

```bash
pip install -r requirements.txt
```
