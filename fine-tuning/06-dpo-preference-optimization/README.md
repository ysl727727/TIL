# 6장. DPO 선호 학습과 응답 변화 분석

> 2026-11-24 학습 기록. 파인튜닝 6일차 수업이에요. 3장 SFT가 **"이렇게 답해"**(정답 하나 따라 쓰기)를 배웠다면, 6장 DPO는 **"이 답이 저 답보다 나아"**(두 답 중 고르기)를 배워요. 4 · 5장의 LoRA · QLoRA가 "어디를 고치나"를 바꿨다면, 6장은 **"무엇을 배우나"(손실 식)**를 바꿔요. 그래서 양자화 · 어댑터를 빼고 **3장 전체 가중치 SFT 모델로 돌아가 목적함수 하나만** 바꿔요. 오늘은 `response_logps` · `dpo_terms` 두 함수와 손실 식 −log σ(m)을 한 줄씩 뜯어보는 데 시간을 가장 많이 썼어요.

> 6장의 한 문장: **좋은 답과 나쁜 답의 점수 격차가 학습 전보다 벌어지도록 −log σ(margin)을 줄이는데, 손실은 차이만 보기 때문에 loss가 0에 가까워져도 좋은 답까지 같이 무너질 수 있다. 그래서 chosen 값과 원문을 따로 읽는다.**

## 큰 흐름

```text
[준비] training_data.zip(2장) + sft_model.zip · sft_report.json(같은 3장 실행) 업로드
       정밀도는 GPU가 아니라 sft_report.json의 weight_dtype이 정함 (받은 SFT는 BF16 → L4)
6-1 응답 쌍        같은 질문 · 같은 규정 → chosen(모범답안) + rejected(판단 하나만 틀림) + 선호 이유
                  train 48행 → 48쌍 · 6유형 × 8 (과잉 보류와 근거 없는 단정을 둘 다)
6-2 목적함수        응답 토큰 log p 합 = 응답 점수 s → (s_지금 − s_기준) × β = reward
                  margin = reward_chosen − reward_rejected → loss = −log σ(margin)
6-3 이어 학습       sft_model 불러오기 → 학습 전 dev 원문 저장 → 기준 점수 [48, 2] 얼리기
                  4쌍마다 1번 · 48 × 2 ÷ 4 = 24갱신 · lr 2e-5 · β 0.1 → loss 0.00004
6-4 변화 분석       48쌍 margin 48/48 양수인데 chosen logp −0.44 → −73.65 (붕괴)
                  dev 12 형식 12/12 → 2/12, 과잉 보류 0/8은 "못 읽어서 0" · 저장 재로딩은 정확
      ↓
7장 평가 · API: 1 기준 · 3 SFT · 4 LoRA · 5 QLoRA · 6 DPO 결과를 같은 조건으로 비교
```

**3장 SFT vs 6장 DPO — 학습 대상은 같고 손실만 달라요**

| | 3장 SFT | 6장 DPO |
|---|---|---|
| 데이터 한 건 | 질문 + 모범답안 | 질문 + **좋은 답 + 나쁜 답** |
| 손실 | 답변 토큰 교차엔트로피(평균) | −log σ(margin): 두 답의 격차가 **기준보다** 벌어졌나 |
| 기준 모델 | 없음 (정답 자체가 기준) | 학습 전 SFT를 고정 (reference) |
| 시작점 | 공개 Qwen2.5-0.5B | 3장 SFT 결과 |
| 학습 대상 | 전체 494,032,768개 | 전체 494,032,768개 (같음) |
| 시작 loss | 모델마다 다름 (3장 dev 0.92) | 항상 0.6931 (= ln 2) |
| 한마디 | 정답지 따라 쓰기 | 두 답안 중 고르기 |

## 학습 목표
- 선호쌍을 "같은 입력, 판단 하나만 다른 두 답"으로 만드는 이유와, 과잉 보류 · 근거 없는 단정을 **둘 다** 넣는 이유를 설명한다.
- 응답 점수를 토큰 log p의 **합**으로 만드는 이유(곱의 log)와 `response_logps`의 인덱싱(한 칸 어긋나기 · mask · scatter\_add)을 설명한다.
- reward · margin · loss를 계산 순서대로 말하고, **두 번의 마이너스**가 각각 왜 붙는지 설명한다.
- β(채점 기준)와 learning rate(보폭)를 구분한다.
- loss가 0에 가까워도 chosen이 무너질 수 있음을 숫자(chosen reward · logp)와 원문으로 확인한다.
- 저장 재현(같은 파일 → 같은 답)과 학습 재현(다시 배워도 같은 답)을 구분한다.

## 실습 환경
- 노트북: `dpo.ipynb` (28셀, 셀 번호는 슬라이드처럼 위에서부터 1번). 보강 `dpo_wandb.ipynb`(W&B 기록 셀 추가) · 통합 실습 `finetuning_ch06_practice`.
- 입력 파일: 2장 `training_data.zip` + 3장 `sft_model.zip` · `sft_report.json`. **둘은 같은 3장 실행에서 나온 짝**이어야 해요.
  - 받은 `sft_report.json`은 **L4 · BF16**이고 `data_sha256`이 `training_data`와 일치해요. `sft_model.zip`도 BF16이에요.
  - BF16 입력이라 **T4에서는 셀 15에서 멈춰요** → L4로 실행.
  - 셀 15는 `source_sft` · `dpo_model` · `dpo_report.json`이 이미 있어도 멈춰요. lr 2e-6 비교는 **런타임 재시작 · 빈 폴더 · 처음부터**.
- 슬라이드 숫자는 강사 PC(RTX 5060 Laptop · BF16 · seed 42 · dev 12 · 1회) 기준이고, T4 · L4는 미실측이에요.

## 실습 파일

