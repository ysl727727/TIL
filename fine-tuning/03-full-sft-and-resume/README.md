# 3장. 전체 가중치 SFT와 학습 재개

> 2026-11-18 학습 기록. 파인튜닝 3일차 수업이에요. 1 · 2장은 가중치를 하나도 바꾸지 않는 준비 단계였고, 3장에서 **처음으로 가중치를 바꿔요.** 2장의 `training_data.zip`을 그대로 읽어서 답변 토큰에만 손실을 걸고, Qwen2.5-0.5B의 **가중치 4.94억 개 전부**를 24번 갱신해요. 12번째에서 일부러 멈췄다가 체크포인트로 이어서 학습하고, 다 배운 모델은 추론용으로 따로 저장해요.
>
> 3장의 한 문장: **답변 토큰만 채점해서 전체 가중치를 바꾸고, 손실이 내려가도 업무 답은 따로 읽고, 이어서 학습할 상태와 쓸 모델은 나눠 저장한다.**

## 큰 흐름

```text
[준비] 설치 → 런타임 재시작 → 버전 · BF16 확인 → training_data.zip 읽기 (48 / 12 / 12, 그룹 안 겹침)
3-1 손실 마스크   encode_example → input 370 = 프롬프트 299(labels −100) + 답변 · EOS 71
                  collate → 가장 긴 것에 맞춰 (2, 379): input pad ID / attention 0 / labels −100
                  toy loss → logits[:, :-1] ↔ labels[:, 1:], 모를 때 손실 = log 6 = 1.791759
3-2 전체 SFT      전체 = 학습 대상 494,032,768 → 학습 전 dev 12문항 응답 · 가중치 표본 256개 보관
                  TrainingArguments(24갱신 계획 · 4문항당 1갱신) + StopAtTwelve → checkpoint-12
3-3 곡선 읽기     log_history → train · dev loss · 학습률, grad_norm은 NaN · 폭증만 확인
                  dev loss가 0에 가까워도 업무 판단은 따로 읽기 (손실 ≠ 업무 정답)
3-4 재개 · 저장   del → checkpoint-12로 새 Trainer → resume_from_checkpoint → 13~24
                  표본 변화 확인 → save_pretrained → 다시 읽어 같은 답 → sft_report.json → sft_model.zip
      ↓
4장 LoRA: 같은 SFT 목표를 W는 고정하고 A · B만 학습 → 메모리 · 결과를 3장과 비교
```

**1 · 2 · 3장 비교**

| 장 | 모델을 어떻게 쓰나 | Qwen 가중치 W | 남기는 것 |
|---|---|---|---|
| 1장 | 추론만 (`generate`) | 읽기만 | `baseline.json` |
| 2장 | 토크나이저만 | 안 씀 | `training_data.zip` |
| **3장** | **SFT 학습** (`Trainer`) | **전부 바뀜** (4.94억 개) | `sft_model/` · `sft_report.json` |

## 학습 목표
- SFT의 학습 신호가 무엇인지, 질문 · 규정은 읽기만 하고 **모범답안과 EOS만 맞히게** 하는 방법을 코드로 설명한다.
- 길이가 다른 문항을 배치로 묶을 때 세 텐서를 각각 다른 값으로 패딩하는 이유를 안다.
- "t번째 출력이 t+1번째 토큰을 맞힌다"(shift)를 작은 텐서로 확인하고, 이 shift를 **누가, 몇 번** 하는지 안다.
- `TrainingArguments`의 학습량 · 학습률 · 정밀도 · 평가 · 저장 설정을 읽고, 유효 배치와 epoch을 계산한다.
- 손실 곡선을 읽되 **dev loss와 업무 정답률을 구분**한다.
- 학습 재개용 체크포인트와 추론용 모델의 차이를 알고, 중단한 학습을 같은 계획으로 이어 간다.

## 실습 환경
- 노트북: `sft.ipynb` (29셀). 2장 `training_data.zip`(SHA-256 `018a6120…`)을 Colab 파일 목록에 올려서 실행
- **Colab GPU 필요.** 런타임 유형을 T4 GPU로 바꿔서 실행
- `%pip install "transformers==5.22.2" "accelerate==1.15.0"` → **런타임 재시작** → 환경 셀부터. 3장은 버전이 다르면 환경 셀이 `RuntimeError`로 멈춰요(1 · 2장 때 5.22.1이 찍힌 문제를 이번엔 재시작으로 해결)
- 모델 `Qwen/Qwen2.5-0.5B-Instruct`, revision `7ae5576…` 고정, `MAX_LENGTH = 512`, `SEED = 42`, `TOTAL_STEPS = 24`, `PAUSE_STEP = 12`
- **T4는 BF16을 하드웨어로 지원하지 않아서** `weight_dtype = torch.float32`로 학습했어요. 슬라이드 숫자(RTX 5060 Laptop · BF16)와 시간 · 손실 · 표본 변화가 다르게 나와요(아래 실행 결과)

## 실습 파일

| 파일 | 하는 일 | 상태 |
|---|---|---|
| `sft.ipynb` | 3-1 마스킹 · 배치 → 3-2 전체 SFT 12갱신 → 3-3 곡선 → 3-4 재개 12→24 · 저장 · 재로딩 · 리포트 | ✅ Colab T4(FP32) 끝까지 실행 |
| `sft_model/` · `sft_report.json` | 추론용 모델 · 학습 기록 (6 · 7장에서 다시 올림) | ⏳ Colab에만 있음, `ARCHIVE_FOLDER` 셀로 ZIP 만들어 내려받기 남음 |
| `sft_run/checkpoint-12` · `-24` | 학습 재개용 상태 | Colab에만 있음 (선택 보관) |

---

## 핵심 이론

### 3-1. 답변 토큰에만 손실 계산하기

**SFT(Supervised Fine-Tuning)** = 이미 사전학습한 모델을 **입력 + 모범답안** 쌍으로 더 학습시키기. RAG처럼 정답을 저장소에 넣는 게 아니라 **손실을 역전파해서 가중치를 바꿔요.**

