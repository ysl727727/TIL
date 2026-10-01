# 8장. 관찰 — Streaming · Callback · Tracing

> 2026-10-01 학습 기록. 사용자에게는 답을 조각으로 바로 보여 주고, 개발자는 Callback으로 시작·조각·완료·오류 이벤트와 실행 시간·토큰 사용량을 옆에서 기록하며, 필요하면 Langfuse로 원격 trace를 보내는 흐름을 정리했습니다.

## 학습 목표

- `stream()` 조각을 반복문 한 곳에서 출력하면서 모으고, 끝나면 `"".join()`으로 합친다.
- `BaseCallbackHandler`의 이벤트 4개를 구현하고 `config={"callbacks": [handler]}`로 실행 한 번에 연결한다.
- Callback은 결과를 바꾸지 않는 관찰자이며, Handler가 여러 개여도 `invoke()`는 한 번이라는 점을 설명한다.
- 실행 시간은 `perf_counter()` 차이로, 토큰은 `usage_metadata`에서 읽고 없으면 0이 아니라 "제공되지 않음"으로 적는다.
- Langfuse는 동의·설정·패키지·인증이 모두 있을 때만 켜고, `flush()` 완료와 조회 가능을 구분한다.

## 실습 파일

| 강 | 주제 | 실습 상태 |
| --- | --- | --- |
| 8-1 | Streaming 응답과 Callback Handler | 📘 이론 정리 |
| 8-2 | LangSmith 또는 대체 tracing 도구 활용 (Langfuse) | 📘 이론 정리 |

실습 노트북은 이번 기록에 포함하지 않았습니다. 6\~10장은 이론 분량이 많아, 실습은 10장 통합 실습(`starter.py`) 하나로 정리했습니다. 아래 확인 문제는 API 없이 풀 수 있는 복습용 문제입니다.

## 전체 흐름

### 한 문장

**사용자에게는 답을 생기는 대로 바로 보여 주고(Streaming), 개발자는 그 실행이 언제 시작·끝났고 얼마나 걸렸는지 옆에서 기록합니다(Callback, Tracing).**

### 왜 필요한가

- 긴 답을 다 만들 때까지 빈 화면이면 사용자는 멈춘 줄 압니다 → **스트리밍**.
- 답이 이상하거나 느릴 때, 안에서 무슨 일이 있었는지 모르면 고칠 수 없습니다 → **Callback, Tracing**.

**비유:** 생방송과 블랙박스. 시청자는 방송을 실시간으로 보고(스트리밍), 방송국은 블랙박스에 언제 시작해서 언제 끝났는지 따로 기록합니다(Callback). 블랙박스가 방송 내용을 바꾸지는 않습니다.

### 그림으로 보기 — 두 흐름은 따로 간다

```text
[답변 흐름 — 사용자용]
question → Prompt → Model → StrOutputParser → 문자열 조각 → for문: 화면에 바로 출력 + 리스트에 모으기 → "".join()

[관찰 흐름 — 개발자용]                    Model 옆에 붙은 Callback Handler
   on_chat_model_start   → "시작" 표시, 개수 0으로, 시작 시각 저장
   on_llm_new_token × N  → 문자열 조각 개수 +1 (출력은 안 함!)
   on_llm_end            → "완료", 걸린 시간, 토큰 사용량
   on_llm_error          → "실패", 예외 이름

[8-2 선택] Langfuse Handler도 같은 실행에 붙이면 → 원격 trace로 전송 → flush() → 다시 조회해서 확인
```

### 강의 흐름

1. **8-1 보여 주기** — `prompt | model | StrOutputParser()` 체인을 `stream()`으로 실행해 `print(chunk, end="", flush=True)`로 즉시 출력하면서 리스트에 모으고, 끝나면 `"".join()`.
2. **8-1 관찰하기** — `BaseCallbackHandler`를 상속해 `on_chat_model_start` / `on_llm_new_token` / `on_llm_end` / `on_llm_error`를 구현하고 `config={"callbacks": [handler]}`로 **그 실행 한 번에만** 연결.
3. **8-2 기록하고 내보내기** — 시작 이벤트에서 `perf_counter()` 저장, 완료 이벤트에서 차이(ms)와 `usage_metadata`의 토큰 3개를 기록. Langfuse Handler는 선택적으로 같은 `callbacks` 목록에 추가, 끝나면 `flush()` → `last_trace_id`로 원격 조회.

