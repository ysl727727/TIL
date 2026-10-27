# 기초 수학 (선형대수)

> 2026-08-05 ~ 08-10, 과정 첫 주 기초 수학 수업 기록입니다. "딥러닝을 이해하기 위한 7장 19강" 흐름으로 벡터·행렬에서 시작해 Attention과 역전파까지 갔고, 실습은 Google Colab에서 UCI 데이터(Wine Quality, Online Retail, AI4I 2020 등)로 했습니다.

| 장 | 날짜 | 주제 | 상태 |
| --- | --- | --- | --- |
| [1](./01-vectors-norms-dot-cosine/) | 08-05 | 벡터·행렬, 노름과 정규화, 내적과 코사인 유사도, 행렬곱과 선형층 | 🧪 1-1·1-2 실습 (1-3은 준비만) |
| [2](./02-span-rank-linear-systems/) | 08-06 | 선형 변환, span·rank·영공간, `Ax = b`, `solve` vs `inv`, 조건수 | 🧪 2-2 완료 · 2-3 일부 |
| [3·4](./03-eigen-pca-svd/) | 08-07 | 고유값·고유벡터, PCA, 직교성과 최소제곱, SVD와 저랭크 근사 | 🧪 4-1 실습 · PCA 미실행 |
| [5~7](./04-tensor-shape-attention-backprop/) | 08-10 | 텐서 shape, Attention `QKᵀ/√d_k`, Softmax·Cross Entropy, 미분·체인룰·역전파 | 🧪 6-1 필수 실습 |

이후 연결: 기초 수학 종합 과제(임베딩·코사인 검색, PCA, SVD, Causal Attention)는 [assignments/basic-math-assignment](../assignments/basic-math-assignment/)에 있고, 08-13에는 첫 주 복습 교재로 다시 복습했습니다([머신러닝 3장](../machine-learning/03-bias-variance-regularization/)).
