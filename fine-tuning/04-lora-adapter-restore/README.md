# 4장. LoRA 어댑터 학습과 모델 복원

> 2026-11-20 학습 기록. 파인튜닝 4일차 수업이에요. 3장은 가중치 4.94억 개를 **전부** 바꿨고, 4장은 **기반 가중치 W를 고정**하고 옆에 붙인 작은 행렬 A · B만 학습해요. 3장 결과 모델이 아니라 **같은 공개 기반 모델**에서 새로 시작하고, 데이터 · 답변 마스크 · 학습 조건은 3장과 똑같이 둔 채 **갱신 대상만** 바꿔서 비교해요. 학습한 어댑터는 몇 MB짜리 파일로 따로 저장하고, 다시 붙여 같은 답이 나오는지 · W에 합쳐도 같은 계산인지 확인해요.
>
> 4장의 한 문장: **W는 고정하고 변화량 (α/r)·BA만 배우고, 어댑터만 저장 · 복원 · 병합한 뒤, 조건을 맞춰 숫자와 원문을 함께 읽는다.**

## 큰 흐름

```text
[준비] torchao 제거 · transformers 5.22.2 · accelerate 1.15.0 · peft 0.21.2 → 재시작
       training_data.zip(2장) + sft_report.json(3장) 업로드 → 해시 · 모델 · 정밀도 대조
4-1 저랭크 업데이트  h = W·x + (α/r)·B·A·x,  W [출력, 입력] · A [r, 입력] · B [출력, r]
                     작은 예제: 두 경로의 합 [3, 0] = 병합한 (W + ΔW)·x [3, 0]
4-2 PEFT 학습        B = 0이면 첫 기울기는 B에만 → LoraConfig(r 8, α 16, q · v) → get_peft_model
                     학습 대상은 lora_ 이름뿐인지 검사 → 3장과 같은 TrainingArguments로 24갱신
4-3 저장 · 복원       save_pretrained → 어댑터만 몇 MB → 같은 기반 + PeftModel.from_pretrained
                     logits allclose · 원문 == → FP32 merge_and_unload로 병합 전후 수치 확인
4-4 같은 조건 비교    check_comparison_inputs → baseline · 전체 SFT · LoRA 원문 → dev 12 형식 검사
                     보강: lr 2e-5 → 2e-4, q · v → all-linear
      ↓
5장 QLoRA: 고정한 기반 가중치를 4비트로 양자화 + LoRA → lora_report.json과 비교
```

**3장 vs 4장 — 학습 목표는 같고 갱신 대상만 달라요**

| | 3장 전체 SFT | 4장 LoRA |
|---|---|---|
| 학습 목표 | SFT (답변 토큰 손실) | SFT (같은 손실) |
| 시작 모델 | 공개 기반 모델 | **같은** 공개 기반 모델 (3장 결과 아님) |
| optimizer가 갱신 | 기반 가중치 494,032,768개 | A · B만 (q · v: 540,672개 / all-linear: 4,399,104개) |
| 결과물 | `sft_model/` (약 1 GB) | `lora_adapter/` (2.1 MB / 17.6 MB) |

## 학습 목표
- LoRA 식 h = W·x + (α/r)·B·A·x에서 W · A · B의 모양, r과 α의 역할, 곱하는 순서를 설명한다.
- 한 선형층의 LoRA 파라미터 수 r × (입력 + 출력)을 계산하고 전체 SFT와 비교한다.
- B = 0에서 시작할 때 첫 기울기가 왜 B에만 가는지 손계산으로 확인한다.
- `LoraConfig` · `get_peft_model`로 어댑터를 붙이고, **LoRA만 학습 대상인지** 검사한다.
- 어댑터만 저장하고, 같은 기반 모델에 다시 붙여 **logits와 생성 원문**이 같은지 확인한다.
- `merge_and_unload`가 같은 계산이라는 것(수치)과 답변 품질(업무)을 구분한다.
- 비교 전에 데이터 · 학습 · 생성 조건을 대조하고, 한 가지만 바꾼 실험으로 원인을 찾는다.

## 실습 환경
- 노트북: `lora.ipynb` (33셀). 입력 파일 두 개: 2장 `training_data.zip`(SHA-256 `018a6120…`) + 3장 `sft_report.json`
- Colab **Tesla T4 GPU**. `%pip uninstall -y torchao`(Colab 기본 구버전 torchao가 PEFT와 충돌) → `transformers==5.22.2` · `accelerate==1.15.0` · `peft==0.21.2` → 런타임 재시작
- 내 환경: Python 3.13.16 · torch 2.14.1+cu130 · transformers 5.22.2 · peft 0.21.2 · accelerate 1.15.0 (torchao는 원래 없어서 `Skipping` 경고만)
- T4는 BF16 미지원 → `MODEL_DTYPE = torch.float32`. 노트북이 **3장 `sft_report.json`의 `weight_dtype`과 같은지** 검사하는데, 3장도 T4 · FP32로 돌려서 통과했어요
- 슬라이드 숫자는 강사 PC(RTX 5060 Laptop · BF16) 기준이라 시간 · 메모리 · 손실이 내 실행과 달라요

## 실습 파일

| 파일 | 하는 일 | 상태 |
|---|---|---|
| `lora.ipynb` | 4-1 작은 행렬 → 4-2 LoRA 24갱신 → 4-3 저장 · 복원 · 병합 → 4-4 비교 · 새 세션 복원 | ✅ Colab T4(FP32). 원본 설정(lr 2e-5 · q · v) 실행 후, **보강 설정(lr 2e-4 · all-linear)으로 다시 실행** |
| `sft_report.json` | 3장 baseline · 전체 SFT 원문 (비교 입력) | ✅ 3장에서 내려받아 업로드 |
| `lora_adapter/` · `lora_report.json` | 어댑터 가중치 · 설정 · 원문 기록 (5장 비교 입력) | ⏳ Colab에서 내려받아 보관 남음 |
| `finetuning_ch04_practice.ipynb` | 통합 실습 TODO 1\~8 (`lora_delta` · `LoraConfig` · 복원) | ⏳ TODO 1(rank 읽기)만 질문으로 정리, 실행 결과 미확인 |

---

## 핵심 이론

### 4-1. 저랭크 업데이트를 행렬로 이해하기

**SFT와 LoRA는 다른 축이에요.** SFT는 **무엇을 배우는지**(모범답안 토큰 손실), LoRA는 **어느 파라미터를 바꾸는지**에 관한 선택이에요. 같은 질문 · 근거 · 모범답안으로 SFT를 하면서 전체 가중치를 갱신할 수도 있고, LoRA 어댑터만 갱신할 수도 있어요. LoRA가 갱신 **대상**을 정하고, 학습 데이터와 손실이 갱신 **방향**을 정해요.

