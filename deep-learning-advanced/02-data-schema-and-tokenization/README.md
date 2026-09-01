# Chapter 2: Data Schema Auditing and Tokenization

> 2026-09-01 학습 기록. 2-1 이론과 기본 실습을 정리했습니다. 2-2·2-3은 완료하지 못해 `WEEKEND_PRACTICE_BACKLOG.md`로 이월했습니다.

## Learning Goals

- 필수 key 누락, 공백 텍스트, 중복 ID, 허용되지 않은 label을 원본 행 단계에서 한 번에 감사하는 함수를 만든다.
- 오류가 여러 개 겹쳐도 즉시 중단하지 않고 모든 검사를 끝내 하나의 report로 모은다.
- Greedy longest-match 방식의 toy subword tokenizer를 구현해 `##` prefix 규칙과 `[CLS]/[SEP]/[UNK]` 역할을 분리한다.

## Practice Files

| Lesson | File | Basic practice status |
| --- | --- | --- |
| 2-1 | `01-schema-audit-and-tokenizer-basic.ipynb` | 뉴스 샘플 schema 감사기(누락 key·공백 텍스트·중복 ID·허용 label), greedy longest-match subword tokenizer와 ID 왕복 확인 |
| 2-2 | 미완료 | 오늘 완료하지 못해 주말 backlog로 이월 |
| 2-3 | 미완료 | 오늘 완료하지 못해 주말 backlog로 이월 |

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

## Environment

```bash
pip install -r requirements.txt
```

표준 라이브러리(`collections.Counter`)만 사용하므로 별도 패키지 설치가 필요하지 않습니다.
