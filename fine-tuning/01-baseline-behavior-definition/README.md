# 1장. 학습할 행동과 기준 응답 정의

> 2026-11-16 학습 기록. 파인튜닝 1일차 수업이에요. RAG · CE · LLMOps에서는 **모델은 그대로 두고 입력을** 바꿨다면, 파인튜닝은 **모델의 가중치를** 바꿔요. 그런데 1장은 아직 학습하지 않아요. "학습 뒤에 좋아졌다"고 말하려면 학습 **전**에 같은 입력 · 같은 설정에서 무엇이 틀렸는지부터 남겨야 하기 때문이에요. 가상 출장 규정 도우미 문항 4개로 Qwen2.5-0.5B-Instruct의 학습 전 응답 8개를 얻고, 형식과 의미를 나눠 읽고, `baseline.json`으로 저장했어요.
>
> 1장의 한 문장: **기준 응답은 정답 예시가 아니라 비교의 출발점이다. 형식 통과 ≠ 업무 의미 ≠ 참조 일치.**

## 큰 흐름

```text
1-1 입력 분리   cases(질문 + 문서 → 모델)  vs  review_criteria(정답 행동 → 사람)
                build_messages: system = 답하는 규칙, user = 질문 + 문서 JSON (ensure_ascii=False)
1-2 토큰 · 원리  apply_chat_template → input_ids [1, 289], 끝에 <|im_start|>assistant
                세 점수 예제: softmax → −log p → 기울기 p − y → step  (손실 1.099 → 0.909)
1-3 실제 응답    from_pretrained(revision 고정, float32) → eval + inference_mode
                GenerationConfig(greedy, repetition_penalty 1.1, max_new_tokens 192) → 응답 8개
1-4 나눠 읽기    inspect_response: json_object → schema_ok → citation_ids_ok (앞이 실패하면 뒤는 안 봄)
                형식 0/4 · 0/4, 의미도 틀림 → 이것이 "학습할 행동" → baseline.json
      ↓
2장 학습 예제 72개 → 3장 SFT → 4장 LoRA → 5장 QLoRA → 6장 DPO → 7장 평가 · API → 8장 검증 · 인계
```

**과정 지도** — 1\~2장은 학습하지 않고(CPU), 3장부터 GPU로 같은 문제를 다른 방법으로 학습해 dev 12문항으로 비교해요.

| 장 | 하는 일 | 학습 |
|---|---|---|
| 1 | 학습 전 기준 응답 (`baseline.json`) | 안 함 |
| 2 | 학습 데이터 72개 | 안 함 |
| 3 · 4 · 5 | SFT를 전체 가중치 · LoRA · QLoRA로 | GPU |
| 6 | 3장 SFT 결과에서 DPO | GPU |
| 7 · 8 | 평가 · API, 검증 · 인계 | — |

## 학습 목표
- 프롬프트 · RAG · 파인튜닝이 **바꾸는 곳**을 구분한다 (지시 텍스트 / 근거 문서 / 가중치).
- 모델 입력(`cases`)과 사람용 기준(`review_criteria`)을 분리해 정답 누수를 막는다.
- 토큰 ID · 채팅 템플릿 · 손실 · 기울기(`p − y`)로 학습이 숫자를 어떻게 바꾸는지 설명한다.
- greedy 생성 설정을 고정해 학습 전 응답을 얻고, 새 토큰만 잘라 읽고, 잘림을 구분한다.
- 형식 검사 · 업무 의미 · 참조 일치를 다른 기준으로 읽고, 재현에 필요한 네 가지를 저장한다.

## 실습 환경
- **Colab CPU** (Python 3.13.18 · torch 2.14.1+cpu · transformers 5.22.2). 처음 한 번 모델 약 1GB 다운로드
- 모델: `Qwen/Qwen2.5-0.5B-Instruct`, revision `7ae557604adf67be50417f59c2c2f167def9a775` (파라미터 494,032,768개)
- `%pip install "transformers==5.22.2"` 뒤에 **런타임 재시작**을 안 하면 이미 불러온 5.22.1이 그대로 쓰여요 → 재시작 후 환경 확인 셀부터
- 로컬(다음 장 대비)에도 같은 환경을 만들어 둠: `uv` + `pyproject.toml`

```toml
dependencies = ["torch", "transformers==5.22.2", "accelerate", "ipykernel", "numpy==2.5.2"]
[tool.uv.sources]
torch = [{ index = "pytorch-cu128" }]   # RTX 50 시리즈(Blackwell)는 CUDA 12.8 빌드가 필요
```

- numpy 최신 2.5.5는 Windows **스마트 앱 컨트롤**이 DLL을 막아서 2.5.2로 고정 (보강 때 numpy 2.3.5 고정과 같은 문제). 로컬 RTX 5060에서 `generate("안녕")` → "안녕하세요! 어떻게 도와드릴까요" 확인

## 실습 파일

| 파일 | 하는 일 | 상태 |
|---|---|---|
| `problem_definition.ipynb` | 수업 노트북. 1-1\~1-4 순서대로 실행, `baseline.json` 저장 | ✅ 끝까지 실행 |
| `finetuning_ch01_practice.ipynb` | 통합 실습. 세 함수의 빈칸 8개(`build_messages` · `inspect_response` · `plan_learning_action`) + 응답 생성 + 사람 검토 | 🧪 TODO 1\~8 · 생성 · 저장 완료, `manual_reviews` 채우기 남음 |
| `1장_직접구현_실습.ipynb` | 표준 라이브러리만으로 BPE · 채팅 템플릿 · 가중치 갱신 · greedy 생성 직접 만들기 (Easy → Hard → Answer) | ✅ Easy 4개 통과 (Hard는 선택) |

---

## 핵심 이론

### 1-1. 입력 분리 — 모델에 넣을 것과 사람이 들고 있을 것

**프롬프트 · RAG · 파인튜닝은 바꾸는 곳이 달라요.**

| 방법 | 무엇을 바꾸나 | 비용 | 언제 |
|---|---|---|---|
| 프롬프트 | 지시와 문맥 텍스트 | 즉시 · 거의 없음 | 형식 · 지시를 먼저 시도 |
| RAG | 검색한 근거 문서 | 검색 저장소 운영 | 자주 바뀌는 **지식** |
| 파인튜닝 | 학습 가능한 가중치 | 데이터 + GPU 학습 | 지시해도 반복되는 **행동** 실패 |

- 규정이 95,000원으로 바뀌면 문서만 바꾸면 돼요. 금액을 가중치에 외우게 하면 규정이 바뀔 때마다 다시 학습해야 해요.
- 그래서 **금액(지식)은 문서로, "근거 읽고 JSON으로 답하고 근거 없으면 보류"(행동)는 학습으로.**
- 1장은 검색기 없이 문서를 직접 넣어 생성 단계만 관찰해요.

**네 문항 — 같은 질문인데 문서만 다르면 정답이 반대예요.**

