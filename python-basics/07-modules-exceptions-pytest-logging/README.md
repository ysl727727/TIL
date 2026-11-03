# 7장. 모듈 · 패키지 · import · 예외 처리 · pytest · logging (보강 2주 2일)

> 2026-11-03 학습 기록. Python 보강 2주 2일 수업입니다. 한 파일에 몰아 쓰던 코드를 **파일과 폴더로 나누고**, import해도 안전하게 만들고, 이상한 값은 **이름 붙은 오류**로 알리고, `assert`를 **pytest**로 한 번에 돌리고, print 대신 **logging**으로 남기는 법을 배웠습니다(uv + Python 3.12). 문제 파일은 수업 자료라 올리지 않고, 배운 규칙과 내가 푼 코드, 헷갈린 점만 정리합니다.

## 진행 상황

| 파일 | 문제 | 상태 |
|---|---|---|
| `lecture/1_module` ~ `5_pytest` | 수업 이론 1~5 예제 실행 | ✅ 진행 |
| `step0/` | 0단계 따라 치기 (`calc.py` · `step0.py` · `test_step0.py`) | ✅ 진행 (`1 passed`) |
| `practice/q1.py` + `shapes.py` | 기초 1. 모듈 나누기 `rect_area` | ✅ 통과 |
| `practice/q2.py` + `safe.py` | 기초 2. 안전한 변환 `safe_int` | ✅ 통과 |
| `practice/test_shapes.py` | 기초 3. 첫 pytest 파일 | ✅ 통과 (`1 passed`) |
| `practice/q4.py` + `tools/` | 응용 1. 패키지 `from tools import is_prime` | ⬜ 남음 |
| `practice/q5.py` + `wallet.py` | 응용 2. 내 예외 `InsufficientFunds` · `withdraw` | ⬜ 남음 |
| `practice/test_wallet.py` | 응용 3. `pytest.raises` 테스트 | ⬜ 남음 |
| `practice/q7.py` + `validate.py` | 심화 1. 한 줄 검사 `parse_record` | ⬜ 남음 |
| `practice/q8.py` + `validate.py` | 심화 2. 오류 모으기 `parse_records` | ⬜ 남음 |
| `practice/q9.py` + `scores.py` | 심화 3. 파일 읽기 `read_scores` | ⬜ 남음 |
| `practice/q10.py` + `app.py` | 실무 1. logging `process` | ⬜ 남음 |

- 실행: 각 폴더로 들어가서 `uv run python q1.py`, 테스트는 `uv run pytest -q`
- 2주 1일 [클래스 · 상속](../06-classes/)에서 이어지는 내용 (내 예외 = `Exception`을 상속한 클래스)

## 큰 흐름

1. **모듈**: 코드를 파일 여러 개로 나누고 `import`로 가져다 쓴다.
2. **패키지**: 파일이 많아지면 폴더로 묶는다. `__init__.py`에서 끌어올리면 짧게 가져올 수 있다.
3. **`if __name__ == "__main__":`**: import하면 파일이 한 번 다 실행되니까, 직접 실행할 때만 돌릴 코드는 여기에 넣는다.
4. **예외**: 오류는 정확한 이름으로 잡고(`try/except`), 내 상황에 맞는 오류는 `Exception`을 상속해 만들어 `raise`로 던진다.
5. **pytest**: 나눈 함수들의 `assert`를 `test_` 파일로 옮겨 한 번에 돌린다. 에러가 나야 맞는 건 `pytest.raises`로 확인한다.
6. **logging**: 함수 안에서는 print 대신 딱지 붙은 logger로 남기고, 어디까지 찍을지는 입구(`__main__` 블록)에서 `level`로 정한다.

> 한 줄로: 파일을 나누고(1, 2), import해도 안전하게 만들고(3), 이상한 값은 이름 붙은 오류로 알리고(4), pytest로 한 번에 검사하고(5), print 대신 logging으로 기록한다(6).

## 오늘 배운 것

### 1. 모듈: 파일 하나가 곧 import 단위

```python
# shapes.py
def rect_area(w, h):
    return w * h
```

```python
# main.py  (같은 폴더)
import shapes                      # 방법 1: 모듈 이름으로
print(shapes.rect_area(3, 4))      # 12

from shapes import rect_area       # 방법 2: 함수만 꺼내서
print(rect_area(3, 4))             # 12
```

