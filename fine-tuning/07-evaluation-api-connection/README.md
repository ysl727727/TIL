# 7장. 모델 성능 평가와 서비스 연결

> 2026-11-25 학습 기록. 파인튜닝 7일차 수업. 3~6장이 **"어떻게 배우게 할까"**였다면, 7장은 **새로 학습하지 않고** 지금까지 만든 다섯 결과(base · full\_sft · lora · qlora · dpo)를 **같은 dev 12문항으로 채점**한다. 그리고 형식을 지킨 3장 SFT 하나만 **검색 · FastAPI에 연결**한다. 오늘은 `inspect_response`의 세 관문과 "형식 통과 ≠ 업무 정답"을 가장 오래 붙잡았고, dev가 무엇인지와 코드 펜스를 벗기면 어떻게 되는지를 질문했다.

> 7장의 한 문장: **숫자 앞에는 출처(같은 파일 · 같은 문항 · 같은 설정), 뒤에는 원문. 형식 검사 · HTTP 200은 "약속을 지켰다"일 뿐이라 금액 비교 · 승인 판단은 사람이 원문으로 따로 채점하고, 후보는 고정하되 배포 승인으로 바꾸지 않는다.**

## 큰 흐름

```text
[준비] training_data.zip(2장) · sft_model.zip · sft_report.json(3장) · lora_report.json(4장)
       · qlora_report.json(5장) · dpo_report.json(6장) = 6개 업로드, 학습은 안 함
7-1 형식 · 의미    파일 지문(sha256) 대조 → JSON · 계약 · 인용 ID 세 관문 → 형식은 맞고 뜻은 틀린 답
7-2 같은 입력      보고서 5개의 dev 답 60개를 문항 ID로 정렬 → 질문 · 근거 · 생성 설정 대조
                  → 단계별 통과 수 · 첫 실패 단계 → 원문 읽기 (SFT만 형식 12/12, 그런데 over_limit 오답)
7-3 검색 · API     팀 필터 + 낱말 겹침 검색 → 3장 SFT 복원 → /answer (422 입구 · 200/502 출구) → TestClient
                  → 80,000원 질문은 200인데 판단 틀림, 통신비 질문은 보류로 맞음
7-4 실패 · 후보    형식 · 검색 · 업무 판단 · 운영으로 실패 칸 나누기 → full_sft 후보 고정(deployment_ready False)
                  → evaluation_report.json · candidate_manifest.json
      ↓
8장 검증 · 인계: 고정한 후보와 생성 설정으로 test를 처음 연다
```

**6장까지 vs 7장 — 배우는 장과 채점하는 장**

| | 3~6장 | 7장 |
|---|---|---|
| 가중치 | 바뀜 (SFT · LoRA · QLoRA · DPO) | **안 바뀜** (저장된 답 재채점 · SFT 복원만) |
| 비교 단위 | 한 방법의 학습 전 vs 후 | **다섯 방법 × 같은 dev 12** = 60개 |
| 채점 | 형식 · 보류 · 단정 집계 | 관문별 통과 · **첫 실패 단계** · 사람 원문 검토 |
| 결과물 | 모델 · 보고서 | `evaluation_report.json` · `candidate_manifest.json` |
| GPU | 처음부터 필요 | 7-1 · 7-2는 CPU, **7-3 SFT 복원부터 BF16 GPU** |

## 학습 목표
- 채점 전에 보고서와 입력 파일의 sha256 지문을 대조하는 이유와, 지문이 보장하는 것("같은 파일")과 보장하지 않는 것("좋은 설정")을 구분한다.
- 형식 검사(JSON · 계약 · 인용 ID) · 업무 의미 · 참조 일치를 구분하고, 형식이 완벽한 오답을 예로 설명한다.
- `inspect_response`의 세 관문과 "첫 실패 단계만 세는" 이유를 설명한다.
- dev(모의고사)와 test(수능)의 역할을 구분하고, dev 성과를 일반화 성능이라고 말하지 않는 이유를 설명한다.
- 검색 → 생성 → 출력 검사를 FastAPI로 잇고 422 · 502 · 200의 의미와 한계를 설명한다.
- 실패를 형식 · 검색 · 업무 판단 · 운영 칸으로 나누고 칸마다 다음 수정 방향을 말한다.

## 실습 환경
- 노트북: `evaluation_and_connection.ipynb` (22셀, 셀 번호는 슬라이드처럼 위에서부터 1번). 통합 실습 `finetuning_ch07_practice.ipynb`.
- 입력 6개: `training_data.zip` · `sft_model.zip` · `sft_report.json` · `lora_report.json` · `qlora_report.json` · `dpo_report.json`. SFT 모델과 보고서는 **6장 DPO 입력으로 썼던 바로 그 파일**이어야 한다(다시 압축 X, JSON 다시 저장 X).
  - 받은 수업자료 보고서 4개는 모두 **L4**에서 만든 것이고, sft · lora · qlora 데이터 지문 · dpo 입력 3개 지문이 모두 일치 → 셀 5 통과.
  - 받은 `dpo_report.json`은 **lr 2e-5** 실행이라 dpo 형식 통과가 0/12(JSON 12). 슬라이드(2/12)와 달라도 오류가 아니다.
  - `sft_model.zip`은 BF16 → **셀 14부터 native BF16 GPU(L4)** 필요. `candidate_sft` 폴더가 이미 있으면 멈추니 빈 작업 폴더에서.
- 패키지 고정: `transformers 5.22.2` · `accelerate 1.15.0` · `fastapi 0.162.0` · `httpx 0.28.1` · `pydantic 2.14.3` · `starlette 1.10.0`.
- 슬라이드 숫자는 강사 PC(RTX 5060 Laptop · BF16 · seed 42 · dev 12 · 1회) 기준. "수업자료(L4)" 값은 받은 보고서를 노트북과 같은 검사 로직으로 세어 본 값.

## 실습 파일

| 파일 | 하는 일 | 상태 |
|---|---|---|
| `evaluation_and_connection.ipynb` | 7-1 지문 · 세 관문 → 7-2 다섯 결과 60개 비교 → 7-3 검색 · SFT 복원 · `/answer` → 7-4 실패 분류 · 후보 고정 | ✅ 수업 · 핵심 함수 정리 (수업자료 보고서로 형식 통과 수 확인) |
| `finetuning_ch07_practice.ipynb` | 통합 실습 TODO 1\~8: `inspect_response` · `retrieve_documents` · `answer_question` | ✅ Colab 실행 · TODO 답과 이유 정리 |
| `evaluation_report.json` · `candidate_manifest.json` | 60개 원문 · 검사 · 선정 / 후보 인수인계서 (8장 입력) | ✅ 8장 입력으로 보관 |

---

## 핵심 이론

### 준비: 환경 셀 (셀 2 · 3)과 `file_sha256`

```python
MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
REVISION = "7ae557604adf67be50417f59c2c2f167def9a775"   # 기반 모델의 정확한 버전(커밋)

def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):   # 1MB씩 읽기
            digest.update(chunk)
    return digest.hexdigest()
```
**쉽게:** `file_sha256`은 파일의 **지문**을 만든다. 1바이트라도 다르면 지문이 완전히 달라진다.
- 1GB짜리 `sft_model.zip`을 한 번에 메모리에 올리지 않으려고 **1MB씩 나눠서** 읽는다.
- `fastapi`(API 서버), `httpx`(TestClient가 내부에서 씀), `pydantic`(입력 검사), `starlette`(FastAPI의 바탕) 버전도 고정. 다르면 "런타임 재시작" 에러로 멈춘다.
- **왜 학습을 안 하나:** 다시 학습하면 결과가 또 흔들리니까(6장 학습 재현 0~2/12), **보고서에 이미 저장된 답**을 다시 채점한다. 모델 다섯 개를 동시에 GPU에 올리지도 않는다.

