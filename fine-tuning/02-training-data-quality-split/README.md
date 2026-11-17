# 2장. 학습 데이터 구성과 품질 검증

> 2026-11-17 학습 기록. 파인튜닝 2일차 수업이에요. 1장이 "학습 전 모델이 무엇을 틀리는지 기준 남기기"였다면, 2장은 **그 목표 행동(근거 읽기 · JSON · 보류 · 인용)을 학습 대화 72개로 만들고, 검사하고, 그룹째로 나누기**예요. 이번에도 학습은 하지 않아요. 모델 가중치는 불러오지 않고 **토크나이저만** 써서 CPU로 끝까지 돌아요. 결과물 `training_data.zip` 하나를 3\~8장이 그대로 읽어요.
>
> 2장의 한 문장: **모범답안은 규칙이 만들고, 자료와 검사 함수를 함께 시험하고, 행이 아니라 그룹으로 나눈다.**

## 큰 흐름

```text
2-1 모범답안   규정 그룹 12 × 사례 6 = 72개, reference_answer(규칙 함수)로 정답 생성 — 모델 출력 복사 X
2-2 대화 · 토큰 레코드 = 메타데이터(id · group_id · case_type) + messages(system · user · assistant)
               두 번 토큰화: prompt 299 / full 376 → 접두부 assert → 답변 77개, 길이 257~380 ≤ 512
2-3 품질 검사   validate_record 5단계(식별 → 대화 → 형식 → 인용 → 업무 규칙) 72/72
               일부러 틀린 복사본 2개 → 2/2 탐지 (검사 함수의 테스트)
2-4 그룹 분할   그룹 목록 정렬 → seed 42로 섞기 → 8 / 2 / 2 그룹 = 48 / 12 / 12행, 겹침 0
               JSONL + dataset_info.json → training_data.zip → 다시 읽어 비교 · SHA-256
      ↓
3장 encode_example: 이 경계로 labels = −100 마스킹 → 전체 가중치 SFT → 학습 전후 비교
```

**1 · 2장은 학습하지 않는 준비 단계**

| 장 | 모델을 어떻게 쓰나 | Qwen 가중치 W | 남기는 것 |
|---|---|---|---|
| 1장 | 불러와서 **추론만** (`generate`) | 읽기만, 안 바뀜 | `baseline.json` (학습 전 기준) |
| 2장 | **토크나이저만**, 가중치 파일은 안 불러옴 | 안 씀 | `training_data.zip` (학습시킬 정답) |
| 3장\~ | 2장 ZIP으로 실제 학습 | 바뀜 (4 · 5장은 W 고정 + A · B만) | 학습 전후 비교 |

## 학습 목표
- 모범답안을 모델 출력이 아니라 **규칙 함수**로 만들어 72개를 일관되게 유지한다.
- 메타데이터(분리 · 분석용)와 messages(모델 입력)를 나누고, 학습과 생성에서 넣는 messages를 구분한다.
- 정답 없는 대화와 정답 있는 대화를 각각 토큰화해 **답변 시작 위치**를 찾고, 길이 상한을 토큰으로 확인한다.
- 자료를 검사하고, **검사 함수도 틀린 예로 시험**한다.
- 같은 문제의 변형이 train과 test에 흩어지지 않게 **그룹 단위로** 나누고, 데이터에 지문(해시)을 남긴다.

## 실습 환경
- 노트북: `data_preparation.ipynb` (21셀, 1장 파일이나 변수 없이 독립 실행)
- Colab CPU, `%pip install "transformers==5.22.2"` → 런타임 재시작 → 위에서부터
- 모델 · 템플릿 버전은 1장과 같게 고정: `Qwen/Qwen2.5-0.5B-Instruct`, revision `7ae5576…`
- `MAX_LENGTH = 512`(입력 + 모범답안 **토큰** 상한), `SEED = 42`
- 1일차에 만든 로컬 환경(`uv` · transformers 5.22.2 · Qwen 캐시)으로도 그대로 돌아감. 새로 받을 것 없음
- 결과물 `training_data.zip`은 Colab 왼쪽 파일 목록에서 내려받아 보관 (3\~8장 노트북에 업로드)

## 실습 파일

| 파일 | 하는 일 | 상태 |
|---|---|---|
| `data_preparation.ipynb` | 2-1 모범답안 72개 → 2-2 토큰 경계 · 길이 → 2-3 검사 · 의도한 오류 → 2-4 그룹 분할 · ZIP | ✅ Colab CPU 실행 · 로컬 재실행(JSONL 해시 일치) |
| `training_data.zip` | `train` / `dev` / `test.jsonl` + `dataset_info.json` | ✅ 로컬에 보관 (3장 폴더에 복사해 둠) |

---

## 핵심 이론

### 2-1. 근거를 모범답안으로 바꾸기 — 규칙 함수가 정답을 만든다

**규정 그룹 12개 × 사례 6종 = 72개.** 그룹 하나 = 한 팀의 규정 계열(구판 v1 + 개정판 v2). 한도 65,000\~120,000원, 개정 한도는 +10,000원.

