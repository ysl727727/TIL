# Chapter 5: Hugging Face Hub and AutoModel

> 2026-09-07 학습 기록. 6-1, 6-3, 6-4, 6-5강 이론을 정리했습니다. 실습 노트북은 아직 없고 이론만 정리된 상태이며(주말로 이월), 아래 Core Theory는 `딥러닝_심화_6장_HuggingFace_강의_정리.md`를 기반으로 합니다.

## Learning Goals

- Hugging Face Hub가 모델 weight+설정+문서+버전을 함께 관리하는 저장소임을 이해하고, Model Card를 체크리스트(task, language, intended use, training data, metrics, limitations, license)로 읽는다.
- Model ID와 revision(branch/tag/commit)의 차이를 구분하고, 재현성이 중요할 때 commit hash로 고정해야 하는 이유를 설명한다.
- `AutoTokenizer`/`AutoModel`이 `config.json`의 `model_type`으로 실제 클래스를 자동 선택하는 흐름과, Base Model(`last_hidden_state`)과 Task-specific Model(`logits`)의 출력 차이를 구분한다.
- Masked Mean Pooling으로 padding을 제외하고 문장 벡터를 만드는 방법을 이해한다.
- `AutoModelForSequenceClassification`(`[B,C]`)과 `AutoModelForCausalLM`(`[B,L,V]`)의 출력 shape과 후처리 차이를 비교한다.
- `save_pretrained()`/`from_pretrained()`로 모델과 tokenizer를 한 쌍으로 저장·재로드하고, 저장 전후 logits를 비교해 추론 재현성을 검증하는 흐름을 이해한다.

## Practice Files

아직 실습 노트북이 없습니다. 6장 실습은 주말(2026-09-12~13)로 이월했습니다.

## Core Theory

### 1. Hugging Face Hub와 Model Card

- Hub는 단순 다운로드 사이트가 아니라 모델 weight(`model.safetensors`), 설정(`config.json`), tokenizer 파일, 문서(`README.md`=Model Card), 버전(branch/tag/commit)을 함께 관리하는 Git과 유사한 저장소다.
- Model ID는 `조직이름/저장소이름` 형태이고, revision은 그 저장소의 특정 버전을 가리킨다. `main`은 계속 바뀔 수 있는 "움직이는 버전"이라, 재현성이 중요하면 commit hash로 고정해야 안전하다.
- Model Card를 읽는 순서: task/language 지원 범위 → Base인지 Fine-tuned인지 → intended use/out-of-scope → 학습 데이터 → 평가 데이터셋/지표 → limitations/bias/실패 사례 → license. limitation이 자세히 적혀 있는 것은 나쁜 신호가 아니라 판단 정보를 충분히 제공한다는 좋은 신호다.
- License가 있다고 도메인 성능·편향 없음·개인정보 안전·저작권 문제 없음까지 자동으로 보장되지 않는다 — license 확인과 "실제로 써도 되는지" 판단은 별개 절차이며, 내부 평가가 항상 필요하다.

### 2. AutoClass와 Base Model 출력

- AutoClass는 Model ID 저장소의 `config.json`을 읽어 `model_type`을 식별하고 실제 클래스를 자동 선택한다(사람이 클래스 이름을 직접 고르지 않아도 됨).

| 클래스 | 대표 출력 |
| --- | --- |
| `AutoModel` (Base) | `last_hidden_state [B, L, H]` |
| `AutoModelForSequenceClassification` | `logits [B, C]` |
| `AutoModelForMaskedLM` | `logits [B, L, V]` |
| `AutoModelForCausalLM` | `logits [B, L, V]` |

- Base Model은 "정답 label"을 직접 주지 않고 문맥이 반영된 토큰별 벡터를 만든다 — `logits`가 없는 것은 오류가 아니라 Task Head가 안 붙어 있어 설계상 원래 없는 것이다.
- Masked Mean Pooling: padding 위치(`attention_mask=0`)는 곱해서 0이 되어 사라지고, 진짜 토큰만 합쳐져 평균에 반영된다(문장별 실제 토큰 개수로 나눔, 0으로 나누기는 `clamp(min=1e-9)`로 방지). Padding까지 포함해 단순 평균을 내면 결과가 왜곡된다.
- `AutoConfig.from_pretrained()`로 가중치를 실제로 불러오기 전에 `hidden_size`, `num_hidden_layers`, `num_attention_heads`, `num_key_value_heads` 등 구조를 먼저 확인할 수 있다(메모리 부담 없음) — `num_attention_heads`/`num_key_value_heads`는 3장에서 배운 MHA/MQA/GQA 개념과 직결된다.

### 3. Task-specific AutoModel과 Logits 비교

- Task Head는 Base 모델의 문맥 벡터를 특정 문제의 출력 형태로 바꿔주는 마지막 레이어다. `num_labels`(분류 클래스 수), `id2label`/`label2id`(숫자 ID ↔ 이름 매핑)가 함께 쓰인다.
- 분류 logits `[B,C]`: 각 행이 한 문장의 클래스별 점수(softmax 전). Causal LM logits `[B,L,V]`: 각 위치가 다음 토큰 후보 전체에 대한 점수.
- 분류 결과 해석은 `softmax(dim=-1)` → `argmax(dim=-1)` → `model.config.id2label`로 이름 변환하는 흐름이며, GPT류는 마지막 위치의 `[B,V]`에서 `softmax`+`topk`로 후보를 확인한다.

### 4. 저장·재로드와 추론 재현

- 모델 weight만 저장하면 안 된다 — tokenizer 규칙이 달라지면 같은 문장도 다른 `input_ids`가 되어 결과가 완전히 바뀔 수 있으므로, 모델과 tokenizer는 항상 같은 폴더에 한 쌍으로 저장한다(`model.save_pretrained()` + `tokenizer.save_pretrained()`).
- 검증 흐름: 저장 전 baseline logits를 CPU에 `.clone()`해 보관 → 저장 → 객체 삭제(`gc.collect()`, `torch.cuda.empty_cache()`)로 진짜 재로드 상황을 흉내 → `local_files_only=True`로 로컬 폴더에서 재로드 → 같은 입력으로 다시 추론 → `torch.testing.assert_close()`(부동소수점 오차 허용)로 logits 비교, `torch.equal()`로 최종 예측 클래스가 정확히 같은지 비교.
- 재현성은 seed 하나로 끝나지 않는다 — Model ID, 정확한 revision(commit hash), 라이브러리 버전(`transformers`, `torch`), device/dtype, 전처리 설정(padding, truncation, max length)까지 메타데이터로 함께 기록해야 완성된다.
- (선택) 폐쇄망 반입 시에는 허용된 모델·revision·license를 승인 기록에 남기고, 필요한 파일(weight/config/tokenizer/generation config/custom code)을 확인하고, checksum으로 무결성을 검증한 뒤 `local_files_only=True`로 오프라인 재현 결과를 baseline과 비교해야 한다.

## Environment

이 챕터는 아직 실습 코드가 없습니다. 실습을 추가하면 `torch`, `transformers`, `huggingface_hub`가 필요합니다.