| 방식 | 학습 · 병합에서 바뀌는 값 | 추론 시 파라미터 구조 |
| --- | --- | --- |
| 전체 가중치 SFT | 기존 모델의 가중치 | 원래 모델과 같은 구조 |
| LoRA, 병합 전 | 대상 층마다 추가한 $A,B$ | 기존 모델 + 별도 어댑터 |
| LoRA, 병합 후 | $A,B$의 효과를 $W'$에 반영 | $W'$의 모양은 $W$와 같음 |

**식과 모양**

$$
h=Wx+\frac{\alpha}{r}B(Ax)=(W+\Delta W)x,\qquad \Delta W=\frac{\alpha}{r}BA
$$

- $x$는 **LoRA를 붙인 그 선형층에 도착한 입력 벡터**예요. 토큰 임베딩이 층을 지날 때마다 다시 계산되는데, 그중 이 층이 받는 표현 하나가 $x$. 같은 층에서는 **같은 $x$**가 W 경로와 LoRA 경로에 들어가요.
- 입력 차원 $n$, 출력 차원 $m$이면 $W$ $(m,n)$, $A$ $(r,n)$, $B$ $(m,r)$. **$r$은 어댑터 안의 중간 차원**이에요.
- 열벡터 기준으로 $A$를 먼저 적용해 $Ax$ $(r\times1)$, 거기에 $B$를 적용해 $(m\times1)$ → 그래서 $AB$가 아니라 **$BA$**예요.

$$
x\;(n\times1)\xrightarrow{\;A\;}Ax\;(r\times1)\xrightarrow{\;B\;}B(Ax)\;(m\times1)
$$

- $BA$는 $(m,n)$이라 $W$에 더할 수 있고, 각 열이 $B$의 $r$개 열의 조합이라 $\operatorname{rank}(\Delta W)\le r$. 이 상한은 **변화량 $\Delta W$**에 걸리는 거지 모델 전체의 rank를 바꾸는 게 아니에요.
- **W를 작은 A · B로 대체하는 게 아니에요.** W 옆에 변화량만 따로 배우는 옆길을 더하는 구조예요.
- 초기화: 원논문은 A를 Gaussian, **PEFT 기본은 Kaiming uniform**, 둘 다 **B = 0** → 학습 시작 시점의 출력은 원래 모델과 같아요.

**작은 숫자로 확인 (실제 Qwen 가중치 아님)**

```python
W = torch.tensor([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])   # (2, 3)
A = torch.tensor([[1.0, 0.0, -1.0]])                   # (1, 3)
B = torch.tensor([[0.5], [-0.5]])                      # (2, 1)
x = torch.tensor([2.0, 1.0, 1.0])
rank, alpha = 1, 2 #alpha는 보통 r의 2배.
delta_W = (alpha / rank) * (B @ A)
lora_output   = W @ x + (alpha / rank) * (B @ (A @ x))
merged_output = (W + delta_W) @ x
```

```text
W, A, B의 모양: (2, 3) (1, 3) (2, 1)
A @ x: [1.0]
기존 출력: [2.0, 1.0]
추가할 변화량: [1.0, -1.0]
LoRA 출력: [3.0, 0.0]
병합한 출력: [3.0, 0.0]
```

- **`A @ x`의 모양이 왜 맞나**: `x`는 shape `(3,)`인 1차원 텐서예요. 행렬 오른쪽의 1차원 텐서는 열벡터처럼 곱하고 끝의 크기 1 축을 뺀 결과가 나와요. `torch.tensor([[2., 1., 1.]])`처럼 만들면 `(1, 3)`이라 안쪽 차원 3 vs 1이 안 맞아요. 2차원 열벡터는 `[[2.], [1.], [1.]]`.

```python
A @ x               # (1, 3) @ (3,)   → (1,)  [1.]
B @ (A @ x)         # (2, 1) @ (1,)   → (2,)  [0.5, -0.5]
W @ x               # (2, 3) @ (3,)   → (2,)  [2., 1.]
A @ x.unsqueeze(-1) # (1, 3) @ (3, 1) → (1, 1)
```

- **마지막은 왜 `@`가 아니라 `+`인가**: LoRA 경로의 결과는 기존 출력에 **원소별로 더할 보정값**이에요. 배율 α/r = 2라 $[2,1]+2\cdot[0.5,-0.5]=[3,0]$. 두 1차원 출력을 `@`로 곱하면 내적이라 숫자 하나가 나와요.
- $(W+\Delta W)x = Wx+\Delta Wx$ → **학습할 땐 옆길로 따로, 배포할 땐 합쳐서 하나로.** 이게 4-3 병합의 근거예요.

**파라미터 수: 한 선형층 = r × (입력 + 출력)**

| 층 (한 블록) | W 모양 [출력, 입력] | W 원소 (고정) | LoRA r × (입력 + 출력) |
|---|---|---|---|
| `q_proj` | 896 × 896 | 802,816 | 8 × (896 + 896) = 14,336 |
| `v_proj` | 128 × 896 | 114,688 | 8 × (896 + 128) = 8,192 |
| 블록 합계 × 24 | | | 22,528 × 24 = **540,672** |

- `v_proj`는 출력이 **128**이라 q와 모양이 달라요(Qwen2.5는 K · V head가 적은 GQA 구조).
- 전체 494,573,440 = 기반 494,032,768(3장이 전부 학습한 수) + LoRA 540,672 → **0.11%**.
- 예: $W$가 $1000\times1000$이고 $r=8$이면 갱신하는 값이 100만 개에서 $8(1000+1000)=16{,}000$개로 줄어요.
- 기반 쪽은 `requires_grad=False`라 기울기 · AdamW 상태를 안 만들어서 메모리가 크게 줄어요.

### 4-2. PEFT로 LoRA 학습하기

**B = 0인데 왜 첫 갱신에서 B가 바뀌나 — 초기값과 기울기는 다른 값**

```python
A_small = torch.nn.Parameter(torch.tensor([[1.0, 0.0, -1.0]]))   # 손계산용으로 고정한 값
B_small = torch.nn.Parameter(torch.zeros(2, 1))                  # B = 0
target = torch.tensor([3.0, 0.0])
optimizer_small = torch.optim.SGD([A_small, B_small], lr=0.1)
prediction = W @ x + 2 * (B_small @ (A_small @ x))
loss_small = torch.nn.functional.mse_loss(prediction, target)
optimizer_small.zero_grad()  # 이전에 저장된 기울기 초기화
loss_small.backward()        # 현재 손실의 기울기를 .grad에 저장
optimizer_small.step()       # A와 B에 현재 값 - 0.1 × 기울기 적용
```

