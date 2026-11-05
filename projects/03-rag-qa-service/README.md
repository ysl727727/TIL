# RAG 프로젝트(3) 진행 기록: 문서 근거 Q&A 서비스 — 데이터 · 검색 담당

> KANT 3차(심화) 프로젝트 "RAG 기반 Q&A 서비스"의 진행 기록이에요. 팀 ADEN에서 **A 데이터 · 검색**(PDF 추출 · 청킹 · 색인 · 검색 3종 · 검색 실패 분석)을 맡았어요. 날짜별로 한 일을 쌓고, 끝나면 회고로 정리할 예정이에요. 팀 코드와 데이터, API 키는 올리지 않아요.

## 1. 프로젝트 한눈에

| 항목 | 내용 |
|---|---|
| 언제 | 2026-11-05 시작 |
| 누가 | 팀 ADEN. A 데이터 · 검색(나), B 답변 생성 · API · 통합, C 기록 · 평가 |
| 무엇을 | 해운 문서 PDF를 근거로 답하는 Q&A 서비스. 문서명 · 페이지를 표시하고, 조건이 빠지면 되묻고(clarify) 근거가 없으면 보류(abstain) |
| 어떻게 | FastAPI + LangChain + Langfuse(필수), 생성 모델 `gpt-6-luna`, E5 임베딩 + Qdrant Cloud |
| 비교 | RAG 3종 **Naive / Hybrid(BM25 + RRF) / Hybrid + Reranker** — 같은 질문, 같은 설정 |
| 평가 | Hit@k · Recall@k, RAGAS Faithfulness, LLM-as-a-Judge(사실 · 조건 · 근거 · 판단), 보안 답변 4개(보안 질문 2개 × 기본 / 방어 프롬프트), 응답 시간 · 오류율 · 토큰 |

## 2. 진행 일지

