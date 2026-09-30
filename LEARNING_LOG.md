# 📝 전체 학습 기록

> 최신 기록이 위에 옵니다. 목차와 진행 상태는 [README](./README.md), 밀린 실습은 [주말 실습 백로그](./WEEKEND_PRACTICE_BACKLOG.md)에서 확인합니다.
> 날짜는 당일 기록이나 주말 백로그에 남아 있는 경우에만 적었습니다.

## 2026-09-30 · LangChain 3\~6-1: LCEL, Runnable 조합, 구조화 출력, Document

- 3장: `prompt | model | parser`는 **연결만** 하고 API 호출은 `invoke()` 때 일어남. 오류가 나면 `dict → ChatPromptValue → AIMessage → str` 경계 중 어디서 자료형이 달라졌는지부터 확인
- 3-2강: `invoke()`는 1건, `batch()`는 리스트(결과도 입력 순서대로 리스트, 입력 수만큼 API 호출), `stream()`은 조각을 반복문으로 받음
- 4장: 앞 결과가 필요하면 Sequence, 같은 입력을 각자 쓰면 Parallel(모델 branch 수만큼 API 호출). `.assign()`은 원본 dict를 보존하며 필드를 추가하고, 서로 의존하는 필드는 assign을 단계별로 나눔
- 5장: `with_structured_output()`으로 Pydantic 객체를 받고, `parser.parse()`는 JSON 해석 → 스키마 검증 두 단계. `parse()` 실패는 `OutputParserException`, `model_validate()` 실패는 `ValidationError`
- 5-3강: 검증 실패 시 수정 요청은 **최대 1회**, 같은 Parser로 재검증하고 실패하면 `None`. 스키마 통과는 형식만 보장하고 내용의 정확성은 보장하지 않음
- 6-1강: 본문은 `page_content`(str), 부가 정보는 `metadata`(dict). 같은 의미는 모든 문서에서 같은 키로, 선택 키는 `.get()`으로 읽음. formatter는 Document를 바꾸지 않고 표시용 문자열만 만듦
- 6-2강(Retriever)·6-3강(retrieval chain)은 10/01에 이어서 진행

## 2026-09-29 · LangChain 기초와 Python 보강 드릴

- LangChain 1-1강: OpenAI SDK 직접 호출은 입력 준비·모델 실행·출력 정리를 한 함수가 모두 맡고, LangChain은 같은 일을 `Prompt → Model → Parser` 세 역할로 나눔 — 모델이 같으므로 답변 품질이 아니라 **코드 구성 방식**이 달라짐
- `model.invoke()`의 반환값은 문자열이 아니라 `AIMessage`이며, 본문만 쓰려면 Parser를 붙여야 함. OpenAI의 `user`와 LangChain의 `human`은 같은 자리
- 선택 기준: 프롬프트가 여러 개인가 / 모델·출력 형식을 교체할 가능성이 있는가 / Retriever·Memory를 연결할 계획인가 — 대부분 "예"면 LangChain, 단발 호출이면 직접 SDK
- LangChain 1-2강: `langchain-core`(공통 규격) / `langchain-openai`(OpenAI 어댑터) / `langchain`(상위 기능) 역할 분리, 설치 이름의 하이픈과 import의 언더스코어 차이, uv `sync --locked --python 3.12` 환경 구성과 `.venv` 인터프리터 선택
- `.env`로 키 분리 + `.gitignore`(`.env`, `.venv/`, `__pycache__/`) — `.gitignore`는 앞으로의 추적만 막을 뿐 이미 올라간 키를 무효화하지 않음
- LangChain 2-1강: `PromptTemplate.format()`은 문자열, `ChatPromptTemplate.format_messages()`는 역할별 메시지 목록을 반환. 중괄호를 문자로 남기려면 `{{ }}`
- LangChain 2-2강: `StrOutputParser`/`CommaSeparatedListOutputParser`/`JsonOutputParser`의 결과 자료형 차이, Parser는 형식을 **강제**하지 않고 `get_format_instructions()`를 Prompt에 넣는 단계가 따로 필요, JSON은 자료형→키→값 순서로 검사
- `langchain_chapter01_starter.ipynb`(같은 사내 질문을 두 방식으로 처리) 확보했으나 TODO 1\~3이 `NotImplementedError` 상태로 **미완료** — 주말로 이월
- Python 기초 드릴 3종 직접 실행: 비교 체이닝과 `True == 1`, `append`/`extend`·`remove`/`pop`의 "값이냐 위치냐" 구분, 리스트 메서드가 제자리 수정이라 `None`을 반환한다는 점, 중첩 반복에서 안쪽 범위를 `len(matrix[i])`로 두어야 안전하다는 점