- `import shapes`는 **shapes.py를 처음부터 한 번 실행**한다. 그 뒤로 `shapes.이름`으로 쓸 수 있다.
  - 그래서 파일 맨 아래에 `print`가 있으면 import만 해도 찍힌다. 0단계 A의 `"calc 모듈이 읽혔어요"`가 이것이다.
- 파이썬은 **실행한 파일이 있는 폴더**에서 모듈을 찾는다. 다른 폴더에서 실행하면 `ModuleNotFoundError`가 난다.

### 2. 패키지와 import

```
2_package/
├── main.py
└── tools/
    ├── __init__.py     ← 비어 있어도 됨. "이 폴더는 패키지다" 표시
    └── numbers.py      ← def is_prime(n): ...
```

**`__init__.py`로 짧게 가져오기 (끌어올리기)**

```python
# __init__.py가 비어 있으면
from tools.numbers import is_prime   # ✅ 폴더.파일까지 다 적어야 함
from tools import is_prime           # ❌ ImportError (tools 바로 아래엔 is_prime이 없음)
```

```python
# tools/__init__.py 에 한 줄 써 두면
from .numbers import is_prime
```

```python
from tools import is_prime                       # ✅ 이제 가능
from tools.numbers import is_prime as is_prime2
print(is_prime is is_prime2)                     # True
```

- `from tools import ...`를 하면 파이썬은 `tools/__init__.py`를 실행한다. 거기서 `is_prime`을 가져와 두니까 `tools`에서 바로 꺼낼 수 있다.
- `__init__.py`는 함수를 **복사하는 게 아니라** 같은 함수 객체를 가리키는 이름을 하나 더 만든다. 그래서 `is` 비교가 `True`다.

**상대 import(`.`)와 절대 import**

- `.` = **이 파일이 들어 있는 패키지**(여기서는 `tools`)
- 절대 import(`from tools.numbers import is_prime`)도 동작하지만, 패키지 안에서는 상대 import가 더 낫다.
  1. 패키지 이름(`tools` → `utils`)을 바꿔도 안 깨진다.
  2. 실행 위치에 덜 흔들린다(`ModuleNotFoundError: No module named 'tools'` 방지).
  3. "같은 패키지 안의 모듈"이라는 게 바로 보인다.

**`main.py`에서는 `.numbers`를 쓸 수 없다**

1. **위치가 다르다**: `main.py`의 `.`은 `2_package`라서, `.numbers`는 `2_package/numbers.py`를 찾는다(없음).
2. **직접 실행하는 파일이다**: `python main.py`로 실행하면 `__name__ == "__main__"`이 되어 **소속 패키지가 없다**. 그래서 상대 import는 경로와 상관없이 실패한다.

```
ImportError: attempted relative import with no known parent package
```

| 파일 | 역할 | import 방식 |
|---|---|---|
| `main.py` | 직접 실행하는 **입구** | 절대 import `from tools.numbers import ...` |
| `tools/__init__.py` | import되는 **패키지 내부** | 상대 import `from .numbers import ...` |

### 3. `__name__`과 `if __name__ == "__main__":`

```
① 직접 실행:   uv run python app.py
② 남이 가져감: 다른 파일에서 import app
```

파이썬은 지금 ①인지 ②인지를 `__name__`에 **자동으로** 적어 둔다.

| 실행 방식 | `__name__` 값 |
|---|---|
| `python step0.py`로 **직접 실행** | `"__main__"` |
| 다른 파일에서 `import calc`로 **불려옴** | `"calc"` (모듈 이름) |

```python
# step0.py
import calc

print(__name__)       # __main__  ← 내가 직접 실행한 파일
print(calc.__name__)  # calc      ← import로 불려온 모듈
```

- `__name__`: **지금 이 파일**의 이름표, `calc.__name__`: **calc 모듈**의 이름표
- 같은 `calc.py`라도 `python calc.py`로 실행하면 `__main__`, import되면 `calc`가 된다.

```python
# app.py
def process(items):
    ...

if __name__ == "__main__":        # 이 파일을 직접 실행했을 때만 참
    print(process([1, 2, 3]))
```