| 날짜 | 한 일 | 결과 |
|---|---|---|
| 11-05 | 발제 확인, 데이터셋 비교, 팀 저장소 clone → `feat/basic-data-search`. 해운 Basic으로 PDF 추출 → 청킹 → 임베딩 → Qdrant Cloud 색인 → Naive 검색 → Hit / Recall 점검(PR #2). PR 코드를 파일별로 읽으며 흐름 공부 | development Hit@5 0.929 · Recall@5 0.564 · Recall@20 0.867 |

## 3. 데이터셋

| | Basic | Intermediate | Advanced |
|---|---|---|---|
| PDF | 15개 × 24쪽 | 50개 × 60\~95쪽 | 120개 × 150쪽 |
| 표 | 없음 | 거의 모든 페이지 | 거의 모든 페이지 |

- 분야는 금융 · 제조 · 해운 3개, 질문 24개는 세 난이도에 공통으로 들어 있어요.
- 해운을 고른 이유: 예약번호 · 장비번호 같은 **코드성 식별자가 많아서** Hybrid(BM25)가 Naive보다 나아지는 걸 보여 주기 좋아요.

## 4. 개념 정리

### 색인(Indexing)
검색할 수 있게 미리 정리해 두는 작업이에요. 이 프로젝트에서는 PDF → 청크 → 벡터 → Qdrant 저장까지를 뜻해요.

### Qdrant 로컬 vs 클라우드

| 방식 | 저장 위치 | 특징 |
|---|---|---|
| `QdrantClient(":memory:")` | 메모리 | 프로그램이 끝나면 사라짐 (강의안 방식) |
| `QdrantClient(path=...)` | 내 PC 파일 | 나만 씀 |
| **Qdrant Cloud** | 서버 | 팀원이 같은 색인을 공유 → 우리 팀은 **처음부터 Cloud만** 사용 |

- 무료 티어: RAM 1GB, vCPU 0.5, 디스크 4GB, 카드 등록 없음. **1주일 동안 안 쓰면 일시정지, 4주가 지나면 삭제**
- 용량 추정 (해운만, 청크 하나 = 384차원 벡터 + payload)

| | 청크 | RAM | 디스크 |
|---|---|---|---|
| Basic | 620 | 약 1.5MB | 약 3MB |
| Intermediate | 약 7,700 | 약 18MB | 약 37MB |
| Advanced | 약 28,000 | 약 65MB | 약 135MB |

→ Advanced까지 늘어나도 무료 티어로 충분해요.

- API 키는 **클러스터마다 따로** 만들고(Cluster Detail → API Keys), **만들 때 한 번만 보여 주니까** 바로 `.env`에 저장해요.
- `QDRANT_URL`, `QDRANT_API_KEY`는 `.env`에 두고 git에서 제외(`.gitignore`). 코드는 `load_dotenv()`로 읽어요. 키는 코드 · 문서 · 로그 · 채팅에 절대 붙여 넣지 않아요.
- 컬렉션 이름 `basic_multilingual-e5-small_p800` = 데이터 폴더 + 모델 + 청크 글자 수. 클러스터를 팀이 같이 쓰니까, 같은 이름이 이미 있으면 `--recreate` 없이는 지우지 않고 멈추게 했어요.

### 왜 PDF를 페이지 단위로 먼저 나누나?
- `.pdf`를 떼는 건 `book_id`(문서 이름표)를 만드는 일이고, 페이지 나누기는 **몇 쪽인지** 알아내는 일이라 목적이 달라요.
- 출처에 페이지 표시가 필수라서, 페이지별로 읽어야 청크마다 `page` 값이 따라와요.
- 청크가 두 페이지에 걸치면 출처가 애매해져요 → **청크는 페이지 경계를 넘지 않게** 잘라요.
- 페이지마다 머리말(ID | 부서, 제목, 소제목)과 꼬리말(`n / 24`)이 반복돼요 → 꼬리말은 지우고, 머리말은 `heading`으로 청크 앞에 붙여요.
- pypdf도 원래 페이지 단위로 텍스트를 줘요.

### 청킹 방식 비교 (정답 근거 인용 258개로 확인)

| 방식 | 인용 보존 | 문제 |
|---|---|---|
| 페이지 통째 | 100% | 360쪽 중 106쪽이 E5 한도 512토큰을 넘어 **뒷부분이 잘린 채 임베딩됨** |
| **문단 800자 (선택)** | 98.1% | 최대 482토큰, 한도 안 |
| 글자 500 / overlap 100 | 84.1% | 문장 중간에서 잘림 |

- 인용 보존 = 정답 근거 인용문이 청크 하나 안에 끊기지 않고 들어 있는 비율
- 결과: 360쪽 → 청크 620개 (청크 2개인 페이지 260개, 1개인 페이지 100개)
- `heading`은 **색인할 때만** 본문 앞에 붙여요. LLM 문맥에 들어갈 `text`는 본문만.

### 데이터 모양을 dataclass로 정의하는 이유
- `PageDocument`(페이지 텍스트) → `Chunk`(검색 단위 조각) → `RetrievedChunk`(청크 + 순위 + 점수 + 검색 방식)
- 데이터셋을 셋으로 나눈 게 아니라 **같은 데이터가 단계마다 바뀌는 모양**을 정한 거예요.
  - 페이지일 땐 아직 `chunk_id`가 없어요.
  - 순위 · 점수는 청크가 아니라 **질문**에 따라 달라져요 → `RetrievedChunk`가 `Chunk`를 안에 품고 `rank`, `score`, `retriever`만 덧붙여요.
- 클래스로 정의하면 A · B · C가 **같은 데이터 모양을 약속**으로 공유할 수 있고, 필드 이름 오타나 누락도 바로 드러나요.
- `@dataclass`: `__init__` 같은 반복 코드를 자동으로 만들어 줘요 (보강 2주 1일 [클래스](../../python-basics/06-classes/)).
- `frozen=True`: 만든 뒤 값을 바꿀 수 없어요 → 여러 단계를 거쳐도 데이터가 몰래 바뀌지 않아요 (`chunk.page = 3` → `FrozenInstanceError`).
- `asdict(chunk)`로 dict로 바꿔 Qdrant에 저장하고, `Chunk(**payload)`로 다시 복원해요.
- 다른 선택지: dict는 키 오타(`"pgae"`)를 실행해 봐야 알고 필드 목록이 코드에 안 보여요. Pydantic은 입력 검증이 필요한 API 요청 · 응답(B 담당)에 맞고, 내부 데이터는 표준 라이브러리로 충분해요.

### Dense 검색과 E5
- **dense 검색 = 임베딩 벡터끼리 의미가 가까운지 비교하는 검색.** 지금의 Naive가 이 방식이에요.
- 모델: `intfloat/multilingual-e5-small` (384차원, 최대 512토큰)
- E5 규칙: 문서는 `"passage: "`, 질문은 `"query: "`를 앞에 붙여 임베딩
- 장점: "보관료" ↔ "저장 비용"처럼 표현이 달라도 찾아요.
- 약점: `GRTU552903` 같은 코드는 의미가 없어서 정확히 그 번호가 있는 청크를 놓칠 수 있어요.

### Naive → Hybrid → Reranker
- **BM25**: 단어가 글자 그대로 겹치는 청크를 찾음. 코드 · 번호에 강함
- **RRF**: dense 순위와 BM25 순위를 `1/(60+순위)`로 합침. 점수 단위가 달라서 순위로 합쳐요.
- **Hybrid = dense + BM25 + RRF** → dense를 BM25로 바꾸는 게 아니라 **같이 쓰는 것**
- **Reranker**: 후보 20\~50개를 cross-encoder가 질문과 한 쌍씩 다시 읽어서 정밀하게 재정렬
- Naive는 그대로 두고, 비교할 모드를 새로 추가하는 구조예요 (`retrieve(question, mode, ...)`).
- 그 밖의 검색 보강(선택): 메타데이터 필터, 쿼리 재작성 / Multi-query, HyDE, 표 청킹, overlap, parent-child

### 메타데이터(payload)
- Qdrant의 한 칸 = **[청크 텍스트의 벡터] + 꼬리표 {book\_id, page, text, heading ...}**
- 벡터가 되는 건 **청크 텍스트뿐**이고, 문서 ID나 페이지는 벡터 옆에 붙은 메타데이터예요. 검색 결과에서 이 값을 꺼내 출처 표시와 채점에 써요.

### 파이썬 패키지 vs 모듈
- **모듈** = `.py` 파일 하나 (예: `chunker.py`), **패키지** = 모듈을 묶은 폴더 (`__init__.py`가 있음, 예: `app/ingestion/`)
- `from app.ingestion.chunker import chunk_pages` = app 패키지 → ingestion 패키지 → chunker 모듈 → 함수 (보강 2주 2일 [모듈 · 패키지](../../python-basics/07-modules-exceptions-pytest-logging/))
- `scripts/`는 `__init__.py`가 없어도 `python -m scripts.build_index`로 실행돼요. 단, **저장소 루트에서** 실행해야 `app`을 찾아요.

## 5. 코드 흐름: PDF 한 장이 검색 결과가 되기까지 (SB02 5쪽 예시)

| 단계 | 코드 | SB02 5쪽에서 일어난 일 |
|---|---|---|
| 0. 접속 확인 | `build_index.py` → `connect()` | `.env`를 읽고 Qdrant부터 연결. 키가 없으면 PDF 처리 전에 바로 멈춤 |
| 1. 페이지 추출 | `loader.extract_pages` | pypdf → `PageDocument("SB02", "SB02.pdf", 5, text)`, 26줄 1,214자 |
| 2. 머리 · 꼬리 떼기 | `chunker._parse_page` | 꼬리말 `5 / 24` 버림, 앞 3줄 = 문서ID · 부서 / 제목 / 소제목, 본문 22줄 |
| 3. 줄 → 문단 | `_join`, `_paragraphs` | PDF 줄바꿈 이어 붙이기("대수" + "가" → "대수가"), `다.`로 끝나는 줄에서 문단 끊기 → 문단 5개 |
| 4. 800자 채우기 | `_pack` | 205 + 193 + 302자 → 702자. 다음 206자를 넣으면 909자라서 끊음 → 702자, 425자 |
| 5. Chunk 생성 | `chunk_pages` | `SB02-p5-c1`, `SB02-p5-c2` + heading |
| 6. 임베딩 | `Embedder.embed_passages` | `"passage: " + heading + 본문` → 길이 1로 정규화한 384차원 벡터 |
| 7. 업로드 | `build_vector_index` | 벡터 + payload(`asdict(chunk)`) → Qdrant Cloud |
| 8. 자체 점검 | `build_index.py` | 청크 본문으로 검색하면 자기 청크가 1위인지, 색인 수 = 청크 수인지 확인 |
| 9. 질문이 오면 | `retrieve` → `dense_search` | `"query: " + 질문` → 가까운 20개 → `RetrievedChunk(chunk, rank, score, "dense")` |

**코드 리뷰하면서 알게 된 점**
- `_parse_page`는 Basic PDF 틀(앞 3줄이 제목)을 전제해요 → Intermediate 데이터가 오면 PDF 틀부터 확인해야 해요.
- 줄 이어 붙이기 규칙만으로는 띄어쓰기가 약 3% 틀려요("준비 상태" → "준비상태"). Dense엔 영향이 작고, BM25는 글자 2개(bigram) 단위로 쪼개서 대응할 예정이에요.
- 문단 하나가 800자를 넘어도 자르지 않아요 → 대신 build\_index에서 토큰 수를 세서 512 초과가 없는지 확인해요 (최대 482).
- `upload_points`는 기본값이 업로드 완료를 기다리지 않아요(`wait=False`) → 바로 개수를 세면 틀려서 `wait=True`로 해결했어요.
- payload 키 = `Chunk` 필드 이름 → 계약 타입이 바뀌면 색인을 다시 만들어야 해요.
- 포인트 id가 순번(0, 1, 2…)이라 문서 일부만 추가하는 건 안 돼요. 지금은 항상 전체를 다시 만들어서 괜찮아요.

## 6. 평가: 골든 데이터셋과 Hit@k / Recall@k

### 골든 데이터셋
질문마다 사람이 미리 정해 둔 정답이 붙어 있는 평가용 세트예요 (발제 제공).

| 필드 | 뜻 | 쓰는 곳 |
|---|---|---|
| `question` | 사용자 질문 (입력으로 사용) | 검색 · 생성 |
| `reference_answer` | 모범 답안 | Judge |
| `required_facts` / `forbidden_claims` | 반드시 들어갈 사실 / 들어가면 안 되는 주장 | Judge |
| `expected_action` | answer / clarify / abstain | 판단 채점 |
| `evidence_groups` | 근거 문서 · 페이지 · 원문 인용 | Hit / Recall |

- 질문은 시험 문제라서 입력으로 써도 돼요. **정답 필드는 채점에만** 써요 (검색어 · 필터 · 프롬프트에 넣으면 안 됨).
- "한 번만"이 아니라 "채점에만". 같은 정답으로 여러 방식을 채점해야 공정한 비교가 돼요.
- 질문만 담긴 `*_questions.json`으로 검색을 먼저 다 돌리고, **검색이 끝난 뒤에야** 정답 파일을 열어요 (RAG 8장 · LLMOps 2장의 시험지 · 답안지 분리).

### 채점 흐름 (검색만, LLM 없음)
1. 질문 → E5로 벡터화
2. Qdrant의 청크 벡터와 비교해서 상위 k개 선택
3. 뽑힌 청크의 메타데이터에서 `book_id`를 꺼냄
4. 골든 데이터의 정답 문서 ID와 비교

- **Hit@k**: 정답 문서가 하나라도 있으면 1
- **Recall@k**: 찾은 정답 문서 수 ÷ 전체 정답 문서 수
- 발제 예시: 정답이 A · B인데 A만 찾으면 Hit 1, Recall 0.5. 단, A만으로 충분히 답했다면 **답변은 정답일 수 있음** (답변 채점은 별도)
- 정답 문서가 없는 질문은 N/A로 두고 평균에서 빼요 (각 세트 30문항 중 2문항).

### Naive 결과 (해운 Basic, k=5, Qdrant Cloud)

| | Hit@5 | Recall@5 | Recall@20 | 검색 시간 중앙값 |
|---|---|---|---|---|
| development 28문항 | 0.929 | 0.564 | 0.867 | 142ms |
| additional 28문항 | 0.929 | 0.641 | 0.872 | 140ms |

- 관련 문서를 하나는 거의 항상 찾지만, **근거 문서가 여러 개 필요한 질문에서는 절반 정도를 놓쳐요.**
- 예: S-DEV-01은 정답이 SB01 · SB14인데, 상위 5개 중 4개를 SB01이 차지해서 SB14를 놓침 → Hybrid / Reranker로 개선해 볼 지점
- Recall@20은 0.87 → 정답 문서 대부분이 **후보 20개 안에는 있어요.** 순서만 잘 바꿔도(Reranker) 올라갈 여지가 커요.
- 로컬에서 Cloud로 옮겨도 점수는 똑같고, 검색 시간만 약 10ms → 140ms로 늘었어요 (네트워크 왕복).

### 왜 검색 담당(A)이 Hit / Recall을 먼저 쟀나?
- 답변 없이 검색 결과만으로 채점할 수 있어서, B · C 작업을 기다리지 않고 검색이 근거를 찾는지 숫자로 확인할 수 있어요.
- Hybrid / Reranker를 붙였을 때 비교할 **기준점**이 돼요.
- 공식 수치는 B가 고른 최종 문맥으로 C가 다시 측정해요 → A의 것은 **검색 점검용**이에요.

## 7. Git 협업 흐름

- 팀 저장소 **clone** → 작업 **브랜치** → 커밋 → push → **PR** → 리뷰(B) → **merge** → main 반영 (보강 2주 3일 [git · Git Flow](../../python-basics/08-git-gitflow-github/))
- 브랜치 이름은 사람이 아니라 **작업 기준**: `종류/작업` (feat, fix, docs, refactor, test, chore). 예) `feat/basic-data-search`
- 커밋 메시지: `종류(영역): 변경 내용`. 예) `feat(ingestion): PDF 페이지 추출과 문단 800자 청킹`
- 다른 사람 담당 파일(`.gitignore`, `pyproject.toml`, `.env.example`)은 직접 고치지 않고 PR 본문에 요청으로 남겨요.
  - 그 전까지 내 PC에서만 git이 무시할 파일은 `.git/info/exclude`에 적어요 (데이터 · 산출물 폴더).
