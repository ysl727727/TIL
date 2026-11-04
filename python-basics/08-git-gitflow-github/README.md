# 8장. git · Git Flow · GitHub (보강 2주 3일)

> 2026-11-04 학습 기록. Python 보강 2주 3일 수업이에요. 1일에 클래스로 묶고, 2일에 파일로 나누고 테스트했다면, 3일은 **그 코드를 git으로 기록하고 Git Flow로 협업하는 법**이에요. 로컬 연습 저장소(`practice`)에서 커밋 · 가지 · merge를 해 보고, 팀 저장소(`git-study`)에 내 feature 가지를 올려 develop으로 PR을 만들었어요. 실습 저장소 내용은 올리지 않고 명령과 헷갈린 점만 정리해요.

## 진행 상황

> 내 `practice` 저장소의 `git log --graph` 기준으로 표시했어요.

| 단계 | 할 일 | 상태 |
|---|---|---|
| 0단계 | `git init` → add → commit → `diff` → `restore` | ✅ (README 커밋 + `--amend`) |
| 기초 1 · 2 | app.py 커밋 → 수정 → `git diff` → 커밋 | ✅ (`feat: add app.py`, `fix: app.py print`) |
| 기초 3 | `.env` + `.gitignore` → `chore: ignore .env` | ⬜ 남음 |
| 응용 1 | main에서 develop 만들고 이동 | ✅ |
| 응용 2 | feature/greet → `--no-ff`로 develop에 merge | ✅ (merge 커밋 2개) |
| 응용 3 | release/1.0 → VERSION → main merge + tag v1.0.0 → develop merge | ⬜ 남음 |
| 심화 1 · 2 | hotfix/1.0.1 → main + tag → develop merge 충돌 해결 | ⬜ 남음 |
| 심화 3 | `git revert`로 되돌리기 | ⬜ 남음 |
| 실무 1 | 원격 연결 → feature 가지 push → PR(base develop) | 🧪 팀 저장소에 `feature/ysl` push · PR 생성까지 |
| 더 해 보기 | 두 폴더 clone → 같은 줄 수정 → 충돌 해결 | 📘 정리만 (6-1) |

## 큰 흐름

```text
git config 설정(처음 한 번)
→ git init / clone 으로 저장소
→ 수정 → git add → git commit   (작업 폴더 → 스테이지 → 커밋)
→ develop에서 feature/이름 가지 만들기
→ git push origin feature/이름
→ GitHub PR (base = develop) → Merge
→ git switch develop; git pull  → 다 쓴 가지 삭제
```

> 한 줄로: 기록은 작업 폴더 → 스테이지 → 커밋, 협업은 feature 가지 → PR → develop. **push 전이면 reset, push 후면 revert.**

---


## 1. 처음 한 번: git config

```powershell
git config --global user.name "이름"
git config --global user.email "GitHub 이메일"
git config --global init.defaultBranch main
git config --global core.editor "code --wait"
git config --global core.autocrlf false
git config --global pull.rebase false       # pull은 merge 방식으로
git config --global fetch.prune true        # 원격에서 지워진 가지는 내 쪽에서도 정리
git config --global --list                  # 확인: 7개 다 보이면 OK
```

- `--global` = 이 컴퓨터 전체에 적용. 어느 폴더에서 쳐도 똑같다.
- `--global` 없이 쓰면 **그 저장소에서만** 적용된다.
- `#` 뒤는 PowerShell 주석이라 같이 붙여넣어도 괜찮다.
- user.email은 GitHub 계정 이메일과 같아야 커밋이 내 계정으로 연결된다.
- 저장소는 **OneDrive 밖**에 만든다 (.git이 깨질 수 있음).
- 파일 만들기: `Set-Content`(새로 쓰기/덮어쓰기), `Add-Content`(맨 끝에 줄 추가). `echo ... > 파일`은 글자 형식이 달라져서 쓰지 않는다.

---

## 2. git은 "저장 버튼"이 아니라 "되돌릴 수 있는 기록"

Ctrl+S로 저장하면 이전 내용은 사라진다. git은 시점마다 스냅샷을 남겨서 언제든 그때로 돌아갈 수 있다.