- 직접 실행하면 `"__main__" == "__main__"`이 참이라 `print`가 돈다.
- `import app`을 하면 `"app" == "__main__"`이 거짓이라 `print`를 건너뛰고 `process` 함수만 가져간다.
- import하면 파일이 처음부터 끝까지 한 번 실행되기 때문에, 이 if로 막지 않으면 확인용 `print`까지 같이 찍힌다. 테스트 파일이 `app.py`를 import해도 화면에 아무것도 안 찍히는 이유가 이것이다.

### 4. 예외: 예상한 오류만 잡고, 내 오류는 만든다

**① 잡기: `try / except`**

```python
def safe_int(s):
    try:
        return int(s)
    except ValueError:            # int("abc")가 내는 그 오류만
        return None
```

| 입력 | 결과 | 이유 |
|---|---|---|
| `"42"` | `42` | 정상 변환 |
| `"  7 "` | `7` | `int()`는 앞뒤 공백을 알아서 무시한다(`strip()` 필요 없음) |
| `"abc"` | `None` | `ValueError` 발생 → except에서 처리 |
| `"3.5"` | `None` | 소수 문자열도 `int()`에서는 `ValueError` |

- `except Exception:`이나 맨 `except:`로 다 잡으면, 오타(`NameError`) 같은 **진짜 버그까지 조용히 숨는다**. 그래서 `except ValueError:`처럼 **에러 이름을 정확히** 쓴다.

**② 만들기 + 던지기: `class` + `raise`**

```python
class InsufficientFunds(Exception):     # 내 예외: Exception을 상속한 빈 클래스
    pass

def withdraw(balance, amount):
    if amount > balance:
        raise InsufficientFunds(f"잔액 {balance}, 요청 {amount}")   # 상황을 이름으로 알린다
    return balance - amount

withdraw(1000, 300)   # 700
withdraw(100, 500)    # InsufficientFunds: 잔액 100, 요청 500
```

- `raise` = 오류를 던진다. 함수가 그 자리에서 멈춘다.
- 메시지에 숫자를 넣어 두면 나중에 왜 틀렸는지 단서가 된다.

**③ 모으기 (심화 2)**: 한 줄이 틀렸다고 전체를 멈추지 않는다. `errors.append(...)`로 기록하고 계속 간다.

**왜 굳이 `Exception`을 상속한 클래스를 만드나?**

1. **`Exception`을 상속해야 `raise`할 수 있다.**
   ```python
   class InsufficientFunds:              # 상속 없음
       pass
   raise InsufficientFunds("잔액 부족")   # ❌ TypeError: exceptions must derive from BaseException
   ```
   상속하면 메시지를 담는 기능이나 `str(e)` 같은 것도 부모한테 물려받는다. 그래서 안이 `pass`로 비어 있어도 된다(2주 1일 상속과 같은 원리).
2. **이름이 따로 있어야 그 상황만 골라 잡을 수 있다.** `ValueError`를 쓰면 `int("abc")` 같은 다른 실수와 잔액 부족이 구분되지 않는다. `except InsufficientFunds as e:`로 **잔액 부족만** 딱 잡히고, 다른 오류는 그대로 보인다.

> `(Exception)` 상속 = **던질 수 있는 자격** / 내 이름 클래스 = **그 상황만 골라 잡는 이름표**

**`Exception`은 정해진 건가?** 네. **파이썬에 원래 들어 있는 클래스**이고 **모든 오류의 부모**다. import 없이 바로 쓴다.

```
Exception                 ← 파이썬이 만들어 둔 부모
├─ ValueError             int("abc")
├─ TypeError              Student() 인자 틀림
├─ IndexError             [].pop()
├─ KeyError               d["없는키"]
├─ ZeroDivisionError      1 / 0
├─ AttributeError         w.doposit 오타
└─ InsufficientFunds      ← 내가 만든 것도 여기 붙음
```

- `issubclass(ValueError, Exception)` → `True`
- `except Exception:`이 모든 오류를 잡는 이유: 부모로 잡으면 자식이 전부 잡히기 때문이다.

### 5. pytest

**왜 쓰나**

