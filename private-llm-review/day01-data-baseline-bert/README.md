# 1일차. 데이터 점검 · 기준 모델 · BERT 분류기 학습

> 2026-10-06 학습 기록. 목요일 프로젝트 시작 전, 그동안 배운 내용을 `project2-kit`으로 다시 실행해 보는 복습 수업의 1일차(교안 09·01\~04)입니다. 환경을 준비하고 step01\~03(데이터 읽기·점검·기준 모델)과 step04(BERT 학습 2회)를 실행해, 교안 슬라이드의 값을 그대로 재현했습니다.

## 학습 목표

- `uv`로 Python 3.12 환경을 만들고, 터미널 위치·네트워크 문제를 원인부터 구분해 해결한다.
- step 파일이 앞 단계의 함수를 import해 이어지는 **파이프라인 구조**를 설명한다.
- 토큰화 → 배치 → logits → loss → backward → step 흐름을 실제 출력값으로 확인한다.
- gradient accumulation에서 loss를 나누는 이유와 `.grad`에 gradient가 쌓이는 방식을 설명한다.
- 검증 macro F1 기준으로 checkpoint를 저장하는 조건(`>` vs `>=`)과 동점 처리 규칙을 기록한다.

## 실습 파일

| 교안 | 실행한 것 | 실습 상태 |
| --- | --- | --- |
| 09 | 환경 준비 (`uv sync`, `check_environment.py`) | ✅ 완료 |
| 01 | `step01_read_data.py` — CSV·라벨 읽기 | ✅ 완료 |
| 02 | `step02_check_data.py` — 데이터 점검 5가지 | ✅ 완료 |
| 03 | `step03_train_baseline.py` — TF-IDF + 로지스틱 기준 모델 (macro F1 1.0) | ✅ 완료 |
| 04 | `practice04` 관찰, `step04_train_classifier.py` BERT 학습 2회 (lr2e5, lr5e5) | ✅ 완료 (교안 값과 일치) |
| 퀴즈 | 2-1 \~ 3-2 | ✅ 완료 |

실습 코드는 수업에서 받은 키트(`project2-kit`)라 올리지 않고, 실행 결과와 이해한 내용만 기록합니다.

## 오늘 한 일 (육하원칙)

오늘 1일차 Review(09·01\~04)를 직접 실행했어요. BERT 두 실험(lr2e5, lr5e5)을 학습해서 checkpoint까지 만들었어요.

| 항목 | 내용 |
| --- | --- |
| 언제 | 2026-10-06 10:00\~16:50 |
| 어디서 | 노트북(RTX 5060 Laptop GPU), `project2-kit\project2-kit` |
| 무엇을 | 환경 준비 → step01\~03 실행 → practice04 관찰 → step04 BERT 학습 2회 → 퀴즈 2-1\~3-2 |
| 어떻게 | 실행 결과를 교안 슬라이드 값과 하나씩 대조하고, 막히는 개념은 작은 숫자 예시로 다시 계산 |
| 왜 | 1일차 결과물(baseline, lr2e5, lr5e5 폴더)이 2일차 05\~08의 입력이라서 |
| 결과 | 교안과 같은 값 재현: lr2e5 F1 0.7827→0.9722→1.0, lr5e5 F1 0.9441→1.0→1.0 |

가장 오래 붙잡은 개념은 gradient accumulation이에요. "왜 loss를 4로 나누나", "어디에 모이나", "배치 1이면 안 되나"를 차례로 물어보면서 정리했어요.

## 환경 준비와 트러블슈팅

막힌 원인은 대부분 **터미널 위치**와 **네트워크**였어요. 코드 문제는 없었어요.

| 증상 | 원인 | 해결 |
| --- | --- | --- |
| `can't open file ...steps\check_environment.py`, Python 3.11 실행 | 압축을 풀면서 폴더가 한 겹 더 생김. `pyproject.toml`을 못 찾아 기본 Python으로 실행됨 | `cd project2-kit`로 한 칸 더 들어가기. 정상 위치 = `...\project2-kit\project2-kit` |
| `uv sync`: `No pyproject.toml found` | 위와 같은 원인 | 같은 해결 |
| `Failed to download pydantic ... network timeout (30s)` | 수업 와이파이에서 다운로드가 30초를 넘김 | `$env:UV_HTTP_TIMEOUT = "300"`, `$env:UV_CONCURRENT_DOWNLOADS = "2"` 후 `uv sync --frozen` 다시 실행 |
| step03: `FileExistsError: 기준 모델이 이미 있습니다` | 이미 한 번 학습해서 결과 폴더가 있음. 덮어쓰지 않으려는 안전장치 | 고장 아님. 다시 하려면 폴더를 지우지 말고 `Rename-Item`으로 이름만 바꾸기 |
| practice04: `symlinks ... not support`, `hf_xet not installed` | 윈도우 캐시 방식 안내, 다운로드 도구 안내 | 무시해도 됨 |
| `newly initialized: ['classifier.bias', 'classifier.weight']` | 분류층(768→3)을 새로 만들었다는 안내 | 정상 |

