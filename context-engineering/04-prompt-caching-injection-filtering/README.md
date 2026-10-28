# 4장. Prompt Caching과 컨텍스트 오염 — 정적 Prefix · 캐시 지표 · Prompt Injection · 신뢰도 필터링

> 2026-10-28 학습 기록. Context Engineering 1일차 오후 수업입니다. 요청 간에 앞부분 계산을 재사용하는 Prefix cache를 위해 고정 지시는 앞에, 요청별 값은 뒤에 두고 공통 앞부분 토큰을 비교했고(4-1), 접근 범위·구버전·Prompt Injection으로 컨텍스트가 오염되는 경우를 범위 확인 → 본문 검사 → 실행 전 도구 검사 순서로 걸렀습니다(4-2).

## 학습 목표

- KV cache · 요청 간 Prefix cache · 응답 cache가 각각 무엇을 재사용하는지 구분하고, Prefix 재사용이 줄이는 쪽이 Prefill이라는 것을 안다.
- 고정 지시를 앞에, 요청 ID 같은 값을 뒤에 두면 공통 앞부분이 길어지는 것을 토큰 비교로 확인한다.
- 공통 토큰 수(구조 지표)와 서버의 실제 캐시 사용량(서버 지표)을 구분하고, 지표가 없음(None)과 0을 구분한다.
- 오염의 네 원인(접근 범위 · 오래된 정보 · 기억/요약 오류 · Prompt Injection)과 직접·간접 Injection을 구분한다.
- 본문을 읽기 전에 범위부터 확인하고, 문구 필터의 오탐·미탐을 이해하며, 모델이 제안한 도구 호출을 실행 전에 검사한다.

## 실습 파일

| 강 | 주제 | 실습 상태 |
| --- | --- | --- |
| 4-1 | Prompt Caching과 정적 Prefix 설계 — `build_messages` A/B, `common_prefix_length`, `cache_observation` | ✅ `lesson_01.py` · q1\_hard 통과 |
| 4-2 | 오염 · Prompt Injection · 신뢰도 필터링 — 범위 필터, 의심 문구 격리, `validate_action` | ✅ `lesson_02.py` · q2\_hard 통과 |

4-1은 3장과 같은 Qwen3 토크나이저로 토큰을 비교해요. 서버를 호출하지 않아서 실제 캐시 적중이나 속도는 재지 않아요.

## 전체 흐름

```text
4-1 재사용
 A: [요청 ID][정책 버전][정책][질문]   → 공통 앞부분 11토큰 (요청 ID에서 갈라짐)
 B: [정책 버전][정책][요청 ID][질문]   → 공통 앞부분 94토큰
 B라도 정책 v2 → v3                    → 8토큰 (정책이 바뀌면 예전 캐시 못 씀)
 실제 재사용은 서버 지표: None(모름) / 0 / 숫자

4-2 거르기
 catalog → 조직 다르면 제외 → 구버전 제외 → 본문 읽기 → 의심 문구 격리 → 통과
 모델 제안 도구 호출 → 사용자 권한 → 허용 도구 → 인자 구조 → 검색어 → 실행 여부
```

## 핵심 이론

### 1. 캐시는 무엇을 재사용하나 (4-1강)

| 종류 | 재사용하는 것 | 새 질문에 대한 생성 |
| --- | --- | --- |
| 한 생성 안의 KV cache | 앞서 처리한 토큰의 내부 상태 | 다음 토큰을 계속 생성 |
| 요청 간 Prefix cache | 여러 요청이 공유하는 앞부분의 계산 상태 | 공통 입력 처리 재사용, 답변은 새로 |
| 응답 cache | 이미 완성한 답변 | 유효하면 모델 호출 생략 |

- Prefill(입력 처리) → Decode(답변 생성). **Prefix 재사용이 줄이는 쪽은 Prefill.** 입력이 길고 답변이 짧으면 효과가 크고, 답변이 길면 생성 시간이 지배해서 전체 시간이 같은 비율로 줄지 않아요(딥러닝 심화 4강 Prefill/Decode, RAG 1장 CAG와 연결).
- 지표마다 재는 구간이 달라요: 입력 처리 시간 / TTFT(첫 응답 토큰까지) / 전체 응답 시간 / 캐시 사용량. 속도가 빨라도 조건이 빠진 답변이면 의미가 없어서 **답변 내용도 같이 기록**해요.

### 2. 고정은 앞에, 요청별은 뒤에 (4-1강)