- 지금까지는 파일 끝에 `assert`를 줄줄이 붙였다. **첫 번째에서 깨지면 그 자리에서 멈춰서** 나머지는 볼 수 없다.
- 문제가 10개면 `q1.py`부터 `q10.py`까지 하나씩 직접 실행해야 한다.
- pytest는 `test_` 파일을 다 찾아서 한 번에 돌린다. **하나가 깨져도 나머지는 계속 돌리고**, 어느 테스트가 어떤 입력에서 깨졌는지 보여 준다.

```python
# test_shapes.py
from shapes import rect_area

def test_rect_area():
    assert rect_area(3, 4) == 12
    assert rect_area(0, 5) == 0
    assert rect_area(2.5, 2) == 5.0
```

```
uv run pytest -q test_shapes.py   # → 1 passed   (python -m pytest test_shapes.py 도 같음)
uv run pytest -q                  # 폴더의 모든 test_*.py
```

- 파일 이름과 함수 이름이 **`test_`로 시작**해야 pytest가 테스트로 인식한다.
- `assert`를 한 줄에 하나씩 나눠 쓰면 실패한 줄을 바로 알 수 있다.
- pytest가 `test_shapes.py`를 돌리면 `shapes.py`를 **import**한다. 그래서 `shapes.py`의 확인용 코드는 `if __name__ == "__main__":` 아래에 두어야 테스트할 때 안 찍힌다(3번과 연결).

**assert 안의 숫자는 바꿔도 될까?**

```
rect_area(3, 4)  ==  12
   └ 입력           └ 기대하는 정답
```

- **입력**은 자유롭게 바꿔도 된다. **정답**은 그 입력에 맞는 진짜 답이어야 한다. 틀리게 적으면 함수가 맞아도 테스트가 실패한다.
- 좋은 테스트는 비슷한 값을 여러 번 넣는 대신 **서로 다른 상황**을 고른다: 평범한 정수 `(3, 4)` / 경계값 0 `(0, 5)` / 실수 `(2.5, 2)`

**`pytest.raises`: 에러가 나야 정답인 테스트 (4번과 연결)**

```python
# try/except로 직접 확인하면
try:
    withdraw(100, 500)
    assert False, "예외가 나야 해요"     # 여기까지 오면 에러가 안 난 것 → 실패
except InsufficientFunds as e:
    assert "500" in str(e)

# pytest에서는
with pytest.raises(InsufficientFunds):
    withdraw(100, 500)
```

- "이 안에서 `InsufficientFunds`가 나야 통과"라는 뜻이다.
- 내 예외를 따로 만들어 두었기 때문에 **정확히 그 상황 때문에 난 에러인지** 집어서 검사할 수 있다.

### 6. logging = 딱지 붙은 print

```python
logger.debug("안 보여요")       # 개발 중에만 보고 싶은 것
logger.info("보여요")           # 평소 진행 상황
logger.warning("경고도 보여요")  # 이상하지만 계속 진행
```

```
DEBUG  <  INFO  <  WARNING
```

```python
logging.basicConfig(level="INFO")    # 프로그램 입구에서 한 번: INFO부터 위로만 찍어라
```

```
INFO app: 보여요
WARNING app: 경고도 보여요
```

- DEBUG는 INFO보다 아래라서 안 찍힌다. `level="DEBUG"`로 바꾸면 세 줄이 **다** 찍힌다.

**print보다 좋은 점**

- print는 숨기려면 그 줄을 **지워야** 한다. 파일이 나뉘어 있으면 `process`를 부르는 곳(테스트 포함)마다 다 찍힌다.
- logging은 그 줄을 **그대로 두고**, `level` 한 단어만 바꾸면 숨겼다 보였다 한다.
- 함수 안에서는 **남기기만** 하고, 보여 줄지는 **입구**(`if __name__ == "__main__":` 아래)에서 정한다. 그래서 `q10.py`가 `import app`으로 가져가면 그 블록은 안 돌고, `q10.py`가 직접 `app.logger.setLevel(...)`로 레벨을 바꿔 가며 검사할 수 있다.

**`%s`, `%d`**

```python
logger.debug("처리 중: %s", item)
logger.info("합계 %d (항목 %d개)", total, len(items))
```

- `%s` = 아무 값, `%d` = 정수 자리. 뒤에 쓴 값이 순서대로 들어간다(f-string의 `{}` 역할).

**`INFO app:`에서 `app`은 왜 나오나?**

