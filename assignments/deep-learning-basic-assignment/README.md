# 딥러닝 기초 종합 과제 — 손글씨 숫자 분류 모델의 학습·비교·저장·추론 흐름

> 제출용 채점 과제입니다. 정규 강의 실습(`deep-learning-basics`, `deep-learning-advanced`)과는 별개로, 지난주에 부여되어 마감 기한에 맞춰 제출한 산출물입니다.

## 과제 구성

| 단계 | 주제 |
| --- | --- |
| 0 | 환경과 공통 설정 |
| 1 | 데이터 분할·DataLoader·배치 입구 검사 |
| 2 | ImageMLP와 CNN 모델 완성 |
| 3 | 학습·검증 루프와 MLP-CNN 공정 비교 |
| 4 | Best checkpoint 저장·복원·학습 재개 |
| — | 최종 test (이 단계에서만 DataLoader 생성) → 최종 자동 검증 → 마무리 |

각 단계는 문제 배경 → 배우는 것 → 수행 순서 → 제출 결과물 → 자주 하는 실수 → (선택) 5점 도전 심화로 구성되어 있고, 문제마다 결과 해석을 직접 서술하는 칸이 있습니다.

## 큰 흐름

1. **1단계**: 손글씨 숫자 데이터를 train/validation/test로 나누고 DataLoader와 배치 shape·dtype을 검사해 파이프라인 입구를 검증
2. **2단계**: MLP와 CNN 두 모델을 완성해 같은 입력에 대해 동작하도록 구조를 맞춤
3. **3단계**: 공통 학습/검증 루프로 MLP와 CNN을 같은 조건에서 공정하게 비교하고 결과를 그래프로 확인
4. **4단계**: validation 기준 best checkpoint를 저장하고, 복원해서 학습을 이어가는 흐름까지 구현 — 9장(실험 재현성)에서 다룬 checkpoint/재개 개념을 실전 파이프라인에 연결
5. 마지막에 최종 test로 한 번만 성능을 확인하고, 자동 검증 셀로 전체 흐름이 깨지지 않았는지 체크
6. 노트북 마지막에 AI(Claude 등)를 활용한 부분을 개념/함수·문법/그래프 구현으로 구분해 별도 기록

## Files

| File | 설명 |
| --- | --- |
| `deep_learning_basic_assignment_이용석.ipynb` | 1~4단계 구현, 최종 test 및 자동 검증 포함 |

## Environment

```bash
pip install torch torchvision matplotlib
```