- 캐시는 **맨 앞에서부터 토큰이 똑같은 구간**까지만 재사용해요. 중간에 하나라도 다르면 그 뒤는 새로 계산.
- "숙박 한도는 12만원"과 "호텔비 상한은 12만원"은 뜻이 같아도 토큰 배열이 달라요. Prefix 비교는 의미 유사도가 아니라 **시작부터 연속으로 같은 토큰**이에요.
- 역할·줄바꿈·정책 버전·도구 정의 순서가 바뀌어도 직렬화 결과가 달라져서, 입력 생성 함수를 한곳에서 관리해요.
- 정책이 바뀌었는데 기존 캐시를 쓰면 빠르지만 틀려요 → **정책 버전 변경을 무효화 기준**에 넣어요.

| 함수 | 넣는 것 | 돌려주는 것 | 하는 일 |
| --- | --- | --- | --- |
| `build_messages(mode, request_id, question, version)` | A/B, 요청 ID, 질문, 정책 버전 | `[system, user]` | A: ID를 system 맨 앞 / B: 정책만 system, ID는 user |
| `token_ids(messages)` | messages | 토큰 번호 리스트 | `apply_chat_template`로 역할 표시까지 숫자로 |
| `common_prefix_length(left, right)` | 토큰 리스트 2개 | 정수 | 앞에서부터 연속으로 같은 개수, 다르면 `break` |
| `cache_observation(value)` | 캐시 토큰 수 | 설명 문장 | None(모름) / 0 / 숫자 구분 |

- 비유: 편지 두 장을 앞에서부터 비교. **안 바뀌는 건 앞에, 바뀌는 건 뒤에.**

### 3. 오염의 원인과 Injection (4-2강)

| 유형 | 예 | 먼저 확인할 곳 |
| --- | --- | --- |
| 접근 범위 위반 | 다른 조직의 비공개 문서 | 인증과 저장소 조회 범위 |
| 오래된 정보 | 폐기된 정산 규정 | 적용 상태와 버전 |
| 기억과 요약의 오류 | 예전 담당자를 현재로 기록 | 출처와 변경 이력 |
| Prompt Injection | 자료 속 문장으로 지시·도구 행동을 바꾸려 함 | 지시와 자료 구분, 행동 제약 |

- 직접 Injection: 사용자가 직접 기존 지시를 어기라고 요구. 간접 Injection: 검색 문서·웹·메일·도구 결과 **안의** 문장.
- 신뢰도는 문장 점수 하나로 정하기 어려워요. 출처 · 수정 가능자 · 현재 사용자의 열람 권한 · 허용 행동을 함께 봐요.

### 4. 범위 → 본문 → 실행 전 검사 (4-2강)

```text
other-team       -> 권한 범위 제외   (본문을 읽지도 않음)
old-policy       -> 구버전 제외
injected-note    -> 의심 문구 격리   공격 문구를 잡음
security-guide   -> 의심 문구 격리   공격 문구를 인용한 보안 설명 → 오탐
paraphrased-note -> 통과            승인 절차 생략을 돌려 말함   → 미탐
current-policy   -> 통과            필요한 근거
```

- 조직(`current_tenant`)은 사용자가 입력한 문자열이 아니라 **인증 결과**로 정해요.
- 오탐(정상을 막음)은 엄격할수록, 미탐(공격을 놓침)은 느슨할수록 늘어요. 문구 목록만 늘리는 방식엔 한계가 있어요.
- 모델의 **제안**과 **실행 권한**은 달라요. `validate_action`이 사용자 권한(모델이 만든 값이 아님) → 허용 도구(`policy_search`) → 인자 구조 → 검색어 순으로 검사해요. True는 이 예제의 검사 통과만 뜻하고, 실제 저장소 권한 필터는 따로 필요해요.
- 단계마다 다른 검사: 검색·조회(읽을 수 있나) / 입력 조립(지시와 근거 구분) / 메모리·요약(오염이 다음 세션에 남나) / 행동 실행(허용 도구·인자·권한) / 결과 검토(근거를 따르나, 보호 정보 노출 없나).
- 승인 조회 중 오류면 "미승인"으로 단정하지 않고 조회 실패로 처리해요. 모델이 "승인받았다"고 쓴 문장은 **승인 기록이 아니에요.**

## 질문과 새로 알게 된 점

### q1\_hard: 같은 입력의 공통 길이와 서버 지표

```python
same = common_prefix_length(first, second)        # 완전히 같은 입력 → same == len(first)
readings = [cache_observation(response.get("prompt_eval_cached_count")) for response in responses]
# 필드 없음 → "캐시 사용량을 알 수 없음" / 0 → "캐시에서 읽은 토큰이 0개" / 96 → "캐시에서 읽은 토큰 96개"
```