## 3. 세 곳: 작업 폴더 → 스테이지 → 커밋

```
작업 폴더 (내가 편집하는 파일)
   │  git add 파일
   ▼
스테이지 (다음 커밋에 넣을 것 고르는 대기실)
   │  git commit -m "메시지"
   ▼
커밋 (스냅샷, 영구 기록)
```

```powershell
git status --short        # 지금 상태
git add app.py            # 스테이지에 올리기
git commit -m "feat: add app.py"
git log --oneline         # 커밋 목록 한 줄씩
git diff                  # 작업 폴더 vs 마지막 커밋: 무엇이 바뀌었나
```

### status --short 읽기 (왼쪽 = 스테이지, 오른쪽 = 작업 폴더)

| 표시 | 뜻 |
|---|---|
| `??` | git이 모르는 새 파일 |
| ` M` | 수정했지만 아직 add 안 함 |
| `M ` | add까지 함 |
| `A ` | 새 파일을 add 함 |
| ` D` | 커밋된 파일을 지움 (아직 add 안 함) |
| `UU` | 양쪽 모두 수정 = 충돌 |
| (아무것도 없음) | 깨끗함 (working tree clean) |

### 커밋 메시지 머리말

| 머리말 | 뜻 |
|---|---|
| `feat:` | 기능 추가 |
| `fix:` | 버그 수정 |
| `docs:` | 문서 |
| `chore:` | 설정·잡일 |

> 실수: `fixed` 처럼 머리말 없이 쓰지 말기 → `fix: change print to world333` 처럼 무엇을 고쳤는지까지.

---

## 4. Git Flow: 가지마다 맡은 일이 있다

| 가지 | 어디서 만들고 | 어디로 합치나 | 하는 일 |
|---|---|---|---|
| main | 처음부터 있음 | 없음 | 실제로 배포된 코드. 직접 커밋하지 않음 |
| develop | main에서 한 번 | release를 거쳐 main으로 | 다음 배포에 들어갈 것을 모으는 줄기 |
| feature/이름 | develop | develop | 기능 하나 |
| release/버전 | develop | main과 develop | 배포 직전 정리, 버전 번호 |
| hotfix/버전 | main | main과 develop | 이미 배포된 코드의 급한 버그 |

```
main     ●────────────────────●─────────●   v1.0.0   v1.0.1
          \                  /  \      /  \
hotfix     \                /    ●────●    \       급한 버그 수정
            \              /                \
release      \        ●───●                  \      배포 준비
              \      /     \                  \
develop        ●────●───────●────●─────────────●    다음 배포 모으기
                \  /
feature          ●●                                 기능 하나
```

```powershell
git switch -c feature/greet                    # 지금 가지에서 새 가지 만들고 이동
git switch develop                             # 다른 가지로 이동
git merge --no-ff feature/greet -m "merge: feature/greet"   # 합치기
git tag v1.0.0                                 # 배포 시점에 이름표
git log --oneline --graph --all                # 모든 가지를 그림으로
git branch                                     # 가지 목록 (* = 지금 가지)
git branch -a                                  # 원격 가지까지
git branch -d 가지                             # 다 쓴 가지 지우기
```

- `--no-ff` = 합친 흔적(merge 커밋)을 꼭 남겨라 → 그래프에 갈라진 선이 남는다.
- hotfix와 release는 **두 곳(main, develop)**에 합친다. main에만 합치면 다음 배포 때 버그가 다시 살아난다.
- 같은 줄을 두 가지에서 다르게 고치면 merge 때 충돌 → `<<<<<<<`, `=======`, `>>>>>>>` 사이를 사람이 하나로 정리하고 add → commit.
- 작은 팀은 main + feature만 쓰는 GitHub Flow도 많이 쓴다.

### 외울 것
- `git switch 가지` = 이미 있는 가지로 이동
- `git switch -c 가지` = 새로 만들고 이동 (**지금 있는 가지 기준**으로 만들어짐 → feature는 develop에서!)
- 지금 있는 가지는 `-d`로 못 지운다 → 다른 가지로 옮긴 뒤 지우기