| 학습에 넣는 것 | 손실에서 하는 일 | 코드 위치 |
|---|---|---|
| 질문 · 규정 | 문맥으로 **읽기만** | `input_ids`의 프롬프트 구간 (labels −100) |
| 모범답안의 앞 토큰 | 다음 토큰을 맞히는 문맥 (**teacher forcing**) | `input_ids`의 답변 구간 |
| 모범답안의 다음 토큰 + EOS | 실제 **예측 목표** | `labels`에서 −100이 아닌 위치 |

- SFT ≠ 전체 가중치. 3장은 전체, 4 · 5장은 LoRA의 A · B만 **같은 SFT 목표**로 학습해요.
- 프롬프트를 빼고 답변만 채점하는 건 이 수업의 선택이에요. 모든 SFT 구현이 똑같이 마스킹하진 않아요.

**`encode_example` — 대화 1개 → `input_ids` · `attention_mask` · `labels`**

```python
prompt_ids = apply_chat_template(messages[:2], add_generation_prompt=True)    # system + user + "assistant\n" = 299
full_ids   = apply_chat_template(messages,     add_generation_prompt=False)   # + 답변 + <|im_end|> + \n = 371
assert full_ids[:299] == prompt_ids                                           # 경계가 맞아야 자를 수 있음
end = len(prompt_ids) + answer_ids.index(eos_id) + 1                          # EOS까지 포함, 뒤 \n만 버림
input_ids = full_ids[:end]                                                    # 370
labels = [-100] * len(prompt_ids) + input_ids[len(prompt_ids):]               # 299개 −100 + 71개 채점
```

```text
input_ids  = [ <|im_start|> system ... user ... assistant \n | {"status" ... -v1"]} <|im_end|> ]
labels     = [ -100 ...                                -100 | {"status" ... -v1"]} <|im_end|> ]
              └──────────── 299개: 읽기만 ───────────────┘ └──── 71개: 채점 ─────────────┘
attention  = [ 1 1 1 ... 1 ]  (아직 패딩이 없어서 전부 1)
```

- `+1`은 슬라이스 `[:end]`가 끝을 포함하지 않아서 EOS까지 넣으려고 붙여요. **EOS는 남기고 뒤의 `\n`만** 잘라요. EOS를 배워야 "여기서 멈춰"를 알아요.
- 512를 넘으면 자르지 않고 에러. 실제 최대 379.
- **labels를 미리 한 칸 밀지 않아요.** 미는 건 모델 내부가 해요.
- test는 학습 · 설정 선택에 안 쓰니 **토큰화도 안 해요.**

```text
첫 학습 문항: policy03-below
입력 길이 / 답변 시작 / 학습 토큰 수: 370 299 71
학습할 답변과 종료 표시: {"status": "answered", "answer": "숙박비 지원 한도는 1박 85,000원입니다. 질문의 1박 80,000원은 한도 이하이므로 사전 승인이 필요하지 않습니다.", "citations": ["policy03-v1"]}<|im_end|>
최대 길이: {'train': 379, 'dev': 379}
```

**`collate` — 여러 문항을 한 배치로**

GPU는 여러 문항을 **행렬 하나로 한꺼번에** 계산할 때 빨라요. 행렬은 줄 길이가 같아야 해서, 짧은 문항 뒤를 채워 가장 긴 문항에 맞춰요(`padding_side="right"`).

```python
def collate(features):
    return {
        "input_ids":      pad_sequence([...], batch_first=True, padding_value=tokenizer.pad_token_id),
        "attention_mask": pad_sequence([...], batch_first=True, padding_value=0),
        "labels":         pad_sequence([...], batch_first=True, padding_value=-100),
    }
```

| 텐서 | 진짜 토큰 자리 | 패딩 자리 |
|---|---|---|
| `input_ids` | 토큰 ID | pad ID 151643 (자리만 채움) |
| `attention_mask` | 1 | 0 (읽지 마) |
| `labels` | −100 또는 정답 ID | −100 (채점하지 마) |

- Qwen은 pad ID 151643이 또 다른 종료 ID(`<|endoftext|>`)와 같아요. 그래서 **값이 아니라 위치**로 패딩을 구분해요.
- 가장 짧은 문항 + 가장 긴 문항(379)을 묶어 `check_padded_batch`로 확인: 세 모양이 같은지, `labels[attention_mask == 0]`이 전부 −100인지, EOS 위치와 채점 토큰 수가 그대로인지 → **(2, 379)**.

**toy loss — 한 칸 밀어서 맞히기**

```python
toy_logits = torch.zeros(1, 4, 6)                    # [배치, 위치, 어휘], 점수 전부 0
toy_labels = torch.tensor([[-100, -100, 2, 5]])
loss = F.cross_entropy(toy_logits[:, :-1, :].reshape(-1, 6),   # 마지막 위치 예측은 짝이 없어서 뺌
                       toy_labels[:, 1:].reshape(-1),          # 0번 예측의 정답은 1번 토큰이라 첫 칸 뺌
                       ignore_index=-100)
# 패딩 검사 통과, 배치 모양: (2, 379)
# shift 후 학습 대상 수 / 균등 분포 손실: 2 1.791759
```

점수가 다 같으면 6개에 1/6씩 → 손실 = −log(1/6) = **log 6**. 아무것도 모를 때(6지선다 찍기)의 손실이에요. 1장 세 점수 예제의 log 3 = 1.099와 같은 원리.

| 어디서 | shift는 누가 |
|---|---|
| 3\~5장 SFT · LoRA · QLoRA | 모델 내부 (labels만 넘김) |
| 6장 DPO 손실 함수 | 로짓을 직접 받아서 직접 (한 곳에서만) |

### 3-2. 전체 가중치를 학습 대상으로 두고 SFT 시작

**모델 불러오기와 전체 = 학습 대상**

```python
model = AutoModelForCausalLM.from_pretrained(MODEL_ID, revision=REVISION,
            dtype=weight_dtype, attn_implementation="sdpa").to("cuda")
model.config.use_cache = False           # KV 캐시는 생성용, 학습엔 필요 없음
assert total_parameters == trainable_parameters   # 494,032,768 == 494,032,768 (100%)
```

- `bf16_available`은 `including_emulation=False`로 **하드웨어가 직접 지원할 때만** True. T4는 False → FP32. FP16으로 바꾸지 않아요(범위가 좁아 손실 스케일링 같은 장치가 더 필요).
- 전체 SFT 메모리 어림: 파라미터 × 바이트 × 약 4(가중치 · 기울기 · AdamW 상태 2개) + 활성값. BF16이면 0.92 GiB × 4 ≈ 3.7 GiB, FP32면 그 2배.

