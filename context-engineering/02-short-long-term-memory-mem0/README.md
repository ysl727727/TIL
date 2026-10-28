# 2장. 단기·장기 메모리 설계와 Mem0 — 저장 판단 · 보존 기간 · ID로 수정·삭제

> 2026-10-28 학습 기록. Context Engineering 1일차 오전 수업입니다. 기억 후보를 "저장하지 않음 / 현재 대화만 / 확인 필요 / 장기 저장"으로 나누고 만료를 조회 시점에 확인하는 정책(2-1), 실제 메모리 저장소 Mem0(Ollama 임베딩 + Qdrant 로컬 파일 + SQLite 이력)로 저장 → 조회 → 수정 → 삭제를 실습했습니다(2-2).

## 학습 목표

- 단기·장기 메모리를 저장 장소가 아니라 **쓰임**(지금 작업 vs 다음 세션)으로 나눈다.
- `decide_memory`로 저장 결정과 **이유**를 함께 돌려주고, 필요한 필드만 옮기고, 조회할 때 다시 만료를 확인한다.
- Mem0의 네 역할(추출 LLM · Embedder · Vector store · History store)과 `from_config` / `add`의 차이를 설명한다.
- add 응답의 ID로 대상을 고정하고, `owned_record`로 소유자를 확인한 뒤 수정·삭제한다. 삭제 범위(활성 목록 · 이력 · 캐시 · 백업)를 구분한다.

## 실습 파일

| 강 | 주제 | 실습 상태 |
| --- | --- | --- |
| 2-1 | 단기 메모리와 장기 메모리 설계 — `decide_memory`, 만료, `active_memories` | ✅ `lesson_01.py` · q1\_hard 통과 |
| 2-2 | Mem0로 저장부터 삭제까지 — `from_config`, `add`, `get_all` · `search`, `owned_record`, `update` · `delete` | ✅ `lesson_02.py` · q2\_hard 통과 |

2-2는 Ollama 임베딩 모델 `nomic-embed-text`(768차원)가 필요하고, 실행하면 `ch02/local_store`에 Qdrant 데이터와 `history.db`가 생겨요. 실행할 때마다 새 사용자 ID를 써서 이전 실행과 섞이지 않아요.

### 환경 문제: grpcio DLL 차단

- 키트의 `grpcio 1.85.0`을 Windows **스마트 앱 컨트롤**이 막아서 `qdrant_client`·`mem0` import 때 `DLL load failed while importing cygrpc: 애플리케이션 제어 정책에서 이 파일을 차단했습니다`가 났어요(RAG 9-3 `srsly`와 같은 현상).
- RAG 키트의 `grpcio 1.84.0`은 정상이라, 2-2 파일 4개만 그 버전을 얹어 실행했어요. 키트 파일은 바꾸지 않았어요.

```powershell
uv run --with grpcio==1.84.0 lesson_02.py
```

## 전체 흐름

```text
기억 후보
 └─ decide_memory → (결정, 이유)
      secret                       → 저장하지 않음
      session                      → 현재 대화만 (단기)
      preference 아님 / 동의 없음    → 확인 필요
      ttl이 int 아님 / 1~180 밖     → 확인 필요 (보존 기간)
      통과                          → 장기 저장 → 필요한 필드만 + expires_on
 └─ 조회할 때: 사용자 범위 · 관련성 · 만료(expires_on > 오늘)

Mem0 (2-2)
 from_config(빈 저장소 설정) → add(기억 넣기, ADD ID 받기)
 → get_all(저장됐나) / search(찾아지나)
 → owned_record(내 것인가) → update → 다시 읽기
 → owned_record → delete → get_all로 사라졌나 → client.close()
```

## 핵심 이론

### 1. 단기 vs 장기 (2-1강)

| 구분 | 단기 메모리 | 장기 메모리 |
| --- | --- | --- |
| 목적 | 지금 대화·작업을 이어 감 | 다음 세션에서도 다시 씀 |
| 예 | 현재 예약, 직전 도구 결과, 미완료 단계 | 응답 언어 선호, 확인된 프로젝트 상태 |
| 끝나는 기준 | 작업 완료, 세션 종료, 상태 만료 | 목적 종료, 선호 변경, 보존 기한, 삭제 요청 |
| 주의 | 오래된 도구 결과를 현재 사실로 쓰지 않기 | 저장됐어도 지금 유효한지 확인 |

