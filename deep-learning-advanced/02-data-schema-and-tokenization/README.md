# Chapter 2: Data Schema Auditing and Tokenization

> 2026-09-02 학습 기록. 2-1~2-3 기본·심화 실습을 모두 정리했습니다. (2-2·2-3 기본은 전날 이월분을 오늘 완료)

## Learning Goals

- 필수 key 누락, 공백 텍스트, 중복 ID, 허용되지 않은 label을 원본 행 단계에서 한 번에 감사하는 함수를 만든다.
- Greedy longest-match 방식의 toy subword tokenizer를 구현해 `##` prefix 규칙과 `[CLS]/[SEP]/[UNK]` 역할을 분리한다.
- 실제 Hugging Face tokenizer(`AutoTokenizer`)로 특수 토큰 부착·ID 변환·decode 왕복을 확인한다.
- 즉석 동적 padding(`tokenizer(..., padding=True)`)과 `DataCollatorWithPadding`으로 나중에 패딩하는 방식의 차이를 이해한다.
- `BatchEncoding`의 field·shape·dtype을 하드코딩하지 않고 직접 검사해 PAD-mask 일치를 확인한다.
- `Dataset`/`DatasetDict`로 train/validation/test 세 split에 동일한 전처리를 적용하고, id 중복(leakage) 여부를 검사한다.
- 두 vocabulary 정책(작은/큰)의 평균 token 수·UNK 수·embedding parameter 수를 비교한다.
- Fast tokenizer의 `offset_mapping`으로 subword가 원문의 어느 문자 범위에서 왔는지 추적한다.
- 원본 token 길이 분포와 절단 비율을 근거로 `max_length` 후보를 감사·선택한다.

## Practice Files

| Lesson | File | Practice status |
| --- | --- | --- |
| 2-1 기본 | `01-schema-audit-and-tokenizer-basic.ipynb` | 뉴스 샘플 schema 감사기(누락 key·공백 텍스트·중복 ID·허용 label), greedy longest-match subword tokenizer와 ID 왕복 확인 |
| 2-1 심화 | `02-vocabulary-comparison-advanced.ipynb` | 작은/큰 vocabulary의 평균 token 수·UNK 수·embedding parameter 수 비교, "클수록 무조건 좋지 않은" 이유 정리 확인 |
| 2-2 기본 | `03-dynamic-padding-and-batch-encoding-basic.ipynb` | `AutoTokenizer` 특수 토큰 인코딩, 즉석 동적 padding, `BatchEncoding` field·shape·PAD-mask 일치 확인 |
| 2-2 심화 | `04-offset-mapping-advanced.ipynb` | fast tokenizer `offset_mapping`으로 subword-원문 문자 범위 매핑, special token 처리 확인 |
| 2-3 기본 | `05-data-collator-and-dataset-pipeline-basic.ipynb` | `DataCollatorWithPadding` 나중 패딩, `Dataset`/`DatasetDict` `map()` 전처리, split id disjoint 검증 확인 |
| 2-3 심화 | `06-max-length-audit-advanced.ipynb` | 원본 token 길이 분포 기반 `max_length` 후보별 절단률 비교, 최소 절단 후보 선택 확인 |

여섯 파일 모두 첫 실행에서 자동 검증(`PASS`)을 통과했고 별도 수정 셀은 없었습니다.

## Core Theory

### 1. 원본 행 단계 데이터 감사

- 필수 key(`id`/`text`/`label`) 누락, 공백만 있는 text, 중복 ID, 허용되지 않은 label을 각각 다른 index 목록에 기록한다.
- `if row["text"]`만으로는 공백 문자열(`"  "`)을 걸러내지 못한다 — `.strip()`까지 확인해야 한다.
- `Counter`로 ID 중복과 label별 개수를 한 번에 집계하고, 허용된 label만 분포에 포함해 오류 label이 통계를 왜곡하지 않게 한다.
- 즉시 예외를 내지 않고 모든 행을 검사하면 한 번의 수정 주기에 여러 오류를 함께 고칠 수 있다.

### 2. Toy Subword Tokenizer (Greedy Longest-Match)

- 각 시작 위치에서 가능한 가장 긴 등록 조각부터 거꾸로 탐색한다(longest-match first).
- 단어 중간부터 시작하는 조각에만 `##` prefix를 붙여 vocabulary에서 찾는다.
- 끝까지 분해하지 못하면 일부 조각만 남기지 않고 단어 전체를 `[UNK]` 하나로 처리한다.
- 전체 앞뒤에 `[CLS]`, `[SEP]`를 붙여 token 목록을 완성하고 vocab으로 ID를 매핑한다.
- 이 구현은 WordPiece의 핵심 직관만 단순화한 것이며, 실제 tokenizer는 정규화·pre-tokenization·언어별 규칙과 학습된 vocabulary까지 함께 사용한다.

### 3. 실제 Tokenizer 기본 인코딩