```text
                 ┌──────────── 데이터 흐름 (사용자에게 보여 줄 답변) ────────────┐
 question dict → Prompt → Model → StrOutputParser → 문자열 조각 → for문: 출력 + 리스트에 저장 → "".join()
                            │
                            └─ 관찰 흐름 (개발자용 상태) ─ Callback Handler(들)
                                  on_chat_model_start   → 개수 0으로 / 시작 시각 저장
                                  on_llm_new_token × N  → 문자열 이벤트 개수 +1
                                  on_llm_end            → 완료 · 실행 시간 · 토큰 사용량
                                  on_llm_error          → 실패 · 예외 클래스 이름

 8-2  callbacks = [LocalTraceHandler(항상), LangfuseHandler(동의+설정+패키지+인증 모두 OK일 때만)]
      chain.invoke(..., config={"callbacks": callbacks})   ← 1회만 실행
      finally: langfuse_client.flush() → last_trace_id로 GENERATION 재조회 (2초 간격, 최대 약 60초)
```

3\~7장 → 8장 연결고리: 3-2의 `stream()`은 "조각을 받아 출력"까지였고, 8-1은 같은 실행에 **Handler를 옆에 붙여** 실행 상태를 봅니다. 8-2의 `max_retries=0`은 "invoke 1번 = 요청 시도 1번"을 맞추기 위한 설정이고, 제대로 된 Retry 정책은 9장에서 배웁니다.

## 핵심 이론

### 1. Streaming 응답과 Callback Handler (8-1강)

| 구분 | 확인하는 내용 | 실습 출력 |
| --- | --- | --- |
| 답변 흐름 | 모델이 생성한 실제 문장 | `[스트리밍 답변]` 아래 본문 |
| 실행 흐름 | 모델 호출의 시작·진행·완료·오류 | `[Callback]`으로 시작하는 상태 |

**스트리밍 체인** — 마지막이 `StrOutputParser`라서 `stream()` 반복문에서 받는 값을 문자열로 다룰 수 있습니다.

```python
collected_chunks: list[str] = []
for raw_chunk in chain.stream(input_data, config={"callbacks": [handler]}):
    chunk = str(raw_chunk)
    collected_chunks.append(chunk)           # 나중에 쓸 전체 답변용
    print(chunk, end="", flush=True)         # 사용자는 기다리지 않고 바로 봄
full_text = "".join(collected_chunks)
if not full_text.strip():
    raise ValueError("스트리밍 답변이 비어 있습니다.")
print(f"[전체 답변 자료형] {type(full_text).__name__}")   # str
```

- 조각의 개수와 경계는 실행마다 다릅니다. 한 조각 = 한 글자·한 단어라고 가정하지 않고, 내용 없는 보조 조각이 올 수도 있습니다.
- 스트리밍 출력과 전체 문자열 저장은 대체 관계가 아닙니다. 같은 반복문에서 둘 다 합니다.

**Callback Handler** — 체인·모델이 실행되는 동안 이벤트를 받는 객체입니다. 이번 강의는 4개만 씁니다.

| 메서드 | 실행 시점 | 이번 실습에서 하는 일 |
| --- | --- | --- |
| `on_chat_model_start()` | 채팅 모델 호출 시작 | 조각 개수를 0으로 초기화, 시작 표시 |
| `on_llm_new_token()` | 새 출력 조각 도착 | 내용 있는 문자열이면 개수 +1 |
| `on_llm_end()` | 모델 호출 정상 완료 | 완료 상태와 개수 출력 |
| `on_llm_error()` | 모델 호출 실패 | 예외 클래스 이름만 출력 |

```python
from typing import Any
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

class SimpleStreamingHandler(BaseCallbackHandler):
    def __init__(self) -> None:
        self.text_event_count = 0

    def on_chat_model_start(self, serialized: dict[str, Any], messages: list[list[Any]], **kwargs: Any) -> None:
        self.text_event_count = 0                       # 재사용해도 이번 실행만 세도록
        print("[Callback] 채팅 모델 호출 시작")

    def on_llm_new_token(self, token: str | list[str | dict[str, Any]], **kwargs: Any) -> None:
        if isinstance(token, str) and token:            # 내용 있는 문자열만
            self.text_event_count += 1                  # 출력은 하지 않음!

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        print()
        print(f"[Callback] 채팅 모델 호출 완료 · 문자열 이벤트 {self.text_event_count}개")

    def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
        print()
        print(f"[Callback] 채팅 모델 호출 실패 · {type(error).__name__}")
```

