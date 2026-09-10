# Chapter 7: Prompt Engineering to PEFT

> 2026-09-09 학습 기록. 8-1, 8-2, 8-4, 8-5강 이론을 정리했습니다. 실습 노트북은 아직 없고 이론만 정리된 상태이며(주말로 이월), 아래 Core Theory는 `260908_7강_강의요약.docx` 다음 강의인 8강 정리자료(`8강_Prompt_Engineering부터_PEFT_Fine-tuning까지.pdf`)를 기반으로 합니다.

## Learning Goals

- Prompt Engineering, Prompt-only, Prompt-tuning, PEFT, Full Fine-tuning이 "무엇을 바꾸는가"(입력 vs 모델 파라미터) 기준으로 어떻게 다른지 구분한다.
- 새로운 태스크를 만났을 때 바로 Fine-tuning을 선택하지 않고 Prompt-only baseline부터 시작해야 하는 이유를 설명한다.
- Prompt-only baseline의 4요소(평가셋, prompt template, output schema, metric)를 고정해야 하는 이유와, 출력 형식 실패(format success)를 별도로 기록하는 이유를 이해한다.
- LoRA가 큰 가중치 업데이트를 저랭크 행렬 두 개(`A`, `B`)로 근사한다는 직관과, `r`/`lora_alpha`/`target_modules`/`lora_dropout` 설정의 의미를 이해한다.
- Prompt Tuning과 LoRA의 차이(입력 앞 soft prompt vs 모델 내부 Linear layer 경로)를 구분한다.
- Prompt-only와 Fine-tuned/PEFT 모델을 공정 비교(같은 평가셋·정답·metric·parsing 규칙)하는 방법과, 평균 성능이 좋아져도 regression(기존에 맞던 사례가 틀리게 되는 것) 사례를 반드시 확인해야 하는 이유를 이해한다.

## Practice Files

아직 실습 노트북이 없습니다. 8장 실습은 주말(2026-09-12~13)로 이월했습니다.

## Core Theory

### 1. 모델 적응 방법의 스펙트럼 (8-1강)

학습 파라미터 수·비용·위험이 커지는 순서: `Prompt-only → Prompt-tuning → PEFT(LoRA 등) → Full Fine-tuning`.

| | Prompt Engineering | Prompt-tuning | PEFT(LoRA) | Full Fine-tuning |
| --- | --- | --- | --- | --- |
| 바뀌는 대상 | 사람이 읽는 prompt 문장 | 학습 가능한 soft prompt 벡터 | 모델 내부 일부 파라미터(adapter) | 모델 전체 파라미터 |
| 모델 가중치 | 고정 | 보통 고정 | 대부분 고정 | 전체 업데이트 |
| 학습 데이터 | 없어도 가능 | 필요 | 필요 | 필요 |
| 결과물 | prompt template | soft prompt checkpoint | adapter checkpoint | 전체 모델 checkpoint |

- Prompt-tuning은 이름에 "prompt"가 들어가지만 Prompt Engineering과 다르다 — 전자는 사람이 문장을 편집하는 것이고, 후자는 모델이 학습할 수 있는 작은(사람이 읽을 수 없는) soft prompt 파라미터를 입력 앞에 추가해 학습하는 것이다.
- 처음부터 모델을 학습시키지 않는다 — 먼저 Prompt-only baseline을 만들고, 오류 분석으로 학습이 정말 필요한지 확인해야 한다. Fine-tuning은 Prompt-only를 무조건 대체하는 방법이 아니라 데이터와 평가 체계가 준비됐을 때 선택하는 방법이다.

### 2. Prompt-only Baseline 설계 (8-2강)

Baseline이 필요한 이유는 둘이다: ① 학습 없이도 어느 정도 해결되는 문제인지 확인, ② 이후 PEFT/Fine-tuning 결과가 baseline보다 실제로 좋아졌는지 비교하는 기준선 확보.

Baseline 설계 4요소: 평가셋(고정된 샘플), Prompt template(모든 샘플에 적용할 입력 형식), Output schema(따라야 하는 출력 형식, 예: label only), Metric(Accuracy, Macro-F1, format success).

- Prompt template을 함수로 관리하면(`build_prompt(text)`) 평가셋 전체에 같은 조건을 적용할 수 있고, prompt 버전(`PROMPT_VERSION`)을 결과표와 함께 저장해 이후 버전 간 비교가 가능하다 — prompt template을 바꾸는 것도 실험 조건이 바뀐 것이므로 반드시 버전을 남겨야 한다.
- 모델 출력이 형식(schema)을 어길 수 있다("label만 출력하세요"라고 했는데 설명을 덧붙이는 등). `parse_label_only()` 같은 검증 함수로 정규화(strip, lower) 후 허용 라벨과 매칭되는지 확인하고, 실패하면 `None`으로 처리해 형식 실패를 별도로 기록한다.
- 결과표에는 `raw_output`과 `prediction`을 함께 저장해야 한다 — 모델이 정답을 알고 있었지만 형식을 어긴 것인지, 아예 잘못된 라벨을 예측한 것인지 구분해야 다음 실험 방향을 정할 수 있다.

