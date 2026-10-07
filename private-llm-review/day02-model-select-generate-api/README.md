# 2일차. 모델 선택 · 복원과 예측 · 생성 호출 · API

> 2026-10-07 학습 기록. 프로젝트 전 복습 수업 2일차(교안 05\~08)입니다. 1일차에 학습한 BERT checkpoint를 골라 복원하고, 문의 → 라벨 → 프롬프트 → LLM 답변 → 기록·비교 → 웹 API로 이어지는 흐름을 step05\~10까지 모두 실행했습니다. 실습·퀴즈를 직접 돌려 보고, 막힌 곳은 질문으로 풀었습니다.

## 학습 목표

- `selected.json`이 가중치가 아니라 **"누구의 어느 실험을 무슨 기준으로 골랐는지"** 를 기록한다는 점을 설명한다.
- `max(key=lambda …)`의 동점 처리(목록 앞 후보)와 `>` vs `>=` 차이를 실제 값으로 확인한다.
- checkpoint 복원 → 토큰화 → logits → softmax → label·confidence 흐름을 값으로 따라간다.
- `json.dumps`로 원문 경계를 표시해 프롬프트를 만들고, Ollama를 HTTP로 호출해 같은 모양의 결과를 받는다.
- FastAPI 서버(step10)의 입력 검사(422)·LLM 실패(502)·성공(200)을 구분한다.

## 실습 파일

| 교안 | 실행한 것 | 실습 상태 |
| --- | --- | --- |
| 05 | `step05_select_model.py` — lr2e5 / lr5e5 검증 F1 비교 → `selected.json` | ✅ 완료 |
| 05 | `step06_predict.py` — checkpoint 복원과 예측, 실습 1·3, 퀴즈 1-1·2-1 | ✅ 완료 (공통 문의 confidence 0.6360, 교안과 일치) |
| 06 | `step07_call_models.py` — Ollama 생성 호출, `practice06` 실습 1 | ✅ 완료 |
| 07 | `step08` 체인 연결, `practice07` 실습 1, `step10_serve_api.py` 코드 읽기와 실제 요청 | ✅ 완료 |
| 08 | `step09_compare.py` 기록과 비교, `practice08` | ✅ 완료 |

실습 코드는 수업에서 받은 키트(`project2-kit`)라 올리지 않고, 실행 결과와 이해한 내용만 기록합니다.

## 오늘 한 일 (육하원칙)

| 항목 | 내용 |
| --- | --- |
| 언제 | 2026-10-07 07:00\~18:00 |
| 어디서 | 노트북(RTX 5060), `project2-kit\project2-kit` |
| 무엇을 | step05(모델 선택) → step06(복원·예측) → step07(생성 호출) → step08(체인) → step09(기록·비교) → step10(API), practice06·07·08, 퀴즈 |
| 어떻게 | 파일 전체 코드를 먼저 보고 위에서부터 한 줄씩 읽기, 실행 결과를 교안 값과 대조 |
| 왜 | 어제 학습한 BERT를 실제 문의 → 라벨 → 답변 흐름에 연결하기 위해 |
| 결과 | 공통 문의 confidence 0.6360(교안과 일치), Ollama 생성 호출 성공, 실습 결과와 에러 원인 정리 |

## 2일차 파이프라인

```
selected.json ← step05: lr2e5 / lr5e5 validation F1 비교 (둘 다 1.0 → 앞 후보 lr2e5)
      ↓
step06: load_classifier() → checkpoint 복원 → predict_text() → label, confidence
      ↓
step08: apply_policy() → POLICIES[label] + 원문 → prompt
      ↓
step07: call_model(ollama | openai, prompt) → result (text, usage, error …)
      ↓
step10: FastAPI /generate, /compare  →  step09: 여러 번 호출해 results.jsonl 기록
```

## step별 핵심

### step05\_select\_model.py

