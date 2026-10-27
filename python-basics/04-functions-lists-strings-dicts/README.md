# 4장. 함수 · 리스트 · 문자열 · 딕셔너리 드릴 (보강 1주 2일)

> 2026-10-27 학습 기록. Python 보강 1주 2일 수업입니다. 함수(`return`), 기본값·키워드 인자, 슬라이스, 문자열 메서드, 딕셔너리로 세기, 두 수의 합, `sorted`의 `key`, `Counter`를 문제 10개로 연습했습니다(uv + Python 3.12). 문제 파일은 수업 자료라 올리지 않고, 배운 규칙과 내가 푼 코드, 실수만 정리합니다.

## 진행 상황

| 파일 | 문제 | 상태 |
|---|---|---|
| `day2/step0.py` | 0단계 따라 치기 + 수업 코드 실습 | ✅ 진행 (수업 1~5 코드 직접 타이핑) |
| `day2/q1.py` | 기초 1. 평균과 범위 자르기 | ✅ 통과 |
| `day2/q2.py` | 기초 2. 슬라이스로 자르기 | ✅ 통과 |
| `day2/q3.py` | 기초 3. 딕셔너리로 세기 | ✅ 통과 |
| `day2/q4.py` | 응용 1. 리스트 알고리즘 (뒤집기·교대로·누적합) | ⬜ 남음 |
| `day2/q5.py` | 응용 2. 문자열 알고리즘 (모음·단어 뒤집기·to_upper) | ⬜ 남음 |
| `day2/q6.py` | 응용 3. 원본을 지키는 함수 (remove_evens·make_grid) | ⬜ 남음 |
| `day2/q7.py` | 심화 1. 두 수의 합 (20만 개 1초) | ⬜ 남음 |
| `day2/q8.py` | 심화 2. 팰린드롬과 애너그램 | ⬜ 남음 |
| `day2/q9.py` | 심화 3. 2차원 리스트 (transpose·col_sums·trace) | ⬜ 남음 |
| `day2/q10.py` | 실무 1. Counter·sorted·f-string | ⬜ 남음 |

- 실행: `uv run python day2/q4.py` → `통과`가 찍히면 정답
- 1일차 남은 문제: `q6.py` ~ `q10.py` (응용 3, 심화 1~3, 실무 1) → [3장](../03-operators-conditionals-loops/)
- 다음 예고: 정렬과 이진 탐색 직접 구현, 재귀 추적, 시간을 재서 알고리즘 빠르기 비교

## 오늘 배운 것

### 1. 함수: `return` vs `print`
```python
def average(numbers: list[float]) -> float:   # 이름, 매개변수, 타입힌트, 반환 타입
    return sum(numbers) / len(numbers)         # 결과를 밖으로 돌려준다

avg = average([12, 32, 64])                    # 돌려준 값을 변수에 받아서
print(avg > 80)                                # 다음 계산에 쓴다
```
- `print`는 화면에 보여 주기, `return`은 다음 코드가 쓸 값을 돌려주기
- `return`이 없으면 결과는 `None` → `None > 80`은 `TypeError`
- 함수는 정의(`def`)할 때 저장만 되고, 호출할 때 실행됨

### 2. 기본값 매개변수와 키워드 인자
```python
def clamp(x, low=0, high=100): ...

clamp(150)             # low=0, high=100 (둘 다 기본값)
clamp(5, 10, 20)       # 순서대로: low=10, high=20
clamp(150, 200)        # ❌ 순서대로라 low=200이 됨
clamp(150, high=200)   # ✅ low는 기본값, high만 200
```
- 기본값이 있으면 생략 가능, 없으면 꼭 줘야 함
- `이름=값`으로 주면 순서 자유 (`greet(greeting="hi", name="Kiin")`)
- **중간 기본값을 건너뛰고 뒤의 것만 바꾸려면 이름을 꼭 붙여야 함**

### 3. 인덱싱과 슬라이스 `[시작:끝:간격]`
```python
scores = [88, 92, 75, 60, 99]
scores[0], scores[-1]   # 88, 99  (음수는 뒤에서부터)
scores[1:3]             # [92, 75] (끝은 포함 안 함)
scores[::-1]            # 뒤집기
scores[::2]             # 두 칸씩
scores[10:]             # []  슬라이스는 범위를 넘어도 오류 없음 (scores[10]은 IndexError)
```
- 콜론 **왼쪽이 시작, 오른쪽이 끝**
  - `[:-n]` → 뒤 n개를 **뺀** 앞부분
  - `[-n:]` → 뒤 n개
- 리스트는 바꿀 수 있음(`scores[0] = 100`), 문자열은 못 바꿈(`word[0] = "P"`는 `TypeError` → `word.upper()`처럼 새로 만듦)
- 문자열도 슬라이스 규칙이 같음: `"python"[1:4]` → `'yth'`