- Callback은 Prompt·모델 답변·Parser 결과를 **바꾸지 않습니다.** Handler를 붙여도 모델 요청이 한 번 더 발생하지 않습니다.
- `on_llm_new_token`의 이름에 token이 있지만 "출력 이벤트 조각"으로 이해합니다. tokenizer의 토큰 1개 = 호출 1번이라고 가정하지 않고, 값이 문자열이 아닐 수도 있어 `isinstance(token, str) and token`으로 확인합니다.
- 답변 본문은 **반복문 한 곳에서만** 출력합니다. Callback까지 조각을 출력하면 답변이 두 번 보입니다.
- Handler는 체인을 만들 때가 아니라 실행 설정 `config={"callbacks": [handler]}`에 넣습니다. `callbacks`는 **목록**이라 여러 개를 붙일 수 있습니다.
- `handler.text_event_count`(모델 이벤트 수)와 `len(collected_chunks)`(Parser 뒤 체인 조각 수)는 관찰 지점이 달라 **같다고 기대하지 않습니다.** 성공 기준은 합친 답변이 비어 있지 않은 것.
- 오류가 나면 `on_llm_error()`가 호출되고, 오류 자체는 체인 호출 쪽으로도 전달됩니다.
- 실행 결과 구조: `[스트리밍 답변]` → `[Callback] 채팅 모델 호출 시작` → 답변 → `[Callback] 채팅 모델 호출 완료 · 문자열 이벤트 N개` → `[전체 답변 자료형] str`. N의 크기는 답변 품질과 무관합니다.

| 자주 나는 오류 | 원인 → 해결 |
| --- | --- |
| 한 글자씩 나올 거라 예상 | 조각 크기는 일정하지 않음. 조각 경계로 문장 해석 금지 |
| `print(chunk)`로 출력 | 조각마다 줄바꿈 → `print(chunk, end="", flush=True)` |
| Callback에서도 조각 출력 | 답변이 두 번 보임 → 반복문만 출력, Callback은 상태·개수만 |
| Handler를 만들고 연결 안 함 | `config={"callbacks": [handler]}` |
| `{"callbacks": handler}` | 목록으로: `[handler]` |
| 이벤트 수 = 조각 수라고 판단 | 관찰 지점이 다름. 전체 답변이 비었는지만 확인 |

### 2. LangSmith 또는 대체 tracing 도구 활용 (8-2강)

**Tracing** = 하나의 요청이 어떤 단계를 거쳤고, 각 단계가 언제 시작·끝났는지를 연결해 기록하는 방법. 이번 강의는 `invoke()` 한 번과 원격 trace 한 건만 다루고, 대체 도구로 **Langfuse**를 씁니다.

| 관찰 값 | 의미 | 확인 위치 |
| --- | --- | --- |
| 시작·완료 | 모델 호출이 정상 진행됐는지 | 로컬 Callback |
| 실행 시간 | 모델 시작부터 완료까지 | 로컬 Callback |
| 입력·출력·전체 토큰 | 사용량 | 모델 완료 결과 (`LLMResult`) |

**실행 시간** — `time.perf_counter()`(경과 시간 측정용 단조 시계)의 차이 × 1000 = ms.

```python
def on_chat_model_start(self, serialized, messages, **kwargs):
    self.started_at = time.perf_counter()
    self.elapsed_milliseconds = None                 # 이전 실행 값 초기화
    print("[로컬 trace] 채팅 모델 호출 시작")

def on_llm_end(self, response, **kwargs):
    if self.started_at is not None:
        self.elapsed_milliseconds = (time.perf_counter() - self.started_at) * 1000
    (self.input_tokens, self.output_tokens, self.total_tokens) = extract_usage_from_result(response)
```

실행 시간은 네트워크·답변 길이에 따라 달라지므로 특정 숫자를 정답으로 고정하지 않습니다.

**토큰 사용량 읽기**

```python
message = response.generations[0][0].message       # 완료 결과 안의 AIMessage
usage = message.usage_metadata                      # {"input_tokens", "output_tokens", "total_tokens"}
```