| 파일 | 하는 일 | 상태 |
|---|---|---|
| `dpo.ipynb` | 6-1 선호쌍 48 → 6-2 손실 함수 → 6-3 DPO 24갱신 → 6-4 변화 분석 · 저장 재로딩 | 📘 수업 · 코드 질문 정리 (Colab L4 실행 기록 남음) |
| `dpo_wandb.ipynb` | 학습 셀 아래에 W&B 기록 셀만 붙여 lr 2e-5 · 2e-6 · 1e-6 겹쳐 보기 | 📘 슬라이드 값으로 정리 |
| `finetuning_ch06_practice` | 통합 실습 | ⬜ 아직 |
| `dpo_report.json` · `dpo_model.zip` | 보고서 + 추론용 모델 (7장 입력) | ⬜ 내려받기 남음 |

---

## 핵심 이론

### 6-1. 선호 이유를 응답 쌍으로 표현하기

**한 쌍의 모양: 입력은 같고 판단만 달라요**
```text
질문  다온팀 출장에서 1박 80,000원인 방을 예약하려면 무엇을 해야 하나요?
규정  한도 1박 85,000원 · 이하는 사전 승인 불필요 · 초과는 예약 전 서면 승인

chosen   {"status": "answered", "answer": "...80,000원은 한도 이하이므로 사전 승인이 필요하지 않습니다.", "citations": ["policy03-v1"]}
rejected {"status": "abstained", "answer": "제공된 근거로는 ... 확인할 수 없습니다. 담당자에게 확인하세요.", "citations": []}
선호 이유: 숙박비 규정이 충분한데도 답하지 않는 과잉 보류를 피합니다.
```
둘 다 **형식은 맞아요.** 다른 건 판단 하나예요. 그래야 모델이 형식이 아니라 판단을 비교해서 배워요.

**여섯 유형, 잘못은 하나씩 (유형마다 8쌍 = 48쌍)**

| 유형 | chosen | rejected에 넣은 잘못 | 피하려는 행동 |
|---|---|---|---|
| below | 한도 이하 · 승인 불필요 | 보류(abstained) | 과잉 보류 |
| boundary | 한도와 같음 · 불필요 | 초과라고 답함 | 경계값 오판 |
| over\_limit | 초과 · 예약 전 서면 승인 | 한도 이하라고 답함 | 초과 놓침 |
| updated | 개정 한도로 · 불필요 | 초과라고 답함 | 개정 규정 미반영 |
| missing | 보류 · 담당자 확인 | 지원되지 않는다고 단정 | 근거 없는 단정 |
| irrelevant | 보류 · 담당자 확인 | 숙박비 규정을 다른 경비에 적용 | 엉뚱한 근거 사용 |

- **과잉 보류와 근거 없는 단정을 둘 다 넣어요.** "보류하지 마"만 가르치면 근거 없이 다 답해 버려요.
- rejected는 실제 사람이 고른 선호가 아니라 **교재용으로 일부러 틀리게 만든 답**이에요. 라벨이 틀리면 틀린 선호도 그대로 배워요.

**`make_pair` (셀 8): 정답지를 복사해서 한 군데만 틀리게**
```python
prompt = row["messages"][:2]          # [system, user] = 질문 + 규정 → 두 답이 공유
chosen = row["messages"][2]["content"]  # 2장 모범답안 = 좋은 답
rejected = dict(json.loads(chosen))   # 복사본을 고쳐야 chosen이 안 바뀜
# below → 보류 답으로 통째로 교체 / boundary · over_limit · updated → 판단 문장 한 줄 바꿔치기
assert old in answer["answer"]        # 바꿀 문구가 실제로 있어야 함 (엉뚱한 오답 방지)
assert chosen != rejected_text        # 두 답이 같으면 비교할 게 없음
pairs = [make_pair(row) for row in records["train"]]   # train 48 → 48쌍 (test는 열지도 않음)
```

### 6-2. 기준 모델과 선호 목적함수 이해하기

```text
s      = 응답 토큰 log p의 합                       (답안 전체를 쓸 확률의 log)
reward = β × (s_지금 − s_기준)                       (기준 = 학습 전 SFT, 얼려 둠)
m      = reward_chosen − reward_rejected            = β[(s⁺_θ − s⁻_θ) − (s⁺_ref − s⁻_ref)]
L      = −log σ(m)
```

#### ① 응답 점수: `response_logps` (셀 12)
```python
def response_logps(logits, labels):              # logits [B,T,V], labels [B,T]
    targets = labels[:, 1:]                      # 정답 앞 1칸 버림 (위치 t가 t+1을 맞히니까)
    mask = targets.ne(-100)                      # 채점할 칸 = -100이 아닌 칸 (응답 + EOS)
    token_logps = -F.cross_entropy(
        logits[:, :-1, :][mask].float(),         # 예측 뒤 1칸 버림, 채점 칸만, FP32로
        targets[mask], reduction="none")         # 칸마다 따로 (평균 X)
    owners = mask.nonzero(as_tuple=False)[:, 0]  # 각 칸이 몇 번째 응답 것인지 (행 번호)
    sums = torch.zeros(logits.shape[0], device=logits.device
           ).scatter_add(0, owners, token_logps) # 응답별 저금통에 더하기
    return sums, mask.sum(dim=1)                 # (응답별 점수 합, 응답별 토큰 수)
```
**쉽게:** 받아쓰기 채점이에요. 질문 · 패딩 칸(−100)은 빼고 **답 칸에서만** "이 글자일 거라고 얼마나 확신했나"(log p)를 구해서 답안별로 더해요.

toy로 한 줄씩 찍어 본 결과 (B 2 · T 4 · V 6, 후보 6개가 모두 1/6):
```text
labels      = [[-100, -100, 2, 5], [-100, -100, 2, -100]]
targets     = [[-100, 2, 5], [-100, 2, -100]]          (2, 3)
mask        = [[F, T, T], [F, T, F]]
logits[:, :-1, :][mask]  → (3, 6)      targets[mask] → [2, 5, 2]
token_logps = [-1.7918, -1.7918, -1.7918]               # = log(1/6)
owners      = [0, 0, 1]
sums        = [-3.5835, -1.7918]                        # 합: 긴 답이 더 낮음
mask.sum(1) = [2, 1]      평균 = [-1.7918, -1.7918]      # 평균: 둘이 같음
```