**학습 전 기록 남기기**

```python
generation = GenerationConfig(do_sample=False, num_beams=1, max_new_tokens=192, repetition_penalty=1.1, ...)
dev_before = [generate_probe(model, row) for row in records["dev"]]      # dev 12문항 답 전부 보관
sample_before = parameter.detach().flatten()[sample_indices].float().cpu().clone()   # q_proj 고정 위치 256개
```

- greedy(`do_sample=False`)라 같은 입력이면 같은 답 → 학습 전후를 **같은 조건**으로 비교할 수 있어요.
- `generate_probe`는 `messages[:2]`(모범답안 제외) + `add_generation_prompt=True`로 입력을 만들고, `generate` 결과에서 **입력 길이만큼 잘라 새 답만** 읽어요.
- 가중치 표본은 `linspace`로 고르게 뽑은 256자리를 `.clone()`으로 따로 복사해요. 학습으로 원본이 바뀌어도 복사본은 그대로라 나중에 비교할 수 있어요.

**TrainingArguments — Trainer에 주는 설정표** (모델도, 권장값도 아님)

| 묶음 | 설정 | 값 | 쉬운 뜻 |
|---|---|---|---|
| 학습량 | `max_steps` | 24 | 가중치를 총 24번 갱신 (epoch보다 우선) |
| | `per_device_train_batch_size` | 1 | 한 번에 1문항 계산 |
| | `gradient_accumulation_steps` | 4 | 4문항의 기울기를 모아 1번 갱신 |
| 학습률 | `learning_rate` · `warmup_steps` | 2e-5 · 2 | 2갱신 동안 올렸다가 |
| | `lr_scheduler_type` | linear | 24에서 0이 되도록 일정하게 감소 |
| | `optim` · `weight_decay` | adamw\_torch · 0.01 | AdamW, 가중치가 너무 커지지 않게 당김 |
| | `max_grad_norm` | 1.0 | 기울기 **전체 크기**를 1로 제한 (가중치 값을 자르는 게 아님) |
| 정밀도 | `bf16` · `fp16` | 지원 시 True · False | T4는 둘 다 False → FP32 |
| | `gradient_checkpointing` | True | 활성값 일부를 버렸다가 역전파 때 다시 계산 (메모리 ↔ 시간) |
| 평가 · 로그 | `eval_steps` · `logging_steps` | 4 · 4 | **4갱신(= 16문항)**마다 |
| | `logging_nan_inf_filter` | False | NaN을 숨기지 않음 |
| 저장 | `save_steps` · `save_total_limit` | 12 · 2 | 12갱신마다 저장, 최대 2개 보관 |
| | `save_only_model` | False | optimizer · scheduler · 난수 상태까지 저장 → **재개 가능** |
| | `report_to` | none | W&B 같은 외부 서비스로 안 보냄 |

```text
유효 배치 = 장치별 배치 1 × GPU 1 × 누적 4 = 4문항당 1갱신
train 48문항 ÷ 4 = 12갱신 = 1 epoch  →  max_steps 24 = 2 epoch
```

**StopAtTwelve — 계획은 24로 두고 멈추기만**

```python
class StopAtTwelve(TrainerCallback):
    def on_step_end(self, args, state, control, **kwargs):
        if state.global_step == PAUSE_STEP:
            control.should_training_stop = True
        return control
```

`max_steps=12`로 바꾸면 학습률이 12에서 0이 되도록 **계획 자체가** 바뀌어요. 그래서 계획은 24로 두고 콜백으로 멈추기만 해요. Colab 세션 종료 · GPU 선점으로 학습이 끊기는 상황을 흉내 낸 거예요.

**Trainer 연결 → 첫 구간**

```python
trainer = Trainer(model=model, args=args, train_dataset=encoded["train"], eval_dataset=encoded["dev"],
                  data_collator=collate, processing_class=tokenizer, callbacks=[StopAtTwelve()])
eval_before = trainer.evaluate()          # 학습 전 dev loss (가중치 안 바뀜)
first_train_output = trainer.train()      # 1~12갱신 후 멈춤 → sft_run/checkpoint-12
```

- `processing_class=tokenizer`만 넣는다고 답변 전용 labels가 생기진 않아요. 그 일은 `encode_example`과 `collate`가 해요.
- 체크포인트에 `trainer_state.json`(global\_step 12 · max\_steps 24) · `optimizer.pt` · `scheduler.pt` · `rng_state.pth` · `model.safetensors`가 있는지 assert, loss · eval\_loss · grad\_norm이 전부 유한한지 assert.

### 3-3. 손실 곡선과 학습 설정 읽기

```python
train_points = [(item["step"], item["loss"])      for item in first_history if "loss" in item]
dev_points   = [(item["step"], item["eval_loss"]) for item in first_history if "eval_loss" in item]
ax.plot(*zip(*train_points), marker="o")     # zip(*[(4, a), (8, b)]) → (4, 8), (a, b)
```

`trainer.state.log_history`는 딕셔너리 리스트예요. 학습 로그 줄엔 `"loss"`, 평가 줄엔 `"eval_loss"`가 있어서 **키가 있는 줄만** 골라요.

**읽는 법**

| 값 | 무엇 | 주의 |
|---|---|---|
| train loss | 최근 4갱신(16문항)의 **평균** | 앞쪽의 높은 손실이 섞여 있어서 dev보다 높아도 이상하지 않음 |
| dev loss | 그 시점 모델로 dev 12문항을 **한 번** 계산 | 학습에 안 쓴 그룹(policy01 · 05) |
| learning\_rate | warmup 2 → 2e-5 → 24에서 0 근처 | 계획대로 줄어드는지 |
| grad\_norm | 기울기 전체 크기 | 자르기 **전** 값이 기록될 수 있어서 1보다 커도 실패 아님. NaN · 폭증만 봄 |

**손실 ≠ 업무 정답 (슬라이드 · BF16 실행)**

```text
policy01-over_limit (한도 65,000원, 질문 70,000원)
학습 후: "질문의 1박 70,000원은 한도 이하이므로 사전 승인이 필요하지 않습니다."  ← 틀림
```