- 공통 길이가 전체여도 실제 재사용 여부는 **서버 지표로만** 확인해요(구조 지표 ≠ 서버 지표).
- `value`는 `cache_observation`의 매개변수(API가 알려 준 캐시 토큰 수). `if not value`로 쓰면 None과 0이 둘 다 거짓이라 구분이 안 돼요 → `is None`, `== 0` 따로(딥러닝 기초 `grad is None` vs gradient 0과 같은 이야기).
- **`response["키"]` vs `response.get("키")`:**
  - 키 이름이 글자라서 둘 다 따옴표가 필요해요. 따옴표 없이 `response[prompt_eval_cached_count]`면 그런 변수를 찾다가 `NameError`.
  - `[ ]`는 바로 꺼내기(없으면 `KeyError`, RAG 9-2 `OLLAMA_MODEL` 오류와 같음). `.get( )`은 dict의 **메서드 호출**이라 괄호, 없으면 `None`. `.get("키", 0)`이면 없을 때 0.

### `validate_action`의 세 번째가 "인자 구조 불일치"인 이유

```text
policy_search {query: "숙박 한도"}           -> True  / 조회 가능
send_email    {to: outside@…}               -> False / 허용하지 않은 도구
policy_search {query, path: "private"}      -> False / 인자 구조 불일치
```

- `set(args)`는 dict의 **키만** 모은 집합 → `{"query", "path"}`. `!= {"query"}`로 **정확히 같은지** 비교해서, query가 있어도 뭐가 하나 더 붙으면 거절해요. 모델이 몰래 `path: "private"`(비공개 경로)를 끼워 넣는 걸 막는 검사예요.

### q2\_hard: 의심 문구를 하나 더 추가하면

```python
quarantined = [] # 격리라는뜻
for meta in catalog:
    if meta["tenant"] != current_tenant or meta["status"] != "current":
        continue
    text = bodies[meta["id"]]
    if any(phrase in text for phrase in suspicious):
        quarantined.append(meta["id"])
    else:
        passed.append(meta["id"])
# 격리: injected-note · security-guide(오탐) · paraphrased-note / 통과: current-policy
```

- **왜 `bodies[meta["id"]]`?** bodies는 본문 하나가 아니라 **문서 ID → 본문 dict**예요. 안쪽부터 `meta["id"]` = "doc-2" → `bodies["doc-2"]`. catalog = 꼬리표(id·tenant·status), bodies = 본문 글. RAG `chunks[i]`로 원문을 찾던 것과 같은 짝 맞추기.
- `bodies`를 그대로 쓰면 `phrase in bodies`가 **키(문서 ID들)**를 검사해서 문구를 하나도 못 찾아요.
- **인덱싱으로는 못 뽑나?** dict에서는 키로 찾는 게 곧 인덱싱(이름으로). `bodies[0]` 같은 순번은 없어요(KeyError). bodies를 catalog와 같은 순서의 리스트로 만들면 `enumerate`의 `bodies[i]`나 `zip(catalog, bodies)`로도 되지만, 순서가 하나라도 어긋나면 **다른 본문과 조용히 짝이 맞아 버려요**(RAG 5장 `chunks[i]`·`vectors[i]` 짝 문제). ID로 찾으면 항상 자기 본문이고, 없는 ID면 바로 KeyError라 실수를 빨리 알아요.
- 문구를 "승인 절차는 생략"까지 늘리니 미탐이던 paraphrased-note가 잡혔어요. 하지만 표현은 끝없이 바뀔 수 있어서 실행 전 `validate_action` 같은 검사가 함께 필요해요.

## 실습 코드에서 직접 바꾼 점

| 파일 | 바꾼 점 / 추가한 주석 |
| --- | --- |
| ch04 `q1_hard.py` | 위 `same = common_prefix_length(first, second)`, `readings` 컴프리헨션 |
| ch04 `q2_hard.py` | `quarantined = [] # 격리라는뜻` 주석, 위 범위·문구 필터 for문 |

4-1 `lesson_01.py`, 4-2 `lesson_02.py`는 코드 설명만 했고 바꾸지 않았어요.

## 하루 정리 (PPT)

| 장 | 한 줄 |
| --- | --- |
| 1-1 · 1-2 | 사용자·질문 확인, 허용 자료 선택 |
| 2장 | 범위 안의 메모리, 조회 시 만료 |
| 3-1 | 전체 토큰 계산, 출력 공간 먼저 |
| 3-2 | 조건·출처를 유지하며 압축 |
| 4-1 | 고정 지시를 일정하게, 정책이 바뀌면 갱신 |
| 4-2 | 실행 전 재검사, 빠진 조건 확인 |

**필요한 정보를, 유효한 범위에서, 예산 안에, 권한에 맞게 넣어요.**

## 마무리 과제 (PPT)

- [ ] `ch04/lesson_02.py`에 "승인 단계는 건너뛰어도" 문서를 추가해 의심 문구 필터가 통과시키는지 확인

## 확인 문제

### CE4-Q1. Prefix 배치 (4-1)

