# Chapter 8: Text Generation and Chat Templates

> 2026-09-09 학습 기록. 9-1, 9-2, 9-3, 9-4, 9-5강 이론을 정리했습니다. 실습 노트북은 아직 없고 이론만 정리된 상태이며(주말로 이월), 아래 Core Theory는 `9강_generate__로_시작하는_텍스트_생성과_Chat_Template.pdf`를 기반으로 합니다.

## Learning Goals

- Forward pass(logits 한 번 계산)와 `generate()`(다음 토큰 선택+입력에 붙이기를 반복하는 autoregressive 과정)의 차이를 설명한다.
- `max_length`(입력+출력 전체 길이)와 `max_new_tokens`(새로 생성할 토큰 수만 제한)의 차이를 구분한다.
- Greedy decoding(결정적, 안정적)과 Sampling(비결정적, 다양함)의 장단점과 각각 적절한 상황을 구분한다.
- Temperature(분포의 날카로움 조절), Top-k(상위 k개 후보만 유지), Top-p(누적 확률 p까지 후보 유지)가 각각 어떤 축을 제어하는지 설명한다.
- Chat model 입력이 단순 문자열이 아니라 `role`/`content` 구조의 messages임을 이해하고, `system`/`user`/`assistant` role의 차이를 설명한다.
- `apply_chat_template()`이 필요한 이유와 `add_generation_prompt`의 역할을 이해하고, formatted text → tokenized input → generate 순서로 입력을 디버깅하는 흐름을 익힌다.

## Practice Files

아직 실습 노트북이 없습니다. 9장 실습은 주말(2026-09-12~13)로 이월했습니다.

## Core Theory

### 1. Forward Pass vs generate() (9-1강)

| 구분 | Forward pass | generate() |
| --- | --- | --- |
| 목적 | 주어진 입력의 logits 계산 | 새 텍스트 생성 |
| 반복 여부 | 보통 한 번 | 여러 번(토큰마다) |
| 출력 | logits, hidden states | 생성된 token ids 또는 text |
| 사용 예 | loss 계산, 다음 토큰 점수 확인 | 챗봇 답변, 문장 생성 |

- Autoregressive 생성 루프: prompt → `input_ids` → 다음 토큰 후보 logits 계산 → decoding strategy로 토큰 1개 선택 → `input_ids` 뒤에 붙이기 → 종료 조건(EOS, `max_new_tokens`, stopping criteria, timeout/stop string)까지 반복.
- `max_length`(입력+출력 전체 길이 제한)와 `max_new_tokens`(새로 생성할 토큰 수만 제한, prompt 길이와 무관)는 다르다 — 실습에서는 prompt 길이가 매번 달라도 출력량을 비슷하게 제어할 수 있는 `max_new_tokens`가 이해하기 쉽다.
- `generated_ids`는 prompt 토큰과 새로 생성된 토큰을 모두 포함하므로, 새로 생성된 부분만 보려면 `generated_ids[0, input_length:]`처럼 입력 길이를 기준으로 잘라내야 한다.
- (선택) `use_cache=True`이면 Prefill(prompt 전체 처리)에서 만든 K/V를 Decode(토큰 하나씩 처리) 단계에서 재사용해 매 step마다 prompt 전체 K/V를 다시 만들지 않는다 — cache sequence length가 누적 토큰 길이에 따라 늘어나며, MHA/GQA의 `H_kv`가 cache 메모리에 미치는 영향은 3장에서 배운 GQA 개념과 직결된다.

### 2. Greedy Decoding vs Sampling (9-2강)

- Greedy decoding: 매 단계 가장 높은 확률의 토큰을 선택. 안정적이고 재현하기 쉽지만 단조롭거나 한 번의 잘못된 선택이 이후 경로를 제한할 수 있다. 정보 추출처럼 출력이 안정적이어야 하거나 같은 입력에 같은 답변이 중요할 때 적합하다.
- Sampling: 확률 분포에서 토큰을 뽑아 항상 1등만 선택하지 않으므로 더 다양한 결과가 나온다. 아이디어 생성·브레인스토밍·창작처럼 다양성이 중요하거나 단일 정답이 없는 open-ended generation에 적합하다. 다양성은 높이지만 사실성·형식 안정성을 보장하지 않으므로 중요 업무에는 사람 검토/후처리 검증이 필요하다.
- Beam search: 여러 후보 경로를 동시에 유지하며 누적 점수로 최종 경로를 선택한다. 번역·요약처럼 목적이 명확한 생성에 적합하지만 챗봇형 답변에서는 반복적이거나 다양성이 낮은 결과를 만들 수 있다.
- `do_sample=False`이면 `temperature`/`top_k`/`top_p`를 바꿔도 결과에 반영되지 않는다(sampling이 꺼져 있으므로). `set_seed(42)`로 sampling 결과가 반복될 가능성이 높아지지만, GPU 연산·라이브러리 버전·모델 checkpoint·병렬 처리 방식에 따라 완전한 재현이 보장되지는 않는다 — 재현성에는 seed뿐 아니라 model ID/revision/라이브러리 버전/generation config를 함께 기록해야 한다.

### 3. Temperature, Top-k, Top-p (9-3강)