- 모델을 열지 않고 `config.json`, `validation_metrics.json`만 읽는다(torch import 없음).
- 이름 해석: `"lr2e5"` → 내 실험(learner01), `"learner02/lr5e5"` → 다른 사람 실험.
- `run = learner_dir.parent / run_learner / run_name` : 한 칸 올라갔다가 내려와서 다른 사람 폴더도 같은 줄로 찾는다.
- 검사: 후보 2개 이상, 가중치 파일 존재, F1 0\~1, 라벨 순서 동일.
- `max(candidates, key=lambda c: c["validation_macro_f1"])` → 동점이면 **목록 앞 후보** = lr2e5.
- 결과는 `selected.json`: 가중치가 아니라 "누구의 어느 실험을 무슨 기준으로 골랐는지" 기록.

### step06\_predict.py

- `load_classifier()`: `selected.json` → `learner01\lr2e5` → `config.json` → checkpoint에서 토크나이저·모델 복원(`local_files_only=True`, CPU, `eval()`).
- 라벨 순서 확인: checkpoint의 `id2label`과 `config["labels"]`가 다르면 멈춘다.
- `predict_text()` 흐름

| 단계 | 코드 | 공통 문의 값 |
| --- | --- | --- |
| 자르기 전 토큰 수 | `tokenizer(text, truncation=False)` | 30 |
| 잘림 여부 | `30 > 192` | `truncated = False` |
| 점수 | `model(**features).logits` | `[1, 3]` |
| 확률 | `.softmax(dim=-1)[0]` | `[0.6360, 0.2531, 0.1109]` |
| 예측 | `argmax` → `labels[0]` | shipping |
| confidence | `probabilities[index]` | 0.6360 |

### step07\_call\_models.py

- `PROVIDER = "ollama"`(19줄) → 바꾸려면 `"openai"`로 직접 수정 후 같은 명령 실행.
- `build_prompt()`: 안내 기준 + 출력 형식 + `"사용자 입력: " + json.dumps(원문)` → **문자열 하나**.
- `call_ollama()`: `httpx`로 `127.0.0.1:11434/api/generate`에 HTTP 요청. `ollama run` 채팅 창은 필요 없고 **서버만 켜져 있으면 됨**.
- `call_model()`: 성공·실패 모두 같은 모양으로 반환. 실패하면 `error`에 예외 타입 이름만 남김.
- `valid_output()`: 필드(answer, next\_steps)와 타입만 검사. 내용은 사람이 읽는다.

### step10\_serve\_api.py

```
① uv run python steps/step10_serve_api.py
② 직접 실행했네 → main()
③ uvicorn.run → 서버 켜짐
④ lifespan: 분류 모델 읽어서 선반(app.state)에 올림
⑤ 손님 대기
    /health   → "ok"
    /generate → 검사 → 분류 → LLM 1개 → 200/502
    /compare  → 검사 → 분류 → LLM 2개 → 200/502
```

**입력 검사 클래스**

```python
class TextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_INPUT_CHARS)

    @field_validator("text")
    @classmethod
    def nonblank(cls, text):
        if not text.strip():
            raise ValueError("공백만 입력할 수 없습니다.")
        return text.strip()

class GenerateRequest(TextRequest):
    provider: Literal["ollama", "openai"] = "ollama"
```

| 규칙 | 코드 |
| --- | --- |
| 빈칸 ✕ | `min_length=1` |
| 너무 길면 ✕ | `max_length=...` |
| 띄어쓰기만 ✕ | `nonblank` |
| ollama/openai만 (기본 ollama) | `Literal[...] = "ollama"` |

- `(BaseModel)` = 기능 **물려받기(상속)** → `__init__` 자동 생성. `GenerateRequest(TextRequest)` = TextRequest 규칙 그대로 + provider 칸 추가.
- `"     "`은 5글자라 `min_length`는 통과 → `nonblank`에서 걸림 → 422.
- `cls` = 클래스 자체. 파이썬이 첫 칸에 **자동으로** 넣으므로 안 써도 자리는 있어야 한다. 약속상 일반 메서드는 `self`, `@classmethod`는 `cls`.

**lifespan과 /health**