- **왜 합인가:** 답안 전체 확률 = 토큰 확률의 **곱**, log를 씌우면 **합**이에요. 평균은 "글자 하나당 실력"이라 다른 목적함수가 돼요(DPO 원논문도 합).
- **읽는 감각:** 71토큰 답의 합이 −0.11이면 토큰당 약 99.8%(exp(−0.11/71)), −66.53이면 토큰당 약 39%로 문장이 깨지는 수준이에요.

#### ② 손실: `dpo_terms` (셀 12)
```python
def dpo_terms(policy_logps, reference_logps):    # 둘 다 [chosen, rejected]
    log_ratios = policy_logps - reference_logps.detach()   # 학습 전보다 얼마나 변했나 (기준엔 기울기 X)
    rewards = BETA * log_ratios                  # β 곱하기 = 암묵적 reward
    margin = rewards[0] - rewards[1]             # chosen 변화 − rejected 변화 = m
    return -F.logsigmoid(margin), margin, rewards   # L = −log σ(m), 수치 안정 버전
```

| margin | σ(margin) = 좋은 답이 이길 확률 | loss = −log σ | 미는 힘 1 − σ |
|---|---|---|---|
| −2 | 0.119 | 2.127 | 0.88 |
| **0 (시작)** | **0.500** | **0.6931 (= ln 2)** | **0.50** |
| 0.2 | 0.550 | 0.5981 | 0.45 |
| 2 | 0.881 | 0.1269 | 0.12 |
| 5 | 0.993 | 0.0067 | 0.007 |

- 기울기 dL/dm = −(1 − σ(m))는 **항상 음수** → m을 키우면 loss는 언제나 줄어요. 1장의 `p − y`와 같은 모양이에요.
- `logsigmoid`를 한 번에 쓰는 이유: m이 아주 음수면 σ가 0으로 뭉개져 log(0) = −∞가 돼요.

#### ③ 함정: 차이만 보고 절대값은 안 봐요 (β 0.1 손계산)

| chosen logp 변화 | rejected logp 변화 | margin | loss | 읽기 |
|---|---|---|---|---|
| 0 | −20 | +2 | 0.1269 | 나쁜 답만 내려감 · 바라는 모양 |
| −10 | −30 | +2 | 0.1269 | **좋은 답도 내려감 · 과최적화** |

#### ④ β와 learning rate는 달라요

| | β = 0.1 | learning rate = 2e-5 |
|---|---|---|
| 정체 | **채점 기준** (손실 식 안) | **보폭** (optimizer 안) |
| 코드 위치 | `rewards = BETA * log_ratios` | `AdamW(lr=LEARNING_RATE)` |
| 바꾸면 | reward · margin · loss의 눈금과 기울기 | 갱신 한 번의 가중치 이동량 |
| margin 3에 필요한 logp 차이 변화 | 0.1이면 30, 1이면 3 | 관계없음 |

β가 다른 실행끼리는 reward · margin 눈금이 달라서 숫자를 그대로 비교하면 안 돼요.

#### ⑤ 토큰화: `encode_response` · `collate_pair` (셀 13)
```text
input_ids: [system ... user(질문 + 규정) ... assistant 시작] [답 토큰 ... EOS]
labels   : [-100   ...  -100                ...  -100      ] [답 토큰 ... EOS]
```
- 프롬프트만 / 프롬프트 + 답을 **두 번 토큰화**해서 앞부분이 같은지 assert → 경계를 믿을 수 있어요(2장과 같은 방법). EOS까지만 자르고 뒤 템플릿 개행은 버려요.
- chosen · rejected를 한 배치 **[2, T]**로 패딩: `input_ids`는 pad ID, `attention_mask`는 0, `labels`는 −100(3장 세 값과 같음).

### 6-3. SFT 결과에서 DPO 이어 학습하기

```text
셀 15 SFT 불러오기 → 셀 16 학습 전 dev 원문 저장 → 셀 17 기준 점수 48쌍 얼리기 → 셀 19 모델 직접 갱신(24번)
```
- 셀 15 확인: CUDA · BF16 지원, ZIP 경로가 전부 `sft_model/`, 토크나이저 어휘 · 템플릿이 기반 모델과 같은지, **dropout 0**(같은 가중치면 점수가 매번 같아야), 전체 494,032,768개가 학습 대상(풀 DPO).
- 셀 16 `generate_response`: 질문만 넣고 모델이 쓴 **원문 그대로** 저장 + EOS 종료 · 길이 제한 기록. 3장 보고서 원문과 다른 건수 0 → 입력 짝이 맞음.
- 셀 17 기준 점수: 학습 전 SFT로 48쌍 점수를 **한 번만** 재서 `reference_scores` [48, 2] 숫자로 얼려요. **모델을 두 개 올릴 필요가 없어요.**
```text
첫 기준 log-prob: [-0.1136, -39.3067]     # chosen은 거의 확신, rejected는 매우 낮음
초기 margin / loss: 0.0  0.6931            # policy = reference라서
```

**학습 반복문 (셀 19): 4쌍 모아 1번, 총 24번**
```python
for epoch in range(EPOCHS):                                    # 2회, 회차마다 순서 섞기
    for position, index in enumerate(order, start=1):
        scores = pair_logps(model, pairs[index])               # 지금 모델의 [chosen, rejected]
        loss, margin, rewards = dpo_terms(scores, reference_scores[index].to(model.device))
        (loss / ACCUMULATION).backward()                       # 1/4씩 기울기 쌓기
        if position % ACCUMULATION == 0:                       # 4쌍마다
            clip_grad_norm_(..., max_norm=1.0)  →  optimizer.step()  →  optimizer.zero_grad()
```

| 설정 | 값 |
|---|---|
| EPOCHS · ACCUMULATION | 2 · 4 → 48 × 2 ÷ 4 = **24갱신** |
| optimizer · weight\_decay · max\_norm | AdamW · 0.01 · 1.0 |
| scheduler | **없음** (3\~5장의 선형 감소와 다름) |
| 학습 시간 · 최대 메모리 | 16초 · 4.49 GiB (gradient checkpointing) |