| id | 질문 | 넣는 문서 | 정답 행동 |
|---|---|---|---|
| boundary | 1박 85,000원, 사전 승인 필요? | TRAVEL-01 (한도 85,000) | 같은 금액 → 승인 불필요 |
| over\_limit | 1박 90,000원, 무엇을 해야? | TRAVEL-01 (한도 85,000) | 초과 → 예약 전 서면 승인 |
| updated | 1박 90,000원, 무엇을 해야? | TRAVEL-02 (한도 95,000) | 이하 → 승인 불필요 |
| missing | 출장 통신비 한도는? | 없음 | abstained · 확인 불가 · 담당자 |

- over\_limit와 updated는 **질문 문장이 똑같아요.** 외운 답인지, 문서를 읽고 답하는지 가려요.
- 근거 없는 통신비를 "지원 불가"로 단정하는 것도 오류예요. 정답은 "확인할 수 없음 + 담당자 안내".
- 실무에서도 데이터를 모으기 전에 **틀리기 쉬운 경우**를 일부러 설계해요: 경계값(=), 조금 넘음, 개정, 근거 없음.

**`cases`는 모델로, `review_criteria`는 사람에게.** 정답 행동을 입력에 섞으면 정답을 보고 푸는 셈이라(정답 누수) 그 점수는 학습 전 실력이 아니에요. 평가 정답(골든셋)은 입력과 다른 필드 · 다른 파일에 둬요. (LLMOps 2장 `input` vs `expected_output`, RAG 8장 `reference`는 평가에만과 같은 원칙)

**SFT · LoRA · QLoRA · DPO는 서로 다른 축이에요.**

| | 바꾸는 축 | 한 줄 | 장 |
|---|---|---|---|
| **SFT** | 학습 목표 (무엇을 정답 신호로) | 모범답안 하나를 따라 쓰기 — 모범답안 **토큰에만** 손실 | 3장 |
| **DPO** | 학습 목표 | 같은 질문의 chosen vs rejected, **"A가 B보다 낫다"** | 6장 |
| **LoRA** | 학습 대상 (어떤 숫자를 바꾸나) | W는 고정, 작은 A · B만 학습 (540,672개 = 0.1%) | 4장 |
| **QLoRA** | 학습 대상 | LoRA와 같고 고정된 W를 NF4(4비트)로 압축 | 5장 |

- 그래서 "SFT랑 LoRA 중 뭐 쓰지?"는 질문이 어긋나요. **"LoRA로 SFT를 한다"**가 맞는 말이에요.
- 3\~5장은 SFT 목표 그대로 **대상만** 바꿔 비교하고, 6장은 3장 SFT 결과에서 DPO를 해요.

**`build_messages` — system은 계약, user는 이번 데이터.**

```python
def build_messages(case, explicit: bool):
    # 검토 기준은 빼고, 질문과 제공 문서만 user 메시지에 직렬화
    model_input = {"question": case["question"], "documents": case["documents"]}
    return [
        {"role": "system", "content": explicit_instruction if explicit else simple_instruction},
        {"role": "user", "content": json.dumps(model_input, ensure_ascii=False)},
    ]
```

| | simple | explicit |
|---|---|---|
| 필드 | JSON 3필드 | + 3필드만, 코드 펜스 금지 |
| 보류 규칙 | 없음 | 근거 없으면 abstained |
| 인용 규칙 | 없음 | answered ↔ 문서 ID |
| 토큰 수 | 32 | 165 |

- 같은 질문 · 문서 · 가중치에서 **system 지시만** 바꿔 비교해요.
- **`ensure_ascii=False`**: 없으면 한글이 `\uXXXX`로 바뀌어 같은 문장이 21토큰 → 71토큰이 되고, 모델이 뜻을 못 읽어요(통합 실습에서 직접 겪음 → 아래 질문 정리).
- assistant 자리는 1장에서 비워 둬요. **모델이 채울 자리**이고, 정답은 3장 학습 때만 들어가요.
- 실무: 학습(2\~3장)과 추론에서 system 문자열을 글자 하나까지 같게 써요. 2장 `SYSTEM_PROMPT` = 1장 explicit 지시.

### 1-2. 토큰 · 원리 — 모델은 토큰 ID를 읽고, 학습은 `p − y` 방향으로 움직인다

**모델은 글자가 아니라 토큰 ID를 읽어요.** byte-level BPE라 자주 나오는 **바이트 묶음**이 토큰 하나가 돼요.

```python
tokenized = tokenizer.apply_chat_template(
    messages,
    tokenize=True,
    add_generation_prompt=True,   # 끝에 <|im_start|>assistant\n → "여기서부터 답하라"
    return_dict=True,
    return_tensors="pt",
)
print(tuple(tokenized["input_ids"].shape))   # (1, 289)  [B=문장 1개, T=특수 토큰 포함 289개]
print(tokenizer.convert_ids_to_tokens(tokenized["input_ids"][0, :16].tolist()))
# ['<|im_start|>', 'system', 'Ċ', 'ìłľ', 'ê³µ', 'ëĲľ', 'Ġê·', '¼', 'ê±°', ...]
```

- `ìłľ`처럼 깨져 보이는 건 한글 UTF-8 **바이트를 글자로 표시**한 것이에요. decode하면 '제'로 돌아와요. `Ġ` = 앞 공백이 토큰에 붙어 있음, `Ċ` = 줄바꿈.
- **숫자는 한 자리씩** 쪼개져요: '85,000' = 6토큰. 금액 비교를 숫자 크기가 아니라 토큰 순서로 배우게 돼요(3장 이후 남는 70,000원 오답의 배경).
- 어휘 151,665개, 특수 토큰 `<|im_start|>` 151644 · `<|im_end|>` 151645 · `<|endoftext|>` 151643.
- 비용 · 지연 · 컨텍스트 한도(32,768) · 학습 MAX\_LENGTH(512)는 **모두 토큰 기준**이에요.
- 템플릿을 적용한 문자열을 `tokenizer(text)`로 또 토큰화하면 특수 토큰이 두 번 붙을 수 있어서, `tokenize=True`로 한 번에 끝내요.
- 모델 계열마다 템플릿이 달라요(Qwen `<|im_start|>`, Llama `<|start_header_id|>`). 모델을 바꾸면 템플릿부터 바뀌어요.

| `add_generation_prompt` | 언제 | 끝 모양 |
|---|---|---|
| `True` | 추론 입력 (1장) | `...<|im_end|>\n<|im_start|>assistant\n` |
| `False` | 정답이 들어간 학습 대화 (2\~3장) | `...모범답안<|im_end|>\n` |

**세 점수 한 번 갱신 — 로짓 → 확률 → 손실 → 기울기.** Qwen 가중치가 아니라 후보 토큰 3개의 점수만 직접 학습하는 **원리 예제**예요.

```python
scores = torch.nn.Parameter(torch.zeros(1, 3))   # [1, 3] = 위치 1개, 후보 3개
target = torch.tensor([2], dtype=torch.long)     # 정답은 세 번째 후보
optimizer = torch.optim.SGD([scores], lr=0.3)

before_probabilities = scores.detach().softmax(dim=-1)   # 후보 축(마지막 축)끼리 합 1
loss = torch.nn.functional.cross_entropy(scores, target) # softmax 전 "로짓"을 넣음
optimizer.zero_grad()
loss.backward()                                  # 기울기만 계산
gradient = scores.grad.detach().clone()          # 이번 기울기를 복사해 보관
optimizer.step()                                 # 값을 실제로 바꾸는 건 여기
```

