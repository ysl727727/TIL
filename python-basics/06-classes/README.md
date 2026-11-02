# 6장. 클래스 — 객체 · `__init__` · `self` · 던더 메서드 · 상속 · `@dataclass` (보강 2주 1일)

> 2026-11-02 학습 기록. Python 보강 2주 1일 수업입니다. 딕셔너리 + 함수로 하던 일을 **데이터와 동작을 한 덩어리로 묶는 클래스**로 바꾸는 법을 배웠습니다(uv + Python 3.12). 함수 인자(`*` · `**`)를 먼저 복습하고, 클래스 · 던더 메서드 · 상속 · `@dataclass` 순서로 진행했습니다. 문제 파일은 수업 자료라 올리지 않고, 배운 규칙과 내가 푼 코드, 실수만 정리합니다.

## 진행 상황

| 파일 | 문제 | 상태 |
|---|---|---|
| `day4/step0.py` | 0단계 따라 치기 + 함수 인자 복습 | ✅ 진행 (Wallet · Point · Shape/Circle 직접 타이핑) |
| `day4/q1.py` | 기초 1. 학생 카드 `Student` | ✅ 통과 |
| `day4/q2.py` | 기초 2. 지갑 `Wallet` | ✅ 통과 |
| `day4/q3.py` | 기초 3. 점: 출력과 비교 `Point` | ✅ 통과 |
| `day4/q4.py` | 응용 1. 스택 `Stack` | ✅ 통과 |
| `day4/q5.py` | 응용 2. 집계기 `Tally` | ⬜ 남음 |
| `day4/q6.py` | 응용 3. 상속 `Rectangle(Shape)` | ⬜ 남음 |
| `day4/q7.py` | 심화 1. 분수 `Fraction` (`math.gcd`로 약분) | ⬜ 남음 |
| `day4/q8.py` | 심화 2. 재고 `Inventory` (주어진 예외 사용) | ⬜ 남음 |
| `day4/q9.py` | 심화 3. 벡터 `Vector` | ⬜ 남음 |
| `day4/q10.py` | 실무 1. `@dataclass` | ⬜ 남음 (이론만) |

- 실행: `uv run python day4/q1.py`
- 1주 2일 [기본값 · 키워드 인자](../04-functions-lists-strings-dicts/)와 [이전 클래스 기초](../02-class-lambda-decorator/)에서 이어지는 내용

## 오늘 배운 것

### 0. 함수 인자 복습

```python
def order(menu, count=1):          # count=1 → 기본값
    return menu, count

order("커피")                # ('커피', 1)  기본값 사용
order("커피", 2)             # ('커피', 2)  위치 인자: 순서대로
order(menu="커피", count=2)  # ('커피', 2)  키워드 인자: 이름 적기
```

| 언제 | `*` / `**`가 하는 일 | 예 |
|---|---|---|
| **부를 때** | 푼다 | `f(*[1, 2])` → `f(1, 2)`, `f(**{"a": 1})` → `f(a=1)` |
| **만들 때** | 모은다 | `def f(*args)` → 튜플, `def f(**kwargs)` → 딕셔너리 |

```python
def add(a, b, c):
    return a + b + c

add(*{"a": 1, "b": 2, "c": 3})     # 'abc'  딕셔너리에 별 하나 → 키만 풀림

def greet(name, *, loud=False):    # * 뒤 인자는 반드시 이름을 적어야 함
    return name.upper() if loud else name

greet("kim", loud=True)   # 'KIM'
greet("kim", True)        # TypeError
```

- 같은 날 LLMOps 2장의 `evaluate(*, output, expected_output, **kwargs)`가 이 문법이에요 → [LLMOps 2장](../../llmops/02-golden-dataset-prompt-regression/) "질문과 새로 알게 된 점"

### 1. 클래스 · 객체 · `__init__` · `self`