Traceback은 **맨 아랫줄부터** 읽어요. 맨 아랫줄이 진짜 원인이에요.

### check\_environment.py 결과

- Python 3.12.13, torch 2.11.0+cu128, GPU 사용 가능: True (RTX 5060 Laptop GPU), `.venv` 경로 정상
- `OpenAI 키 설정: False` → 2일차 06 전까지 `.env` 필요
- Ollama 모델이 `qwen3.6:35b`만 있음 → 교안 모델 `qwen3:4b-instruct-2507-q4_K_M` 필요

### 자주 쓴 명령

```powershell
pwd                                        # 현재 위치 확인
uv run python steps\step01_read_data.py   # step 파일 실행
Get-Content <파일 경로>                    # 결과 파일 내용 보기
ollama stop <모델 이름>                    # BERT 학습 전 GPU 비우기
```

## step 파일 파이프라인 구조

practice 파일은 개념을 보여 주는 연습용이고, **실제 파이프라인은 step 파일**이에요. 뒤 step이 앞 step의 함수를 import해서 그대로 다시 써요.

| 파일 | 만드는 함수 | 다음 단계로 넘기는 것 |
| --- | --- | --- |
| step01\_read\_data.py | `read_rows`(CSV → list\[dict\]), `read_labels`(labels.json → 라벨 순서) | 180행, 라벨 순서 |
| step02\_check\_data.py | `check_splits`: 빈 값·라벨·id 중복·상황별 라벨·분할 간 중복 5가지 검사 | 검사 통과(겹침 0) |
| step03\_train\_baseline.py | `train_baseline`: 읽기(01) → 검사(02) → TF-IDF + 로지스틱 → 평가 → 저장 | `baseline/` (macro F1 1.0) |
| step04\_train\_classifier.py | `run_training`: 읽기(01) → 검사(02) → BERT 학습 → epoch마다 검증 → 조건부 저장 | `lr2e5/`, `lr5e5/` checkpoint |

### 경로 계산: ROOT와 DATA\_DIR

```python
# lesson_settings.py
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / DATASET        # DATASET = "inquiries"
```

| 단계 | 값 |
| --- | --- |
| `__file__` + `.resolve()` | `project2-kit\project2-kit\steps\lesson_settings.py` |
| `.parents[0]` | `...\project2-kit\project2-kit\steps` |
| `.parents[1]` = ROOT | `project2-kit\project2-kit` |
| `ROOT / "data" / "inquiries"` = DATA\_DIR | `...\project2-kit\project2-kit\data\inquiries` |
| `DATA_DIR / "train.csv"` | `...\data\inquiries\train.csv` |

- `Path` 사이의 `/`는 나눗셈이 아니라 "폴더 안으로 들어가기"예요.
- 터미널 위치가 아니라 **파일 자신의 위치**를 기준으로 계산해서, 어디서 실행해도 같은 데이터 폴더를 찾아요.
- `DATASET`, `LEARNER`를 한 곳에서만 정해서 step01\~11이 모두 같은 값을 써요.

### read\_rows 핵심

- `csv.DictReader`가 첫 줄을 키로 써서 각 행을 dict로 바꿔요. **모든 값은 문자열**이에요.
- `split(",")` 대신 csv 모듈을 쓰는 이유: 본문 안 쉼표(따옴표 안)를 문장의 일부로 알아봐요.
- `encoding="utf-8-sig"`는 엑셀이 붙이는 BOM 문자를 제거해요. `with`는 파일을 자동으로 닫아요.

## 04 BERT 실습 결과

모든 출력이 교안 슬라이드의 값과 같았어요. lr2e5는 3번째 epoch, lr5e5는 2번째 epoch가 저장됐어요.

### practice04 출력의 뜻 (PREVIEW\_ROWS = 2 → 1)

`PREVIEW_ROWS`는 train.csv 180행 중 관찰에 쓸 앞쪽 행 수예요(`[:PREVIEW_ROWS]`). 학습은 하지 않고 모양만 봐요.

