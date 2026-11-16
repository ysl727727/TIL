# Fine-tuning

> 2026-11-16 파인튜닝 1일차(1장 4강)부터 시작한 기록이에요. RAG · Context Engineering · LLMOps가 **"모델은 그대로 두고 입력과 운영을 바꾸기"**였다면, 파인튜닝은 **"예제로 손실을 계산해 모델의 가중치를 바꾸기"**예요. 실습 주제는 끝까지 하나: **가상 출장 규정 도우미**가 근거를 읽고 정해진 JSON으로 답하고, 근거가 없으면 보류하기. 모델은 `Qwen/Qwen2.5-0.5B-Instruct`.

## 큰 흐름

```text
1장 학습할 행동과 기준 응답 정의   (학습 안 함 · CPU)
  1-1  입력 분리   cases(모델) vs review_criteria(사람), build_messages, SFT·LoRA·QLoRA·DPO 지도
  1-2  토큰 · 원리  apply_chat_template [1, 289], 세 점수 예제 p − y, 손실 1.099 → 0.909
  1-3  실제 응답    revision 고정 · float32 · greedy · 192토큰 → 응답 8개 (잘림 1)
  1-4  나눠 읽기    json_object → schema_ok → citation_ids_ok, 형식 0/4 · 0/4, baseline.json
      ↓  "학습할 행동: JSON · 보류 · 인용 · 근거 읽기"
2장 학습 예제 72개 → 3장 SFT → 4장 LoRA → 5장 QLoRA → 6장 DPO → 7장 평가 · API → 8장 검증 · 인계
```

## 장별 한 줄과 중요 개념

| 장 | 한 줄 | 중요 개념 | 상태 |
| --- | --- | --- | --- |
| [1장](./01-baseline-behavior-definition/) | 학습 전 같은 입력 · 같은 설정의 응답을 기준으로 남긴다 | **지식은 문서로 · 행동은 학습으로**, 정답 누수, 학습 목표(SFT · DPO) vs 학습 대상(LoRA · QLoRA), `ensure_ascii=False`, `add_generation_prompt`, **기울기 = p − y**, `backward` vs `step`, revision 고정 · greedy 명시, 새 토큰만 읽기 · 잘림 먼저, **형식 ≠ 의미 ≠ 참조 일치**, 재현의 네 가지 | ✅ 수업 · 통합 실습 · 직접 구현 Easy (`manual_reviews` 남음) |

## 오늘의 교훈

1. **좋아졌다고 말하려면 학습 전 기준부터.** 같은 입력 · 같은 생성 설정 · 같은 revision으로 남긴 원문이 있어야 비교가 돼요.
2. **정답은 모델 입력에 섞지 않는다.** `cases`는 모델로, `review_criteria`는 사람에게.
3. **SFT와 LoRA는 다른 축이다.** "LoRA로 SFT를 한다"가 맞는 말.
4. **검사 통과 ≠ 모델이 받은 입력이 맞다.** `\uXXXX`로 바뀐 한글도 `json.loads` 비교는 통과했어요.
5. **형식 통과 ≠ 업무 의미.** 의미는 사람이 원문을 읽고, 그 판단을 학습 행동으로 연결해요.
6. **손실이 낮다 ≠ 업무 판단이 맞다.** 앞 토큰 하나만 보는 모델은 손실 0.37에서도 "이하 → 승인 필요"를 말해요.

## 앞 과목과 이어지는 부분

| 파인튜닝 | 앞에서 본 것 |
| --- | --- |
| 1장 `cases` vs `review_criteria` | LLMOps 2장 `input` vs `expected_output`, RAG 8장 `reference`는 평가에만 |
| 1장 `apply_chat_template` · `add_generation_prompt` | 딥러닝 심화 8장 Chat Template, CE 3장 chat template로 토큰 세기 |
| 1장 BPE · 한글 바이트 깨짐 | 딥러닝 심화 2장 subword tokenizer |
| 1장 softmax · 교차엔트로피 · `p − y` | LLM 실전 1장 Logit · Softmax · CE, 기초 수학 6장 Softmax · CE · 역전파 |
| 1장 `softmax(dim=-1)` | 보강 NumPy `axis=1` · softmax 응용 3 |
| 1장 greedy · `repetition_penalty` · `max_new_tokens` | 딥러닝 심화 8장 `generate()` · Greedy · Sampling |
| 1장 형식 검사 `inspect_response` | LLMOps 4장 pydantic `Answer` · 출처 범위, RAG 6장 `validate_answer` |
| 1장 분모를 같이 쓰는 지표(0/4) | LLMOps 3장 지표마다 분모가 다름 |
| 1장 SFT · DPO 지도 | LLM 실전 3\~5장 SFT · RLHF · DPO, 딥러닝 심화 7장 PEFT(LoRA) |