## 2026-09-23 · 데이터 엔지니어링: Query API, 비동기 호출, API 안정성

- 7-1강: 질문 요청에서 `document_id`와 `context` 중 **하나만** 허용 — 둘 다 오면 무엇을 근거로 답했는지 알 수 없고, 둘 다 없으면 근거 없는 답이 됨(`model_validator`로 검사 → 422)
- 7-1강: `resolve_context()`가 (본문, 출처 목록)을 함께 반환하도록 설계하면 응답의 `sources`를 채우는 코드가 한 줄로 끝남. 프롬프트는 지시문 → `[근거]` → `[질문]` → `[답변]` 순서로 경계를 만들어 조립
- 7-2강: `LLM_MODE` 환경 변수로 mock / external / ollama 전환, **기본값을 mock**으로 두어 키 없이 전체 흐름 검증. 키는 `Authorization: Bearer` header에만, Ollama는 `data["message"]["content"]`에서 본문 추출
- 7-2강: 외부 실패를 그대로 흘리지 않고 422(계약 위반) / 404(문서 없음) / 502(외부 오류·형식 깨짐) / 503(연결 불가)로 우리 API 코드로 변환
- 8-1강: 비동기는 **대기 시간이 겹칠 때만** 빨라짐. `httpx.AsyncClient`를 `async with`로 한 번만 만들어 공유, `response.json()`은 `await` 대상이 아님, `asyncio.gather()`의 결과는 완료 순서가 아니라 **입력 순서**
- 8-2강: `timeout=2.0`은 전체가 아니라 connect/read/write/pool **단계별** 최대 시간. `for attempt in range(2)`는 최초 1회 + 재시도 1회 = 총 2회 호출
- 8-2강: 재시도는 timeout과 5xx만, 4xx(429 포함)는 즉시 실패. `httpx.TimeoutException`이 `RequestError`의 하위 클래스라 **먼저 잡지 않으면 재시도가 사라짐**
- 8-2강: `ExternalServiceError(RuntimeError)`로 좁힌 뒤 경계에서 `HTTPException(502)`로 변환, `@app.middleware("http")`는 `call_next()` 결과를 반드시 반환하고 method·path·status 세 가지만 기록
- LLM 실전 10-1강(밀려 있던 강의를 보강으로 진행): 재시도 계층을 겹치면 SDK 3회 × 앱 3회 × Tool 3회 = 최대 27회까지 늘어남 — retry 책임을 한 계층에만 모으고 `OpenAI(max_retries=0)`로 명시. Full Jitter(`Uniform(0, min(cap, base×2^a))`)와 fallback ladder(기본 모델 → 재시도 → 단순 Prompt → 대체 모델 → 캐시·기능 축소 → 사람)까지 정리

## 2026-09-22 · 데이터 엔지니어링: 정제, FastAPI, Pydantic

