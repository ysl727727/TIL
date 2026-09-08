# Chapter 4: Pretrained Language Models (BERT vs GPT)

> 2026-09-07 학습 기록. 5-1, 5-2, 5-4강 이론을 정리했습니다. 실습 노트북은 아직 없고 이론만 정리된 상태이며(주말로 이월), 아래 Core Theory는 `딥러닝_심화_5장_사전학습언어모델_정리.md`를 기반으로 합니다.

## Learning Goals

- 언어모델이 토큰의 등장 패턴·순서·문맥 관계를 학습하는 것이며, 사실을 정확히 암기하는 것이 아님을 구분한다.
- 사전학습(대규모 비라벨 데이터로 일반 패턴 학습)과 Fine-tuning(목적별 데이터로 추가 학습)의 관계를 설명한다.
- LM Objective가 "사전학습 중 반복해서 풀도록 설계한 문제"이며, 모델의 구조(정보가 흐르는 방식)와는 별개의 개념임을 구분한다.
- Masked LM(BERT, 양방향 문맥)과 Causal LM(GPT, 왼쪽 문맥만)의 차이와 각각 자연스러운 활용처를 설명한다.
- BERT의 `[CLS]`/`[SEP]`/`[MASK]`/`[PAD]` 역할과 Token/Position/Token Type embedding 구성을 이해한다.
- GPT의 Causal Self-Attention, 한 칸 shift 구조, Autoregressive Generation(`generate()`) 흐름을 이해한다.

## Practice Files

아직 실습 노트북이 없습니다. 5장 실습은 주말(2026-09-12~13)로 이월했습니다.

## Core Theory

### 1. 언어모델과 사전학습

- 언어모델은 문장을 "이해"한다기보다, 학습 데이터에서 관찰한 토큰·문맥의 통계적/구조적 패턴을 파라미터에 학습한 것으로 보는 게 더 정확하다.
- 적은 라벨 데이터로 처음부터 분류 모델을 학습하면 단어 의미·문장 관계·라벨 기준을 동시에 배워야 해서 어렵다. 그래서 먼저 대규모 비라벨 텍스트로 일반 언어 패턴을 학습(Pretraining)한 뒤, Fine-tuning·Task Head 추가·Feature 활용·Prompt 기반 사용 등으로 목적별 데이터에 적용한다.
- LM Objective는 입력을 어떻게 가공하고, 어떤 위치를 예측하게 하며, 어떤 문맥을 볼 수 있게 하는지를 정의한 "반복해서 푸는 문제"다. Objective와 Loss는 다른 개념이지만 연결돼 있다 — Objective는 풀도록 만든 문제, Loss는 예측과 정답의 차이를 수치화한 것이다.
- 모델의 능력은 Objective 하나로 결정되지 않는다 — 구조, 데이터 규모/품질, tokenizer, 모델 크기, Fine-tuning 방식이 함께 영향을 준다.

### 2. Masked LM vs Causal LM

| 비교 항목 | Masked LM | Causal LM |
| --- | --- | --- |
| 대표 질문 | 가려진 토큰은? | 다음 토큰은? |
| 문맥 방향 | 왼쪽+오른쪽 | 왼쪽+현재 |
| 대표 모델 | BERT | GPT |
| 자연스러운 출발점 | 문맥 표현, 분류, 토큰 이해 | 이어쓰기, 생성, 대화 |

- 구조(정보가 모델 안에서 어떻게 흐르는가)와 Objective(학습할 때 어떤 문제의 loss를 줄이는가)는 따로 봐야 한다 — `BERT = Encoder-only + Masked LM`, `GPT = Decoder-only + Causal LM`처럼 조합으로 이해해야 새 모델을 만났을 때 혼란이 없다. Model card에서 `architecture`, `pretraining objective`, `intended use`를 각각 따로 확인해야 한다.
- Downstream task(사전학습 모델을 실제 목적에 적용하는 구체적 문제)의 "자연스러운 후보"는 절대 규칙이 아니다 — 지원 언어, 학습 데이터/도메인, model card·라이선스, 파라미터 수·VRAM, 지연시간·비용, 실제 평가 성능을 함께 확인해야 한다.