- 이미 push한 커밋 메시지 고치기
  - `git filter-branch --msg-filter`로 메시지만 수정 → 코드는 같아도 **커밋 해시가 전부 바뀜**
  - 그래서 강제 push가 필요해요. `--force-with-lease`는 그 사이 다른 사람이 push했다면 덮어쓰지 않고 멈춰서 `--force`보다 안전해요.
  - 수정 전 상태는 백업 브랜치로 남겨 둬요.

## 8. 팀 역할 (Basic 계획서 기준)

| 역할 | 담당 |
|---|---|
| **A 데이터 · 검색 (나)** | PDF 추출, 청킹, 색인, 검색 3종 `retrieve()`, 검색 실패 분석 |
| B 답변 생성 · API · 통합 | LangChain + gpt-6-luna 답변, FastAPI `/query`, 출처 검증, 최종 문맥 선택 |
| C 기록 · 평가 | Langfuse, RAGAS, Judge, 보안 평가, 비교표 |

- 현재: PR #2(검색, A), PR #3(답변 · API · Langfuse 연결, B, Draft)
- Naive `retrieve()`를 먼저 넘긴 이유: B가 바로 연결할 수 있고, Hybrid · Reranker는 **같은 반환 타입**으로 나중에 추가하면 돼요.

## 9. 트러블슈팅