### 4. 문자열 메서드와 `ord` / `chr`
```python
s = "  hello big world "
s.split()               # ['hello', 'big', 'world']  (공백 기준, 앞뒤·연속 공백 정리)
"-".join(s.split())     # 'hello-big-world'
ord("a")                # 97   글자 → 번호
chr(65)                 # 'A'  번호 → 글자
```
- `A`~`Z` = 65~90, `a`~`z` = 97~122 → **대소문자는 항상 32 차이**
- 번호가 순서대로라 `"a" <= ch <= "z"`로 소문자 판별 가능
- 한글도 번호가 있어서 비교·정렬 가능 (`ord("가")` = 44032)

### 5. 딕셔너리: 이름(키)으로 찾기
```python
counts = {}
for f in ["사과", "배", "사과"]:
    counts[f] = counts.get(f, 0) + 1   # 처음 보는 키는 0에서 시작
print(counts)                          # {'사과': 2, '배': 1}
counts.get("포도", 0)                   # 0  (없는 키를 counts["포도"]로 읽으면 KeyError)
for name, n in counts.items(): ...     # 키와 값을 함께 순회
max(counts, key=counts.get)            # 값이 가장 큰 키
```
- "세기"는 1일차 누적 패턴(`count += 1`)이 키별로 쪼개진 것
- 딕셔너리는 넣은 순서를 기억함
- `.keys()`, `.values()`는 `list()`로 감싸면 리스트처럼 다룰 수 있음

### 6. 두 수의 합: 이중 루프 → 딕셔너리
```python
def two_sum_fast(nums, target):
    seen = {}                          # {값: 위치}
    for i, n in enumerate(nums):
        if target - n in seen:         # 짝을 본 적 있나?
            return (seen[target - n], i)
        seen[n] = i                    # 없으면 지금 수를 기억
```
- `two_sum_fast([2, 1, 4, 5, 7], 9)` → `(2, 3)` (4 + 5, **값이 아니라 위치**)
- 이중 루프는 모든 쌍을 봄(n(n−1)/2번), 딕셔너리는 한 번만 훑음(n번)
- "짝을 찾는다" → "짝이 될 수를 미리 기억해 두고 묻는다"

### 7. `sorted`의 `key`와 `lambda`
```python
sorted(counts, key=lambda s: s[0], reverse=True)   # ['사과', '배']
```
- 딕셔너리를 `sorted`/`max`에 넣으면 **키만** 꺼내서 다룸
- `key`는 **비교 기준만** 정함 → 결과에는 원래 항목이 통째로 나옴 (`'사'`로 비교하지만 `'사과'`가 나옴)
- `lambda s: s[0]` = `def f(s): return s[0]`의 한 줄 버전
- 점수로 정렬하려면 대상이 `(이름, 점수)` 튜플이어야 함: `sorted(students, key=lambda s: s[1], reverse=True)`
- 딕셔너리를 값으로 정렬: `sorted(counts.items(), key=lambda s: s[1], reverse=True)`

### 8. `Counter`
```python
from collections import Counter
Counter(["사과", "배", "사과"]).most_common(1)   # [('사과', 2)]
```
- 세기 패턴을 한 번에 해 줌. `most_common(k)`는 많은 순 k개를 `(항목, 개수)` 리스트로

## 내가 푼 코드 (기초 1~3)

```python
# 기초 1
def average(numbers: list[float]) -> float:
    return sum(numbers) / len(numbers)

def clamp(x, low=0, high=100):
    if x < low:
        return low
    elif x > high:
        return high
    else:
        return x

# 기초 2
def head(items, n):
    return items[:n]

def tail(items, n):
    return items[len(items) - n:]

def every_other(items):
    return items[::2]

def drop_edges(items):
    return items[1:-1]      # 길이 2 이하면 저절로 빈 결과

# 기초 3
def count_items(items: list[str]) -> dict[str, int]:
    counts = {}
    for item in items:
        counts[item] = counts.get(item, 0) + 1
    return counts

def most_common_item(items: list[str]) -> str:
    counts = count_items(items)       # 위 함수 재사용
    best = items[0]
    for item, n in counts.items():
        if n > counts[best]:
            best = item
    return best
```

## 내가 한 실수 / 헷갈린 것

| 실수 | 증상 | 고침 |
|---|---|---|
| `items[len(items-n):]` | 리스트에서 숫자를 빼려고 해서 `TypeError` | `items[len(items) - n:]` (괄호 먼저 닫기) |
| `tail`을 `items[:-n]`로 | 뒤 n개가 아니라 뒤 n개를 **뺀** 나머지 | `[-n:]` 방향 |
| `tail`을 `items[-n:]`로 | n=0이면 `[-0:]` = `[0:]` = 전체 | `items[len(items) - n:]` |
| `sorted(counts, key=lambda s: s[0])`을 점수 정렬로 착각 | 딕셔너리는 키만 나와서 `s[0]`이 키의 첫 글자 | 값 기준이면 `.items()` + `s[1]` |
| `key=`를 쓰면 그 값만 나온다고 생각 | 실제론 원래 항목이 나옴 | key는 줄 세우는 기준일 뿐 |

**핵심: 콜론 왼쪽은 시작, 오른쪽은 끝 / `key`는 기준일 뿐 결과는 원래 항목 / 없는 키는 `.get(key, 0)`**