```python
logger = logging.getLogger("app")     # ① 로거 이름 = "app"
logging.basicConfig(level="INFO", format="%(levelname)s %(name)s: %(message)s")   # ② 찍는 모양
```

| format 자리 | 들어가는 값 |
|---|---|
| `%(levelname)s` | 딱지 → `INFO` |
| `%(name)s` | 로거 이름 → `app` |
| `%(message)s` | 내가 쓴 글자 → `보여요` |

- `getLogger("wallet")`로 바꾸면 `INFO wallet: 보여요`가 된다.
- 파일이 여러 개면 로그도 여러 파일에서 찍히니까, 이름이 있어야 **어느 파일에서 나온 로그인지** 안다.
- 수업 예시의 `getLogger(__name__)`은 3번의 그 이름표를 쓰는 것이다. `app.py`가 import되면 자동으로 `"app"`이 들어간다.

## 내가 푼 코드

```python
# 기초 1. shapes.py
def rect_area(w, h):
    return w * h

# 기초 2. safe.py
def safe_int(s):
    try:
        return int(s)
    except ValueError:
        return None

# 기초 3. test_shapes.py
from shapes import rect_area

def test_rect_area():
    assert rect_area(3, 4) == 12
    assert rect_area(0, 5) == 0
    assert rect_area(2.5, 2) == 5.0      # 실수 상황도 하나 더 추가
```

## 그 밖에 질문한 것

### `rect_area`의 자료형

```python
type(rect_area)            # <class 'function'>  ← rect_area 자체는 "함수"
type(rect_area(3, 4))      # int    → 12
type(rect_area(2.5, 2))    # float  → 5.0
```

- `rect_area`는 숫자가 아니라 **함수**다. **돌려주는 값**의 자료형은 넣은 값에 따라 달라진다. 곱하는 값 중 하나라도 float이면 결과도 float이다.
- 파이썬 함수는 반환 자료형을 따로 정하지 않고, 계산 결과를 그대로 돌려준다.
- `5.0 == 5`는 `True`다. 값 비교에서는 int와 float을 같은 숫자로 본다.
- VS Code에서 마우스를 올리면 뜨는 `(function) def rect_area(w, h) -> ...`는 **설명창(툴팁)**이지 경고가 아니다. 실제 경고와 에러는 노란 · 빨간 물결줄과 **문제(Problems) 패널**로 확인한다.

### 소수 판별 `is_prime` (응용 1에서 `tools/`로 옮길 함수)

```python
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True
```

- 1 이하는 소수가 아니고, **√n까지만** 나눠 보면 충분하다.
- `is_prime(97)` → `True`, `is_prime(91)` → `False` (91 = 7 × 13)

## 오늘 한 실수 · 헷갈린 것

| 상황 | 결과 | 교훈 |
|---|---|---|
| `shapes.py` 맨 아래에 `print(type(rect_area))`를 남겨 둠 | `q1.py`가 import할 때마다 `<class 'function'>`이 같이 찍힘 | import = 파일 한 번 실행. 확인용 코드는 `if __name__ == "__main__":` 아래로 |
| 파일을 저장하지 않고 실행 | 고친 내용이 반영 안 됨 | 탭 옆 ● 표시 = 저장 안 됨, `Ctrl + S` |
| 다른 폴더에서 실행 | `ModuleNotFoundError: No module named 'safe'` | 파이썬은 실행한 파일의 폴더에서 모듈을 찾음. 그 폴더로 `cd`한 뒤 실행 |
| `main.py`에서 `from .numbers import ...` | `attempted relative import with no known parent package` | 직접 실행하는 입구는 절대 import, 패키지 안에서만 상대 import |

## 오늘의 한 줄

- 파일 하나 = 모듈, 폴더 + `__init__.py` = 패키지
- import하면 그 파일이 한 번 실행된다 → 직접 실행할 때만 할 일은 `if __name__ == "__main__":`
- 오류는 정확한 이름으로 잡고, 내 오류는 `class 이름(Exception)`으로 만들어 `raise`
- `test_`로 시작하는 파일 · 함수 = pytest가 한 번에 돌리는 테스트, 에러가 나야 맞으면 `pytest.raises`
- logging = 딱지 붙은 print, 보여 줄 등급은 입구에서 `level`로