| 증상 | 원인 · 판단 | 해결 |
|---|---|---|
| Qdrant Cloud 접속이 `ConnectError [WinError 10054]`로 끊김 | 다른 HTTPS 사이트와 DNS는 정상인데 브라우저로 클러스터 `/healthz`도 안 열림 → 내 PC가 아니라 클러스터 쪽 문제 | 클러스터를 지우고 **미국 서부 리전**에 새로 만든 뒤, 새 API 키로 `.env` 교체 |
| `get_sentence_embedding_dimension()` FutureWarning | 이름이 바뀜 | `get_embedding_dimension()`으로 변경 |
| Windows 콘솔(cp949)에서 한글 깨짐 | 콘솔 인코딩 | `sys.stdout.reconfigure(encoding="utf-8")` |

## 10. 헷갈렸다가 정리된 것

- dense = E5. "E5가 코드에 약하다"는 말은 지금의 dense 검색이 약하다는 뜻이고, 그래서 BM25를 **추가**해요.
- `sorted(Path(...).glob("*.pdf"))`는 파일을 만드는 게 아니라 **PDF 경로 목록을 메모리에 만드는 것** → PDF는 `data/basic/documents/`에 미리 넣어 둬야 해요.
- 골든 데이터의 "OR 후보" 설명은 **답변 채점용**. 검색 Recall은 발제 정의대로 문서 단위로 계산해요.
- clone과 branch는 둘 중 하나가 아니에요 → clone으로 저장소를 내 PC에 받고, 그 안에서 branch를 따서 작업해요.
- PR을 올린다고 바로 main에 들어가는 게 아니에요 → 리뷰 후 **merge해야** main에 반영돼요.
- 브랜치는 `core/ysl`처럼 담당 폴더 · 이름으로 만드는 게 아니라, 팀 git 규칙대로 작업 단위(`feat/...`)로 만들어요.