- `AutoTokenizer.from_pretrained(model_id, local_files_only=True)`: 네트워크 상태와 결과를 분리하기 위해 로컬 캐시만 사용.
- `tokenizer.tokenize(text)`는 특수 토큰 없이 서브워드 토큰만 반환, `tokenizer.encode(text, add_special_tokens=True)`는 `[CLS] ... [SEP]`가 자동으로 붙은 실제 모델 입력용 ID를 반환한다.
- `tokenizer.decode(ids, skip_special_tokens=...)`로 ID를 문자열로 복원하며 특수 토큰 유지/제거를 선택할 수 있다.
- 검증: 맨 앞이 `cls_token_id`, 맨 뒤가 `sep_token_id`, `len(tokens_without_special) + 2 == len(ids_with_special)`(특수 토큰 2개만 추가됐는지).

### 4. 동적 Padding — 즉석 방식 vs Collator 방식

| | 즉석 패딩 (`tokenizer(texts, padding=True)`) | `DataCollatorWithPadding` |
| --- | --- | --- |
| 패딩 시점 | 토큰화 즉시 | 나중에 collator 호출 시점 |
| 실제 활용 | 간단한 일회성 처리 | `Dataset.map()` + `DataLoader` 표준 학습 파이프라인 |

- 즉석 방식: `tokenizer(texts, padding=True, truncation=True, max_length=..., return_tensors="pt")` → `input_ids`(`[문장 수, 최대 길이]`)와 `attention_mask`(실제 토큰=1, 패딩=0)를 바로 반환한다.
- Collator 방식: 문장을 하나씩 `padding=False`로 개별 토큰화해 원래 길이를 보존한 뒤, `collator(features)` 호출 시점에 그 배치의 최장 길이로 동적 패딩한다.
- 두 방식 모두 `input_ids.eq(pad_token_id)`(패딩 위치)와 `attention_mask.eq(0)`(마스크 0 위치)이 `torch.equal()`로 정확히 같은 위치를 가리켜야 한다.
- `attention_mask.sum(dim=1)`으로 각 문장의 실제(패딩 제외) 길이를 구할 수 있다.

### 5. Dataset / DatasetDict 파이프라인

```python
dataset = DatasetDict({name: Dataset.from_dict(columns) for name, columns in raw.items()})

def tokenize_batch(batch):
    encoded = tokenizer(batch["text"], padding=False, truncation=True, max_length=max_length)
    encoded["labels"] = [int(label) for label in batch["label"]]
    return encoded

tokenized = dataset.map(tokenize_batch, batched=True)
```

- `dataset.map(..., batched=True)`는 train/validation/test 세 스플릿 모두에 동일한 전처리 규칙을 적용한다. 실행 중 뜨는 진행바(`Map: 100% ... N/N`)는 정상 처리 완료 표시이며 에러가 아니다.
- `label` → `labels`로 이름을 바꾸고 `int()`로 캐스팅해 Hugging Face 모델/Trainer가 기대하는 필드명을 맞춘다.
- Collator에는 문자열 열(`id`, `text`)을 제외하고 `input_ids`, `attention_mask`, `labels`(+있으면 `token_type_ids`)만 선택해서 넘긴다.
- 데이터 누수(leakage) 검증: `train∩val`, `train∩test`, `val∩test`가 모두 비어 있는지 집합 연산으로 확인한다.

### 6. 두 Vocabulary 정책 비교

- 큰 vocabulary는 더 긴 조각을 담을 수 있어 평균 token 수와 UNK 수를 줄이지만, `len(vocab) * embedding_dim`만큼 embedding parameter 수가 늘어난다.
- 따라서 더 큰 vocabulary가 무조건 좋은 것은 아니다 — sequence 길이 감소와 parameter 증가라는 trade-off를 함께 봐야 한다.

### 7. Offset Mapping으로 원문 범위 추적

- `offset_mapping`은 Rust 기반 fast tokenizer(`tokenizer.is_fast`)에서만 제공된다.
- `return_offsets_mapping=True`로 인코딩하면 각 token의 `(start, end)` 문자 위치를 함께 얻는다.
- non-special token에서는 `source_piece == text[start:end]`가 성립해야 하며, special token은 보통 `(0, 0)`으로 표시된다.
- 정규화(normalization)가 적용되면 offset 해석에 주의가 필요하다 — 원문과 정규화된 문자열이 완전히 같지 않을 수 있다.

### 8. `max_length` 후보 절단 감사

- truncation 없이 special token을 포함한 원래 token 길이를 먼저 측정해야 절단률이 왜곡되지 않는다.
- 후보 길이별로 `truncated_count`(절단되는 문장 수), 보존 token 비율을 계산한다.
- 절단 비율이 가장 낮은 후보를 선택하고, 동률이면 더 작은 후보를 선택해 불필요하게 큰 `max_length`를 피한다.

## Environment

```bash
pip install -r requirements.txt
```