- 4강: 정제는 원본을 덮어쓰지 않고 별도 산출물을 만드는 일. 텍스트는 `html.unescape()` → `re.sub(r"<[^>]+>", " ", …)` → `" ".join(split())` 순서를 지켜야 이스케이프된 태그와 붙어 버리는 문장 문제를 함께 해결
- 4강: 중복은 `set`으로 판정하고, `입력 = 정상 + 중복 제외 + 규칙 제외` 등식이 맞는지로 정제 코드를 1차 검증. RAG 문서는 `document_id`/`content`/`metadata` 세 부분으로 고정하고 출처·날짜를 본문에 섞지 않음
- 4강: `make_document_id`는 허용 문자만 남기고 `-`로 치환 → `strip("-")` → `lower()` → `doc-news-001` 형태. 출처가 여럿이면 원본 ID끼리 충돌할 수 있어 출처를 ID에 포함
- 5강: FastAPI는 경로·함수를 **선언**하고 Uvicorn이 포트를 열어 **실행** — 코드에 포트가 없는 이유. 경로는 자원(명사), 동작은 method
- 5강: path(자원 특정) / query(거르거나 자르기) / body(구조화된 입력) 구분, `Query(default=30, ge=5, le=100)`로 규칙을 선언하면 `/openapi.json`에 그대로 노출. 422는 형식 위반(함수 진입 전), 404는 형식은 맞고 자원이 없음
- 6강: `Field(min_length/max_length)`, list 기본값은 `default_factory=list`(가변 기본값 공유 방지), list의 `max_length`는 **원소 수**. `ConfigDict(str_strip_whitespace=True, extra="forbid")`로 공백 차이와 오타 키를 차단
- 6강: `@field_validator(..., mode="before")`는 타입 변환 전 필드 하나, `@model_validator(mode="after")`는 전부 채워진 뒤 모델 전체이며 `self`를 반환해야 함. `ValidationError.errors()`의 `loc`·`type`으로 원인 분류
- 6강: 요청 모델과 응답 모델을 분리하고 `response_model`로 응답 필드를 고정, 201/404/409/422를 구분. 메모리 저장소 `DOCUMENTS`와 보조 인덱스 `SOURCE_INDEX`는 항상 함께 갱신·초기화
- 4\~8강 모두 **강의 교안만 수령**하고 실습 파일이 없어 이론 정리만 진행

## 2026-09-21 · 데이터 수집: 수집 전략, API 호출, 원본 저장

- 1장: 수집 경로(어디서 받는가)와 데이터 형식(어떤 구조인가)을 다른 축으로 구분, 갱신 주기·비용 기준으로 RAG/질문 시점 API/스냅샷 선택, 이용약관→robots.txt→개인정보→저작권→접근·부하 5단계 리스크 게이트
- 1장 실습: 후보 4건을 `choose_route`/`judge_source`/`make_record`로 판단해 경로·상태·근거·확인일을 담은 `collection_plan.json` 생성 — 가능 2건, robots 미확인으로 주의 1건, 개인정보로 제외 1건
- 2장: HTTP 요청·응답 계약, base URL과 endpoint 구분, header/query/body의 역할 차이, 상태 코드별 다음 행동, API 키를 환경 변수로 분리, HTTPX Client에 headers·params·timeout 지정
- 2장 실습: 공개 API(JSONPlaceholder)에 `live` GET 요청으로 상태 200·글 2건 확인, `raise_for_status()` → Content-Type → 리스트/필수 키 순서로 응답 검증, `MockTransport`로 로컬 인증 헤더 연습(공개 클라이언트에는 키 미전달)
- 3장: `has_next` 종료 신호로 page 반복, 429에서 page를 올리지 않고 같은 page 재시도, `append` 대신 `extend`로 전체 목록 병합, 원본(`raw_response.json`)과 가공(`items.json`/`items.csv`) 분리 보존, 로그에는 출처·시각·건수·상태만 남기고 키·개인정보 제외
- 3장 실습은 solution 파일만 확보하고 아직 실행하지 못해 주말로 이월

## 2026-09-09\~10 · Logit, 손실 함수, Optimizer (실습 대기)

- 1-1강: logit vs probability 구분, softmax의 max trick(수치 안정성), `axis=-1` 배치 계산, stable log-softmax
- 1-2강: 문제 유형(회귀/이진/다중 분류)별 MSE/BCE/Cross Entropy 선택 기준과 NumPy 구현, `np.clip`으로 BCE의 `log(0)` 방지
- 2-1강: Gradient Descent 갱신식(`θ ← θ − η∇L`)과 선형 모델(`y=wx+b`) 직접 학습, learning rate가 너무 작거나 클 때의 현상 비교
- 2-2강: SGD(현재 gradient만)·Momentum(velocity 누적)·Adam(1차+2차 모멘트) 차이와 같은 문제에서 loss curve 비교
- `chapter01_starter.ipynb`(사내 LLM 출력 채점 통합 실습)를 오늘 시작했으나 TODO 1\~3이 아직 `NotImplementedError` 상태로 미완료 — 주말로 이월

