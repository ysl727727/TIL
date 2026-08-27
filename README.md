# TIL: Private LLM Engineer Journey

> Deep Learning Chapter 9까지의 실제 파일 구조와 학습 상태를 2026-08-27 기준으로 갱신했습니다.

KANT Private LLM 엔지니어 교육과정에서 학습하고 직접 실험한 내용을 기록하는 저장소입니다.
강의 원문을 옮기기보다 무엇을 이해했고, 코드로 무엇을 검증했으며,
결과에서 어떤 결론을 얻었는지를 중심으로 정리합니다.

## Current Status

- 과정: KANT Private LLM 엔지니어 교육과정
- 현재 단계: Deep Learning Foundations
- 현재 주제: 실험 재현성, logging, `state_dict`, checkpoint와 학습 재개
- 최근 진행: 9-1~9-5 이론·기본 실습 정리, 수정 셀 2개 재실행 예정
- 복습 예정: 10-1 학습 곡선과 10-2 Overfitting·Underfitting 진단
- 목표: 평가와 운영까지 고려하는 LLM 엔지니어

## Deep Learning Contents

| Chapter | Topics | Status |
| --- | --- | --- |
| 1 | ML과 DL, 학습 흐름, 문제 입출력, PyTorch 코드 읽기 | Completed |
| 2 | Tensor dtype·shape·broadcasting, CPU/GPU와 debugging | Completed |
| 3 | Perceptron, MLP, `nn.Linear`, flatten, `forward` | Completed |
| 4 | Non-linearity, ReLU, Sigmoid, Softmax와 출력층 계약 | Completed |
| 5 | Loss, optimizer, learning rate와 parameter update | Completed with one pending rerun |
| 6 | Computation graph, Autograd, gradient와 안전한 평가 | Partial advanced practice pending |
| 7 | Transform, DataLoader, split과 pipeline debugging | Advanced practice completed |
| 8 | MLP train·validation·metric·history 종합 흐름 | 8-8 completed; 8-1~8-7 review pending |
| 9 | Seed, logging, `state_dict`, checkpoint, resume와 실험 폴더 | Basic reviewed; two corrected cells need rerun; advanced deferred |
| 10 | 학습 곡선과 Overfitting·Underfitting 진단 | Not started due to health issue |

## Repository Structure

아래 구조에는 현재 학습 중심인 `deep-learning` 영역만 표시합니다.

```text
TIL/
├── README.md
├── WEEKEND_PRACTICE_BACKLOG.md
└── deep-learning/
    ├── 01-pytorch-foundations/
    │   ├── README.md
    │   ├── 01-ml-vs-dl-basic.ipynb
    │   ├── 02-ml-vs-dl-advanced.ipynb
    │   ├── 03-training-flow-basic.ipynb
    │   ├── 04-problem-io-basic.ipynb
    │   ├── 05-pytorch-code-reading-basic.ipynb
    │   ├── 06-tensor-dtype-shape-basic.ipynb
    │   ├── 07-batch-broadcasting-basic.ipynb
    │   ├── 08-device-basic.ipynb
    │   ├── 09-device-advanced.ipynb
    │   ├── 10-shape-device-debugging-basic.ipynb
    │   └── requirements.txt
    ├── 02-mlp-foundations/
    │   ├── README.md
    │   ├── 01-perceptron-linear-boundary-basic.ipynb
    │   ├── 02-mlp-layers-basic.ipynb
    │   ├── 03-linear-weight-bias-basic.ipynb
    │   ├── 04-image-flatten-basic.ipynb
    │   ├── 05-mlp-forward-basic.ipynb
    │   └── requirements.txt
    ├── 03-activation-output-layers/
    │   ├── README.md
    │   ├── 01-nonlinearity-basic.ipynb
    │   ├── 02-nonlinearity-advanced.ipynb
    │   ├── 03-relu-basic.ipynb
    │   ├── 04-relu-advanced.ipynb
    │   ├── 05-sigmoid-binary-basic.ipynb
    │   ├── 06-sigmoid-binary-advanced.ipynb
    │   ├── 07-softmax-multiclass-basic.ipynb
    │   ├── 08-softmax-multiclass-advanced.ipynb
    │   └── requirements.txt
    ├── 04-loss-optimization-training-loop/
    │   ├── README.md
    │   ├── 01-loss-function-basic.ipynb
    │   ├── 02-loss-function-advanced.ipynb
    │   ├── 03-task-loss-selection-basic.ipynb
    │   ├── 04-task-loss-selection-advanced.ipynb
    │   ├── 05-optimizer-learning-rate-basic.ipynb
    │   ├── 06-optimizer-learning-rate-advanced.ipynb
    │   ├── 07-parameter-update-flow-basic.ipynb
    │   ├── 08-parameter-update-flow-advanced.ipynb
    │   └── requirements.txt
    ├── 05-autograd-data-pipeline/
    │   ├── README.md
    │   ├── 01-computation-graph-chain-rule-basic.ipynb
    │   ├── 02-computation-graph-chain-rule-advanced.ipynb
    │   ├── 03-requires-grad-basic.ipynb
    │   ├── 04-requires-grad-advanced.ipynb
    │   ├── 05-backward-grad-basic.ipynb
    │   ├── 06-backward-grad-advanced.ipynb
    │   ├── 07-training-step-order-basic.ipynb
    │   ├── 08-training-step-order-advanced.ipynb
    │   ├── 09-autograd-debugging-basic.ipynb
    │   ├── 10-autograd-debugging-advanced.ipynb
    │   ├── 11-transform-advanced.ipynb
    │   ├── 12-dataloader-split-advanced.ipynb
    │   ├── 13-data-pipeline-debugging-advanced.ipynb
    │   └── requirements.txt
    ├── 06-mlp-training-validation/
    │   ├── README.md
    │   ├── 01-mlp-end-to-end-advanced.ipynb
    │   └── requirements.txt
    └── 07-experiment-reproducibility/
        ├── README.md
        ├── 01-seed-reproducibility-basic.ipynb
        ├── 02-logging-design-basic.ipynb
        ├── 03-state-dict-checkpoint-basic.ipynb
        ├── 04-resume-training-basic.ipynb
        ├── 05-experiment-directory-basic.ipynb
        └── requirements.txt
```