```python
groups = [
    {"group_id": f"policy{i:02d}", "team": team, "limit": limit, "updated_limit": limit + 10000}
    for i, (team, limit) in enumerate(zip(teams, limits), start=1)
]

for group in groups:
    old_document = make_document(group)                 # {group_id}-v1
    new_document = make_document(group, updated=True)   # {group_id}-v2
    for kind, amount, document in [
        ("below",      group["limit"] - 5000, old_document),
        ("boundary",   group["limit"],        old_document),
        ("over_limit", group["limit"] + 5000, old_document),
        ("updated",    group["limit"] + 5000, new_document),   # over_limit과 같은 질문
        ("missing",    None,                  None),
        ("irrelevant", None,                  old_document),   # missing과 같은 질문
    ]:
        ...
```

| case\_type | 질문 금액 (policy03 · 다온 · 한도 85,000) | 넣는 문서 | 모범답안 |
|---|---|---|---|
| below | 80,000원 (한도 −5,000) | v1 | answered · 한도 이하 → 승인 불필요 |
| boundary | 85,000원 (= 한도) | v1 | answered · 한도와 같음 → 승인 불필요 |
| over\_limit | 90,000원 (한도 +5,000) | v1 | answered · 초과 → 예약 전 서면 승인 |
| updated | 90,000원 (같은 질문) | v2 (95,000) | answered · 개정 한도 이하 → 불필요 |
| missing | 통신비 질문 | 없음 | abstained · 확인 불가 + 담당자 |
| irrelevant | 통신비 질문 (같은 질문) | v1 숙박 규정 | abstained · 숙박 규정으로 판단 금지 |

- 1장의 네 문항에 **below**(한도 −5,000)와 **irrelevant**(무관한 문서)가 추가됐어요. "문서가 있다 = 답할 수 있다"가 아니라는 걸 가르치는 사례.
- 같은 그룹 안에 **질문 문장이 똑같은 쌍이 두 개**(초과 ↔ 개정, 없음 ↔ 무관) → 2-4에서 그룹째로 나눠야 하는 이유.
- 실무: 모으기 전에 **경우의 수 표(커버리지 표)**부터 설계해요.

**`reference_answer` — 정답은 규칙이 만든다.**

```python
def reference_answer(spec):
    if spec["case_type"] in {"missing", "irrelevant"}:          # 근거 부족 → 보류
        return {"status": "abstained",
                "answer": "제공된 근거로는 출장 중 통신비 지원 한도를 확인할 수 없습니다. 담당자에게 확인하세요.",
                "citations": []}
    amount, limit = spec["amount"], spec["limit"]
    if amount > limit:                                          # 초과
        answer = (f"숙박비 지원 한도는 1박 {limit:,}원입니다. "
                  f"질문의 1박 {amount:,}원은 한도를 초과하므로 예약 전 서면 승인을 받아야 합니다.")
    else:                                                       # 같음 / 이하
        relation = "한도와 같으므로" if amount == limit else "한도 이하이므로"
        answer = (f"숙박비 지원 한도는 1박 {limit:,}원입니다. "
                  f"질문의 1박 {amount:,}원은 {relation} 사전 승인이 필요하지 않습니다.")
    return {"status": "answered", "answer": answer, "citations": [spec["documents"][0]["id"]]}
```

```text
policy03-over_limit 다온팀 출장에서 1박 90,000원인 방을 예약하려면 무엇을 해야 하나요?
{"status": "answered", "answer": "숙박비 지원 한도는 1박 85,000원입니다. 질문의 1박 90,000원은 한도를 초과하므로 예약 전 서면 승인을 받아야 합니다.", "citations": ["policy03-v1"]}
policy03-updated 다온팀 출장에서 1박 90,000원인 방을 예약하려면 무엇을 해야 하나요?
{"status": "answered", "answer": "숙박비 지원 한도는 1박 95,000원입니다. 질문의 1박 90,000원은 한도 이하이므로 사전 승인이 필요하지 않습니다.", "citations": ["policy03-v2"]}
```

- **모델 출력을 정답으로 복사하지 않아요.** 틀린 답을 학습시키는 사고를 막아요.
- 문장 틀이 하나뿐이라 모델은 이 문장을 **그대로 외워요.** 3장 이후 답이 이 문장으로 나오는 이유이고, 다양성은 낮아요.
- 실무: 실제 업무 정답은 규칙 함수로 다 만들 수 없어요 → 라벨링 가이드 + 사람 검수. LLM으로 초안을 만들면 금액 · 조건이 바뀌지 않았는지 코드로 걸러요.

### 2-2. 대화 형식과 정답 토큰 — 답변이 어디서 시작하나

**레코드 한 줄: 바깥은 분리용, 안쪽 messages만 모델이 봐요.**

```python
rows.append({
    "id": spec["id"],                 # ┐
    "group_id": spec["group_id"],     # ├ 분리 · 분석용 메타데이터 → 모델 입력에 안 넣음
    "case_type": spec["case_type"],   # ┘
    "messages": [
        {"role": "system", "content": SYSTEM_PROMPT},     # 1장 explicit 지시와 같은 문자열
        {"role": "user", "content": json.dumps(model_input, ensure_ascii=False)},          # 질문 + 문서
        {"role": "assistant", "content": json.dumps(reference_answer(spec), ensure_ascii=False)},  # 학습 때만
    ],
})
```

