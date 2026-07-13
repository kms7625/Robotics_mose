
# 누군가는 정보를 만들어내고 — 파이썬 퍼블리셔 작성 (문제8)

---

## 1. 게시(Publish)/구독(Subscribe) 관계

ROS2에서 노드 간 통신은 토픽을 사이에 둔 게시/구독 구조로 이루어진다 (문제7에서 확인).

- **게시자(Publisher)**: 토픽에 메시지를 보내는 쪽. 누가 받는지 몰라도 된다.
- **구독자(Subscriber)**: 토픽에서 메시지를 받는 쪽. 누가 보내는지 몰라도 된다.
- 구독 대상은 상대 노드가 아니라 **토픽**이므로, 게시자를 다른 프로그램으로 교체해도
  구독자는 그대로 동작한다 — 이번 문제가 바로 그 실증이다.

### turtlesim_node ↔ turtle_teleop_key 의 통신 구조

1. `turtle_teleop_key` **노드**가 방향키 입력을 Twist 메시지로 변환해 `/turtle1/cmd_vel`
   **토픽에 게시**한다.
2. `turtlesim_node`는 teleop 노드가 아니라 `/turtle1/cmd_vel` **토픽을 구독**하고 있다가,
   올라온 메시지를 받아 거북이를 움직인다.

이번 문제에서 만든 `circle_turtle` 노드는 이 구조에서 **`turtle_teleop_key`의 자리(게시자)**를
대신한다. 방향키 대신 코드가 명령을 만들어낸다.

## 2. 토픽 유형 — geometry_msgs/msg/Twist 의 개별 값

`ros2 topic info /turtle1/cmd_vel`로 확인한 유형은 `geometry_msgs/msg/Twist`이며, 값 6개로
구성된다.

| 속성          | 의미                                                   | 평면 로봇(거북이·라인트레이서)에서 |
| ------------- | ------------------------------------------------------ | ----------------------------------- |
| `linear.x`  | 전후 직선 속도 (양수 = 전진)                           | **사용** — 전진 속도         |
| `linear.y`  | 좌우 직선 속도 (옆으로 미끄러짐)                       | 바퀴 로봇은 옆으로 못 가므로 0      |
| `linear.z`  | 상하 직선 속도                                         | 드론용, 평면 로봇은 0               |
| `angular.x` | x축 기준 회전 (옆으로 기울기)                          | 0                                   |
| `angular.y` | y축 기준 회전 (앞뒤로 기울기)                          | 0                                   |
| `angular.z` | 바닥에 수직인 축 기준 회전 속도 (양수 = 반시계, rad/s) | **사용** — 회전 속도         |

즉 평면 위를 달리는 로봇은 `linear.x`(전진)와 `angular.z`(회전) 두 값만 쓴다.

### 원을 그리는 원리

- `angular.z`만 주면 제자리 회전, `linear.x`만 주면 직진.
- **둘을 동시에** 주면 전진하면서 계속 꺾으므로 원이 그려진다 — 핸들을 꺾은 채 액셀을 밟는
  것과 같다.
- 원의 반지름은 두 값의 비율로 정해진다 (Chapter1 문제6 차동 구동의 $v = r\omega$ 관계):

$$
r = \frac{linear.x}{angular.z}
$$

## 3. 파이썬 퍼블리셔 작성 방법

문제6의 타이머 노드 구조에 다음 세 조각을 추가하면 된다.

```python
from geometry_msgs.msg import Twist                              # ① 메시지 클래스 import

self.publisher = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)   # ② 게시자 생성

msg = Twist()                        # ③ 빈 메시지 생성 (모든 값 0.0)
msg.linear.x = 2.0
msg.angular.z = 1.0
self.publisher.publish(msg)          #    게시
```

- `create_publisher(메시지유형, '토픽이름', 큐크기)` — 토픽 이름은 teleop이 쓰던
  `/turtle1/cmd_vel`과 **정확히 같아야** turtlesim_node가 받는다 (토픽은 이름으로 만난다).
  큐 크기 10은 구독자가 못 받은 메시지를 쌓아두는 개수.