### 7-1. 형식 검사와 업무 의미 평가하기

#### 채점 전에 파일 지문부터 맞추기 (셀 5)
```python
input_sha256 = {name: file_sha256(name) for name in input_names}      # 6개 파일 지문
reports = {name: json.loads(Path(name + "_report.json").read_text(encoding="utf-8"))
           for name in ["sft", "lora", "qlora", "dpo"]}

for name in ["sft", "lora", "qlora"]:                                   # 같은 데이터로 학습했나
    if reports[name].get("data_sha256") != input_sha256["training_data.zip"]:
        raise ValueError(f"{name} 보고서와 training_data.zip이 다릅니다.")
for name in ["training_data.zip", "sft_model.zip", "sft_report.json"]:  # 6장이 쓴 파일과 같은가
    if reports["dpo"].get("input_sha256", {}).get(name) != input_sha256[name]:
        raise ValueError(f"6장에서 입력으로 사용한 파일과 다릅니다: {name}")

with ZipFile("training_data.zip") as archive:
    dataset_info = json.loads(archive.read("dataset_info.json"))
    dev_bytes = archive.read("dev.jsonl")          # test.jsonl은 이름만 확인, 내용은 안 읽음
```
```text
비교할 dev: 12 개, 그룹: ['policy01', 'policy05']
test 내용은 읽지 않았습니다.
```
**쉽게:** 다섯 답안지를 비교하기 전에 **"다 같은 시험지로 본 시험인가"**를 먼저 확인한다.
- 각 보고서는 학습할 때 쓴 파일의 지문을 기록해 뒀다. 지금 올린 파일의 지문과 대조한다.

  | 보고서 | 대조하는 지문 |
  |---|---|
  | sft · lora · qlora | 데이터 ZIP |
  | dpo | 데이터 · 모델 · SFT 보고서 |

- `check_dev_records`가 확인하는 4가지
  - dev 파일 지문
  - 중복 없는 12문항
  - 그룹(policy01 · policy05)
  - 대화 역할(system · user · assistant)
- **지문이 맞다 = "같은 파일"이라는 뜻.** "좋은 설정으로 만든 보고서"라는 뜻은 아니다. 예: lr 2e-5로 무너진 DPO 보고서도 지문은 통과한다.
- 수업자료(L4): sft · lora · qlora 데이터 지문 일치, dpo 입력 3개 모두 일치 → 셀 5 통과.

#### 한 답을 세 가지 질문으로 채점

| 질문 | 무엇을 보나 | 누가 |
|---|---|---|
| **형식 검사** | JSON · 키 3개 · 타입 · 인용 ID | 자동 (셀 7 · 10) |
| **업무 의미** | 금액 비교 · 승인 조건 · 근거 적용 | 사람이 원문 읽기 (셀 11) |
| **참조 일치** | 모범답안 객체와 완전히 같은가 | 교안 코드에는 없음 |

생성 원문은 **고치지 않고 보관**한다. 점수를 말할 때는 **검사 이름과 분모**를 같이 말한다. 예: "형식 통과 12/12", "원문 검토로 초과 2문항 오답".

> 참조 일치는 가장 좁은 기준이다. 표현만 다르고 뜻이 맞는 답도 불일치가 되니까 교안은 쓰지 않는다.

#### 핵심 함수: `inspect_response` (셀 7), 관문 세 개
```python
def inspect_response(raw, source_ids):
    result = {"json_object": False, "schema_ok": False, "citation_ids_ok": False}
    try:
        value = json.loads(raw)                      # ① JSON으로 읽히나 (코드 펜스 안 벗김)
    except json.JSONDecodeError:
        return result
    if not isinstance(value, dict):                  #    리스트 · 숫자면 탈락
        return result
    result["json_object"] = True

    status, answer, citations = value.get("status"), value.get("answer"), value.get("citations")
    valid_fields = (
        set(value) == {"status", "answer", "citations"}      # ② 키가 정확히 3개
        and isinstance(status, str) and status in {"answered", "abstained"}
        and isinstance(answer, str) and bool(answer.strip()) #    answer 빈칸 X
        and isinstance(citations, list) and all(isinstance(x, str) for x in citations)
    )
    if not valid_fields:
        return result
    if (status == "answered" and not citations) or (status == "abstained" and citations):
        return result                                # ② 상태와 인용이 짝이 맞나
    result["schema_ok"] = True
    result["citation_ids_ok"] = set(citations).issubset(source_ids)   # ③ 준 문서 ID 안인가
    return result
```
**쉽게:** 답을 관문 세 개에 차례로 통과시킨다. 앞 관문에서 떨어지면 뒤 관문은 **보지도 않고** False로 남는다.

| 관문 | 묻는 것 | 떨어지는 답 |
|---|---|---|
| ① `json_object` | JSON 객체로 읽히나 | ` ```json ... ``` ` 코드 펜스로 감싼 답 |
| ② `schema_ok` | 키 · 타입 · 상태와 인용의 짝 | 보류(abstained)인데 answer가 빈칸 / 답했는데(answered) 인용이 없음 |
| ③ `citation_ids_ok` | 인용이 준 문서 ID 안인가 | `政策01-v1`처럼 ID가 살짝 다름 |

- **코드 펜스를 벗겨서 통과시키지 않는다.** 모델이 "JSON만 출력"이라는 **약속을 지켰는지** 재는 검사라서.
- `issubset`: 인용한 ID가 **모두** 준 문서 ID 집합 안에 있는가. 빈 인용 `[]`는 항상 True(보류는 ②에서 이미 짝을 봤음).
- `check_format_examples`는 이 함수가 일부러 만든 반례 5개를 제대로 거르는지 먼저 시험한다(함수를 위한 테스트).

#### 형식이 완벽한 오답도 통과한다 (셀 7 출력)
```python
wrong_meaning = {
    "status": "answered",
    "answer": "70,000원은 65,000원 이하이므로 사전 승인이 필요하지 않습니다.",
    "citations": ["policy01-v1"],
}
```
```text
형식이 정상인 의미 오류: {'json_object': True, 'schema_ok': True, 'citation_ids_ok': True}
```
**쉽게:** 70,000 > 65,000이니 정답은 "예약 전 서면 승인 필요"인데, 세 관문은 **전부 True**.
- 숫자의 대소 관계, 승인 시점, 근거가 부족한 이유는 형식 검사가 **보지 못한다.**
- 그래서 "형식 통과 = 정답"이라고 말하면 안 된다.

#### 업무 의미는 문항 유형마다 다르게 묻는다

| 유형 | 가온팀 예 (policy01) | 읽을 때 묻는 것 | 맞는 방향 |
|---|---|---|---|
| below | 60,000원 · 한도 65,000 | 한도 이하를 확인했나 | 승인 불필요 |
| boundary | 65,000원 · 한도 65,000 | 같은 금액을 초과로 바꾸지 않았나 | 승인 불필요 |
| over_limit | 70,000원 · 한도 65,000 | 초과와 서면 승인을 연결했나 | **승인 필요** |
| updated | 70,000원 · 개정 한도 75,000 | 개정 한도로 다시 판단했나 | 승인 불필요 |
| missing | 통신비 · 문서 없음 | 모른다고 하고 담당자를 안내했나 | 보류 |
| irrelevant | 통신비 · 숙박 규정만 있음 | 숙박 근거를 끌어다 쓰지 않았나 | 보류 |

마루팀(policy05)도 같은 여섯 유형. 한도 105,000원 → 개정 115,000원. 6유형 × 2팀 = dev 12문항.


### 7-2. 같은 입력으로 응답 변화 비교하기

