# Chapter 1: 변수·조건문·리스트·딕셔너리 기초 드릴

> 2026-09-29 학습 기록. **Python 보강 자료**로 받은 연습 파일 3개를 직접 타이핑하며 확인했습니다. 변수와 자료형, 조건문, 리스트·딕셔너리 메서드, 중첩 반복문이 대상입니다. 강의 노트가 아니라 손으로 돌려 본 드릴이라 정답 코드와 주석 형태로 남겼습니다.

## Practice Files

| File | Topics | Practice status |
| --- | --- | --- |
| `01-variables-types-and-fstrings.py` | 변수 재할당, `int`/`float`/`str` 변환, `type().__name__`, 비교 연산과 체이닝, 문자열 결합 3가지, 이스케이프 | 완료(직접 실행) |
| `02-conditionals-and-list-methods.py` | `if`/`elif`/`else`, 중첩 조건문과 `input()`, `extend`/`append`/`remove`/`pop`/`sort(reverse=True)` | 완료(직접 실행) |
| `03-dict-methods-and-nested-loops.py` | `dict.update`/`keys`, 2차원 리스트 인덱스 탐색, 짝수/홀수 합 | 완료(직접 실행) |

## Core Points

### 1. 변수와 자료형

- `a = a + 1`처럼 자기 자신을 참조해 다시 대입하는 형태가 가장 기본적인 갱신 패턴이다.
- 문자열 `"30"`에 숫자를 더하려면 `int(minutes) + 10`으로 변환한다. 계속 숫자로 쓸 거라면 `minutes = int(minutes)`로 **변수 자체를 바꿔 둔다**.
- `type(count).__name__`은 `<class 'int'>` 대신 `int`만 출력한다.

### 2. 비교 연산과 체이닝

```python
priority = 1
print(priority < True)          # False — True는 1로 취급된다
print(True <= priority <= 3)    # True  — 1 <= 1 and 1 <= 3
```

Python에서 `bool`은 `int`의 하위 자료형이라 `True == 1`, `False == 0`이다. 비교를 `a <= b <= c`로 이어 쓰면 `a <= b and b <= c`와 같고, `b`는 한 번만 계산된다.

### 3. 문자열 결합 세 가지

```python
print("안녕," + name)   # + 는 문자열끼리만 가능
print(name, "안녕")     # 쉼표는 공백을 자동으로 넣는다
print(f"{name} 안녕")   # f-string이 가장 읽기 쉽다
```

`\n`은 줄바꿈, 작은따옴표로 감싸면 큰따옴표를 그대로 쓸 수 있다(`'"복습"완료'`).

### 4. 조건문 — `elif`와 중첩

```python
if int(birth_date) < 2000:
    if gender == "남성":
        print("start with 1")
    elif gender == "여성":
        print("start with 2")
    else:
        print("성별이 올바르지 않습니다.")
```

`input()`은 항상 **문자열**을 돌려주므로 숫자 비교 전에 `int()`로 바꾼다. 바깥 조건(출생연도)과 안쪽 조건(성별)을 분리하면 경우의 수가 늘어도 구조가 유지된다.

### 5. 리스트 메서드 — 무엇을 반환하는가

| 메서드 | 하는 일 | 반환값 |
| --- | --- | --- |
| `append(x)` | 끝에 **한 개** 추가 | `None` |
| `extend(list)` | 다른 리스트 원소를 **풀어서** 추가 | `None` |
| `remove(값)` | 그 **값**을 찾아 첫 번째 것 제거 | `None` |
| `pop(index)` | 그 **위치**의 원소 제거 | 제거한 값 |
| `sort(reverse=True)` | 제자리 내림차순 정렬 | `None` |

`append(extra_member)`로 리스트를 넣으면 리스트 안에 리스트가 들어가고, `extend`는 원소를 하나씩 풀어 넣는다. `remove`는 값, `pop`은 인덱스를 받는다는 차이가 핵심이다.

**순서가 결과를 바꾼다** — `remove(32)`로 원소를 하나 지운 뒤 `pop(2)`를 하면, 지우기 전 기준의 3번째가 아니라 **지운 뒤 기준의 3번째**가 사라진다.

### 6. 딕셔너리

```python
phones.update({"Samsung": "Galaxy"})        # 없으면 추가
phones.update({"Samsung": "Galaxy Series"}) # 있으면 덮어쓰기
print(phones.keys())                        # dict_keys([...])
```

`update()`는 추가와 수정을 같은 메서드로 처리한다. `keys()`는 리스트가 아니라 `dict_keys` 뷰를 돌려주며, 리스트가 필요하면 `list(phones.keys())`로 감싼다.

### 7. 중첩 반복문으로 인덱스 찾기

```python
for i in range(len(matrix)):
    for j in range(len(matrix[i])):
        if matrix[i][j] == "Hyundai":
            print(i, j)
```

안쪽 범위를 `len(matrix[1])`처럼 **특정 행 길이로 고정하면** 행마다 길이가 다를 때 건너뛰거나 `IndexError`가 난다. `len(matrix[i])`로 현재 행을 기준으로 두는 편이 안전하다.

### 8. 짝수·홀수 합

```python
total = 0
for row in matrix2:
    for n in row:
        if n % 2 == 0:
            total += n
```

`range(len(...))` 없이 원소를 직접 순회하면 인덱스를 신경 쓰지 않아도 된다. **인덱스가 필요하면 `range(len(...))`, 값만 필요하면 직접 순회**로 구분한다. 음수까지 다룰 때는 홀수 판정을 `n % 2 == 1` 대신 `n % 2 != 0`으로 쓰는 편이 안전하다.

## Questions and Newly Learned Points

- `True <= priority <= 3`이 참인 이유가 `True == 1`이기 때문이라는 점이 가장 의외였다.
- `append`와 `extend`, `remove`와 `pop`의 차이를 "값이냐 위치냐", "하나냐 풀어서냐"로 정리하니 헷갈리지 않았다.
- 리스트 메서드는 대부분 **새 리스트를 반환하지 않고 제자리에서 바꾼다** — `numbers = numbers.sort()`로 쓰면 `None`이 된다.
- 여러 메서드를 연달아 쓸 때는 각 단계 후의 리스트 상태를 직접 그려 보고 다음 인덱스를 정해야 했다.