```text
초기 출력: [2.0, 1.0]
첫 A 기울기: [[0.0, 0.0, 0.0]]
첫 B 기울기: [[-2.0], [2.0]]
한 번 갱신한 출력: [2.4000000953674316, 0.6000000238418579]
작은 예제 손실: 1.0 -> 0.35999995470046997
```

- B = 0이면 옆길 출력이 0 → 시작 모델 = 원래 모델.
- A의 기울기는 **B를 곱해서** 거꾸로 오는데 B의 **값**이 0이라 A 기울기가 0이에요. 반대로 B의 기울기는 $Ax=1$을 곱해서 오니까 0이 아니에요.
- 그래서 A는 그대로, B는 $[0,0]^\top-0.1[-2,2]^\top=[0.2,-0.2]^\top$. 출력은 $[2,1]+2\cdot[0.2,-0.2]=[2.4,0.6]$, 손실 1.0 → 0.36.
- 한 번 갱신해서 B ≠ 0이 되면 **다음부터 A에도** 기울기가 가요. 작은 예제의 `step()`은 한 번, 실제 LoRA 실습은 **24번**.

**같은 데이터 · 같은 답변 마스크**: 3장 `encode_example`과 같은 방식(두 번 토큰화 → EOS까지 · labels −100). 배치 모양 (2, 370), 첫 예제 손실 토큰 **71개**. 노트북이 3장 `sft_report.json`의 `data_sha256`과 지금 ZIP 해시가 같은지, 모델 · revision · 정밀도가 같은지 먼저 확인해요.

**LoraConfig — 어디에, 얼마나 크게 붙일지**

```python
lora_config = LoraConfig(
    task_type="CAUSAL_LM",
    r=8,
    lora_alpha=16,
    target_modules=["q_proj", "v_proj"],    # 보강 실행에서는 "all-linear"
    lora_dropout=0.0,
    bias="none",
    init_lora_weights=True,
    base_model_name_or_path=MODEL_ID,
    revision=REVISION,
)
model = get_peft_model(base_model, lora_config)
```

| 파라미터 | 값 | 의미 |
|---|---|---|
| `task_type` | `CAUSAL_LM` | 다음 토큰 생성용 PEFT 구성 |
| `r` | 8 | A · B 중간 차원. 늘리면 학습 파라미터와 표현 범위가 늘지만 품질은 실험으로 확인 |
| `lora_alpha` | 16 | 배율 α/r = 2. r만 바꿔도 배율이 달라지니 둘을 따로 읽기 |
| `target_modules` | `q_proj`, `v_proj` | Attention의 query · value 투영층에만 |
| `lora_dropout` · `bias` | 0.0 · none | 옆길 dropout 끔, bias는 학습 안 함 |
| `init_lora_weights` | True | PEFT 기본 초기화 (A Kaiming uniform, B = 0) |

- 8과 16은 이 수업의 작은 비교 설정이지 최적값이 아니에요. 실무에선 r 8\~16, α = 2r, target은 all-linear로 시작하는 경우가 많지만 **dev로 확인**이 먼저.
- `r=8 → 16`으로 올리면서 `alpha=16 → 32`로 같이 올리면 배율 α/r = 2를 유지할 수 있어요.

**`q_proj` · `v_proj`에 붙인다는 뜻** — `proj`는 projection. Attention 안에서 입력 벡터를 목적에 맞는 벡터로 바꾸는 선형층이에요.

| 층 | 역할 | 원본 실습 |
| --- | --- | --- |
| `q_proj` | **Q(Query)**: 현재 토큰이 어떤 정보를 참고할지 판단하는 기준 | LoRA 적용 |
| `k_proj` | **K(Key)**: 각 토큰의 K를 현재 토큰의 Q와 비교해 참고 점수를 정함 | 기존 경로 |
| `v_proj` | **V(Value)**: 참고 비율에 따라 실제로 섞는 정보 | LoRA 적용 |
| `o_proj` | 여러 head에서 모은 정보를 합친 뒤 출력 벡터로 변환 | 기존 경로 |

한 head 기준으로 $q_i$와 $k_j$를 비교해 점수를 구하고, softmax 가중치로 $v_j$를 섞어요(가중치가 0.8 · 0.2면 $0.8v_1+0.2v_2$). `target_modules=["q_proj", "v_proj"]`면 **각 블록의 q와 v에 별도의 $A,B$**가 붙어요(bias · 위치 처리 생략).

$$
q_i=W_qx_i+\frac{\alpha}{r}B_qA_qx_i,\qquad k_i=W_kx_i,\qquad v_i=W_vx_i+\frac{\alpha}{r}B_vA_vx_i
$$

**`target_modules`는 붙일 위치**, **`r`은 각 어댑터의 중간 차원**을 정해요. `all-linear`는 q · k · v · o · gate · up · down **7개 층 전부**.

**붙인 뒤 검사**

```python
model.print_trainable_parameters()
assert all("lora_" in name for name, value in model.named_parameters() if value.requires_grad)
first_lora = next(m for m in model.modules() if hasattr(m, "lora_A"))
frozen_reference = first_lora.base_layer.weight.detach().cpu().clone()     # 학습 뒤 W 그대로인지 비교용
assert torch.count_nonzero(first_lora.lora_B["default"].weight) == 0        # B = 0 확인
```

| 검사 | 언제 | 막는 사고 |
|---|---|---|
| 학습 대상 = `lora_` 이름뿐 | 붙인 직후 | 기반 가중치까지 학습 (사실상 전체 SFT) |
| B = 0 → 학습 뒤 B ≠ 0, W 그대로 | 학습 전 · 후 | 어댑터가 안 배웠거나 W가 바뀜 |

`get_peft_model`은 옆길을 **붙이기만** 해요. 호출만으로 학습이 끝난 게 아니에요.

**PEFT · LoRA · SFT는 답하는 질문이 달라요**

| 이름 | 답하는 질문 | 이 과정 |
|---|---|---|
| SFT | 모범답안으로 무엇을 예측하도록 배울까? | 3 · 4 · 5장의 학습 목표 |
| DPO | 두 응답의 선호를 어떻게 배울까? | 6장 |
| LoRA | 어떤 추가 파라미터만 학습할까? | 4장 |
| QLoRA | 고정 기반 가중치의 저장 비용을 어떻게 줄일까? | 5장 |
| PEFT 라이브러리 | 이런 구성을 어떤 도구로 적용할까? | `LoraConfig` · `get_peft_model` |

