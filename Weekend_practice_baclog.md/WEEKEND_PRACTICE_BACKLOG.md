# Weekend Practice Backlog

> Updated on 2026-09-10 after Chapter 7-8 (8/9강) lecture notes and the start of the
> Logits-to-Optimizer (LLM Practical Foundations) material.

이번 주는 실습이 계속 밀리고 있습니다 — 5·6장은 아직 시작도 못 했고, 7-2~7-8도 그대로이며,
어제(8·9강)와 오늘(logits/optimizer 1~2장) 이론만 정리한 채 실습은 손대지 못했습니다.
`chapter01_starter.ipynb`는 오늘 열어봤지만 TODO 1~3이 전부 미완료 상태입니다. 다음
주말(2026-09-12~13)에는 밀린 실습을 종류별로 나눠 순서대로 처리합니다. 체크박스는 강의를
들었거나 자료를 받았다는 뜻이 아니라, **직접 실행하고 결과를 설명할 수 있는지**를 기준으로
표시합니다.

## 0. Latest Update: Chapter 7-8 (8/9강) and Logits-to-Optimizer Notes

### Completed this week (2026-09-09 ~ 09-10)

- [x] 8강(8-1,8-2,8-4,8-5강) 이론 정리 — Prompt Engineering→PEFT 스펙트럼, Prompt-only baseline 설계, LoRA, 공정 비교/Regression
- [x] 9강(9-1~9-5강) 이론 정리 — generate() autoregressive loop, decoding strategy, Temperature/Top-k/Top-p, Chat Template 디버깅
- [x] 딥러닝 실전 1장(1-1,1-2강)·2장(2-1,2-2강) 이론 정리 — logit/softmax 수치안정성, MSE/BCE/CE, Gradient Descent, SGD/Momentum/Adam

### Not Completed This Week

- [ ] 5장 실습 (여전히 미착수)
- [ ] 6장 실습 (여전히 미착수)
- [ ] 7-2 ~ 7-8 실습 (여전히 미착수)
- [ ] 8강 실습 (Prompt-only baseline, LoRA 코드 실습 — 아직 자료 없음, 실습 파일 도착 시 진행)
- [ ] 9강 실습 (generate(), decoding, chat template 코드 실습 — 아직 자료 없음, 실습 파일 도착 시 진행)
- [ ] `chapter01_starter.ipynb` TODO 1~3 완성 (stable softmax/log-softmax, 문의별 CE/MSE/BCE, 평균·worst 문의 찾기)

실습 부채가 여러 주 누적되고 있습니다. 다음 주말에는 **완료 가능한 만큼만** 목표로 잡고,
전부 따라잡으려 하지 않습니다.

### Minimum Catch-Up Plan (2026-09-12~13)

1. 가장 먼저 `chapter01_starter.ipynb` TODO 1~3 완성 — 통합 실습 하나라 상대적으로 짧고, 오늘 이론을 그대로 적용하면 됨
2. 다음으로 5장 실습(있다면) 착수 — 이후 6장·7장과 이어지는 순서라 먼저 처리
3. 시간이 남으면 6장, 7-2 순서로 진행
4. 8강·9강 실습은 자료가 아직 없어 이번 주말 우선순위에서는 제외 — 자료 도착 시 별도로 진행
5. 이틀 안에 다 못 끝내도 괜찮음 — 이번 주말은 완주보다 "밀린 항목을 더 늘리지 않는 것"이 목표

## 1. Latest Update: Chapters 5-7 and Graded Assignments

### Completed this week (2026-09-06 ~ 09-08)