- 읽는 순서: ① `AIMessage.usage_metadata` → ② 없으면 `LLMResult.llm_output`의 공급자별 사용량 → ③ 둘 다 없으면 `None` → 화면에 **"제공되지 않음"**.
- `read_integer()`는 **정수만** 인정합니다. `bool`은 `int`의 하위 자료형이지만 제외하고, 문자열·실수는 `None`. 문자열을 억지로 바꾸거나 토큰 값을 직접 계산하지 않습니다.
- 체인은 `Prompt | Model | StrOutputParser`라서 최종 호출자는 **문자열**을 받습니다. 토큰 메타데이터는 최종 문자열이 아니라, Model 완료 시점의 `LLMResult`를 받은 Handler에서 읽습니다.
- 실행 시간이 짧거나 토큰이 적다는 것만으로 답변 품질을 판단할 수 없습니다.

**Langfuse를 선택 기능으로 준비하기**

| 조건 | 없으면 |
| --- | --- |
| `ENABLE_LANGFUSE_UPLOAD=1` (명시적 업로드 동의) | 로컬 trace만 |
| `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL` | 로컬 trace만 |
| `langfuse` 패키지 (`uv add "langfuse==4.14.1"`) | `ImportError` → 로컬 trace만 |
| `auth_check()` 성공 | 인증 실패 → 로컬 trace만 |

- 네 가지 중 하나라도 없으면 `create_optional_langfuse_callback()`이 `(None, None)`을 반환 — **오류가 아니고**, 로컬 Handler와 모델 실행은 계속됩니다.
- `LANGFUSE_BASE_URL`은 프로젝트 지역 주소: EU `https://cloud.langfuse.com`, US `https://us.cloud.langfuse.com`, Japan `https://jp.cloud.langfuse.com`, HIPAA `https://hipaa.cloud.langfuse.com`. 키가 맞아도 지역이 다르면 인증·조회가 실패할 수 있습니다.
- `get_client()`가 객체를 돌려줬다고 인증 성공이 아닙니다 → 시작 단계에서 `auth_check()`를 **한 번만** 호출 (매 요청마다 반복하는 상태 확인용이 아님).
- Langfuse import는 **함수 안에서** 합니다. 파일 위쪽에서 import하면 로컬만 쓰려는 실행도 `ImportError`로 멈춥니다.
- 업로드를 켜면 Prompt와 답변이 외부 프로젝트에 기록될 수 있으므로 예제 질문만 쓰고 개인정보·API Key·회사 비밀은 넣지 않습니다.
- OpenAI API 사용량은 ChatGPT Plus·Pro 구독과 **별도로 과금**됩니다. 결제·사용 한도·모델 권한을 확인합니다.

**같은 실행에 두 Handler 연결하기**

```python
local_handler = LocalTraceHandler()
langfuse_handler, langfuse_client = create_optional_langfuse_callback()
callbacks: list[Any] = [local_handler]              # 로컬은 항상
if langfuse_handler is not None:
    callbacks.append(langfuse_handler)              # 선택 Handler는 있을 때만

model = ChatOpenAI(api_key=api_key, model=model_name, timeout=20,
                   max_retries=0,                   # SDK 내부 자동 Retry 끄기
                   use_responses_api=True)
raw_answer = chain.invoke({"question": SAMPLE_QUESTION},
                          config={"callbacks": callbacks, "run_name": "langchain_beginner_trace"})
```

- Handler가 두 개여도 `chain.invoke()`는 **한 번**입니다. Handler마다 체인을 따로 실행하면 모델 요청도 두 번 발생합니다.
- 다만 `invoke()` 1번이 항상 HTTP 요청 1번은 아닙니다. 자동 Retry가 켜져 있으면 일시 오류 뒤 요청이 늘 수 있어서, 이번 실습은 `max_retries=0`으로 끕니다 (Retry가 나쁜 기능이라는 뜻이 아님 → 9장).
- `run_name`은 trace에서 실행을 알아보기 쉽게 붙이는 이름이며 Prompt·답변을 바꾸지 않습니다.

**flush()와 원격 조회 검증**

```text
invoke() 완료 → handler의 last_trace_id 읽기 → flush()로 ingestion API 전송 완료
  → 같은 trace_id의 GENERATION observation 조회 (core, basic, model, usage 필드)
     → 있으면 model·usage 확인 → 원격 조회 성공
     → 없으면 2초 기다렸다 재조회 (최대 31회, 약 60초)
```

