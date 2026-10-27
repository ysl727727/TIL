# 4강. Transformer 전체 구조 — Encoder · Decoder · Position · FFN · Residual · LayerNorm · KV Cache

> 2026-09-04 학습 기록. 딥러닝 심화 4강(4-1 ~ 4-6) 이론을 "쉽게 정리" 노트로 공부했습니다. 3강의 Attention이 **부품**이었다면, 4강은 그 부품을 Embedding · Position · FFN · Residual · LayerNorm · Output Head와 엮은 **전체 구조**입니다. 별도 실습 노트북은 없고, 노트 안의 PyTorch 코드로 shape을 확인했습니다.

> 폴더 번호는 올린 순서라 09이지만, 강의 순서상 [3장 Attention](../03-attention-and-multihead/)과 [5강 사전학습 LM](../04-pretrained-language-models/) 사이입니다.

## 학습 목표

- Self-Attention · Transformer Block · Transformer Model을 구분한다.
- Encoder-only(BERT) · Decoder-only(GPT) · Encoder-Decoder(T5)가 어느 방향 문맥을 보는지 구분한다.
- hidden state `[B, L, D]`와 logits `[B, C]` / `[B, L, V]`의 차이를 안다.
- Learned · Sinusoidal 위치 정보를 왜 더하는지, Padding Mask와 Causal Mask가 어떻게 다른지 설명한다.
- FFN · Residual · LayerNorm(Pre-Norm)의 역할과 shape 조건을 안다.
- 학습은 병렬, 생성은 순차인 이유와 Prefill/Decode, KV Cache가 무엇을 저장하는지 설명한다.

## 전체 흐름

```text
문자열 → tokenizer → input_ids [B,L], attention_mask [B,L]
 → Token Embedding + Position 정보          [B,L,D]
 → Block × N  ( Self-Attention → +Residual → LayerNorm
                 → FFN(D → D_ff → D) → +Residual → LayerNorm )   [B,L,D] 유지
 → Output Head
     문장 분류  [B,C]   (대표 표현 → Classification Head)
     토큰 분류  [B,L,C]
     Causal LM [B,L,V]  (각 위치 → LM Head)
```

## 핵심 이론

### 1. 구조 조감 (4-1)

| 이름 | 범위 |
| --- | --- |
| Self-Attention | 토큰끼리 서로 참고해 새 표현을 만드는 **연산 하나** |
| Transformer Block | Attention + FFN + Residual + LayerNorm 한 층 |
| Transformer Model | Embedding + Block 여러 층 + Output Head |

| 계열 | 보는 방향 | 용도 | 대표 |
| --- | --- | --- | --- |
| Encoder-only | 앞뒤 전부 | 분류, 검색, 개체명 | BERT |
| Decoder-only | 왼쪽(과거)만 | 생성, 대화, 코드 | GPT |
| Encoder-Decoder | 이해 + 생성 | 번역, 요약 | T5 |

- 원조 Transformer는 번역기 구조. Encoder 출력(`memory`)은 문장을 벡터 하나로 압축한 게 아니라 **위치별 문맥 표현의 집합** `[B, L_src, D]`이고, Decoder는 Cross-Attention으로 이걸 참고해요.
- 본체가 내는 건 hidden state까지. **Head를 붙여야** logits가 나오고, 확률은 softmax까지 해야 나와요. `[B,L,D]`와 `[B,L,V]`는 둘 다 3축이지만 마지막 축의 뜻이 완전히 달라요.

### 2. 위치 정보 (4-2)

- Self-Attention은 순서를 모르는 연산이라 "나는 너를 좋아한다"와 "너는 나를 좋아한다"를 구분하려면 위치 정보가 필요해요.
- `token_hidden [B,L,D] + position_hidden [1,L,D]` → 원소별 덧셈, 축 구조는 그대로.
- Learned Position Embedding(`nn.Embedding(max_len, D)`) vs Sinusoidal(고정 sin/cos). 최신 LLM은 Q·K를 회전시키는 **RoPE**를 많이 써요.