| 언제 | 넣는 messages | 이유 |
|---|---|---|
| 학습 (3\~6장) | system + user + assistant | assistant(모범답안) 토큰에서 손실 계산 |
| 생성 · 평가 (1 · 3 · 7장) | system + user | 정답을 넣으면 평가가 무의미 |

- `case_type="over_limit"`을 입력에 넣으면 "초과니까 승인"이라는 정답을 알려 주는 셈(**정답 누수**).
- 이 messages 형식은 OpenAI Chat · HF 채팅 템플릿 · TRL SFTTrainer가 그대로 받는 사실상 표준이에요.

**두 번 토큰화해서 답변 시작 위치 찾기**

```python
prompt_ids = tokenizer.apply_chat_template(
    sample["messages"][:2],           # system + user만
    tokenize=True, return_dict=False,
    add_generation_prompt=True,       # 끝에 <|im_start|>assistant\n
)
full_ids = tokenizer.apply_chat_template(
    sample["messages"],               # + assistant(모범답안)
    tokenize=True, return_dict=False,
    add_generation_prompt=False,      # 정답이 이미 있으니 안 붙임
)
assert full_ids[: len(prompt_ids)] == prompt_ids, "정답 앞의 토큰이 생성 입력과 다릅니다."
answer_ids = full_ids[len(prompt_ids):]
```

```text
입력 토큰: 299 전체 토큰: 376
답변과 종료 부분 토큰: 77
답변 부분 끝: '-v1"]}<|im_end|>\n'
답변 종료 토큰 ID: 151645
```

경계 근처 토큰을 하나씩 꺼내 보면 (policy03-over\_limit):

```text
prompt_ids (299개)  ... '\n', '<|im_start|>', 'assistant', '\n'                       ← 여기서 끝
full_ids   (376개)  ... '\n', '<|im_start|>', 'assistant', '\n', '{"', 'status', '":', ' "', 'answered', ...
                                                              ↑ 인덱스 299 = 정답 첫 토큰
full_ids 끝         ... '1', '"]}', '<|im_end|>', '\n'

full_ids = [ 질문 부분 299개 (= prompt_ids)  |  답변 77개 = 모범답안 75 + <|im_end|> + 줄바꿈 ]
           0                               299                                          376
```

- 학습 대화는 추론 입력을 **앞부분에 그대로 품고** 있어요(1장 직접 구현 ②의 "▼ 답변 시작 위치 ▼"를 진짜 토크나이저로).
- **assert가 필수인 이유**: 템플릿에 따라 정답 앞에 다른 토큰(생각 토큰, 기본 system 등)이 끼면 경계가 한 칸 밀려서 질문 토큰을 정답으로 배우거나 정답 첫 토큰을 놓쳐요. 에러 없이 조용히 틀려요.
- **글자 수로 경계를 찾으면 안 돼요.** 토큰 경계는 글자 경계와 달라요. 토큰 ID 리스트 길이로만 계산해요.
- labels 마스킹은 3장에서: `labels = [-100] * 299 + full_ids[299:]`(질문 위치는 손실 제외, 모델은 읽기는 함). 3장은 마지막 줄바꿈 하나를 정답에서 빼요.

**템플릿 함정**

| 함정 | 증상 | 막는 법 |
|---|---|---|
| system 누락 | 기본 system("You are Qwen, created by Alibaba Cloud…")이 몰래 들어가 학습 · 추론 입력이 달라짐 | system을 항상 명시 (`SYSTEM_PROMPT`) |
| 템플릿 차이 | 정답 앞에 다른 토큰이 붙어 경계가 밀림 | `full_ids[:len(prompt_ids)] == prompt_ids` assert |
| 문자 길이로 경계 | 토큰 경계와 어긋남 | 토큰 ID 리스트 길이로만 계산 |
| 모델 교체 | Llama · Gemma는 다른 제어 토큰 | 토크나이저의 템플릿을 그대로 사용 |

**MAX\_LENGTH 512 — 글자가 아니라 토큰 수, 넘으면 멈춰요.**

```python
lengths = {row["id"]: len(tokenizer.apply_chat_template(row["messages"], tokenize=True,
                                                        return_dict=False, add_generation_prompt=False))
           for row in rows}
too_long = [rid for rid, n in lengths.items() if n > MAX_LENGTH]
assert not too_long, f"길이 상한을 넘는 사례를 먼저 검토하세요: {too_long}"
```

```text
전체 대화 토큰 범위: 257 ~ 380
길이 상한: 512 초과: 0
모델 가중치는 불러오지 않았습니다.
```

| 구간 | 토큰 |
|---|---|
| 프롬프트 | 205 \~ 302 |
| 모범답안 + 종료 | 52(보류) \~ 79(초과) |
| 합계 | 257(missing, 문서 없음) \~ 380 |

- **자르지 않는 이유**: 오른쪽을 자르면 정답 끝과 `<|im_end|>`가 사라져 **끝내는 법**을 못 배워요. 왼쪽을 자르면 **근거 문서**가 사라져요. 둘 다 에러 없이 조용히 틀려요.
- 긴 문서는 학습 데이터에서 자르기보다 RAG 단계에서 필요한 부분만 넣도록 줄여요.
- 실무: max\_length는 실제 길이 분포(최대 · 상위 1%) + 여유로. 배치는 가장 긴 것에 맞춰 패딩돼요.

