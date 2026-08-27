# Chapter 9: Experiment Reproducibility and Checkpoints

> 2026-08-27 학습 기록. 9-1~9-5 이론과 기본 실습을 정리했습니다. 별도 심화 문제는 이번 기록에서 제외했으며 시간이 남을 때 진행합니다.

## Learning Goals

- Python, NumPy, PyTorch와 데이터 순서에 영향을 주는 seed를 함께 관리한다.
- 실험 설정과 epoch별 metric을 파일로 남겨 비교 가능한 실험을 만든다.
- `state_dict`와 checkpoint의 차이를 이해하고 저장·복원 흐름을 설명한다.
- 실험별 폴더에 config, metrics, checkpoint와 결과물을 모아 관리한다.
- seed 고정만으로 모든 환경에서 완전히 같은 결과가 보장되지는 않는다는 한계를 기록한다.

## Practice Files

| Lesson | File | Basic practice status |
| --- | --- | --- |
| 9-1 | `01-seed-reproducibility-basic.ipynb` | Python·NumPy·PyTorch seed와 모델 초기화 재현 확인 |
| 9-2 | `02-logging-design-basic.ipynb` | epoch log dictionary와 log list 누적 확인 |
| 9-3 | `03-state-dict-checkpoint-basic.ipynb` | `state_dict` key·shape 확인, key 수정 셀 재실행 예정 |
| 9-4 | `04-resume-training-basic.ipynb` | model·optimizer checkpoint 저장 및 복원 확인 |
| 9-5 | `05-experiment-directory-basic.ipynb` | 실험 폴더·JSON 흐름 확인, 경로 수정 셀 재실행 예정 |

9-3의 `model_State` 표기는 이후 코드와 이름을 일관되게 맞추기 위해 `model_state`로 수정했습니다. 9-5의 `make_exp_dir()`는 생성한 상세 경로를 `Path(root)`로 다시 덮어쓰던 줄을 제거했습니다. 두 수정 셀은 현재 환경에서 PyTorch를 실행할 수 없어 출력 재검증이 필요합니다.

## Core Theory

### 1. Seed and Reproducibility

재현성을 높이려면 하나의 seed만 적는 것으로 끝나지 않습니다. 다음 난수 흐름과 데이터 순서를 함께 관리해야 합니다.

- `random.seed(seed)`: Python 난수
- `np.random.seed(seed)`: NumPy 난수
- `torch.manual_seed(seed)`: PyTorch CPU 난수와 모델 초기화
- `torch.cuda.manual_seed_all(seed)`: CUDA 난수
- 별도 `torch.Generator`: `random_split`과 `DataLoader`의 shuffle 순서

같은 seed라도 PyTorch·CUDA 버전, 장치, 연산 종류와 실행 순서가 달라지면 결과가 완전히 같지 않을 수 있습니다. 따라서 코드와 seed뿐 아니라 실행 환경도 함께 기록합니다.

### 2. Logging Contract

`config.json`에는 실험 조건을, metric log에는 epoch별 결과를 남깁니다.

```text
config: data · model · optimizer · seed · environment
metrics: epoch · train loss/accuracy · valid loss/accuracy
checkpoint: model · optimizer · completed epoch · history
```

재개할 때는 checkpoint의 완료 epoch와 기존 metric log의 마지막 epoch가 같은지 먼저 확인하고 다음 epoch만 추가해야 중복 기록을 막을 수 있습니다.

### 3. `state_dict` and Checkpoint

- `model.state_dict()`: weight, bias와 등록된 buffer의 값
- `optimizer.state_dict()`: optimizer 설정과 Adam의 moving average 같은 내부 상태
- 추론용 저장: 모델 상태와 같은 모델 구조를 다시 만들 config
- 일반 학습 재개: model, optimizer, 완료 epoch, history, best metric과 config
- 완료 epoch 다음부터 정확히 재개: 위 항목에 난수 상태와 DataLoader generator 상태까지 추가

`state_dict`는 모델 구조 자체가 아니므로 같은 구조의 모델을 먼저 만든 뒤 `load_state_dict()`로 값을 주입해야 합니다.

### 4. Resume Boundary

이번 강의에서 정확한 재개란 모든 batch 처리와 history 기록이 끝난 epoch 경계에서 다음 epoch를 시작하는 경우입니다. epoch 중간에 중단되었다면 미완료 epoch를 처음부터 다시 실행합니다. seed를 다시 지정하는 것만으로는 저장 시점의 난수 상태로 돌아가지 않습니다.