## Latest Learning Log

### Experiment Reproducibility and Result Management

- Python·NumPy·PyTorch·CUDA seed와 split·DataLoader generator를 함께 관리
- seed 고정은 재현성을 높이지만 버전·장치·연산이 다르면 완전히 같은 결과를 보장하지 않음
- `config.json`과 epoch metric log로 실험 조건과 결과를 분리해 기록
- model·optimizer의 `state_dict`와 완료 epoch·history를 checkpoint로 구성
- `torch.load()`는 파일을 읽고 `load_state_dict()`는 읽은 값을 객체에 실제로 주입
- `last.pt`는 재개용, `best.pt`는 validation 기준 평가·추론용으로 구분
- 정확한 재개 범위를 완료 epoch 다음 경계로 한정하고 난수·loader generator 상태까지 복원
- 한 번의 실험에서 생긴 config·metrics·checkpoint·plot을 하나의 run directory로 연결

### Questions from 2026-08-27

- `json.dump()`는 파일 저장, `json.dumps()`는 JSON 문자열 반환
- `indent`는 가독성, `ensure_ascii=False`와 UTF-8은 한글 저장을 위한 설정
- 파일 모드 `w`는 덮어쓰기, `a`는 이어쓰기, `r`은 읽기
- `json_text[:80]`은 저장 전 JSON 문자열의 앞부분만 확인하는 slicing
- `map_location="cpu"`로 GPU checkpoint를 CPU 환경에서 읽는 방법
- `Path.unlink()`와 `shutil.rmtree()`의 파일·폴더 삭제 범위 차이
- `make_exp_dir()`에서 만든 상세 경로를 상위 `Path(root)`로 다시 덮어쓰지 않아야 함

### Deferred for Health and Time

- 10-1·10-2는 건강 문제로 진행하지 못해 완료 처리하지 않음
- 9장 별도 심화는 기본 흐름과 10장 복습 뒤 시간이 남을 때 진행

### Autograd and Safe Evaluation

- 계산 그래프와 Chain Rule, leaf·non-leaf Tensor의 gradient 저장 위치
- `requires_grad`, `backward()`, gradient 누적과 표준 step 순서
- `grad is None`과 값이 0인 gradient의 의미 구분
- `model.eval()`과 `torch.no_grad()`, 학습 Loss 경로와 metric용 `detach()` 구분

### Data Pipeline

- `Dataset`은 sample 단위 접근, `DataLoader`는 batching과 shuffle을 담당
- transform은 전체 전처리이며 augmentation은 transform의 일부
- train 통계로 모든 split을 정규화해 validation 정보 누수 방지
- `SubsetWithTransform`으로 train augmentation과 validation·test transform 분리
- split용 seed와 shuffle용 seed를 분리해 재현 범위 명확화
- 첫 batch의 shape·dtype·device·finite 값과 forward 출력을 먼저 검사

### End-to-End MLP

- `nn.Module → loss·optimizer → train → validation → metric → history` 연결
- 학습에서는 gradient와 parameter update를 사용하고 검증에서는 `torch.no_grad()` 사용
- batch 평균 Loss에 `y.shape[0]`을 곱해 sample 수 기준 epoch Loss 계산
- validation 중 parameter가 변하지 않는지 epoch마다 감사
- validation Loss로 best epoch를 고르고 test는 최종 한 번만 확인
- 8-8 종합 실습을 완료했지만 8-1~8-7 개별 흐름은 주말 복습 대상으로 유지

### Questions and Newly Learned Points

- `total_loss = seen = 0`: 두 누적 변수를 동시에 0으로 초기화하는 다중 할당
- `torch.enable_grad() if training else torch.no_grad()`: mode에 따른 가변 gradient context
- `valid_unchanged &= condition`: 모든 validation에서 조건이 유지되는지 논리 AND 누적
- `min(range(len(values)), key=values.__getitem__)`: 최솟값 자체가 아닌 index 반환
- `y.shape[0]`: 현재 batch의 실제 sample 수
- `unbiased=False`: 표준편차 계산 시 `N`으로 나누는 설정
- epsilon: 표준화에서 0으로 나누는 오류를 막는 작은 값

## Recording Principles

- 교육자료 원본 대신 직접 작성한 코드와 해석만 공개합니다.
- 실행 환경, 데이터, random seed와 평가 지표를 기록합니다.
- 성공한 결과뿐 아니라 오류와 개선 방향도 남깁니다.
- API key, 개인정보 및 사용 권한이 불분명한 데이터는 올리지 않습니다.