- 게시를 한 번만 하면 거북이는 잠깐 움직이다 만다. **타이머(문제6)로 일정 간격마다 반복
  게시**해야 계속 원을 그린다.

## 4. 완성된 circle_turtle.py

```python
import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist

class circle_turtle(Node):
  def __init__(self):
    super().__init__('circle_turtle')
    self.publisher = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)
    self.timer     = self.create_timer(0.1, self.timer_callback)

  def timer_callback(self):
    msg = Twist()
    msg.linear.x  = 2.0
    msg.angular.z = 1.0
    self.publisher.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = circle_turtle()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

작성 경로: `~/ros2_ws/src/my_robot_controller/my_robot_controller/circle_turtle.py`

- 타이머 간격 0.1초: 부드러운 원을 위해 짧은 간격으로 반복 게시
- `linear.x = 2.0, angular.z = 1.0`: 반지름 2.0의 원

### 속성값 변경 실험

`angular.z`를 1.0 → 2.0으로 올리면 반지름이 $2.0/2.0 = 1.0$으로 줄어들 것으로 예측했고,
실행 결과 **실제로 원이 작아졌다**. 같은 전진 속도로 더 빨리 꺾으니 더 작은 원을 도는 것이다.
반대로 `linear.x`를 올리면(각속도 고정) 원이 커진다.

실험 결과 화면: `turtlesim_circles.png` — 값을 바꿔가며 실행해 크기가 다른 원들이 겹쳐
그려진 모습. 큰 원을 돌 때는 화면 경계에 닿아 turtlesim이 `Oh no! I hit the wall!` 경고를
출력하며 이동을 제한(clamping)하는 것도 확인했다.

## 5. package.xml 의존성 추가

```xml
<depend>geometry_msgs</depend>
<depend>turtlesim</depend>
```

**의존성을 추가한다는 것의 의미**: `package.xml`은 패키지의 신분증 같은 파일이고,
`<depend>`는 "이 패키지가 동작하려면 이 패키지들이 필요하다"는 **선언**이다. 이렇게 명시해두면
다른 사람(또는 배포 도구)이 이 패키지를 받아 빌드할 때 필요한 패키지의 존재를 자동으로
확인·설치할 수 있다.

**두 의존성을 추가하는 이유**: 코드가 `geometry_msgs`의 Twist 클래스를 import하고, 게시 대상인
`/turtle1/cmd_vel` 토픽은 `turtlesim` 패키지의 노드가 구독하므로, 이 패키지는 두 패키지에
의존한다.

## 6. 빌드와 실행

### 6.1 entry_points 등록

```python
entry_points={
    'console_scripts': ['logging_node  = my_robot_controller.logging:main',
                        'timer_node    = my_robot_controller.timer_test:main',
                        'circle_turtle = my_robot_controller.circle_turtle:main'
    ],
},
```

### 6.2 빌드 및 실행

```bash
cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

- 터미널 1: `ros2 run turtlesim turtlesim_node` (전역 패키지이므로 워크스페이스 source 불필요)
- 터미널 2: `source ~/ros2_ws/install/setup.bash` 후 `ros2 run my_robot_controller circle_turtle`

**실행 결과: 거북이가 원을 그리며 계속 움직인다.** 우리가 만든 게시자 노드가 teleop을 대신해
거북이를 조종하는 것이다.

## 7. rqt_graph 확인

두 노드가 실행 중인 상태에서 `rqt_graph`(Nodes/Topics (active) 모드)로 확인한 구조:

```
[/circle_turtle] ──→ [/turtle1/cmd_vel] ──→ [/turtlesim]
```

- 문제7의 talker→/chatter→listener와 같은 구조에서, 게시자 자리에 우리가 만든 노드가 들어갔다.
- 그래프에서 `/turtle1/cmd_vel` 사각형을 감싸는 큰 사각형 `/turtle1`이 보이는데, 이는 별도의
  토픽이 아니라 **네임스페이스 틀**이다 — `/turtle1/`로 시작하는 토픽들을 rqt_graph가 묶어
  표시하는 방식이다.