PEFT(Parameter-Efficient Fine-Tuning)는 적은 파라미터만 학습하는 방법들의 **묶음 이름**이자 Hugging Face **라이브러리 이름**이에요. LoRA는 그중 하나의 방법. **어댑터** = 기반 모델과 함께 쓰는 추가 학습 부분(A · B + 설정)이고 혼자서 언어 모델이 되지 않아요.

**학습 조건은 3장과 같게**: 배치 1 × 누적 4, `max_steps` 24(2 epoch), lr 2e-5, warmup 2 · linear, gradient checkpointing, eval · logging 4. 다른 건 `save_strategy="no"`(Trainer 자동 중간 저장만 끔, 어댑터는 4-3에서 직접 저장)와 **optimizer가 A · B만 갱신**한다는 것. 단, **lr 2e-5는 3장 전체 SFT 기준**이지 LoRA에 맞춘 값이 아니에요 → 4-4 보강에서 바꿔 봐요.

### 4-3. 어댑터 저장과 다시 불러오기

```python
adapter_path = Path("lora_adapter")
model.save_pretrained(adapter_path)                     # 어댑터 가중치 + 설정만
with torch.inference_mode():
    saved_logits = model(**probe_inputs).logits[0, -1].float().cpu()   # 마지막 위치 다음 토큰 점수 보관
del trainer, model, base_model, first_lora; gc.collect(); torch.cuda.empty_cache()

base_model = AutoModelForCausalLM.from_pretrained(MODEL_ID, revision=REVISION, dtype=MODEL_DTYPE, ...)
model = PeftModel.from_pretrained(base_model, adapter_path, is_trainable=False)
reloaded_logits = model(**probe_inputs).logits[0, -1].float().cpu()
assert torch.allclose(saved_logits, reloaded_logits, atol=1e-4, rtol=1e-4)
assert probe_reloaded["raw_response"] == probe_after["raw_response"]
```

| 함수 | 하는 일 | 확인 |
|---|---|---|
| `model.save_pretrained` | `adapter_model.safetensors`(A · B) + `adapter_config.json`(설정 · 기반 모델 ID · revision) + README | 기반 모델은 중복 저장 안 함 |
| `PeftModel.from_pretrained(..., is_trainable=False)` | 같은 기반 모델에 어댑터를 **추론용**으로 연결 (이어 학습하면 True) | 모델 ID · revision · 토크나이저 · dtype 맞추기 |
| `merge_and_unload()` | 변화량을 W에 합친 모델 반환 | 병합 전후 수치 오차 |

- **저장 · 복원**은 학습한 어댑터를 다시 연결해서 같은 계산을 재현하는 과정이에요. `saved_logits`는 학습을 마친 모델의 다음 토큰 점수, `reloaded_logits`는 다시 붙인 어댑터로 같은 입력을 계산한 점수. **수치는 `allclose`로, 생성 원문은 `==`로** 따로 확인해요.
- 기반 모델 ID · revision이 다르면 어댑터가 **다른 W 위에** 더해져 의미 없는 출력이 나와요. 그래서 `adapter_config.json`의 `base_model_name_or_path` · `revision`부터 assert.

**`torch.allclose(a, b, atol, rtol)`**: 각 원소에서 $|a-b|\le\mathrm{atol}+\mathrm{rtol}\cdot|b|$. `atol`은 0 근처에서도 허용하는 절대 오차, `rtol`은 두 번째 인자 $b$의 크기에 비례하는 상대 오차. 둘 다 0.01이면 $b=0$에서 허용 0.01, $b=100$에서 1.01. (여기 소문자 $a,b$는 비교값이고 LoRA의 대문자 $A,B$와 다른 것) **허용 오차는 업무 답의 오답을 허용한다는 뜻이 아니에요.**

**병합 — `merge_and_unload(safe_merge=True)`**

```python
model = model.float()                                   # 반올림 오차를 작게 보려고 FP32에서 비교
before_merge = model(**probe_inputs).logits[0, -1]
merged_model = model.merge_and_unload(safe_merge=True) # W' = W + ΔW, 옆길 제거 (safe_merge: NaN 검사)
after_merge = merged_model(**probe_inputs).logits[0, -1]
assert torch.allclose(before_merge, after_merge, atol=1e-4, rtol=1e-4)
```

| 배포 방식 | 장점 | 단점 |
|---|---|---|
| 기반 + 어댑터 (`PeftModel`) | 업무별 어댑터 교체, 저장 몇 MB | 추론 때 옆길 계산이 조금 더 |
| 병합 (`merge_and_unload`) | 일반 모델과 같은 속도, 서빙 도구 호환 | 어댑터마다 전체 모델 크기로 저장 |

병합 검사는 **계산이 같은지(수치)**를 보는 거지 **답의 품질**이 아니에요. 디스크에 저장한 어댑터 파일은 병합 뒤에도 다시 쓸 수 있어요.

### 4-4. 같은 조건에서 학습 결과 비교하기

```python
def check_comparison_inputs(sft_report, report, probe_after):
    for key in ["max_steps", "learning_rate", "gradient_accumulation_steps", "max_length", "seed"]:
        assert sft_report["config"][key] == report["config"][key]
    for key, value in GENERATION.items():
        assert sft_report["generation"][key] == value
    for old_probe in [sft_report["probe_before"], sft_report["probe_after"]]:
        assert old_probe["case_id"] == probe_after["case_id"]
        assert old_probe["messages"] == probe_after["messages"]
```

- 파일 · 모델(data\_sha256 · revision · dtype) → 학습 조건(steps · lr · 누적 · seed) → 생성 조건(GENERATION 전부) → 관찰 문항(case\_id · messages) 순으로 대조하고, **다르면 비교를 멈추고 원인부터** 찾아요.
- baseline 원문이 3장 `probe_before`와 **같은지**도 assert → 같은 모델 · 같은 입력에서 출발했다는 증거.
- `inspect_response`는 1장과 같은 원문 검사예요. **코드 펜스를 지워서 통과시키지 않아요**(서비스에서 파서가 실패하는 것과 같아서).

**슬라이드 결과 (RTX 5060 · BF16)**