- Temperature: 다음 토큰 확률 분포의 날카로움을 조절한다. 낮으면 1등 후보에 확률이 집중되어 안정적·보수적(다양성 부족 가능), 높으면 후보 간 확률 차이가 줄어 다양하지만 의미가 흐려질 수 있다.
- Top-k: 확률이 높은 상위 k개 후보만 남기고 그 안에서 sampling한다(예: `top_k=10`이면 상위 10개만 후보).
- Top-p(Nucleus sampling): 누적 확률이 p에 도달할 때까지 후보를 남긴다. 확률이 한두 후보에 몰려 있으면 적은 후보만, 분포가 넓으면 더 많은 후보가 남는 식으로 상황에 따라 후보 수가 달라진다.
- 파라미터 실험 해석 순서: ① `do_sample=True`인지 먼저 확인 → ② prompt·model revision·seed·`max_new_tokens`·stop 조건 고정 → ③ 한 번에 한 축만 바꿔 영향 방향 관찰 → ④ 여러 seed에서 평균뿐 아니라 실패 사례·분산도 기록 → ⑤ 품질과 함께 TTFT·TPOT·출력 토큰 수 확인. 세 값(temperature/top-k/top-p)을 동시에 크게 바꾼 결과만 보고 어느 설정이 원인인지 단정하지 않는다.
- `do_sample=False`에서는 sampling용 파라미터로 해석하지 않으며, `temperature=0`처럼 구현마다 다르게 처리되는 값은 API 동작을 직접 확인해야 한다.

### 4. Chat Message Role과 Chat Template (9-4강)

- Chat model은 대화 데이터로 학습됐기 때문에 "누가 말했는지"에 대한 역할 정보가 중요하다. 같은 문장이라도 `system` 지침인지, `user` 질문인지, `assistant`의 이전 답변인지에 따라 의미가 다르다.

| role | 의미 | 예시 |
| --- | --- | --- |
| system | 모델의 전반적 행동 지침 | "친절하고 간결하게 답하세요." |
| user | 사용자의 요청 | "Transformer를 쉽게 설명해줘." |
| assistant | 모델의 이전 답변 | "Transformer는 Attention 기반 구조입니다." |

- role 이름은 모델/템플릿이 기대하는 값과 정확히 맞아야 한다 — `usr`, `bot`처럼 임의로 쓰면 template 적용이 실패하거나 예상과 다르게 동작할 수 있다.
- 모델마다 대화 형식이 다르다(`<|user|>` 특수 토큰, `[INST] ... [/INST]` 형식 등). `apply_chat_template()`은 tokenizer 안의 규칙으로 `messages` 리스트(모델과 무관한 공통 구조)를 모델별 포맷 문자열로 변환한다. 직접 문자열을 조합하면 role 순서·generation prompt·특수 토큰을 빠뜨리기 쉽다.
- 멀티턴 대화에서는 이전 user/assistant 메시지를 순서대로 넣지만, 대화가 길어지면 token budget을 초과할 수 있어 오래된 이력을 요약하거나 일부만 유지하는 전략이 필요하다.

### 5. apply_chat_template과 입력 디버깅 (9-5강)

- 디버깅 흐름: ① messages(role 점검) → ② formatted text(`tokenize=False`로 문자열 확인) → ③ tokenized(`return_tensors="pt"`로 `input_ids` shape·길이 확인) → ④ `generate()`. 출력이 이상하면 decoding 설정보다 먼저 입력 formatted text와 role 구조부터 점검한다.
- `add_generation_prompt=True`는 다음 assistant 답변이 시작될 위치를 표시하는 형식을 추가한다 — 생성용 입력을 만들 때는 보통 이 값을 켠다. 대부분의 generation prompt는 문자열 끝부분에 추가되므로 실습에서는 전체 문자열보다 마지막 부분을 보는 것이 유용하다.

| 자주 나는 오류 | 원인 | 해결 |
| --- | --- | --- |
| `chat_template`이 없습니다 | tokenizer에 template이 정의되지 않음 | 다른 chat model tokenizer 사용 또는 template 정의 확인 |
| role 오류 | `user`/`assistant`/`system` 외 임의 role 사용 | 모델 문서의 role 규칙 확인 |
| 출력이 이상합니다 | generation prompt 누락 가능성 | `add_generation_prompt=True` 확인 |
| token 길이가 너무 깁니다 | 대화 이력 과도하게 길어짐 | 요약, truncation, history pruning |
| 특수 토큰이 중복됩니다 | 직접 포맷한 문자열에 template을 또 적용 | messages 원본에만 template 적용 |

- (선택) Decoder-only batch의 Left Padding과 Context Budget: 생성 batch는 마지막 열에서 다음 토큰 logits를 읽으므로 decoder-only 모델은 left padding을 권장하는 경우가 많다(짧은 시퀀스 왼쪽에 PAD를 채움). `attention_mask`는 PAD 위치를 0으로 표시한다. Context 예산은 대략 `prompt tokens + max_new_tokens <= effective context limit`로 잡으며, chat template의 system/role 토큰과 검색 문서도 prompt 길이에 포함되므로 truncation이 필요하면 system 지시나 최신 user 요청을 무심코 잘라내지 않도록 우선순위를 정해야 한다.

## Environment

이 챕터는 아직 실습 코드가 없습니다. 실습을 추가하면 `transformers`, `torch`가 필요합니다.