| 출력 | 2문장 | 1문장 | 뜻 |
| --- | --- | --- | --- |
| 앞 여섯 토큰 | `[CLS] 주문 ##한 지 사흘 ##이` | 같음 | `##` = 앞 토큰에 붙는 조각 |
| 앞 여섯 번호 | `[2, 4867, 2470, 1583, 9229, 2052]` | 같음 | 어휘 사전 번호. 정답 라벨과 무관 |
| 토큰 길이 | `[30, 21]` | `[30]` | padding 전 문장별 토큰 수 |
| 배치 크기 input\_ids | `[2, 32]` | `[1, 32]` | 문장 수 × 칸 수. 30을 8의 배수로 올려 32 |
| labels 크기 | `[2]` | `[1]` | 문장마다 정답 1개 |
| 정답 번호 | `[0, 0]` | `[0]` | 0 = shipping |
| 초기 BERT logits | `[2, 3]` | `[1, 3]` | 문장 수 × 라벨 3개 |
| 초기 BERT loss | 1.3402 | 1.3798 | 문장별 −ln(정답 확률)의 평균 |
| backward / step 직후 가중치 변경 | False / True | 같음 | 가중치는 step에서 바뀜 |
| 작은 층 logits와 정답 | `[2, 3] [2]` | 같음 | CSV와 무관한 고정 2행 입력 |

loss가 바뀐 이유: 1번 문장의 정답 확률 약 0.2516 → −ln = 1.3798, 2번 문장 약 0.2724 → 1.3006. 두 값의 평균이 1.3402예요.

### step04 학습 기록

| 실험 | epoch 1 F1 | epoch 2 F1 | epoch 3 F1 | 마지막 train\_loss | 저장 epoch | optimizer\_steps\_at\_checkpoint |
| --- | --- | --- | --- | --- | --- | --- |
| lr2e5 | 0.7827 | 0.9722 | 1.0 | 0.3030 | 3 | 36 |
| lr5e5 | 0.9441 | 1.0 | 1.0 | 0.0242 | 2 | 24 |

- 저장 조건은 `if metrics["macro_f1"] > best_score:`(211줄)예요. 저장할 때마다 덮어써서 마지막 저장본 하나만 남아요.
- lr5e5의 3번째 epoch는 `1.0 > 1.0` = False라서 저장하지 않았어요.
- 저장 epoch × 12(epoch당 갱신 수) = optimizer\_steps인지로 교차 확인해요.

### 퀴즈 답

| 퀴즈 | 답 |
| --- | --- |
| 2-1 경사하강 (lr 0.1) | `0 -4.0 0.4` / `1 -3.2 0.72` / `2 -2.56 0.976` → 계속 반복하면 **2로 수렴** |
| 2-1 lr = 1 | 4 → 0 → 4 … 진동, **수렴 안 함**. 2까지 거리에 (1 − 2·lr) = −1이 곱해져서 거리는 그대로, 부호만 바뀜 |
| 2-2 zero\_grad 누락 | `0 3.0` / `1 6.0` / `zero 뒤: 3.0`. backward는 `.grad`에 **더해요** |
| 3-1 갱신 횟수 | `45 12 36`. BATCH\_SIZE 8이면 23, 6, 18 (올림 두 번) |
| 3-2 `>` vs `>=` | `lr5e5 2 1.0` / `lr2e5 3 1.0`. `>=`면 lr5e5는 3 |

동점 epoch 선택(3-2 ③)에는 정답이 하나로 정해져 있지 않아요. epoch 2는 더 적은 학습(24번 갱신)으로 같은 점수를 얻었고, epoch 3은 validation\_loss가 더 낮아요(0.0387 → 0.0166). 두 경우 모두 **어떤 규칙으로 골랐는지 기록하는 것**이 핵심이에요.

## 학습 루프 한 줄씩 (step04 174\~197줄)

배치마다 ① 계산 → ② `.grad`에 더하기를 하고, 4배치마다 ③ 가중치 변경 → ④ `.grad` 비우기를 해요. 교안 슬라이드에서 빠진 줄(window\_size, 기록용 세 줄)도 포함했어요.