### 2-3. 조건과 근거 부족의 품질 확인 — 자료와 검사 함수를 함께 시험

**`validate_record` 다섯 단계**

```python
def validate_record(row):
    # ① 식별 정보: 필드 4개, group_id · case_type이 원래 명세와 같은가
    assert set(row) == {"id", "group_id", "case_type", "messages"}
    spec = specs_by_id[row["id"]]
    assert row["group_id"] == spec["group_id"] and row["case_type"] == spec["case_type"]
    # ② 대화: 역할 순서 system · user · assistant, system == SYSTEM_PROMPT, user == 명세
    check_message_fields(row["messages"])
    user = json.loads(row["messages"][1]["content"])
    assert user == {"question": spec["question"], "documents": spec["documents"]}
    # ③ 응답 형식: status · answer · citations
    response = json.loads(row["messages"][2]["content"])
    check_response_fields(response)
    # ④ 인용: 문자열 목록, 제공 문서 ID 안, 중복 없음
    citations = response["citations"]
    source_ids = {doc["id"] for doc in user["documents"]}
    assert set(citations) <= source_ids and len(citations) == len(set(citations))
    # ⑤ 업무 규칙(shortcut): 정해 둔 문장 틀의 핵심 구절만 확인
    check_reference_rule(spec, response, citations)
```

| ⑤ 업무 규칙 | 있어야 하는 것 | 있으면 안 되는 것 |
|---|---|---|
| 근거 부족 | abstained · 빈 인용 · "확인할 수 없습니다" · "담당자" | — |
| 답할 수 있음 | answered · 인용 1개 · 1박 한도와 질문 금액 둘 다 | — |
| 초과 | "초과" · "예약 전 서면 승인을 받아야" | "사전 승인이 필요하지" |
| 이하 · 같음 | "사전 승인이 필요하지 않습니다" | "예약 전 서면 승인을 받아야" |

```text
형식과 교재 규칙 검사: 72 / 72 통과
응답 상태: {'answered': 48, 'abstained': 24}
```

- ⑤는 이 교재의 정형 문구만 보는 **shortcut**이에요. 표현이 다른 올바른 답이나 실제 규정에는 사람 검토가 따로 필요해요.
- 실무: 학습 데이터 검사 네 가지 — **스키마 · 중복 · 누수 · 라벨 규칙**.

**검사 함수도 시험해요 — 일부러 틀린 복사본 두 개**

```python
bad_citation = copy.deepcopy(sample)                      # 원본은 그대로 두고 복사본만 망가뜨림
response = json.loads(bad_citation["messages"][2]["content"])
response["citations"] = ["없는-문서"]                      # → ④ 인용에서 거절
...
bad_boundary = copy.deepcopy(next(r for r in rows if r["id"] == "policy03-boundary"))
response["answer"] = "1박 85,000원은 한도를 초과하므로 예약 전 서면 승인을 받아야 합니다."  # → ⑤에서 거절
...
rejected = 0
for bad in [bad_citation, bad_boundary]:
    try:
        validate_record(bad)
    except AssertionError:
        rejected += 1
assert rejected == 2
```

```text
의도한 오류 탐지: 2 / 2
원본 자료: 72 개 유지
```

- 검사 함수가 **"항상 통과"하는 버그가 가장 위험해요.** 맞는 예는 통과하고, 틀린 예는 실패하는지가 검사 함수의 테스트예요(LLMOps 4장 "막는 코드 vs 막았다고 말하는 코드"와 같은 생각).
- `copy.deepcopy`: messages 안의 dict까지 통째로 복사. 그냥 대입이나 얕은 복사면 원본 72개가 같이 망가져요(1장 `.clone()`과 같은 이유).

### 2-4. 그룹 단위로 나누기 — 행이 아니라 "같은 문제" 단위로

**행을 섞어 자르면**: 72행을 seed 42로 행 단위로 섞으면 test 12행 중 **12행 모두**가 같은 그룹 형제를 train에 두고, **5행은 질문 문장까지** train과 같아요. 시험 문제를 이미 본 셈 → 점수가 부풀어요(**데이터 누수**).

```python
group_ids = sorted({row["group_id"] for row in rows})   # set 순서는 실행마다 다를 수 있어 먼저 정렬
random.Random(SEED).shuffle(group_ids)                 # 전역 random을 건드리지 않는 독립 생성기
split_groups = {
    "train": set(group_ids[:8]),
    "dev":   set(group_ids[8:10]),
    "test":  set(group_ids[10:]),
}
splits = {name: [row for row in rows if row["group_id"] in selected]
          for name, selected in split_groups.items()}
check_split_overlap(split_groups, splits, groups)     # 그룹 · user 입력 겹침 0, 빠짐 0, 48/12/12
```

```text
train 행: 48 그룹: ['policy03', 'policy04', 'policy06', 'policy07', 'policy08', 'policy09', 'policy10', 'policy12']
dev 행: 12 그룹: ['policy01', 'policy05']
test 행: 12 그룹: ['policy02', 'policy11']
유형: 세 집합 모두 여섯 사례가 같은 비율 (그룹마다 6종이 함께 움직이니까)
뒤 장의 공통 dev 문항: policy01-over_limit
```