**loss는 성공, chosen은 추락 (교안 lr 2e-5 · 갱신 직전 네 쌍 평균)**

| 갱신 | loss | margin | chosen reward | rejected reward |
|---|---|---|---|---|
| 1 | 0.693147 | 0.00 | 0.00 | 0.00 |
| 4 | 2.517169 | 5.46 | **−6.54** | −12.00 |
| 24 | 0.000041 | 11.54 | **−5.73** | −17.27 |

- chosen reward −5.73 = 0.1 × 변화 → **좋은 답의 logp가 학습 전보다 약 57 떨어짐.** 나쁜 답이 더 떨어져서 margin만 커졌어요. ③의 "과최적화" 줄이 그대로 나왔어요.
- 갱신 4의 loss 2.517이 시작값보다 큰 이유: 초반 갱신이 일부 쌍을 margin < 0 쪽으로 밀었어요.

**(보강) W&B로 lr 비교 — 24번째 갱신**

| lr | loss | margin | chosen reward | rejected reward |
|---|---|---|---|---|
| 2e-5 교안 | 0.000041 | 11.54 | −5.73 | −17.27 |
| 2e-6 | 0.516517 | 0.59 | **+0.02** | −0.57 |
| 1e-6 | 0.623265 | 0.16 | +0.01 | −0.16 |

lr을 1/10로 줄이면 loss는 덜 줄지만 **chosen이 0 근처에서 유지돼요.** 학습 코드는 그대로 두고 기록 셀만 붙이고, API 키는 코드에 쓰지 않아요.

### 6-4. 선호 변화와 과잉 보류 분석하기

**학습한 48쌍: 48/48 양수인데 좋은 답은 붕괴**

| | 학습 전 (SFT) | 2e-5 교안 | 2e-6 |
|---|---|---|---|
| margin 양수 | 0/48 (전부 0) | 48/48 | 48/48 |
| 평균 loss | 0.6931 | 0.00002 | 0.3269 |
| 첫 쌍 chosen logp | −0.11 | **−66.53** | −0.11 |
| 48쌍 평균 chosen logp | −0.44 | **−73.65** | −0.36 |
| 48쌍 평균 rejected logp | −37.62 | −236.31 | −55.76 |

margin 양수 = "기준보다 차이가 나아졌다"일 뿐, chosen 확률이 올랐다는 뜻이 아니에요.

**dev 12 자유 생성 (`summarize_behavior`)**

| | DPO 전 (SFT) | 2e-5 교안 | 2e-6 |
|---|---|---|---|
| 형식 통과 | 12/12 | **2/12** | 12/12 |
| 과잉 보류 (답할 수 있는 8개) | 0/8 | 0/8 | 0/8 |
| 근거 없는 answered (근거 부족 4개) | 0/4 | **4/4** | 0/4 |
| status를 못 읽음 | 0 | **8** | 0 |

- 2e-5의 "과잉 보류 0/8"은 **status를 못 읽은 8개가 어느 쪽에도 안 세져서 생긴 0**이에요.
- `inspect_response`는 원문을 고쳐 주지 않고 그대로 파싱해서 ① 형식 ② status만 세요. 금액 비교나 이유가 맞는지는 채점하지 않아요 → **원문을 읽어야 해요.**
```text
policy01-over_limit · DPO 후   "...예약 전 서면 승인을 받아 보실 수 없습니다.supports#query}"
policy05-below · DPO 후        "...출장소로 출장예약 하지没有 사전 승인이 ... therefore the answer is policy05-v1. [3]"
```

**저장 · 재로딩 (셀 24)**: 저장 전후 마지막 위치 logits `torch.equal` + 생성 원문 일치 → 최대 차이 0.0 · True. 모델 ZIP 0.931 GiB.
- **저장 재현**(같은 파일 → 같은 답)은 정확했어요. **학습 재현**(다시 배워도 같은 답)은 같은 2e-5에서 형식 1/12 · 0/12 · 2/12로 흔들렸어요. 무너진 모델은 작은 수치 차이에도 결과가 달라져요.
- `dpo_model.zip`은 **추론용**이에요(optimizer 상태 없음, 학습 재개용 아님).

---

## 질문과 새로 알게 된 점

### 큰 줄기: 두 축과 조합

| 축 | 질문 | 해당 |
|---|---|---|
| **무엇을 배우나** (목표 · 데이터 · 손실) | 정답을 따라 쓰나, 둘 중 고르나 | **SFT** / **DPO** |
| **어디를 고치나** (방법 · 메모리) | 전부, 옆길만, 압축 몸통 + 옆길 | **풀** / **LoRA** / **QLoRA** |

```text
              풀 파인튜닝     LoRA          QLoRA
SFT           3장            4장           5장
DPO           6장(교안)      DPO+LoRA      DPO+QLoRA

① SFT로 형식 · 말투 잡기 (풀 / LoRA / QLoRA 중 하나)
② 그 SFT 결과가 두 역할: reference(얼려 둔 기준) + policy(여기서 출발, 시작할 땐 같음)
③ DPO로 판단 다듬기 (풀 / LoRA / QLoRA 중 하나)
```

**학습 한 바퀴: LoRA DPO vs LoRA SFT**

| 단계 | LoRA DPO | LoRA SFT |
|---|---|---|
| ① 입력 | 질문 + 좋은 답 + 나쁜 답 | 질문 + 정답 1개 |
| ② 기준 | reference(SFT, 어댑터 끔)로 학습 전 격차 | 없음 (정답 자체가 기준) |
| ③ 지금 | policy(SFT + 어댑터)로 지금 격차 | policy(원래 모델 + 어댑터)로 정답 토큰 확률 |
| ④ 벌점 | margin = β × (지금 격차 − 학습 전 격차) → −log σ(margin) | 토큰마다 −log p(정답)의 평균 |
| ⑤ backward | 기울기가 몸통을 지나 A · B까지 | 같음 |
| ⑥ step | A · B만 바뀜 | 같음 |