| 단계 | 값 |
|---|---|
| 점수 s | [0, 0, 0] |
| softmax p | [0.333, 0.333, 0.333] |
| 손실 −log p₂ | **1.099** |
| 기울기 p − y | [0.333, 0.333, **−0.667**] |
| s − 0.3 × 기울기 | [−0.1, −0.1, 0.2] |
| 다시 p / 손실 | [0.299, 0.299, **0.403**] / **0.909** |

- **`backward()`는 기울기만 계산**, 값을 바꾸는 건 **`step()`**. `cross_entropy`에는 softmax 전 **로짓**을 넣어요(안에서 softmax를 함).
- 실제 모델은 위치마다 로짓이 `[어휘 151,936]` 한 줄씩이고, 정답 토큰 확률을 올리는 이 계산을 **답변 토큰 수만큼 평균한 것이 SFT 손실**(3장)이에요.

**왜 기울기가 `p − y`일까 — 교차엔트로피 미분과 연쇄법칙.**

```text
① p_i = e^(s_i) / Σ_j e^(s_j)
② L = −log p_y
③ L = −s_y + log Σ_j e^(s_j)
④ ∂L/∂s_i = −[i = y] + p_i  =  p_i − y_i        (y = 정답 one-hot)
```

- 부호 = 방향(양수면 그 점수를 내려야 손실이 줄어요), 크기 = 얼마나 틀렸나.
- 연쇄법칙: **w의 기울기 = (뒤에서 온 오차) × (그 가중치에 들어온 입력)**. 예) x = 3, w = 0.5, 정답 2 → ∂L/∂w = (1.5 − 2) × 3 = −1.5. 마지막 층(lm\_head)이면 (p − y) · hᵀ.
- 검산: (L(s₂ + 0.001) − L(s₂ − 0.001)) / 0.002 = −0.6667 = autograd의 −0.667. PyTorch는 작은 값을 더해 비교하지 않고, 연산마다 미분 공식을 알고 한 번에 계산해요(autograd). 수치 미분은 검산용.

| | SGD (1장) | AdamW (3장) |
|---|---|---|
| 갱신 | θ − lr·g | θ − lr·m/√v (보정) |
| 추가 메모리 | 0 | 파라미터당 2개 |
| 흔한 lr | — | 전체 1e-5대 · LoRA 1e-4대 |

### 1-3. 실제 응답 — greedy로 고정해 학습 전 응답 8개 얻기

**불러오기는 학습이 아니에요.**

```python
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    revision=REVISION,      # 커밋 해시로 고정 → 저장소가 갱신돼도 같은 가중치 · 템플릿
    dtype=torch.float32,    # 1장은 CPU · GPU 모두 float32로 맞춤
).to(DEVICE)
model.eval()                # 평가 동작(dropout 끔). 기울기 기록 끄기와는 다름
```

| 저장 방식 | 0.5B 모델 크기 |
|---|---|
| fp32 (1장) | 1.98 GB (494,032,768 × 4바이트) |
| bf16 | 0.99 GB |
| NF4 (QLoRA) | 0.25 GB |
| 전체 학습 fp32 (가중치 + 기울기 + AdamW 2개) | 7.90 GB ≈ 4배 → 그래서 LoRA · QLoRA |

| | 추론 (1장 generate) | 학습 (3장 train) | 무엇을 제어하나 |
|---|---|---|---|
| `model.eval()` | 켬 | 끔 (Trainer가 `train()`으로) | dropout 등 평가 동작 |
| `torch.inference_mode()` | 켬 | 끔 | 기울기 그래프 기록 |

**생성 설정 — 가중치를 바꾸지 않고, 계산된 점수에서 무엇을 출력할지 고르는 규칙.**

```python
generation = GenerationConfig(
    do_sample=False, num_beams=1,     # greedy: 가장 큰 후보 하나
    repetition_penalty=1.1,           # 이미 나온 토큰 점수 깎기: logit>0 → /1.1, <0 → ×1.1
    max_new_tokens=192,               # 입력 제외 새 토큰 상한 (글자 수 아님)
    eos_token_id=model.generation_config.eos_token_id,   # [151645, 151643]
    pad_token_id=tokenizer.pad_token_id,                 # 151643
)
```

- 이 저장소 **기본값은 sampling**(temperature 0.7 · top\_p 0.8 · top\_k 20)이라, 명시 안 하면 실행마다 답이 달라져 비교가 무너져요. 생성 설정은 코드에 명시해요.
- greedy vs sampling: 후보가 ('cat', 0.4), ('dog', 0.3)…이면 greedy는 늘 cat. sampling은 확률대로 cat 4번 · dog 3번꼴로 뽑아요. 평가 · 비교 · JSON은 greedy나 낮은 temperature.
- `temperature` · `top_p` · `top_k`는 sampling에서만 의미가 있어요(greedy에 넣으면 무시 경고).
- `repetition_penalty`는 greedy 순위에도 영향을 줘서 비교 중 고정해요. 너무 크면 JSON 따옴표 · 괄호도 깎여요.

**`generate`는 "입력 + 새 토큰"을 돌려줘요 → 입력 뒤만 읽기.**

```python
with torch.inference_mode():
    generated = model.generate(**inputs, generation_config=generation)
new_tokens = generated[0, input_length:]                   # [0, :289]는 입력(버림), [0, 289:]가 새 토큰
raw_response = tokenizer.decode(new_tokens, skip_special_tokens=True)  # 제어 토큰은 "표시에서만" 뺌
ended_with_eos = bool(len(new_tokens) and new_tokens[-1].item() in eos_ids)
length_limited = len(new_tokens) >= generation.max_new_tokens and not ended_with_eos
```

- greedy 한 걸음: 전체 토큰 → 마지막 위치 로짓 `[151,936]` → 반복 패널티 → 가장 큰 1개 → 붙이기 → EOS나 상한까지 반복.
- 형식 실패를 모델 탓으로 읽기 전에 **잘림부터** 확인해요.

**내 실행 결과 — 응답 8개 (CPU, greedy)**