| | train | dev | test |
|---|---|---|---|
| 크기 | 48행 · 8그룹 | 12행 · 2그룹 | 12행 · 2그룹 |
| 언제 | 가중치 갱신 (3 SFT · 4 LoRA · 5 QLoRA · 6 DPO) | 학습 중 점검 · 후보 비교 (여러 번) | 후보 · 설정을 다 고정한 뒤 **한 번** |
| 주의 | 여기 점수가 좋은 건 당연 | 여러 번 보고 고르면 낙관적으로 부풂 | 보고 고치면 dev가 됨 |

- dev 12행이면 **1문항 = 8.3%p**. 숫자 하나로 결론 내지 말고 원문을 읽어요.
- 그룹으로 나눠도 문장 틀이 같아 비슷함은 남아요. 이 점수는 "같은 틀의 새 그룹"이지 실제 업무 일반화가 아니에요.
- 실무: 같은 문서 · 고객 · 세션 · 날짜 단위로 나눠요(GroupKFold). 시간이 흐르는 데이터는 과거로 학습, 최근으로 평가.

**JSONL · dataset\_info · ZIP · SHA-256으로 보관**

```python
for name, part in splits.items():
    path = output_dir / f"{name}.jsonl"
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in part), encoding="utf-8")
    file_hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
...
with zipfile.ZipFile(archive_path) as archive:          # 저장 직후 다시 읽어 원본과 비교
    for name in splits:
        restored = [json.loads(line) for line in archive.read(f"{name}.jsonl").decode("utf-8").splitlines()]
        assert restored == splits[name]
```

| 파일 | 내용 | SHA-256 앞자리 (로컬 실행 = 슬라이드) |
|---|---|---|
| `train.jsonl` | 48줄 | `d9154d79…` |
| `dev.jsonl` | 12줄 | `e48906f0…` |
| `test.jsonl` | 12줄 | `2bca42ac…` |
| `dataset_info.json` | 데이터 카드 | — |
| `training_data.zip` | 위 넷 | 실행마다 다름 (압축 시 파일 시각이 들어감) |

| `dataset_info` 필드 | 왜 |
|---|---|
| `synthetic` · `limitations` | 무엇이고 한계는 |
| `model_id` · `revision` · `system_prompt` | 같은 템플릿 · 지시 |
| `split_seed` · `split_groups` | 분할 재현 |
| `max_length` · `max_observed_tokens` | 512 · 380 |
| `dev_probe_id` | 3\~7장이 같이 지켜볼 `policy01-over_limit` |
| `file_sha256` | 무결성 — 3장이 `data_sha256`으로 기록, 4\~7장이 같은 데이터인지 대조 |

- **JSONL** = 한 줄에 레코드 하나 → 줄 수 = 레코드 수, 한 줄씩 읽고 쓰기 쉬움.
- **SHA-256** = 파일 지문. 데이터에도 버전이 있어요. 실험 기록에 모델 버전과 데이터 해시를 함께 남겨요(HF dataset card와 같은 역할).
- 저장 직후 ZIP을 다시 읽어 비교해야 한글 인코딩 · 빠진 줄을 여기서 잡아요. 압축하면 train 66,681 → 2,196 B(템플릿 반복이 많아서).
- Colab: 노트북 저장 ≠ 런타임 파일 저장 → **`training_data.zip`은 따로 내려받아 3\~8장 노트북에 업로드.**

---

## 실행 결과 (내 실행 — Colab CPU, 슬라이드와 같음)

| 단계 | 결과 |
|---|---|
| 환경 | Python 3.13.18 · torch 2.14.1+cpu · transformers **5.22.1** (아래 참고) |
| 2-1 | 규정 그룹 12 · 사례 72 · 유형별 12개씩 |
| 2-2 | 입력 299 · 전체 376 · 답변 77 · 종료 ID 151645 · 길이 257\~380 · 초과 0 |
| 2-3 | 72/72 통과 · answered 48 / abstained 24 · 의도한 오류 2/2 탐지 |
| 2-4 | train 48 (policy03·04·06·07·08·09·10·12) · dev 12 (01·05) · test 12 (02·11) · dev 문항 `policy01-over_limit` · `/content/training_data.zip` 저장 |

- 로컬(Python 3.12 · transformers 5.22.2)에서도 같은 노트북을 돌려 숫자가 모두 같았고, JSONL 해시도 슬라이드와 일치했어요(ZIP 해시는 압축할 때 파일 시각이 들어가서 실행마다 달라요).
- **transformers가 5.22.1로 찍혔어요.** 1장 때처럼 `%pip install` 뒤 런타임을 재시작하지 않아서, 이미 불러온 Colab 기본 버전이 그대로 쓰인 거예요. 2장은 토크나이저만 쓰고 결과(299 · 376 · 257\~380)가 5.22.2와 같아서 이번엔 문제가 없었지만, 3장부터는 학습 코드가 버전에 더 민감하니 **설치 → 런타임 재시작 → 환경 확인 셀에서 5.22.2 확인** 순서를 지키기.