왜 쓰나: `{"owner": "영희", "balance": 1000}` 같은 딕셔너리와 함수로도 되지만, 사람이 많아지면 **데이터와 동작을 한 덩어리로** 묶는 게 편해요 → 객체지향.

```python
class Wallet:                          # 클래스 이름은 대문자로 시작 (MyWallet)
    def __init__(self, owner, balance=0):
        self.owner = owner
        self.balance = balance

    def deposit(self, amount):
        self.balance += amount

w = Wallet("영희", 1000)   # self = w → w.owner = "영희", w.balance = 1000
w.deposit(500)             # Wallet.deposit(w, 500)과 같음
print(w.balance)           # 1500
```

| 용어 | 뜻 |
|---|---|
| `class` | 붕어빵 틀 |
| 객체 | 찍어낸 붕어빵. `w`는 내가 붙인 이름일 뿐 |
| `__init__` | 객체가 만들어질 때 자동 실행. `self.이름 = 이름`으로 값을 넣음 |
| `self` | **`.` 앞에 있는 그 객체**. `w.deposit(500)`이면 `self`는 `w` |

- 메서드 안에서는 `self.이름`으로 꺼내 써요.
- 객체마다 값이 따로예요. `Wallet(50)`을 새로 만들어도 `w`는 그대로.

### 2. 던더 메서드 (`__이름__`)

```python
class Point:
    def __init__(self, x, y):
        self.x, self.y = x, y

    def __repr__(self):                    # print(p), repr(p) 때 보여 줄 글자
        return f"Point({self.x}, {self.y})"

    def __eq__(self, other):               # p == q 판정
        return self.x == other.x and self.y == other.y

print(Point(1, 2))                 # Point(1, 2)  (없으면 <__main__.Point object at 0x...>)
print(Point(1, 2) == Point(1, 2))  # True         (없으면 False: 서로 다른 객체)
```

| 던더 | 언제 불리나 |
|---|---|
| `__init__` | `Point(1, 2)` 만들 때 |
| `__repr__` | `print(p)`, `repr(p)` (`__str__`이 없으면 `str(p)`도) |
| `__eq__(self, other)` | `p == q` → **self = 왼쪽, other = 오른쪽** |
| `__len__` | `len(obj)` |
| `__add__` / `__mul__` | `a + b` / `a * 2` |
| `__contains__` | `x in obj` |

- 수업 코드는 `isinstance(other, Point) and …`로 다른 종류와 비교할 때도 안전하게 했어요.

### 3. 상속 · `super()` · 오버라이드

```python
class Shape:
    def __init__(self, name):
        self.name = name
    def area(self):
        raise NotImplementedError          # 자식이 꼭 채워야 하는 자리
    def describe(self):                    # 공통 동작 → 자식이 그대로 물려받음
        return f"{self.name}: 넓이 {self.area():.2f}"

class Circle(Shape):
    def __init__(self, r):
        super().__init__("원")             # 부모 __init__ 먼저 실행
        self.r = r
    def area(self):                        # 부모 area 덮어쓰기
        return 3.14159 * self.r ** 2

print(Circle(1).describe())                # 원: 넓이 3.14
```

- `class 자식(부모):` → 부모 메서드를 다 물려받아요.
- `super().__init__(...)` → 부모의 초기화를 먼저 실행.
- 같은 이름으로 다시 쓰면 오버라이드(자식 것이 우선).
- `describe()`는 부모에 있지만 안에서 부르는 `self.area()`는 **자식(Circle)의 area**예요. `self`가 Circle 객체라서.
- `Circle(name, r)`로 받아서 `super().__init__(name)`에 넘기는 방식도 가능해요(내가 단 주석).

### 4. `@dataclass` (실무)

```python
from dataclasses import dataclass, field, asdict

@dataclass
class Student:
    name: str
    score: int
    tags: list[str] = field(default_factory=list)   # 가변 기본값은 이렇게

s = Student("영희", 88)
print(s)                          # Student(name='영희', score=88, tags=[])
print(s == Student("영희", 88))    # True
print(asdict(s))                  # {'name': '영희', 'score': 88, 'tags': []}
```