### 3. Encoder Block과 Padding Mask (4-3)

- Encoder Block이 하는 일은 딱 두 가지: **토큰 간 소통**(Self-Attention) + **토큰별 가공**(Position-wise FFN). 입력과 출력 shape `[B,L,D]`가 같아서 층을 쌓을 수 있어요.
- 문장 표현은 Masked Mean Pooling: `PAD` 자리는 0으로 만들고 진짜 토큰 수로 나눠요.
- **mask 규칙이 API마다 반대**: Hugging Face `attention_mask`는 `1 = 사용`, PyTorch bool mask는 `True = 차단`.

### 4. Decoder-only와 Causal Mask (4-4)

```python
def make_causal_mask(L):
    return torch.triu(torch.ones(L, L, dtype=torch.bool), diagonal=1)   # True = 미래(차단)
```

- 행 하나 = "이 위치가 어디까지 볼 수 있나". i번째 토큰은 0~i까지(자기 자신 포함).
- `diagonal=1`이 정상, `diagonal=0`이면 자기 자신까지 막아 버리는 실수.
- **Label shift**: 입력 `<BOS> 나는 AI를 배운다` / 정답 `나는 AI를 배운다 <EOS>` → 문장 하나로 다음 토큰 예측 문제 4개.
- 실험으로 확인: 마지막(미래) 위치 값을 크게 바꿔도 0번 위치 출력은 그대로여야 마스크가 작동한 것.

### 5. FFN · Residual · LayerNorm (4-5)

| 부품 | 역할 | shape |
| --- | --- | --- |
| Position-wise FFN | 각 토큰 벡터 **내부**를 변환(`D → D_ff → D`, 보통 4배로 넓혔다가 다시 줄임) | `[B,L,D]` 유지 |
| Residual `X + Sublayer(X)` | 원본을 우회로로 보존하고 **변화량만 더함**, 깊은 층의 gradient 지름길 | 두 텐서 shape이 같아야 덧셈 가능 |
| LayerNorm | **한 토큰의 D축 안에서** 평균·분산 정규화 후 학습 가능한 scale·bias 적용 | `[B,L,D]` 유지 |

- BatchNorm은 샘플들끼리, LayerNorm은 한 샘플(한 토큰) 안에서 통계를 내요.
- Post-Norm(계산 후 정규화) vs **Pre-Norm**(정규화 후 계산, 최신 LLM 기본). 최신 모델은 **RMSNorm**, FFN 활성화는 **SwiGLU**를 많이 써요.

### 6. Shape · Mask · Memory 종합 (4-6)

| | Padding Mask | Causal Mask |
| --- | --- | --- |
| 목적 | PAD 무시 | 미래 차단 |
| shape | `[B,L]` | `[L,L]` |
| 문장마다 | 보통 다름 | 보통 같음 |
| 쓰는 곳 | Encoder·Decoder 모두 | 생성용 Decoder |

- Attention 점수 칸 수는 `B × H × L × L`. L이 2배면 4배(제곱 증가) → 긴 컨텍스트가 비싼 이유.
- **학습은 병렬**(정답을 이미 알아서 causal mask만 씌우면 모든 위치 동시 계산, Teacher Forcing), **생성은 순차**(다음 토큰이 아직 없음).
- **Prefill**: 프롬프트 전체를 한 번에 처리하며 K·V를 계산. **Decode**: 새 토큰 1개씩 반복.
- **KV Cache**: 과거 토큰의 K·V만 저장해 재사용. 가중치도, attention 점수 전체도 아니에요. 반복 계산을 줄일 뿐 순차성은 그대로.

```text
KV Cache bytes ≈ 2 × num_layers × batch × cached_length × num_kv_heads × D_head × bytes
```

- GQA/MQA는 `num_kv_heads`를 줄여 KV Cache 메모리를 줄여요(3장 GQA 계산과 연결).

## 코드로 확인한 shape