| 코드 | 하는 일 |
| --- | --- |
| `for epoch in range(1, epochs + 1):` | 1, 2, 3. 1 epoch = train 180문장을 한 번 다 읽기 |
| `model.train()` | 학습 모드(Dropout 켬). epoch 끝의 검증이 `eval()`로 바꾸므로 매 epoch 되돌림 |
| `optimizer.zero_grad(set_to_none=True)` | epoch 시작 때 `.grad`를 비움(None) |
| `for index, batch in enumerate(train_loader):` | 45배치, index 0\~44. 매 epoch 순서를 섞음 |
| `batch = {k: v.to(device) ...}` | 텐서 4개를 GPU로 옮김 |
| `window_start`, `window_size` | 이번 묶음의 배치 수. index 0\~43은 4, 마지막 index 44는 1 |
| `with torch.autocast(...)` | 16비트(bfloat16)로 계산해 메모리 절약. CPU에서는 꺼짐 |
| `output = model(**batch)` ① | dict를 인자로 펼침. logits `[4, 3]` + 배치 평균 loss. 가중치 그대로 |
| `loss = output.loss / window_size` | 합이 평균이 되도록 미리 나눔 |
| `scaler.scale(loss).backward()` ② | gradient를 각 가중치의 `.grad`에 **더함**. RTX 5060은 bfloat16이라 scaler가 꺼져 있어 `loss.backward()`와 같음 |
| `batch_count`, `total_train_loss`, `count` | 기록용. epoch 끝 `train_loss` = 합 ÷ 180 |
| `if (index + 1) % 4 == 0 or 마지막:` | `%`는 나머지. 4번째 배치이거나 마지막 배치일 때만 아래 실행 |
| `scaler.step(optimizer)` ③ | 모인 `.grad`를 읽어 **가중치를 실제로 바꿈** |
| `optimizer.zero_grad(...)` ④ | step 직후에만 비움 |
| `updates += 1` | epoch당 12번, 총 36번 |

`if` 블록 안의 `unscale_`, `clip_grad_norm_`, `scheduler.step()`은 아직 자세히 설명하지 않았어요(다음에 할 일).

### gradient를 모아 두는 곳: 각 가중치의 `.grad`

- 모으는 것은 가중치가 아니라 gradient예요.
- 가중치 텐서마다 같은 모양의 `.grad` 칸이 붙어 있어요. 예: `classifier.weight [3, 768]` ↔ `.grad [3, 768]`
- optimizer는 `AdamW(model.parameters(), ...)`로 가중치 목록을 받아 두어서, `step()`과 `zero_grad()`가 같은 `.grad` 칸을 읽고 비워요.

### 4배치 모으기 (배치마다 grad가 3이라고 할 때)

| 순서 | 동작 | `.grad` |
| --- | --- | --- |
| 배치 1 | backward | 3 |
| 배치 2 | backward | 6 |
| 배치 3 | backward | 9 |
| 배치 4 | backward | 12 |
|  | step → zero\_grad | 0 |

배치마다 zero\_grad를 하면 앞 배치 값이 지워져서 마지막 배치만 반영돼요. 그래서 4배치 사이에는 **비우지 않는 것**이 모으는 방법이에요.

## 질문과 새로 알게 된 점

오늘 직접 물어본 질문을 순서대로 정리했어요. 가장 큰 배움은 "gradient는 step 전까지만 모으고, 모을 때는 평균이 되도록 나눈다"예요.

**Q1. `DATA_DIR`이 왜 `...\project2-kit\data\inquiries`가 되나?** `lesson_settings.py` 위치에서 상위 폴더로 두 번 올라간 곳이 ROOT이고, 거기에 `data`, `inquiries`를 붙인 거예요. `/`는 나눗셈이 아니라 폴더 안으로 들어가기예요.

**Q2. practice와 step 중 무엇을 공부해야 하나?** step이 실제 파이프라인이에요. step03이 step01·02의 함수를 import해서 써요. practice는 중간값을 눈으로 확인하는 연습용이에요.

**Q3. `grad = 2*(w - 2)`에서 왜 `(w - 2)`가 나오나?** L(w) = (w − 2)²를 미분하면 2(w − 2)예요(전개: w² − 4w + 4 → 2w − 4). w = 0에서 −4. 부호는 갈 방향, 크기는 목표까지의 거리를 알려 줘요.

**Q4. 2(w − 2)를 만들려고 임의로 (w − 2)²를 정한 건가?** 순서가 반대예요. 손실 함수 (w − 2)²를 설명용으로 먼저 골랐고, 2(w − 2)는 그 미분 결과예요. 최솟값(w = 2)을 알고 손으로 계산할 수 있어서 골랐어요.