| | policy | reference | 바뀌는 것 |
|---|---|---|---|
| 풀 SFT (3장) | 모델 자체 | 없음 | 전체 가중치 |
| LoRA SFT (4장) | 모델 + 어댑터 | 없음 | A · B |
| QLoRA SFT (5장) | 4비트 몸통 + 어댑터 | 없음 | A · B |
| 풀 DPO (6장) | SFT 모델 자체 | 학습 전 점수를 **미리 숫자로 저장** | 전체 가중치 |
| LoRA DPO | SFT + 어댑터 | 학습 전 SFT (**어댑터 끄면 됨**) | A · B |
| QLoRA DPO | 4비트 SFT + 어댑터 | 4비트 SFT (어댑터 끔) | A · B |

### DPO 손실 계산 순서 (내가 설명한 것 + 다듬은 내용)

> 처음엔 "CE로 −log p 점수를 만들고 그다음 −sigmoid?"라고 이해했어요. 큰 순서는 맞지만 ① CE 결과는 손실이 아니라 **점수 재료**이고 ② 그 사이에 reference 비교 · margin 단계가 있고 ③ 마지막은 −sigmoid가 아니라 **−log sigmoid**예요.

**① CE → 토큰마다 −log p**
- softmax로 V개 후보에 0\~1 확률(합 1)을 매기고 정답 토큰의 p를 꺼내요(실제로는 log\_softmax로 한 번에).
- 문장 확률은 토큰 확률의 곱이라 0에 수렴 → **log**로 곱을 합으로 바꿔요.
- p는 0\~1이라 **log p는 항상 0 이하**(−∞ \~ 0)예요. 작을수록(더 음수일수록) 맞힐 확률이 낮아요.
- optimizer는 경사하강법으로 손실을 **줄이는 방향**으로만 움직여요. 그래서 CE는 **−를 붙여 −log p**(잘 맞힐수록 0에 가까운 벌점)로 줘요.

| | 범위 | 잘 맞힐수록 |
|---|---|---|
| p | 0 \~ 1 | 1에 가까워짐 |
| log p | −∞ \~ 0 | 0에 가까워짐 (커짐) |
| −log p | 0 \~ +∞ | 0에 가까워짐 (작아짐) |

**② 다시 − → 토큰 log p (점수)**
- DPO는 CE를 손실로 쓰지 않고 **log p를 꺼내는 도구**로만 써요. 그래서 −를 한 번 더 붙여 되돌려요: `token_logps = -F.cross_entropy(...)`

**③ 응답 토큰 log p 합 → 응답 점수 s**
- chosen · rejected 각각, policy · reference 둘 다 → 점수 4개.

**④ (policy − reference) × β → reward**
- reward = "학습 전보다 이 답의 점수가 **얼마나 올랐나**". reference는 `.detach()`로 고정이라 움직이는 건 policy뿐이에요.
- **왜 reference − policy가 아닌가:** 계산이 불가능해서가 아니라, reward가 "오른 양"이어야 뒤의 −log σ(chosen − rejected)와 방향이 맞아요. 반대로 빼면 좋아진 모델의 손실이 오히려 커지고 학습이 거꾸로 가요.

| (ref [chosen −4, rejected −3] → policy [−3, −4]) | policy − ref | ref − policy |
|---|---|---|
| reward (× 0.1) | [+0.1, −0.1] | [−0.1, +0.1] |
| margin | **+0.2** | **−0.2** |
| loss | **0.598** (0.693보다 줄어듦 ✓) | **0.798** (늘어남 ✗) |

**⑤ reward\_chosen − reward\_rejected → margin**
- margin은 확률이 아니라 **격차**(−∞ \~ +∞)예요.
- **학습은 이 격차가 커지는 방향으로 가요.** −log σ(m)은 m이 클수록 작아지는 식이라 손실을 줄이는 것 = margin을 키우는 것이에요. 틀리고 있으면(m 작음) 1 − σ가 커서 세게, 잘 이기고 있으면 살살 고쳐요.
- 손실은 **차이만** 봐서, chosen · rejected가 둘 다 떨어져도 격차만 벌어지면 손실은 줄어요(2e-5: chosen reward −5.73 · 형식 2/12).

**⑥ σ(margin) → 좋은 답이 이길 확률 (0\~1)** — margin 0이면 0.5(학습 시작).

**⑦ −log σ(margin) → loss**
- **곱 → 합:** 48쌍을 모두 맞힐 확률 = σ(m₁) × σ(m₂) × … × σ(m₄₈). 곱하면 0에 수렴하니 log로 합으로 바꿔요 → 쌍마다 −log σ(m)을 더하거나 평균.
- **틀릴수록 세게:** log 없이 −σ(m)을 쓰면 많이 틀릴 때 기울기가 사라져요.

| margin | −σ(m)의 기울기 크기 σ(1−σ) | −log σ(m)의 기울기 크기 1−σ |
|---|---|---|
| −4 (크게 틀림) | **0.018 (거의 안 고침)** | **0.98 (세게 고침)** |
| 0 | 0.25 | 0.50 |
| +4 (잘 맞힘) | 0.018 | 0.018 |

- **−를 붙이는 이유:** log σ(m)은 0 이하이고 클수록 좋은 값이라, 경사하강법이 줄이는 방향으로 학습하도록 뒤집어요. 시작 loss는 0.693이에요.

**마이너스가 두 번 나오는 이유**

| 위치 | 방향 | 이유 |
|---|---|---|
| ② `-F.cross_entropy(...)` | 벌점(−log p) → 점수(log p) | CE가 손실용이라 −가 붙어 나옴 → 상쇄해서 점수 재료로 |
| ⑦ `-F.logsigmoid(margin)` | 점수(log σ) → 벌점(−log σ) | optimizer가 줄이는 방향 = 좋은 답 쪽이 되게 |

