# 가상 로봇의 구성 요소를 생성한다 — Python 노드 작성 (문제5)

---

## 1. `rclpy.node.Node`를 상속받아 노드 클래스 작성하기

ROS2의 모든 노드는 `rclpy.node` 모듈의 **`Node` 클래스를 상속**받아 정의한다. `Node`는 ROS2가
미리 만들어둔 노드의 기본 뼈대(로그 남기기 등 공통 기능이 이미 구현돼 있음)이고, 우리는 이를
상속받아 원하는 동작을 추가한 자식 클래스를 만든다.

```python
class LoggingNode(Node):
    def __init__(self):
        super().__init__('logging_node')
```

- `class LoggingNode(Node):` — `Node`(부모)를 상속받아 `LoggingNode`(자식) 클래스를 정의한다.
- `super().__init__('logging_node')` — 부모 클래스의 초기화 함수를 호출하면서 **이 노드의 이름**을
  `'logging_node'`로 지정한다. 이 이름이 `ros2 node list` 등에서 보이는 이름이 된다.

## 2. 노드 객체 생성

클래스는 틀일 뿐이고, 실제로 동작하려면 그 틀로 **객체(인스턴스)**를 만들어야 한다.

```python
node = LoggingNode()
```

이 한 줄로 `__init__`이 실행되며 실제 노드 객체가 생성된다.

## 3. `rclpy.init()` / `rclpy.spin()` / `rclpy.shutdown()`

| 함수                 | 역할                                           |
| -------------------- | ---------------------------------------------- |
| `rclpy.init()`     | ROS2 통신 시스템을 초기화한다                  |
| `rclpy.spin(node)` | 해당 노드를 계속 실행 상태로 유지하며 대기한다 |
| `rclpy.shutdown()` | ROS2 통신 시스템을 정리하고 종료한다           |

`rclpy.spin(node)`가 없으면 프로그램은 초기화만 하고 바로 끝나버린다 — 지시서가 요구하는
"로봇이 계속 동작하듯 프로그램이 계속 실행 상태로 남아 있는" 동작이 바로 이 함수로 구현된다.

## 4. 로그 남기기와 확인하기

### 4.1 로그 남기기

일반 파이썬은 `print()`를 쓰지만, 화면이 없는 로봇 환경에서는 `Node`가 제공하는 로깅 메서드를
사용한다.

```python
self.get_logger().info(self.get_name())
```

- `self.get_logger()` — 이 노드 전용 로거 객체를 가져온다.
- `.info(...)` — **정보(info) 수준**으로 로그를 남긴다 (수준: debug < info < warn < error < fatal).
- `self.get_name()` — 이 노드 자신의 이름을 동적으로 가져온다. 이름을 하드코딩하지 않아도 된다.

### 4.2 로그 확인하기

`ros2 run`으로 노드를 실행하면 터미널에 로그가 바로 출력된다. 그 외에도 ROS2는 모든 로그를
파일로 남기며, 아래 경로에서 세션이 끝난 뒤에도 확인할 수 있다.

```bash
ls ~/.ros/log/
```

## 5. 완성된 `logging.py`

```python
import rclpy
from rclpy.node import Node

class logging_node(Node):
    def __init__(self):
        super().__init__('logging_node')
        self.get_logger().info(self.get_name())

def main(args=None):
    rclpy.init(args=args)
    node = logging_node()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
   main()
```

작성 경로: `~/ros2_ws/src/my_robot_controller/my_robot_controller/logging.py`

**시행착오**: 처음엔 클래스 정의 이름(`logging_node`)과 `main()`에서 객체를 생성할 때 쓴 이름
(`LoggingNode`, `Logging_Node`)이 서로 달라 실행 시 `NameError`가 날 뻔했다. 파이썬은 대소문자와
철자가 정확히 일치해야 같은 클래스로 인식하므로, 클래스 정의와 사용 지점의 이름을 동일하게
맞췄다.

## 6. 노드를 실행 가능하게 만들기 — `setup.py` 수정