**Q5. gradient가 축적돼도 되나?** step 전까지는 돼요. 같은 가중치에서 구한 gradient의 합 = 큰 배치 하나의 gradient예요(합의 미분 = 미분의 합). step 뒤까지 남기면 옛 위치의 gradient가 섞여서, lr 0.1 예시에서 w가 2를 지나 4까지 달려가고 출렁여요.

**Q6. 배치마다 zero\_grad를 하고 4개를 모아 step하나?** 아니에요. 4배치 사이에는 zero\_grad를 하지 않아요. 따로 모아 두는 상자가 없고, `.grad` 한 칸이 곧 모으는 상자예요.

**Q7. 가중치를 모아 놓는 곳이 어디인가?** 모으는 건 gradient이고, 각 가중치의 `.grad` 속성에 쌓여요. `backward()`가 자동으로 더하고, optimizer가 같은 칸을 읽어요.

**Q8. 네 배치 평균 loss 1.00이 기준이 되나?** 결과는 같아요. 다만 optimizer가 보는 건 loss 값이 아니라 gradient예요. 조각(0.30, 0.25, 0.20, 0.25)별 gradient를 더하면 평균 loss 1.00의 gradient와 같아져요. 예: 정답 1, 2, 3, 2, w = 0 → 조각 합 −4.0 = 평균 loss의 gradient −4.0.

**Q9. 왜 네 loss를 다 더해 평균을 만든 뒤 backward 한 번 하지 않나?** forward를 하면 계산 기록이 GPU 메모리에 남고 backward를 해야 풀려요. 다 더한 뒤 한 번에 하면 배치 4개분(16문장) 메모리가 필요해서 누적하는 의미가 없어져요. 그래서 조각마다 바로 backward하고, 미리 ÷4 해 둡니다.

**Q10. ÷4 없이 1.2, 1.0, 0.8, 1.0 그대로 하면 안 되나?** 돌아는 가지만 loss 크기가 gradient 크기를 그대로 정해요. `.grad`에 "합 4.0"의 gradient가 쌓여서 보폭이 4배가 돼요. 학습률 2e-5를 몰래 8e-5로 올린 것과 같아요. 마지막 묶음(배치 1개)과 크기도 달라져요.

**Q11. ÷4를 안 하면 16문장 배치 하나의 ×4가 되나?** 네. `output.loss`는 배치 평균이라 네 평균을 더하면 4 × (16문장 평균)이에요. 참고로 `/`는 나누기, `%`는 나머지예요.

**Q12. 배치 크기를 늘리면 메모리가 늘면, 애초에 1로 하면 되지 않나?** 가능하지만 느려요. GPU는 문장 1개든 4개든 한 번 호출 시간이 비슷해요. 1 × 16은 4 × 4보다 메모리는 줄지만 호출이 4배(갱신당 4번 → 16번)라 시간이 늘어요. gradient는 같아요.

| 조합 | GPU에 한 번에 올라가는 문장 | 갱신당 모델 호출 | gradient |
| --- | --- | --- | --- |
| 16 × 1 | 16 | 1 | 16문장 평균 |
| 4 × 4 (kit 설정) | 4 | 4 | 16문장 평균 |
| 1 × 16 | 1 | 16 | 16문장 평균 |

메모리가 허락하는 만큼 배치를 키우고, 부족한 만큼 accumulation으로 채워요.

**Q13. BATCH\_SIZE 8이면 갱신이 어떻게 되나?** 배치 23, epoch당 갱신 6, 총 18로 모두 줄어요. 갱신 1번이 보는 문장은 32개로 늘어서 방향은 안정적이지만, 같은 epoch에서 덜 학습될 수 있어요.

## 다음에 할 일

2일차 06을 실행하려면 Ollama 4b 모델과 `.env`가 먼저 있어야 해요.

- [ ] `ollama pull qwen3:4b-instruct-2507-q4_K_M` 후 `ollama list`로 확인
- [ ] `Copy-Item .env.example .env` → `OPENAI_API_KEY` 입력 → `check_environment.py`에서 `True` 확인
- [ ] 학습 루프 `if` 블록 설명 듣기: `unscale_`, `clip_grad_norm_`, `scheduler.step()`(warmup)
- [ ] step01 ③ `read_labels`, ④ `main`과 `__main__` 이어서 읽기
- [ ] step02 `check_splits`, step03 `train_baseline` 한 줄씩 읽기
- [ ] 2일차 05: `step05_select_model.py`로 `selected.json` 만들기 (lr2e5와 lr5e5가 모두 F1 1.0이라 동점 처리 규칙을 확인)