- 저장 후보를 볼 때 묻는 네 가지: 다음 대화의 어떤 질문에 쓰나 · 누구의 정보인가 · 당사자가 확인했나 · 언제까지 유효한가.
- 비밀 정보는 임베딩·추출 단계로 보내기 **전에** 빼요. 모델의 추측과 사용자가 직접 밝힌 선호는 근거가 달라요.
- "30일 지나면 자동 삭제?" → 아니에요. `active_memories`는 **조회에서 빼는 필터**일 뿐, 물리 삭제·백업·이력 정리는 따로 설계해요.
- 요약한 대화도 장기 메모리가 아니에요. 요약은 표현 방식이고, 세션을 넘어 재사용하기로 했을 때 장기 메모리 정책을 적용해요.

```text
m1 preference·동의·30  → 장기 저장   (만료 2026-11-07)
m2 session·A호텔       → 현재 대화만
m3 secret              → 저장하지 않음
m4 preference·동의 X   → 확인 필요
m5 preference·ttl 0    → 확인 필요 (보존 기간)
만료일 당일 조회 결과 수: 0
```

### 2. Mem0의 네 역할 (2-2강)

| 역할 | 하는 일 | 이 실습 |
| --- | --- | --- |
| 추출용 LLM | 저장할 사실 추출·갱신 판단 | Ollama qwen3 설정만, `infer=False`라 호출 안 함 |
| Embedder | 기억·질문 → 벡터 | `nomic-embed-text` 768차원 |
| Vector store | 벡터·기억 저장·조회 | Qdrant 로컬 폴더 |
| History store | 변경 이력 | SQLite `history.db` |

- `Memory.from_config`는 **빈 저장소를 만드는 설정**(서랍장 조립)이고, 기억은 `memory.add(...)`로 넣어요(서랍에 메모). RAG 5장으로 치면 `from_config` = `QdrantClient()` + `create_collection`, `add` = `upsert`.
- `MEM0_TELEMETRY=False`·`MEM0_DIR` 환경 변수는 `from mem0 import Memory` **전에** 설정해요.
- `infer=False`: LLM 추출 없이 원문 그대로 저장.
- `get_all(filters=scope)` = **저장됐나**(목록), `search(..., threshold=0)` = **찾아지나**(유사도). 한 건을 찾았다고 검색 품질이 좋다고 판단할 수 없어요.

### 3. ID로 수정·삭제 (2-2강)

- ✗ search 결과 `[0]`을 수정 / ✗ update 응답만 보고 성공 처리 / ✓ **add 응답 ID → 범위 확인 → 수정 → 재조회**.
- `user_id` 필터만으로 인증이 해결되지 않아요. 필터에 넣는 ID 자체를 신뢰할 수 있어야 해요.
- 삭제 뒤 확인할 곳: 활성 목록·검색 / 이미 꺼낸 컨텍스트 / 이력과 로그 / 캐시와 백업. "완전히 삭제됐어요"라고 안내하려면 이력·백업까지 처리해야 해요.

```text
저장 수: 1
등록한 기억 검색: True
수정 후: 한국어로 자세한 설명을 선호합니다.
활성 목록에서 삭제: True
```

## 질문과 새로 알게 된 점

### q1\_hard: 새 후보 저장 판단과 만료

```python
results = []
new_records = []
for item in new_candidates:
    decision, reason = decide_memory(item)
    results.append((item["id"], decision))
    if decision == "장기 저장":
        new_records.append({
            "source_id": item["id"], "text": item["text"],
            "expires_on": (today + timedelta(days=item["ttl_days"])).isoformat(),
        })
# results = [('m6', '장기 저장'), ('m7', '확인 필요')]   m6 만료 2027-04-06
```

- **bool은 int의 하위 타입**이라 `isinstance(True, int)`는 통과해 버려요. 그래서 `type(ttl) is not int`로 정확히 검사해요. 안 그랬으면 `timedelta(days=True)` = 1일짜리 기억이 조용히 저장됐을 거예요.
- `reason`은 results에 담지 않아서 출력되지 않아요. 보려면 `(item["id"], decision, reason)`으로 같이 담아요.

### `purpose`(2-2) vs `reason`(2-1)