## 질문과 새로 알게 된 점

### 두 번 토큰화해서 답변 시작 위치 찾기
- 3장 SFT는 **모범답안 토큰에만** 손실을 계산해요. 그러려면 376개 중 어디까지가 질문이고 어디부터가 답인지 **토큰 번호로** 알아야 해요.
- 정답을 빼고 한 번(`[:2]` + `True` = 299), 넣고 한 번(전체 + `False` = 376) 토큰화하면 `full_ids` 앞 299개가 `prompt_ids`와 똑같아요. 그래서 **인덱스 299부터가 정답**이에요.
- 3장에서는 `input_ids = full_ids`(376개 전부 읽음), `labels = [-100] * 299 + full_ids[299:]`(질문 위치는 채점 안 함).

### assistant와 `add_generation_prompt`
- **assistant = 대화에서 모델 쪽 역할의 이름표.** system은 개발자가 정한 규칙, user는 사용자, assistant는 모델의 답. 모델은 "assistant 자리에 오는 글 = 내가 써야 하는 글"이라고 배웠어요.
- **`add_generation_prompt` = 끝에 `<|im_start|>assistant\n`("이제 네 차례")을 붙일지 정하는 스위치.**
- 대본에 비유하면 assistant는 "AI:"라는 배역 이름. True는 대본 끝에 "AI:"까지만 써 두고 대사는 비워 두는 것, 학습용 대본은 대사까지 다 있으니 "AI:"를 또 붙이지 않아요.

```text
True (생성 · 평가: 1장, 7장)          False (학습: 2~3장)              잘못: 정답 있는데 True
<|im_start|>user                     <|im_start|>user                 <|im_start|>user
안녕<|im_end|>                        안녕<|im_end|>                    안녕<|im_end|>
<|im_start|>assistant                <|im_start|>assistant            <|im_start|>assistant
   ← 비어 있음, 모델이 이어 씀         안녕하세요!<|im_end|>              안녕하세요!<|im_end|>
                                        ← 그대로 끝                     <|im_start|>assistant  ← 쓸데없이 또
```

(실제 Qwen은 system이 없으면 맨 앞에 기본 system을 자동으로 붙여요. 그래서 2장은 `SYSTEM_PROMPT`를 항상 명시해요.)

### 1 · 2장은 학습을 안 하는데 W · A · B 어디에 영향이 가나
**어디에도 안 가요.**

| | W (Qwen 원래 가중치) | A · B (LoRA 어댑터) |
|---|---|---|
| 토크나이저만 (2장) | 안 씀. `model.safetensors`를 불러오지도 않음 | 없음 |
| 추론 (1장 `generate`) | **읽기만** (곱셈에 사용) | 없음 |
| 학습 (3장 전체 SFT) | **바뀜** | 없음 |
| LoRA 학습 (4 · 5장) | 읽기만 (고정) | **새로 붙이고 이것만 바뀜** |

- 토크나이저는 모델 **밖의 번역기**예요. 글자 ↔ 숫자 ID 규칙표(`vocab.json`, `merges.txt`)만 쓰고, W가 있는 파일과는 별개예요.
- 추론은 `inference_mode()`로 기울기 기록을 끄고, `optimizer.step()`이 없어요. W를 바꾸는 건 오직 `step()`. 계산기로 계산해도 회로가 바뀌지 않는 것과 같아서, 1장을 몇 번 돌려도 같은 응답이 나와요(greedy).
- A · B는 4장에서 처음 생겨요: `출력 = W·x` → `출력 = W·x + B·A·x`. 지금 Qwen엔 없어요.
- 1장 `optimizer.step()`은 Qwen이 아니라 숫자 3개짜리 원리 예제, 직접 구현 `train_step`은 9×9 작은 행렬이었어요.

### 그럼 아무것도 파인튜닝 안 되는데 왜 하나
**파인튜닝이 성공했는지 판단할 수 있게 만드는 단계**예요. 요리로 치면 1장은 "지금 맛보기", 2장은 "레시피와 재료 준비", 불(학습)은 3장에서 켜요.
- **1장이 없으면 좋아졌는지 말할 수 없어요.** 3장 결과가 학습 덕분인지는 학습 전 답(펜스 · "승인 필요" 오답 · 50만원 환각 · 형식 0/4)을 같은 조건으로 남겨 놨어야 알아요.
- **2장이 없으면 틀린 걸 배워요.** 파인튜닝은 보여 준 정답을 따라 하도록 배우니 데이터가 곧 결과예요.

| 2장에서 하는 일 | 안 하면 |
|---|---|
| 규칙 모범답안 + 72/72 검사 | 85,000원에 "초과"라고 쓴 답이 섞이면 그 오답을 학습 |
| 답변 경계 299 | 질문 토큰을 정답으로 배우거나 정답 첫 토큰을 놓침 |
| 길이 512 확인 (자르지 않음) | `<|im_end|>`가 잘려 답을 끝내는 법을 못 배움 |
| 그룹 단위 분할 | 시험 문제를 미리 본 셈, 점수가 부풀어 "잘 됐다"고 착각 |

