# Chapter 6: Text Classification Fine-tuning with Trainer

> 2026-09-08 학습 기록. 7-1, 7-2, 7-3, 7-5, 7-6, 7-7, 7-8강 이론을 정리했습니다(7-4강 자료는 아직 없음). 실습은 7-1만 완료했고, 7-2~7-8 실습은 주말(2026-09-12~13)로 이월했습니다.

## Learning Goals

- 텍스트 분류 문제를 Fine-tuning 전에 입력/출력/라벨/성공 기준(5요소)으로 먼저 정의해야 하는 이유를 설명한다.
- 결측·중복·label 불균형·split 간 leakage를 데이터 단계에서 점검하는 감사 함수를 만든다.
- `DatasetDict`의 split 역할 분리, `id2label`/`label2id` 매핑, `seed`+`stratify`를 사용한 재현 가능한 분할을 이해한다.
- `Dataset.map()`으로 tokenization을 배치 적용하고, `DataCollatorWithPadding`으로 동적 padding하는 흐름을 이해한다.
- Accuracy만으로는 불균형 데이터에서 위험한 이유를 설명하고, Macro-F1과 Confusion Matrix로 보완하는 `compute_metrics`를 이해한다.
- `TrainingArguments`가 실험 재현성 기록이라는 것과, `Trainer`를 구동하는 6대 부품(model, args, datasets, tokenizer, data_collator, compute_metrics)의 역할을 이해한다.
- Checkpoint/Best Model/Final Model의 차이를 구분하고, 학습 실패(정체·과적합·NaN·OOM) 진단을 위한 소규모 오버핏 sanity check를 이해한다.
- Error Analysis(Classification Report, Confusion Matrix, High/Low Confidence 오류)로 오류 패턴을 해석하고 Fine-tuning 리포트의 6대 구성 요소를 정리한다.

## Practice Files

| Lesson | File | Practice status |
| --- | --- | --- |
| 7-1 | `01-data-quality-and-leakage-audit.ipynb` | 텍스트 정규화 후 빈 문장·허용 안 된 label·중복 감사(`audit_classification_records`), label 분포·imbalance ratio 계산, train/validation 간 정확 중복+Jaccard 기반 near-duplicate leakage 탐지 확인 |
| 7-2 | 미완료 | 주말 backlog로 이월 (DatasetDict, Label Encoding, Stratified Split) |
| 7-3 | 미완료 | 주말 backlog로 이월 (Tokenization Mapping, DataCollatorWithPadding) |
| 7-5 | 미완료 | 주말 backlog로 이월 (compute_metrics, Accuracy/Macro-F1) |
| 7-6 | 미완료 | 주말 backlog로 이월 (TrainingArguments, Trainer 설정) |
| 7-7 | 미완료 | 주말 backlog로 이월 (Fine-tuning 실행·평가·Checkpoint) |
| 7-8 | 미완료 | 주말 backlog로 이월 (Error Analysis, Fine-tuning 리포트) |

7-1은 첫 실행에서 assert 검증을 모두 통과했고 별도 수정 셀은 없었습니다.

## Core Theory

### 1. 문제 정의와 데이터 품질 점검 (7-1강)

- Fine-tuning은 모델을 불러와 학습 버튼을 누르는 것이 아니다 — "무엇을 입력으로 받고, 어떤 라벨을 예측하며, 무엇을 성공으로 볼 것인가"(문제 정의 5요소)가 흔들리면 학습 결과가 좋아도 실제 문제 해결로 이어지지 않는다.
- KLUE YNAT(한국어 뉴스 제목 토픽 분류) 예시로 데이터 점검 흐름을 익힌다: `load_dataset()`으로 로드 후 컬럼 이름을 직접 확인 → `id2label`/`label2id` 매핑 → label imbalance 확인(다수 클래스만 찍어도 Accuracy가 높게 나올 수 있어 Macro-F1/소수 클래스 recall을 함께 봐야 함) → 결측(`isna()`)·중복(`duplicated()`)·leakage 후보(라벨명이 입력 텍스트에 직접 노출되는 경우 등) 점검.
- 오늘 실습(7-1)에서는 이 원칙을 직접 구현했다: 공백을 정규화(`" ".join(text.split())`)한 뒤 빈 문장·허용되지 않은 label·정규화 후 중복을 순서대로 걸러내고, 정상 record와 오류 리포트를 분리했다. Label 분포는 `Counter`로 개수·비율을 구하고 `max/min`으로 imbalance ratio를 계산했다. Split leakage는 소문자화+공백 정리+끝 문장부호 제거로 정규화한 뒤 정확 중복과, 단어 집합 Jaccard similarity가 threshold(0.8) 이상인 near-duplicate까지 함께 찾았다 — validation에 train 문장이 섞이면 일반화 성능이 아니라 암기 재현 능력을 측정하게 된다.

### 2. DatasetDict, Label Encoding, Split 고정 (7-2강)

- `DatasetDict`는 split 이름(`train`/`validation`/`test`)을 key로 갖는 사전형 구조다. train은 파라미터 업데이트용, validation은 학습 중 모델 상태·설정 조정용, test는 최종 성능 확인용으로 역할이 명확히 분리돼야 한다 — validation을 계속 보며 모델을 수정하는 것도 간접적인 의사결정 개입이라, 객관적 최종 검증에는 별도 test가 필요하다.
- `id2label`/`label2id`는 "정치", "경제" 같은 이름을 모델이 학습하는 정수 ID로 양방향 변환하기 위해 필요하며, `label_mapping.json`으로 저장해두면 이후 모델 생성 시 config에 재사용해 재현성을 높인다.
- 재현 가능한 split은 `seed`(동일 분할 보장)와 `stratify_by_column`(라벨 분포를 원본과 균등하게 유지)로 만든다. 분할 후에는 set 교집합으로 split 간 동일 텍스트가 섞이지 않았는지 반드시 확인해야 한다 — 섞이면 모델이 일반화가 아니라 암기로 점수를 부풀릴 수 있다.