- `@` = **데코레이터**. 바로 아래 클래스에 기능을 덧붙여 줘요(제너레이터 아님).
- `@dataclass`가 `__init__` · `__repr__` · `__eq__`를 자동으로 써 줘요.
- 리스트 같은 가변 기본값은 `= []` 대신 `field(default_factory=list)` → 객체마다 새 빈 리스트. `list`에 괄호가 없는 건 "리스트 만드는 함수"를 넘겨서, 객체를 만들 때마다 dataclass가 `list()`를 불러 주기 때문.
- `asdict(s)` → 객체를 딕셔너리로.

## 내가 푼 코드

```python
# 기초 2. Wallet
class Wallet:
    def __init__(self, balance=0):
        self.balance = balance
    def deposit(self, amount):
        self.balance += amount
    def withdraw(self, amount):
        if self.balance >= amount:     # 충분하면 빼고 True
            self.balance -= amount
            return True
        return False                   # 부족하면 아무것도 안 바꾸고 False

# 응용 1. Stack
class Stack:  ### 바꾸기만 하는것에는 return 안하는것이 관례.
    def __init__(self):
        self.items = []
    def push(self, item):
        self.items.append(item)        # 넣기만 → return 없음
    def pop(self):
        if self.is_empty():
            raise IndexError
        return self.items.pop()        # 맨 뒤를 빼고 그 값을 돌려줌
    def is_empty(self):
        return len(self.items) == 0
    def __len__(self):                 # len(st)가 되게
        return len(self.items)
```

- 기초 1 `passed()`는 `return self.score >= 60` 한 줄. 비교 결과가 이미 True/False라 if가 필요 없어요.
- 기초 3 `Point`는 위 던더 메서드 코드와 같아요.
- `pop()` = 맨 뒤를 빼고 그 값을 돌려줌, `pop(i)` = i번째, 비어 있으면 `IndexError`.

## 오늘 한 실수

| 실수 | 결과 | 교훈 |
|---|---|---|
| `def doposit`을 만들고 `w.deposit()` 호출 | `AttributeError: … Did you mean: 'doposit'?` | 만든 이름과 부르는 이름은 철자까지 같아야 함 |
| `__repr__`에서 `f"point(...)"` (소문자) | `AssertionError` | 문자열 비교는 대소문자까지 따짐 |
| `push`에서 `return self.items` | 통과는 하지만 안쪽 리스트가 밖으로 노출됨 | 안쪽 리스트를 통째로 돌려주지 않기 |
| `Wallet("용석, 1000")` | 따옴표가 하나라 `owner = "용석, 1000"`, `balance = 0` | 인자는 `Wallet("용석", 1000)`처럼 따로 |

**관례: 바꾸기만 하는 메서드는 `return`하지 않는다**

- 바꾸기만 하는 것은 `None`을 돌려줌: `append`, `sort`, `update`, 내가 만든 `push`, `deposit`
- 새 값을 만드는 것은 그 값을 돌려줌: `sorted()`, `s.upper()`
- 예외: 바꾸면서 돌려줄 의미가 있을 때 → `pop()`(뺀 값), `withdraw()`(성공 여부)
- 흔한 실수: `items = items.sort()` → `items`가 `None`이 됨

## 오늘의 한 줄

- 클래스 = 데이터(`self.이름`)와 동작(메서드)을 한 덩어리로
- `self` = 점(`.`) 앞의 그 객체
- `print`는 `__repr__`, `==`는 `__eq__`, `len()`은 `__len__`을 부른다
- 자식은 부모를 물려받고, 같은 이름으로 다시 쓰면 덮어쓴다
- `@dataclass`는 `__init__` · `__repr__` · `__eq__`를 대신 써 준다