### 3. BERT: Encoder-only와 Masked LM

- BERT(Bidirectional Encoder Representations from Transformers)는 Transformer Encoder를 여러 층 쌓아 입력의 각 토큰을 문맥 반영 표현으로 만드는 사전학습 모델이며, 대표 출력은 `last_hidden_state: [B, L, D]`다.
- Bidirectional은 "거꾸로 읽는다"가 아니라 각 토큰 표현을 만들 때 왼쪽+오른쪽 토큰을 함께 참고할 수 있다는 뜻이다.
- 정답을 그대로 보여주면 모델이 복사만 하게 되므로, 일부 위치를 가려서 원래 토큰을 맞히게 한다(Masked Language Modeling). 원 BERT 논문은 선택된 15% 위치를 80% `[MASK]` 교체, 10% 임의 토큰 교체, 10% 원래 토큰 유지로 처리했다(정답은 세 경우 모두 원래 토큰).
- MLM loss는 선택된 위치만 사용한다: `hidden state [B,L,D] → LM Head → logits [B,L,V]`.
- `[CLS]`(입력 맨 앞, 문장 분류의 대표 표현으로 자주 활용되지만 Fine-tuning+Head 없이 자동으로 좋은 결과를 주지 않음), `[SEP]`(문장 끝/쌍 경계), `[MASK]`(MLM 예측 위치), `[PAD]`(배치 길이 맞춤) — 문자열을 직접 외우기보다 `tokenizer.cls_token` 등으로 확인해야 한다.
- 입력 표현 = Token Embedding + Position Embedding + Token Type Embedding(문장 쌍 구분, 단일 문장은 보통 전부 0). 모든 Encoder-only 모델이 `token_type_ids`를 쓰는 것은 아니다(RoBERTa는 보통 안 씀).

### 4. GPT: Decoder-only와 Causal LM

- GPT(Generative Pre-trained Transformer)는 Decoder-only Block을 여러 층 쌓고 이전 토큰으로 다음 토큰을 예측하도록 사전학습된 생성형 모델이다. 원래 Encoder-Decoder의 Decoder와 달리 별도 Encoder와 Cross-Attention이 일반적으로 없다(`Causal Self-Attention + FFN + Residual + LayerNorm`).
- Causal Self-Attention은 각 위치에서 미래 토큰을 볼 수 없다 — 정답 토큰을 미리 보여주면 복사만 하게 되는 정보 누출을 막기 위해서다.
- Causal LM Objective는 입력·정답 토큰을 한 칸 shift해 다음 토큰을 예측한다: `<BOS> I learn AI`를 보고 각각 `I`, `learn`, `AI`, `<EOS>`를 예측. 학습 시엔 Causal Mask로 미래 정보를 차단한 채 여러 위치의 loss를 병렬 계산할 수 있지만(Teacher Forcing), 생성 시엔 방금 만든 토큰을 다음 입력에 추가하며 순차적으로 진행한다.
- `outputs.logits`는 `[B,L,V]`이며, 다음 토큰 후보는 보통 마지막 실제 토큰 위치의 `[:, -1, :]`로 확인한다(padding이 있는 배치에서는 padding side와 attention mask를 함께 고려해야 함).
- `generate()`는 종료 조건(EOS, `max_new_tokens`, stop sequence 등)까지 토큰 선택+입력 갱신을 반복한다. Greedy(최고 점수 선택)가 이 강의에서 다룬 방식이며, Sampling·Beam Search는 이후 강의에서 다룬다.
- 생성 결과 해석 시 주의: 다음 토큰 확률은 사실성 점수가 아니고, Prompt 표현에 민감하며, 생성이 길어질수록 오류가 누적될 수 있고, Greedy가 항상 최선은 아니다.
- (선택) Causal LM의 label/loss mask: padding 위치와 prompt 위치(response-only 학습 시)는 `labels=-100`으로 학습 대상에서 제외한다. Causal mask(미래 차단)와 loss mask(어느 위치를 학습할지)는 이름은 비슷하지만 역할이 다르다.

## Environment

이 챕터는 아직 실습 코드가 없습니다. 실습을 추가하면 `torch`, `transformers`가 필요합니다.