> **"①에서 −붙이고 ②에서 다시 붙일 거면 처음부터 안 붙이면 되지 않나?"** → 개념으로는 맞아요. ①의 −는 우리가 붙인 게 아니라 `F.cross_entropy`가 원래 −log p를 돌려주는 함수라서 생긴 거예요. `logits.log_softmax(-1).gather(-1, targets.unsqueeze(-1)).squeeze(-1)`로 정답 칸을 바로 꺼내면 −없이 같은 값이 나와요(TRL 같은 라이브러리가 이 방식). 노트북은 한 줄로 짧아서 CE를 썼어요. 그래서 **진짜 의미 있는 마이너스는 ⑦ 하나**예요.

> **한 줄:** CE로 log p를 꺼내 응답 점수를 만들고, reference보다 오른 만큼(reward)의 격차(margin)를 σ로 확률로 바꾼 다음, −log를 씌워 손실로 만들어요. 경사하강법은 이 손실을 줄이면서 margin을 키워요.

### CE와 sigmoid는 어디에 쓰이고, 교차엔트로피(SFT)와 DPO 손실은 뭐가 다른가

| | cross\_entropy | sigmoid (logsigmoid) |
|---|---|---|
| 위치 | `response_logps` | `dpo_terms` |
| 후보 수 | V개 (약 15만 단어) | 2개 (좋은 답 vs 나쁜 답) |
| 출력 | 토큰마다 log p(정답) | −log P(좋은 답 승) = loss |
| 역할 | 응답 점수의 **재료** (DPO에선 손실 아님) | **손실** |
| SFT에서는 | 이게 곧 손실 | 안 씀 |

- 후보가 여러 개면 softmax, **두 개면 sigmoid**: softmax([a, b])의 첫 칸 = e^a / (e^a + e^b) = σ(a − b).
- 둘 다 −log(확률) 꼴이에요. 차이는 **무엇의 확률이냐** — SFT는 15만 후보 중 정답 토큰(**절대**), DPO는 두 답 중 좋은 답이 이길 확률(기준 대비 **상대**). 그래서 SFT는 정답을 외우기만 할 수 있고, DPO는 좋은 답까지 같이 무너질 수 있어요.

### 기호: α, β, σ
- **β** = margin 배율 0.1 (채점 기준, lr과 다름) · **σ** = sigmoid (알파 아님) · **α**는 DPO 식에 없음(LoRA의 `lora_alpha`가 따로 있을 뿐).

### 응답 점수를 왜 만드나
- DPO는 "좋은 답을 나쁜 답보다 얼마나 더 쓰려고 하나"를 비교해요. 두 답은 토큰도 길이도 달라서 **토큰끼리는 비교할 수 없어요** → 답마다 숫자 하나(총점)로 요약해요.
- 그 숫자 = log P(모델이 이 답을 통째로 쓸 확률). 학습 전 SFT로도 같은 방식으로 재서(`reference_scores`) 빼면 "얼마나 변했나"가 나와요.

### logits는 [B, T, V], labels는 [B, T]인 이유
- logits = 위치마다 다음 단어를 **단어장 전체에 점수**로 냄 → V 축 있음. labels = 위치마다 정답은 **하나**라 번호만 → V 축 없음, 채점 안 할 자리는 −100.
- 비유: logits는 문제마다 보기 15만 개 전부에 매긴 확신 점수표, labels는 정답 번호만 적힌 답안지.

### 한 칸 어긋나게 자르기와 `(3, 6)` · `[2, 5, 2]` (사이드)
```text
예측(logits 위치) → 맞힐 정답(labels 위치)
      0 → 1 (-100)     1 → 2 (2)     2 → 3 (5)     3 → (없음, 버림)
```
- `logits[:, :-1, :]`(마지막 자리 빼기) → (2, 3, 6), `labels[:, 1:]`(첫 자리 빼기) → (2, 3).
- mask (2, 3)가 앞 두 축(B, T−1)에서 칸을 고르고 V 축은 통째로 따라와요 → `(3, 6)`과 `[2, 5, 2]`, 같은 순서로 뽑아서 **줄끼리 짝이 맞아요.**

### labels의 −100 · `mask = targets.ne(-100)`이면 마스크가 아닌 자리 아닌가? (사이드)
- **−100 = "여긴 채점하지 마"** (프롬프트 · 패딩). cross\_entropy의 `ignore_index=-100`, 3장 SFT와 같은 원리.
- `ne` = not equal → **True = 응답 토큰**. 여기서 mask는 "가리는 것"이 아니라 **"남길 자리를 고르는 체"**예요. 가림 표시는 labels의 −100 쪽. 머릿속으로 `keep` · `is_answer`로 읽으면 돼요.

### owners · scatter\_add, 그리고 열은 왜 필요 없나
- token\_logps가 **한 줄로 섞여서** 어느 응답 것인지 정보가 없어요. `mask.nonzero()`는 True 칸 좌표 [행, 열]을 token\_logps와 같은 순서로 줘요 → `[:, 0]` 행 번호 = **주인 이름표** `[0, 0, 1]`.
- `zeros(B).scatter_add(0, owners, token_logps)` = 이름표 보고 저금통에 더하기: [0, 0] → [−1.79, 0] → [−3.58, 0] → [−3.58, −1.79]. 실제로는 [chosen, rejected] 2통.
- **열이 필요 없는 이유:** 열은 `[mask]`로 예측과 정답을 짝지을 때 **이미 썼어요.** 남은 일은 응답별로 더하기뿐이고 더하기는 위치와 상관없어요(반별 총점엔 "몇 반"만 필요).

### DPO에서 system · user는 어디에 들어가나
- `make_pair`: `prompt = row["messages"][:2]`([0] system, [1] user = 질문 + 규정), chosen · rejected가 **같은 prompt 공유**.
- `encode_response`: **input\_ids에는 들어가고**(조건을 읽어야 답 확률을 계산), **labels는 −100**(점수에선 빠짐).
- `generate_response`: `messages[:2]`만 넣고 답은 모델이 써요.