| dev 12문항 (슬라이드) | 학습 전 | 학습 후 |
|---|---|---|
| dev loss | 0.921 | 0.0049 |
| JSON만 출력 | 0/12 | 12/12 |
| 판단 맞음 | - | 10/12 (over\_limit 01 · 05 틀림) |

손실은 **토큰 71개의 평균**이라, "이하/초과" 몇 토큰만 틀리면 평균에 묻혀요. 사람에게는 금액 판단 하나가 틀리면 업무상 오답이에요. 그래서 7장에서 생성한 답을 규칙으로 따로 채점해요. 손실이 이렇게 0에 붙으면 실무에서는 **외우기(과적합)**를 의심하고 원문을 직접 읽어요.

### 3-4. 체크포인트로 재개하고 모델 저장하기

| | 학습 체크포인트 `sft_run/checkpoint-N` | 추론용 모델 `sft_model/` |
|---|---|---|
| 들어 있는 것 | 가중치 + optimizer + scheduler + 난수 + 진행 단계 | 가중치 + 설정 + 토크나이저 |
| 용도 | **학습 이어 하기** | **답 생성** (6장 DPO 출발점 · 7장 평가) |
| 크기 (BF16 기준) | 약 3 GB (optimizer가 가중치의 2배) | 약 1 GB |

`sft_model`만 읽고 새 optimizer로 `train()`하면 AdamW가 쌓아 둔 평균 · 분산이 0부터 다시 시작해서 **재개가 아니라 새 학습**이에요.

```python
del trainer, model; gc.collect(); torch.cuda.empty_cache()     # GPU에 모델 두 개가 남지 않게
model = AutoModelForCausalLM.from_pretrained(checkpoint, dtype=weight_dtype, ...).to("cuda")
trainer = Trainer(model=model, args=args, ...)                  # 같은 args, 콜백 없음
trainer.train(resume_from_checkpoint=str(checkpoint))           # optimizer · scheduler · 난수 · step 복원
assert trainer.state.global_step == 24                          # 24번 "추가"가 아니라 처음부터 센 목표 → 13~24만
```

- `missing keys: ['lm_head.weight']` 경고: Qwen2.5-0.5B는 입력 임베딩과 출력층이 **가중치를 공유**(tie\_word\_embeddings)해서 따로 저장하지 않아요. 무시해도 돼요.

**저장 → 다시 읽기 → 리포트**

```python
parameter_change = {"changed_count": (sample_before != sample_after).sum().item(), ...}
assert parameter_change["changed_count"] > 0
model = trainer.accelerator.unwrap_model(model, keep_fp32_wrapper=False)   # 학습용 포장 벗기기
dev_after = [generate_probe(model, row) for row in records["dev"]]
model.save_pretrained(MODEL_DIR); tokenizer.save_pretrained(MODEL_DIR)    # 토크나이저는 따로 저장
reloaded = AutoModelForCausalLM.from_pretrained(MODEL_DIR, ...)
assert generate_probe(reloaded, probe)["raw_response"] == probe_after["raw_response"]
```

- `unwrap_model`로 혼합 정밀도 포장을 벗겨야 저장 후 다시 읽은 모델과 **같은 조건**에서 생성해요.
- 메모리에서 지우고 **파일에서만** 다시 읽어 같은 답이 나오면 저장이 제대로 된 거예요(greedy라 같아야 함).
- `sft_report.json`: 설정 · 환경 · 데이터 해시 · 로그 전체 · **dev 학습 전후 원문** · 표본 변화 · 재개 기록 · 시간 · 메모리. 4 · 7장 비교의 근거.

**`ARCHIVE_FOLDER` — 7장이 받는 ZIP**

```python
ARCHIVE_FOLDER = Path("sft_model")     # 기본 None이면 아무것도 안 함
for path in source_folder.rglob("*"):
    if path.is_file():                 # 폴더 항목 X, 파일만
        archive.write(path, arcname=path.relative_to(source_folder.parent))   # sft_model/파일명
```

7장은 ZIP 안 이름 목록을 정확히 검사해요. 탐색기 · macOS로 압축하면 `sft_model/` 폴더 항목이 끼어서 거부돼요. 꼭 이 셀로 만들기. `ZIP_STORED`는 압축 없이 담아 시간을 아껴요(가중치는 압축이 거의 안 됨).

**새 세션에서 checkpoint-12만 이어 학습** (`RUN_SAVED_CHECKPOINT = True`일 때만): `checkpoint-12.zip`을 올리고 설치 → 데이터 → encode → collate까지만 실행한 뒤 이 셀로 12 → 24. ZIP을 풀기 전에 모든 경로가 복원 폴더 안인지(`is_relative_to`) 확인해서 **zip slip**(폴더 밖에 파일 쓰기)을 막아요.

---

## 실행 결과 (내 실행 — Colab Tesla T4 · FP32)

| 단계 | 결과 |
|---|---|
| 환경 | Python 3.13.16 · torch 2.14.1+cu130 · **transformers 5.22.2** · accelerate 1.15.0 · matplotlib 3.10.0 · CUDA 13.0 · Tesla T4 · `bf16_supported: false` → `torch.float32` |
| 데이터 | 48 / 12 / 12 · dev policy01 · 05 · test policy02 · 11 · ZIP SHA-256 `018a6120…` (슬라이드와 같음) |
| 3-1 | 370 / 299 / 71 · 최대 379 · 배치 (2, 379) · toy 2개 · 1.791759 |
| 3-2 | 전체 = 학습 대상 494,032,768 · 관찰 문항 `policy01-over_limit` · 학습 전 dev loss **0.9167** |
| 첫 구간 | 1\~12갱신 **196.9초** · checkpoint-12 파일 11개 (`optimizer.pt` · `scheduler.pt` · `rng_state.pth` · `trainer_state.json` · `model.safetensors` · `training_args.bin` · config · tokenizer · chat\_template) |
| 재개 | 12 → 24 · **456.3초** · 최종 dev loss **0.000303** |
| 표본 변화 | 256개 중 **256개** 바뀜 · 최대 변화 1.41e-4 |
| 관찰 문항 | 학습 후 **"한도를 초과하므로 예약 전 서면 승인을 받아야 합니다."** (맞음) |
| 저장 | `/content/sft_model` · 저장 전후 같은 응답 **True** · `sft_report.json` · `checkpoint-24` |