---

## 5. 되돌리기: 실수의 종류에 맞는 명령 하나

| 상황 | 명령 | 뜻 |
|---|---|---|
| 수정했는데 커밋 전, 버리고 싶다 | `git restore 파일` | 작업 폴더를 마지막 커밋으로 |
| add까지 했는데 빼고 싶다 | `git restore --staged 파일` | 스테이지에서만 내림(수정은 유지) |
| 방금 커밋 메시지 오타 | `git commit --amend -m "새 메시지"` | 마지막 커밋을 고쳐 씀 |
| 방금 커밋을 풀고 다시 하고 싶다 | `git reset --soft HEAD~1` | 커밋만 취소, 변경은 스테이지에 남김 |
| 이미 push한 커밋을 취소 | `git revert 커밋` | "반대 내용의 새 커밋"을 추가 |
| reset --hard로 날렸다 | `git reflog` → `git reset --hard HEAD@{n}` | HEAD가 거쳐 온 기록으로 복구 |

> **한 줄 원칙: push 전이면 reset, push 후면 revert.** 공유된 기록은 지우지 말고 덧붙여 되돌린다.

- `--amend`는 기존 커밋을 고치는 게 아니라 **새 커밋으로 바꿔치기** → 커밋 해시가 바뀐다 (`6da9460` → `389f9ec`). 그래서 push 후엔 쓰지 않는다.

---

## 6. GitHub: push, Pull Request, merge

```powershell
git remote add origin https://github.com/<계정>/<저장소>.git   # 원격에 origin 이름 붙이기
git remote -v                         # 원격 확인
git push -u origin main               # 처음 올릴 때 -u로 연결
git pull                              # 원격의 새 커밋 가져와 합치기
git clone https://github.com/<계정>/<저장소>.git   # 원격 저장소 통째로 받기
```

### 같은 저장소에서 PR 흐름 (팀·회사 대부분)

```powershell
git switch develop; git switch -c feature/readme   # ① develop에서 가지 만들고 작업, 커밋
git push -u origin feature/readme                  # ② 가지를 GitHub에 올리기
# ③ GitHub 웹: Compare & pull request → base를 develop으로 바꾸기 → Create pull request
# ④ (팀이면) 동료가 Files changed에서 리뷰 → Approve
# ⑤ Merge pull request → Confirm merge
git switch develop; git pull                       # ⑥ 합쳐진 develop 받기
git branch -d feature/readme                       # ⑦ 다 쓴 가지 지우기
```

- PR 기본 base는 **main** → feature는 **develop으로 꼭 바꾸기**.
- 팀 규칙: main·develop에 직접 push 금지 · PR은 작게(한 가지 일) · PR 전 `uv run pytest` 통과.

### 포크(fork): 쓰기 권한 없는 남의 저장소(오픈소스)에 기여할 때

```powershell
# ① GitHub 웹: 원본에서 Fork → 내 계정에 복사본
git clone https://github.com/<내계정>/<저장소>.git                  # 내 복사본 (origin)
git remote add upstream https://github.com/<원본계정>/<저장소>.git  # 원본 (upstream)
git switch -c fix/typo                 # ② 가지 만들어 작업, 커밋
git push -u origin fix/typo            # ③ 내 복사본에 올리기
# ④ GitHub 웹: 원본 저장소로 Pull Request
git switch main; git pull upstream main; git push origin main   # 원본 바뀌면 따라가기
```

- **origin = 내 복사본, upstream = 원본.** 헷갈리지 않는 게 핵심.
- Fork할 때 "Copy the main branch only" 체크를 끄면 develop도 같이 복사된다.

---

## 6-1. PR 충돌(conflict) → 관리자 입장에서 no conflict로 만들고 Merge까지

### 충돌은 왜 생기나 (Notion "더 해 보기" 상황)

```
develop ──●────────────●  ← 영희 PR 먼저 Merge (app.py 1줄: print("Hi, Younghee!"))
           \
            ●  feature/hello-chulsoo  (app.py 1줄: print("Hi, Chulsoo!"))
```

