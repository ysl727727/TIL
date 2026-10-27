# 3~5장. Transformer Attention · SFT와 Preference Alignment · LLM API와 응답 정책

> 2026-09-11 학습 기록. "딥러닝 실전 & 프롬프트 엔지니어링" 3·4·5장 이론 PDF를 정리하고, 5장 실습으로 OpenAI Responses API에 첫 요청을 보내 봤습니다. 3장은 딥러닝 심화에서 배운 Attention을 다시 정리하는 장이고, 4장은 Base Model이 대화형 모델이 되는 과정(SFT → RLHF/DPO), 5장은 API 요청·응답 구조와 System/Developer Prompt 설계입니다.

## 학습 목표

- Q·K·V가 "같은 입력의 세 관점"이라는 것과 scaling → masking → softmax → Value 가중합 순서를 다시 확인한다.
- Base Model / SFT / Instruction Model의 차이와, SFT가 잘 바꾸는 것(행동·형식)과 못 바꾸는 것(최신 지식)을 구분한다.
- Preference 데이터(`prompt`, `chosen`, `rejected`), Reward Model, RLHF(PPO)와 DPO의 흐름 차이를 설명한다.
- Responses API의 최소 요청(`model` + `input`)과 응답의 `id` · `status` · `usage` · `output_text`를 읽는다.
- 좋은 Developer Prompt를 역할 · 맥락 · 범위 · 제약 · 출력 형식 · 성공 기준을 담은 "작은 계약서"로 쓴다.

## 실습 파일

| 장 | 주제 | 상태 |
| --- | --- | --- |
| 3장 | Q/K/V와 Score, Scaling/Masking/Softmax, Multi-Head shape 디버깅 | 📘 이론 ([딥러닝 심화 3장](../../deep-learning-advanced/03-attention-and-multihead/)에서 실습) |
| 4장 | Base Model → SFT → Instruction Model, Preference Data · Reward Model · RLHF/PPO · DPO | 📘 이론 |
| 5장 | API 요청/응답 구조, System/Developer Prompt와 응답 정책 | 🧪 `api_docs_first_request.ipynb` 실행 (JSON 확인 → 요청 → 응답 전체 보기) |

## 핵심 이론

### 1. Attention 다시 보기 (3장)

- Q·K·V는 서로 다른 데이터가 아니라 같은 입력을 **찾을 정보 · 비교용 색인 · 실제 내용**으로 투영한 결과.
- `Q @ K.T`는 아직 확률이 아니고, scaling → masking → softmax를 거쳐야 attention weight.
- Causal mask는 `-inf`(또는 매우 작은 값)로 처리해야 해요. **0으로는 부족**(softmax 뒤에도 0이 아닌 확률이 남음).
- Multi-Head는 shape이 같아도 transpose 순서가 틀리면 값이 섞여서, 값보다 **축 순서**를 추적하는 게 핵심.

### 2. Base Model에서 정렬된 모델까지 (4장)

```text
Base Model (텍스트를 잘 이어 쓰는 모델)
 → SFT: (지시, 정답 응답) 쌍으로 지시를 따르는 법 학습 → Instruction Model
 → Preference Alignment: "더 나은 응답"의 기준을 비교 데이터로 학습
      RLHF: 후보 응답 생성 → 사람이 순위 → Reward Model 학습 → PPO로 policy 조정
      DPO : prompt + chosen + rejected 쌍으로 policy를 직접 학습
```

- SFT는 **행동**(형식·말투·처리 순서)을 잘 바꾸지만, 최신 지식이나 실시간 정보는 RAG·Tool이 더 적합해요.
- Preference record: `{"prompt": …, "chosen": 더 선호하는 응답, "rejected": 덜 선호하는 응답}`. 순위 1위 vs 2위로 쌍을 만들어요.
- "그냥 더 좋아 보인다"로 평가하면 데이터가 흔들려서 **rubric을 먼저** 만들고 평가자가 같은 기준을 써요.
- PPO는 Reward Model + 온라인 생성(rollout)이 필요해 복잡하지만 유연하고, DPO는 고정된 pair로 직접 최적화해 단순해요.
- 위험: 선호의 주관성·편향, **reward hacking**(점수만 높이는 방향으로 학습).

### 3. LLM API와 응답 정책 (5장)

```python
client = OpenAI(api_key=...)            # 키는 코드에 쓰지 않고 환경 변수·Secrets로
response = client.responses.create(
    model="...",
    instructions="처음 배우는 사람에게 한국어로, 예시 하나를 포함해 두 문장으로.",
    input="HTTP가 뭐야?",
)
response.output_text     # SDK가 output 안의 텍스트를 모아 주는 편의 속성
response.id, response.status, response.usage   # 운영에 필요한 정보
```