### 5. Experiment Directory

한 실험의 설정과 결과는 하나의 run directory 안에서 연결합니다.

```text
runs/<timestamp>_<experiment>/
├── config.json
├── metrics.csv
├── checkpoints/
│   ├── last.pt
│   └── best.pt
└── plots/
    └── loss_curve.png
```

`last.pt`는 마지막 완료 epoch에서 재개하기 위한 상태이고, `best.pt`는 validation 기준으로 선택된 평가·추론용 상태입니다.

## Questions and Newly Learned Points

### Config and JSON

- `os.makedirs(path, exist_ok=True)`는 중간 폴더까지 만들며 기존 폴더가 있어도 오류를 내지 않는다.
- `os.path.join(a, b)`은 Windows와 Linux의 경로 구분자를 직접 하드코딩하지 않고 경로를 연결한다.
- `with open(path, "w", encoding="utf-8") as file:`은 블록이 끝나면 파일을 자동으로 닫는다.
- `json.dump(data, file)`은 열린 파일에 저장하고, `json.dumps(data)`는 JSON 문자열을 반환한다. 끝의 `s`를 string으로 기억한다.
- `indent=4`는 JSON을 네 칸 들여써 읽기 쉽게 만들 뿐 값에는 영향을 주지 않는다.
- `ensure_ascii=False`와 UTF-8 encoding을 함께 사용하면 한글을 `\uXXXX`가 아닌 원래 글자로 저장할 수 있다.
- 변수 이름은 숫자로 시작할 수 없다. `0json_text`가 아니라 `json_text`처럼 작성한다.
- `json_text[:80]`은 JSON 문자열의 처음 80글자만 미리 확인하는 slicing이다.

### File Modes and Logging

- `w`: 기존 내용을 지우고 새로 작성
- `a`: 기존 내용을 유지하고 파일 끝에 추가
- `r`: 읽기 전용

완성된 config는 보통 `w`로 저장하고, epoch가 끝날 때마다 한 줄씩 누적하는 log는 `a`를 사용할 수 있습니다.

### Function Call Flow

`make_epoch_log(2, 0.812345, 0.923456, 0.73456)`의 네 값은 함수 parameter에 순서대로 전달됩니다. 함수가 dictionary를 `return`하고, 바깥의 `print()`가 반환된 dictionary를 화면에 출력합니다.

### Loading a Checkpoint

- `torch.load(path, map_location="cpu")`: checkpoint 파일을 Python dictionary로 읽는다.
- `model.load_state_dict(checkpoint["model_state"])`: 읽은 parameter 값을 실제 모델에 주입한다.
- `optimizer.load_state_dict(checkpoint["optimizer_state"])`: optimizer 내부 상태를 복원한다.
- `map_location="cpu"`: GPU에서 저장된 Tensor도 GPU가 없는 환경에서 CPU로 읽게 한다.
- `strict=True`: model과 state dictionary의 key가 정확히 맞아야 한다.
- `strict=False`: 맞는 key만 불러올 수 있지만 누락을 숨길 수 있으므로 결과를 확인해야 한다.

### Files, Directories, and the `make_exp_dir` Bug

- `Path(path).unlink(missing_ok=True)`는 파일 하나를 삭제한다.
- `shutil.rmtree(path, ignore_errors=True)`는 하위 내용을 포함한 폴더 전체를 삭제한다.
- `Path(root) / f"{exp_name}_seed{seed}"`는 `pathlib` 방식의 안전한 경로 결합이다.
- 생성한 상세 경로 뒤에 다시 `path = Path(root)`를 대입하면 반환값이 상위 `runs`로 바뀐다. 생성한 경로를 그대로 `return path`해야 한다.

## Chapter 10 Status

10-1 학습 곡선 해석과 10-2 Overfitting·Underfitting 진단은 건강 문제로 오늘 진행하지 못했습니다. 완료로 표시하지 않으며, 컨디션이 회복된 뒤 이론과 실습을 차례대로 확인합니다.

## Deferred Advanced Practice

9장 별도 심화 문제는 현재 필수 백로그로 두지 않습니다. 기본 흐름과 10장이 정리된 뒤 시간이 남을 때 진행합니다.

## Environment

```bash
pip install -r requirements.txt
```