- 참고로 `turtlesim_node`는 `/turtle1/cmd_vel`의 구독자이면서 동시에 `/turtle1/pose`(현재
  위치·방향), `/turtle1/color_sensor`(밟고 있는 바닥 색) 등의 **게시자**이기도 하다. 이
  토픽들은 현재 구독자가 없어 rqt_graph 기본 필터(dead sink 숨김)에 걸러져 보이지 않는다.
  하나의 노드가 토픽에 따라 게시자와 구독자 역할을 겸할 수 있다 — 실제 로봇도 모터 노드가
  속도 명령을 구독하면서 엔코더로 잰 실제 속도를 게시하는 식으로 동작한다.

저장 이미지: `rqt_graph_circle_turtle.png`

## 8. 시행착오

1. **상속 대상 혼동** — `class circle_turtle(Twist):`로 시작했다. Twist는 보낼 데이터(메시지)의
   형태일 뿐이고, 노드가 되려면 `Node`를 상속해야 한다.
2. **메서드 정의에 `self.` 사용** — `def self.publisher(self):`는 문법 오류. `self.`은 정의가
   아니라 접근할 때 붙인다. 또한 `self.publisher`(게시자 객체)와 같은 이름을 메서드에 쓰면
   충돌하므로 콜백은 별도 이름(`timer_callback`)으로 지었다.
3. **타이머 누락** — 게시 코드만 있고 `create_timer`가 없으면 콜백을 아무도 호출하지 않는다.
4. **entry_points의 모듈 경로 오류** — `my_robot_controller.package.sml:main`으로 등록해
   `ModuleNotFoundError: No module named 'my_robot_controller.package'`가 났다. 형식은
   `패키지이름.파일이름:함수이름`이며, 파일이름 자리에는 코드가 든 `.py` 파일 이름(확장자
   제외)이 들어가야 한다 (`my_robot_controller.circle_turtle:main`).
5. **setup.py 수정 후 재빌드 누락** — 수정 후에도 동일한 에러가 났다. `.py` 코드는
   `--symlink-install` 덕에 저장만 하면 반영되지만, **setup.py 수정은 재빌드가 필요**하다.
6. **새 터미널에서 워크스페이스 source 누락** — `Package 'my_robot_controller' not found`.
   전역 ROS2는 `.bashrc`로 자동이지만 워크스페이스는 터미널마다 `source ~/ros2_ws/install/setup.bash`가 필요하다.
7. 경로 오타 (`row2_ws`, `rosw_ws`, `my_robot_controlle`) — `nano`는 없는 경로를 열면 에러
   없이 빈 새 파일을 보여주므로 오타를 눈치채기 어렵다. **Tab 자동완성**을 쓰면 오타가 원천
   차단되고, 자동완성이 안 되는 지점이 곧 오타 위치다.

## 9. 라인트레이서 운반 로봇과의 연결

이번에 만든 구조가 라인트레이서의 핵심 골격이다. `circle_turtle`은 고정된 Twist를 게시했지만,
라인트레이서의 제어 노드는 IR 센서 값에 따라 `linear.x`(전진)와 `angular.z`(조향)를 매번 계산해
게시하게 된다. 즉 "타이머로 주기 실행 + Twist 게시"라는 이번 패턴에서 값 계산 부분만 센서
기반으로 바뀌는 것이다.

## 10. 제출물

- 본 문서: `8_publisher.md`
- rqt_graph 이미지: `rqt_graph_circle_turtle.png`
- 워크스페이스 `src` 압축: `my_robot_ws_src.tar.gz` (`~/ros2_ws`에서 `tar -czvf my_robot_ws_src.tar.gz src`로 생성)

**가정**: 지시서에 "적당한 크기의 원", "적당한 속도/간격"으로만 명시돼 있어, 타이머 0.1초,
`linear.x = 2.0`, `angular.z = 1.0`(반지름 2.0)을 기준값으로 정했다. 속성 변경 실험은
`angular.z`(1.0→2.0)와 `linear.x` 조정으로 수행했다.
