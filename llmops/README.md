# LLMOps

> 2026-10-30 LLMOps 1일차(1장 4강)부터 시작한 기록이에요. RAG·Context Engineering이 "무엇을 넣을까"였다면, LLMOps는 **"그 요청에서 실제로 무슨 일이 있었는지 증거를 남기고, 읽고, 비교하는 것"**이에요.

## 큰 흐름

```text
1장 실행 관측과 실패 원인 분석
  준비  .env 키 4개 → connect() → answer() → response_completed 점수
  1-1  기록하고   질문 1개 = Trace 1개, 검색은 직접 span · 모델은 CallbackHandler
  1-2  다시 찾고  Trace ID + 시간 범위로 재조회, GENERATION 종료 확인
  1-3  나누고     규정 문서 vs 업무 도구 결과, 부모 시간 ⊃ 자식 시간
  1-4  분류하고   형식 → 실행 실패 → 검색 없음 순서, failure_category 점수
      ↓
2장 (예정) Golden Dataset · 프롬프트 버전 · 변경 전후 회귀 판정
3장 (예정) usage · latency 집계
4장 (예정) 마스킹 · 보안 검사
```

## 장별 한 줄과 중요 개념

| 장 | 한 줄 | 중요 개념 |
| --- | --- | --- |
| [1장](./01-tracing-failure-analysis/) | 한 요청의 증거를 남기고 읽는다 | Trace vs observation, **호출 성공 ≠ 응답 완료 ≠ 품질 성공**, 열려 있는 with가 부모, flush ≠ 서버 조회, 부모 시간에 자식 포함, 판정 순서, 모르는 상태 ≠ 성공 |

## 오늘의 교훈

1. **모델을 바꾸기 전에 근거가 처음 사라진 단계부터.** 검색 → 입력 조립 → 생성 순서로 본다.
2. **완료는 정답이 아니다.** `completed`·`response_completed`·"서버 기록 확인"은 평가할 답이 있다는 뜻일 뿐.
3. **ID로 다시 찾는다.** 질문 문장이 아니라 Trace ID와 시간 범위로, 조회가 비었다고 모델을 다시 부르지 않는다.
4. **모르는 건 모른다고 분류한다.** 상태 누락·시각 오류를 성공으로 채우면 품질이 실제보다 좋아 보인다.

## 앞 과목과 이어지는 부분

| LLMOps 1장 | 앞에서 본 것 |
| --- | --- |
| system / human 메시지 분리 | CE 1장 `kind` vs `role` |
| context에 `[id] 본문` | CE 1장 `[id / kind / source]` 표지, RAG 6장 `[S1]` 인용 |
| 완료 검사 `MODEL_RESPONSE_INCOMPLETE` | RAG 6장 `validate_answer`, `insufficient ≠ system_error` |
| `retrieval_empty` | RAG 7-1 q10 BM25 `[]` |
| 검색 없음의 기대 행동 → Golden Dataset | RAG 8장 golden 세트 · Hit/Recall |
| `usage`의 `cache_read` | CE 4장 Prefix cache 서버 지표 |