- [x] 기초 수학 종합 과제 제출 (문서 임베딩/Cosine 검색, PCA, SVD, Causal Attention+autograd SGD)
- [x] 딥러닝 기초 종합 과제 제출 (DataLoader 검사, MLP/CNN, 학습·검증 루프 비교, checkpoint 저장·복원·재개)
- [x] 5장(5-1,5-2,5-4강) 이론 정리 — 사전학습, LM Objective, BERT(Masked LM), GPT(Causal LM)
- [x] 6장(6-1,6-3,6-4,6-5강) 이론 정리 — HF Hub/Model Card, AutoClass, Base/Task-specific 출력, 저장/재로드
- [x] 7장(7-1,7-2,7-3,7-5,7-6,7-7,7-8강) 이론 정리 — 문제 정의부터 Error Analysis/리포트까지 Fine-tuning 전체 파이프라인
- [x] 7-1 실습: 텍스트 분류 데이터 품질 감사(결측·중복·label 불균형), split leakage(정확 중복+Jaccard) 탐지

### Not Completed This Week

- [ ] 5장 실습 (5-1, 5-2, 5-4강에 대응하는 실습 노트북 전체)
- [ ] 6장 실습 (6-1, 6-3, 6-4, 6-5강에 대응하는 실습 노트북 전체)
- [ ] 7-2 실습: DatasetDict, Label Encoding, Stratified Split
- [ ] 7-3 실습: Tokenization Mapping, DataCollatorWithPadding
- [ ] 7-5 실습: compute_metrics, Accuracy/Macro-F1
- [ ] 7-6 실습: TrainingArguments, Trainer 설정
- [ ] 7-7 실습: Fine-tuning 실행·평가·Checkpoint 관리
- [ ] 7-8 실습: Error Analysis, Fine-tuning 리포트

과제 마감이 이유입니다 — 5·6장은 실습을 아예 시작 못 했고, 7장도 이론만 정리한 채 실습은
7-1 하나만 진행했습니다.

### Minimum Catch-Up Plan (2026-09-12~13)

1. 5장 실습부터 순서대로: Masked LM/Causal LM 관련 실습이 있다면 이론 요약(README Core Theory)을 먼저 훑고 시작
2. 6장 실습: AutoModel/AutoTokenizer 기본 동작, 저장/재로드 재현성 확인 위주로 진행
3. 7-2 → 7-3 → 7-5 → 7-6 → 7-7 → 7-8 순서대로 이어서 진행 (Trainer 파이프라인이 순차적으로 쌓이는 구조라 순서를 지키는 게 유리함)
4. 이틀 안에 다 못 끝내면 7-2~7-3(데이터 파이프라인)까지만이라도 완료해 다음 주 실습과 이어지게 함

## 2. Chapter 9 and 10

### Completed on 2026-08-27

- [x] 9-1 기본: Python·NumPy·PyTorch seed와 모델 초기화 재현 확인
- [x] 9-2 기본: epoch log dictionary와 log list 누적
- [x] 9-3 기본: model `state_dict` key·shape와 checkpoint 구성
- [x] 9-4 기본: model·optimizer checkpoint 저장과 복원
- [x] 9-5 기본: 실험 폴더·config·metrics 저장 흐름 확인
- [x] `json.dump()`와 `json.dumps()`의 파일·문자열 반환 차이 정리
- [x] JSON의 `indent`, `ensure_ascii=False`, UTF-8 encoding 역할 정리
- [x] `w`·`a`·`r` 파일 모드와 log 누적 방식 구분
- [x] `torch.load()`와 `load_state_dict()`의 읽기·주입 역할 구분
- [x] `map_location="cpu"`, `Path.unlink()`, `shutil.rmtree()` 용도 정리
- [x] `make_exp_dir()`가 생성한 상세 경로를 다시 덮어쓰는 버그 확인 및 수정

9-3의 checkpoint key 표기와 9-5의 경로 반환 코드는 공개용 노트북에서 바로잡았습니다.
현재 환경에서는 PyTorch를 실행할 수 없어 수정 셀의 출력 재확인은 추후 진행합니다.

### Not Completed Due to Health Issue

- [ ] 10-1 학습 곡선 해석: train·validation loss와 accuracy curve 읽기
- [ ] 10-2 Overfitting·Underfitting 진단: 곡선의 높이·방향·gap 구분

오늘 진행하지 못한 이유는 건강 문제입니다. 밀린 분량을 한 번에 따라잡는 일정으로 잡지 않고,
컨디션이 회복되면 10-1 이론과 예시 곡선을 먼저 본 뒤 10-2로 넘어갑니다.