| 실행 | 학습 파라미터 | dev loss | 형식 | 판단(보조) | 시간 · 메모리 |
|---|---|---|---|---|---|
| 3장 전체 SFT (lr 2e-5) | 494,032,768 | 0.0049 | 12/12 | 10/12 | 27초 · 4.66 GiB |
| 4장 원본 (2e-5 · q · v) | 540,672 | 0.8717 | **0/12** | 0/12 | 19초 · 1.61 GiB |
| ① lr 2e-4 · q · v | 540,672 | 0.4411 | 12/12 | 6/12 | 18초 · 1.61 GiB |
| ①+② lr 2e-4 · all-linear | 4,399,104 | 0.0184 | 12/12 | 10/12 | 27초 · 1.67 GiB |

- 원본은 dev loss가 0.92 → 0.87로 조금 줄었지만 관찰 문항 원문이 **학습 전과 글자까지 같아요.** 학습은 됐지만(W 그대로 · B ≠ 0) **24번 × 2e-5로는 행동을 바꿀 만큼 안 움직였어요.**
- lr만 2e-4: 형식은 배웠지만 답이 짧아지고, 통신비 질문에 "최대 500원까지 지원"처럼 **근거를 지어내요.**
- lr 2e-4 + all-linear: 전체 SFT와 같은 10/12를 **메모리 약 1/3**로. 남은 2개는 초과 금액 문항이고, 모든 금액에 "**한도와 같으므로**"라고 쓰는 버릇이 생겨요.
- 메모리 차이의 출처: SFT는 4.94억 개 전부의 기울기 + AdamW 상태 2개, LoRA는 54만 개분만. 작은 모델 · 24갱신에선 시간 차이가 크지 않지만 큰 모델일수록 메모리 차이가 결정적이에요.

**보강 실습에서 바꾸는 줄**

| 바꾼 줄 | 셀 | 영향 |
|---|---|---|
| ① `learning_rate=2e-5` → `2e-4` | TrainingArguments (4-2) | 형식 0/12 → 12/12 |
| ② `target_modules` → `"all-linear"` | LoraConfig (4-2) | 학습 파라미터 540,672 → 4,399,104 |
| ③ 병합 검사 `atol=1e-4` → `1e-3` | merge (4-3) | BF16에선 ① 후 오차 1.6e-4로 멈춤 |
| ④ report의 `config` | lora\_report 저장 (4-4) | 값을 직접 적은 줄이라 ① ②와 같이 고치기. 고치면 `check_comparison_inputs`의 learning\_rate 대조에서 멈추니 그 키만 목록에서 빼기 |

all-linear 4,399,104개 계산: 블록마다 q 14,336 + k 8,192 + v 8,192 + o 14,336 + gate · up · down 각 8 × (896 + 4,864) = 46,080 → 183,296 × 24 = **4,399,104**.

---

## 실행 결과 (내 실행 — Colab Tesla T4 · FP32)

**① 원본 설정 (lr 2e-5 · q · v)** — 내 메모 기준

- dev loss **0.9167 → 0.8466** (약 7.6% 감소). 슬라이드(BF16 0.9207 → 0.8717)처럼 조금만 줄었어요.
- 손실은 dev 모범답안 토큰을 얼마나 잘 예측했는지일 뿐이라, 생성 답의 형식 · 정확도는 dev 문항에서 따로 봐야 해요. 이 실행의 노트북 출력은 남기지 않아서 형식 개수는 기록이 없어요.

**② 보강 설정 (lr 2e-4 · all-linear)** — 내려받은 노트북 출력

| 단계 | 결과 |
|---|---|
| 데이터 | train/dev 48 / 12 · 관찰 문항 `policy01-over_limit` · 배치 (2, 370) · 첫 예제 손실 토큰 71 |
| 작은 예제 | [3, 0] = [3, 0] · 첫 A 기울기 0 · B 기울기 [−2, 2] · 손실 1.0 → 0.36 |
| 학습 대상 | trainable **4,399,104** / all 498,431,872 = **0.8826%** · 첫 W/A/B (896, 896) (8, 896) (896, 8) · 배율 2.0 |
| 학습 | 24갱신 **1분 29초** · dev loss **0.9167 → 0.0140** · 기반 W 그대로(`frozen_unchanged`) · B ≠ 0 |
| 저장 | `README.md` · `adapter_config.json` · `adapter_model.safetensors` **17,640,136 bytes** (4,399,104 × 4바이트 FP32 + 헤더) |
| 복원 | logits 최대 절대 오차 **0.0** · 응답 일치 **True** |
| 병합 (FP32) | 최대 절대 오차 **6.39e-05** (1e-4 안이라 ③ 안 바꿔도 통과) · 다음 토큰 ID 4913 = 4913 |
| 비교 | 형식 + 인용 ID: baseline **0/12** · 전체 SFT **12/12** · LoRA **12/12** |
| 새 세션 복원 셀 | 다시 읽은 응답 = 저장한 원문 **True** |

| 갱신 | train loss | dev loss |
|---|---|---|
| 0 | - | 0.9167 |
| 4 | 0.7766 | 0.4217 |
| 8 | 0.2727 | 0.1085 |
| 12 | 0.0687 | 0.0375 |
| 16 | 0.0249 | 0.0219 |
| 20 | 0.0245 | 0.0177 |
| 24 | 0.0204 | 0.0140 |

**같은 규정 계열 policy01 원문 비교** (모범답안과 비교)