### LoRA는 어떻게 적용되나 · "어댑터에 DPO 적용?"
- 교안은 **풀 DPO**예요(전체 `requires_grad`, AdamW에 `model.parameters()` 전체).
- DPO = 무엇을 배우나, LoRA = 어디를 고치나라서 독립이에요. **"LoRA로 DPO 한다"**가 맞는 표현이에요. 어댑터에 DPO를 적용하는 게 아니라, **모델 전체의 출력으로 DPO 손실을 계산하고 그 손실로 고치는 게 어댑터뿐**이에요.
- **reference가 공짜:** B = 0 시작이라 처음엔 policy = reference, 몸통이 얼어 있어서 **어댑터를 끄면(`model.disable_adapter()`) = reference**. 풀 DPO는 전체가 바뀌니 학습 전 점수를 미리 숫자로 저장해야 해요.
- 바꿀 곳 스케치: SFT 로드 뒤 `get_peft_model`(`lora_dropout=0.0`), AdamW엔 `requires_grad`인 것만, 가중치 검사는 `lora_B`, 저장은 어댑터만. lr은 다시 골라야 하고, LoRA가 붕괴를 막아 주지는 않아요.
- 내 이해 확인 ("reference 기준, policy = reference + 어댑터, 출력 차이로 가중치 수정?") → 거의 맞음. ① 수정되는 건 **A · B뿐**(몸통은 끝까지 안 바뀌어서 reference가 고정으로 남음) ② 출력을 바로 빼지 않고 각자 "좋은 답 − 나쁜 답" 격차를 먼저 구한 뒤 **격차끼리** 비교.

### SFT는 가중치를 바꾸는 건데, LoRA · QLoRA는 원래 가중치를 안 바꾸잖아?
- SFT의 정의는 **"질문 + 모범답안을 교차엔트로피로 따라 쓰게 학습"**이에요. 어떤 숫자를 고칠지는 정의에 없어요. 풀은 W를, LoRA · QLoRA는 **A · B라는 가중치**를 고쳐요.
- 모델 전체로 보면 실제로 쓰는 가중치가 W' = W + (α/r)·BA로 바뀐 거예요. `merge_and_unload()`로 합치면 진짜 하나의 모델이 돼요.

### QLoRA는 base model만 양자화하는 차이? · scale은?
- 네. **얼려 둔 몸통의 Linear만 NF4로 저장**하고 계산은 BF16(T4는 FP32), 임베딩 · Norm · A · B는 FP32예요. prepare 단계가 하나 늘고 느려지고, 복원도 같은 4비트로 해야 해요. DPO + QLoRA면 reference = 4비트 SFT(어댑터 끔).
- **양자화 scale**(가중치 64개마다 1개, 번호를 원래 크기로 되돌림, 학습 안 됨)과 **LoRA scale α/r**(어댑터 효과의 세기, 설정 하나)은 이름만 비슷한 다른 것이에요.

### SFT 단계와 DPO 단계의 방법 조합 · "SFT로 다시 하면 재학습?"

| SFT | DPO | 메모 |
|---|---|---|
| 풀 | 풀 | 교안 (3장 → 6장) |
| 풀 | LoRA / QLoRA | SFT를 얼리고 어댑터로 DPO |
| LoRA | LoRA | SFT 어댑터를 먼저 merge한 뒤 새 어댑터 |
| QLoRA | QLoRA | 큰 모델일 때, reference도 4비트 기준 |

| 이름 | 출발점 | 예 |
|---|---|---|
| 재개 (resume) | 중단된 체크포인트 | 3장: 12에서 멈췄다가 24까지 |
| 이어 학습 / 추가 SFT | 끝난 SFT 결과 | SFT 모델에 새 데이터로 한 번 더 (reference 필요 없음) |
| 재학습 (처음부터) | 공개 원본 모델 | Qwen부터 다시 SFT |

같은 데이터로 또 하면 epoch를 늘린 것과 같아서 과적합 위험, 새 데이터만 쓰면 예전 걸 잊을 수 있어서 보통 섞어요.

### 5장 복습: 2비트 예제에서 서로 다른 값인데 복원값이 같아지는 이유 (사이드)
- 2비트는 칸이 4개(−2, −0.667, +0.667, +2)뿐이고 **가장 가까운 칸**에 넣어요. 경계는 칸 사이 중간(−1.333, 0, +1.333).
- 번호 `[0, 1, 2, 2, 3]`의 세 · 네 번째 값은 둘 다 0 \~ 1.333이라 둘 다 0.667로 복원돼요. 칸 번호만 저장하니 원래 차이는 사라져요(최대 오차 0.633). 4비트 16칸이면 0.100.

---

## PPT 정리
- 6장 결과물: **`dpo_report.json`(설정 · 기록 · 48쌍 변화 · dev 전후 원문 · 집계 · 재로딩)과 `dpo_model.zip`(추론용)**, 그리고 `preference_pairs.jsonl` · `reference_scores.json` · `dpo_learning.png`
  - 6-1 같은 입력, 판단 하나만 다른 두 답 → 48쌍 · 유형 6개 · 선호 이유
  - 6-2 기준보다 차이가 벌어졌는지 손실로 → logp → reward → margin → loss
  - 6-3 SFT에서 24번, 기준은 고정 → loss · margin · **chosen reward**
  - 6-4 점수와 자유 생성을 따로 → 형식 · 보류와 단정 · **원문**
- 7장 전에: `dpo_report.json`과 SFT 입력(`sft_model.zip`) 보관(7장 다섯 방법 비교), 설정 바꿔 보기 lr **2e-6**(런타임 재시작 · 빈 폴더 · 처음부터).

---

## 확인 문제

> 객관식 8 · 서술형 2. **정답 보기**를 누르면 열려요.

### FT6-Q1. 객관식 — 시작점
6장이 5장 QLoRA 어댑터가 아니라 3장 SFT 모델에서 시작하는 이유로 가장 알맞은 것은?
1. QLoRA 모델은 DPO를 지원하지 않아서
2. 학습 목표(목적함수)의 변화에만 집중하려고
3. 3장 모델이 더 작아서
4. 5장 결과 파일이 7장에서 쓰이지 않아서

<details>
<summary>정답 보기</summary>
<p><b>2.</b> 양자화 · 어댑터까지 섞으면 무엇 때문에 결과가 바뀌었는지 알 수 없어요. 그래서 전체 가중치 SFT로 돌아가 손실 식만 바꿔요.</p>
</details>