**손실 로그 (내 실행 vs 슬라이드)**

| 갱신 | train (내) | dev (내) | 학습률 | train (슬라이드) | dev (슬라이드) |
|---|---|---|---|---|---|
| 0 | - | 0.9167 | - | - | 0.9207 |
| 4 | 0.6809 | 0.1156 | 1.91e-05 | 0.7016 | 0.1599 |
| 8 | 0.0716 | 0.0475 | 1.55e-05 | 0.0926 | 0.0456 |
| 12 | 0.0389 | 0.0158 | 1.18e-05 | 0.0338 | 0.0199 |
| 16 | 0.0098 | 0.0037 | | 0.0115 | 0.0092 |
| 20 | 0.0040 | 0.0006 | | 0.0159 | 0.0070 |
| 24 | 0.0005 | 0.0003 | | 0.0111 | 0.0049 |

- 학습률은 슬라이드와 똑같이 1.91e-5 → 1.55e-5 → 1.18e-5로 줄었어요(계획은 정밀도와 상관없음).
- 첫 학습 직전에 `tokenizer has new PAD/BOS/EOS tokens … Updated tokens: {'pad_token_id': 151643}` 안내가 떠요. 토크나이저의 pad ID를 모델 설정에 맞춰 넣었다는 뜻이고, collate가 쓰는 151643과 같아요.
- **아직 확인 못 한 것**: dev 12문항 전체의 형식 · 판단 개수(`sft_report.json`의 `dev_after`에 있음)와 최고 메모리(`peak_allocated_gib`). 노트북 출력에는 관찰 문항 하나만 찍혀요.

## 질문과 새로 알게 된 점

### `prompt_ids`는 왜 `messages[:2]`이고, `add_generation_prompt`는 왜 True / False를 나누나
- messages = [system, user, assistant]. 앞 2개 + `add_generation_prompt=True` → `<|im_start|>assistant\n`까지 붙어 **"답변 직전까지"** = 299토큰.
- `full_ids`는 3개 전부 + `False` → 답변 + `<|im_end|>` + `\n`까지 371토큰(policy03-below 기준).
- True는 "이제 답해"라는 자리를 새로 만들고, False는 이미 있는 메시지만 템플릿으로 감싸요. 정답이 든 대화에 True를 쓰면 답 뒤에 또 답을 시작하라는 대화가 돼요.

### `+1`은 EOS를 빼는 게 아니라 넣는 것
- `end = 299 + answer_ids.index(eos_id) + 1` → EOS **포함**까지. Qwen 템플릿은 메시지마다 `<|im_end|>\n`을 붙여서, EOS는 남기고 **뒤 `\n`만** 잘라요.
- 그래서 `full_ids`(371, `\n` 포함)와 `input_ids`(370, `\n` 제외)는 다른 리스트예요.

### −100은 무엇이고, 슬라이싱 · −100 · attention 0은 어떻게 다른가
- −100은 PyTorch `cross_entropy`의 기본 `ignore_index`. 실제 토큰 ID로는 나올 수 없는 값이라 "채점 제외" 표시로 써요.

| 표시 | 의미 | 쓰는 곳 |
|---|---|---|
| 슬라이싱 | 아예 없앰 | 답 뒤 `\n` 제거, shift 때 짝 없는 칸 |
| labels −100 | 읽지만 채점 X | 프롬프트, 패딩 |
| attention 0 | 읽지도 않음 | 패딩만 |

- `encode_example`에서 attention이 전부 1인 건 **아직 패딩이 없어서**예요. attention이 없으면 모델이 빈칸까지 참고해서, 같은 문항도 누구와 묶이느냐에 따라 결과가 달라져요.

### `[:, :-1, :]`과 `[:, 1:]` — 쉼표는 축 구분
- logits는 `(batch, seq_len, vocab)` 3축, labels는 `(batch, seq_len)` 2축. 축 순서는 Hugging Face 출력 규칙이에요.
- **위치 축(두 번째)만** 잘라요. **logits는 마지막을 빼고, labels는 첫 칸을 빼요.** (처음엔 반대로 헷갈렸어요)
- `[1:]`만 쓰면 batch 축을 자르고, `[:-2]`는 두 칸을 빼서 안 돼요.

### 이 방식의 이름: next-token prediction + teacher forcing
- 목표는 **next-token prediction**(causal language modeling). t번째 출력이 t+1번째 토큰을 맞혀요.
- **teacher forcing**: 학습 때 모델이 만든 토큰이 아니라 **정답 토큰을 입력으로** 깔아 줘서, 순전파 한 번으로 모든 위치를 채점해요.

### dev loss는 낮은데 생성은 틀릴 수 있는 이유 (exposure bias)
- 손실 평가는 매 위치에 **정답 앞부분**을 깔아 주니까 "이하/초과" 한 토큰을 틀려도 그 자리에서 끝나요.
- 자유 생성은 **자기가 뽑은 토큰을 이어 써서**, 한 토큰 실수가 결론 전체를 뒤집어요.
- 그래서 dev loss만 보지 않고 실제 생성 답을 학습 전후로 비교해요.

### SDPA
- **Scaled Dot-Product Attention**, `softmax(QKᵀ/√d)·V`를 PyTorch에 들어 있는 빠른 함수로 계산하는 방식이에요. 결과는 기본(eager) 구현과 같고 더 빨라요.

### gradient checkpointing vs 학습 체크포인트

| | gradient checkpointing | 학습 체크포인트 |
|---|---|---|
| 무엇 | 계산 방식 설정 | 저장 폴더 (`checkpoint-12`) |
| 어디 | GPU 메모리 | 디스크 |
| 목적 | 활성값 일부만 저장 → 메모리 절약 | 끊긴 학습 이어 하기 |
| 대가 | 재계산으로 시간 증가 | 용량 (BF16 약 3 GB) |

### `eval_steps=4`는 accumulation 4 때문인가 — 반만 맞음
- step은 **갱신 횟수**. 4문항(배치 1 × 누적 4)마다 1갱신.
- `eval_steps=4` 자체는 따로 정한 값이고, "4갱신 × 4문항 = **16문항마다** 평가"가 되는 게 accumulation 때문이에요.