### Optional Only: Chapter 9 Advanced

- [ ] 9-1~9-5 별도 심화 문제

9장 심화는 필수 주말 과제가 아닙니다. 10장 기본 흐름과 기존 미완료 항목을 무리 없이 확인한 뒤
시간이 남을 때만 진행합니다.

## 3. Latest Deep Learning Progress

### Completed on 2026-08-26

- [x] 7-3 심화: train 통계 정규화, `SubsetWithTransform`, transform 순서 승인
- [x] 7-4 심화: 재현 가능한 split, 목적별 DataLoader, 평가 sample 누락 검사
- [x] 7-5 심화: shape·dtype 계약 수정, batch audit, pipeline 후보 승인
- [x] 8-8 종합 심화: train·validation 분리, 3 epoch baseline, validation 기반 report
- [x] Validation 전후 parameter가 변하지 않는지 검사
- [x] Test를 모델 선택에 쓰지 않고 최종 한 번만 확인하는 원칙 정리

### Completed on 2026-08-25

- [x] 6-1 기본: 계산 그래프와 Chain Rule을 수식·Autograd로 비교
- [x] 6-2 기본·심화: `requires_grad`, `detach()`, layer freeze와 gradient 연결 진단
- [x] 6-3 기본·심화: scalar Loss, `.grad` shape·finite·norm 감사
- [x] 6-4 기본: gradient 누적과 표준 mini-batch step 확인
- [x] 6-5 기본·심화: 안전한 validation, metric 분리와 Autograd 디버깅
- [x] 7-1·7-2 이론 및 코드 흐름 확인: `Dataset`, `DataLoader`, Custom Dataset

### Earlier Partial Practice Still Pending

- [ ] 6-1 심화 2번 셀 재실행: 문법 오류 수정 후 결과 확인
- [ ] 6-4 심화 2·3번: parameter update 검증과 잘못된 gradient 누적 비교
- [ ] 5-2 심화 `compute_loss` 셀: 회귀·이진·다중 분류 입력으로 최종 실행

### Not Completed Individually

- [ ] 8-1 `nn.Module` 구조와 `forward` 설계 개별 실습
- [ ] 8-2 MLP 모델 클래스 완성 개별 실습
- [ ] 8-3 Loss와 optimizer 연결 개별 실습
- [ ] 8-4 Train loop 작성 개별 실습
- [ ] 8-5 Validation loop 작성 개별 실습
- [ ] 8-6 Accuracy와 metric 누적 개별 실습
- [ ] 8-7 Epoch 로그와 시각화 개별 실습

미완료 이유: **8-8이 8-1~8-7을 하나의 MLP 파이프라인으로 모은 종합 실습이라,
시간이 부족한 상황에서 8-8 실행을 우선했습니다.** 종합 실습 완료만으로 개별 단계를 모두
설명할 수 있다고 보지 않으므로 8-1~8-7은 완료 처리하지 않습니다.

주말에는 개별 노트북을 처음부터 모두 다시 풀기보다 먼저 눈으로 살펴보면서,
각 내용이 8-8의 어느 코드에 해당하는지 표시합니다. 시간이 남으면 `run_epoch()`를 재작성합니다.

## 4. Questions and Newly Learned Points

### Python and PyTorch Syntax

- [x] `total_loss = seen = 0`: 두 변수를 동시에 0으로 초기화하는 다중 할당
- [x] `context = torch.enable_grad() if training else torch.no_grad()`: mode별 context 선택
- [x] `valid_unchanged &= condition`: 논리 AND 결과를 epoch마다 누적
- [x] `min(range(len(valid_loss)), key=valid_loss.__getitem__)`: 최소 Loss의 index 찾기
- [x] `y.shape[0]`: 현재 batch에 포함된 실제 sample 수
- [x] `x.shape`은 전체 shape이고 `x.shape[0]`은 첫 번째 축의 크기라는 차이

### Data Pipeline