- 최소 흐름은 `model + input → output_text`지만 운영에서는 `id`(추적), `status`(완료 여부), `usage`(토큰·비용)를 함께 기록해요.
- 좋은 Developer Prompt = 멋진 문구가 아니라 **역할 · 맥락 · 범위 · 제약 · 출력 형식 · 성공 기준**을 담은 작은 계약서. 길이가 아니라 조건 누락·충돌이 없는 게 핵심.

## 내가 한 실습 (5장 API 첫 요청)

```python
request_body = {"model": "gpt-4.1-mini", "input": "HTTP 요청과 응답을 식당 주문에 빗대어 설명해 줘."}
print(json.dumps(request_body, ensure_ascii=False, indent=2))    # 보내기 전에 JSON 모양 확인

client = OpenAI(api_key=getpass("OpenAI API 키: ").strip())       # 키는 화면에 안 보이게 입력
response = client.responses.create(model=..., instructions=..., input="HTTP가 뭐야?")
print(response.output_text)
print(response.to_json())        # id, model, output, usage를 원본 JSON으로 확인
```

- SDK의 `responses.create()`가 딕셔너리를 JSON으로 바꿔 HTTP 요청을 보내 줘요. 데이터 엔지니어링 2장(HTTP 요청·응답)과 같은 일을 SDK가 대신하는 것.
- `output_text`는 원래 응답에 있는 칸이 아니라 SDK가 `output` 안의 텍스트를 모아 준 편의 속성이에요.

## 질문과 새로 알게 된 점

- Instruction 모델이 지시를 잘 따르는 건 원래 능력이 아니라 **SFT로 따로 배운 행동**이에요. 그래서 Base 모델에 지시를 주면 이어 쓰기만 할 수 있어요.
- SFT로 사내 규정 같은 최신 지식을 넣으려 하기보다 RAG로 근거를 주는 게 맞다는 기준이 생겼어요(이후 RAG 과목의 출발점).
- DPO 데이터의 chosen/rejected는 딥러닝 심화 7장 PEFT·Fine-tuning, 앞으로의 LLM Fine-tuning 과목과 이어져요.

## 확인 문제

### L-Q1. Causal mask 값 (3장)

미래 토큰을 막을 때 score에 0을 넣으면 안 되는 이유는?

① 0은 softmax에서 항상 1이 되어서  
② softmax에서 e⁰ = 1이라 미래 토큰에도 확률이 남기 때문에, `-inf`(e^−∞ = 0)를 넣어야 한다  
③ 0은 행렬곱이 안 되어서  
④ 상관없다

<details>
<summary>정답 보기</summary>

**②** — mask는 softmax **전에** `-inf`로 채워야 그 칸의 확률이 정확히 0이 되고 나머지가 재분배돼요.

</details>

### L-Q2. SFT의 범위 (4장)

사내 규정이 매달 바뀌는 상담 챗봇. 최신 규정을 반영하는 방법으로 가장 적절한 것은?

① 매달 SFT로 규정 문장을 외우게 한다  
② 규정은 RAG·Tool로 근거를 주고, SFT는 답변 형식·말투 같은 행동 조정에 쓴다  
③ DPO로 규정을 학습한다  
④ temperature를 낮춘다

<details>
<summary>정답 보기</summary>

**②** — SFT는 행동을 잘 바꾸지만 자주 바뀌는 지식에는 RAG·Tool이 적합해요.

</details>

### L-Q3. PPO vs DPO (4장)

PPO와 DPO의 차이로 맞는 것은?

① DPO는 Reward Model과 온라인 rollout이 필요하다  
② PPO는 preference 데이터가 필요 없다  
③ PPO는 Reward Model + 온라인 생성으로 policy를 조정하고, DPO는 고정된 (prompt, chosen, rejected) 쌍으로 policy를 직접 최적화한다  
④ 둘은 같은 알고리즘의 다른 이름이다

<details>
<summary>정답 보기</summary>

**③** — 둘 다 사람의 선호를 학습 신호로 바꾸지만 중간 단계와 운영 복잡도가 달라요.

</details>

### L-Q4. 서술형 — 응답에서 무엇을 기록할까 (5장)

API 응답에서 `output_text`만 저장하면 운영에서 어떤 문제가 생기는지, 함께 남겨야 할 필드와 이유를 쓰세요.

<details>
<summary>예시 답안</summary>

답변 문장만 남으면 어떤 요청에 대한 응답인지 추적할 수 없고(`id`), 응답이 정상 완료됐는지 잘렸는지 알 수 없고(`status`), 토큰과 비용이 얼마나 들었는지 모릅니다(`usage`). 장애를 조사하거나 비용을 관리하고 모델·프롬프트를 바꿨을 때 전후를 비교하려면 이 값들을 같이 기록해야 해요. 키는 이 기록에도, 코드에도 남기지 않아요.

</details>