- 짧은 스크립트는 바로 끝나서 백그라운드 대기열의 trace가 못 나갈 수 있으므로 `finally`에서 `flush()`.
- `flush()` 반환 = ingestion API **전송 완료**일 뿐, 서버 처리·조회 반영 완료가 아닙니다 (보통 15\~30초 걸림). 같은 trace_id의 Generation이 실제로 조회돼야 원격 수집까지 확인한 것입니다.
- Handler 하나를 `invoke()` 한 번에만 쓰면 `last_trace_id`를 읽기 쉽지만, 여러 요청이 동시에 도는 서버에서 Handler를 공유하면 다른 요청의 ID로 바뀔 수 있습니다 → 요청별 Handler 또는 미리 정한 trace ID.
- 이 실습의 재조회는 Langfuse v4 Observations API 기준입니다 (Self-hosted v3는 범위 밖).

| 자주 나는 오류 | 원인 → 해결 |
| --- | --- |
| Langfuse가 꺼져 있으면 실습이 멈춘다고 생각 | 선택 기능 → `(None, None)`, 로컬만 계속 |
| 파일 위쪽에서 langfuse import | 함수 안에서 import, 실패 시 로컬로 |
| Parser 결과 자료형 미확인 | `answer = str(raw_answer)` |
| 토큰 수가 항상 있다고 가정 | `None`을 0으로 바꾸지 말고 "제공되지 않음" |
| invoke 1번 = HTTP 1번이라고 단정 | 자동 Retry가 있으면 늘 수 있음 → `max_retries=0` |
| Handler마다 체인을 따로 실행 | 한 `callbacks` 목록에 넣고 invoke 1번 |
| Client 생성 = 인증 성공 | `auth_check()`로 확인 |
| 짧은 실행에서 `flush()` 생략 | `finally`에서 `flush()` |
| `flush()` 완료 = 원격 조회 성공 | `last_trace_id`로 제한 시간 안에 재조회 |
| 최종 문자열에서 토큰 찾기 | Model 완료 이벤트의 `LLMResult`에서 읽기 |

## 확인 문제

모두 API 없이 풀 수 있습니다. `from typing import Any`, `from langchain_core.callbacks import BaseCallbackHandler`, `from langchain_core.outputs import LLMResult`, `from langchain_core.messages import AIMessage`가 되어 있다고 가정합니다. 각 문제 바로 아래에 정답과 해설이 있습니다. 먼저 풀어 본 뒤 확인하세요.

### 8-Q1. 조각 출력 비교 (8-1)

```python
source_chunks = ["실행", "을 ", "관찰", "합니다."]
collected = []
for chunk in source_chunks:
    collected.append(chunk)
    print(chunk, end="", flush=True)
print()
print("".join(collected))
print(len(collected), type("".join(collected)).__name__)
```

(1) 출력을 쓰세요. (2) 반복문 안을 `print(chunk)`로 바꾸면 첫 부분이 어떻게 보이나요?

> 힌트: `end=""`는 줄바꿈 대신 빈 문자열을 붙입니다.

<details>
<summary>정답 보기</summary>

(1)

```text
실행을 관찰합니다.
실행을 관찰합니다.
4 str
```

첫 줄은 조각이 도착할 때마다 이어서 출력한 결과, 둘째 줄은 저장한 조각을 합친 결과입니다. (2) 조각마다 줄이 바뀌어 `실행` / `을 ` / `관찰` / `합니다.`가 네 줄로 나뉘어 보입니다 (8-1 오류 2).

</details>

### 8-Q2. 이벤트와 시점 연결 (8-1)

아래 상황마다 호출되는 Callback 메서드 이름을 쓰세요.

1. 모델이 두 번째 출력 조각을 보냈다.
2. `chain.stream()`을 시작해 채팅 모델 호출이 막 시작됐다.
3. API Key가 잘못돼 모델 호출이 실패했다.
4. 모델이 답변을 끝까지 정상적으로 만들었다.

그리고 정상 실행에서 메서드가 불리는 순서를 쓰세요.

> 힌트: 정상 실행은 "시작 → 조각 여러 번 → ?" 입니다.

<details>
<summary>정답 보기</summary>

