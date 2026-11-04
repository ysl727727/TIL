# LLMOps

> 2026-10-30 LLMOps 1일차(1장 4강)부터 시작한 기록이에요. 2026-11-02 2일차에 2장, 11-03 3일차에 3장, 11-04 4장을 들었어요. RAG·Context Engineering이 "무엇을 넣을까"였다면, LLMOps는 **"그 요청에서 실제로 무슨 일이 있었는지 증거를 남기고, 읽고, 비교하는 것"**이에요.

## 큰 흐름

```text
1장 실행 관측과 실패 원인 분석
  준비  .env 키 4개 → connect() → answer() → response_completed 점수
  1-1  기록하고   질문 1개 = Trace 1개, 검색은 직접 span · 모델은 CallbackHandler
  1-2  다시 찾고  Trace ID + 시간 범위로 재조회, GENERATION 종료 확인
  1-3  나누고     규정 문서 vs 업무 도구 결과, 부모 시간 ⊃ 자식 시간
  1-4  분류하고   형식 → 실행 실패 → 검색 없음 순서, failure_category 점수
      ↓  "고친 게 정말 좋아졌나?"
2장 평가 데이터와 변경 전후 검증
  2-1  질문 고정   golden 6개 검사 → dev 4 · holdout 2 데이터셋 (input · expected_output · metadata)
  2-2  변경 하나   같은 이름에 기준선 v1 · 후보 v2, 비교는 번호로 고정 (latest X)
  2-3  채점        dev 4 × 2버전 = 모델 8회, evaluate() 규칙 점수 4개, 오류 ≠ 0점
  2-4  판정        질문 ID로 짝짓기, 하나라도 나빠지면 BLOCK → 통과 후보만 holdout → REVIEW
      ↓  "점수는 같은데 더 비싸고 느려졌다면?"
3장 운영 지표 분석과 개선
  3-1  정의        모의 5행으로 지표별 분모, None = 모름 · 0 = 확인된 무료, p95와 timeout 장애
  3-2  측정        문맥 길이만 바꿔 before / after 번갈아 4회, usage · latency_ms, case_id로 짝
  3-3  사용자 신호  trace_id에 피드백 점수, 응답률(전체 요청) ≠ 긍정 비율(응답자)
  3-4  판단        GENERATION 비용만 합산, 버전별 summarize, 표본 → 비용 미확인 → 비용 증가 → REVIEW
      ↓  "기록에 개인정보가 남거나, 모델이 권한 밖 문서를 읽는다면?"
4장 신뢰 경계 · 개인정보 · 출력 검증 · 보안 평가
  4-1  권한        principal(서버 인증 결과)로만 판단, 읽기 전 차단, read_ids로 실제 읽기 확인
  4-2  개인정보    redact(모델 입력) · mask_spans(Langfuse) · 응답 검사(화면), 정규식의 한계
  4-3  출력        pydantic Answer: 구문 · 타입 → 필드 관계 → 출처 범위(<=), output_valid ≠ 사실 정확성
  4-4  공격 평가    direct · indirect · normal 같은 방어에, 공격 표식 없음 AND 업무 수행, run_tool 도구 통제
```

## 장별 한 줄과 중요 개념

| 장 | 한 줄 | 중요 개념 |
| --- | --- | --- |
| [1장](./01-tracing-failure-analysis/) | 한 요청의 증거를 남기고 읽는다 | Trace vs observation, **호출 성공 ≠ 응답 완료 ≠ 품질 성공**, 열려 있는 with가 부모, flush ≠ 서버 조회, 부모 시간에 자식 포함, 판정 순서, 모르는 상태 ≠ 성공 |
| [2장](./02-golden-dataset-prompt-regression/) | 같은 질문 · 같은 규칙으로 변경 전후를 질문별로 비교한다 | 기대 행동(terms · citations · abstain), dev/holdout, **프롬프트는 번호로 고정**, 시험지 · 답안지 분리, 대괄호 출처 set `==`, **오류 ≠ 0점**, ID로 짝짓기, 평균이 올라도 BLOCK |
| [3장](./03-operational-metrics-cost-feedback/) | 분모를 밝힌 지표로 비용 · 속도 · 사용자 반응을 읽는다 | **지표마다 분모가 다름**, **모르는 비용 ≠ 0원**, p95가 좋아진 장애(완료율 같이 보기), 한 가지만 바꿔 번갈아 측정, 피드백은 `trace_id`에, `score_id`로 중복 덮어쓰기, GENERATION만 합산, 판정 순서 |
| [4장](./04-trust-boundary-privacy-output-security/) | 모델이 판단하기 전에 애플리케이션이 경계마다 막고 증거를 남긴다 | **인증 결과 ≠ 사용자 주장**, 읽기 전 차단 + `read_ids`, 입력 · 관측 · 응답 마스킹은 따로, `redact(x) != x`, `extra="forbid"` · `strict=True` · `check_relation`, **존재하는 출처 ≠ 이번 요청의 출처**, 정상 대조군, **모델의 제안 ≠ 실행 허가** |