- 이 실수들은 **에러가 안 나요.** 학습은 잘 돌고 손실도 내려가는데 결과만 조용히 틀려요(1장 직접 구현의 "손실 0.37인데 이하 → 승인 필요"처럼).
- 실무에서도 GPU 학습은 코드 몇 줄이고, 시간 대부분은 **무엇을 가르칠지 정하고 좋은 데이터로 공정하게 잴 수 있게 준비하는 일**에 써요.

## 실습 코드에서 직접 바꾼 점
- `check_split_overlap`의 첫 assert 옆에 주석 추가: `#각 train, dev, test 겹치는 그룹 id가 있는지 확인.`
  - `("train", "dev")`, `("train", "test")`, `("dev", "test")` 세 쌍마다 `isdisjoint`(공통 원소가 하나도 없으면 True)로 **그룹 ID**가 겹치지 않는지 보고, 이어서 user 입력 문자열도 겹치지 않는지 한 번 더 봐요.
  - 마지막 두 assert는 그룹이 빠지거나 추가되지 않았는지(`set.union(...) == 전체 12그룹`), 행 수가 48/12/12인지 확인.
- 나머지 셀은 원본 그대로 실행.

## PPT 정리
- 2장 결과물: **검사를 통과한 72개를 그룹째로 나눈 ZIP**
  - 2-1 모범답안은 규칙 함수가 만든다 → 72개 = 12그룹 × 6사례
  - 2-2 두 번 토큰화해 답변 경계를 찾고 길이를 확인한다 → 경계 299 · 257\~380 ≤ 512
  - 2-3 자료와 검사 함수를 함께 시험한다 → 72/72 통과 · 오류 2/2 탐지
  - 2-4 행이 아니라 그룹으로 나누고 지문을 남긴다 → 48/12/12 · `training_data.zip`
- 학습도, 성능 측정도 하지 않았어요. 이 ZIP이 3\~8장의 공통 입력.
- 다음 3장: 이 경계로 `encode_example`에서 **labels = −100 마스킹** → **전체 가중치 SFT** → 학습 전후 비교
- 3장 전에 직접 해 볼 것: `training_data.zip` 내려받기(3\~8장 노트북에 업로드), `dataset_info.json` 읽어 보기(분할 seed · 그룹 · 파일 해시)

---

## 확인 문제

> 객관식 6 · 단답형 6, 섞어서 배치했어요. **정답 보기**를 누르면 열려요.

### FT2-Q1. 객관식 — 모범답안 만들기
2장에서 72개 모범답안을 만드는 방법으로 맞는 것은?

1. 1장 모델이 생성한 답을 복사한다
2. 사람이 72개를 하나씩 손으로 쓴다
3. 금액과 한도를 비교하는 규칙 함수 `reference_answer`로 만든다
4. 더 큰 LLM에게 답을 쓰게 해서 그대로 쓴다

<details>
<summary>정답 보기</summary>
<p><b>3.</b> 모델 출력을 정답으로 복사하면 틀린 답을 학습시켜요. 규칙 함수라 72개가 일관되지만 문장 틀이 하나뿐이라 모델이 그 문장을 그대로 외우게 돼요. 실무에선 라벨링 가이드 + 사람 검수, LLM 초안은 코드로 금액 · 조건을 검사해요.</p>
</details>

### FT2-Q2. 단답형 — 새로 생긴 사례
1장 네 문항에 없던 `irrelevant`(숙박 규정만 주고 통신비 질문)를 넣은 이유는?

<details>
<summary>정답 보기</summary>
<p>"문서가 있다 = 답할 수 있다"가 아니라는 걸 가르치려고요. 무관한 문서만 있으면 그걸로 판단하지 말고 <b>abstained + 빈 인용 + 담당자 안내</b>를 해야 해요. missing과 질문 문장이 같고 문서만 달라요.</p>
</details>

### FT2-Q3. 객관식 — 메타데이터
레코드의 `case_type`을 모델 입력(user 메시지)에 넣으면 생기는 문제는?

1. 토큰이 512를 넘는다
2. "초과니까 승인"이라는 정답을 미리 알려 주는 셈이다 (정답 누수)
3. 채팅 템플릿이 깨진다
4. 그룹 분할이 안 된다

<details>
<summary>정답 보기</summary>
<p><b>2.</b> <code>id</code> · <code>group_id</code> · <code>case_type</code>은 분리 · 분석용 메타데이터라 모델에 안 넣어요. 모델은 messages만 봐요.</p>
</details>

### FT2-Q4. 단답형 — 답변 경계
`prompt_ids`가 299개, `full_ids`가 376개이고 `full_ids[:299] == prompt_ids`예요. 정답은 어디부터이고, `answer_ids` 77개는 무엇으로 이뤄져 있나요?

<details>
<summary>정답 보기</summary>
<p><b>인덱스 299부터</b>(<code>full_ids[299:]</code>). 77개 = 모범답안 75 + <code>&lt;|im_end|&gt;</code> + 줄바꿈. 3장은 마지막 줄바꿈 하나를 정답에서 빼요.</p>
</details>

### FT2-Q5. 객관식 — assert
`assert full_ids[:len(prompt_ids)] == prompt_ids`를 하는 이유로 가장 알맞은 것은?