### 3. PEFT 개념과 LoRA (8-4강)

- PEFT는 모델 대부분을 고정하고 작은 추가 파라미터(adapter)만 학습해 메모리·저장 비용을 줄이는 접근이다. 장점: 학습 파라미터가 적음, 태스크별 adapter를 따로 저장·교체 가능, 원본 모델을 유지한 채 특정 행동만 조정. 단점: Full Fine-tuning보다 항상 좋은 것은 아니고, 어느 layer에 adapter를 넣을지 결정해야 하며, adapter 관리·병합·배포 전략이 필요하다.
- LoRA(Low-Rank Adaptation)는 기존 가중치 `W`를 직접 크게 바꾸는 대신, 작은 저랭크 행렬 `A`(d×r), `B`(r×d) 경로를 학습해 업데이트를 근사한다: `h = Wx + BAx`. `r`(rank)이 작을수록 학습 파라미터가 적다.
- LoRA 설정: `r`(저랭크 rank, 작을수록 파라미터 적음), `lora_alpha`(업데이트 스케일 조절), `target_modules`(LoRA를 붙일 모듈 이름, 보통 attention projection), `lora_dropout`(과적합 완화).
- Prompt Tuning vs LoRA: 둘 다 모델 본체는 보통 고정하지만, Prompt Tuning은 입력 앞 soft prompt embedding을 학습하고 LoRA는 모델 내부 특정 Linear layer에 업데이트 경로를 붙여 학습한다.
- `LoraConfig` → `get_peft_model(base_model, lora_config)` → `peft_model.print_trainable_parameters()`로 전체 대비 학습 가능 파라미터 비율이 충분히 작은지(PEFT의 목적과 맞는지) 반드시 확인한다.
- (선택) Causal LM용 LoRA/QLoRA: `target_modules`는 모델마다 이름이 달라 `named_modules()`로 실제 이름을 확인해야 한다. QLoRA는 base weight를 4-bit로 불러오고 LoRA adapter만 학습하는 방식이며 "4-bit 모델 전체를 그대로 학습한다"는 설명은 부정확하다. SFT에서는 padding과 prompt 위치를 `labels=-100`으로 mask해 assistant response만 loss에 반영할지 결정한다. Adapter 저장만으로는 base weight가 없으므로 base model ID·revision, PEFT config, tokenizer를 함께 기록해야 한다.

### 4. Prompt-only vs Fine-tuned 결과 비교 (8-5강)

- 공정 비교 조건: 같은 평가셋·같은 정답 라벨·같은 metric·같은 parsing 규칙·같은 기록 방식. 평가셋이나 metric이 다르면 비교 자체가 성립하지 않는다.
- 비교 지표: Accuracy, Macro-F1(라벨 불균형 시 유용), Format success(출력 형식 준수율), Latency, Cost, Qualitative review(사람이 직접 읽는 정성 평가).
- Regression: 평균 지표가 좋아져도 일부 중요한 샘플에서 오히려 성능이 나빠질 수 있다. Prompt-only는 맞혔는데 Fine-tuned가 틀린 사례(regression)와, Prompt-only는 틀렸는데 Fine-tuned가 맞힌 사례(개선)를 나눠 확인해야 한다 — 특정 오류가 리스크가 큰 도메인(고객 문의, 의료, 법률, 보안 등)에서는 평균 지표가 좋아져도 중요 클래스의 recall이 낮아지면 배포하면 안 된다.
- 비교 리포트 7항목: 문제 정의, 실험 조건(모델·prompt 버전·split·seed·후처리 규칙), 정량 결과, 정성 결과, 오류 분석, 결론(Prompt-only 유지/PEFT 적용/데이터 보강/Fine-tuning 확대 중 선택), 한계.
- (선택) 생성 모델의 Release Gate: Task 품질, 안전·보안(민감정보 노출·prompt injection·유해 출력), Regression(기존 통과 사례 유지), 시스템(TTFT/TPOT/VRAM), 운영(rollback 절차)을 모두 통과해야 배포하며, 평가용 decoding parameter와 실제 서비스 설정이 다르면 결과도 달라지므로 둘 다 기록해야 한다.

## Environment

이 챕터는 아직 실습 코드가 없습니다. 실습을 추가하면 `transformers`, `peft`, `accelerate`, `torch`가 필요합니다.
