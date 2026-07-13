
# 리눅스 기본 환경 구성 및 사용법 (문제1)

---

## 1. 배경

과정2는 ROS2 및 ROS2 파이썬 프로그래밍을 학습하는 것을 목표로 하며, ROS2 Humble은 ubuntu 22.04.x 환경에 최적화되어 있다. 라인트레이싱 운반 로봇의 온보드 컴퓨터(Raspberry Pi 등) 역시 실제로는 ubuntu 리눅스 위에서 ROS2를 구동하게 되므로, 본 문서는 그 이전 단계로 리눅스 개발 환경을 구성하고 기본 사용법을 익히는 내용을 다룬다.

---

## 2. 우분투 리눅스 설치

### 2.1 설치 방법 비교

| 순위    | 방법                                                                                                                                                                                                                                       | 특징                                                                               |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| 1       | 네이티브 설치                                                                                                                                                                                                                              | 컴퓨터 전원 시 우분투가 바로 부팅. 성능은 가장 좋으나 기존 OS와 병행 사용이 어려움 |
| 1       | VMWare Workstation 가상머신<br />[support.broadcom.com/group/ecx/productdownloads?subfamily=VMware%20Fusion&amp;freeDownloads=true](<https://support.broadcom.com/group/ecx/productdownloads?subfamily=VMware%20Fusion&freeDownloads=true>) | 개인 사용자 무료, 스냅샷/복구 기능으로 실습에 유리                                 |
| 2       | Oracle VirtualBox 가상머신                                                                                                                                                                                                                 | 완전 무료(프리웨어), VMWare 대비 성능·안정성이 다소 낮음                          |
| 3(최후) | WSL2                                                                                                                                                                                                                                       | 윈도우 내 설치로 간편하지만 GUI·하드웨어 접근(USB 시리얼 등)에 제약               |

### 2.2 선택한 방법 (가정)

본 실습에서는 **VMWare Workstation 가상머신**에 **ubuntu 22.04.x**를 설치하는 것으로 가정한다. 이유는 다음과 같다.

- 실습 중 잘못된 설정을 스냅샷으로 즉시 복구할 수 있어 반복 학습에 유리하다.
- 이후 과정에서 ROS2·Gazebo 시뮬레이션을 구동할 때 필요한 그래픽/USB 패스스루를 VirtualBox보다 안정적으로 지원한다.
- 호스트 OS(윈도우/맥)를 그대로 유지하면서 로봇 개발 환경만 격리할 수 있다.

### 2.3 설치 절차 개요

1. VMWare Workstation Player/Pro 설치
2. ubuntu-22.04.x-desktop-amd64.iso 다운로드([cdimage.ubuntu.com/ubuntu/releases/22.04/release](https://cdimage.ubuntu.com/ubuntu/releases/22.04/release/)) - ubuntu-22.04.5-live-server-arm64.iso 다운로드
3. 새 가상머신 생성 → ISO 지정 → 메모리 4GB 이상, 디스크 40GB 이상 할당 권장
4. 설치 마법사에 따라 언어/키보드/사용자 계정 설정 후 설치
5. 설치 완료 후 `sudo apt update && sudo apt upgrade` 로 시스템 최신화

---

## 3. 리눅스 기본 사용법

### 3.1 터미널 실행 방법

| 방법           | 설명                                    |
| -------------- | --------------------------------------- |
| 단축키         | `Ctrl + Alt + T`                      |
| GUI 검색       | Activities → "Terminal" 검색 후 실행   |
| 파일 관리자 내 | 폴더에서 우클릭 → "Open Terminal Here" |

### 3.2 파일·디렉토리 관리 명령어

| 명령어    | 기능                    | 예시                       |
| --------- | ----------------------- | -------------------------- |
| `pwd`   | 현재 디렉토리 경로 출력 | `pwd`                    |
| `ls`    | 디렉토리 내용 나열      | `ls -al`                 |
| `cd`    | 디렉토리 이동           | `cd ~/study/linux`       |
| `mkdir` | 디렉토리 생성           | `mkdir -p ~/study/linux` |
| `rm`    | 파일/디렉토리 삭제      | `rm -r 폴더명`           |
| `cp`    | 복사                    | `cp a.txt b.txt`         |
| `mv`    | 이동/이름변경           | `mv a.txt study/`        |
| `find`  | 파일 검색               | `find / -name "*.py"`    |

### 3.3 파일 내용 확인·편집

| 명령어               | 용도                    |
| -------------------- | ----------------------- |
| `cat`              | 파일 전체 내용 출력     |
| `less` / `more`  | 페이지 단위로 내용 확인 |
| `head` / `tail`  | 파일 앞/뒤 일부 확인    |
| `nano`, `vim`    | 터미널 기반 편집기      |
| VS Code (`code .`) | GUI 기반 편집           |

### 3.4 파일 권한

리눅스 파일 권한은 `소유자(user) / 그룹(group) / 기타(other)` 3주체에 대해 `읽기(r)=4, 쓰기(w)=2, 실행(x)=1` 권한을 부여하는 방식이다.

```
-rwxr-xr--  1 user group  ...  1_hello.py
 │└┬┘└┬┘└┬┘
 │ u  g  o
 └ 파일 종류(-: 일반파일, d: 디렉토리)
```

| 명령어    | 기능        | 예시                                                         |
| --------- | ----------- | ------------------------------------------------------------ |
| `chmod` | 권한 변경   | `chmod +x 1_hello.py` (실행 권한 부여), `chmod 755 파일` |
| `chown` | 소유자 변경 | `sudo chown $USER:$USER /test`                             |

### 3.5 실행파일·셸 스크립트와 `source`

- **실행파일**: 실행 권한(`x`)이 있고 `#!` (shebang)로 인터프리터를 지정한 파일. `./script.sh` 또는 `python3 script.py` 형태로 실행한다.
- **셸 스크립트**: `.sh` 확장자의 셸 명령어 모음. 새 서브셸에서 실행되며, 스크립트 내 `cd`나 환경변수 변경이 부모 셸에 반영되지 않는다.
- **`source`**: 스크립트를 현재 셸에서 직접 실행(`source script.sh` 또는 `. script.sh`)하여, 환경변수 설정이나 `cd` 결과가 현재 셸에 그대로 반영되도록 한다. ROS2 사용 시 `source /opt/ros/humble/setup.bash`로 ROS2 환경변수를 현재 셸에 적용하는 것이 대표적 예다.

### 3.6 사용자 권한과 `sudo`

- 리눅스는 일반 사용자와 **슈퍼유저(root)** 를 구분하며, 시스템 설정 변경·패키지 설치 등 민감한 작업은 root 권한이 필요하다.
- `sudo`(superuser do)는 일반 사용자가 임시로 관리자 권한을 얻어 명령을 실행하게 해주는 명령어이다. 예: `sudo apt install code`

### 3.7 패키지 관리와 `apt`

| 명령어                        | 기능                     |
| ----------------------------- | ------------------------ |
| `sudo apt update`           | 패키지 목록 최신화       |
| `sudo apt upgrade`          | 설치된 패키지 업그레이드 |
| `sudo apt install <패키지>` | 패키지 설치              |
| `sudo apt remove <패키지>`  | 패키지 제거              |

### 3.8 홈 디렉토리

`/home/<사용자명>` (축약 표기 `~`)은 사용자별 개인 작업 공간으로, 로그인 시 기본 위치가 된다. 본 실습의 `~/study/linux`도 홈 디렉토리 하위에 생성한다.

---

## 4. 개발 도구 설치

```bash
# Chrome 설치
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install ./google-chrome-stable_current_amd64.deb
크롬안되면 sudo apt install chromium-browser -y 이걸로 설치



# Visual Studio Code 설치
sudo apt update
sudo apt install software-properties-common apt-transport-https wget -y
wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
sudo install -D -o root -g root -m 644 packages.microsoft.gpg /etc/apt/keyrings/packages.microsoft.gpg
sudo sh -c 'echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/keyrings/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list'
sudo apt update
sudo apt install code
```

> WSL2를 사용하는 경우: chrome/VSCode를 리눅스 쪽에 설치하는 대신, 윈도우에 Visual Studio Code를 설치하고 "WSL" 확장을 추가하여 `code .` 명령으로 WSL2의 파일을 윈도우 VSCode에서 원격 편집하는 방식을 사용한다.

---

## 5. 파이썬 프로그램 작성 및 실행

### 5.1 프로그램 내용

`~/study/linux/1_hello.py` (제출본: `2/1/1_hello.py`)는 `/test` 디렉토리에 `Hello Linux` 문자열이 담긴 파일을 생성한다. 파일명은 지시서에 명시되지 않아 `hello_linux.txt`로 가정한다.

```python
#!/usr/bin/env python3
import os

TARGET_DIR = "/test"
TARGET_FILE = os.path.join(TARGET_DIR, "hello_linux.txt")
CONTENT = "Hello Linux"

def create_hello_file():
    try:
        os.makedirs(TARGET_DIR, exist_ok=True)
    except PermissionError:
        print(f"[오류] '{TARGET_DIR}' 디렉토리 생성 권한이 없습니다.")
        print("다음 중 하나를 실행한 뒤 다시 시도하세요:")
        print(f"  1) sudo mkdir -p {TARGET_DIR} && sudo chown $USER:$USER {TARGET_DIR}")
        print(f"  2) sudo python3 1_hello.py")
        raise SystemExit(1)

    with open(TARGET_FILE, "w") as f:
        f.write(CONTENT + "\n")

    print(f"[완료] '{TARGET_FILE}' 파일에 '{CONTENT}' 문자열을 기록했습니다.")

if __name__ == "__main__":
    create_hello_file()
```

### 5.2 예외 없이 동작하게 하는 방법

`/test`는 파일시스템 루트 바로 아래 디렉토리이므로, 일반 사용자 권한으로는 디렉토리 생성 시 `PermissionError`가 발생할 수 있다. 이를 예외 없이 실행하는 방법은 두 가지다.

1. **사전 권한 부여**: `sudo mkdir -p /test && sudo chown $USER:$USER /test` 로 디렉토리를 미리 만들고 소유권을 현재 사용자로 변경한 뒤, `python3 1_hello.py`를 일반 권한으로 실행한다.
2. **관리자 권한 실행**: `sudo python3 1_hello.py` 로 프로그램 자체를 관리자 권한으로 실행한다.

프로그램 내부적으로는 `os.makedirs(..., exist_ok=True)`로 디렉토리가 이미 있어도 오류가 나지 않게 하고, `PermissionError`를 `try/except`로 처리해 원인과 해결 방법을 안내한 뒤 `SystemExit(1)`로 종료하도록 했다.

### 5.3 실행 방법

```bash
cd ~/study/linux
sudo mkdir -p /test && sudo chown $USER:$USER /test   # 최초 1회
python3 1_hello.py
```

### 5.4 실행 결과 확인 방법

```bash
cat /test/hello_linux.txt
# 출력: Hello Linux

ls -l /test
# 출력 예: -rw-r--r-- 1 user user 12 Jul  7 10:00 hello_linux.txt
```

`cat` 명령으로 파일 내용이 정확히 `Hello Linux`인지, `ls -l`로 파일이 정상 생성되었는지 확인한다.

---

## 6. 라인트레이서 운반 로봇과의 연관성

본 실습에서 다룬 리눅스 기초는 이후 로봇 개발에 직접 활용된다.

| 실습 내용                | 로봇 개발 연계                                                                                  |
| ------------------------ | ----------------------------------------------------------------------------------------------- |
| 파일 권한(`chmod`)     | 시리얼 포트(`/dev/ttyUSB0` 등) 접근 권한 부여, 센서/모터 드라이버 실행 권한 설정              |
| `source` / 셸 스크립트 | ROS2 환경변수 적용(`source /opt/ros/humble/setup.bash`), 로봇 부팅 시 자동 실행 스크립트 작성 |
| 패키지 관리(`apt`)     | ROS2, Gazebo 및 각종 드라이버 패키지 설치                                                       |
| 파이썬 파일 입출력       | 라인트레이싱 주행 중 센서 로그·이동 기록을 파일(CSV 등)로 저장하는 로직의 기초                 |
| `sudo`/사용자 권한     | GPIO·하드웨어 제어 시 필요한 권한 관리                                                         |

---

## 7. 합리적 가정 정리

- 우분투 설치 방법: VMWare Workstation 가상머신 + ubuntu 22.04.x
- `/test`에 생성할 파일명: `hello_linux.txt` (지시서에 파일명 미지정)
- 프로그램 실행 환경: 일반 사용자 계정, 필요 시 `sudo`로 디렉토리 소유권 조정
