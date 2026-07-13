#!/usr/bin/env python3
"""~/study/linux 디렉토리에서 실행: /test 디렉토리에 'Hello Linux' 문자열 파일을 생성한다."""

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