## 2026-09-09\~10 · Prompt Engineering에서 PEFT까지, 텍스트 생성과 Chat Template 이론

- 8강(8-1,8-2,8-4,8-5강): Prompt-only→Prompt-tuning→PEFT→Full Fine-tuning 스펙트럼, Prompt-only baseline 4요소(평가셋/template/schema/metric), LoRA 저랭크 근사(`h=Wx+BAx`)와 `r`/`lora_alpha`/`target_modules`, Prompt-only vs Fine-tuned 공정 비교와 Regression 확인
- 9강(9-1\~9-5강): Forward pass vs `generate()` autoregressive loop, `max_length` vs `max_new_tokens`, Greedy vs Sampling vs Beam, Temperature/Top-k/Top-p, Chat message role(system/user/assistant)과 `apply_chat_template()`/`add_generation_prompt` 디버깅 흐름
- 어제(8·9강) 이론만 정리, 실습 노트북은 아직 없음 — 주말로 이월

## 2026-09-06\~08 · 종합 과제: 기초 수학과 딥러닝 기초

- 기초 수학 종합 과제: 문서 임베딩·Cosine Vector Search, 고유값 분해 기반 PCA, SVD 저랭크 압축, Causal Attention forward+vocabulary softmax/loss+autograd 1-step SGD까지 4문제(공식 20점) 제출 완료
- 딥러닝 기초 종합 과제: 데이터 분할·DataLoader 검사, ImageMLP/CNN 완성, 학습·검증 루프 공정 비교, best checkpoint 저장·복원·재개까지 4단계 + 최종 test·자동 검증 제출 완료
- 지난주 부여, 마감 기한에 맞춰 이번 주(주말+월+화)에 집중 작업 — 이 기간 동안 5·6장 실습을 진행하지 못함
- 정규 강의 실습과 분리해 `assignments/` 폴더에 별도 보관

## 2026-09-06\~08 · 텍스트 분류 Fine-tuning 이론 + 7-1 실습

- 7장(7-1,7-2,7-3,7-5,7-6,7-7,7-8강) 이론 정리: 문제 정의 5요소 → DatasetDict/Stratified Split → Tokenization Mapping/DataCollator → compute_metrics(Accuracy vs Macro-F1) → TrainingArguments/Trainer 6대 부품 → Fine-tuning 실행/Checkpoint 관리 → Error Analysis/리포트까지 전체 파이프라인 흐름
- 7-1 실습만 완료: 텍스트 정규화 후 빈 문장·허용 안 된 label·중복 감사, label 분포/imbalance ratio 계산, train-validation 간 정확 중복+Jaccard 기반 near-duplicate leakage 탐지
- 7-2\~7-8 실습은 과제 마감으로 시간이 부족해 주말(2026-09-12\~13)로 이월

## 2026-09-06\~08 · 사전학습 언어모델과 Hugging Face Hub 이론

- 5장(5-1,5-2,5-4강): 사전학습·LM Objective의 큰 그림, Masked LM(BERT, 양방향 문맥)과 Causal LM(GPT, 왼쪽 문맥) 비교, BERT의 special token·입력 표현 3요소, GPT의 Causal Self-Attention·한 칸 shift·Autoregressive Generation
- 6장(6-1,6-3,6-4,6-5강): Hugging Face Hub 구조와 Model Card 체크리스트, AutoClass의 config 기반 자동 클래스 선택과 Base/Task-specific 출력 차이, Masked Mean Pooling, 모델+tokenizer 저장/재로드 재현성 검증 흐름
- 두 챕터 모두 실습 노트북 없이 이론만 정리, 실습은 주말(2026-09-12\~13)로 이월

## Attention과 Multi-Head Attention 실습 (완료)