### Trainer와 `args`
- Trainer는 **실행자**, `args`(`TrainingArguments`)는 **설정표**(학습률 · 배치 · 평가 · 저장 주기 · 저장 위치). 학습 루프 코드는 Trainer 안에 다 있고, 우리는 옵션만 지정해요.

### 가중치 표본 256개는 왜 보나
- 학습 전에 `q_proj`에서 고른 간격 256자리를 `.clone()`해 두고, 학습 후 같은 자리와 비교해서 `changed_count > 0`을 확인해요.
- BF16 반올림이나 얼어 있는(학습 대상이 아닌) 가중치 때문에 "loss는 내려가는데 가중치는 그대로"인 경우를 잡아요.
- 256개 중 바뀐 비율 ≠ 전체 4.94억 개 중 바뀐 비율. **표본**이에요.

### 같은 코드인데 내 실행(FP32)과 슬라이드(BF16)가 다른 이유
- **표본 변화 256/256 vs 24/256**: BF16은 유효 숫자가 적어서 아주 작은 갱신이 반올림으로 사라져요. FP32는 그 작은 변화도 남아서 전부 바뀐 걸로 나와요.
- **최종 dev loss 0.0003 vs 0.0049**, 관찰 문항 **맞음 vs 틀림**: 같은 계획이라도 정밀도가 다르면 갱신 결과가 조금씩 달라져요. 다만 dev 1문항이고 dev 전체 판단은 아직 안 세어서, **"FP32라서 금액 비교를 배웠다"고 일반화하면 안 돼요.** 슬라이드도 "하드웨어와 정밀도가 달라지면 수치 결과가 달라질 수 있다"고 해요.
- **시간 196.9 + 456.3초 vs 12.6 + 14.7초**: T4 + FP32라 계산이 훨씬 느리고, FP32 체크포인트는 BF16의 2배 크기라 저장 · 불러오기도 오래 걸려요.

### SFT vs DPO
- SFT: 모범답안 토큰을 그대로 따라 배우기 (3장, `training_data.zip`의 assistant 메시지가 모범답안).
- DPO: 좋은 답(chosen) vs 나쁜 답(rejected)의 **선호**를 배우기 (6장, `sft_model`에서 시작).

### 역전파 한 번의 흐름
- loss(−log p) → `backward()`가 체인 룰로 각 가중치의 기울기 계산 → `optimizer.step()`(AdamW, lr 2e-5)이 가중치를 조금 바꿈. 3장은 이걸 4문항마다 1번, 24번 해요.

### 추론용 모델은 왜 "추론용"인가
- 체크포인트는 optimizer 상태까지 담은 **학습 이어 하기용**, `sft_model/`(`save_pretrained`)은 **답변 생성용**. 둘의 가중치 값은 같아요.
- test 12는 3장에서 안 써요. train 48 = 학습, dev 12 = 반복 확인, test 12 = 7 \~ 8장에서 마지막에 한 번.

### 모델을 바꿀 땐
- 모델 카드만 보지 말고 토크나이저로 직접 확인: 채팅 템플릿, EOS, 기본 system 프롬프트, pad 토큰, thinking 토큰, 기본 generation config.

## 실습 코드에서 직접 바꾼 점

코드는 원본과 **한 줄도 다르지 않고**(주석을 뺀 코드 비교로 확인), 셀마다 이해한 내용을 주석으로 달았어요.

**준비 · 3-1**

| 위치 | 내가 단 주석 | 메모 |
|---|---|---|
| `import ... Trainer,` | `#학습을 위한 모든코드가 쌓여있음. 오늘은 옵션만 지정해서 학습.` | 맞음. 학습 루프는 Trainer 안에 있음 |
| `TOTAL_STEPS = 24` | `# 가중치를 몇 번 바꿀것인지? 배치사이즈?` | 앞부분이 맞음. **가중치 갱신 횟수**이고 배치 크기는 아님(배치는 1 × 누적 4) |
| `padding_side = "right"` | `# 123, 142, 124, 126,` / `# 123, pad, pad, pad` | 빈칸을 뒤에 붙인다는 그림 |
| `def encode_example` | `# 이 함 수 잘봐두기.` | 4 · 5 · 6장도 같은 마스킹을 씀 |
| `end = ... + 1` | `# \n 계행문자 때문에` | EOS까지 넣고 뒤 `\n`만 버림 |
| `labels = [-100] * ...` | `# 시스템, 유저는 -100 그 이후는 유지.` | 정확히는 `assistant\n`까지 299개가 −100 |
| `def collate` | `# 인코드 example , collate는 보기(pad_sequence) 이걸이용해 batch만들기` | |
| `return {` | `#두개를 묶는행위. > 분산처리동시연산 학습의효율성` | 여러 문항을 행렬 하나로 한꺼번에 계산 |
| `shortest = min(` | `# 가장긴것 기준으로 행렬연산 기준 맞추기. 실무에선 라이브러리로 함.` | 실무는 `DataCollatorForSeq2Seq` 같은 것 |
| `cross_entropy(` | `# 손실계산.` | |
| `toy_logits[:, :-1, :]` | `#마지막껀 필요X` | 마지막 예측은 짝이 없음 |
| `toy_labels[:, 1:]` | `# 0번째가아닌 1번째 봐야해서` | 0번 예측의 정답은 1번 토큰 |

**3-2**