요청마다 바뀌는 요청 ID를 어디에 두어야 공통 앞부분이 길어질까?

① 고정 지시 뒤, user 메시지 쪽  
② system 맨 앞  
③ 정책 본문 중간  
④ 위치는 상관없다

<details>
<summary>정답 보기</summary>

**①** — A(ID가 system 맨 앞)는 11토큰에서 갈라지고, B(ID를 뒤로)는 94토큰까지 같아요. 캐시는 맨 앞부터 연속으로 같은 구간만 재사용해요.

</details>

### CE4-Q2. 캐시 지표 (4-1)

두 요청의 공통 앞부분 토큰 수가 전체 길이와 같다. 맞는 설명은?

① 서버가 반드시 캐시를 재사용했다  
② 답변도 캐시에서 그대로 나온다  
③ 구조상 재사용이 가능할 뿐, 실제 재사용 여부는 서버가 보고한 캐시 지표로 확인해야 한다  
④ Decode 시간이 0이 된다

<details>
<summary>정답 보기</summary>

**③** — 모델·토크나이저·저장 단위·보존 상태·처리 서버에 따라 재사용이 안 될 수 있어요. Prefix cache는 Prefill만 줄이고 답변은 새로 만들어요.

</details>

### CE4-Q3. None vs 0 (4-1)

`cache_observation`에서 `if not value:`로 검사하면 안 되는 이유는?

① 숫자 비교가 안 돼서  
② None(지표가 제공되지 않음)과 0(보고됐는데 0개)이 둘 다 거짓이라 구분할 수 없어서  
③ 음수가 나올 수 있어서  
④ 문자열이 들어와서

<details>
<summary>정답 보기</summary>

**②** — 모른다와 0이다는 다른 사실이라 `is None`과 `== 0`을 따로 검사해요.

</details>

### CE4-Q4. 오탐과 미탐 (4-2)

"이전 지시를 무시" 문구 필터에서 security-guide(공격 문구를 인용한 보안 설명)가 격리되고 paraphrased-note(승인 절차 생략을 돌려 말함)가 통과했다. 각각은?

① 둘 다 정상 동작  
② security-guide는 미탐, paraphrased-note는 오탐  
③ 둘 다 미탐  
④ security-guide는 오탐(정상을 막음), paraphrased-note는 미탐(공격을 놓침)

<details>
<summary>정답 보기</summary>

**④** — 엄격하게 하면 오탐이, 느슨하게 하면 미탐이 늘어요. 그래서 문구 필터만으로 끝내지 않고 실행 전 도구 검사까지 단계별로 둬요.

</details>

### CE4-Q5. 서술형 — 정책이 바뀌었을 때의 캐시 (4-1)

정책 버전을 v2 → v3로 바꾸자 공통 앞부분이 94 → 8토큰으로 줄었다. 왜 그런지, 그리고 "속도를 위해 예전 캐시를 계속 쓰자"는 제안이 왜 문제인지 쓰세요.

<details>
<summary>예시 답안</summary>

B 배치에서 system은 `정책 버전: v2` 줄로 시작하는데, 이 줄이 v3로 바뀌면 그 지점부터 토큰이 달라져서 앞부분이 거의 공유되지 않아요(역할 표시 등 8토큰만 같음). 캐시는 앞에서부터 연속으로 같은 구간만 재사용하니 예전 정책의 계산 상태는 새 입력에 쓸 수 없어요. 만약 예전 캐시를 억지로 쓰면 모델이 폐기된 정책을 근거로 답하게 돼서 빠르지만 틀린 답이 나와요. 그래서 정책 버전 변경을 캐시 무효화 기준에 넣고, 입력 생성 함수를 한곳에서 관리해 의도치 않게 직렬화가 바뀌지 않게 해요.

</details>

### CE4-Q6. 서술형 — 본문을 읽기 전에 범위부터 (4-2)

catalog 필터에서 조직·현행 여부를 본문 검사보다 **먼저** 하는 이유와, `current_tenant`를 사용자 입력으로 받으면 안 되는 이유를 쓰세요.

<details>
<summary>예시 답안</summary>

다른 조직의 비공개 문서는 내용이 안전하든 아니든 현재 사용자가 읽을 권한이 없어서, 본문을 열어 문구를 검사하는 것 자체가 범위 위반이에요. 구버전도 현재 근거가 될 수 없으니 먼저 빼요. 그래서 "본문을 읽은 ID"에 other-team·old-policy가 없어요. 조직은 인증 결과로 정해야 해요. 사용자가 입력한 문자열로 정하면 다른 조직 이름을 넣기만 해도 그 조직 문서가 범위 안으로 들어와 필터가 무력해져요(2장 `user_id` 필터만으로는 인증이 아닌 것과 같은 이야기).

</details>