- Q·K·V projection 함수와 Query별 최상위 Key 찾기, softmax+threshold 기반 관계 리포트 구현
- Scaled Dot-Product Attention 전체 구현(scale → mask → softmax → weighted sum), padding mask와 `[B,T,D]` batch attention까지 확장
- Attention weight를 Value 가중합으로 분해해 context vector 기여도 계산, Shannon entropy로 attention 집중도 측정, 여러 head의 최상위 관계 일치(unanimous) 확인
- `nn.Module` 기반 학습 가능한 `SelfAttention`과 padding mask를 지원하는 `MaskedSelfAttention` 작성 (parameter 수 계산까지 검증)
- `split_heads`/`merge_heads` shape 변환과 `MultiHeadSelfAttention` 전체 구현, GQA의 KV Cache 절감 배수 계산, shape trace 디버거로 첫 번째 계약 위반 지점 탐지
- softmax의 `dim=-1` 이유, 스케일링을 head 분리 전/후 `hidden_size`/`head_dim` 중 무엇으로 하는지, `unsqueeze`가 선택이 아니라 차원 추가라는 점 등 Q&A로 정리
- 오늘 목표(3-1\~3-5)를 모두 완료해 주말로 이월할 항목 없음

## Attention과 Multi-Head Attention 이론

- Q/K/V는 입력에 서로 다른 학습된 projection을 곱한 결과이며, `Q=K=V=X`는 값이 아니라 입력 출처가 같다는 뜻
- `softmax(QKᵀ/√d_k + M)V` 연산 순서(scale → mask → softmax → weighted sum)를 고정 순서로 확인
- mask는 반드시 softmax 이전에 적용해야 확률 행 합이 정확히 1로 유지됨(사후 적용 시 합이 깨짐)
- Padding mask(`[B,L_k]`, 샘플마다 다름)와 Causal mask(`[L_q,L_k]`, `torch.tril()`)의 목적·shape 차이, 라이브러리마다 반대인 boolean 의미 주의
- Multi-Head의 `split_heads`(view+transpose)/`merge_heads`(transpose+contiguous+reshape) 축 변환과, `transpose` 뒤 `contiguous()`가 필요한 이유(메모리 재정렬 없이는 reshape가 불안전)
- `W_O`가 head별 결과를 실제로 섞어주는 유일한 지점이라는 것, Multi-Head일 때만 merge 직후 한 번 사용
- 아직 실습 코드는 작성하지 않아 이론 정리만 완료

## 데이터 스키마 감사와 토큰화 (완료)

- 2-2: `AutoTokenizer` 특수 토큰 인코딩, 즉석 동적 padding(`padding=True`), `BatchEncoding` field·shape·PAD-mask 일치 검증
- 2-3: `DataCollatorWithPadding`으로 나중에 패딩하는 방식, `Dataset`/`DatasetDict.map()`으로 train/validation/test 동일 전처리, split id disjoint(누수 없음) 검증
- 2-1 심화: 작은/큰 vocabulary의 평균 token 수·UNK 수·embedding parameter 수 비교 → 큰 vocabulary가 무조건 좋지 않은 이유
- 2-2 심화: fast tokenizer `offset_mapping`으로 subword-원문 문자 범위 매핑
- 2-3 심화: 원본 token 길이 분포 기반 `max_length` 후보별 절단률 비교, 최소 절단 후보 선택
- 어제 미완료였던 2-2·2-3 기본을 포함해 Chapter 2 전체(기본+심화) 완료, 주말로 이월할 항목 없음

## RNN/LSTM의 한계와 Transformer 등장 배경 (심화)

- 1-1 심화: 긴 문맥·병렬 학습·streaming 조건으로 RNN/LSTM vs Transformer 첫 baseline을 추천하는 규칙 기반 함수, 실제 benchmark를 대체하지 못하는 한계 정리
- 1-2 심화: `sort_keys=True` + `separators=(",", ":")` canonical JSON과 SHA-256 hash로 실험 설정 식별자 생성 → key 순서 무관 동일 hash, `seed` 변경 시 hash 변경 검증
- Chapter 1 전체(기본+심화) 완료

## RNN/LSTM의 한계와 Transformer 등장 배경

- 수동 RNN hidden state 구현(`tanh(token @ W_x + hidden @ W_h)`)으로 순차 의존성을 직접 확인 → 첫 token만 바꿔도 마지막 상태가 달라짐
- RNN 경로 길이(`length-1`)와 Self-Attention 경로 길이(`1`), attention score 원소 수(`length²`)를 나란히 비교 → 길이가 32배가 되면 score 수는 1,024배
- "경로가 짧다"가 "계산량이 항상 작다"를 의미하지 않는다는 점을 수치로 확인
- workflow 체크리스트에서 `Counter`로 누락·중복을 함께 계산하고, 필수 단계 집합에 투영해 순서 오류까지 검증
- classification(`AutoModelForSequenceClassification`, `[B,C]`)과 generation(`AutoModelForCausalLM`, `[B,L,V]`)의 model head·loss·metric·후처리 계약을 분기로 정리

