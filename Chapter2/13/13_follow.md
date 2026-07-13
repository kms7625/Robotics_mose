# 문제13 — 종합 프로젝트: 거북이 추적 프로그램 (turtle_follow)

## 1. 목표와 설계

launch로 turtlesim과 제어 노드를 실행하면, 제어 노드가 `/spawn`으로 임의 위치에
두 번째 거북이(turtle2)를 만들고, 먼저 있던 거북이(turtle1)가 자연스러운 곡선
궤적으로 turtle2를 추적한다. 만나면 이동하던 turtle1을 지우고 종료하며,
`/quit` 서비스가 호출되면 두 거북이 모두 지우고 종료한다.

새로운 개념은 거의 없고, 문제8~12에서 배운 도구를 전부 조립하는 문제다:

| 요구사항 | 사용한 도구 | 배운 문제 |
|---|---|---|
| launch로 두 노드 실행 | 런치파일 + `data_files` | 문제12 |
| `/spawn`으로 거북이 추가 | 서비스 클라이언트 + `call_async` | 문제11 |
| 목표를 향해 이동 | pose 구독 + cmd_vel 발행 (폐쇄 루프) | 문제10 |
| 만나면 지우고 종료 | `/kill` 클라이언트 + `SystemExit` | 문제11 |
| `/quit` 처리 | 서비스 서버 | 문제11 |

## 2. /spawn 서비스 정찰 (명령행 4단계 절차)

구현 전에 처음 쓰는 `/spawn`의 요청/응답 구조를 명령행으로 조사했다:

```
$ ros2 service type /spawn
turtlesim/srv/Spawn

$ ros2 interface show turtlesim/srv/Spawn
float32 x
float32 y
float32 theta
string name # Optional.  A unique name will be created and returned if this is empty
---
string name

$ ros2 service call /spawn turtlesim/srv/Spawn "{name: 'turtle2',  x: 5, y: 6}"
requester: making request: turtlesim.srv.Spawn_Request(x=5.0, y=6.0, theta=0.0, name='turtle2')

response:
turtlesim.srv.Spawn_Response(name='turtle2')
```

- 요청: 위치(x, y), 방향(theta, 라디안), 이름(비우면 자동 생성)
- **응답이 이름을 돌려주는 이유**: 이름을 비워 자동 생성됐을 때, 그 이름을 알아야
  새 거북이의 토픽(`/turtle2/cmd_vel` 등)에 접근할 수 있기 때문이다.
- 요청 데이터(YAML)는 **콜론 뒤에 공백 필수** — `{x:5}`는 `x:5` 전체를 필드
  이름으로 해석해 에러가 난다. `{x: 5}`로 써야 한다.

## 3. 추적의 수학 — atan2와 P 제어

turtle1이 turtle2를 향해 가려면 매 pose 갱신마다:

1. **목표 방향각**: 두 위치의 차이 벡터가 가리키는 각도

   ```
   dx = 목표x − 내x,  dy = 목표y − 내y
   target_angle = atan2(dy, dx)      # 라디안
   ```

2. **방향 오차에 비례한 회전** (P 제어 — 과정1 문제7의 그 원리):

   ```
   error = target_angle − 내 theta
   angular.z = 3.0 × error           # 오차 크면 빨리, 작으면 살살 회전
   linear.x  = 1.5                   # 일정 속도 전진
   ```

3. **오차 각도 보정**: 각도는 한 바퀴 돌면 제자리이므로, 보정 없이는 "오른쪽
   10°"를 "왼쪽 350°"로 계산할 수 있다. while 루프로 오차를 −π~+π 범위로
   접어서 항상 가까운 쪽으로 돌게 한다.

전진과 회전을 동시에 주기 때문에 결과 궤적이 꺾이지 않는 자연스러운 곡선이
된다 (지시서 3번). 라인트레이서가 선 중심과의 오차에 비례해 조향하는 것과
같은 구조다.

## 4. 종료 설계 — 판정 플래그와 사슬 호출

- **판정 플래그(`self.finished`)**: pose는 초당 수십 번 들어오므로, 만남을
  감지한 뒤에도 `follow()`가 계속 호출된다. 플래그 없이는 이미 사라진 거북이에
  kill을 반복 주문하게 된다. 한 번 판정되면 이후 호출은 즉시 return한다.