| 문항 | baseline | 3장 전체 SFT (내 FP32) | 4장 LoRA (보강) |
|---|---|---|---|
| boundary 65,000 | ` ```json ` 펜스 + 규정 복사 | "한도와 같으므로 승인 불필요" ✅ | "한도와 같으므로 승인 불필요" ✅ |
| over\_limit 70,000 | 펜스 + 규정 복사 | "한도를 **초과하므로** 서면 승인" ✅ | "한도와 **같으므로** 서면 승인" — 결론은 맞고 이유가 틀림 |
| updated 70,000 (한도 75,000) | 펜스 + 규정 복사 | "한도 **이하**이므로 승인 불필요" ✅ | "한도와 **같으므로** 승인 불필요" — 결론은 맞고 이유가 틀림 |
| missing | `answered` 한 단어 | abstained + 담당자 확인 ✅ | abstained + 담당자 확인 ✅ |

- 형식 12/12인데도 **이유 문장이 틀려요.** 슬라이드에서 말한 "all-linear는 모든 금액에 '한도와 같으므로'라고 쓴다"는 버릇이 내 실행에서도 보였어요. 승인 필요 여부(결론)만 보는 간이 판단으로는 맞아 보여도 업무 문장으로는 오답이에요.
- dev 12문항 전체의 LoRA 원문은 `lora_report.json`의 `comparison`에 있어요(아직 안 내려받아서 policy01 네 문항만 확인).
- **고칠 점**: ① ②만 바꾸고 ④ report의 `config`(learning\_rate 2e-5 · target\_modules q · v)는 그대로라, 저장된 `lora_report.json`이 **실제 학습 설정과 달라요.** 그래서 `check_comparison_inputs`도 learning\_rate 대조를 통과해 버렸어요. 5장에서 이 보고서를 읽기 전에 config를 2e-4 · all-linear로 고치고, 비교 키에서 learning\_rate만 빼기.

## 질문과 새로 알게 된 점

### SFT와 LoRA는 어떻게 다른가
SFT는 **무엇을 배우는지**, LoRA는 **어느 파라미터를 바꾸는지**. 그래서 "SFT 목표를 LoRA로 학습한다"가 맞는 말이에요. PEFT는 이런 방법들의 범주이자 실습에서 쓴 라이브러리 이름이에요.

### $x$는 무엇이고, 왜 $AB$ 대신 $BA$인가
$x$는 LoRA를 붙인 그 선형층에 도착한 입력 벡터. 열벡터 기준으로 $A$ $(r,n)$를 먼저 곱해 $r$차원으로 줄이고, $B$ $(m,r)$로 출력 차원으로 되돌리니 $B(Ax)=BAx$. 가로 벡터로 쓰면 전치해서 $(BAx)^\top=x^\top A^\top B^\top$이고 $A^\top$ $(n,r)$, $B^\top$ $(r,m)$.

### PyTorch에서 `A @ x`의 shape는 왜 맞나
`x = torch.tensor([2., 1., 1.])`는 `(3,)` 1차원이라 열벡터처럼 곱해지고 결과에서 크기 1 축이 빠져요. `[[2., 1., 1.]]`로 만들면 `(1, 3)`이라 안 맞음.

### B가 0인데 왜 첫 갱신에서 B가 바뀌나
초기값과 기울기는 다른 값. B의 **값**이 0이라 A로 가는 기울기가 0이고, B의 **기울기**는 $Ax$가 0이 아니라서 [−2, 2]. 한 번 갱신하면 B ≠ 0이 되어 다음부터 A도 학습돼요.

### `q_proj`, `v_proj`에 붙인다는 게 무슨 뜻인가
Attention 안의 Query · Value를 만드는 선형층에 각각 별도의 A · B를 붙인다는 뜻. 일반식의 출력 $h$가 `q_proj`에선 $q$, `v_proj`에선 $v$. `target_modules`는 **위치**, `r`은 **각 어댑터의 중간 차원**.

### dev loss가 조금 줄었을 때 뭘 확인할까
원본 설정에서 0.9167 → 0.8466(약 7.6%)일 때 확인한 순서:
- **기준 실습 조건**: train 48 · dev 12, lr 2e-5, 24갱신, r 8 · α 16, 프롬프트와 패딩은 labels −100, test는 튜닝에 안 씀.
- **학습률 실험**: 같은 기반 모델에 **새 어댑터를 붙여 처음부터**, 24갱신 유지하고 2e-5 기준으로 5e-5 · 1e-4(슬라이드 보강은 2e-4)를 비교. 후보값이니 중간 dev loss와 생성 결과로 판단.
- **학습량 실험**: `training_history`에서 train · dev loss가 함께 내려가면 `max_steps=48`(약 네 바퀴) 비교. train만 내려가고 dev가 오르면 과적합 의심.
- **다른 선택지**: 오류 유형에 맞는 예제 보강, rank 올리기(`r 8 → 16`이면 `alpha 16 → 32`로 배율 유지), 붙이는 위치 넓히기(all-linear).
- 출력이 그럴듯해도 ` ```json ` 펜스가 있으면 `json.loads(raw)`가 실패해요. dev 12개에서 **순수 JSON · 금액 · 승인 조건 · 실제 근거 인용 · 근거 없을 때 보류**를 함께 보고, 형식이 맞아도 금액 · 인용은 근거와 대조.
- 학습률이나 갱신 횟수를 바꾼 실험은 **보고서의 설정값도 같이** 고쳐요(위 "고칠 점"). `check_comparison_inputs()`는 3장과 학습 조건이 같다고 가정하니 튜닝 실험은 기준 비교와 따로 기록.

### 저장 · 복원과 병합은 무엇을 검증하나
- **저장 · 복원**: 같은 기반 모델 ID · revision · 토크나이저 · 정밀도로 `PeftModel.from_pretrained(..., is_trainable=False)` → logits `allclose` + 원문 `==`. 같은 GPU · 같은 정밀도라 오차 0.0이었어요.
- **병합**: $W'=W+\Delta W$로 옆길을 없앤 모델. 파라미터 구성은 달라도 같은 입력의 출력 크기는 같아서, FP32에서 병합 전후 logits를 `allclose`로 비교하고 최고 점수 토큰 ID도 확인. **계산 재현 확인**이지 답변 품질 평가가 아니에요.

### 어댑터 크기는 왜 2.1 MB(슬라이드) vs 17.6 MB(내 실행)인가
학습한 A · B는 **FP32로 저장**돼요. q · v는 540,672 × 4바이트 = 2,162,688(+ 헤더 = 2,175,168), all-linear는 4,399,104 × 4 = 17,596,416(+ 헤더 = 17,640,136). 기반 모델(BF16 약 942 MB)은 넣지 않아요. 실무에서는 업무별 어댑터 여러 개를 **기반 모델 하나**에 바꿔 끼워요.

### 같은 조건 비교는 왜 한 가지만 다르게 하나
결과 차이가 무엇 때문인지 말하려면 다른 조건이 같아야 해요. 다만 "같은 lr 2e-5"처럼 **그 한 가지에 맞지 않는 조건이 섞였는지**도 봐야 해요. 2e-5는 전체 SFT 기준이라 LoRA가 안 움직인 거였어요.

## 실습 코드에서 직접 바꾼 점

원본 `lora.ipynb`와 셀 단위로 비교했어요. 코드는 보강 실습의 **두 줄만** 바꿨고, 나머지는 주석이에요.

**바꾼 코드**

| 셀 | 원본 | 바꾼 값 | 메모 |
|---|---|---|---|
| LoraConfig (4-2) | `target_modules=["q_proj", "v_proj"]` | `target_modules="all-linear"` | 보강 ② |
| TrainingArguments (4-2) | `learning_rate=2e-5` | `learning_rate=2e-4` | 보강 ① |
| 병합 검사 (4-3) | `atol=1e-4` | 그대로 | FP32라 오차 6.39e-05로 통과해서 ③ 불필요 |
| report config (4-4) | `2e-5` · `["q_proj", "v_proj"]` | 그대로 | ④ 안 고침 → 보고서가 실제 설정과 다름 (위 "고칠 점") |