- [x] Dataset은 sample 하나, DataLoader는 batch·shuffle을 담당
- [x] Transform은 전체 전처리이고 augmentation은 transform의 일부
- [x] Train·validation·test의 학습·선택·최종 확인 역할 구분
- [x] `random_split(..., generator=torch.Generator().manual_seed(42))`로 split 재현
- [x] `SubsetWithTransform`으로 train과 evaluation transform 분리
- [x] Wrapper의 목적은 learning rate 최적화가 아니라 transform 격리와 평가 무결성 유지
- [x] `unbiased=False`는 표준편차 계산에서 `N`으로 나누는 설정
- [x] epsilon은 표준화 분모가 0이 되는 문제를 방지

### Autograd Carry-over

- [x] `nn.Linear(2, 1)`의 weight shape가 `[1, 2]`인 이유
- [x] `.reshape(-1, 1)`로 `[N]`을 `[N, 1]` 계약에 맞추는 방법
- [x] `torch.zeros_like(x)`가 shape·dtype을 유지하는 이유
- [x] `param.grad is None`과 값이 0인 gradient의 차이
- [x] 입력 scale이 MSE gradient norm을 크게 만들 수 있다는 점
- [x] `model.eval()`과 `torch.no_grad()`의 서로 다른 역할
- [x] `.detach()`는 학습 Loss 경로가 아니라 metric·로그 경로에 사용

### Weekend Recall Check

- [ ] 위 표현을 보지 않고 한 줄씩 다시 작성
- [ ] 각 표현이 필요한 이유를 코드 실행 흐름과 함께 설명
- [ ] `loss.item() * y.shape[0]`이 batch 합계를 복원하는 이유 설명
- [ ] validation에서 gradient와 parameter update를 모두 막아야 하는 이유 설명

## 5. Highest Priority: 8-1~8-7 Visual Review

### First Pass: Match Each Lesson to 8-8

- [ ] 8-1: `nn.Module`, `__init__`, `forward`, `model(x)` 위치 찾기
- [ ] 8-2: input·hidden·output dimension과 parameter 수 확인
- [ ] 8-3: `criterion`과 `optimizer`가 model parameter에 연결되는 위치 찾기
- [ ] 8-4: `zero_grad → forward → loss → backward → step` 표시
- [ ] 8-5: `model.eval()`과 `torch.no_grad()` 및 update 금지 확인
- [ ] 8-6: `total_loss`, `correct`, `seen` 누적식 확인
- [ ] 8-7: history, epoch 로그, validation curve와 best epoch 선택 확인

완료 기준:

```text
개별 강의:
8-8에서 대응하는 코드:
입력과 출력:
학습 때만 실행되는 부분:
검증 때만 실행되는 부분:
내 말로 설명:
```

### Second Pass: Rebuild if Time Allows

- [ ] `TinyMLP` 또는 `nn.Sequential` 모델을 보지 않고 작성
- [ ] 공통 `run_epoch(training, loader)` 뼈대 재작성
- [ ] 마지막 작은 batch를 포함해 sample 수 기준 Loss·accuracy 계산
- [ ] Validation 전후 parameter clone을 비교해 불변성 확인
- [ ] Validation Loss의 최소 index로 best epoch 선택
- [ ] Test 평가 횟수가 1회인지 report에 기록

## 6. Data Pipeline Reinforcement

- [ ] Train 통계와 validation 자체 통계로 정규화한 결과 비교
- [ ] `unbiased=True`와 `False`의 표준편차 차이 확인
- [ ] 상수 feature를 epsilon 없이 표준화해 오류를 확인하고 수정
- [ ] Train·validation·test index의 교집합이 0인지 검사
- [ ] Split 전체 합집합이 원본 index를 모두 포함하는지 검사
- [ ] Train에는 random transform, validation에는 deterministic transform 적용
- [ ] Evaluation loader에서 `drop_last=True`가 sample을 버리는 예제 재현
- [ ] 첫 batch의 shape·dtype·device·finite 값을 출력하는 audit 함수 작성

## 7. Carried Backlog

### Autograd Reinforcement