1 `on_llm_new_token()` · 2 `on_chat_model_start()` · 3 `on_llm_error()` · 4 `on_llm_end()`. 정상 순서: `on_chat_model_start` → `on_llm_new_token` × N → `on_llm_end`. 실패하면 `on_llm_end` 대신 `on_llm_error`로 가고, 예외는 체인 호출 쪽으로도 전달됩니다.

</details>

### 8-Q3. 문자열 이벤트 세기 (8-1)

```python
class TextCountHandler(BaseCallbackHandler):
    def __init__(self) -> None:
        self.count = 0
    def on_llm_new_token(self, token, **kwargs: Any) -> None:
        if isinstance(token, str) and token:
            self.count += 1

h = TextCountHandler()
for t in ["안녕", "", ["하세요"], " ", "반갑습니다", {"type": "text"}]:
    h.on_llm_new_token(t)
print(h.count)
```

> 힌트: 빈 문자열 `""`은 거짓, 공백 한 칸 `" "`은 참입니다. 리스트·dict는 `str`이 아닙니다.

<details>
<summary>정답 보기</summary>

`3`. 세는 것은 `"안녕"`, `" "`, `"반갑습니다"`입니다. `""`은 내용이 없어서, `["하세요"]`와 `{"type": "text"}`는 문자열이 아니라서 제외됩니다. `" "`처럼 공백만 있어도 파이썬에서 참이므로 세어진다는 점에 주의하세요. 실제 모델 실행에서는 LangChain이 이 메서드를 호출하고, 여기서는 조건 확인을 위해 직접 호출했습니다.

</details>

### 8-Q4. 초기화를 빼먹으면? (8-1)

8-Q3의 `TextCountHandler`(시작 이벤트 없음)를 두 번의 실행에 재사용했고, 첫 실행에서 문자열 이벤트 5개, 두 번째 실행에서 3개가 왔습니다. (1) 두 번째 실행이 끝난 뒤 `count`는? (2) 두 번째 실행만 세려면 어떻게 고치나요?

> 힌트: 값을 0으로 되돌리는 코드가 어디에도 없습니다.

<details>
<summary>정답 보기</summary>

(1) `8` — 이전 실행의 5가 남아 누적됩니다. (2) 채팅 모델 호출이 시작될 때 초기화합니다.

```python
def on_chat_model_start(self, serialized: dict[str, Any], messages: list[list[Any]], **kwargs: Any) -> None:
    self.count = 0          # 새 호출마다 이번 실행만 세도록
```

이렇게 하면 두 번째 실행 뒤 `count`는 `3`입니다.

</details>

### 8-Q5. 버그 찾기 — Handler 연결 (8-1)

세 코드가 각각 의도대로 동작하지 않는 이유를 쓰세요.

```python
# (가)
handler = SimpleStreamingHandler()
for c in chain.stream(input_data):
    print(c, end="", flush=True)

# (나)
for c in chain.stream(input_data, config={"callbacks": handler}):
    print(c, end="", flush=True)

# (다) on_llm_new_token 안에 print(token, end="")를 추가하고,
#      반복문에서도 print(c, end="", flush=True)
```

> 힌트: 연결 여부, `callbacks`의 자료형, 출력 담당이 몇 곳인지 보세요.

<details>
<summary>정답 보기</summary>

(가) Handler 객체만 만들고 `config`에 넣지 않아 **이벤트를 하나도 받지 못합니다** (오류 4). (나) `callbacks` 값은 Handler **목록**이어야 합니다 → `{"callbacks": [handler]}` (오류 5). (다) 반복문과 Callback이 모두 조각을 출력해 **같은 답변이 두 번** 보입니다. 답변 출력은 반복문 한 곳, Callback은 상태·개수만 (오류 3).

</details>

### 8-Q6. 두 개수는 같을까? (8-1)

실행이 끝난 뒤 `handler.text_event_count == 12`, `len(collected_chunks) == 14`였습니다. 버그일까요? 이 실습의 성공 기준은 무엇인가요?

> 힌트: 두 값은 서로 다른 지점에서 관찰한 개수입니다.

<details>
<summary>정답 보기</summary>

버그가 아닙니다. `text_event_count`는 **모델 Callback**이 본 문자열 이벤트 수, `len(collected_chunks)`는 **Parser 뒤 체인 반복문**이 받은 조각 수로, 관찰 경계가 달라 다를 수 있습니다 (오류 6). 성공 기준은 조각을 합친 `full_text`가 **비어 있지 않은 것**(`full_text.strip()`이 참)입니다. N의 크기로 답변 품질을 판단하지도 않습니다.