- **만남 판정**: 두 거북이 거리(`sqrt(dx²+dy²)`)가 0.5 미만이면 "만남"으로
  판정하고 turtle1(이동 로봇)을 `/kill` → 완료 콜백에서 `SystemExit`.
- **/quit의 사슬 호출**: 둘 다 지워야 하므로 "turtle1 kill → 완료되면 turtle2
  kill → 완료되면 SystemExit"으로 done 콜백을 사슬처럼 연결했다. 모든 호출은
  `call_async`라 처리 중에도 노드는 멈추지 않는다 (문제11의 데드락 회피).

## 5. 구현 코드

### turtle_follow.py

```python
import random                              # 임의 위치를 위한 표준 라이브러리
import rclpy
import math
from rclpy.node import Node
from turtlesim.srv import Spawn
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose
from std_srvs.srv import Empty
from turtlesim.srv import Kill


class TurtleFollow(Node):
    def __init__(self):
        super().__init__('turtle_follow')
        self.spawn_client = self.create_client(Spawn, '/spawn')

        req = Spawn.Request()
        req.x = random.uniform(1.0, 10.0)      # 1~10 사이 임의 실수 (벽에서 안전한 범위)
        req.y = random.uniform(1.0, 10.0)
        req.theta = random.uniform(0.0, 6.28)  # 임의 방향 (0~2π 라디안)
        req.name = 'turtle2'
        future = self.spawn_client.call_async(req)     # 비동기 호출
        future.add_done_callback(self.spawn_done)      # 완료 시 콜백 예약

        self.pose1 = None
        self.pose2 = None
        self.create_subscription(Pose, '/turtle1/pose', self.pose1_callback, 10)
        self.create_subscription(Pose, '/turtle2/pose', self.pose2_callback, 10)
        self.publisher = self.create_publisher(Twist, '/turtle1/cmd_vel', 10)

        self.kill_client = self.create_client(Kill, '/kill')      # /kill 클라이언트
        self.create_service(Empty, '/quit', self.quit_callback)   # /quit 서버
        self.finished = False                                      # 판정 플래그

    def spawn_done(self, future):
        result = future.result()               # 응답 객체 꺼내기
        self.get_logger().info(f'거북이 생성됨: {result.name}')

    def pose1_callback(self, msg):
        self.pose1 = msg
        self.follow()                  # 내 위치가 갱신될 때마다 추적 판단

    def pose2_callback(self, msg):
        self.pose2 = msg

    def follow(self):
        if self.finished:
            return                     # 종료 절차 중이면 아무것도 안 함
        if self.pose1 is None or self.pose2 is None:
            return                     # 둘 다 받기 전엔 아무것도 안 함

        dx = self.pose2.x - self.pose1.x
        dy = self.pose2.y - self.pose1.y
        target_angle = math.atan2(dy, dx)          # 목표 방향각
        distance = math.sqrt(dx**2 + dy**2)        # 두 거북이 사이 거리

        if distance < 0.5:                          # 만남 판정 (0.5칸 이내)
            self.finished = True
            self.get_logger().info('만났다! 이동 로봇 제거 후 종료')
            req = Kill.Request()
            req.name = 'turtle1'                    # 이동 중인 로봇을 지운다
            future = self.kill_client.call_async(req)
            future.add_done_callback(self.last_kill_done)
            return

        error = target_angle - self.pose1.theta    # 방향 오차
        while error > math.pi:                     # 오차를 -π ~ +π 범위로 보정
            error -= 2 * math.pi
        while error < -math.pi:
            error += 2 * math.pi

        cmd = Twist()
        cmd.linear.x = 1.5             # 일정 속도 전진
        cmd.angular.z = 3.0 * error    # P 제어: 오차에 비례해 회전
        self.publisher.publish(cmd)

    def last_kill_done(self, future):
        raise SystemExit                            # 마지막 kill 완료 → 종료

    def quit_callback(self, request, response):
        self.finished = True                        # 추적 중지
        self.get_logger().info('quit 요청: 두 로봇 모두 제거')
        req = Kill.Request()
        req.name = 'turtle1'
        future = self.kill_client.call_async(req)
        future.add_done_callback(self.quit_kill1_done)
        return response

    def quit_kill1_done(self, future):
        req = Kill.Request()
        req.name = 'turtle2'                        # turtle1 다음 turtle2 제거
        future = self.kill_client.call_async(req)
        future.add_done_callback(self.last_kill_done)


def main(args=None):
    rclpy.init(args=args)
    node = TurtleFollow()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### launch/follow.launch.py

```python
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='turtlesim',
            executable='turtlesim_node',
        ),
        Node(
            package='my_robot_controller',
            executable='turtle_follow',
        ),
    ])
