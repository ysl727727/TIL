# 0장. 파이썬 베이직반 — 변수 · 입출력 · 문자열 · 조건문 · 반복문

> 2026-08-04 ~ 08-05 학습 기록. 과정 시작 직후 들은 파이썬 베이직반입니다. 변수와 자료형, `print`/`input`, 문자열 인덱싱·슬라이싱·메서드, 조건문을 수업 노트북으로 따라 치고 실습문제·미니과제를 풀었습니다. 반복문(08-05)은 미니과제를 받았지만 아직 풀지 못했습니다.

## 학습 목표

- `int`·`float`·`str`·`bool` 자료형을 구분하고 `type()`으로 확인한다.
- `input()`은 항상 문자열을 돌려준다는 점과 `int()`, `map(int, input().split())`로 바꾸는 법을 안다.
- 문자열 인덱싱 `[i]`, 슬라이싱 `[start:end:step]`, 메서드(`upper`, `find`, `replace`, `split`, `join`, `strip`, `count`)를 쓴다.
- `if`/`elif`/`else`, `and`/`or`/`not`, `in`, 조건부 표현식으로 분기를 만들고 **조건 순서**가 결과를 바꾼다는 것을 안다.

## 실습 파일

| 날짜 | 주제 | 상태 |
| --- | --- | --- |
| 08-04 | 변수 — 수업 코드 + 실습문제 3 + 미니과제 | ✅ 완료 |
| 08-04 | 입출력 — 수업 코드 + 실습문제 3 + 미니과제 | ✅ 완료 |
| 08-04 | 문자열 — 수업 코드 + 실습문제 3 + 미니과제 | ✅ 완료 (뒤 3글자 슬라이스 실수) |
| 08-04 | 조건문 — 수업 코드 + 실습문제 3 + 미니과제 5 | ✅ 완료 |
| 08-05 | 반복문 — 미니과제 9문제 | ⬜ 미착수 (빈 셀) |

## 핵심 이론

### 1. 변수와 자료형

```python
age = 25            # int
height = 175.5      # float
name = "홍길동"      # str
is_student = True   # bool
a, b = b, a         # 한 줄로 값 교환
```

- 변수 이름은 영문자·밑줄로 시작, 숫자로 시작 불가(`1st_place` ❌), 예약어 불가(`for` ❌).
- `10 + 3.5`는 `float`. `'10' == 10`은 `False`(값도 타입도 다름).
- 정수는 불변 객체라 `y = x` 뒤에 `x = 10`을 해도 y는 원래 값 그대로(새 객체를 가리킬 뿐).

### 2. 입출력

```python
print("이름:", name, "나이:", age)           # 쉼표 = 공백으로 이어 줌
print(f"이름: {name}, 나이: {age}")           # f-string
print(1, 2, 3, sep=";", end="!")            # 1;2;3!
age = int(input("나이: "))                   # input은 항상 str
n1, n2 = map(int, input().split())           # 여러 값 한 번에
nums = list(map(int, input().split()))
```

### 3. 문자열

```python
s = "Hello, World!"
s[0], s[-1]          # 'H', '!'
s[0:5], s[7:]        # 'Hello', 'World!'   [start:end) — end는 포함 안 함
s[::2], s[::-1]      # 'Hlo ol!', 거꾸로
s.find("Python")     # 없으면 -1
s.index("Python")    # 없으면 ValueError
"a,b,c".split(",")   # ['a', 'b', 'c']  (리스트)
" & ".join([...])    # 리스트 → 문자열
```

- 문자열은 **바꿀 수 없음**: `s[0] = 'h'`는 `TypeError` → `'h' + s[1:]`처럼 새로 만든다.
- `replace` 같은 메서드는 원본을 바꾸지 않고 새 문자열을 돌려줘요 → 원본에 다시 담을지, 새 변수에 담을지 정해야 해요.

### 4. 조건문

```python
if score < 0 or score > 100:   # 예외부터 먼저 걸러 낸다
    print("범위 밖")
elif score >= 90: ...
result = "합격" if score >= 60 else "불합격"
if "apple" in fruits: ...
```

- 위에서부터 **첫 번째로 맞는 길 하나만** 실행 → 순서가 결과를 바꿔요.
- 윤년: `(y % 4 == 0) and (y % 100 != 0 or y % 400 == 0)` — 괄호로 묶음을 분명히.

## 내가 작성한 코드

```python
# 입출력 실습 1+ : 숫자만 int로 바꾸기
name, age = map(lambda x: int(x) if x.isdigit() else x,
                input("이름과 나이를 입력하세요: ").split())

# 문자열 실습 2
sentence = "   I love Python. Python is powerful!   "
sentence = sentence.strip().lower()
sentence.count("python")                 # 2
sentence.replace("python", "java")
sentence.split()                         # 공백 기준 단어 리스트

# 조건문 미니과제 5 : 알파벳 아닌 것부터 거르기
if not s.isalpha():
    print("알파벳 이외의 문자가 있습니다.")
elif s.islower():
    print("전부 소문자")
elif s.isupper():
    print("전부 대문자")
else:
    print("대소문자 섞여 있음")
```

### 삼각형 판정 — 순서를 바꿔서 고친 코드

```python
if a <= 0 or b <= 0 or c <= 0:
    print("삼각형이 아닙니다.")
elif not (a + b > c and a + c > b and b + c > a):
    print("삼각형이 아닙니다.")
else:
    if a**2 + b**2 == c**2 or b**2 + c**2 == a**2 or a**2 + c**2 == b**2:
        print("직각삼각형")              # 직각을 먼저 판정
    elif a == b == c:
        print("정삼각형")
    elif a == b or b == c or a == c:
        print("이등변삼각형")
    else:
        print("일반 삼각형")
# 3 4 5 → 직각삼각형
```

## 내가 한 실수 / 헷갈린 것

| 실수 | 증상 | 고침 |
| --- | --- | --- |
| 삼각형 판정에서 `a != b != c`를 직각보다 먼저 검사 | `3 4 5`가 "일반 삼각형" | 직각삼각형 조건을 먼저. 그리고 `a != b != c`는 a와 c를 비교하지 않음 |
| `bool(input("True 또는 False"))` | "False"를 입력해도 `True` | 빈 문자열이 아니면 전부 True. `choose == "y"`처럼 글자를 비교 |
| 뒤 3글자를 `st1[-4:-1]` | `Python` → `tho` | `st1[-3:]` (끝 인덱스는 포함 안 됨) |
| `"apple, banana".split(",")` | `' banana'`처럼 앞 공백이 남음 | `split(", ")` 또는 항목마다 `strip()` |
| `prnt(result)` | `NameError` | 오타 → `print` |
| `'h' + str[1:]` | 변수 `str1` 대신 내장 타입 `str`을 슬라이스해서 오류 | `'h' + str1[1:]`, 내장 이름(`str`, `list`, `id`)을 변수명으로 쓰지 않기 |
| `print(st1, "", st2, "!")` | `Hello  Python !` (공백이 겹침) | f-string `f"{st1} {st2}!"` |

**핵심: `input()`은 항상 문자열 / 슬라이스 끝은 포함 안 함 / 조건은 위에서부터 하나만 실행**

## 다음에 할 것

- 08-05 반복문 미니과제 9문제(1~n 출력, 합, 3의 배수, 약수, 0 입력 시 종료, 피라미드, 숫자 맞히기, 구구단, 자릿수 합)
- 이어지는 보강: [1장](../01-syntax-conditionals-collections/) → [3장](../03-operators-conditionals-loops/)(반복문 드릴)