</details>

### 8-Q7. 결정적인 시계로 실행 시간 (8-2)

```python
clock_values = iter([3.0, 3.5])
def fixed_clock() -> float:
    return next(clock_values)

class TimingHandler(BaseCallbackHandler):
    def __init__(self, clock) -> None:
        self.clock = clock
        self.started_at = None
        self.elapsed_milliseconds = None
    def on_chat_model_start(self, serialized, messages, **kwargs):
        self.started_at = self.clock()
    def on_llm_end(self, response, **kwargs):
        if self.started_at is None:
            raise RuntimeError("시작 이벤트가 먼저 필요합니다.")
        self.elapsed_milliseconds = (self.clock() - self.started_at) * 1000

h = TimingHandler(clock=fixed_clock)
h.on_chat_model_start(serialized={}, messages=[])
h.on_llm_end(response=LLMResult(generations=[]))
print(f"{h.elapsed_milliseconds:.2f}ms")
```

(1) 출력은? (2) 새 `TimingHandler`를 만들고 `on_chat_model_start` 없이 `on_llm_end`부터 부르면? (3) 완성 실습에서는 `fixed_clock` 대신 무엇을 쓰나요?

> 힌트: 3.5 − 3.0 = 0.5초입니다.

<details>
<summary>정답 보기</summary>

(1) `500.00ms` — (3.5 − 3.0) × 1000. (2) `started_at`이 `None`이라 `RuntimeError: 시작 이벤트가 먼저 필요합니다.` — 잘못된 호출 순서를 즉시 알립니다. (3) `time.perf_counter` (경과 시간 측정용 단조 시계). 연습에서 고정 시계를 주입하면 결과가 항상 같아 검증하기 쉽습니다.

</details>

### 8-Q8. read_integer 결과 (8-2)

```python
def read_integer(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None

for v in [12, True, "12", 12.0, None, 0]:
    print(read_integer(v), end=" ")
```

그리고 `bool` 검사를 `int` 검사보다 **먼저** 하는 이유를 쓰세요.

> 힌트: `isinstance(True, int)`는 `True`입니다.

<details>
<summary>정답 보기</summary>

`12 None None None None 0`

`bool`은 `int`의 하위 자료형이라 `int` 검사를 먼저 하면 `True`가 정수 `True`(=1)로 통과해 버립니다. 토큰 개수로 쓸 수 없는 값이므로 먼저 걸러냅니다. `"12"`(문자열)·`12.0`(실수)도 억지로 바꾸지 않고 `None`(알 수 없음)으로 처리합니다. `0`은 정상 정수라 그대로 반환됩니다.

</details>

### 8-Q9. 토큰 사용량 읽기와 표시 (8-2)

```python
m1 = AIMessage(content="관측 완료",
               usage_metadata={"input_tokens": 12, "output_tokens": 4, "total_tokens": 16})
m2 = AIMessage(content="관측 완료")
for m in [m1, m2]:
    usage = m.usage_metadata
    if usage is not None:
        print(f"입력 {usage['input_tokens']}, 출력 {usage['output_tokens']}, 전체 {usage['total_tokens']}")
    else:
        print("토큰 사용량: 제공되지 않음")
```

(1) 출력은? (2) `m2`일 때 "입력 0, 출력 0, 전체 0"으로 표시하면 안 되는 이유는? (3) 체인이 `prompt | model | StrOutputParser()`일 때 토큰 사용량을 `chain.invoke()`의 결과에서 읽을 수 없는 이유는?

> 힌트: 없는 값과 0은 다릅니다. Parser 뒤의 결과 자료형을 떠올려 보세요.

<details>
<summary>정답 보기</summary>

(1)

```text
입력 12, 출력 4, 전체 16
토큰 사용량: 제공되지 않음
```

(2) 0은 "실제로 0개를 썼다"는 잘못된 정보가 됩니다. 모델이 값을 주지 않았으면 추측하지 않고 "제공되지 않음"으로 표시합니다 (오류 4). (3) 최종 결과는 `StrOutputParser`가 만든 **문자열**이라 메타데이터가 없습니다. 토큰은 Model 완료 시점의 `LLMResult` → `generations[0][0].message.usage_metadata`를 받는 Handler의 `on_llm_end`에서 읽습니다 (오류 10).

</details>