| variant / case | 출력 토큰 | 원문 요약 | 정답 행동 |
|---|---|---|---|
| simple / boundary | 104 | `답변:` 85,000원 한도… "사전 승인이 필요하다는 점을 고려해" (앞뒤 모순) | 승인 불필요 |
| simple / over\_limit | 72 | "1박 90,000원의 예약을 할 수 없습니다" (승인 조건을 뒤집음) | 서면 승인 |
| simple / updated | **192 (잘림)** | 95,000원은 맞게 읽고 지어낸 조건 1\~4 나열 후 끊김 | 승인 불필요 |
| simple / missing | 38 | `결과:` "통신비는 최대 50만원까지 지원" (근거 없는 숫자 = 환각) | 보류 + 담당자 |
| explicit / boundary | 61 | ` ```json ` 펜스 + "사전 승인이 필요합니다" (오답) | 승인 불필요 |
| explicit / over\_limit | 58 | 펜스 + "다음과 같은 방법으로 할 수 있습니다" (내용 없음) | 서면 승인 |
| explicit / updated | 58 | over\_limit과 **같은 문장**, 인용만 TRAVEL-02 | 승인 불필요 |
| explicit / missing | **2** | `answered` 한 단어 | abstained |

지시를 구체적으로 바꾸면 형식은 JSON에 가까워지지만(코드 펜스는 여전) 의미는 다 틀려요. 이건 지시만 바꾼 비교라 **파인튜닝 효과가 아니에요.** 이 실패들이 3장에서 고칠 목표예요.

### 1-4. 나눠 읽기 — 형식 · 의미 · 참조 일치는 다른 기준

**`inspect_response` — 세 단계, 앞이 실패하면 뒤는 안 봐요.**

```python
def inspect_response(raw, source_ids):
    result = {"json_object": False, "schema_ok": False, "citation_ids_ok": False}
    try:
        response = json.loads(raw)            # ① 원문 그대로. 코드 펜스를 지워서 성공으로 바꾸지 않음
    except json.JSONDecodeError:
        return result
    if not isinstance(response, dict):
        return result
    result["json_object"] = True

    schema_ok = (                              # ② 키 3개 · status 값 · 자료형
        set(response) == {"status", "answer", "citations"}
        and response["status"] in ("answered", "abstained")
        and isinstance(response["answer"], str) and bool(response["answer"].strip())
        and isinstance(response["citations"], list)
        and all(isinstance(item, str) for item in response["citations"])
    )
    if not schema_ok:
        return result
    if response["status"] == "answered" and not response["citations"]:   # 상태 계약
        return result
    if response["status"] == "abstained" and response["citations"]:
        return result
    result["schema_ok"] = True

    result["citation_ids_ok"] = set(response["citations"]).issubset(source_ids)   # ③ 인용 ⊆ 제공 문서
    return result
```

- 앞 단계 실패 시 뒤를 False로 두는 이유: **거짓 세 개를 독립된 오류 세 개로 세지 않으려고.**
- 내 결과: 8개 모두 ① 단계에서 실패 — simple은 앞말(`답변:` · `결과:`), explicit은 코드 펜스, missing은 `answered` 한 단어. **형식과 인용 ID 통과 simple 0/4 · explicit 0/4** (분모 = 관찰용 4문항, 업무 정답률 아님).

**세 기준은 서로 달라요.**

| 응답 예 | 형식 | 의미 | 참조 일치 |
|---|---|---|---|
| `{"status":"answered","answer":"한도 이하라 승인 불필요",...}` (초과 문항) | 통과 | **오답** | 불일치 |
| `{"status":"answered","answer":"예약 전에 문서로 승인 받으세요",...}` | 통과 | 정답 | **불일치** |
| ` ```json { ... 모범답안과 같은 내용 ... } ``` ` | **실패** | 정답 | 실패 |

- **형식 통과** = 후속 프로그램이 읽을 수 있나 / **업무 의미** = 금액 비교 · 승인 시점 · 보류 이유가 맞나(사람이 읽음) / **참조 완전 일치** = 모범답안 dict와 글자까지 같나(가장 좁아서 표현이 다른 올바른 답도 틀렸다고 함).
- API 모델은 JSON 모드로 형식을 강제할 수 있지만, 로컬 모델은 학습으로 형식을 익히고(3장) 의미는 따로 봐요.
- 지표는 **검사 이름 + 분모**를 같이 써요: "형식과 인용 ID 통과 0/4".

**`baseline.json` — 나중에 "왜 달라졌나"를 답할 수 있게.**

| 필드 | 답해 주는 질문 |
|---|---|
| `model_id` · `revision` | 같은 가중치 · 템플릿인가 |
| `runtime` · `weight_dtype` | 환경 · 정밀도 차이인가 |
| `generation` | 생성 규칙이 같은가 |
| `cases` · `review_criteria` | 같은 문제로 비교하나 |
| `records[]` | 실제 원문과 판정 근거 |

- 실험 재현의 네 가지: **모델 버전 · 데이터 · 설정 · 원문.** 응답만 저장하면 무엇 때문에 결과가 달라졌는지 몰라요.
- Colab: 노트북 저장 ≠ 런타임 파일 저장. `/content/baseline.json`은 따로 내려받아요. 같은 셀을 다시 돌리면 덮어써져요.
- 1장 네 문항은 **행동 관찰용**이라 학습이나 최종 평가 데이터로 같이 쓰지 않아요. 2장은 별도 72개를 만들어요.

---

## 통합 실습 — `finetuning_ch01_practice.ipynb`

> 세 함수의 빈칸 8개를 채우고, 자기 점검 3개를 통과한 뒤에만 실제 모델을 돌려요. 새 Colab 세션 · CPU.

### TODO 1\~3 `build_messages`

```python
def build_messages(case, explicit):
    instruction = explicit_instruction if explicit else simple_instruction          # TODO 1
    model_input = {"question": case["question"], "documents": case["documents"]}   # TODO 2
    return [                                                                        # TODO 3
        {"role": "system", "content": instruction},
        {"role": "user", "content": json.dumps(model_input, ensure_ascii=False)},
    ]
```

- 결과: "입력 자기 점검 통과: 4개 사례" — 두 지시가 같은 user 입력을 받는지, `json.loads` 했을 때 원래 질문 · 문서와 같은지 확인.

### TODO 4\~6 `inspect_response`

수업 노트북과 같은 세 단계예요. 결과: "형식 자기 점검 통과: 6개 합성 응답".

| 합성 응답 | 기대값 | 걸리는 곳 |
|---|---|---|
| 형식과 의미가 맞는 예 | T, T, T | — |
| **형식은 맞지만 경계 판단이 틀린 예** | **T, T, T** | 의미는 자동 검사로 못 잡음 ← 이 실습의 핵심 |
| 문서가 없어 보류한 예 | T, T, T | `set() ⊆ set()`은 True |
| 없는 문서 ID를 인용한 예 | T, T, **F** | TODO 6 |
| boolean을 답변으로 쓴 예 | T, **F**, F | TODO 5 `isinstance(answer, str)` |
| 코드 펜스를 붙인 예 | **F**, F, F | TODO 4 `json.loads` 실패 |

### TODO 7\~8 `plan_learning_action`

```python
# TODO 7: 길이 → 형식 → 의미 순서 (지금 당장 확인할 실행 문제)
if length_limited:
    followup = "check_length"
elif not all(checks.values()):
    followup = "check_format"
else:
    followup = "read_meaning"