## 오늘의 교훈

1. **모델을 바꾸기 전에 근거가 처음 사라진 단계부터.** 검색 → 입력 조립 → 생성 순서로 본다.
2. **완료는 정답이 아니다.** `completed`·`response_completed`·"서버 기록 확인"은 평가할 답이 있다는 뜻일 뿐.
3. **ID로 다시 찾는다.** 질문 문장이 아니라 Trace ID와 시간 범위로, 조회가 비었다고 모델을 다시 부르지 않는다.
4. **모르는 건 모른다고 분류한다.** 상태 누락·시각 오류를 성공으로 채우면 품질이 실제보다 좋아 보인다.
5. **하나만 바꾸고 질문별로 본다.** 프롬프트 외의 조건은 고정하고, 평균이 올라도 나빠진 질문이 하나라도 있으면 막는다.
6. **실패는 0점이 아니다.** 틀린 답(0점)과 평가할 답이 없는 오류를 섞으면 프롬프트 탓인지 인프라 탓인지 모른다.
7. **숫자보다 분모 먼저.** 오류율 · p95 · 응답률 · 긍정 비율은 분모가 다 다르다. 분모와 파악률(coverage)을 같이 남긴다.
8. **모르는 비용은 0원이 아니다.** 하나라도 모르면 합계는 None, 비용 · 지연이 좋아져도 품질 지표와 함께 본다.
9. **모델의 말은 권한 증명이 아니다.** 권한은 서버의 인증 결과로, 본문을 읽기 전에 검사한다.
10. **막는 코드와 막았다고 말하는 코드는 다르다.** `read_ids` · `rejected != 2` · `read_ids == []`처럼 실제 부작용으로 검사기를 검사한다.

## 앞 과목과 이어지는 부분

| LLMOps | 앞에서 본 것 |
| --- | --- |
| 1장 system / human 메시지 분리 | CE 1장 `kind` vs `role` |
| 1장 context에 `[id] 본문` | CE 1장 `[id / kind / source]` 표지, RAG 6장 `[S1]` 인용 |
| 1장 완료 검사 `MODEL_RESPONSE_INCOMPLETE` | RAG 6장 `validate_answer`, `insufficient ≠ system_error` |
| 1장 `retrieval_empty` | RAG 7-1 q10 BM25 `[]` |
| 1장 검색 없음의 기대 행동 → 2장 Golden Dataset | RAG 8장 golden 세트 · Hit/Recall |
| 1장 `usage`의 `cache_read` | CE 4장 Prefix cache 서버 지표 |
| 2장 dev / holdout 분리 | RAG 8장 dev/test 분리 |
| 2장 질문 ID로 짝짓기 | CE 4장 `bodies[meta["id"]]`, RAG 5장 `chunks[i]` 짝 문제 |
| 2장 abstain은 진짜 bool만 | CE 2장 `type(ttl) is int` |
| 2장 대괄호 출처 set 비교 | CE 4장 `set(args) != {"query"}`, RAG 6장 `[S1]` 인용 |
| 3장 문맥 길이와 입력 토큰 · 비용 | CE 3장 토큰 예산 · 압축 |
| 3장 GENERATION만 합산(부모 비용 중복) | 1장 부모 시간에 자식 시간 포함 |
| 3장 판정 순서(None 먼저 거르기) | 1장 `classify` "처음 걸리는 return이 결과" |
| 3장 `{v: summarize(...) for v in ...}` | 2장 `[r for r in rows if r["split"] == split]` |
| 4장 문서 안의 명령 따르지 않기 · 간접 주입 | CE 4장 컨텍스트 오염 · Prompt Injection |
| 4장 `run_tool` 키 · 이름 허용 목록 | CE 4장 실행 전 도구 검사 `set(args) != {"query"}` |
| 4장 `Answer` + 출처 범위 `<=` | RAG 6장 `validate_answer` · `[S1]` 인용 |
| 4장 `security_case_pass`를 같은 Trace에 | 3장 피드백을 `trace_id`에 `create_score` |