#### 답안지 60장: 다섯 결과

| 이름 | 출발점 → 학습 | 어디서 꺼내나 |
|---|---|---|
| base | 공개 모델 그대로 | `reports["sft"]["dev_before"]` |
| full_sft | 공개 모델 → 전체 SFT | `reports["sft"]["dev_after"]` |
| lora | 공개 모델 → A · B만 | `reports["lora"]["dev_after"]` |
| qlora | NF4 기반 → A · B만 | `reports["qlora"]["comparison"]["qlora"]` |
| dpo | SFT → 선호 학습 | `reports["dpo"]["dev_after"]` |

#### 핵심 코드: 입력 맞추기 (셀 9)
```python
comparison = {"base": ..., "full_sft": ..., "lora": ..., "qlora": ..., "dpo": ...}   # 위 표

generation = reports["sft"]["generation"]                 # 기준 생성 설정
for name in ["lora", "qlora", "dpo"]:
    settings = reports[name]["generation"] if name == "dpo" else reports[name]["config"]["generation"]
    for key in generation_keys:                            # do_sample · num_beams · max_new_tokens · ...
        if settings.get(key) != generation.get(key):
            raise ValueError(f"{name}의 생성 설정이 다릅니다: {key}")

responses = []
for model_name, outputs in comparison.items():
    if len(outputs) != 12 or {item["case_id"] for item in outputs} != set(dev_by_id):
        raise ValueError(f"{model_name}의 dev 12개가 일치하지 않습니다.")
    for item in outputs:
        row = dev_by_id[item["case_id"]]                   # 행 순서가 아니라 문항 ID로 맞춤
        if item["messages"] != row["messages"][:2]:        # system · user (질문 + 근거)가 같은가
            raise ValueError(...)
        source_ids = {doc["id"] for doc in json.loads(row["messages"][1]["content"])["documents"]}
        responses.append({"model": model_name, "case_id": row["id"], "case_type": row["case_type"],
                          "raw_response": item["raw_response"],
                          "format_checks": inspect_response(item["raw_response"], source_ids),
                          "length_limited": item["length_limited"]})
```
```text
같은 dev 입력을 확인한 응답: 60
과거 학습 시간과 메모리는 측정 구간이 달라 새 종합 순위로 합치지 않습니다.
```
**쉽게:** 답안지 60장을 **문항 번호(ID)로 정렬**하고, 문제지(질문 + 근거 문서)와 채점 조건(생성 설정)이 같은지 하나씩 확인한 다음에 채점한다.
- `messages[:2]`는 system + user. `[2]`(assistant)는 모범답안이라 비교 대상이 아니다.
- **같게 맞춘 것:** 문항 · 질문 · 근거 문서 · 생성 설정
- **안 맞춘 것:** 학습 목적 · 양자화 · 학습 자원
- 학습 시간 · 메모리는 장마다 잰 구간이 달라서 하나의 순위표로 합치지 않는다.

#### 핵심 코드: 단계별 통과 수와 첫 실패 단계 (셀 10)
```python
for name in comparison:
    rows = [item for item in responses if item["model"] == name]
    counts = {key: sum(item["format_checks"][key] for item in rows)       # True=1로 더하기
              for key in ["json_object", "schema_ok", "citation_ids_ok"]}
    counts.update(model=name, total=len(rows),
                  format_ok=sum(all(item["format_checks"].values()) for item in rows))

failure_counts = {}
for name in comparison:
    stages = Counter()
    for item in [x for x in responses if x["model"] == name]:
        stage = next((key for key, passed in item["format_checks"].items() if not passed),
                     "format_passed")                 # 처음 False인 관문 하나만
        stages[stage] += 1
    assert sum(stages.values()) == 12
```
**쉽게:**
- `sum(True, False, ...)`는 True 개수, `all(...)`은 세 관문 다 True인가.
- **첫 실패만 센다.** JSON에서 떨어진 답은 ②③도 자동으로 False인데, 이걸 실패 3개로 세면 부풀려진다.
- `next(..., "format_passed")`: 처음 False인 키를 꺼내고, 없으면 기본값 "format_passed".
- 분모는 항상 **dev 12개**.

#### 결과: SFT만 12/12

| 방법 | JSON | + 계약 | + 인용 = 형식 통과 | 처음 떨어진 곳 (슬라이드) | 수업자료(L4) 형식 통과 · 첫 실패 |
|---|---|---|---|---|---|
| base | 0 | 0 | 0 | JSON 12 | 0 · JSON 12 |
| **full_sft** | 12 | 12 | **12** | 없음 | **12** · 없음 |
| lora | 0 | 0 | 0 | JSON 12 | 0 · JSON 12 |
| qlora | 11 | 1 | 0 | 계약 10 · 인용 1 · JSON 1 | 0 · 계약 9 · 인용 2 · JSON 1 |
| dpo | 4 | 4 | 2 | JSON 8 · 인용 2 | **0 · JSON 12** |

- **형식 통과 수는 업무 정답 수가 아니다.**
- 수업자료의 dpo는 lr **2e-5** 실행이라 6장에서 본 붕괴(말 자체가 깨짐) 때문에 JSON부터 전부 떨어진다. 슬라이드와 달라도 오류가 아니다.

#### 원문 읽기 (셀 11): 70,000원은 초과인가?
```python
criteria_by_type = {
    "below":      "질문 금액이 문서의 1박 한도 이하인지 확인하고 사전 승인 불필요를 설명하는가?",
    "boundary":   "한도와 같은 금액을 초과로 바꾸지 않는가?",
    "over_limit": "질문 금액의 초과 사실과 예약 전 서면 승인 필요를 연결하는가?",
    "updated":    "제공된 개정 문서의 한도를 사용해 같은 질문 금액을 다시 판단하는가?",
    "missing":    "확인할 근거가 없음을 설명하고 담당자 확인을 안내하는가?",
    "irrelevant": "숙박비 근거를 통신비에 적용하지 않고 확인할 수 없는 이유를 설명하는가?",
}
review_criteria = {row["id"]: {"question_and_documents": ..., "reference_response": ...,
                               "review_question": criteria_by_type[row["case_type"]]}
                   for row in dev_rows}
# policy01의 다섯 유형(below 제외)만 다섯 모델 원문 + 모범답안을 찍음
```
**쉽게:** 의미 채점은 코드가 못 하니까 **사람이 읽을 질문지**를 문항마다 붙인다. 키워드("승인", "초과") 유무로 정답률을 만들지 않는다. 같은 낱말도 부정문이나 문맥에 따라 뜻이 달라지니까.

| 방법 | over_limit 원문 핵심 | 형식 | 뜻 |
|---|---|---|---|
| 모범답안 | 70,000원은 한도를 **초과**하므로 예약 전 서면 승인을 받아야 합니다. | - | - |
| full_sft | 70,000원은 한도 **이하**이므로 사전 승인이 필요하지 않습니다. | O | **X** |
| base · lora | ` ```json ` … 한도 이하의 예약에는 … | X | X |
| qlora | `"citations": ["政策01-v1"]` (키도 빠짐) | X | X |
| dpo | … 서면 승인을 받아 보실 수 없습니다.supports#query} | X | X |

> 형식 12/12인 full_sft도 over_limit에서 **숫자 비교를 틀린다.** 7장의 핵심 장면.
> below 문항과 마루팀(policy05) 답은 `evaluation_report.json`의 `responses`에서 읽는다.


### 7-3. 검색과 API에 학습 모델 연결하기

#### 요청 한 건이 지나가는 네 칸
```text
① 입력 검사          ② 검색                 ③ 생성                ④ 출력 검사
AnswerRequest   →   retrieve_documents  →  generate_answer   →  inspect_response
   ↓ 실패               ↓ 없으면               (3장 SFT,              ↓
 422 접수 거절        빈 목록 그대로 전달      학습된 유일한 칸)     200 형식 통과 / 502 형식 실패