### FT6-Q2. 객관식 — rejected
선호쌍의 rejected에 대한 설명으로 옳은 것은?
1. 실제 사용자들이 싫다고 고른 답이다
2. 형식을 일부러 깨뜨린 답이다
3. chosen과 질문이 다른 답이다
4. 같은 질문 · 규정에서 판단 하나만 틀리게 바꾼 답이다

<details>
<summary>정답 보기</summary>
<p><b>4.</b> 형식은 둘 다 맞고 판단 하나만 달라요. 교재용으로 만든 답이고 실제 사람 선호가 아니에요.</p>
</details>

### FT6-Q3. 객관식 — 합
`response_logps`가 응답 점수를 토큰 log p의 **합**으로 만드는 이유는?
1. 답안 전체가 나올 확률(토큰 확률의 곱)의 log이기 때문에
2. 평균보다 계산이 빠르기 때문에
3. 합이 항상 0보다 크기 때문에
4. 긴 답을 유리하게 만들기 위해

<details>
<summary>정답 보기</summary>
<p><b>1.</b> 곱의 log = log의 합이에요. 평균은 "토큰당 실력"이라 다른 목적함수가 돼요. 합이면 긴 답은 오히려 점수가 낮아져요.</p>
</details>

### FT6-Q4. 객관식 — 시작 loss
학습 시작 직후(policy = reference) 첫 쌍의 loss가 0.6931인 이유는?
1. β가 0.1이라서
2. learning rate가 2e-5라서
3. margin이 0이라 σ(0) = 0.5, −log 0.5 = ln 2라서
4. chosen logp가 −0.1136이라서

<details>
<summary>정답 보기</summary>
<p><b>3.</b> 아직 아무것도 안 변했으니 변화량이 모두 0이고, margin도 0이에요.</p>
</details>

### FT6-Q5. 객관식 — β와 lr
β와 learning rate에 대한 설명으로 **틀린** 것은?
1. β는 손실 식 안의 채점 기준이다
2. β를 바꿔도 margin 눈금은 그대로라 다른 β끼리 margin을 비교해도 된다
3. learning rate는 갱신 한 번의 이동 폭이다
4. β 0.1에서 margin 3을 얻으려면 logp 차이 변화가 30 필요하다

<details>
<summary>정답 보기</summary>
<p><b>2.</b> β가 다르면 reward · margin 눈금이 달라서 그대로 비교하면 안 돼요.</p>
</details>

### FT6-Q6. 객관식 — 기울기 누적
학습 반복문에서 `(loss / ACCUMULATION).backward()`의 역할은?
1. 4쌍 평균에 해당하는 기울기를 쌓아 두고, 갱신은 4쌍마다 한 번 한다
2. 매 쌍마다 가중치를 갱신한다
3. reference 점수를 다시 계산한다
4. 기울기를 0으로 비운다

<details>
<summary>정답 보기</summary>
<p><b>1.</b> 4로 나눠 쌓고, <code>position % 4 == 0</code>일 때 clip → step → zero_grad를 해요. 48 × 2 ÷ 4 = 24번이에요.</p>
</details>

### FT6-Q7. 객관식 — margin 양수
교안 2e-5 결과에서 "48쌍 margin 48/48 양수"가 의미하는 것으로 옳은 것은?
1. chosen의 확률이 모두 올라갔다
2. dev 질문에 모두 정답을 냈다
3. rejected보다 chosen의 logp가 모두 높아졌다
4. 학습 전보다 chosen − rejected의 차이가 나아졌을 뿐이다

<details>
<summary>정답 보기</summary>
<p><b>4.</b> chosen 평균 logp는 −0.44에서 −73.65로 오히려 무너졌어요. margin은 상대적인 차이만 봐요.</p>
</details>

### FT6-Q8. 객관식 — 과잉 보류 0/8
2e-5 dev 결과에서 "과잉 보류 0/8"을 좋은 소식으로 읽으면 안 되는 이유는?
1. 답할 수 있는 문항이 4개뿐이라서
2. 보류가 많을수록 좋은 모델이라서
3. status를 못 읽은 응답 8개가 어느 쪽에도 안 세져서 생긴 0이라서
4. 형식 통과가 12/12라서

<details>
<summary>정답 보기</summary>
<p><b>3.</b> 형식 통과는 2/12였어요. 답이 깨져 status를 못 읽으니 보류로도 안 세진 거예요.</p>
</details>

### FT6-Q9. 서술형 — 손실 식
DPO 손실 L = −log σ(m)에서 σ와 −log가 각각 하는 일을 설명하고, loss만 보면 안 되는 이유를 쓰세요.

<details>
<summary>정답 보기</summary>
<p>σ(m)은 margin을 0과 1 사이 "chosen이 이길 확률"로 바꿔요. −log는 그 확률이 1이면 0, 0에 가까우면 무한대인 벌점으로 바꿔요(log 확률이 0 이하라서 −를 붙여 줄여야 할 양수로). 그런데 m은 <b>차이</b>만 봐요. chosen도 같이 떨어지면서 rejected가 더 떨어지면 loss는 작아지는데 좋은 답이 무너져요(2e-5: chosen reward −5.73, 형식 2/12). 그래서 chosen 값과 원문을 같이 봐야 해요.</p>
</details>

### FT6-Q10. 서술형 — 두 가지 재현
저장 재현과 학습 재현의 차이를 이 장의 결과로 설명하세요.

<details>
<summary>정답 보기</summary>
<p><b>저장 재현</b>은 같은 파일을 다시 불러오면 같은 답이 나오는지예요. 재로딩 logits 차이 0.0, 원문 일치 True로 정확했어요. <b>학습 재현</b>은 다시 학습해도 같은 답이 나오는지예요. 같은 2e-5 설정에서도 형식 통과가 1/12 · 0/12 · 2/12로 실행마다 달랐어요. 과최적화로 무너진 모델은 작은 수치 차이에도 결과가 크게 흔들려요.</p>
</details>
