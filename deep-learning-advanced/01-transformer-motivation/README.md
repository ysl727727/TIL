# Chapter 1: RNN/LSTM Limits and Transformer Motivation

> 2026-09-01 학습 기록. 1-1~1-2 이론과 기본 실습을 정리했습니다.

## Learning Goals

- `nn.RNN` 없이 수동으로 hidden state 순환 계산을 구현해 순차 의존성을 직접 확인한다.
- RNN의 위치 간 최단 경로(`length-1`)와 Self-Attention 한 층의 경로(`1`), 그리고 attention score 원소 수(`length²`)를 계산해 서로 다른 병목을 비교한다.
- 정보 경로 길이와 `L²` 비용이라는 두 성질을 동시에 보고 한쪽 구조만 일방적으로 우월하다고 단정하지 않는다.
- 프로젝트 workflow 체크리스트에서 누락·중복·순서 오류를 함께 검증하는 감사 함수를 만든다.
- 분류(classification)와 생성(generation) task별로 model head·logits shape·loss·metric이 다름을 반영한 실행 계약(task plan)을 생성한다.

## Practice Files

| Lesson | File | Basic practice status |
| --- | --- | --- |
| 1-1 | `01-hidden-state-and-attention-cost-basic.ipynb` | 수동 RNN hidden state 구현, 첫 token 변경 시 마지막 상태 변화 검증, RNN vs Self-Attention 경로 길이·score 수 비교 확인 |
| 1-2 | `02-nlp-task-workflow-and-contract-basic.ipynb` | workflow 누락/중복/순서 검증기, classification·generation task별 실행 계약 생성기 확인 |

두 파일 모두 첫 실행에서 자동 검증(`PASS`)을 통과했고 별도 수정 셀은 없었습니다.

## Core Theory

### 1. 수동 RNN Hidden State

`hidden = tanh(token @ W_x + hidden @ W_h)` 공식으로 각 시점의 hidden state를 계산한다. 초기 hidden은 입력과 같은 dtype의 0 벡터로 만든다. 이전 hidden이 다음 시점 계산에 재사용되는 것이 순차 의존성의 실체이며, 첫 token만 바꿔도 여러 단계를 거쳐 마지막 상태가 달라진다는 사실로 이를 검증한다.

### 2. RNN vs Self-Attention 정보 경로·비용

- RNN 경로 길이: `length - 1` (인접 hidden을 순서대로 전달하는 횟수)
- Self-Attention 경로 길이: 한 층에서 모든 위치가 직접 연결되므로 `1`
- Self-Attention score 원소 수(head·batch 제외 기본값): `length ** 2`
- 길이가 32배가 되면 score 수는 `32² = 1,024`배가 된다. "경로가 짧다"는 사실이 "계산량이 항상 작다"를 의미하지 않으며, 서로 다른 병목(직렬 경로 길이 vs 메모리·score 비용)을 나란히 봐야 한다.

### 3. Workflow 검증

`Counter` 하나로 누락(missing)과 중복(duplicates)을 함께 계산할 수 있다. `set(stages) == set(REQUIRED)`만 비교하면 중복과 순서를 놓치므로, 실제 목록을 필수 단계 집합에 투영(projection)한 뒤 기준 순서와 비교해야 순서 오류를 잡는다. 오류가 있어도 즉시 중단하지 않고 모든 검사를 끝내 하나의 report로 모으면 한 번에 여러 문제를 확인할 수 있다.

### 4. Task별 실행 계약 (Classification vs Generation)

분류와 생성이 공유하는 것은 tokenizer(`AutoTokenizer`)뿐이다.

| | Classification | Generation |
| --- | --- | --- |
| Model | `AutoModelForSequenceClassification` | `AutoModelForCausalLM` |
| Logits shape | `[B, C]` | `[B, L, V]` |
| Loss | cross entropy | causal LM |
| Metric | accuracy, macro-F1 | quality review, latency |
| 완료 확인 | validation으로 선택 후 test 1회 | prompt 제거 후 새 token만 decode·검토 |

같은 tokenizer API를 쓴다고 model head까지 대체할 수 있는 것은 아니다 — head, loss, 후처리, 평가 지표가 모두 task에 따라 달라진다.

## Environment

```bash
pip install -r requirements.txt
```