```python
@asynccontextmanager
async def lifespan(app):
    classifier = load_classifier()
    app.state.chain = create_chain(classifier)
    yield

app = FastAPI(title="2차 프로젝트 단계별 API", lifespan=lifespan)

@app.get("/health")
def health():
    return {"status": "ok"}
```

- 모델 불러오기는 느리므로 요청마다가 아니라 **서버 켤 때 한 번만** 하고 `app.state`(서버의 선반)에 올려 둔다. `yield` = 준비 끝, 서버 돌려라.
- `/health`가 "ok"여도 **LLM이 잘 되는지는 모른다** (문 열린 것만 확인).

**/generate와 /compare**

```python
@app.post("/generate")
def generate(body: GenerateRequest, request: Request):
    prepared = request.app.state.chain.invoke(body.text)
    result = generate_prepared(prepared, body.provider)
    response = {"classification": prepared["classification"], "result": result}
    return JSONResponse(response, status_code=502 if result["error"] else 200)

@app.post("/compare")
def compare(body: TextRequest, request: Request):
    prepared = request.app.state.chain.invoke(body.text)
    result = compare_prepared(prepared)
    failed = any(row["error"] for row in result["results"])
    return JSONResponse(result, status_code=502 if failed else 200)
```

| | `/generate` | `/compare` |
| --- | --- | --- |
| 검사표 | `GenerateRequest` | `TextRequest` (provider 필요 없음) |
| LLM | 하나 | 둘 다 |
| 실패 판단 | 그 하나 실패 → 502 | **하나라도** 실패 → 502 (`any`) |

| 코드 | 의미 |
| --- | --- |
| 200 | 성공 (답이 맞는지, 잘렸는지는 따로 확인) |
| 422 | 사용자 입력이 잘못됨 — 함수 실행 **전**에 요청 모델 검사에서 나옴 |
| 502 | 서버는 괜찮은데 뒤쪽 LLM이 실패 |

- `/compare`는 분류를 **한 번만** 하고 같은 프롬프트를 두 LLM이 공유 → **같은 조건에서 비교**.
- `/docs` = FastAPI가 자동으로 만드는 테스트 화면. `access_log=False` = 요청마다 터미널 기록 안 찍기.
- `if __name__ == "__main__":` → 직접 실행할 때만 서버가 켜지고, import만 했을 때는 켜지지 않는 **안전장치**.

## 실습·퀴즈 결과

### 05 실습 1. 동점에서 남는 epoch

| scores | 조건 | 남는 epoch |
| --- | --- | --- |
| `[0.78, 0.94, 0.91]` | `>` | 2 |
| `[0.78, 0.94, 0.94]` | `>` | 2 (먼저 도달) |
| `[0.78, 0.94, 0.94]` | `>=` | 3 (나중에 덮어씀) |

### 05 퀴즈 1-1. max()로 후보 고르기

- 출력: `lr2e5` / `dict` / `lr5e5`
- key 없이 `max(candidates)` → `TypeError: '>' not supported between instances of 'dict' and 'dict'`
- 동점이면 순서만으로 결과가 바뀌므로 **점수 + 동점 처리 기준**을 함께 기록해야 한다.

### 05 실습 3. 같은 모델에 입력만 바꾸어 예측

| 문장 | label | confidence | truncated |
| --- | --- | --- | --- |
| 공통 문의 | shipping | 0.6360 | false |
| 새 문의 ("알려주세요", 띄어쓰기 없음) | shipping | 0.7210 | false |

- 교안 새 문의(`알려 주세요`)는 0.7126 → **띄어쓰기 한 칸만 달라도 토큰이 달라져 점수가 바뀐다.**
- 라벨이 같아도 confidence는 다르다. confidence ≠ 정답 확률.

### 06 practice06 실습 1

```
프롬프트의 입력: "배송 상태가\"준비 중\"입니다.\n확인 방법을 알려 주세요."
원문 복원: True
```

- `json.dumps`가 원문 경계를 `"`로 표시하고, 속 따옴표는 `\"`, 줄바꿈은 `\n`으로 바꾼다.
- `json.loads`로 되돌리면 원문과 같다(True).