| 위치 | 내가 단 주석 | 메모 |
|---|---|---|
| 모델 셀 첫 줄 | `# 유효배치 = gpu개수 x per device 트레인배치사이즈 x 그래디언트 어커뮬레이션스탭. 여기에 maxsteps 곱한것과 train 데이터셋 갯수로 epoch를 계산가능.` | 4 × 24 = 96문항 ÷ 48 = **2 epoch** |
| `attn_implementation="sdpa"` | `# scaled dot attention 연산 방법론 규정.` | Scaled **Dot-Product** Attention |
| `GenerationConfig(` | `# 학습이 위주이나 중간확인을 위해 generation도 있음.` / `# 디코딩이 따로 일어나지는않지만 학습전 어떤 대답이나오는지 확인. (generate probe)` | 학습엔 안 쓰이고 전후 비교용 |
| `row["messages"][:2]` | `# 출력을 내기위해 assistant제외.` | 모범답안을 보여 주면 시험이 안 됨 |
| `**inputs` | `# 리턴 dict True라. 풀어주어서 넣어주기위해.` | `input_ids=…, attention_mask=…`로 풀어서 전달 |
| `max_steps=TOTAL_STEPS` | `# 맨위에서전역변수로 선언.` | |
| `per_device_train_batch_size=1` | `# gpu 개수 x per_device_train.. x gradient accumulation = 유효 배치수, 학습데이터까지 고려해서 epoch.` | |
| `gradient_accumulation_steps=4` | `# 4번한것을 한번에 모아서 처리.` | 기울기를 모아서 1번 갱신 |
| `weight_decay=0.01` | `# 과적합을 막기위한 규제.높을수록 많은규제.` | 머신러닝 3장 규제와 같은 생각 |
| `if state.global_step == PAUSE_STEP` | `#전역변수로 12로 세팅함.` | |
| `eval_dataset=encoded["dev"]` | `#중간중간 평가위해.` | 4갱신마다 dev loss |
| `callbacks=[StopAtTwelve()]` | `#여기서 콜백.` | |
| `reset_peak_memory_stats()` | `# 그전학습에 쓴 메모리 비워주기.` | 고칠 점: 메모리를 비우는 게 아니라 **최고값 기록을 0으로** 되돌려서 이번 구간의 최고값만 재게 함. 비우는 건 `empty_cache()` |
| `trainer.train()` | `# 실질적 학습 시작.` | |
| `first_elapsed = ...` | `# 학습 시간 재기.` | |
| `first_history = list(trainer.state.log_history)` | `# trainer state 가져와서 로그 확인?` | 맞음. 4갱신마다 쌓인 loss · eval\_loss · 학습률 · grad\_norm 딕셔너리 리스트 |

**3-4**

| 위치 | 내가 단 주석 | 메모 |
|---|---|---|
| `parameter = dict(model.named_parameters())[...]` | `#실무에선 wandb로 학습한것 남김. 랭퓨즈랑 비슷한개념.` | 둘 다 "기록 · 추적" 도구. W&B는 **학습 실험**(loss · 설정), Langfuse는 **LLM 앱 호출**(LLMOps 1장 trace) |
| `"sample_count": sample_before.numel()` | `# number elements. 가중치 개수를 구할 수 있는 함수.` / `# np.ones(2,3,4) > 2*3*4 처럼 해줌` | NumPy에선 `np.ones((2, 3, 4)).size` = 24 (모양은 튜플로) |
| `dev_after = [generate_probe(...)]` | `# 핵심함수. 모델은 만든모델. row를 넣어봄.` | 학습 전과 같은 함수 · 같은 설정 |
| `gc.collect()` · `empty_cache()` | `# 3,4줄 많이쓰임. 메모리 해제.` | `del`과 같이 써야 효과 |
| 재로딩 셀 끝 | `#체크포인트에 불러와서 트레이닝 다시.한것과 그걸 저장하고 저장한걸 불러와서 응답이같은지.` | 저장 전후 같은 응답 True |
| `report` 끝 | `# 리포트형태로 남겨 어떤 argment 로 학습했는지 확인가능.` | 4 · 7장에서 비교 근거 |
| `ARCHIVE_FOLDER` 셀 끝 | `#라이브러리를 활용하는 코드들. 트레이너. 오토모델forLM등` | |

## PPT 정리
- 3장 결과물: **학습한 `sft_model`과 기록**
  - 3-1 프롬프트는 −100, 답변과 EOS만 손실 → 370 = 299 + 71 · 배치 (2, 379)
  - 3-2 전체 가중치를 24갱신 계획으로 학습 → 4.94억 개 · checkpoint-12
  - 3-3 손실은 내려가도 업무 답은 따로 읽기 → dev 0.921 → 0.0049 · 판단 10/12
  - 3-4 재개 상태와 추론용 모델을 나눠 저장 → 12 → 24 · `sft_model.zip`
- 학습 전에는 코드 펜스 9/12, JSON만 0/12, missing 두 문항은 'answered' 한 단어. 학습 후 형식 12/12.
- 모범답안이 규칙 함수의 문장 틀 하나라 **그 틀을 빨리 외워요.** 실제 업무 데이터는 이렇게 빨리 안 내려가요.
- 현업보강 실험: 학습률 · LoRA · DPO를 바꿔도 초과 금액 오답은 남았고(DPO에서 1건만 고침), 9장에서 데이터 · 모델 크기로 다뤄요.
- 다음 4장: 같은 SFT 목표를 **LoRA(A · B만 학습)**로 해서 메모리 · 결과를 3장과 비교.
- 숙제: `sft_model.zip`(ARCHIVE\_FOLDER 셀) · `sft_report.json` 내려받아 보관(6 · 7장에 업로드), dev 12문항 `dev_before` · `dev_after` 원문 비교.

---

## 확인 문제

> 객관식 6 · 단답형 6, 섞어서 배치했어요. **정답 보기**를 누르면 열려요.

### FT3-Q1. 객관식 — 채점 대상
3장 `encode_example`에서 손실을 계산하는 위치로 맞는 것은?

1. 모범답안 토큰과 EOS
2. system · user 토큰 전부
3. 패딩 토큰
4. 답변 뒤의 `\n`

<details>
<summary>정답 보기</summary>
<p><b>1.</b> 프롬프트 299개(<code>assistant\n</code>까지)는 labels −100으로 읽기만 하고, 답변 70 + EOS 1 = 71개만 채점해요. 패딩도 −100, 뒤의 <code>\n</code>은 아예 잘라내요.</p>
</details>

### FT3-Q2. 단답형 — `+1`
`end = len(prompt_ids) + answer_ids.index(eos_id) + 1`에서 `+1`을 빼면 어떻게 되나요?

<details>
<summary>정답 보기</summary>
<p>슬라이스 <code>[:end]</code>가 끝을 포함하지 않아서 <b>EOS가 빠져요.</b> 모델이 "여기서 멈춰"를 못 배워서 답을 끝내지 못하고 이어 써요. (assert <code>labels[-1] == eos</code>가 막아 줘요)</p>
</details>

### FT3-Q3. 객관식 — 패딩 값
`collate`에서 패딩 자리를 채우는 값의 조합으로 맞는 것은? (input\_ids / attention\_mask / labels)

1. 0 / 0 / 0
2. pad ID / 1 / −100
3. −100 / 0 / pad ID
4. pad ID / 0 / −100