## 11. 다음 할 일

- [ ] PR #2 B 리뷰 반영
- [ ] BM25 + RRF로 `hybrid` 모드 구현
- [ ] Reranker로 `hybrid_rerank` 모드 구현 (CPU에서는 느릴 수 있으니 시간도 같이 기록)
- [ ] 3종 Hit@k / Recall@k 비교 → 검색 실패 사례 분석
- [ ] `heading`(제목 줄)을 LLM 문맥에도 넣을지 B와 결정
- [ ] Qdrant 무료 클러스터를 1주일 넘게 방치하지 않기 (정지됨)
- [ ] Naive 기준으로 평가까지 한 바퀴 완주 (팀)

## 12. 숫자 치트시트

| 항목 | 값 |
|---|---|
| 해운 Basic | PDF 15개 × 24쪽 = 360쪽 → 청크 620개 |
| 청킹 | 문단 800자, 페이지 경계 안 넘음, 인용 보존 98.1%, 최대 482토큰 |
| 임베딩 | multilingual-e5-small, 384차원, 최대 512토큰 |
| Naive (dev, k=5) | Hit 0.929 · Recall 0.564 · Recall@20 0.867 · 142ms |
| Naive (additional, k=5) | Hit 0.929 · Recall 0.641 · Recall@20 0.872 · 140ms |
| RRF | `1/(60+순위)` |