```
**쉽게:** RAG의 축소판. 다만 검색은 벡터 검색이 아니라 **낱말 겹침**이다. 그리고 **LoRA · QLoRA · DPO 모델은 이 경로에 올라가지 않는다.** 형식을 12/12 지킨 full_sft만 연결한다.

#### 핵심 함수: `retrieve_documents` (셀 13)
```python
corpus = []
for row in dev_rows:
    if row["case_type"] == "updated":                       # 개정판(v2) 문서만 "현재 규정"으로
        payload = json.loads(row["messages"][1]["content"])
        group = next(g for g in dataset_info["groups"] if g["group_id"] == row["group_id"])
        corpus.append({**payload["documents"][0], "team": group["team"], "version": "v2"})

def retrieve_documents(question, team):
    terms = ["숙박", "예약", "방"]
    candidates = [
        (sum(term in question and term in doc["text"] for term in terms), doc)   # 겹친 낱말 수
        for doc in corpus
        if doc["team"] == team                                                  # 팀부터 거르기
    ]
    candidates.sort(key=lambda pair: pair[0], reverse=True)                     # 많이 겹친 순
    return ([{"id": candidates[0][1]["id"], "text": candidates[0][1]["text"]}]
            if candidates and candidates[0][0] > 0 else [])                     # 0개 겹치면 빈 목록
```
```text
검색 문서: [('가온', 'policy01-v2'), ('마루', 'policy05-v2')]
통신비 질문 검색: []
```
**쉽게:** 검색 대상은 문서 **두 개뿐**(가온 v2, 마루 v2).
1. 질문한 사람의 팀 문서만 남긴다.
2. "숙박 · 예약 · 방" 중 몇 개가 **질문과 문서 양쪽에** 들어 있는지 센다.
3. 1개 이상 겹치면 그 문서 1개를, 하나도 안 겹치면 빈 목록을 돌려준다.

- `{**doc, "team": ...}`: 문서 딕셔너리를 펼쳐 복사하고 키를 덧붙이는 문법.
- `True + True = 2`라서 `sum(bool, ...)`로 겹친 개수를 셀 수 있다.

| 질문 (team=가온) | 검색 | 맞나 |
|---|---|---|
| 숙박 예약 | policy01-v2 | O |
| 통신비 지원 | 없음 | O |
| 80,000원 **숙소**는 승인 필요? | 없음 | X (동의어 못 잡음) |
| **호텔**은 얼마까지? | 없음 | X |
| 통신비 **예약**은 어떻게? | policy01-v2 | X (낱말만 겹침) |
| **마루팀** 숙박 한도는? | policy01-v2 | X (팀 인자가 가온) |

위 두 줄은 교안 출력, 아래 네 줄은 튜터가 검색 함수만 호출해 본 결과. **검색 품질 평가가 따로 필요하다.**

#### SFT 복원 (셀 14): 새 학습 없이 되살리기
```python
if not torch.cuda.is_bf16_supported(including_emulation=False):
    raise RuntimeError("저장 모델은 BF16입니다. native BF16 GPU를 연결하세요.")
model_root = Path("candidate_sft").resolve()
if model_root.exists():
    raise FileExistsError("이전 candidate_sft를 보관하고 빈 작업 폴더에서 시작하세요.")

with ZipFile("sft_model.zip") as archive:
    names = archive.namelist()
    if len(names) != len(set(names)) or set(names) != expected_files:   # 정확히 6개 파일
        raise ValueError(...)
    for member in archive.infolist():
        target = (model_root / member.filename).resolve()
        if not target.is_relative_to(model_root) or member.file_size <= 0:   # 폴더 밖 경로 · 빈 파일 거절
            raise ValueError(...)
    for name in names:                                                   # 확인한 6개만 복사
        ...shutil.copyfileobj(source, destination)

tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
source_tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=REVISION)
assert tokenizer.get_vocab() == source_tokenizer.get_vocab()            # 어휘 같나
assert tokenizer.chat_template == source_tokenizer.chat_template        # 대화 템플릿 같나
model = AutoModelForCausalLM.from_pretrained(model_path, local_files_only=True,
            dtype=torch.bfloat16, attn_implementation="sdpa").to("cuda").eval()
```
**쉽게:** 압축을 풀기 전에 **"이 ZIP이 진짜 3장 모델 폴더인가"**를 확인하고, 안전한 것만 꺼낸다.

| 확인 | 다르면 |
|---|---|
| GPU · BF16 지원 | 멈춤 |
| `candidate_sft` 폴더가 이미 있음 | 멈춤 (덮어쓰기 방지) |
| ZIP 안 6개 파일 · 경로 · 빈 파일 | 멈춤 |
| 토크나이저 어휘 · 대화 템플릿 | 멈춤 |
| dev 한 문항의 원문 (셀 15) | 멈추지 않고 **False만 기록** |

- 6개 파일: `config.json` · `generation_config.json` · `model.safetensors` · `tokenizer.json` · `tokenizer_config.json` · `chat_template.jinja` (모두 `sft_model/` 아래)
- `is_relative_to`: `../../` 같은 경로로 폴더 밖에 파일을 쓰는 **ZIP 경로 공격**을 막는다.
- `.eval()`: 드롭아웃 같은 학습용 동작을 끄는 추론 모드.

#### 핵심 함수: `generate_answer` (셀 15)
```python
def generate_answer(question, documents):
    messages = [
        {"role": "system", "content": dataset_info["system_prompt"]},
        {"role": "user", "content": json.dumps({"question": question, "documents": documents},
                                               ensure_ascii=False)},
    ]
    inputs = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                                           return_dict=True, return_tensors="pt").to(model.device)
    if inputs["input_ids"].shape[1] > 512:                     # [1, T]의 T = 입력 토큰 수
        raise ValueError("입력이 512토큰을 넘었습니다. 질문과 근거를 줄여 주세요.")

    with torch.inference_mode():                               # 역전파 기록 안 함
        output = model.generate(**inputs, generation_config=generation_config)

    new_ids = output[0, inputs["input_ids"].shape[1]:]         # 입력 뒤에 붙은 새 토큰만
    eos = generation_config.eos_token_id
    eos = [eos] if isinstance(eos, int) else eos
    ended = bool(len(new_ids) and new_ids[-1].item() in eos)   # 스스로 끝냈나
    return {"raw_response": tokenizer.decode(new_ids, skip_special_tokens=True),
            "input_tokens": inputs["input_ids"].shape[1],
            "new_tokens": len(new_ids),
            "length_limited": len(new_ids) >= generation_config.max_new_tokens and not ended}