### 8-Q10. 선택 Handler와 업로드 조건 (8-2)

```python
def build_callbacks(local_handler, optional_handler):
    callbacks = [local_handler]
    if optional_handler is not None:
        callbacks.append(optional_handler)
    return callbacks

print(build_callbacks("local", None))
print(build_callbacks("local", "langfuse"))
```

(1) 출력은? (2) 아래 각 경우 Langfuse 원격 tracing이 켜지나요? (패키지는 설치돼 있고 인증은 성공한다고 가정)

| 경우 | `ENABLE_LANGFUSE_UPLOAD` | PUBLIC / SECRET / BASE_URL |
| --- | --- | --- |
| A | 없음 | 셋 다 있음 |
| B | `1` | BASE_URL만 없음 |
| C | `1` | 셋 다 있음 |
| D | `true` | 셋 다 있음 |

> 힌트: `has_langfuse_settings()`는 `os.getenv("ENABLE_LANGFUSE_UPLOAD", "").strip() == "1"`로 동의를 확인합니다.

<details>
<summary>정답 보기</summary>

(1)

```text
['local']
['local', 'langfuse']
```

(2) A 꺼짐 (명시적 동의 없음 — 키가 있어도 외부 전송 안 함) · B 꺼짐 (지역 주소 없음) · C **켜짐** · D 꺼짐 (정확히 `"1"`이어야 함). 꺼진 경우에도 오류가 아니라 `(None, None)`이 반환되고 로컬 Handler만으로 실행이 계속됩니다.

</details>

### 8-Q11. 요청 횟수 (8-2)

```python
model = ChatOpenAI(model=model_name, max_retries=0)
chain = prompt | model | StrOutputParser()
callbacks = [LocalTraceHandler(), langfuse_handler]
chain.invoke({"question": "tracing은 왜 필요한가요?"}, config={"callbacks": callbacks})
```

(1) 모델 호출은 몇 번 일어나나요? (2) 로컬 trace와 Langfuse trace를 따로 얻으려고 `invoke()`를 Handler마다 한 번씩 두 번 호출하면? (3) `max_retries=0`을 쓰는 이유는?

> 힌트: `callbacks` 목록은 관찰자를 추가할 뿐입니다.

<details>
<summary>정답 보기</summary>

(1) **1번**. 두 Handler가 같은 실행 한 번을 함께 관찰합니다. (2) 모델 요청도 **2번** 발생해 비용이 늘고, 두 trace가 서로 다른 실행을 기록하게 됩니다 (오류 6). (3) 자동 Retry가 켜져 있으면 `invoke()` 1번에도 일시 오류 뒤 HTTP 요청이 추가될 수 있어서, "invoke 1번 = 요청 시도 1번"을 같은 조건에서 관찰하려고 SDK 내부 Retry를 끕니다. Retry 자체가 나쁜 것은 아니며 정책 설계는 9장에서 합니다.

</details>

### 8-Q12. Langfuse 검증 개념 O/X (8-2)

1. `get_client()`가 객체를 반환했으면 인증도 성공한 것이다.
2. `auth_check()`는 매 요청마다 호출해 상태를 확인하는 용도다.
3. `flush()`가 반환되면 Langfuse 화면과 조회 API에서 바로 trace를 볼 수 있다.
4. 짧은 스크립트에서는 `finally`에서 `flush()`를 호출해 대기 중인 이벤트를 보낸다.
5. 여러 요청이 동시에 도는 서버에서 Handler 하나를 공유해도 `last_trace_id`는 항상 내 요청의 ID다.
6. 키가 맞으면 `LANGFUSE_BASE_URL`의 지역은 달라도 된다.
7. Langfuse 패키지가 없으면 로컬 trace도 실행되지 않는다.

> 힌트: 전송 완료와 조회 가능 상태를 구분하세요.

<details>
<summary>정답 보기</summary>

1 X (`auth_check()`로 따로 확인) · 2 X (짧은 실습의 시작 단계에서 한 번) · 3 X (ingestion 전송 완료일 뿐, 반영까지 보통 15\~30초 → 재조회로 확인) · 4 O · 5 X (다른 요청 ID로 바뀔 수 있음 → 요청별 Handler 또는 미리 정한 trace ID) · 6 X (다른 지역이면 인증·조회 실패 가능) · 7 X (함수 안 import가 실패하면 로컬 trace만으로 계속)

</details>