### 07 practice07 실습 1. TEXT 양끝 공백 두 칸

| 출력 | 결과 | 이유 |
| --- | --- | --- |
| 저장된 예측 라벨 | shipping | 파일에 저장된 기록이라 TEXT와 무관 |
| 정리한 원문 | 양끝 공백 없음 | `TEXT.strip()` |
| 원문이 프롬프트에 포함 | True | |
| 요청 확인 | 공백 없는 원문, ollama | `TextRequest.nonblank`가 `strip()` |

### 07 퀴즈 2-2를 실제 서버로 요청 (requests)

| 요청 | 퀴즈(max 20) | 실제 step10(max 4000) |
| --- | --- | --- |
| `"  배송 문의  "` | OK `'배송 문의'` ollama | 200 |
| provider `"OpenAI"` | 422 literal\_error | 422 literal\_error |
| `"   "` | 422 value\_error | 422 value\_error |
| `"가" * 21` | 422 string\_too\_long | **200** (4000자 안) |
| text 없음 | 422 missing | 422 missing |

- 실제 서버 응답은 `{"classification": ..., "result": ...}` → `body.get("text")`는 None.
- 422는 함수 실행 **전**에 요청 모델 검사에서 나온다(분류·생성 비용 0).

## 오늘 만난 에러와 원인

| 에러 | 원인 | 해결 |
| --- | --- | --- |
| practice08 실행 시 퀴즈 출력이 먼저 나옴 | step06 맨 아래(`__main__` 밖)에 붙인 퀴즈 코드가 import 체인(practice08 → step09 → step06)으로 실행됨 | 퀴즈를 별도 파일(`quiz06.py`)로 옮김 |
| `FileNotFoundError: …\development01\results.jsonl` | step09\_compare.py를 실행하기 전에 practice08을 먼저 실행함 | 처음엔 14줄(final\_live01)로 대신 읽고, step09 실행 후 다시 확인 |
| practice07 `KeyError: 'classification'` | 퀴즈 함수 이름 오타 `aplly_policy` → import한 step08의 `apply_policy`가 대신 불림 | 퀴즈를 `quiz07.py`로 옮기고 이름 수정 |
| `TypeError: type list doesn't define __round__` | `round([값, 4])` | `round(값, 4)` |

**배운 점:** step 파일에는 퀴즈를 붙이지 않는다. `if __name__ == "__main__":` 밖의 코드는 **import될 때도 실행**된다.

## 질문과 새로 알게 된 점

**Q1. max 없이 for문으로 후보를 고르려면?**

```python
best = None
for c in candidates:
    if best is None or c["f1"] > best["f1"]:
        best = c
```

`>`면 동점일 때 먼저 나온 것(max와 같음), `>=`면 나중 것이 남는다.

**Q2. `c`가 뭐지?** for문이 후보 dict를 하나씩 꺼내 담는 변수 이름(candidate의 약자). 이름은 바꿔도 된다. lambda의 `c`도 "지금 보는 후보 하나".

**Q3. lambda에 반복문이 깔려 있나?** 아니다. lambda는 값 하나를 받아 값 하나를 돌려주는 작은 함수일 뿐. **반복은 max / min / sorted가 하고**, 원소마다 lambda를 한 번씩 부른다.

**Q4. confidence가 softmax 점수인가?** 그렇다. softmax 확률 중 **가장 큰 값**(고른 라벨의 확률). label은 그 위치, confidence는 그 값. 정답일 확률을 보장하지는 않는다.

**Q5. 퀴즈 2-1 `round([probs[index],4])` 에러?** 대괄호 때문에 list를 round에 넘김 → `TypeError`. `round(probs[index], 4)`로 고친다.

**Q6. find\_correct\_label 완성 (라벨 순서가 틀렸을 때 진짜 라벨 찾기)**

