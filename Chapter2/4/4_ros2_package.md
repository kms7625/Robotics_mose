# 가상 로봇의 틀을 잡아보자 — ROS2 패키지 및 파이썬 빌드 시스템 (문제4)

---

## 1. 워크스페이스(Workspace)란

지금까지는 이미 만들어진 패키지(`demo_nodes_cpp`, `turtlesim`)를 실행만 해봤다. 직접 패키지를
만들려면, ROS2가 정한 폴더 구조 규칙을 따라야 하는데 이 전체 폴더를 **워크스페이스**라 부른다.

핵심 규칙: 워크스페이스 폴더(`~/ros2_ws`) 안에 **`src`** 라는 폴더를 만들고, 내가 만드는 모든
패키지는 그 `src` 안에 둔다.

```bash
mkdir -p ~/ros2_ws/src
```

## 2. `colcon` 빌드 도구

실제 로봇 프로젝트는 패키지가 수십 개(센서 노드, 제어 노드, 모터 구동 노드 등)에 달할 수 있다.
이 여러 패키지를 한 번에 빌드해주는 도구가 **`colcon`**이다. `src` 폴더 안을 스캔해서 어떤
패키지가 있는지 파악한 뒤, 각각을 빌드해 워크스페이스 최상위에 `build`, `install`, `log` 결과
폴더를 만든다.

### 2.1 설치 시행착오

`colcon`은 ROS2 전용 도구가 아니라 범용 빌드 도구라서, `ros-humble-desktop`을 설치해도 자동으로
같이 설치되지 않는다. 별도 설치가 필요하다.

```bash
cd ~/ros2_ws
colcon build
```

```
colcon: command not found
```

진단 순서:

1. `echo $ROS_DISTRO` → `humble` 출력됨 → ROS2 환경 자체(`~/.bashrc`의 `source` 설정)는
   정상이므로 환경설정 누락이 원인이 아님을 확인.
2. `which colcon` → 아무 결과도 없음 → `colcon` 실행 파일 자체가 시스템에 없다는 뜻.
3. 별도 패키지로 설치:

```bash
sudo apt install -y python3-colcon-common-extensions
```

설치 후 재확인:

```bash
which colcon
```
```
/usr/bin/colcon
```

```bash
colcon build
```
```
Summary: 0 packages finished [0.19s]
```

"0 packages"인 이유는 아직 `src` 폴더가 비어 있어 빌드할 패키지가 없었기 때문이다.

## 3. `ros2 pkg create`로 패키지 생성

### 3.1 개념

- **빌드 시스템**: ROS2 패키지는 C++(`ament_cmake`) 또는 Python(`ament_python`)으로 만들 수
  있다. 이번엔 Python으로 만들 것이므로 `ament_python`을 지정한다.
- **`rclpy`**: "ROS Client Library for Python"의 줄임말. Python 코드에서 노드를 만들고
  publish/subscribe 등 ROS2 기능을 사용할 수 있게 해주는 파이썬 라이브러리다. 문제2에서 실행한
  `demo_nodes_cpp`가 C++ 기반이라면, 앞으로 만들 패키지는 Python 기반이고 그 핵심 의존성이
  `rclpy`다.

### 3.2 명령 문법 시행착오

```bash
ros2 pkg create --build-type ament_python --dependencies rclpy my_robot_controller
```
```
ros2 pkg create: error: the following arguments are required: package_name
```

`--dependencies`는 여러 개의 값을 받을 수 있는 옵션이라, 뒤에 오는 `my_robot_controller`까지
의존성 이름으로 인식해버려 정작 패키지 이름(위치 인자)이 비었다. **패키지 이름을 옵션들보다
앞에 두면** 해결된다.

```bash
cd ~/ros2_ws/src
ros2 pkg create my_robot_controller --build-type ament_python --dependencies rclpy
```

정상적으로 `my_robot_controller` 패키지가 생성되었다.

## 4. `tree`로 패키지 구조 확인

```bash
sudo apt install -y tree
cd ~/ros2_ws
tree
```

```
.
├── build
│   └── COLCON_IGNORE
├── install
│   ├── COLCON_IGNORE
│   ├── local_setup.bash
│   ├── local_setup.ps1
│   ├── local_setup.sh
│   ├── _local_setup_util_ps1.py
│   ├── _local_setup_util_sh.py
│   ├── local_setup.zsh
│   ├── setup.bash
│   ├── setup.ps1
│   ├── setup.sh
│   └── setup.zsh
├── log
│   ├── build_2026-07-09_07-03-52
│   │   ├── events.log
│   │   └── logger_all.log
│   ├── COLCON_IGNORE
│   ├── latest -> latest_build
│   └── latest_build -> build_2026-07-09_07-03-52
└── src
    └── my_robot_controller
        ├── my_robot_controller
        │   └── __init__.py
        ├── package.xml
        ├── resource
        │   └── my_robot_controller
        ├── setup.cfg
        ├── setup.py
        └── test
            ├── test_copyright.py
            ├── test_flake8.py
            └── test_pep257.py

11 directories, 23 files
```