# TODO 8: 사람이 고른 실패 종류 → 2장에서 만들 학습 예시
learning_action = {
    "not_reviewed": "read_first",
    "supported": "keep_observing",
    "boundary": "boundary_pair",           # 85,000(같음) vs 90,000(초과) 대조
    "approval": "approval_steps",          # 초과 + 예약 전 서면 승인을 함께
    "updated": "changed_document_pair",    # 같은 질문에 85,000 / 95,000 문서 대조
    "missing": "missing_evidence_pair",    # 근거 있으면 답, 없으면 이유 + 담당자
}[review_kind]
```

- `followup`과 `learning_action`을 따로 두는 이유: 한 칸에 섞으면 "코드 펜스 때문에 실패"로만 기록돼서 **"경계 금액을 틀렸다"는 진짜 학습 목표를 잃어버려요.** 형식이 틀려도(`check_format`) 사람이 확인한 경계 오답의 `boundary_pair`는 그대로 남아요.
- 결과: "행동 연결 자기 점검 통과", `형식 정상인 경계 오답: {'followup': 'read_meaning', 'learning_action': 'boundary_pair'}`.

### 실제 생성 · 저장

- 응답 8개는 수업 노트북과 **글자까지 같게** 나왔어요(같은 revision · greedy · 같은 설정 → 재현됨). 형식 통과 simple 0/4 · explicit 0/4.
- `practice_result.json` 저장(실제 응답 8개). 단, `manual_reviews`를 아직 안 채워서 "의미 검토 전: 8"인 상태로 저장됐어요.

**내가 읽은 의미 검토 (다음에 `manual_reviews`에 넣을 값)**

| 키 | 정답 | 모델 응답 | kind |
|---|---|---|---|
| simple:boundary | 승인 불필요 | "한도 내 가능… 사전 승인이 필요하다는 점 고려" (모순) | `boundary` |
| simple:over\_limit | 서면 승인 받으면 가능 | "예약을 할 수 없습니다" (조건을 뒤집음) | `approval` |
| simple:updated | 승인 불필요 | 192토큰에서 잘림 | `not_reviewed` (잘린 답은 그대로 두는 규칙) |
| simple:missing | 보류 | "최대 50만원" 단정 | `missing` |
| explicit:boundary | 승인 불필요 | "사전 승인이 필요합니다" | `boundary` |
| explicit:over\_limit | 서면 승인 | 승인 언급 없음 | `approval` |
| explicit:updated | 95,000 적용 | over\_limit과 같은 답 | `updated` |
| explicit:missing | abstained | `answered` 한 단어 | `missing` |

---

## 직접 구현 실습 — `1장_직접구현_실습.ipynb` (Easy)

> 1장에서 라이브러리가 대신 해 준 네 가지를 **표준 라이브러리만으로** 만들어 봐요. Easy는 보조 함수가 주어지고 main 함수 하나만 채워요.

| 실습 | 직접 만든 것 | 1장에서 대응하는 것 |
|---|---|---|
| ① | `train_bpe` | `AutoTokenizer`, `convert_ids_to_tokens` |
| ② | `apply_chat_template` | `apply_chat_template(add_generation_prompt=...)` |
| ③ | `train_step` | 세 점수 예제, `backward()` · `step()` |
| ④ | `generate` | `model.generate`, `repetition_penalty`, `max_new_tokens` |

### ① 미니 BPE — 가장 자주 붙어 나오는 바이트 쌍을 40번 합치기

```python
def train_bpe(corpus, num_merges):
    ids_list = [to_bytes(t) for t in corpus]          # 문장마다 UTF-8 바이트 숫자 리스트
    merges = {}                                       # (a, b) -> 새 토큰 ID
    vocab = {i: bytes([i]) for i in range(256)}       # 토큰 ID -> 바이트
    for k in range(num_merges):
        counts = get_pair_counts(ids_list)            # 이웃한 쌍 개수
        if not counts:
            break
        pair = max(counts, key=counts.get)            # 가장 많이 나온 쌍
        new_id = 256 + k
        merges[pair] = new_id
        vocab[new_id] = vocab[pair[0]] + vocab[pair[1]]          # 두 토큰의 바이트를 이어 붙임
        ids_list = [merge(ids, pair, new_id) for ids in ids_list] # 모든 문장에 적용
    return merges, vocab
```

```text
'숙박비 지원 한도': 바이트 23개 → 토큰 1개 ['숙박비 지원 한도']
'1박 70,000원': 바이트 14개 → 토큰 9개 ['1', '박', ' ', '7', '0', ',', '00', '0', '원']
'통신비': 바이트 9개 → 토큰 9개 ['�', '�', '�', '�', '�', '�', '�', '�', '�']
✅ BPE 토크나이저 통과
```

- 학습 문장에 20번 나온 "숙박비 지원 한도"는 통째로 1토큰. 처음 보는 70,000은 잘게, 한 번도 안 나온 "통신비"는 바이트 9개 그대로(바이트 하나로는 한글이 안 돼서 `�`). Qwen의 `ìłľ`와 같은 이유예요.
- 예) `"abab abab"` → (a, b) 4번 → 256 = `ab` → (256, 256) 2번 → 257 = `abab` → 글자 9개가 토큰 3개.

### ② 채팅 템플릿

```python
def apply_chat_template(messages, add_generation_prompt):
    text = ""
    if messages[0]["role"] != "system":                    # system이 없으면 Qwen 기본 system
        text += format_message("system", DEFAULT_SYSTEM)
    for m in messages:                                      # <|im_start|>역할\n내용<|im_end|>\n
        text += format_message(m["role"], m["content"])
    if add_generation_prompt:                               # 추론할 때만 답변 시작 표시
        text += "<|im_start|>assistant\n"
    return text
```

```text
<|im_start|>system
근거에만 따라 JSON으로 답하세요.<|im_end|>
<|im_start|>user
1박 90,000원인 방을 예약하려면?<|im_end|>
<|im_start|>assistant
▼ 답변 시작 위치 ▼
{"status": "answered"}<|im_end|>
✅ 채팅 템플릿 통과
```

- ▼ 위쪽이 추론 입력(`True`), 아래까지 합친 전체가 학습 대화(`False`). **학습 대화는 추론 입력을 접두부로 가져요.** 3장 SFT에서 "▼ 아래에만 손실"이 이 위치예요.
- system 없이 "안녕"만 보내도 `"You are Qwen, created by Alibaba Cloud..."`가 들어가는 이유도 여기서 확인.

### ③ 가중치 직접 수정 — softmax · 교차엔트로피 · 오차 × 입력 · SGD

```python
def train_step(W, x, y, lr):
    x_vec, y_vec = one_hot(x), one_hot(y)     # 토큰 번호 → one-hot
    p = softmax(forward(W, x_vec))            # 로짓 = W · x → 확률
    loss = -math.log(p[y])                    # 교차엔트로피
    for o in range(V):
        err = p[o] - y_vec[o]                 # 오차 = p − y  (= backward)
        for i in range(V):
            W[o][i] -= lr * err * x_vec[i]    # 기울기 = 오차 × 입력, SGD  (= step)
    return loss
```

```text
epoch  1  평균 손실 2.178
epoch 10  평균 손실 0.567
epoch 30  평균 손실 0.371
✅ 가중치 직접 수정 통과
```

- 정답 칸 err = p − 1 < 0 → `-=` 하면 **올라가고**, 오답 칸은 내려가요. one-hot 입력이라 **지금 토큰의 열만** 바뀌어요.
- 손실이 0까지 안 내려가는 게 정상이에요. 학습 문장에서 `금액` 다음은 `이하`/`초과` 반반, `승인` 다음은 `불필요`/`필요` 반반이라, 바로 앞 토큰 하나만 보는 모델은 그 자리에서 50:50이 최선이에요(이론상 바닥 약 0.25).

### ④ greedy 생성 루프

```python
def generate(W, start, max_new_tokens, repetition_penalty, eos="<e>"):
    out = [start]
    for _ in range(max_new_tokens):
        x = IDX[out[-1]]
        logits = [W[o][x] for o in range(V)]
        logits = apply_repetition_penalty(logits, {IDX[t] for t in out}, repetition_penalty)
        nxt = VOCAB[argmax(logits)]               # greedy: 가장 큰 것
        out.append(nxt)
        if nxt == eos:
            return out, True, False               # ended_with_eos
    return out, False, True                       # length_limited