### 3. Tokenization Mapping과 Data Collator (7-3강)

- `Dataset.map(tokenize_fn, batched=True)`로 텍스트 컬럼(`title`)을 모델 입력용 컬럼(`input_ids`, `attention_mask`, `labels`)으로 일괄 변환한다. `batched=True`는 여러 샘플을 한 번에 넘겨 처리 속도를 높이고, `remove_columns`로 불필요한 원본 컬럼을 제거해 collator 전달 오류를 막는다.
- 여기서는 padding을 미리 하지 않고(`truncation=True, max_length=64`만 적용) `DataCollatorWithPadding`이 배치 단위로 동적 padding(Dynamic Padding)하도록 비워둔다 — 전체 데이터셋 최대 길이가 아니라 현재 배치의 최장 길이에 맞추므로 `padding="max_length"`보다 메모리 효율적이다.
- 배치 shape 계약: `input_ids [B,L]`, `attention_mask [B,L]`, `labels [B]`.

### 4. compute_metrics와 Accuracy/Macro-F1 (7-5강)

- Label 불균형이 심하면 Accuracy는 왜곡된 성적표가 된다(예: 90%가 한 클래스면 그것만 찍어도 Accuracy 90%). 환불 요청 같은 소수 클래스가 중요한 경우 Accuracy만으로는 치명적 오류를 놓칠 수 있다.
- Macro-F1은 클래스별 F1을 구한 뒤 동일 비중으로 평균해, 샘플 수가 적은 소수 클래스 성능도 다수 클래스와 같은 비중으로 반영한다.
- `compute_metrics(eval_pred)`는 Trainer가 넘긴 logits와 labels를 받아 `np.argmax(predictions, axis=-1)`로 예측 클래스를 만들고, `accuracy_score`/`f1_score(average="macro")` 등을 계산해 딕셔너리로 반환한다.
- Confusion Matrix는 행=실제 라벨, 열=예측 라벨이며, 대각선은 정답, 비대각선은 어떤 클래스를 어떤 클래스로 착각했는지 보여주는 단서다.

### 5. TrainingArguments와 Trainer 설정 (7-6강)

- `TrainingArguments`는 단순 코드 옵션이 아니라 실험 기록 문서다 — 나중에 성능 차이의 원인을 추적하는 핵심 근거가 된다(`output_dir`, `num_train_epochs`, `per_device_train/eval_batch_size`, `learning_rate`, `load_best_model_at_end=True`, `metric_for_best_model="macro_f1"` 등).
- `Trainer`는 model, args, datasets, tokenizer, data_collator, compute_metrics 6대 부품을 연결해 학습 루프를 표준화한다.
- 실행 전 체크리스트: `model.config.num_labels`가 데이터셋 라벨 수와 일치하는지, `input_ids`/`attention_mask`/`labels` 컬럼이 모두 있는지, `metric_for_best_model` 이름이 `compute_metrics` 반환 키와 정확히 일치하는지, `save_strategy`와 `eval_strategy` 주기가 같은지, OOM 시 batch size/`max_length`를 조정했는지.

### 6. Fine-tuning 실행·평가·Checkpoint 관리 (7-7강)

- `trainer.train()`은 내부적으로 forward → loss → backward → optimizer step을 표준 루프로 반복한다. OOM이면 `per_device_train_batch_size`를 줄이거나 `max_length`를 단축한다.
- `trainer.evaluate()` 결과는 화면에만 두지 않고 `validation_metrics.json`으로 저장해야 다른 실험과 비교할 수 있다.
- Checkpoint(중간 저장, `checkpoint-*`) vs Best Model(`load_best_model_at_end=True`로 검증 지표가 가장 좋았던 시점이 자동 로드됨) vs Final Model(weight+tokenizer+`label_mapping`+`run_config.json`을 한 폴더에 함께 저장) — 셋의 목적이 다르다.
- 가장 빠른 sanity check는 극소수 샘플로 의도적으로 오버핏시켜보는 것이다 — 이 작은 데이터조차 못 외우면 데이터 로더·모델 구조·loss 계산에 원초적 버그가 있다는 신호다.

### 7. Error Analysis와 Fine-tuning 리포트 (7-8강)

- `trainer.predict()`로 test split의 logits와 정답을 얻고, softmax 후 최댓값을 confidence로 삼아 예측 결과를 `test_predictions.csv`로 저장한다.
- Classification Report(클래스별 Precision/Recall/F1/Support)와 Confusion Matrix로 어떤 클래스가 약한지, 어떤 클래스 쌍을 자주 헷갈리는지 확인한다.
- 틀린 샘플은 High Confidence Error(강하게 확신했지만 틀림 → 잘못된 패턴 학습이나 라벨 오류 의심)와 Low Confidence Error(모델도 애매 → 문장 모호성이나 라벨 경계 불명확 의심)로 나눠 해석한다.
- Fine-tuning 리포트는 성적 자랑이 아니라 재현·개선을 위한 기록이며, 문제 정의·데이터(split seed 포함)·모델/tokenizer·학습 설정·평가 결과·오류 분석 및 개선안 6가지를 반드시 포함해야 한다.

## Environment

```bash
pip install -r requirements.txt
```