- 영희와 철수가 **같은 develop**에서 출발해 **같은 줄**을 다르게 고쳤다.
- 영희 PR이 먼저 합쳐지면 develop이 바뀐다 → 철수 PR에 빨간 경고:
  `This branch has conflicts that must be resolved`
- 이 상태에서는 **Merge pull request 버튼이 잠긴다.**
- (실제 git-study에서도 PR #5 `feature/choi → develop`이 `CONFLICTING` 상태였다)

### 충돌 표시 읽는 법

```
<<<<<<< HEAD              ← 지금 내 가지(feature) 쪽 내용
print("Hi, Chulsoo!")
=======                   ← 구분선
print("Hi, Younghee!")
>>>>>>> develop           ← 합치려는 쪽(develop) 내용
print("bye")
```

- 둘 중 하나를 고르거나, **둘을 합친 한 줄**로 정리한다.
- `<<<<<<<`, `=======`, `>>>>>>>` 세 줄은 **반드시 전부 지운다.** 남기면 그대로 코드에 들어가서 실행 에러가 난다.

### 관리자 방법 A. GitHub 웹에서 바로 해결 (간단한 충돌)

1. 충돌 난 PR 페이지 → 아래쪽 **Resolve conflicts** 버튼
2. 웹 편집기에 충돌 표시가 보인다 → 최종 내용으로 고친다
   ```
   print("Hi, Younghee and Chulsoo!")
   print("bye")
   ```
3. 표시 줄 3개 다 지웠는지 확인 → 오른쪽 위 **Mark as resolved**
4. **Commit merge** → feature 가지에 "develop을 합친 merge 커밋"이 붙는다
5. PR 화면이 초록색으로 바뀐다:
   `This branch has no conflicts with the base branch` ← **no conflict 완성**
6. **Files changed**에서 최종 내용 확인 → (리뷰) **Approve**
7. **Merge pull request** → **Confirm merge**
8. **Delete branch** (다 쓴 feature 가지 정리)

- Resolve conflicts 버튼은 **쓰기 권한(collaborator 이상)**이 있어야 보인다.
- 충돌이 복잡하면 버튼이 안 나오거나 회색 → 방법 B로.

### 관리자 방법 B. 내 컴퓨터에서 해결하고 push (확실한 방법)

```powershell
git fetch origin                              # 원격 최신 정보 받기 (PR 가지 포함)
git switch feature/hello-chulsoo              # PR 가지로 이동 (origin 것을 따라가는 로컬 가지 자동 생성)
git pull origin develop                       # 최신 develop을 이 가지에 합치기
                                              # CONFLICT (content): Merge conflict in app.py
git status --short                            # UU app.py   ← 충돌 난 파일
Get-Content app.py                            # <<<<<<< / ======= / >>>>>>> 확인
Set-Content app.py 'print("Hi, Younghee and Chulsoo!")', 'print("bye")'   # 정리 (VS Code로 고쳐도 됨)
git add app.py                                # "해결했다"고 git에 알리기
git commit --no-edit                          # merge 커밋 (기본 메시지 그대로)
git push                                      # 같은 PR에 커밋이 붙는다
```

→ GitHub PR 화면 새로고침 → `This branch has no conflicts with the base branch` → **Merge pull request** → **Confirm merge** → **Delete branch**

- 충돌 해결 뒤 `git add` = "이 파일 충돌 해결 끝"이라는 신호. `UU` → `M `으로 바뀐다.
- 중간에 포기하고 원래대로: `git merge --abort`
- VS Code에서는 충돌 위에 **Accept Current / Accept Incoming / Accept Both** 버튼이 뜬다 (Current = 내 가지, Incoming = develop).

### 관리자 방법 C. 작성자에게 해결 요청

PR에 댓글: "develop 최신 받아서 충돌 해결 후 push 부탁해요" → 작성자가 방법 B를 자기 컴퓨터에서 진행 (Notion "더 해 보기" 3번이 바로 이 작성자 쪽 흐름).

### Merge 후 모두 최신으로

```powershell
git switch develop
git pull                                      # 합쳐진 develop 받기
Get-Content app.py                            # print("Hi, Younghee and Chulsoo!") / print("bye")
git branch -d feature/hello-chulsoo           # 내 컴퓨터의 다 쓴 가지 정리
```

### 외울 것
- 충돌 = **같은 파일의 같은 줄**을 두 가지가 다르게 고쳤을 때. 다른 줄이면 git이 알아서 합친다.
- 해결 공식: **최신 develop을 feature 가지에 합친다 → 표시 줄 지우고 정리 → add → commit → push.**
- 충돌은 develop이 아니라 **feature 가지 위에서** 해결한다 (develop에 직접 push 금지 규칙).
- 목표 문구: 빨강 `This branch has conflicts that must be resolved` → 초록 `This branch has no conflicts with the base branch`
- 관리자는 Merge 전에 **Files changed**로 최종 결과를 꼭 확인한다.

---

## 7. 실습 단계 (한 저장소를 1→10단계로 키우기)

| 단계 | 할 일 |
|---|---|
| 0단계 | `git init git-practice` → hello.py → add → commit → `Add-Content` → `diff` → `restore` |
| 기초 1 | git-flow 저장소, app.py `print("hello")` → `feat: add app.py` |
| 기초 2 | `print("bye")` 추가 → `git diff` 확인 → `feat: add bye message` |
| 기초 3 | `.env`(API_KEY=fake-key-1234) + `.gitignore`에 `.env` → `chore: ignore .env` |
| 응용 1 | main에서 develop 가지 만들고 이동 |
| 응용 2 | feature/greet → greet.py → `--no-ff`로 develop에 merge → 가지 삭제 |
| 응용 3 | release/1.0 → VERSION(1.0.0) → main merge + tag v1.0.0 → develop merge |
| 심화 1 | main에서 hotfix/1.0.1 → `print("Hello!")` → main merge + tag v1.0.1 |
| 심화 2 | hotfix를 develop에 merge → 충돌(UU) 해결 `print("Hello, team!")` |
| 심화 3 | `chore: debug print` 커밋 → `git revert`로 되돌리기 |
| 실무 1 | GitHub 원격 연결 → main/develop/태그 push → feature/readme PR(base develop) → Merge |
| 더 해 보기 | 같은 저장소를 두 폴더에 clone, 폴더별 `git config user.name`(--global 없이) → 같은 줄 수정 → `git pull origin develop`으로 충돌 해결 |

> 비밀값(.env)은 `.gitignore`에 적어서 절대 커밋하지 않는다. 무시된 파일은 `git status`에도 안 보인다.

---

## 8. 오늘 내가 질문한 것 / 겪은 실수

### Q1. config 7개 이렇게 넣은 거 맞아?
맞다. `git config --global --list`로 7개 다 보이면 OK. `--global`이라 day6에서 쳐도 컴퓨터 전체에 적용.

### Q2. 커밋된 app.py를 지웠더니 `deleted: app.py`가 뜬다
커밋에 들어간 파일은 폴더에서 지워도 **커밋 안에는 남아 있다.** 지운 것도 변경이라 `git add 파일`(또는 `git rm 파일`) → commit 해야 기록된다.
- 처음부터 없던 것처럼 하려면(push 전): `git add app.py` → `git commit --amend -m "docs: add README.md"`
- 되살리려면: `git restore app.py`

### Q3. `nothing to commit, working tree clean`이 떴다
에러 아님. 마지막 커밋 이후 **바뀐 게 없다**는 뜻. (이미 amend로 끝났거나, 파일을 수정/저장 안 했을 때)

### Q4. Set-Content로 바꿨는데 app.py가 안 바뀌었다
Set-Content는 성공했고 커밋까지 됐다. 그런데 **VS Code에 저장 안 한 옛 내용**이 열려 있었고, 그 상태로 Ctrl+S → 옛 내용이 덮어씀.
- 같은 파일을 PowerShell과 VS Code에서 동시에 건드리면 **나중에 저장한 쪽이 이긴다.**
- VS Code 탭에 ● = 저장 안 된 내용 있음.
- 해결: 필기는 README.md로 옮기고, app.py는 `git restore app.py`로 커밋 상태(333) 복구.

### Q5. day6 저장소 안에 git-study를 clone했다 (저장소 안에 저장소)
`git status`에 `?? git-study/`가 뜬다. 여기서 `git add .`하면 꼬인다.
- **저장소끼리는 형제 폴더로.** 부모-자식으로 두지 않는다.
- clone 전에 `pwd`로 지금 위치가 저장소 밖인지 확인.
- 최종 구조:
  ```
  day6/              ← 그냥 폴더 (.git 없음)
    practice/        ← 로컬 연습 저장소
    git-study/       ← GitHub clone
  ```
- 저장소의 정체는 `.git` 폴더 → 폴더째 옮겨도 기록은 그대로.

### Q6. `Move-Item git-study ..\git-study` 했는데 사라졌다
사라진 게 아니라 **한 칸 위**로 이동. `.` = 현재 폴더, `..` = 한 칸 위 폴더.

### Q7. `Rename-Item` → "액세스가 거부되었습니다"
그 폴더를 다른 프로그램(VS Code, 다른 터미널)이 **사용 중**이라는 뜻. 닫고 다시 하거나, 폴더째 말고 내용물만 옮긴다.
- 숨김 폴더 `.git`까지 옮길 땐 `Move-Item ... -Force`

### Q8. `fatal: not a git repository`
git 저장소 **밖**에서 git 명령을 쳤다. `.git`이 있는 폴더로 `cd`해서 들어가기.

### Q9. `git git push ...` → `'git' is not a git command`
`git`을 두 번 침. 앞의 git 하나만: `git push origin feature/yongseok`

### Q10. push했더니 403 `Permission ... denied to ysl727727`
로그인은 됐지만 **그 계정에 쓰기 권한이 없음.** 로그인 문제가 아니다. 에러의 `denied to 계정명`으로 어떤 계정인지 확인.
- 해결 A: 저장소 주인이 Settings → Collaborators에서 내 계정 초대 → 수락 → 다시 push
- 해결 B: fork해서 내 저장소로 push → 원본으로 PR
- 해결 C: git 로그인 계정 바꾸기 (자격 증명 관리자에서 `git:https://github.com` 제거 → 다시 로그인)
- → 오늘은 A로 해결 (push 권한 true).

### Q11. remote가 꼬였다 (origin, upstream이 둘 다 같은 주소)
`git remote -v`로 확인. 필요 없으면 `git remote remove upstream`. 이름 바꾸기는 `git remote rename origin upstream`.

### Q12. 권한 받은 뒤 다시 clone해야 해?
아니다. clone은 저장소당 한 번. 이후 최신은 `git pull`.

### Q13. feature/ysl이 develop이 아니라 main에서 갈라져 있었다
로컬에 develop이 없었기 때문. 다시 만드는 순서:
```powershell
git restore --staged app.py      # 스테이지에서 내리기
Remove-Item app.py               # 전환 시 충돌 방지
git switch develop               # origin/develop 따라가는 로컬 develop 자동 생성
git branch -d feature/ysl        # 내 커밋 없는 옛 가지 삭제
git switch -c feature/ysl        # develop 기준으로 새로
```
- `branch 'develop' set up to track 'origin/develop'` = 원격 develop을 따라가는 로컬 develop이 생겼다는 뜻.

### Q14. add, commit 했는데 또 `nothing to commit`
파일을 **수정·저장 안 해서** 올릴 게 없었다. add 전에 `git status --short`로 ` M` 있는지 먼저 확인하는 습관.

### Q15. PowerShell에 `print('ysl')` → "PRN 장치를 초기화할 수 없습니다"
파이썬 코드를 터미널에 침. PowerShell의 `print`는 **프린터 명령**이다.
- 파일에 넣기: VS Code에서 쓰고 저장, 또는 `Add-Content app.py "print('ysl')"`
- 실행: `uv run python app.py`

### Q16. `git switch -c feature/yongseok` 맞아?
맞다. 단, **develop에 있을 때** 쳐야 develop 기준으로 만들어진다. 다른 가지의 merge 안 된 커밋은 새 가지에 없는 게 정상.

### Q17. PR을 잘못 올렸다 (다른 계정 / base main) → 삭제?
**PR은 삭제가 안 된다. Close만 가능.**
- PR 페이지 맨 아래 **Close pull request** → (원하면) **Delete branch** (원격 가지만 지워짐, 내 컴퓨터 가지는 남음)
- base가 main으로 잘못됐으면: 제목 옆 **Edit**로 base를 develop으로 바꾸거나, 닫고 다시 만들기.

---

## 9. 오늘 성공한 최종 흐름 (git-study)

```powershell
cd bogang\day6\git-study
git switch develop
git switch -c feature/ysl
Add-Content app.py "print('ysl')"
git status --short               #  M app.py
git add app.py
git commit -m "feat: add ysl print"
git push origin feature/ysl      # 71138cf..0cbdf8f  feature/ysl -> feature/ysl
# GitHub: Compare & pull request → base: develop / compare: feature/ysl → Create pull request
```

---

## 10. 체크아웃 (빈칸 채우기)

- feature는 **develop**에서 만들어 **develop**으로 합치고, hotfix는 **main**에서 만들어 **main**과 **develop** 두 곳에 합친다.
- push 전이면 **reset**, push 후면 **revert**.
- 2주차 정리: 클래스로 묶고(1일), 파일로 나누고 테스트하고(2일), git으로 기록하고 Git Flow로 협업했다(3일).

---

## 11. 명령어 치트시트

| 하고 싶은 것 | 명령 |
|---|---|
| 새 저장소 | `git init 폴더` |
| 원격 받기 | `git clone URL` |
| 상태 | `git status` / `git status --short` |
| 스테이지 | `git add 파일` / `git add .` |
| 커밋 | `git commit -m "feat: ..."` |
| 수정된 파일 바로 커밋 | `git commit -am "..."` |
| 기록 | `git log --oneline` / `--graph --all` / `--stat` / `-p` |
| 차이 | `git diff` |
| 가지 목록 | `git branch` / `git branch -a` / `git branch -vv` |
| 가지 이동 / 생성+이동 | `git switch 가지` / `git switch -c 가지` |
| 가지 삭제 | `git branch -d 가지` |
| 합치기 | `git merge --no-ff 가지 -m "merge: 가지"` |
| 태그 | `git tag v1.0.0` / `git tag` |
| 수정 버리기 | `git restore 파일` |
| 스테이지에서 내리기 | `git restore --staged 파일` |
| 지운 파일 기록 | `git rm 파일` (= 지우고 `git add 파일`) |
| 마지막 커밋 고치기 | `git commit --amend -m "..."` |
| 커밋 취소(push 전) | `git reset --soft HEAD~1` |
| 커밋 취소(push 후) | `git revert 커밋` |
| 날린 것 복구 | `git reflog` → `git reset --hard HEAD@{n}` |
| 원격 확인/추가/삭제/이름변경 | `git remote -v` / `add` / `remove` / `rename` |
| 올리기 | `git push origin 가지` (`-u`는 처음 연결) |
| 받기 | `git pull` / `git pull origin develop` |
| 원격 정보만 받기 | `git fetch origin` |
| 충돌 해결 후 | `git add 파일` → `git commit --no-edit` |
| merge 포기 | `git merge --abort` |
| 설정 확인 | `git config --global --list` |
| 파일 새로 쓰기 / 줄 추가 (PowerShell) | `Set-Content 파일 '내용'` / `Add-Content 파일 '내용'` |
| 폴더 이동 (PowerShell) | `Move-Item A ..\A` (숨김은 `-Force`) |

---

## 오늘의 한 줄

- git은 저장 버튼이 아니라 **되돌릴 수 있는 기록**이다. 공유된 기록은 지우지 말고 덧붙여 되돌린다(revert).
- feature는 **develop에 있을 때** 만들고, PR의 base도 **develop**으로 바꾼다.
- 충돌은 develop이 아니라 **feature 가지 위에서** 최신 develop을 합쳐 푼다.

2주 1일 [클래스](../06-classes/) → 2주 2일 [모듈 · 예외 · pytest · logging](../07-modules-exceptions-pytest-logging/) → 2주 3일 git · Git Flow