```python
transformer = nn.Transformer(d_model=16, nhead=4, num_encoder_layers=2,
                             num_decoder_layers=2, dim_feedforward=32,
                             dropout=0.0, batch_first=True)
source_hidden = torch.randn(2, 5, 16)                              # [B,S,D]
target_hidden = torch.randn(2, 4, 16)                              # [B,T,D]
target_mask = nn.Transformer.generate_square_subsequent_mask(4)    # [T,T]
decoder_hidden = transformer(src=source_hidden, tgt=target_hidden, tgt_mask=target_mask)  # [2,4,16]
logits = nn.Linear(16, 100)(decoder_hidden)                        # [2,4,100] = [B,T,V]
```

## 질문과 새로 알게 된 점

- "Transformer = Self-Attention"이 아니다. Attention은 엔진 부품 하나, Transformer는 자동차 전체.
- "모든 Transformer는 Encoder+Decoder"도 아니다. BERT·GPT처럼 한쪽만 쓰는 경우가 많아요.
- Residual은 "입력을 그대로 복사"가 아니라 `X + Sublayer(X)`라서 학습한 변화가 분명히 들어가요.
- LayerNorm 출력이 항상 평균 0·분산 1인 건 아니에요(학습되는 scale·bias가 다시 곱해짐).
- 챗봇에서 첫 글자가 나오기까지는 조금 걸리고(Prefill) 그 뒤로 글자가 좌르륵 나오는(Decode) 이유가 이 구조 때문이었어요. 9장 `generate()`의 `use_cache`, RAG 1장 KV cache 설명으로 이어져요.

## 확인 문제

### T-Q1. 구조 고르기 (4-1)

"문장 속 개인정보 토큰 찾기"에 가장 자연스러운 구조는?

① Decoder-only  
② Encoder-only + 토큰 분류 Head `[B,L,C]`  
③ Encoder-Decoder  
④ Head 없이 hidden state만

<details>
<summary>정답 보기</summary>

**②** — 앞뒤 문맥을 모두 보고 토큰마다 라벨을 붙이는 문제라 Encoder-only + Token Classification. 생성이 필요 없어요.

</details>

### T-Q2. Causal Mask (4-4)

`torch.triu(ones(L, L), diagonal=0)`으로 마스크를 만들면?

① 정상적인 causal mask  
② 자기 자신 위치까지 막아서 각 토큰이 자신조차 못 보는 잘못된 mask  
③ padding mask가 된다  
④ 아무것도 막지 않는다

<details>
<summary>정답 보기</summary>

**②** — 대각선(자기 자신)부터 True(차단)가 돼요. 미래만 막으려면 `diagonal=1`.

</details>

### T-Q3. KV Cache (4-6)

KV Cache가 저장하는 것은?

① 모델 가중치  
② 과거 토큰들의 Key와 Value  
③ 지금까지의 attention 점수 행렬 전체와 최종 확률  
④ 다음에 나올 토큰 후보

<details>
<summary>정답 보기</summary>

**②** — 새 토큰의 Query가 과거 K·V를 다시 참고해야 해서 그것만 저장해요. 계산 반복은 줄지만 생성이 병렬이 되지는 않아요.

</details>

### T-Q4. 서술형 — 학습은 병렬, 생성은 순차

같은 Decoder-only 모델인데 학습은 한 번에 계산하고 생성은 한 토큰씩 해야 하는 이유를 Teacher Forcing, Causal Mask, Prefill/Decode로 설명하세요.

<details>
<summary>예시 답안</summary>

학습 때는 정답 문장 전체를 이미 알고 있어서(Teacher Forcing) 입력과 정답을 한 칸 밀어 놓고, Causal Mask로 각 위치가 미래를 못 보게만 하면 모든 위치의 다음 토큰 예측을 동시에 계산할 수 있어요. 생성 때는 다음 토큰이 아직 존재하지 않아서, 프롬프트 전체를 한 번에 읽는 Prefill 뒤에는 토큰 하나를 만들고 그걸 입력에 붙여 다시 예측하는 Decode를 반복할 수밖에 없어요. KV Cache는 이 반복에서 과거 K·V를 다시 계산하지 않게 해 줄 뿐 순차성 자체는 없애지 못해요.

</details>