- `reason`은 저장 **전** 심사 결과의 이유(반환값, 저장소에는 안 들어감).
- `purpose`는 저장하면서 붙이는 **용도 꼬리표**(2-1의 "재사용 목적"을 실제로 적은 것). `source`(어디서 왔나)와 함께 metadata에 넣어요. metadata는 내가 이름 짓는 dict라 `"reason": reason`도 넣을 수 있어요.

### `new_ids`와 `target_id`

```text
added = {"results": [{"id": "31968933-effd-…", "memory": "한국어로 짧은 답변을 선호합니다.",
                      "event": "ADD", "actor_id": null, "role": "user"}]}
new_ids = ['31968933-effd-…']
```

- `row`는 장소가 아니라 for문에서 꺼낸 **항목(dict 하나)의 변수 이름**. `new_ids = []` → `for row in added["results"]: if row.get("event") == "ADD": new_ids.append(row["id"])`와 같아요.
- `if len(new_ids) != 1: raise`: 문장 하나를 넣었으니 ADD ID도 정확히 1개여야 정상. 0개(저장 안 됨)면 그냥 두면 `IndexError`, 2개 이상(`infer=True`로 쪼개짐)이면 엉뚱한 기억을 수정·삭제할 위험 → **애매하면 추측하지 말고 멈춤**(RAG 6장 `validate_answer`와 같은 생각).
- `[0]`은 리스트에서 문자열 하나를 꺼내려고(`get`·`update`·`delete`는 ID 문자열을 받음).

### `user_id` vs `memory_id`

| | `user_id` | `memory_id` (`target_id`) |
| --- | --- | --- |
| 뜻 | **누구의** 기억인가 | **어떤** 기억인가 |
| 만드는 곳 | 교안이 `"lecture-" + uuid4().hex[:12]`로 직접 | `add` 때 Mem0가 붙여 줌 |
| 쓰는 곳 | filters 범위, 소유자 확인 | get · update · delete로 하나 집기 |

- Mem0 ID도 무작위예요. 설치된 mem0 코드(`mem0/memory/main.py`)에서 `memory_id = str(uuid.uuid4())`를 확인했어요. 같은 문장을 다시 add해도 새 번호.
- **uuid는 암호화가 아니에요.** 겹치지 않는 무작위 이름표일 뿐(`.hex`는 하이픈 없는 16진수, `[:12]`는 앞 12글자). 추측하기 어려울 뿐 비밀번호가 아니라서 `owned_record`로 주인을 확인해야 해요.
- `owned_record(memory_id)`: `memory.get`으로 꺼낸 기억의 `user_id`가 지금 사용자와 다르거나 없으면 `PermissionError`. 이전 실행의 ID나 이미 지운 ID(`get`이 None)가 막혀요. 로그인 검증은 이 함수가 하지 않아요.

### q2\_hard: 두 기억 중 첫 번째만 삭제

```python
first_id = [row["id"] for row in first["results"] if row.get("event") == "ADD"][0]
second_id = [row["id"] for row in second["results"] if row.get("event") == "ADD"][0]
owned_record(first_id)
memory.delete(first_id)
# 남은 기억 = "영어 용어는 괄호로 함께 적어 주세요." 하나 / 다른 사용자 ID → PermissionError
```

- 교안의 `new_ids` → `[0]` 두 줄을 한 줄로 합친 것. 단 `len != 1` 검사가 빠져서 0개면 `IndexError`.
- 기억이 2개라 검색 1위를 지우면 엉뚱한 쪽이 지워질 수 있어서 **add 응답의 ID로 대상을 고정**해요.

## 실습 코드에서 직접 바꾼 점

| 파일 | 바꾼 점 / 추가한 주석 |
| --- | --- |
| ch02 `q1_hard.py` | 위 `results`·`new_records` for문, 끝에 주석 `# 실무에서는 추가로 DB를 insert한다던지 할 수 있다.` |
| ch02 `q2_hard.py` | 위 `first_id`·`second_id` 컴프리헨션 + `[0]`, `owned_record(first_id)` → `memory.delete(first_id)` |
| 실행 방법 | 2-2 파일만 `uv run --with grpcio==1.84.0` (키트 파일 수정 없음) |

## 마무리 과제 (PPT)

- [ ] `ch02/local_store` 폴더를 열어 qdrant 데이터와 `history.db`가 따로 있는지 확인

## 확인 문제

### CE2-Q1. 단기 vs 장기 (2-1)

장기 메모리 후보로 알맞은 것은?