### 6.1 개념

`setup.py`의 `entry_points` → `console_scripts`에 등록해야 `ros2 run`으로 실행할 수 있는 명령이
된다. 문법은 다음과 같다.

```
'실행할_때_쓸_이름 = 패키지이름.파일이름:함수이름'
```

### 6.2 적용

```python
entry_points={
    'console_scripts': [
        'logging_node = my_robot_controller.logging:main'
    ],
},
```

- `logging_node` — 실행 이름 (지시서가 요구한 이름)
- `my_robot_controller.logging` — `my_robot_controller` 패키지 안의 `logging.py` 파일
  (`.py` 확장자는 생략)
- `main` — 실행될 함수

## 7. `--symlink-install` 옵션

### 7.1 역할

기본 `colcon build`는 `src`의 파이썬 파일을 `install` 폴더로 **복사**한다. 그러면 `src`의
코드를 수정해도 실제 실행되는 복사본에는 반영되지 않아, 수정할 때마다 다시 빌드해야 한다.

`--symlink-install`은 복사 대신 **심볼릭 링크**(원본을 가리키는 바로가기)를 만든다. 원본
(`src`)을 고치면 그걸 가리키는 `install`도 즉시 최신 상태가 되므로, 다시 빌드할 필요가 없다.
개발 중 코드를 자주 수정하는 상황에 특히 유리하다.

### 7.2 빌드

```bash
cd ~/ros2_ws
colcon build --symlink-install
```

```
Starting >>> my_robot_controller
Finished <<< my_robot_controller [0.66s]

Summary: 1 package finished [0.79s]
```

이번 실습 환경에서는 `setuptools` 버전 문제(참고사항에 명시된 `pip3 install setuptools==58.2.0`
필요 상황)를 겪지 않고 바로 빌드에 성공했다.

## 8. 빌드 결과 적용 후 노드 실행

### 8.1 개념

문제2에서 `source /opt/ros/humble/setup.bash`로 **ROS2 본체**(talker, listener, turtlesim 등
기본 제공 패키지)를 활성화했다. 이번에 만든 `my_robot_controller`는 별도 워크스페이스
(`~/ros2_ws`)의 패키지이므로, ROS2 본체 source만으로는 부족하다. `colcon build`가 만든
`~/ros2_ws/install` 안의 `setup.bash`도 추가로 source해야 `ros2 run`이 이 패키지를 찾을 수 있다.

```bash
source ~/ros2_ws/install/setup.bash
```

### 8.2 실행 결과

```bash
ros2 run my_robot_controller logging_node
```

```
[INFO] [1783586639.978298265] [logging_node]: logging_node
```

노드 이름(`logging_node`)이 정보 수준 로그로 정확히 기록됨을 확인했다. `self.get_name()`으로
가져온 이름이 `super().__init__('logging_node')`에서 지정한 이름과 일치한다.

Ctrl+C로 종료하면 `KeyboardInterrupt` 트레이스백이 출력되는데, 이는 에러가 아니라 `spin()`
도중 강제 종료했을 때 파이썬이 보여주는 기본 동작이다. `demo_nodes_cpp`의 talker/listener는
Ctrl+C를 우아하게 처리하는 코드가 포함돼 있어 깔끔한 메시지만 나왔던 것이고, 직접 작성한 노드는
그런 예외 처리를 별도로 추가하지 않았을 뿐이다.

## 9. 제출물

- 워크스페이스 전체 압축 파일: `my_robot_ws.tar.gz` (`~`에서 `tar -czf my_robot_ws.tar.gz ros2_ws`로 생성)

**가정**: 지시서에 명시되지 않은 세부 사항 중, Ctrl+C 종료 시 발생하는 `KeyboardInterrupt`
예외를 코드에서 잡아 깔끔하게 종료하는 처리는 이번 실습 범위에서는 생략했다 (지시서가 요구한
범위는 "계속 실행 상태로 남아 있는 것"까지이며, 예외 처리 자체는 다음 문제 이후의 심화 주제로
판단).