슬라이드는 바꾼 줄에 `# 바꿈` 주석을 달라고 했는데, 다음엔 바꾼 줄 옆에 표시해 두기.

**내가 단 주석**

| 위치 | 내가 단 주석 | 메모 |
|---|---|---|
| 1강 설명(markdown) | `(alpha[얼마의 배율을 갖게할건지.일반적으로 실무에선 r의2배] / r)스칼라 이용` | 맞음. α/r은 스칼라 배율 |
| `rank, alpha = 1, 2` | `#alpha는 보통 r의 2배.` | 실무 흔한 시작값 α = 2r |
| 작은 SGD 셀 첫 줄 | `# A는 균등분포에서 추출. B는 0으로시작. B의 기울기가 처음에 0이라 첫A 기울기는 0` | 고칠 점: A 기울기가 0인 이유는 B의 **값**이 0이라서예요. B의 **기울기**는 [−2, 2]로 0이 아님 |
| `A_small = ...` | `# 같은확률을 가진 밀도함수 이용. Kaiming uniform.` | PEFT 기본 초기화 설명으로는 맞음. 이 예제의 A는 손계산용으로 **고정한 값** [1, 0, −1] |
| `mse_loss(...)` | `# 예측과 target에 대해 mse_loss측정` | |
| `optimizer_small.zero_grad()` | `# 가중치 초기화.` | 고칠 점: 가중치가 아니라 **이전 기울기(.grad)**를 0으로 |
| `loss_small.backward()` | `# 기울기 계산.` | |
| `"probe_before",` | `# SFT 전. 밑은 후` | 3장 학습 전 / 후 관찰 문항 |
| LoraConfig 설명(markdown) | `# causal LM, BERT 차이. 다음에올것을 모르는상태에서 예측(causal LM)` | 맞음. BERT는 가운데를 가리고 양쪽을 다 보는 masked LM |
| `MODEL_DTYPE = ...` | `#요즘 프론티어 lv에선 4bit로 줄여서 사용.` | 5장 QLoRA가 기반 가중치를 4비트로 양자화 |
| `lora_config = LoraConfig(` | `# 하이라이트. 중요.` | |
| `get_peft_model(...)` | `# base model은 그대로 두고 독립적인 어댑터로 붙임` | 맞음. 기반 W는 `requires_grad=False`, A · B만 학습 |
| `with torch.inference_mode():` | `# generate 할때에는 gradient계산 필요없기때문에 메모리의 효율적이용.` | |
| `trainer.train()` | `# 실제 학습이 일어나는부분.` | |
| `elapsed_seconds = ...` | `# 시간측정.` | |
| 병합 셀 첫 줄 | `# 학습이 잘된케이스에서 merge.` | 보충: 병합은 학습이 잘됐든 아니든 **같은 계산**이에요. 병합 검사는 품질이 아니라 수치 확인 |
| report 셀 첫 줄 | `R가 결정적으로 어댑터의 shape. 트레이닝 할 가중치를 늘려주는것. 알파는 일종의 학습률.(빠른학습 기대가능 but 가중치 뻥튀기 가능성.)` | r은 A · B 모양(학습 파라미터 수)을 정함. α는 정확히는 학습률이 아니라 **변화량 배율** α/r인데, 크게 하면 갱신 효과가 커져서 학습률을 올린 것과 비슷하게 움직여요 |

**통합 실습 TODO 1 (rank 읽기)**: 실습은 `rank = A.shape[0]`으로 읽고 `B.shape[1]`과 비교해요. B에서 읽도록 바꿔도 되는데, 그때는 **A와 비교해야** 중간 차원 불일치를 잡아요.

```python
rank = B.shape[1]
if rank <= 0 or A.shape[0] != rank:
    raise ValueError("A와 B의 중간 차원이 같아야 합니다.")
```

## PPT 정리
- 4장 결과물: **2.1 MB 어댑터와 같은 조건의 비교**
  - 4-1 W 옆에 저랭크 경로 B·A를 더한다 → 두 경로의 합 = 병합 · 540,672개
  - 4-2 LoraConfig로 붙이고 LoRA만 학습되는지 검사한다 → 0.9207 → 0.8717 · 19초 · 1.61 GiB
  - 4-3 어댑터만 저장하고 같은 기반 위에 복원 · 병합한다 → 2.1 MB · 오차 0.0 · 6.87e-05
  - 4-4 조건을 맞춘 뒤 숫자와 원문을 함께 읽는다 → SFT 12/12 · LoRA 0/12 (lr 2e-5)
- 같은 lr 2e-5에선 LoRA 0/12 — lr · 적용 층을 LoRA에 맞추면 SFT와 같은 10/12를 메모리 1/3로.
- 어느 경우든 **형식 통과와 판단은 따로.** 초과 금액 오답은 설정이 아니라 데이터 · 모델 쪽 문제로 남아요(9장).
- 다음 5장: 고정한 기반 가중치를 **양자화**해 메모리를 더 줄이는 **QLoRA** · 4장 `lora_report.json`과 비교.
- 5장 전에: `lora_adapter` · `lora_report.json` 받기, 설정 바꿔 보기 실습(lr 2e-4 · all-linear · atol 1e-3).

---

## 확인 문제

> 객관식 6 · 단답형 6, 섞어서 배치했어요. **정답 보기**를 누르면 열려요.

### FT4-Q1. 객관식 — 모양
입력 차원 896, 출력 차원 128인 `v_proj`에 r = 8 LoRA를 붙일 때 A와 B의 모양은?

1. A (896, 8) · B (8, 128)
2. A (8, 896) · B (128, 8)
3. A (8, 128) · B (896, 8)
4. A (128, 8) · B (8, 896)

<details>
<summary>정답 보기</summary>
<p><b>2.</b> W가 [출력, 입력] = (128, 896)이니 A는 [r, 입력] = (8, 896), B는 [출력, r] = (128, 8). BA = (128, 896)이라 W에 더할 수 있어요. 파라미터 수 8 × (896 + 128) = 8,192.</p>
</details>

### FT4-Q2. 단답형 — BA 순서
$\Delta W$를 $AB$가 아니라 $BA$로 쓰는 이유는?

<details>
<summary>정답 보기</summary>
<p>열벡터 x에 <b>A를 먼저</b> 곱해 r차원으로 줄이고(Ax), 그다음 B로 출력 차원으로 되돌리니 B(Ax) = BAx예요. 모양으로 봐도 B (m, r) · A (r, n) = (m, n)이라 W와 같은 모양이 돼요.</p>
</details>