```

```text
이하         → 이하 승인 필요 <e> | EOS True | 잘림 False
초과         → 초과 서면 승인 필요 <e> | EOS True | 잘림 False
초과 · 상한 2  → 초과 서면 승인 | EOS False | 잘림 True
✅ greedy 생성 통과  (그런데 '이하 → 승인 필요'는 업무상 오답이에요. 왜일까요?)
```

- **"이하 → 승인 필요"가 나오는 이유**: 이 모델은 바로 앞 토큰 하나만 봐서 `승인` 앞이 `이하`였는지 `초과`였는지 몰라요. ③에서 손실 0.37까지 내려갔는데도 업무상 오답이에요. **손실이 낮다 ≠ 업무 판단이 맞다.** 실제 언어 모델이 긴 문맥을 보는 이유이고, 3장에서 SFT 모델이 70,000원을 "한도 이하"라고 틀리는 장면과 이어져요.
- ①의 숫자 쪼개기도 같은 질문으로 이어져요: 금액이 한 자리씩 토큰이면 "70,000 < 85,000"을 크기가 아니라 토큰 순서로 배워야 해요.

---

## 실행 결과 (내 실행)

| 노트북 | 결과 |
|---|---|
| `problem_definition` | input\_ids (1, 289) · 확률 0.333 → 0.403 · 손실 1.099 → 0.909 · 응답 8개(simple/updated 192토큰 잘림) · 형식 0/4 · 0/4 · `/content/baseline.json` 저장 |
| `finetuning_ch01_practice` | 자기 점검 3개 통과 · 응답 8개(수업 노트북과 동일) · 형식 0/4 · 0/4 · `/content/practice_result.json` 저장(의미 검토 전 8) |
| `1장_직접구현_실습` Easy | ① BPE ✅ · ② 템플릿 ✅ · ③ train\_step ✅ (손실 2.178 → 0.371) · ④ generate ✅ |

## 질문과 새로 알게 된 점

### SFT · LoRA · QLoRA · DPO 표를 쉽게
- **SFT** = 모범답안을 보고 베껴 쓰기 연습. "질문 + 문서 + 모범답안"을 주고, 질문 · 문서 부분은 채점하지 않고 **모범답안 토큰만** 채점해요. `{` 다음에 `"status"`가 와야 하는데 `답변:`을 더 높게 점치면 그만큼 손실 → 2강 세 점수 예제(0.333 → 0.403)를 답변 토큰마다 하는 것.
- **LoRA** = 교과서(W)는 그대로 두고 포스트잇(A · B)만 붙이기. `실제 계산 = W(고정) + B × A(학습)`. 예) W 896×896 ≈ 80만 개, 랭크 8이면 A(8×896) + B(896×8) ≈ 1.4만 개. 포스트잇은 어댑터 파일로 따로 저장돼요.
- **QLoRA** = 교과서를 축소 복사본(4비트)으로 들고 다니고 포스트잇은 원래 크기. 배우는 방식은 여전히 SFT.
- **DPO** = 같은 질문에 chosen(근거 있는데 제대로 답함) vs rejected(근거 있는데 겁먹고 보류)를 주고 "A가 B보다 낫다"를 배워요. SFT로 "근거 없으면 보류"를 가르치면 생기는 **과한 보류 버릇**을 잡는 데 맞아요.

### `softmax(dim=-1)`인 이유
- `scores`는 `[1, 3]` = 위치 1개 · 후보 3개. 확률은 **후보 3개끼리** 나눠 가져야 하고, 그 후보들이 놓인 축이 마지막 축(-1)이에요. `dim=0`이면 칸마다 혼자 100%가 돼서 `[[1., 1., 1.]]`.
- 그냥 `1`이 아니라 `-1`로 쓰는 이유: 실제 Qwen 출력은 `[B, T, 151936]`. 축 개수가 달라도 **어휘(후보) 축은 항상 마지막**이라 `-1`이면 예제와 실제 모델에 같은 코드가 돼요. `dim=1`로 써 두면 실제 모델에선 위치(T) 축으로 나누는 엉뚱한 계산.
- 보강 NumPy의 `axis=1`(행마다 계산), softmax 응용 3과 같은 개념.

### `gradient = scores.grad.detach().clone()`에서 clone하는 이유
- `gradient = scores.grad`는 같은 칸에 이름만 하나 더 붙이는 것(리스트 `b = a` vs `b = a.copy()`). PyTorch는 `zero_grad()` 없이 `backward()`를 또 하면 기울기를 **덮어쓰지 않고 더해요(누적)**.
- 로컬에서 확인: 이름만 붙인 쪽은 `[0.667, 0.667, -1.333]`(두 번 더해짐), clone한 쪽은 `[0.333, 0.333, -0.667]` 그대로.
- `.detach()`는 미분 기록에서 떼어 내지만 **메모리는 원본과 공유**(원본이 바뀌면 같이 바뀜 확인), `.clone()`은 메모리까지 새로 복사. 그래서 둘을 같이 써요.
- `before_probabilities`엔 clone이 없는 이유: `softmax()`가 결과를 이미 **새 텐서로** 만들어 줘서.
- 정리하면 before/after 비교는 확률과 손실로 하고, `gradient`는 그 사이에 "어느 방향으로 얼마나 움직였나"를 보여 주려고 **그 순간 값을 보관**한 거예요. 이 노트북 순서(backward → step 한 번)에선 clone이 없어도 출력이 같지만, 기울기 누적 · clipping처럼 그 칸을 고치는 코드가 붙으면 달라지니까 넣어 두는 습관.

### `build_messages`가 리스트를 돌려주는 이유
- 대화는 **순서가 있는 메시지 여러 개**이고 `apply_chat_template`이 "role/content 딕셔너리의 리스트"를 받기 때문이에요.
- 순서대로 이어 붙이니 순서가 중요하고(자기 점검도 `["system", "user"]` 확인), 멀티턴에선 같은 role이 여러 번 나와요. `{"system": ..., "user": ...}` 딕셔너리면 키가 겹쳐 덮어써져요.
- 3장 SFT 데이터는 이 리스트 끝에 `+ [{"role": "assistant", "content": 모범답안}]`. OpenAI · Claude API의 `messages`도 같은 형식.

### `ensure_ascii=False`를 빼먹었더니 (통합 실습에서 겪은 것)
- 처음 TODO 3을 `json.dumps(model_input)`로만 썼더니 user 메시지가 `1\\ubc15 90,000\\uc6d0...`이 됐고, 생성 결과가 "1,900,000,000", 영어 문장, `"status":"success"` 같은 엉뚱한 답이었어요.
- 자기 점검은 `json.loads(...) == expected_input`으로 비교해서 **통과했어요.** `\uXXXX`도 다시 읽으면 같은 한글이니까. 검사가 통과해도 모델이 실제로 받는 문자열은 다를 수 있다는 것.
- `ensure_ascii=False`를 넣고 다시 돌리니 수업 노트북과 같은 응답이 나왔어요. 1-1 슬라이드의 "21토큰 → 71토큰"이 실제로 어떤 결과를 내는지 직접 본 셈.
- 같이 겪은 것: `%pip install` 뒤에 런타임을 재시작 안 해서 transformers가 5.22.1로 남아 있었어요 → 재시작 후 처음부터 다시 실행.

### one-hot이 뭐지?
- 여러 칸 중 **딱 한 칸만 1**이고 나머지는 0인 벡터. 9개 단어 사전에서 `승인`(5번) = `[0,0,0,0,0,1,0,0,0]`.
- 숫자 5를 그대로 쓰면 "필요(8) > 승인(5)" 같은 의미 없는 크기 관계가 생겨요. one-hot은 모든 단어를 대등하게 표현해요.
- `W · one_hot(5)` = W의 5번 열만 꺼내기. 그래서 학습 때도 그 열만 바뀌어요. 정답 y도 one-hot이라 `p − y`에서 정답 칸만 1을 빼요.
- 실제 Qwen은 사전이 15만 개라 one-hot을 만들지 않고 **임베딩 테이블에서 그 번호의 행을 바로 꺼내요**(`nn.Embedding`). 하는 일은 같고 0 곱하기만 건너뛴 것.

## 실습 코드에서 직접 바꾼 점

**`problem_definition.ipynb`에 단 주석** (수업 들으면서 남긴 메모)
- `REVISION = "7ae5576..."  # 하드코딩. 해시로 바꿀수도 있음.`
- `cases` 규정 문장 옆: `# 정책이 바뀌는 경우가 생긴다는것. 95,000 으로 변경 등`
- `explicit_instruction` 끝: `# 컨텍스트엔지니어링 에서 잘 안될때 예시답변 형태를 주는 경우 잘나올 가능성높음.` (CE의 few-shot 예시 답변 아이디어)
- `def build_messages(...): # 중요 ×4`, 그 아래 `# role은 system, user, assistant 까지 들어갈 수 있다.`
- `apply_chat_template( # 중요`, `add_generation_prompt=True, # 이제부터 너가 답변할 차례다.`
- `# B는 배치, T는 토큰갯수. B가 왜있을까? 모델이 동시에 여려개 요청을 처리할 수 있게.`
- `convert_ids_to_tokens` 옆: `# 문자들이 깨져서 나옴. BPE. 일종의 통계적학습.(알아보기.)` → 직접 구현 ① BPE로 확인
- 세 점수 예제: `#마지막이 타겟.`, `#optimizer SGD, ADAM, ADAMW 많이씀. 세타갱신해줌`, `#왜 dim-1?`, `#CE는 softmax를 계산해주는 로직을 이미 가지고있음.`, `# 예측` / `# 정답`, `# 기울기 비우기.`, `# 다시 돌아가는 연산.`, `# clone?` → 위 질문 정리
- 모델 로드: `model.eval() # 추론`, `num_beams=1, # 샘플링이 아니라 greedy로 최적의 답 고르기.` + cat/dog 샘플링 예시 주석, dtype 출력 옆 `# 나중에 양자화 LOLA QLOLA와 관련.`
- 생성 셀: `# 출력을 끝내기 위한 토큰.`(eos), `# 가중치를 업데이트 하지않고 기존 응답확인.`, `#이제너가답변할차례다. assistant`, `# inference 모드안하면 학습하는모드.`, `# response가 나옴(자연어)`
- 생성 루프를 손으로 따라 친 연습 셀을 하나 추가했어요(실행은 원래 셀로). 따라 치면서 생긴 오타: `recods`, `{eos-ids}`(→ `eos_ids`), `tokenizer=True`(→ `tokenize=True`). 특히 `tokenize`/`tokenizer`는 헷갈리기 쉬움.

**`finetuning_ch01_practice.ipynb`**
- TODO 1\~8 직접 작성 → 자기 점검 3개 통과.
- `manual_reviews`는 아직 기본값(`not_reviewed`) — 위 표대로 채우고 검토 · 저장 셀 다시 실행할 차례.

**`1장_직접구현_실습.ipynb`**
- Easy ①\~④ 모두 직접 채워 통과. ④는 원래 TODO 주석을 통째로 주석 처리해 두고 아래에 구현을 새로 썼고, `check_generate(...)`가 두 번 들어가 출력이 두 번 나와요.

## PPT 정리
- 1장 결과물: **학습 전 기준과 고칠 목표**
  - 1-1 모델 입력과 사람용 기준을 나눈다 → `cases` · `review_criteria` · `build_messages`
  - 1-2 모델은 토큰을 읽고, 학습은 `p − y` 방향으로 움직인다 → input\_ids [1, 289] · 손실 1.099 → 0.909
  - 1-3 greedy로 고정해 학습 전 응답을 얻는다 → 응답 8개 · 잘림 1개
  - 1-4 형식과 의미를 나눠 읽고 기록한다 → 형식 0/4 · 0/4 · `baseline.json`
- 학습할 행동: **JSON · 보류 · 인용 · 근거 읽기** → 2장 예제 72개 → 3장 SFT 전후 비교(같은 생성 설정)
- 2장 전에 직접 해 볼 것: `baseline.json` 내려받기, 직접 구현 실습

---

## 확인 문제

> 객관식 7 · 단답형 7, 섞어서 배치했어요. **정답 보기**를 누르면 열려요.

### FT1-Q1. 객관식 — 무엇으로 고칠까
"출장 숙박 한도가 85,000원에서 95,000원으로 바뀌었다"를 모델이 반영하게 하려면 가장 알맞은 방법은?

1. 95,000원 예제로 파인튜닝을 다시 한다
2. 검색 · 입력 문서를 새 규정으로 바꾼다 (RAG)
3. `repetition_penalty`를 높인다
4. `max_new_tokens`를 늘린다

<details>
<summary>정답 보기</summary>
<p><b>2. 문서를 바꾼다</b> — 자주 바뀌는 <b>지식(금액)은 문서로</b>, 지시해도 반복되는 <b>행동(근거 읽기 · JSON · 보류)은 학습으로</b>. 금액을 가중치에 외우게 하면 규정이 바뀔 때마다 다시 학습해야 해요.</p>
</details>

### FT1-Q2. 단답형 — 같은 질문 두 줄
over\_limit와 updated는 질문 문장이 똑같은데 정답이 반대예요. 이렇게 설계한 이유는?

<details>
<summary>정답 보기</summary>
<p>문서(TRAVEL-01 85,000 / TRAVEL-02 95,000)를 <b>읽어야만</b> 맞힐 수 있게 해서, 모델이 외운 답을 내는지 근거를 읽고 답하는지 가르려고요.</p>
</details>

### FT1-Q3. 객관식 — 두 축
다음 중 맞는 말은?

1. SFT와 LoRA는 같은 줄에서 하나를 고르는 선택지다
2. QLoRA는 SFT와 다른 학습 목표를 쓴다
3. DPO는 질문 하나에 모범답안 하나만 쓴다
4. LoRA로 SFT를 할 수 있다

<details>
<summary>정답 보기</summary>
<p><b>4.</b> SFT · DPO는 <b>학습 목표</b>(무엇을 정답 신호로), LoRA · QLoRA는 <b>학습 대상</b>(어떤 숫자를 바꾸나)이라 다른 축이에요. QLoRA도 목표는 SFT 그대로, DPO는 chosen vs rejected 두 답을 써요.</p>
</details>

### FT1-Q4. 단답형 — 정답 누수
`review_criteria`를 모델 입력에 넣으면 왜 안 될까요?

<details>
<summary>정답 보기</summary>
<p>정답 행동을 보고 푸는 셈이라(<b>정답 누수</b>) 그 점수는 학습 전 실력이 아니에요. 기준은 사람이 출력과 비교할 때만 쓰고, 평가 정답은 다른 필드 · 다른 파일에 둬요.</p>
</details>

### FT1-Q5. 객관식 — backward와 step
세 점수 예제에서 `scores` 값을 **실제로 바꾸는** 줄은?

1. `optimizer.step()`
2. `loss.backward()`
3. `optimizer.zero_grad()`
4. `F.cross_entropy(scores, target)`

<details>
<summary>정답 보기</summary>
<p><b>1. <code>step()</code></b> — <code>backward()</code>는 기울기만 계산해 <code>.grad</code>에 넣고, <code>zero_grad()</code>는 기울기 칸을 비워요. 갱신은 <code>step()</code>이 해요.</p>
</details>

### FT1-Q6. 단답형 — 기울기
점수 [0, 0, 0], 정답이 세 번째일 때 교차엔트로피의 기울기는? 왜 그 모양인가요?

<details>
<summary>정답 보기</summary>
<p><b>[0.333, 0.333, −0.667]</b>. L = −s_y + log Σ e^s를 s로 미분하면 <b>p − y</b>(y = 정답 one-hot). 정답 칸만 음수라 <code>s − lr × g</code>에서 정답 점수가 올라가요.</p>
</details>

### FT1-Q7. 객관식 — softmax 축
실제 모델 로짓 모양이 `[B, T, 151936]`일 때 후보 토큰 확률을 구하는 코드로 맞는 것은?

1. `logits.softmax(dim=0)`
2. `logits.softmax(dim=1)`
3. `logits.softmax(dim=-1)`
4. `logits.softmax()` 축 없이

<details>
<summary>정답 보기</summary>
<p><b>3. <code>dim=-1</code></b> — 어휘(후보) 축은 항상 마지막이에요. <code>dim=1</code>은 위치(T) 축으로 나눠 버려요. <code>-1</code>로 쓰면 <code>[1, 3]</code> 예제와 실제 모델에 같은 코드가 돼요.</p>
</details>

### FT1-Q8. 단답형 — detach와 clone
`scores.grad.detach()`만 하지 않고 `.clone()`까지 붙이는 이유는?

<details>
<summary>정답 보기</summary>
<p><code>detach()</code>는 미분 기록에서만 떼고 <b>메모리는 원본과 공유</b>해서 원본이 바뀌면 같이 바뀌어요. <code>clone()</code>으로 새 메모리에 복사해야 그 순간의 기울기가 보관돼요(기울기는 <code>backward()</code>마다 누적됨).</p>
</details>

### FT1-Q9. 객관식 — 생성 설정
이 저장소 기본 생성 설정을 명시하지 않고 그대로 쓰면 생기는 문제는?

1. 모델 가중치가 조금씩 바뀐다
2. sampling이라 실행마다 답이 달라져 전후 비교가 무너진다
3. 출력이 항상 192토큰에서 잘린다
4. 채팅 템플릿이 적용되지 않는다

<details>
<summary>정답 보기</summary>
<p><b>2.</b> 기본값이 sampling(temperature 0.7 · top_p 0.8 · top_k 20)이에요. 생성 설정은 가중치를 바꾸지 않고, 비교할 땐 greedy(<code>do_sample=False</code>, <code>num_beams=1</code>)로 코드에 명시해요.</p>
</details>

### FT1-Q10. 단답형 — 새 토큰만
`generated[0, input_length:]`처럼 자르는 이유와, 형식 실패를 모델 탓으로 읽기 전에 먼저 확인할 것은?

<details>
<summary>정답 보기</summary>
<p><code>generate</code>는 <b>입력 + 새 토큰</b>을 돌려줘서 입력 뒤만 읽어요. 그리고 <b>잘림</b>(<code>length_limited</code>: 192개를 채웠는데 EOS로 안 끝남)부터 확인해요. simple/updated가 그 예.</p>
</details>

### FT1-Q11. 객관식 — 코드 펜스
explicit 응답이 ` ```json {…} ``` `로 나왔을 때 `inspect_response`의 올바른 처리는?

1. 펜스를 지우고 다시 `json.loads` 해서 통과시킨다
2. `schema_ok`만 False로 둔다
3. `citation_ids_ok`만 확인한다
4. 원문 그대로 `json.loads` → 실패 → 세 값 모두 False

<details>
<summary>정답 보기</summary>
<p><b>4.</b> 펜스를 지워서 성공으로 바꾸면 지표가 부풀어요. 앞 단계가 실패하면 뒤는 보지 않고 False로 두어, 거짓 세 개를 독립 오류 세 개로 세지 않아요.</p>
</details>

### FT1-Q12. 단답형 — 형식 통과 ≠ 의미
"형식은 맞지만 경계 판단이 틀린 예"가 `[True, True, True]`로 나오는 게 왜 이 실습의 핵심일까요?

<details>
<summary>정답 보기</summary>
<p>자동 검사는 파싱 · 필드 · 인용 ID만 보고 <b>금액 비교와 승인 조건은 판정 못 해요.</b> 그래서 사람이 원문을 읽고 <code>review_kind</code>를 고르고, 그걸 학습 행동(<code>boundary_pair</code>)으로 연결해요.</p>
</details>

### FT1-Q13. 객관식 — 재현의 네 가지
`baseline.json`에 함께 남기는 "실험 재현의 네 가지"에 **들지 않는** 것은?

1. 노트북 실행에 걸린 시간
2. 모델 버전 (`model_id` + `revision`)
3. 데이터 (`cases`)
4. 설정 (`generation` · dtype · runtime)

<details>
<summary>정답 보기</summary>
<p><b>1.</b> 네 가지는 모델 버전 · 데이터 · 설정 · 원문(<code>raw_response</code>)이에요. 이걸 같이 남겨야 나중에 "무엇이 바뀌어서 결과가 달라졌나"를 답할 수 있어요.</p>
</details>

### FT1-Q14. 단답형 — 손실은 낮은데
직접 구현 ③에서 평균 손실이 0.371까지 내려갔는데 ④에서 "이하 → 승인 필요"가 나와요. 왜일까요?

<details>
<summary>정답 보기</summary>
<p>바로 앞 토큰 하나만 보는 모델이라 <code>승인</code> 앞이 <code>이하</code>였는지 <code>초과</code>였는지 몰라요(그 자리는 50:50이 최선). <b>손실이 낮다 ≠ 업무 판단이 맞다.</b> 그래서 의미는 사람이 따로 읽고, 실제 모델은 긴 문맥을 봐요.</p>
</details>