`build`/`install`/`log`는 `colcon build`가 만든 결과물 폴더이고, `src/my_robot_controller`가
실제로 작성한 패키지 내용이다.

## 5. `package.xml`과 `setup.py`의 역할

### 5.1 `package.xml`

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <name>my_robot_controller</name>
  <version>0.0.0</version>
  <description>TODO: Package description</description>
  <maintainer email="kangmose@todo.todo">kangmose</maintainer>
  <license>TODO: License declaration</license>

  <depend>rclpy</depend>

  <test_depend>ament_copyright</test_depend>
  <test_depend>ament_flake8</test_depend>
  <test_depend>ament_pep257</test_depend>
  <test_depend>python3-pytest</test_depend>

  <export>
    <build_type>ament_python</build_type>
  </export>
</package>
```

패키지의 메타데이터 파일이다. 이름, 버전, 설명과 함께 **어떤 패키지에 의존하는지**
(`<depend>rclpy</depend>`)를 선언한다. `colcon`이 여러 패키지를 빌드할 때 "이 패키지를 빌드하려면
어떤 패키지가 먼저 필요한지" 파악하는 데 이 파일을 사용한다. XML 형식이며 언어(Python/C++)와
무관하게 모든 ROS2 패키지에 공통으로 존재한다.

### 5.2 `setup.py`

```python
from setuptools import find_packages, setup

package_name = 'my_robot_controller'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='kangmose',
    maintainer_email='kangmose@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
        ],
    },
)
```

Python 표준 도구 `setuptools`를 이용해 패키지를 실제로 설치 가능한 형태로 빌드하는 스크립트다.
특히 `entry_points` → `console_scripts`가 중요한데, 앞으로 노드 코드를 작성하면 여기 등록해야
`ros2 run my_robot_controller <노드이름>`으로 실행할 수 있다. 현재는 비어 있다 — 아직 실제 노드
코드를 작성하지 않았기 때문이다.

### 5.3 `rclpy`가 두 파일에 다르게 나타나는 이유

`rclpy`는 `package.xml`의 `<depend>`에는 있지만, `setup.py`의 `install_requires`(`['setuptools']`만
있음)에는 없다. `rclpy`는 일반 PyPI 패키지(`pip install`로 받는 `requests`, `numpy` 같은 것)가
아니라 **ROS2 자체의 배포 시스템**(apt로 설치되는 `ros-humble-*` 패키지군)에 속한 라이브러리이기
때문이다. `setup.py`의 `install_requires`는 순수 Python 패키징 차원의 의존성만 다루고, ROS2
생태계 차원의 의존성은 `package.xml`을 통해 ROS2의 의존성 해석 도구(`rosdep`)가 처리한다.

## 6. 명령/개념 정리

| 항목 | 정리 |
|------|------|
| `colcon` | `src` 폴더를 스캔해 여러 패키지를 한 번에 빌드하는 도구. ROS2 전용이 아니라 별도 설치 필요 |
| `ament_python` | Python으로 ROS2 패키지를 만들 때 쓰는 빌드 시스템 (C++는 `ament_cmake`) |
| `ros2 pkg create` | 새 패키지의 기본 폴더/파일 구조를 생성하는 명령. 위치 인자(패키지 이름)는 다중값 옵션(`--dependencies` 등)보다 앞에 두어야 함 |
| `rclpy` | ROS Client Library for Python. Python 코드에서 ROS2 노드·통신 기능을 사용하게 해주는 라이브러리 |
| `package.xml` | 패키지 메타데이터 + ROS2 차원 의존성 선언 (모든 패키지 공통) |
| `setup.py` | Python 패키지 설치 스크립트. `entry_points`에 노드를 등록해야 `ros2 run`으로 실행 가능 |

## 7. 제출물

- `src` 디렉토리 압축 파일: `my_robot_ws_src.tar.gz` (`~/ros2_ws`에서 `tar -czf my_robot_ws_src.tar.gz src`로 생성)

**가정**: 지시서에 명시되지 않은 세부 사항 중, `ros2 pkg create`의 `--license`, `--maintainer-email`
등 부가 옵션은 지정하지 않고 기본값(TODO 표시)을 그대로 두었다. 실제 제출/공유 전 라이선스나
메인테이너 정보를 채우는 것이 정석이지만, 이번 실습 단계에서는 패키지 구조 이해가 목적이므로
생략했다.