### FT4-Q3. 객관식 — B = 0
PEFT 기본 초기화(B = 0)로 학습을 시작할 때 맞는 것은?

1. 시작 모델의 출력이 원래 모델과 다르다
2. 첫 역전파에서 A와 B 모두 기울기가 0이다
3. 첫 역전파에서 A 기울기는 0이고 B 기울기는 0이 아닐 수 있다
4. B가 0이라 학습이 끝까지 진행되지 않는다

<details>
<summary>정답 보기</summary>
<p><b>3.</b> A의 기울기는 B의 값을 곱해서 오니 0, B의 기울기는 Ax를 곱해서 오니 0이 아니에요(작은 예제 [−2, 2]). 한 번 갱신하면 B ≠ 0이 되어 다음부터 A도 학습돼요.</p>
</details>

### FT4-Q4. 단답형 — 파라미터 수
q · v에 r = 8을 붙인 LoRA의 학습 파라미터가 540,672개인 계산 과정을 쓰세요. (24블록, q 896×896, v 128×896)

<details>
<summary>정답 보기</summary>
<p>q: 8 × (896 + 896) = 14,336, v: 8 × (896 + 128) = 8,192 → 블록당 22,528 × 24 = <b>540,672</b>. 전체 494,573,440의 0.11%.</p>
</details>

### FT4-Q5. 객관식 — 붙인 뒤 검사
`get_peft_model` 직후 "requires\_grad=True인 파라미터 이름에 모두 `lora_`가 들어 있는지" 검사하는 이유는?

1. 기반 가중치까지 학습 대상이 되면 사실상 전체 SFT가 되기 때문
2. 어댑터 파일 이름을 정하려고
3. B가 0인지 확인하려고
4. 학습률을 자동으로 정하려고

<details>
<summary>정답 보기</summary>
<p><b>1.</b> 기반 가중치가 섞이면 메모리 이점이 사라지고 비교도 무너져요. B = 0 확인은 별도 assert이고, 학습 뒤에는 W가 그대로인지(frozen_unchanged) · B ≠ 0인지 봐요.</p>
</details>

### FT4-Q6. 단답형 — 원본 0/12
원본 4장(lr 2e-5 · q · v)에서 dev loss는 0.92 → 0.87로 줄었는데 형식이 0/12인 이유는?

<details>
<summary>정답 보기</summary>
<p>학습은 됐지만(W 그대로 · B ≠ 0) <b>24번 × 2e-5로는 행동을 바꿀 만큼 움직이지 않았어요.</b> 2e-5는 전체 SFT 기준 학습률이라 LoRA에 맞춘 값이 아니에요. 관찰 문항 원문이 학습 전과 글자까지 같았어요.</p>
</details>

### FT4-Q7. 객관식 — 저장 파일
`model.save_pretrained("lora_adapter")`가 저장하는 것으로 맞는 것은?

1. 기반 모델 전체 가중치 + 어댑터
2. optimizer · scheduler 상태
3. 병합한 W'
4. 어댑터 가중치(A · B)와 adapter\_config.json(기반 모델 ID · revision 등)

<details>
<summary>정답 보기</summary>
<p><b>4.</b> 기반 모델은 중복 저장하지 않아서 몇 MB예요(q · v 2.1 MB, all-linear 17.6 MB, A · B는 FP32). 그래서 다시 쓸 때 같은 기반 모델 ID · revision을 함께 맞춰야 해요.</p>
</details>

### FT4-Q8. 단답형 — allclose
`torch.allclose(a, b, atol=0.01, rtol=0.01)`에서 b = 100일 때 허용 오차는?

<details>
<summary>정답 보기</summary>
<p>atol + rtol × |b| = 0.01 + 0.01 × 100 = <b>1.01</b>. b = 0이면 0.01. 허용 오차는 수치 비교용이지 업무 오답을 허용한다는 뜻이 아니라서 생성 원문은 <code>==</code>로 따로 봐요.</p>
</details>

### FT4-Q9. 객관식 — 병합
`merge_and_unload(safe_merge=True)` 전후 logits를 FP32에서 비교하는 검사가 보여 주는 것은?

1. 병합 후 답변 품질이 좋아졌다
2. (W + ΔW)x = Wx + ΔWx로 같은 계산이라는 것(수치 재현)
3. 어댑터를 다른 기반 모델에도 쓸 수 있다
4. 학습률이 적절했다

<details>
<summary>정답 보기</summary>
<p><b>2.</b> 내 실행에서 최대 절대 오차 6.39e-05, 다음 토큰 ID 4913로 같았어요. 품질은 dev 원문으로 따로 평가해요. safe_merge는 병합 결과에 NaN이 없는지 검사해요.</p>
</details>

### FT4-Q10. 단답형 — 배율 유지
r을 8에서 16으로 올리면서 지금 배율을 유지하려면 lora\_alpha를 얼마로 해야 하나요?

<details>
<summary>정답 보기</summary>
<p><b>32.</b> 배율은 α/r이라 r만 바꾸면 배율도 바뀌어요. 16/8 = 2를 유지하려면 32/16. r을 2배로 하면 학습 파라미터도 2배.</p>
</details>

### FT4-Q11. 객관식 — 비교 조건
`check_comparison_inputs`로 3장과 대조하지 **않는** 것은?

1. max\_steps · learning\_rate · seed
2. 생성 설정(GENERATION) 전부
3. 관찰 문항의 case\_id와 messages
4. 학습 대상 파라미터 수

<details>
<summary>정답 보기</summary>
<p><b>4.</b> 학습 대상 수(494,032,768 vs 540,672)는 일부러 다르게 둔 <b>비교 대상</b>이에요. 나머지는 같아야 차이를 갱신 대상 탓으로 읽을 수 있어요.</p>
</details>

### FT4-Q12. 단답형 — 보고서 config
보강 실습에서 learning\_rate와 target\_modules만 바꾸고 report의 config를 그대로 두면 생기는 문제는?

<details>
<summary>정답 보기</summary>
<p><code>lora_report.json</code>이 <b>실제 학습 설정과 다른 값</b>(2e-5 · q · v)을 기록해서, 5장이 틀린 설정을 읽고 <code>check_comparison_inputs</code>도 learning_rate 대조를 잘못 통과해요. config를 2e-4 · all-linear로 고치고, 일부러 다르게 한 learning_rate 키만 비교 목록에서 빼요.</p>
</details>