- [ ] 6-1 심화 미실행 셀을 실행하고 수기 gradient와 비교
- [ ] 같은 parameter가 두 경로에 쓰일 때 gradient 기여 설명
- [ ] `grad is None`과 0 gradient를 각각 재현
- [ ] 입력 scale 1배·10배에서 MSE gradient norm 비교
- [ ] 6-4 심화 2·3번의 예상·실제 weight와 누적 오류 비교
- [ ] `zero_grad(set_to_none=True/False)`의 `.grad` 상태 비교
- [ ] `eval()`만 쓴 경우와 `eval()+no_grad()`의 `grad_fn` 비교

### Chapter 5 Partial Practice

- [ ] 5-2 별도 심화 `compute_loss(task, output, target)` 셀 실행
- [ ] 회귀 `[B,1]` float output·target과 `MSELoss` 확인
- [ ] 이진 `[B,1]` logits·float target과 `BCEWithLogitsLoss` 확인
- [ ] 다중 `[B,C]` logits·`[B]` long target과 `CrossEntropyLoss` 확인
- [ ] 잘못된 shape·dtype 입력으로 assertion 실패 확인

### Earlier Deep Learning

- [ ] `TinyMLP`의 `__init__`과 `forward`를 보지 않고 다시 작성
- [ ] `nn.Linear(5, 10)`의 weight·bias shape와 parameter 수 손계산
- [ ] 이미지 `[12, 3, 32, 32]`를 flatten해 `[12, 10]` logits 생성
- [ ] MLP flatten과 CNN의 공간 정보 처리 차이 설명
- [ ] ReLU·LeakyReLU·Tanh·GELU 출력과 gradient 비교
- [ ] 이진·다중 분류의 Sigmoid·Softmax 중복 적용 오류 수정
- [ ] 모델·입력·target을 같은 device로 옮기는 helper 재작성
- [ ] 1-3·1-4·1-5·2-1·2-2 별도 심화 실습

### Math and Machine Learning

- [ ] 미완료 기초수학 실습을 한 문제씩 작은 단계로 분해
- [ ] Tree·Random Forest·Boosting을 같은 기준으로 비교
- [ ] Learning·validation curve로 bias와 variance 진단
- [ ] Class weight·undersampling·SMOTE를 같은 CV에서 비교
- [ ] Sampler와 preprocessing을 CV train fold 안에 두어 leakage 방지
- [ ] End-to-end artifact schema guard를 참고 없이 재작성

## 8. Next Weekend Order

### Saturday, 2026-09-12

1. 컨디션을 먼저 확인하고 학습 시간을 짧게 정함
2. `chapter01_starter.ipynb` TODO 1~3 완성을 최우선으로 진행 (분량이 짧고 오늘 이론과 바로 연결됨)
3. 가능하면 10-1 이론에서 train·validation 곡선의 역할 확인 (계속 이월 중)
4. 여유가 있으면 5장 실습(Masked LM/Causal LM 관련) 착수
5. 몸 상태가 좋지 않으면 여기서 종료

### Sunday, 2026-09-13

1. 가능하면 10-2 이론에서 Overfitting·Underfitting 차이 확인 (계속 이월 중)
2. 6장 실습(AutoModel/AutoTokenizer, 저장·재로드) 진행
3. 시간이 남으면 7-2 → 7-3 순서로 실습 진행 (DatasetDict/Split → Tokenization/Collator)
4. 9-3·9-5 수정 셀을 Colab에서 다시 실행해 출력 확인 (계속 이월 중)
5. 추가 여유가 있으면 8-1~8-7 눈복습 중 한 항목만 선택
6. 7-5 이후·8강·9강 실습·9장 심화는 위 항목이 끝나고 시간이 남을 때만 진행

## 9. Working Rule

각 문제는 정답을 보기 전에 다음 네 줄을 먼저 작성합니다.

```text
입력:
출력:
작업 순서:
첫 번째로 작성할 코드:
```

막히면 전체 정답 대신 첫 단계 힌트만 확인합니다. 눈으로 복습할 때도 단순히 넘기지 않고
8-8의 대응 코드와 역할을 한 줄씩 적어 실제 연결을 확인합니다.