## 데이터 스키마 감사와 토큰화 (일부)

- 뉴스 샘플에서 필수 key 누락·공백 텍스트·중복 ID·허용되지 않은 label을 한 번에 감사하는 함수 작성, 오류가 있어도 모든 행을 검사해 하나의 report로 반환
- `Counter`로 ID 중복과 label 분포를 함께 집계, 허용된 label만 분포에 포함
- greedy longest-match 방식의 toy subword tokenizer 구현 → 시작 위치마다 가장 긴 등록 조각을 우선 선택, 중간 조각에는 `##` prefix, 분해 실패 시 단어 전체를 `[UNK]`로 처리
- `[CLS]`/`[SEP]`를 포함한 전체 token·ID 왕복 확인
- 2-2·2-3은 오늘 완료하지 못해 [주말 실습 백로그](./WEEKEND_PRACTICE_BACKLOG.md)로 이월

## CNN 설계, 학습, 리포트

- grayscale/RGB에 맞춘 `in_channels` 선택과 filter progression으로 Conv block 구성
- dummy 입력을 통과시켜 classifier `in_features`를 자동 계산 → 이미지 크기 변화에 안전
- Tensor 메모리를 `numel() * element_size()`로 계산하고 batch size·CPU/GPU 환경별 변화 확인
- filter 수·kernel size를 바꾼 CNN variant를 같은 batch로 비교하되 one-step loss는 참고용으로만 사용
- MLP baseline과 CNN을 같은 seed·DataLoader generator로 공정 비교 → validation loss 기준 CNN이 우세
- `{**config, **metric}`으로 실험 row 생성, best epoch·loss gap 계산, 리포트 문장 자동 생성
- `nn.Module` 상속 CNN 클래스 작성, `eval()`+`no_grad()`+`softmax`+`argmax`로 사람이 읽을 수 있는 추론 결과 정리

## RNN 시퀀스 모델링과 경사 안정성

- sequence 데이터를 `[batch, seq_len, input_size]`로 구성하고 `nn.RNN`의 `output`/`h_n` shape 해석
- `batch_first=False`일 때 `[seq_len, batch, input_size]`로 permute 필요, 단층 RNN에서 `output[:, -1, :]`와 `h_n[-1]` 값 일치 확인
- `num_layers=2`로 쌓으면 `h_n` 첫 차원이 층 수가 되고 마지막 층(`h_n[-1]`)을 분류기에 사용
- 반복 `tanh` 연산으로 step이 늘어날수록 gradient가 작아지는 경사 소실을 직접 확인
- 전체 파라미터 gradient의 global L2 norm(`sqrt(sum(grad**2))`)으로 학습 신호 크기 모니터링
- `clip_grad_norm_`으로 gradient clipping 적용, clipping 전후 norm 비교로 안정화 효과 확인

## 2026-08-31 · 질문 정리

- `requires_grad`, `ones_like`, `atol`, `/` vs `//` 등 PyTorch 기초 표기 재정리
- `Conv2d` 출력 shape 계산식과 `padding = kernel_size // 2`("same padding") 공식
- MLP는 완전연결이라 파라미터가 입력 크기에 비례해 폭증하지만, CNN은 지역 연결+가중치 공유로 파라미터 수가 고정된다는 차이
- sigmoid/tanh의 기울기 소실 원인과 ReLU의 장단점(Dying ReLU 포함)
- RNN의 `output`/`h_n` shape 차이, `seq_len`과 `hidden_size`가 서로 독립적인 값이라는 점
- 딕셔너리 언패킹 `{**config, **metric}`과 `tensor_mb` 메모리 계산 공식

## 건강과 시간 문제로 미룬 항목