```
**쉽게:** 질문 + 검색된 문서를 **학습 때와 똑같은 대화 모양**(system 지시 + user JSON)으로 포장해서 모델에 넣고, 답만 잘라 돌려준다.
- `add_generation_prompt=True`: 끝에 "이제 assistant 차례" 표시를 붙여서 모델이 답을 이어 쓰게 한다.
- `generate`의 출력은 **입력 + 새 답**이라서 입력 길이만큼 잘라낸다.
- `length_limited`: 최대 토큰까지 꽉 채웠는데 EOS로 끝나지 않았다면 **중간에 잘린 답**.
- 셀 15 아래쪽에서 dev 한 문항(probe)을 다시 생성해 3장 원문과 같은지 본다. 다른 GPU면 반올림 차이로 False일 수 있어서 **숨기지 않고 기록만** 한다.

#### API 파라미터 (셀 16): 모델 앞에서 입력 범위 정하기

| 설정 | 값 | 의미 |
|---|---|---|
| `strict` | `True` | `123`을 `"123"`으로 몰래 바꿔 받지 않음 |
| `extra` | `forbid` | 정의 안 한 필드 거절. 요청자가 `documents`를 끼워 넣는 것도 거절 |
| `str_strip_whitespace` | `True` | 양끝 공백 정리 후 검사 → `" "`는 빈 문자열이 돼 거절 |
| `team` 길이 | 1~20 | 빈 팀 · 너무 긴 값 거절 |
| `question` 길이 | 1~500 | 글자 수 제한 (모델 토큰 512 제한과 별개) |

#### 핵심 코드: `AnswerRequest` · `/answer` (셀 18)
```python
class AnswerRequest(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid", str_strip_whitespace=True)
    team: str = Field(min_length=1, max_length=20)
    question: str = Field(min_length=1, max_length=500)

app = FastAPI(title="출장 규정 SFT 연결 예제")

@app.post("/answer")
def answer(request: AnswerRequest):                     # ① 여기서 검사 실패 → FastAPI가 422
    documents = retrieve_documents(request.question, request.team)     # ②
    try:
        generated = generate_answer(request.question, documents)       # ③
    except ValueError as error:                                         # 512토큰 초과
        return JSONResponse(status_code=422, content={"detail": str(error)})

    checks = inspect_response(generated["raw_response"], {doc["id"] for doc in documents})  # ④
    format_ok = all(checks.values()) and not generated["length_limited"]
    body = {**generated, "retrieved_documents": documents, "format_checks": checks,
            "response": json.loads(generated["raw_response"]) if format_ok else None,
            "review_required": True}                                    # 200이어도 사람 검토 필요
    return JSONResponse(status_code=200 if format_ok else 502, content=body)

with TestClient(app) as client:
    result = client.post("/answer", json={"team": "가온", "question": "...1박 80,000원인 방을..."})
    for bad in [{"team": "가온", "question": 123},
                {"team": "가온", "question": " "},
                {"team": "가온", "question": "숙박비", "documents": []}]:
        assert client.post("/answer", json=bad).status_code == 422
```
**쉽게:** **입구는 엄격하게, 출구는 정직하게.**
- **입구:** 이상한 요청은 모델을 부르기도 전에 422로 돌려보낸다. GPU를 아끼고, 요청자가 근거 문서를 조작하는 것도 막는다.
- **출구:** 형식이 깨진 답을 몰래 고쳐서 200으로 내보내지 않고 **502**로 솔직하게 알린다.
- `review_required: True`: 200이어도 업무 판단은 사람이 검토해야 한다는 표시.
- `TestClient`: 진짜 서버를 열지 않고 **같은 프로세스 안에서** 요청을 흉내 낸다. 외부 공개 · 동시 요청 시험은 아니다.

| 보낸 것 · 나온 것 | 상태 | 시험했나 |
|---|---|---|
| `question: 123` (숫자) | 422 | O |
| `question: " "` (공백 한 칸) | 422 | O |
| `documents`를 끼워 넣음 | 422 | O |
| 입력 512토큰 초과 | 422 | 코드만 있음 |
| 답 형식 실패 · 잘림 | 502 | 코드만 있음 |
| 답 형식 통과 | 200 | O (2건) |

> HTTP 상태 코드 정리: **422** = 요청 내용이 규칙에 안 맞음(요청자 잘못), **502** = 뒤쪽(모델)이 제대로 된 답을 못 줌, **200** = 성공. 이 수업에서 "성공"은 **형식 성공**일 뿐이다.

#### 실제 호출: 200인데 판단은 틀림

| 항목 | 요청 1 · 숙박 80,000원 | 요청 2 · 통신비 |
|---|---|---|
| 검색 | policy01-v2 (개정 한도 75,000) | 없음 |
| status | answered | abstained |
| 형식 · HTTP | 통과 · 200 | 통과 · 200 |
| 업무 판단 | **틀림** (80,000 > 75,000인데 "한도 이하") | 맞음 (보류) |

요청 1 원문: "숙박비 지원 한도는 1박 75,000원입니다. 질문의 1박 80,000원은 한도 이하이므로 사전 승인이 필요하지 않습니다."
요청 2 원문: "제공된 근거로는 출장 중 통신비 지원 한도를 확인할 수 없습니다. 담당자에게 확인하세요."

#### 무엇을 검증했고, 무엇은 안 했나

| 대상 | 검증한 것 | 검증하지 않은 것 |
|---|---|---|
| 검색 | 예제 3개 (숙박 1건 · 빈 목록 2건) | 동의어 · 다른 주제 · 문서가 많을 때 |
| 모델 복원 | 파일 · 어휘 · 템플릿 · 원문 1건(기록) | 나머지 11문항 재현 · 다른 GPU |
| 입력 계약 | 잘못된 요청 3개 → 422 | 사용자 인증 · 권한 · 악의적 질문 |
| 출력 | 형식 · 인용 ID · 길이 잘림 | 금액 비교 · 승인 판단 · 인용한 이유 |
| API | 프로세스 안 호출 2개가 200 또는 502 | 외부 공개 · 동시 요청 · 지연 시간 |
| 연결한 모델 | 3장 full SFT 하나 | LoRA · QLoRA · DPO의 서빙 |


### 7-4. 실패 원인을 읽고 수정 방향 정하기

#### 어느 칸에서 실패했는지 나누기

| 실패 | 알아보는 법 | 이 장의 예 | 다음에 시험할 방향 |
|---|---|---|---|
| 형식 | 첫 실패 단계 | 원본 LoRA: 12개 모두 JSON 실패 | 학습 설정 · 데이터 형식 |
| 검색 | `retrieved_documents` | "숙소" 질문 → 빈 목록 | 동의어 · 검색 방법 · 검색 평가 |
| 업무 판단 | 문서는 맞고 answer가 틀림 | 80,000원을 75,000원 이하라고 | 비교 사례 · 규칙 코드 · 사람 검토 |
| 운영 | 이 노트북으로는 모름 | 인증 · 동시 요청 · 외부 공개 | 목적에 맞는 별도 시험 |

**쉽게:** "모델이 틀렸다"로 뭉뚱그리지 말고 **어느 칸**에서 틀렸는지 나눠야 고칠 곳이 보인다.
- 검색이 문서를 못 찾았는데 모델을 다시 학습하면 헛수고.
- 금액 비교처럼 **답이 하나로 정해지는 규칙**은 모델 대신 **코드로 계산**하는 선택지도 있다(`if 금액 > 한도:`).

#### 핵심 코드: 알려진 실패를 남기고 후보 고정 (셀 20)
```python
known_bad = '{"status": "answered", "answer": "숙박비 지원 한도는 1박 65,000원입니다. 질문의 1박 70,000원은 한도 이하이므로 사전 승인이 필요하지 않습니다.", "citations": ["policy01-v1"]}'
selected_raw = next(x["raw_response"] for x in responses
                    if x["model"] == "full_sft" and x["case_id"] == "policy01-over_limit")
reviewed_examples = [{
    "model": "full_sft", "case_id": "policy01-over_limit",
    "raw_response": selected_raw,
    "raw_sha256": hashlib.sha256(selected_raw.encode()).hexdigest(),
    "review_status": "reviewed_same_text" if selected_raw == known_bad else "new_text_needs_review",
    "finding": "70,000원은 65,000원을 초과하지만 승인 불필요라고 답했습니다. ..." if ... else "...직접 검토하세요.",
}]
selection = {
    "candidate": "full_sft",
    "reason": f"같은 dev12에서 SFT의 형식 통과는 {sft_count}/12입니다. ...",
    "known_failures": [reviewed_examples[0]["finding"],
                       "검색은 두 팀의 현재 숙박 문서만 다루며, API의 형식 정상 응답도 업무 의미 검토가 필요합니다."],
    "deployment_ready": False,
}
```
**쉽게:**
- `known_bad`는 **제작자가 사람 눈으로 읽고 틀렸다고 판정한 원문**. 내 실행 원문이 이것과 **글자 하나까지 같을 때만** 그 판정을 재사용한다(`reviewed_same_text`). 다르면 "새 원문이니 직접 읽어라"(`new_text_needs_review`)로 남긴다. 사람 판정을 새 출력에 자동으로 덮어씌우지 않으려는 장치.
  - 수업자료(L4)의 full_sft over_limit 원문은 `known_bad`와 **같다** → `reviewed_same_text`.
- 후보는 `full_sft`로 **코드에 고정**된다. 하지만 `deployment_ready: False`. **"8장에서 최종 시험 볼 후보"이지 "배포 승인"이 아니다.**
- 알려진 실패를 지우지 않고 **함께 넘긴다.** 다음 사람이 같은 실수를 "새 발견"으로 착각하지 않게.

#### 결과 파일 저장 (셀 21)

| 파일 | 내용 | 한마디 |
|---|---|---|
| `evaluation_report.json` | 60개 원문 · 관문 결과 · 요약 · 첫 실패 · 검토 기준 · API 예시 · 검색 목록 · 선정 | 채점 기록 전부 |
| `candidate_manifest.json` | 후보 · 입력 지문 3개 · 생성 설정 · 정밀도 · 선정 이유 · 알려진 실패 · `deployment_ready: False` · `test_used: False` | **후보 인수인계서** |

```python
for name, value in [("evaluation_report.json", evaluation_report),
                    ("candidate_manifest.json", candidate_manifest)]:
    Path(name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    assert json.loads(Path(name).read_text(encoding="utf-8")) == value   # 다시 읽어 같은지
del model; gc.collect(); torch.cuda.empty_cache()                         # GPU 메모리 정리
```
**쉽게:** 저장한 뒤 **다시 읽어서 같은지** 확인한다(6장 저장 · 재로딩과 같은 생각). 8장은 이 두 파일 + `training_data.zip` · `sft_model.zip` · `sft_report.json`, 총 **다섯 파일**에서 시작한다.

> **dev는 이미 여러 번 봤다.** 후보를 고른 데 쓴 dev 성과를 "새 데이터에서의 성능"이라고 말하지 않는다. 그래서 test는 후보와 생성 설정을 **고정한 뒤** 8장에서 처음 연다.

### 핵심 함수 한눈에

| 강 | 함수 · 코드 | 한 줄 |
|---|---|---|
| 준비 | `file_sha256` | 파일 지문, 1MB씩 읽기 |
| 7-1 | `check_dev_records` | dev 12문항 · 그룹 · 역할이 명세와 같은가 |
| 7-1 | `inspect_response` | JSON → 계약 → 인용 ID 세 관문 bool |
| 7-2 | `comparison` · `responses` | 문항 ID로 60개 정렬, 입력 · 설정 대조 |
| 7-2 | `summary` · `failure_counts` | 관문별 통과 수, 첫 실패만 세기 |
| 7-2 | `criteria_by_type` | 사람이 원문 읽을 때 묻는 질문 |
| 7-3 | `retrieve_documents` | 팀 필터 + 낱말 겹침, 없으면 빈 목록 |
| 7-3 | `generate_answer` | 대화 포장 → 생성 → 새 토큰만 · 잘림 여부 |
| 7-3 | `AnswerRequest` · `/answer` | 422 입구 검사 · 200/502 출구 검사 |
| 7-4 | `reviewed_examples` · `selection` | 알려진 실패 유지, 후보 고정, 배포 False |

---

## 질문과 새로 알게 된 점

### dev가 뭐지?
**dev = development(개발용) 데이터**, validation(검증) 데이터라고도 한다. 2장에서 만든 72문항은 **규정 그룹(팀) 단위로** 세 묶음으로 나뉘어 있다.

| 묶음 | 규정 그룹 | 문항 | 언제 쓰나 | 비유 |
|---|---|---|---|---|
| **train** | policy03 · 04 · 06 · 07 · 08 · 09 · 10 · 12 (8팀) | 48 | 학습할 때 (가중치를 고침) | 교과서 연습문제 |
| **dev** | policy01(가온) · policy05(마루) (2팀) | 12 | 개발 **중간에** 확인 · 방법 **비교** · 후보 고르기 | 모의고사 |
| **test** | policy02 · policy11 (2팀) | 12 | 모든 결정을 끝낸 뒤 **마지막에 한 번** (8장) | 수능 |

- 7장의 다섯 방법 비교(60개 답)와 full\_sft 후보 선정은 전부 **dev 12문항**으로 했다.
- 그런데 dev는 3~6장 내내 보면서 설정을 골랐다. 모의고사를 여러 번 보고 거기에 맞춰 공부법을 고르면 모의고사 점수는 실제보다 좋게 나올 수 있다. 그래서 **"dev 12/12"를 새 데이터 성능이라고 말하지 않고**, test는 후보 · 생성 설정을 고정한 뒤 8장에서 처음 연다(`test_used: False`, 노트북은 `test.jsonl`의 이름만 확인하고 내용을 안 읽음).
- train과 dev · test는 **팀 단위로** 나뉘어 있어서, 학습 때 한 번도 못 본 회사 규정에서도 판단하는지 볼 수 있다(2장 그룹 단위 분할).

### `inspect_response`에서 코드 펜스를 제거하려면 `result`를 어떻게 바꿔야 해?
**`result`는 그대로 둔다.** 펜스 때문에 떨어지는 곳은 `json.loads(raw)`라서, 바꿀 곳은 그 **전의 입력**이다. 벗기는 함수를 따로 두고 `inspect_response`는 엄격한 채로 두 번 채점한다.

```python
import re

FENCE = re.compile(r"\s*```(?:json)?\s*(.*?)\s*```\s*", re.S)

def strip_fence(raw):
    m = FENCE.fullmatch(raw)            # 답 전체가 ```json ... ``` 한 덩어리일 때만
    return (m.group(1), True) if m else (raw, False)

text, fence_removed = strip_fence(item["raw_response"])
responses.append({
    ...,
    "raw_response": item["raw_response"],                                   # 원문은 그대로 보관
    "format_checks": inspect_response(item["raw_response"], source_ids),    # 엄격 (교안 기준)
    "format_checks_unfenced": inspect_response(text, source_ids),           # 펜스 허용
    "fence_removed": fence_removed,                                         # 벗겼다는 사실도 기록
})
```
- 정규식: `\s*` 앞뒤 공백 무시 · `(?:json)?` "json"은 있어도 없어도 · `(.*?)` 가운데 내용 · `re.S`면 `.`이 줄바꿈까지 → 여러 줄 JSON도 잡힌다.
- **`result`에 `"fenced"` 키를 넣으면 안 되는 이유**
  - `all(item["format_checks"].values())`: 펜스 없는 정상 답도 `fenced=False` 때문에 형식 실패가 된다.
  - 셀 10 `next(key ... if not passed)`: `fenced`가 실패 단계로 잡힌다.
- `inspect_response` **안에서** 벗기는 것도 안 된다. 셀 7 `check_format_examples`의 "펜스로 감싼 답은 `json_object`에서 떨어져야 한다" assert가 깨진다.

**수업자료 보고서로 돌려 본 결과**

| 모델 | 엄격 형식 통과 | 펜스 있는 답 | 펜스 벗기면 |
|---|---|---|---|
| base | 0/12 | 9 | **9/12** |
| lora | 0/12 | 10 | **10/12** |
| qlora | 0/12 | 0 | 0/12 |
| dpo (2e-5) | 0/12 | 0 | 0/12 |

- base · lora는 JSON 내용은 대부분 맞았고 ```` ```json ```` 포장만 붙였다. 같은 "형식 실패"라도 **포장 문제**와 **내용 문제**는 고칠 곳이 다르다(포장은 프롬프트 · 후처리, 내용은 학습).
- 그래도 base 답은 "한도 이하는 불필요, 초과는 서면 승인"처럼 **규정만 되풀이**하고 질문 금액은 판단하지 않는다. 펜스를 벗겨도 업무 의미는 따로 봐야 한다.
- **교안이 안 벗기는 이유:** 시스템 프롬프트가 "JSON만 출력"을 요구했으니 펜스는 약속 위반. 벗겨서 통과시키면 약속을 지켰는지 측정이 안 되고, API를 받는 프로그램이 `json.loads`를 바로 하면 거기서 터진다. 벗긴다면 **엄격 · 펜스 허용 두 점수를 따로 보고**하고, `/answer`의 `"response": json.loads(...)`에도 벗긴 `text`를 넣어야 한다.

### 6장 `inspect_response`와 7장 `inspect_response`는 뭐가 달라?

| | 6장 | 7장 |
|---|---|---|
| 반환 | `format_ok` 하나 + `status` | 관문별 bool 3개 |
| 목적 | 과잉 보류 · 근거 없는 단정 세기 | **어느 관문에서** 떨어졌나 보기 |

---

## 통합 실습 `finetuning_ch07_practice.ipynb` TODO 1\~8

이전 장 파일 없이 train 48 · dev 12만으로 시작한다. 공개 모델의 dev 답(base)을 남기고, 제공 코드로 SFT를 24갱신한 뒤, 세 함수의 빈칸을 채워 **검사 → 검색 → API**를 직접 연결한다.

### (1) `inspect_response(raw, source_ids)`: 세 관문
```python
value = json.loads(raw)                                          # TODO 1: 원문 그대로 (펜스 안 벗김)
...
result["schema_ok"] = True                                       # TODO 2: 필드 · 상태-인용 규칙 통과 뒤
result["citation_ids_ok"] = set(citations).issubset(source_ids)  # TODO 3: 모든 인용이 제공 ID 안에
```
- TODO 2는 `True` 하나지만 **위치가 핵심**. 앞의 `if not valid_fields: return` · 상태-인용 `return`을 다 지나와야 이 줄에 닿는다. 즉 "여기까지 왔다 = 계약 통과".
- TODO 3의 `issubset`은 "인용한 ID **전부**가 준 문서 안에 있나". 하나라도 밖이면 False. 보류의 빈 `[]`는 항상 True.
- 자기 점검(`check_response_examples`): 정상 답 통과 · 제공 안 한 `D2` 인용 거절 · 펜스 붙은 답 `json_object` False · `status: []` 거절 → **"형식 검사 자기 점검 통과"**.

### (2) `retrieve_documents(question, team)`: 숙박 질문 · 팀 일치만
```python
lodging = any(term in question for term in ("숙박", "예약", "방"))   # TODO 4: 숙박 질문인가
if not lodging:
    return []
selected = [doc for doc in corpus if doc["team"] == team]            # TODO 5: 요청한 팀 문서만
return [{"id": doc["id"], "text": doc["text"]} for doc in selected]  # TODO 6: id · text만 전달
```
- corpus는 dev의 updated(개정판) 문서 2개: `('가온', 'policy01-v2')` · `('마루', 'policy05-v2')`. 팀 이름은 문서 첫 낱말에서 `text.split("팀", 1)[0]`으로 꺼낸다.
- **TODO 4를 `"숙박" in question` 하나로만 쓰면 안 된다.** 자기 점검("숙박 예약")은 통과하지만, 셀 22의 API 질문 "1박 80,000원인 **방**을 **예약**하려면…"에는 "숙박"이 없어서 **빈 목록 → 보류**가 된다. 수업 노트북처럼 "숙박 · 예약 · 방"을 같이 봐야 `policy01-v2`가 잡힌다.
- 반대로 "방"은 **"방법"**에도 들어 있다. "통신비 지원 방법"을 넣으면 `policy01-v2`가 나온다. 낱말 겹침 검색의 한계 → 검색 평가가 따로 필요.
- TODO 6에서 `team` 키를 빼는 이유: 모델 입력은 학습 때와 같은 모양(`id` · `text`)이어야 한다. 점검도 `set(...) == {"id", "text"}`로 확인한다.
- 자기 점검(`check_retrieval_cases`): 숙박 → 그 팀 문서 · 통신비 → `[]` · 없는팀 → `[]` · 키는 id · text만 → **"검색 자기 점검 통과"**.

### (3) `answer_question(question, team)`: 검색 결과로 실제 생성
```python
documents = retrieve_documents(question, team)   # TODO 7: 현재 질문 · 팀으로 검색
...                                              # row = system + user(question · documents JSON)
generated = generate(model, row)                 # TODO 8: 제공 생성 함수로 실제 SFT 응답
```
- `generate`는 `row["messages"][:2]`만 쓰고 정답 assistant는 없다. 생성 조건(greedy · `max_new_tokens=192` · `repetition_penalty=1.1`)은 함수 안에 고정이라 dev 비교와 같은 조건.
- 그다음은 제공 코드: `inspect_response`로 검사 → `ok = all(checks) and not length_limited` → `response`는 ok일 때만 파싱, `review_required: True`.
- `/answer`는 `answer_question` 결과의 `format_ok`로 **200 / 502**, `ValueError`(512토큰 초과)는 **422**, `AnswerRequest`(strict · extra forbid · 공백 정리)가 `123` · `" "` · `documents` 끼워 넣기를 **422**로 거절 → **"실제 생성 2건, 입력 거절 3건 확인"**.

### 수업 노트북과 다른 점

| | 수업 `evaluation_and_connection` | 통합 실습 |
|---|---|---|
| 모델 | 3장 `sft_model.zip` 복원 | 이 세션에서 SFT 24갱신 (`prepared_sft`) |
| 비교 | 보고서 5개 × dev 12 | base vs SFT × dev 12 |
| 검색 | 낱말 **겹친 수**로 정렬 · 1개 | 숙박 질문 여부 + 팀 일치 (제한된 규칙) |
| 생성 | `generate_answer(question, documents)` | `answer_question` 안에서 row를 만들어 `generate(model, row)` |
| 결과 | `evaluation_report.json` · `candidate_manifest.json` | `practice_result.json` (SFT 기록 · 요약 · dev 전후 · API 결과 · `test_used: False`) |

### 교훈
- 빈칸 8개 중 7개가 **한 줄**인데, 진짜 판단은 "어디에 두나"(TODO 2)와 "어떤 낱말로 거르나"(TODO 4)에 있다. 자기 점검을 통과해도 **실제 API 질문**에서 다시 확인해야 한다.
- 마지막 셀은 over\_limit의 실제 원문과 참조를 나란히 찍는다. 200 · 형식 통과여도 70,000원 vs 한도를 직접 읽는다.

---

## PPT 정리
- 7장 결과물: **`evaluation_report.json`(60개 원문 · 관문 결과 · 요약 · 첫 실패 · 검토 기준 · API 예시 · 검색 목록 · 선정)과 `candidate_manifest.json`(후보 인수인계서)**
  - 7-1 형식 통과와 업무 의미를 따로 채점한다 → 세 관문 True인 오답
  - 7-2 같은 문항 · 근거 · 설정으로 비교한다 → 60개 응답 · 원본 SFT 12/12
  - 7-3 검색 · 생성 · 검사를 API로 잇는다 → 200 두 건 중 판단 오류 한 건
  - 7-4 실패 칸을 나누고 후보를 고정한다 → full\_sft · 배포 승인 False
- 슬라이드 24 한 줄: **숫자 앞에는 출처, 뒤에는 원문.**
- 8장 전에: 보고서 2개 + SFT 입력 3개(`training_data.zip` · `sft_model.zip` · `sft_report.json`) 보관 — 8장은 이 다섯 파일에서 시작. 원문 하나를 골라 실패 칸(형식 · 검색 · 업무 판단) 적어 보기.

---

## 확인 문제

> 객관식 8 · 서술형 2. **정답 보기**를 누르면 열린다.

### FT7-Q1. 객관식 — 7장이 하지 않는 일
7장 노트북이 하지 **않는** 일은?
1. 앞 장 보고서의 지문을 대조한다
2. 다섯 결과의 dev 답을 다시 채점한다
3. 모델을 다시 학습한다
4. 3장 SFT를 API에 연결한다

<details>
<summary>정답 보기</summary>
<p><b>3.</b> 7장은 학습하지 않는다. 보고서에 저장된 답을 채점하고, 저장된 3장 SFT 가중치를 복원만 한다.</p>
</details>

### FT7-Q2. 객관식 — 지문
셀 5에서 보고서 지문이 모두 맞았다. 이것이 뜻하는 것은?
1. 보고서가 지금 올린 파일과 같은 파일로 만들어졌다
2. 보고서를 만든 학습 설정이 좋았다
3. 모델이 업무상 정답을 낸다
4. test 데이터로 검증이 끝났다

<details>
<summary>정답 보기</summary>
<p><b>1.</b> 지문은 "같은 파일"만 보장한다. lr 2e-5로 무너진 DPO 보고서도 지문은 통과한다.</p>
</details>

### FT7-Q3. 객관식 — 코드 펜스
`inspect_response`에서 ```` ```json {...} ``` ````처럼 코드 펜스로 감싼 답은 어떻게 되나?
1. 펜스를 벗겨서 세 관문을 다시 본다
2. `schema_ok`에서 떨어진다
3. `citation_ids_ok`에서 떨어진다
4. `json_object`에서 떨어진다

<details>
<summary>정답 보기</summary>
<p><b>4.</b> <code>json.loads</code>가 실패한다. 펜스를 벗기지 않는 건 "JSON만 출력"이라는 약속을 지켰는지 재는 검사이기 때문. 수업자료 base는 펜스 9개, lora는 10개가 여기서 떨어졌다.</p>
</details>

### FT7-Q4. 객관식 — 상태와 인용
`{"status": "abstained", "answer": "확인할 수 없습니다.", "citations": ["policy01-v1"]}`가 떨어지는 관문은?
1. `json_object`
2. `schema_ok`
3. `citation_ids_ok`
4. 통과한다

<details>
<summary>정답 보기</summary>
<p><b>2.</b> 보류(abstained)인데 인용이 있으면 상태와 인용의 짝이 안 맞아 계약 위반. 답했는데(answered) 인용이 없어도 마찬가지.</p>
</details>

### FT7-Q5. 객관식 — 첫 실패 단계
셀 10이 실패를 "첫 실패 단계 하나"만 세는 이유는?
1. 계산이 빠르기 때문에
2. 마지막 관문이 가장 중요하기 때문에
3. 앞 관문에서 떨어지면 뒤 관문은 자동으로 False라서, 다 세면 실패가 부풀려지기 때문에
4. 분모를 60으로 만들기 위해

<details>
<summary>정답 보기</summary>
<p><b>3.</b> JSON에서 떨어진 답은 계약 · 인용도 검사하지 않은 채 False. 이걸 실패 3개로 세면 안 된다. 그래서 모델별 합계가 항상 12.</p>
</details>

### FT7-Q6. 객관식 — 배포 승인
full\_sft가 형식 통과 12/12인데도 후보를 "배포 가능"으로 하지 않는 이유로 **가장** 알맞은 것은?
1. over\_limit에서 70,000원을 한도 이하라고 하는 등 업무 판단 오류가 있고, dev는 이미 여러 번 본 데이터라서
2. JSON 형식이 가끔 깨져서
3. LoRA보다 파일이 커서
4. API가 502를 반환해서

<details>
<summary>정답 보기</summary>
<p><b>1.</b> 형식 통과는 업무 정답이 아니다. 그리고 후보를 고르는 데 쓴 dev 성과는 일반화 성능이 아니라서 8장 test로 따로 확인한다.</p>
</details>

### FT7-Q7. 객관식 — 낱말 겹침 검색
수업 노트북의 `retrieve_documents("80,000원 숙소는 승인이 필요한가요?", "가온")` 결과는?
1. `policy01-v2`
2. `policy05-v2`
3. `policy01-v1`
4. 빈 목록

<details>
<summary>정답 보기</summary>
<p><b>4.</b> "숙박 · 예약 · 방" 중 질문에 들어간 낱말이 없다("숙소"는 목록에 없음). 낱말 겹침 검색은 동의어를 못 잡는다. 반대로 "통신비 지원 방법"은 "방"이 겹쳐서 숙박 문서가 나온다. 검색 품질 평가가 따로 필요한 이유.</p>
</details>

### FT7-Q8. 객관식 — `extra="forbid"`
`AnswerRequest`에 `extra="forbid"`를 둔 이유로 알맞은 것은?
1. 숫자를 문자열로 바꿔 받으려고
2. 요청자가 `documents` 같은 정의 안 된 필드로 근거를 끼워 넣는 것을 막으려고
3. 질문 길이를 500자로 제한하려고
4. 형식 실패를 502로 바꾸려고

<details>
<summary>정답 보기</summary>
<p><b>2.</b> 근거 문서는 서버의 검색이 고르는 것. 요청자가 임의 문서를 넣으면 모델 판단을 조작할 수 있다. 숫자 거절은 <code>strict</code>, 길이는 <code>Field</code>, 502는 출구 검사의 일.</p>
</details>

### FT7-Q9. 서술형 — 200인데 틀린 답
요청 1(숙박 80,000원)은 HTTP 200을 받았다. 그런데 "API가 제대로 답했다"고 말하면 안 되는 이유를 7장의 채점 기준으로 설명하세요.

<details>
<summary>정답 보기</summary>
<p>200은 ④ 출력 검사(JSON · 계약 · 인용 ID · 잘림 없음)를 통과했다는 뜻일 뿐이다. 검색은 개정 한도 75,000원 문서를 맞게 가져왔지만, 모델은 "80,000원은 한도 이하"라고 숫자 비교를 틀렸다. 형식 검사는 금액의 대소 관계나 승인 시점을 보지 못하니까, <code>review_required: True</code>처럼 업무 의미는 사람이 원문을 읽어 따로 판정해야 한다. 실패 칸으로는 "업무 판단" 실패.</p>
</details>

### FT7-Q10. 서술형 — dev와 test
7장이 dev 12문항으로 다섯 방법을 비교하고 후보를 골랐는데도 "새 데이터에서의 성능"이라고 말하지 않는 이유와, test는 언제 여는지 설명하세요.

<details>
<summary>정답 보기</summary>
<p>dev는 3~6장 내내 결과를 보면서 lr · 방법 · 설정을 고르는 데 쓴 <b>모의고사</b>다. 여러 번 보고 거기에 맞춰 고르면 dev 점수는 실제보다 좋게 나올 수 있어서, dev 성과는 "선택에 쓴 점수"일 뿐 일반화 성능이 아니다. 그래서 후보(full_sft)와 생성 설정을 <code>candidate_manifest.json</code>에 먼저 고정하고(<code>test_used: False</code>), 그다음 8장에서 처음 보는 팀(policy02 · policy11)의 test 12문항을 <b>한 번</b> 열어 최종 평가한다.</p>
</details>
