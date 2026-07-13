# 문제12 — Launch File: 로봇을 명령 하나로 시동하기

## 1. Launch File이란

문제11까지는 노드를 하나 실행할 때마다 터미널을 열고 `source` 하고 `ros2 run`을
쳤다. 노드 두 개짜리 시스템인데도 터미널 세 개가 필요했다. 실제 로봇은 센서,
모터, 제어, 로깅 등 노드가 수십 개라서 이 방식으로는 시동 자체가 일이 된다.

**Launch File은 "이 노드들을 이렇게 켜라"는 시동 절차서**다. 한 번의 명령으로
여러 노드를 동시에 실행한다:

```bash
ros2 launch <패키지이름> <런치파일이름>
```

ROS2에서 런치파일은 파이썬으로 작성한다.

## 2. 파이썬 런치파일 작성

런치파일은 노드 코드와 성격이 달라 패키지 안에 `launch/` 디렉토리를 따로 만들어
보관하는 것이 관례다.

```bash
mkdir ~/ros2_ws/src/my_robot_controller/launch
nano ~/ros2_ws/src/my_robot_controller/launch/robot.launch.py
```

`robot.launch.py`:

```python
from launch import LaunchDescription      # 런치 설계도 클래스
from launch_ros.actions import Node       # "노드를 실행하라"는 액션


def generate_launch_description():        # ros2 launch가 찾는 약속된 함수 이름
    return LaunchDescription([
        Node(
            package='turtlesim',               # 패키지 이름
            executable='turtlesim_node',       # 실행 이름
        ),
        Node(
            package='my_robot_controller',
            executable='turtle_move_control',  # 문제11의 제어 노드
        ),
    ])
```

- `generate_launch_description()`은 **약속된 이름**이다. `ros2 launch`가 이
  이름의 함수를 찾아 호출한다.
- `Node(package=..., executable=...)` 하나는 손으로 치던
  `ros2 run <package> <executable>` 명령 하나와 같다. 런치파일은 그 명령들을
  목록으로 묶은 것이다.

## 3. setup.py 수정 — data_files 등록

런치파일만 만들고 빌드하면 `ros2 launch`에서 다음 에러가 난다 (실제 겪은 것):

```
file 'robot.launch.py' was not found in the share directory of package
'my_robot_controller' which is at '.../install/my_robot_controller/share/my_robot_controller'
```

원인: `ros2 launch`는 `src`의 원본이 아니라 **빌드가 `install/`의 share
디렉토리로 복사한 사본**을 읽는데, colcon은 `setup.py`에 등록된 것만 복사한다.
새로 만든 `launch/` 디렉토리는 등록해줘야 한다.

`setup.py`에는 성격이 다른 등록 항목이 두 개 있다:

| 항목             | 용도                                             | 예                 |
| ---------------- | ------------------------------------------------ | ------------------ |
| `entry_points` | **실행 프로그램** 등록 (`ros2 run` 대상) | 파이썬 노드        |
| `data_files`   | install의 share로**복사할 파일** 목록      | 런치파일, 설정파일 |

런치파일은 실행 프로그램이 아니라 `ros2 launch`가 읽는 자료이므로
`data_files`에 등록한다:

```python
import os                    # 파일 맨 위에 추가
from glob import glob        # 파일 맨 위에 추가

    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # 추가: launch/의 *.launch.py를 share/<패키지>/launch로 복사
        (os.path.join('share', package_name, 'launch'),
            glob(os.path.join('launch', '*.launch.py'))),
    ],
```

`glob('launch/*.launch.py')`는 launch 디렉토리의 런치파일 전부를 찾으므로,
나중에 런치파일이 늘어나도 자동으로 포함된다.

수정 후 재빌드해야 반영된다:

```bash
cd ~/ros2_ws        # 반드시 워크스페이스 최상위에서 (홈에서 빌드하면 홈에 build/가 생긴다)
colcon build
source ~/ros2_ws/install/setup.bash
```

## 4. 실행 결과

```
$ ros2 launch my_robot_controller robot.launch.py
[INFO] [launch]: All log files can be found below /home/kangmose/.ros/log/...
[INFO] [launch]: Default logging verbosity is set to INFO
[INFO] [turtlesim_node-1]: process started with pid [3520]
[INFO] [turtle_move_control-2]: process started with pid [3522]
[turtlesim_node-1] [INFO] [...] [turtlesim]: Starting turtlesim with node name /turtlesim
[turtlesim_node-1] [INFO] [...] [turtlesim]: Spawning turtle [turtle1] at x=[5.544445], y=[5.544445], theta=[0.000000]
```

- 명령 하나로 두 노드가 동시에 시작됐고(`process started` 두 줄), turtlesim
  창이 뜨면서 거북이가 곧바로 벽 회피 주행을 시작했다.
- 여러 노드의 출력이 한 터미널에 섞이므로 런치가 `[turtlesim_node-1]`,
  `[turtle_move_control-2]` 같은 노드별 이름표를 붙여준다.

### 추가 실험: 런치 실행 중 /quit 호출

런치가 돌아가는 상태에서 다른 터미널에서 문제11의 `/quit` 서비스를 호출했다:

```
$ ros2 service call /quit std_srvs/srv/Empty "{}"
```

런치 터미널의 기록:

```
[turtle_move_control-2] [INFO] [...] [turtle_move_control]: quit 요청 받음!
[turtle_move_control-2] [INFO] [...] [turtle_move_control]: 거북이 제거 완료, 종료합니다
[INFO] [turtle_move_control-2]: process has finished cleanly [pid 3522]
```

- 런치 시스템이 노드의 종료를 감시하고 있다가 **`process has finished cleanly`**
  라고 기록했다 — 문제11에서 try/except로 구현한 "처리되지 않은 예외 없는
  정상 종료"를 런치 시스템이 확인해준 것이다. 예외로 죽었다면
  `process has died [exit code 1]`이 찍힌다.
- 제어 노드만 종료되고 turtlesim은 계속 실행 중이었다(거북이는 `/kill`로
  제거되어 빈 화면). 런치로 함께 시작한 노드들도 각자 독립적으로 살고 죽는다.

## 5. 실습 중 겪은 문제와 배운 점

| 문제                                     | 원인                                                         | 배운 점                                                                                        |
| ---------------------------------------- | ------------------------------------------------------------ | ---------------------------------------------------------------------------------------------- |
| `was not found in the share directory` | 런치파일을`setup.py`의 `data_files`에 등록하지 않고 빌드 | 새 자료(런치파일 등)는`data_files` 등록 + 재빌드가 필요하다                                  |
| 런치파일을`entry_points`에 등록하려 함 | 등록 위치 혼동                                               | `entry_points`=실행 프로그램(`ros2 run` 대상), `data_files`=복사할 자료. 런치파일은 후자 |
| 홈 디렉토리에서`colcon build` 실행     | 빌드 위치 미확인                                             | 빌드 전 프롬프트가`~/ros2_ws`인지 확인하는 습관                                              |

## 6. 산출물

| 파일                   | 내용                                                                                             |
| ---------------------- | ------------------------------------------------------------------------------------------------ |
| `12_launch.md`       | 본 문서                                                                                          |
| `my_robot_ws.tar.gz` | 워크스페이스 소스 (`ros2_ws/src`) 압축 — `launch/robot.launch.py`, 수정된 `setup.py` 포함 |