- 10-1·10-2는 건강 문제로 진행하지 못해 완료 처리하지 않음
- 9장 별도 심화는 기본 흐름과 10장 복습 뒤 시간이 남을 때 진행
- 12-4의 `loss_value` 미정의 버그 수정 및 재실행 예정

## 2026-08-27 · 실험 재현성과 결과 관리

- Python·NumPy·PyTorch·CUDA seed와 split·DataLoader generator를 함께 관리
- seed 고정은 재현성을 높이지만 버전·장치·연산이 다르면 완전히 같은 결과를 보장하지 않음
- `config.json`과 epoch metric log로 실험 조건과 결과를 분리해 기록
- model·optimizer의 `state_dict`와 완료 epoch·history를 checkpoint로 구성
- `torch.load()`는 파일을 읽고 `load_state_dict()`는 읽은 값을 객체에 실제로 주입
- `last.pt`는 재개용, `best.pt`는 validation 기준 평가·추론용으로 구분
- 정확한 재개 범위를 완료 epoch 다음 경계로 한정하고 난수·loader generator 상태까지 복원
- 한 번의 실험에서 생긴 config·metrics·checkpoint·plot을 하나의 run directory로 연결

## 2026-08-27 · 질문 정리

- `json.dump()`는 파일 저장, `json.dumps()`는 JSON 문자열 반환
- `indent`는 가독성, `ensure_ascii=False`와 UTF-8은 한글 저장을 위한 설정
- 파일 모드 `w`는 덮어쓰기, `a`는 이어쓰기, `r`은 읽기
- `json_text[:80]`은 저장 전 JSON 문자열의 앞부분만 확인하는 slicing
- `map_location="cpu"`로 GPU checkpoint를 CPU 환경에서 읽는 방법
- `Path.unlink()`와 `shutil.rmtree()`의 파일·폴더 삭제 범위 차이
- `make_exp_dir()`에서 만든 상세 경로를 상위 `Path(root)`로 다시 덮어쓰지 않아야 함

## 2026-08-26 · 데이터 파이프라인

- `Dataset`은 sample 단위 접근, `DataLoader`는 batching과 shuffle을 담당
- transform은 전체 전처리이며 augmentation은 transform의 일부
- train 통계로 모든 split을 정규화해 validation 정보 누수 방지
- `SubsetWithTransform`으로 train augmentation과 validation·test transform 분리
- split용 seed와 shuffle용 seed를 분리해 재현 범위 명확화
- 첫 batch의 shape·dtype·device·finite 값과 forward 출력을 먼저 검사

## 2026-08-26 · End-to-End MLP

- `nn.Module → loss·optimizer → train → validation → metric → history` 연결
- 학습에서는 gradient와 parameter update를 사용하고 검증에서는 `torch.no_grad()` 사용
- batch 평균 Loss에 `y.shape[0]`을 곱해 sample 수 기준 epoch Loss 계산
- validation 중 parameter가 변하지 않는지 epoch마다 감사
- validation Loss로 best epoch를 고르고 test는 최종 한 번만 확인
- 8-8 종합 실습을 완료했지만 8-1\~8-7 개별 흐름은 주말 복습 대상으로 유지

## 질문과 새로 알게 된 점

- `total_loss = seen = 0`: 두 누적 변수를 동시에 0으로 초기화하는 다중 할당
- `torch.enable_grad() if training else torch.no_grad()`: mode에 따른 가변 gradient context
- `valid_unchanged &= condition`: 모든 validation에서 조건이 유지되는지 논리 AND 누적
- `min(range(len(values)), key=values.__getitem__)`: 최솟값 자체가 아닌 index 반환
- `y.shape[0]`: 현재 batch의 실제 sample 수
- `unbiased=False`: 표준편차 계산 시 `N`으로 나누는 설정
- epsilon: 표준화에서 0으로 나누는 오류를 막는 작은 값

## 2026-08-25 · Autograd와 안전한 평가

- 계산 그래프와 Chain Rule, leaf·non-leaf Tensor의 gradient 저장 위치
- `requires_grad`, `backward()`, gradient 누적과 표준 step 순서
- `grad is None`과 값이 0인 gradient의 의미 구분
- `model.eval()`과 `torch.no_grad()`, 학습 Loss 경로와 metric용 `detach()` 구분