1. 길이 차이로 경계를 나누려면 앞부분이 토큰 하나까지 같아야 해서
2. 512 토큰 상한을 확인하려고
3. 모델 가중치가 바뀌지 않았는지 보려고
4. JSON 형식을 검사하려고

<details>
<summary>정답 보기</summary>
<p><b>1.</b> 템플릿이 정답 앞에 다른 토큰을 끼우면 경계가 한 칸 밀려 질문 토큰을 정답으로 배우거나 정답 첫 토큰을 놓쳐요. 에러 없이 조용히 틀리니 assert로 먼저 막아요.</p>
</details>

### FT2-Q6. 단답형 — True / False
정답(assistant)이 이미 들어 있는 학습 대화를 `add_generation_prompt=True`로 토큰화하면 어떻게 되나요?

<details>
<summary>정답 보기</summary>
<p>답 뒤에 <code>&lt;|im_start|&gt;assistant\n</code>이 하나 더 붙어서 "답을 다 쓰고 또 답을 시작하라"는 이상한 대화가 돼요. 생성 · 평가 입력(질문만)은 <b>True</b>, 학습 대화(정답 포함)는 <b>False</b>.</p>
</details>

### FT2-Q7. 객관식 — 길이 초과
대화가 512 토큰을 넘을 때 2장의 처리로 맞는 것은?

1. 오른쪽(끝)을 잘라 512에 맞춘다
2. 왼쪽(앞)을 잘라 512에 맞춘다
3. `MAX_LENGTH`를 넘는 만큼 자동으로 늘린다
4. 자르지 않고 assert로 멈춰 원문을 검토한다

<details>
<summary>정답 보기</summary>
<p><b>4.</b> 오른쪽을 자르면 <code>&lt;|im_end|&gt;</code>가 사라져 끝내는 법을 못 배우고, 왼쪽을 자르면 근거 문서가 사라져요. 둘 다 조용히 틀려요. 실제 길이는 257~380이라 초과 0.</p>
</details>

### FT2-Q8. 단답형 — 검사 함수의 테스트
원본 72개가 다 통과했는데도 `bad_citation`, `bad_boundary` 복사본을 일부러 만드는 이유는?

<details>
<summary>정답 보기</summary>
<p>검사 함수가 <b>"항상 통과"하는 버그</b>가 가장 위험해서요. 틀린 예를 넣었을 때 실제로 실패하는지(2/2 탐지)가 검사 함수의 테스트예요. 원본은 <code>copy.deepcopy</code>로 보호해요.</p>
</details>

### FT2-Q9. 객관식 — 행 단위로 섞으면
72행을 행 단위로 섞어 48/12/12로 자르면 생기는 일은?

1. 유형 비율이 정확히 같아진다
2. test 행 대부분이 같은 그룹 형제를 train에 두어 이미 본 문제가 된다
3. 길이 512를 넘는 행이 생긴다
4. ZIP 해시가 같아진다

<details>
<summary>정답 보기</summary>
<p><b>2.</b> seed 42로 해 보면 test 12행이 모두 형제를 train에 두고, 5행은 질문 문장까지 같아요(데이터 누수). 그래서 그룹 목록을 섞어 8/2/2 그룹으로 나눠요.</p>
</details>

### FT2-Q10. 단답형 — sorted
`group_ids = sorted({...})`처럼 섞기 전에 정렬부터 하는 이유는?

<details>
<summary>정답 보기</summary>
<p>set의 순서는 실행마다 다를 수 있어서, 정렬로 순서를 먼저 고정해야 <b>같은 seed에서 같은 분할</b>이 나와요. <code>random.Random(SEED)</code>는 전역 random을 건드리지 않는 독립 생성기.</p>
</details>

### FT2-Q11. 객관식 — dev와 test
다음 중 맞는 말은?

1. test는 설정을 고를 때마다 여러 번 본다
2. dev 점수가 가장 믿을 만한 최종 성능이다
3. test를 보고 설정을 바꾸면 test가 dev가 된다
4. train 점수가 높으면 일반화가 잘 된 것이다

<details>
<summary>정답 보기</summary>
<p><b>3.</b> train은 가중치 갱신(점수가 좋은 게 당연), dev는 여러 번 보고 고르니 낙관적으로 부풀고, test는 모든 결정을 고정한 뒤 <b>한 번</b>. dev 12행이면 1문항 = 8.3%p.</p>
</details>

### FT2-Q12. 단답형 — 1 · 2장은 왜
1 · 2장은 Qwen 가중치 W도, LoRA의 A · B도 바꾸지 않아요. 그런데도 필요한 이유를 두 가지로 말해 보세요.

<details>
<summary>정답 보기</summary>
<p>① <b>1장</b>: 학습 전 응답을 같은 조건으로 남겨야 3장 이후 "좋아졌다"를 말할 수 있어요(<code>baseline.json</code>). ② <b>2장</b>: 파인튜닝은 보여 준 정답을 따라 배우니, 정답 · 경계 · 길이 · 분할이 틀리면 에러 없이 틀린 걸 배우거나 점수가 부풀어요(<code>training_data.zip</code>). 학습이 성공했는지 판단할 수 있게 만드는 단계.</p>
</details>
