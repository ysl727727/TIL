# 2장. 클래스 · 람다 · 데코레이터 · FastAPI 기초

> 2026-10-07 학습 기록. 복습 2일차에 `step10_serve_api.py`를 읽다가 막힌 문법(클래스, 람다, 데코레이터, `@app.get("/")`)을 작은 예제로 직접 쳐 보며 정리했습니다. step10 코드 읽기는 [복습 2일차](../../private-llm-review/day02-model-select-generate-api/#step10_serve_apipy)에 있습니다.

## 오늘 한 것 요약

| 주제 | 한 마디 | 모양 |
| --- | --- | --- |
| 클래스 | 붕어빵 틀 | `class Dog:` → `Dog("초코", 3)` |
| 람다 | 이름 없는 한 줄 함수 | `lambda x: x * 2` |
| 데코레이터 | 함수 포장지 / 등록 표시 | `@wrap`, `@app.get("/")` |
| FastAPI | 웹 서버 클래스 | `app = FastAPI()` |

## 핵심 포인트

### 1. 클래스

```python
class Dog:
    def __init__(self, name, age):   # 만들 때 자동 실행
        self.name = name             # 입력값을 객체에 저장
        self.age = age

    def bark(self):                  # 메서드(행동)
        return f"{self.name}: 멍멍!"

dog1 = Dog("초코", 3)
print(dog1.bark())   # 초코: 멍멍!
```

- `class` = 틀, `dog1 = Dog(...)` = 틀로 찍어낸 객체
- `__init__` = 객체 만들 때 자동 실행
- `self` = "나 자신". 입력값은 `self.xxx`에 저장해야 계속 남는다

**내가 틀린 것: `return print(...)`**

```python
def meow(self):
    return print(f"{self.name}: 야옹")   # ❌ print는 None을 돌려줌
    return f"{self.name}: 야옹"          # ✅
```

| | 하는 일 | 변수에 담으면 |
| --- | --- | --- |
| `print(...)` | 화면에 보여주기만 | `None` |
| `return ...` | 값을 돌려줌 | 그 값 |

→ **메서드 안에서는 `return`, 출력은 밖에서 `print`**

### 2. 람다

```python
lambda 입력: 돌려줄값
double = lambda x: x * 2    # def double(x): return x * 2 와 같음
```

- `return`을 안 써도 `:` 뒤 값이 자동으로 돌아감
- 주로 `sorted(key=...)`처럼 **함수에 규칙을 잠깐 넘길 때** 사용

```python
students = [("철수", 85), ("영희", 92), ("민수", 78)]

sorted(students, key=lambda s: s[0])                 # 이름 가나다순
sorted(students, key=lambda s: s[1], reverse=True)   # 점수 높은 순
```

- `key` = **무엇으로** 비교할지 / `reverse=True` = **큰 것부터**

**내가 틀린 것: `key=lambda s: s`**

- 튜플 통째로 비교 → 첫 칸(이름)으로 정렬됨
- `reverse=True`까지 붙어서 이름 **역순**이 나옴
- 기준을 `s[0]`, `s[1]`로 **명확히** 써야 함

### 3. 데코레이터

```python
def wrap(func):          # 함수를 받음
    def wrapper():       # 감쌀 새 함수
        print("시작")
        func()           # 원래 함수 실행
        print("끝")
    return wrapper       # 괄호 없음 = 함수 자체를 돌려줌

@wrap                    # = say_hi = wrap(say_hi)
def say_hi():
    print("안녕하세요")

say_hi()   # 시작 / 안녕하세요 / 끝
```

- `hello` = 함수 자체, `hello()` = 실행 결과
- `@wrap`은 `say_hi = wrap(say_hi)`의 줄임말
- 데코레이터가 여러 개 겹치면 **아래부터** 적용
- 함수는 정의만 하면 아무 일 없음 → **호출(`greet()`)해야 실행**

### 4. `@app.get("/")`

```python
from fastapi import FastAPI

app = FastAPI()          # dog1 = Dog("초코", 3) 과 같은 모양

@app.get("/")            # "/" 주소로 접속하면 아래 함수 실행
def home():
    return {"msg": "안녕하세요"}
```

| 강아지 | 웹 서버 |
| --- | --- |
| `class Dog:` (내가 만듦) | `FastAPI` (남이 만들어 둠) |
| `dog1 = Dog("초코", 3)` | `app = FastAPI()` |
| `dog1.bark()` | `app.get("/")` |

- FastAPI는 다른 사람이 정의해 둔 클래스 → **설치(`pip install fastapi`) + import** 하면 바로 사용
- import 안 하면 `NameError: name '...' is not defined`

| 종류 | 예시 | 설치 | import |
| --- | --- | --- | --- |
| 내가 만든 것 | `Dog` | ✕ | ✕ (같은 파일) |
| 기본 내장 | `print`, `len` | ✕ | ✕ |
| 표준 라이브러리 | `math`, `random` | ✕ | ○ |
| 외부 라이브러리 | `FastAPI`, `numpy` | ○ | ○ |

**`@wrap` vs `@app.get("/")`**

| | `@wrap` | `@app.get("/")` |
| --- | --- | --- |
| 비유 | 선물 포장지 | 메뉴판에 이름 적기 |
| 함수 | **바뀜** (wrapper로) | **안 바뀜** (등록만) |
| 괄호 입력 | 없음 | 주소 `"/"` |

- `@app.get("/")` = `app.add("/", home)`을 함수 바로 위에 붙이는 모양으로 쓴 것
- 괄호가 있는 데코레이터 = **설정값 먼저 → 함수 나중**

**주소 `/`와 get·post**

```
https://www.example.com/          → "/"        첫 화면
https://www.example.com/login     → "/login"
http://127.0.0.1:8000/health      → "/health"
```

| | 의미 | 비유 |
| --- | --- | --- |
| `get` | 보여줘 | 메뉴판 구경 |
| `post` | 내용을 보낼게 | 주문서 제출 |

## 오늘 만난 에러

| 에러 | 원인 | 해결 |
| --- | --- | --- |
| `SyntaxError: unterminated string literal` | 따옴표 안 닫음 (`print("*****)`) | 따옴표 짝 확인 |
| `NameError: name 'BaseModel' is not defined` | import 빠뜨림 | 맨 위에 `from pydantic import BaseModel, Field, field_validator` |

→ `NameError`는 **① 오타 ② import 누락** 먼저 확인

## 질문과 새로 알게 된 점

- **FastAPI는 이미 만들어진 클래스라 정의 없이 써도 되나?** → 정의는 이미 남이 해 둠. 대신 설치 + import는 필요
- **`@app.get("/")`가 `app.add("/", home)`을 예쁘게 쓴 거라는 게 무슨 뜻?** → 둘 다 "이 주소엔 이 함수"를 서버 안에 저장. `@`는 함수 바로 위에 붙여 쓰는 모양
- **`@wrap`과 `@app.get("/")` 차이?** → wrap은 함수를 바꾸고(포장), app.get은 안 바꾸고 등록만(메뉴판)
- **`/`가 주소인가? 실제로도 `/`로 쓰나?** → `/`는 첫 화면 주소. 다른 페이지는 `/login`처럼 `/` 뒤에 이름을 붙임
- **`cls`, `text`가 뭔가? 안 쓰는데 왜 넣나? 꼭 `cls`여야 하나?** → 첫 칸은 파이썬이 자동으로 채우는 자리라 비워둬야 함. 이름은 자유지만 약속상 `cls`