```python
def find_correct_label(index, correct_labels, wrong_labels):
    label = correct_labels[index]
    for wrong_index, wrong_label in enumerate(wrong_labels):
        if wrong_label == label:
            return label, wrong_index
    raise ValueError(f"{label}이(가) wrong_labels에 없습니다.")
```

- 처음 코드는 `for label in wrong_labels`로 같은 이름을 덮어써서 진짜 라벨이 사라지는 문제가 있었다.
- `wrong_labels.index(label)` 한 줄로도 같다.
- 섞기: `wrong = labels.copy()` → `random.shuffle(wrong)` (shuffle은 반환값 None).
- 섞여도 우연히 같은 자리가 남으면 이번 예측만 맞아 보인다 → step06은 라벨 목록 전체를 미리 비교해 막는다.

**Q7. step07을 실행해야 .env가 생기나?** 아니다. `.env`는 직접 만든다. `lesson_settings.py`의 `load_dotenv`는 있으면 읽고 없으면 넘어갈 뿐.

```powershell
Copy-Item .env.example .env
notepad .env        # OPENAI_API_KEY=키 입력 후 저장
```

**Q8. Ollama 관련 명령**

| 하고 싶은 것 | 명령 |
| --- | --- |
| 메모리에 올라간 모델 보기 | `ollama ps` |
| 모델만 내리기 | `ollama stop qwen3:4b-instruct-2507-q4_K_M` |
| 서버 끄기 | 트레이 아이콘 → Quit Ollama, 또는 `Stop-Process -Name "ollama*" -Force` |
| 채팅(`>>>`) 나가기 | `/bye` 또는 Ctrl+D (`bye`는 메시지로 보내짐) |
| 채팅 대화 기록 지우기 | `/clear` (채팅은 유지) |
| 화면 지우기 | 채팅 안 Ctrl+L, PowerShell에서 `cls` |

- `>>>`에서 입력한 `ollama stop`은 명령이 아니라 모델에게 보낸 질문이 됐다.
- 모델 답변 중 "실행 중 모델은 `ollama list`" 같은 틀린 설명도 있었다 → 실행 중은 `ollama ps`.

**Q9. step07의 `text`가 모델 답변인가?** 그렇다. `body["response"]`를 고치지 않고 담은 **문자열**. 안에 JSON이 들어 있어 `\"`로 보인다. `json.loads(result["text"])` → dict(answer, next\_steps).

- 형식은 통과했지만 "주문번호를 통해서만 조회할 수 있다"는 프롬프트에 없는 단정 → 내용은 사람이 판단.

**Q10. Ollama와 OpenAI 비용 차이?**

- Ollama: 내 컴퓨터에서 실행, API 요금 없음.
- OpenAI(gpt-6-luna): 입력 100만 토큰당 $0.10, 출력 $0.50 ([LLM Gateway](https://llmgateway.io/models/gpt-6-luna)) → 입력 238 + 출력 107토큰 기준 약 $0.00008.

**Q11. practice07의 TEXT가 inquiries인가?** 아니다. `TEXT`는 15줄의 문장 변수, `inquiries`는 데이터 종류 이름(폴더 이름).

**Q12. `/`가 주소인가?** `/`는 첫 화면 주소. 다른 페이지는 `/login`, `/health`처럼 `/` 뒤에 이름을 붙인다. 앞부분(`http://127.0.0.1:8000`)은 어느 서버로, 뒷부분은 그 서버의 어느 함수로.

> 클래스·람다·데코레이터와 `@app.get("/")`의 기초는 [Python 보강 2장](../../python-basics/02-class-lambda-decorator/)에 따로 정리했습니다.

## 다음에 할 일

step05\~10은 모두 실행했어요. 남은 건 선택 실습과 정리예요.

- [ ] step06, practice07, practice08에 붙인 퀴즈 코드를 별도 파일로 정리
- [ ] practice06 실습 2(`payload["debug"] = True`), 실습 3(answer 바꾸기)
- [ ] practice07 실습 2(`LABEL_OVERRIDE = "refund"`)
- [ ] step08의 `prepared`, `result` 안에 정확히 뭐가 들어 있는지 출력해 보기