```

### setup.py

- `entry_points`에 노드 등록 추가: `'turtle_follow = my_robot_controller.turtle_follow:main'`
- `data_files`는 **수정 불필요** — 문제12에서 `glob('launch/*.launch.py')`로
  등록했기 때문에 새 런치파일도 자동 포함된다. 단, 파일명이 반드시
  `.launch.py`로 끝나야 패턴에 걸린다 (처음에 `robot.launch2.py`로 지어서
  glob에 걸리지 않는 문제를 겪었다).

### 지시서에 없는 사항에 대한 가정

- turtle2의 임의 위치는 벽에 너무 붙지 않도록 1.0~10.0 범위로 정했다
  (전체 범위는 0~11.09).
- 만남 판정 거리는 0.5로 정했다 (거북이 크기 수준의 근접).
- 추적 속도 1.5, 회전 이득 3.0은 실험적으로 정한 값이다.

## 6. 실행 결과

### 시나리오 1 — 만남 경로 (자동 종료)

```
$ ros2 launch my_robot_controller follow.launch.py
[INFO] [turtlesim_node-1]: process started with pid [4727]
[INFO] [turtle_follow-2]: process started with pid [4729]
[turtlesim_node-1] [INFO] [...] [turtlesim]: Spawning turtle [turtle1] at x=[5.544445], y=[5.544445], theta=[0.000000]
[turtlesim_node-1] [INFO] [...] [turtlesim]: Spawning turtle [turtle2] at x=[2.937134], y=[2.274156], theta=[1.411596]
[turtle_follow-2] [INFO] [...] [turtle_follow]: 거북이 생성됨: turtle2
[turtle_follow-2] [INFO] [...] [turtle_follow]: 만났다! 이동 로봇 제거 후 종료
[INFO] [turtle_follow-2]: process has finished cleanly [pid 4729]
```

turtle2가 임의 위치(2.94, 2.27)에 생성됐고, turtle1이 곡선 궤적으로 접근해
약 3초 만에 만났다. turtle1만 화면에서 사라지고 제어 노드는 예외 없이
종료됐다(`finished cleanly`).

### 시나리오 2 — /quit 경로

만나기 전에 다른 터미널에서 `/quit`을 호출했다:

```
$ ros2 service call /quit std_srvs/srv/Empty "{}"
```

```
[turtle_follow-2] [INFO] [...] [turtle_follow]: quit 요청: 두 로봇 모두 제거
[INFO] [turtle_follow-2]: process has finished cleanly [pid 4804]
```

두 거북이 모두 사라져 빈 화면이 됐고, 제어 노드는 정상 종료됐다.

## 7. 실습 중 겪은 문제와 배운 점

| 문제 | 원인 | 배운 점 |
|------|------|---------|
| `SyntaxError` at `.async(` | 메서드 이름 `call_async`를 `async`로 잘못 적음 (`async`는 파이썬 예약어) | 트레이스백의 파일·줄번호·`^^^` 표시가 정확한 위치를 알려준다 |
| `TypeError: 'module' object is not callable` | `entry_points` 등록에서 `:main` 누락 | 등록 형식은 `이름 = 패키지.파일:main` — `:main`이 실행할 함수 지정 |
| `AttributeError: no attribute 'finished'` | `__init__`에 속성 추가를 빠뜨림 | 사용하는 속성은 반드시 `__init__`에서 초기화 |
| 코드를 고쳤는데 동작 안 바뀜 | 홈 디렉토리에서 빌드해 옛 빌드가 실행됨 | `cd ~/ros2_ws && colcon build`를 한 줄 습관으로 |
| 런치파일이 share에 복사 안 됨 | 파일명 `robot.launch2.py`가 glob 패턴 `*.launch.py`에 불일치 | 런치파일 이름은 `.launch.py`로 끝나야 한다 |

## 8. 산출물

| 파일 | 내용 |
|------|------|
| `13_follow.md` | 본 문서 |
| `my_robot_ws.tar.gz` | 워크스페이스 소스 (`ros2_ws/src`) 압축 — `turtle_follow.py`, `launch/follow.launch.py`, 수정된 `setup.py` 포함 |
