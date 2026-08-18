# CV Tuning and End-to-End Pipeline

같은 CV 조건에서 하이퍼파라미터 후보를 공정하게 비교하고,
전처리·불균형 처리·분류기를 하나의 Pipeline으로 묶어 저장과 입력 검증까지 연결했습니다.

> 진행 상태: 5-1 기본·심화와 5-2 기본·심화 실습 완료. 5-2 심화는 설명과 코드를 이해한 단계이며 독립 재구현이 필요합니다.

## Experiment 1: Grid Search and Random Search

1,600행의 불균형 합성 데이터에서 Random Forest의 `n_estimators`와 `max_depth`를 탐색했습니다.
Grid와 Random에 같은 개발 데이터, 4-fold, AP, 후보 12개를 배정했습니다.

| Search | Candidates | Folds | CV fits | Best mean AP | Fold std |
| --- | ---: | ---: | ---: | ---: | ---: |
| Grid | 12 | 4 | 48 | 0.618 | 0.042 |
| Random | 12 | 4 | 48 | 0.616 | 0.042 |

두 방법을 합쳐 총 96번 fit했습니다. 최고 평균 AP와 `0.01` 이내인 후보에서는
fold 변동, 트리 수와 깊이 순서로 선택했습니다. 기본 실습에서 선택된 Random 후보는
`n_estimators=180`, `max_depth=10`이었고 sealed Test AP는 `0.731`이었습니다.

### Advanced Analysis

- Grid 12행과 Random 12행을 합친 24개 평가 행을 분석했습니다.
- 고유 하이퍼파라미터 조합은 22개였습니다.
- 허용폭 `0.01`에서 5개 후보가 남았고, 변동이 더 작은 Grid의 `80 trees, depth 10`이 선택됐습니다.
- Random 후보를 12개에서 6개로 줄이면 CV fits는 48회에서 24회로 감소했습니다.
- 이번 실행에서 최고 후보가 같았더라도 다른 데이터에서도 6개면 충분하다는 결론은 내릴 수 없습니다.

## Experiment 2: End-to-End Pipeline

수치형 3개와 범주형 1개가 섞인 1,200행 데이터에서 다음 순서를 하나로 연결했습니다.

```text
numeric/categorical preprocessing
→ RandomOverSampler
→ LogisticRegression
```

완성된 `imblearn` Pipeline 전체를 `GridSearchCV`에 전달했습니다.

```text
GridSearchCV
└── 4-fold StratifiedKFold
    └── train fold마다 Pipeline.fit
        ├── preprocessor.fit/transform
        ├── sampler.fit_resample
        └── classifier.fit
```

Validation fold, sealed Test와 새 요청에서는 학습된 전처리만 재사용하고 sampler는 실행되지 않습니다.
따라서 새 요청 3행은 예측 결과도 3행으로 유지됩니다.

| Item | Result |
| --- | --- |
| C candidates / CV fits | 3 / 12 |
| Best C | 1.0 |
| Best CV AP | 0.440 |
| Sealed Test AP | 0.631 |
| Reload score match | `True` |
| Reload prediction match | `True` |

## Experiment 3: Artifact and Schema Guard

학습된 Pipeline뿐 아니라 feature 순서, dtype, 값 범위, 허용 범주, null 정책,
호출 mode, 버전과 점수 의미를 하나의 artifact에 저장했습니다.

입력 검증에서는 다음 10가지 오류를 모델 실행 전에 차단했습니다.

- 잘못된 dtype과 미등록 범주
- 수치 domain 위반과 무한대
- 필수 열 null
- 누락 열과 추가 열
- 열 순서 변경
- 미지원 source mode
- online 최대 128행 초과

저장·reload 전후 대표 입력의 점수와 0/1 예측이 모두 일치했습니다.

## Learning Reflection

5-1 기본·심화와 5-2 기본은 전체 흐름을 따라 구현할 수 있었습니다.
특히 `StratifiedKFold`가 별도로 실행되는 것이 아니라 `GridSearchCV`가 Pipeline을
각 fold에서 반복 학습시키는 구조를 다시 확인했습니다.

처음에는 Pipeline에 sampler가 있는데 예측에서는 왜 실행되지 않는지 혼동했습니다.
학습 경로에서는 `fit_resample`로 소수 클래스를 보완하지만, 예측 경로에서는 이미 학습된
전처리와 classifier만 사용한다는 차이를 코드로 비교하며 이해했습니다.

5-2 심화의 artifact 구성과 `validate_input`은 각 줄의 역할은 이해되지만,
여러 운영 계약과 예외 처리를 처음부터 혼자 설계하기에는 아직 어렵습니다.
완료 여부와 독립 구현 능력을 구분해, 주말에 작은 guard부터 다시 작성할 계획입니다.

## Next Steps

- [x] 같은 CV 예산으로 Grid와 Random 비교
- [x] 평균 허용폭과 fold 변동을 함께 사용해 후보 고정
- [x] 수치형·범주형 전처리와 sampler를 하나의 Pipeline으로 구성
- [x] Pipeline 전체를 GridSearchCV에 전달
- [x] sealed Test 1회 평가와 저장·reload 동일성 검증
- [x] 입력 계약 위반 10종 자동 검사
- [ ] 5-2 심화 artifact와 schema guard를 참고 없이 다시 구현
- [ ] guard를 객체, 열, dtype, domain, 운영 mode 순서로 나눠 단계별 테스트

## Files

```text
05-cv-tuning-end-to-end-pipeline/
├── README.md
├── cv-search-basic.ipynb
├── cv-search-advanced.ipynb
├── end-to-end-pipeline-basic.ipynb
├── artifact-schema-guard-advanced.ipynb
└── requirements.txt
```

공개 노트북에서는 강의 문제 원문을 제외하고 직접 실행한 코드와 결과, 현재 이해 수준만 남겼습니다.