① 현재 예약 중인 A호텔 이름  
② 사용자가 동의하고 보존 기간 30일을 정한 "한국어로 간결한 설명 선호"  
③ 직전 도구 호출 결과  
④ 사용자의 비밀번호

<details>
<summary>정답 보기</summary>

**②** — 다음 세션에서도 쓰이고, 당사자가 확인했고, 보존 기간이 있어요. ①·③은 현재 대화만(단기), ④는 저장하지 않음(그리고 임베딩 전에 빼기).

</details>

### CE2-Q2. ttl 검사 (2-1)

`ttl_days`가 `True`인 후보를 `isinstance(ttl, int)`로만 검사하면?

① TypeError가 난다  
② "저장하지 않음"이 된다  
③ 자동으로 180일로 바뀐다  
④ bool이 int의 하위 타입이라 통과해서 1일짜리 기억이 조용히 저장된다

<details>
<summary>정답 보기</summary>

**④** — `isinstance(True, int)`는 True. 그래서 `type(ttl) is not int`로 bool을 걸러 "확인 필요(보존 기간)"로 보내요.

</details>

### CE2-Q3. 수정 대상 고르기 (2-2)

기억을 수정할 때 올바른 순서는?

① add 응답 ID로 대상 고정 → `owned_record`로 소유자 확인 → update → 다시 읽어 확인  
② search 결과 `[0]`을 바로 update  
③ update 응답만 보고 성공 처리  
④ user\_id 필터만 맞으면 확인 없이 update

<details>
<summary>정답 보기</summary>

**①** — 검색 순서는 질문에 따라 바뀌어 엉뚱한 기억을 고칠 수 있고, update 응답만으로는 실제 저장 상태를 몰라요. user\_id 필터는 인증이 아니에요.

</details>

### CE2-Q4. 삭제의 범위 (2-2)

`memory.delete(target_id)` 후 `get_all`에서 사라졌다. 맞는 설명은?

① 이력·백업까지 모두 사라졌다  
② 다음 실행에서 다시 나타난다  
③ 활성 목록에서는 빠졌지만 SQLite 이력·로그·캐시·백업에는 남을 수 있다  
④ 다른 사용자의 기억도 함께 지워졌다

<details>
<summary>정답 보기</summary>

**③** — "완전히 삭제됐다"고 안내하려면 이력·백업·이미 꺼낸 컨텍스트까지 처리해야 해요.

</details>

### CE2-Q5. 서술형 — `len(new_ids) != 1`이면 멈추는 이유 (2-2)

add 응답에서 ADD ID가 0개이거나 2개 이상일 때 그냥 `new_ids[0]`을 쓰면 어떤 문제가 생기는지, 왜 멈추는 게 맞는지 쓰세요.

<details>
<summary>예시 답안</summary>

0개면 저장이 안 된 건데 `[0]`에서 `IndexError`가 나거나, 이후 코드가 없는 기억을 다룬다고 착각해요. 2개 이상이면 `infer=True` 등으로 문장이 여러 기억으로 쪼개진 것이라 `[0]`이 사용자가 의도한 기억이 아닐 수 있고, 그 ID로 수정·삭제하면 엉뚱한 기억을 바꾸게 돼요. 대상이 애매할 때 추측해서 진행하면 조용한 데이터 손상이 생기니, RAG 6장 `validate_answer`처럼 예상과 다르면 바로 멈추고 원인을 확인하는 게 안전해요.

</details>

### CE2-Q6. 서술형 — `user_id`와 `memory_id`, 그리고 uuid (2-2)

두 ID의 차이를 쓰고, uuid로 만든 ID가 추측하기 어렵다고 `owned_record` 확인을 생략하면 안 되는 이유를 쓰세요.

<details>
<summary>예시 답안</summary>

`user_id`는 누구의 기억인지(범위·소유자)를, `memory_id`는 그중 어떤 기억 하나인지를 가리켜요. user\_id는 앱이 만들고 memory\_id는 Mem0가 add 때 `uuid4()`로 붙여요. uuid는 암호화가 아니라 겹치지 않는 무작위 이름표라서, 로그·화면·이전 실행 등으로 다른 사람의 ID가 노출되면 그대로 쓸 수 있어요. 그래서 ID를 받았다는 사실만 믿지 말고 `memory.get`으로 꺼낸 기억의 user\_id가 현재 사용자와 같은지 확인한 뒤에만 수정·삭제해야 해요.

</details>