<details>
<summary>정답 보기</summary>
<p><b>4.</b> input은 자리만 채우는 pad ID, attention 0은 "읽지 마", labels −100은 "채점하지 마". Qwen은 pad ID가 다른 종료 ID와 같아서 값이 아니라 위치로 구분해요.</p>
</details>

### FT3-Q4. 단답형 — 두 번 밀기
labels를 `encode_example`에서 미리 한 칸 밀어 두고 Trainer에 넘기면 무슨 일이 생기나요?

<details>
<summary>정답 보기</summary>
<p>Hugging Face Causal LM이 내부에서 또 한 칸 밀어서 <b>두 칸 밀린 토큰</b>(t번째 출력이 t+2번째 토큰)을 배워요. 에러는 안 나고 조용히 틀려요. shift는 한 곳에서 한 번만 — 3 · 4 · 5장은 모델 내부, 6장 DPO만 직접.</p>
</details>

### FT3-Q5. 객관식 — 유효 배치와 epoch
배치 1, GPU 1개, `gradient_accumulation_steps=4`, train 48문항, `max_steps=24`일 때 맞는 것은?

1. 유효 배치 1, 1 epoch = 48갱신
2. 유효 배치 4, 1 epoch = 12갱신, 전체 2 epoch
3. 유효 배치 4, 1 epoch = 24갱신
4. 유효 배치 24, 전체 1 epoch

<details>
<summary>정답 보기</summary>
<p><b>2.</b> 1 × 1 × 4 = 4문항당 1갱신 → 48 ÷ 4 = 12갱신이 한 바퀴 → 24갱신은 두 바퀴.</p>
</details>

### FT3-Q6. 단답형 — StopAtTwelve
12에서 멈추고 싶은데 `max_steps=12`로 바꾸지 않고 콜백을 쓰는 이유는?

<details>
<summary>정답 보기</summary>
<p><code>max_steps</code>를 12로 바꾸면 학습률이 12에서 0이 되도록 <b>계획 자체가</b> 바뀌어요. 계획은 24로 두고 <code>should_training_stop</code>으로 멈추기만 해야, 재개했을 때 원래 24갱신 계획을 그대로 이어 가요.</p>
</details>

### FT3-Q7. 객관식 — 두 가지 체크포인트
다음 중 맞는 말은?

1. gradient checkpointing은 학습 상태를 디스크에 저장한다
2. `save_only_model=True`여야 학습을 재개할 수 있다
3. gradient checkpointing은 활성값 일부를 버렸다가 역전파 때 다시 계산해 메모리를 아낀다
4. `checkpoint-12`에는 가중치만 들어 있다

<details>
<summary>정답 보기</summary>
<p><b>3.</b> gradient checkpointing은 메모리 ↔ 시간 교환이고, 학습 체크포인트는 디스크의 폴더예요. 재개하려면 <code>save_only_model=False</code>로 optimizer · scheduler · 난수 상태까지 저장해야 해요.</p>
</details>

### FT3-Q8. 단답형 — eval\_steps
`eval_steps=4`, `gradient_accumulation_steps=4`, 배치 1이면 dev 평가는 몇 문항마다 하나요?

<details>
<summary>정답 보기</summary>
<p><b>16문항마다.</b> step은 갱신 횟수라 4갱신 × 4문항 = 16문항. "4문항마다"가 아니에요.</p>
</details>

### FT3-Q9. 객관식 — 손실과 업무 정답
슬라이드 실행에서 dev loss가 0.0049인데 over\_limit 2문항이 "한도 이하"로 틀린 이유로 가장 알맞은 것은?

1. 손실은 토큰 평균이라 몇 토큰의 실수가 나머지 70개 가까운 정답 토큰에 묻힌다
2. dev 데이터가 train과 겹쳐서
3. 학습률이 너무 커서 NaN이 나서
4. EOS를 학습하지 않아서

<details>
<summary>정답 보기</summary>
<p><b>1.</b> 손실 평가는 매 위치에 정답 앞부분을 깔아 주니(teacher forcing) 한 토큰 실수가 그 자리에서 끝나지만, 자유 생성은 그 실수를 이어 써서 결론이 뒤집혀요. 그래서 7장에서 생성 답을 규칙으로 채점해요.</p>
</details>

### FT3-Q10. 단답형 — grad\_norm
`max_grad_norm=1.0`인데 로그의 grad\_norm이 21.4로 찍혔어요. 설정이 실패한 건가요?

<details>
<summary>정답 보기</summary>
<p>아니에요. 로그에는 <b>자르기 전</b> 기울기 크기가 기록될 수 있어요. grad\_norm은 NaN이나 갑자기 폭증하는지만 보면 돼요. 그리고 <code>max_grad_norm</code>은 기울기 전체 크기를 줄이는 거지 가중치 값을 1로 자르는 게 아니에요.</p>
</details>

### FT3-Q11. 객관식 — 재개
`checkpoint-12`에서 재개할 때 맞는 것은?

1. `sft_model/`만 읽어서 새로 `train()`하면 같은 재개다
2. `max_steps=24`이므로 재개 후 24번을 더 갱신한다
3. 재개하려면 `StopAtTwelve`를 다시 넣어야 한다
4. `train(resume_from_checkpoint=…)`이 optimizer · scheduler · 난수 · step을 복원해 13\~24만 돈다

<details>
<summary>정답 보기</summary>
<p><b>4.</b> <code>max_steps</code>는 처음부터 센 전체 목표예요. <code>sft_model</code>만 읽고 새 optimizer로 시작하면 AdamW 상태가 0부터라 재개가 아니라 새 학습이에요.</p>
</details>

### FT3-Q12. 단답형 — 다시 읽기 확인
`save_pretrained` 뒤에 모델을 메모리에서 지우고 `sft_model`에서 다시 읽어 같은 문항을 생성하는 이유는?

<details>
<summary>정답 보기</summary>
<p>저장이 제대로 됐는지 확인하려고요. greedy라 같은 입력이면 같은 답이어야 해서, <b>저장 전후 같은 응답: True</b>면 6 · 7장이 이 폴더를 믿고 쓸 수 있어요. 그 전에 <code>unwrap_model</code>로 학습용 포장을 벗겨 생성 조건을 맞춰요.</p>
</details>
