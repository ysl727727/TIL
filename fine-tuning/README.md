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
2장 학습 데이터 구성과 품질 검증   (학습 안 함 · 토크나이저만 · CPU)
  2-1  모범답안     12그룹 × 6사례 = 72, reference_answer 규칙 함수 (모델 출력 복사 X)
  2-2  대화 · 토큰  메타데이터 vs messages, 두 번 토큰화 299 / 376 → 답변 77, 257~380 ≤ 512
  2-3  품질 검사    validate_record 5단계 72/72, 일부러 틀린 복사본 2/2 탐지
  2-4  그룹 분할    8 / 2 / 2 그룹 = 48 / 12 / 12행, JSONL · SHA-256 · training_data.zip
      ↓  "labels = −100 마스킹으로 답변 토큰만 학습"
3장 전체 가중치 SFT와 학습 재개   (처음으로 가중치를 바꿈 · GPU)
  3-1  손실 마스크  encode_example 370 = 299(−100) + 71, collate (2, 379) · pad ID / 0 / −100, shift = log 6
  3-2  전체 SFT     학습 대상 494,032,768 (100%), 유효 배치 4 · 24갱신 계획 · StopAtTwelve → checkpoint-12
  3-3  곡선 읽기    train(구간 평균) vs dev(한 번), grad_norm은 NaN · 폭증만, 손실 ≠ 업무 정답
  3-4  재개 · 저장  resume_from_checkpoint 12 → 24, 표본 변화 · save_pretrained · 다시 읽기 · sft_model.zip
      ↓  "같은 SFT 목표를 A · B만 학습하면?"
4장 LoRA → 5장 QLoRA → 6장 DPO → 7장 평가 · API → 8장 검증 · 인계
```

## 장별 한 줄과 중요 개념

| 장 | 한 줄 | 중요 개념 | 상태 |
| --- | --- | --- | --- |
| [1장](./01-baseline-behavior-definition/) | 학습 전 같은 입력 · 같은 설정의 응답을 기준으로 남긴다 | **지식은 문서로 · 행동은 학습으로**, 정답 누수, 학습 목표(SFT · DPO) vs 학습 대상(LoRA · QLoRA), `ensure_ascii=False`, `add_generation_prompt`, **기울기 = p − y**, `backward` vs `step`, revision 고정 · greedy 명시, 새 토큰만 읽기 · 잘림 먼저, **형식 ≠ 의미 ≠ 참조 일치**, 재현의 네 가지 | ✅ 수업 · 통합 실습 · 직접 구현 Easy (`manual_reviews` 남음) |
| [2장](./02-training-data-quality-split/) | 모범답안은 규칙이 만들고, 자료와 검사 함수를 함께 시험하고, 행이 아니라 그룹으로 나눈다 | **규칙 함수 모범답안**, `below` · `irrelevant`, 메타데이터 vs messages · 정답 누수, 두 번 토큰화 · **답변 경계 assert**, 토큰 상한 512(자르지 않음), `validate_record` 5단계 · **검사 함수의 테스트**, `copy.deepcopy`, **그룹 단위 분할** · `random.Random(SEED)`, JSONL · `dataset_info` · SHA-256 | ✅ 수업 노트북 (Colab · 로컬 재실행, 해시 일치) |
| [3장](./03-full-sft-and-resume/) | 답변 토큰만 채점해서 전체 가중치를 바꾸고, 손실이 내려가도 업무 답은 따로 읽고, 재개 상태와 쓸 모델은 나눠 저장한다 | **labels −100** · EOS까지 자르기, 패딩 세 값 · 위치 기준, **shift는 한 곳에서 한 번**, teacher forcing · exposure bias, 전체 = 학습 대상 4.94억, 유효 배치 · epoch, warmup · linear, gradient checkpointing ≠ 학습 체크포인트, `StopAtTwelve`, **손실 ≠ 업무 정답**, `resume_from_checkpoint`, 체크포인트 vs 추론용 모델, BF16 vs FP32 | ✅ 수업 노트북 (Colab T4 · FP32, `sft_model.zip` 내려받기 남음) |

## 오늘의 교훈

1. **좋아졌다고 말하려면 학습 전 기준부터.** 같은 입력 · 같은 생성 설정 · 같은 revision으로 남긴 원문이 있어야 비교가 돼요.
2. **정답은 모델 입력에 섞지 않는다.** `cases`는 모델로, `review_criteria`는 사람에게.
3. **SFT와 LoRA는 다른 축이다.** "LoRA로 SFT를 한다"가 맞는 말.
4. **검사 통과 ≠ 모델이 받은 입력이 맞다.** `\uXXXX`로 바뀐 한글도 `json.loads` 비교는 통과했어요.
5. **형식 통과 ≠ 업무 의미.** 의미는 사람이 원문을 읽고, 그 판단을 학습 행동으로 연결해요.
6. **손실이 낮다 ≠ 업무 판단이 맞다.** 앞 토큰 하나만 보는 모델은 손실 0.37에서도 "이하 → 승인 필요"를 말해요.
7. **데이터가 곧 결과다.** 정답 · 경계 · 길이 · 분할 중 하나만 틀려도 학습은 에러 없이 돌고, 틀린 걸 배우거나 점수가 부풀어요.
8. **검사 함수도 틀린 예로 시험한다.** "항상 통과"하는 검사가 가장 위험해요.
9. **행이 아니라 같은 문제 단위로 나눈다.** 행 단위로 섞으면 test 12행 모두 형제가 train에 있어요.
10. **손실은 토큰 평균이다.** dev loss 0.0049에서도 "이하/초과" 몇 토큰이 틀리면 업무 답은 오답이에요. 생성 원문을 같은 조건으로 비교해요.
11. **이어서 학습할 상태와 쓸 모델은 다르다.** 재개엔 optimizer · scheduler · 난수 · step까지, 추론엔 가중치 · 설정 · 토크나이저만.

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
| 2장 `case_type`은 모델 입력에 안 넣음 | 1장 `cases` vs `review_criteria`, LLMOps 2장 `metadata` |
| 2장 두 번 토큰화 · `add_generation_prompt` | 1장 직접 구현 ② 채팅 템플릿의 답변 시작 위치 |
| 2장 일부러 틀린 복사본으로 검사 함수 시험 | LLMOps 4장 "막는 코드 vs 막았다고 말하는 코드" |
| 2장 그룹 단위 분할 · 데이터 누수 | 머신러닝 4장 데이터 누수 · GroupKFold, LLMOps 2장 dev · holdout |
| 2장 `copy.deepcopy` | 1장 `.detach().clone()` |
| 3장 labels −100 · `ignore_index` | 1장 세 점수 예제 교차엔트로피, LLM 실전 3장 SFT |
| 3장 `pad_sequence` · `attention_mask` | 딥러닝 심화 Transformer attention mask, 딥러닝 기초 7장 DataLoader · collate |
| 3장 gradient accumulation · `max_grad_norm` | 딥러닝 기초 13장 gradient clipping |
| 3장 `weight_decay` | 머신러닝 3장 Ridge 규제 |
| 3장 체크포인트 · 재개 (`optimizer.pt` · `rng_state.pth`) | 딥러닝 기초 9장 `state_dict` · checkpoint · 재개 |
| 3장 dev loss ≠ 업무 정답 | 1장 형식 ≠ 의미, LLMOps 3장 지표마다 분모가 다름 |
