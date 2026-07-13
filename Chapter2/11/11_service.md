# 문제11 — ROS2 서비스: 서버와 클라이언트 구현

## 1. ROS2 서비스란

### 토픽과의 비교

지금까지 사용한 **토픽**은 방송이다. `/turtle1/pose`는 듣는 쪽이 있든 없든 계속
발행된다. 반면 **서비스**는 전화 통화다 — **요청(Request)을 보내면 응답(Response)이
한 번 돌아온다.** 응답하는 쪽이 **서버**, 요청하는 쪽이 **클라이언트**다.

|                | 토픽                      | 서비스                   |
| -------------- | ------------------------- | ------------------------ |
| 통신 방식      | 일방적 방송 (1:N)         | 요청 → 응답 (1:1)       |
| 데이터 흐름    | 계속 흐름                 | 필요할 때 한 번          |
| 역할           | 퍼블리셔 / 서브스크라이버 | 서버 / 클라이언트        |
| 운반 로봇 예시 | 센서 값, 속도 명령        | "출발해", "배터리 몇 %?" |

서비스의 강점은 **응답이 곧 전달 확인**이라는 점이다. 토픽은 던지고 끝이라
전달 여부를 알 수 없지만, 서비스는 응답이 돌아오지 않으면 실패를 알 수 있다.
긴급 정지처럼 "접수 확인이 필요한 명령"에 서비스가 어울리는 이유다.

## 2. 명령행에서 서비스를 다루는 절차

처음 보는 서비스를 명령행에서 호출할 때는 다음 4단계를 밟는다:

```bash
① ros2 service list                  # 서비스 이름 확인
② ros2 service type <서비스이름>      # 자료형(인터페이스) 확인
③ ros2 interface show <자료형>        # 요청/응답 구조 확인
④ ros2 service call <서비스이름> <자료형> "{필드: 값}"   # 호출
```

③의 출력에서 `---` 구분선 **위가 요청**, **아래가 응답** 구조다.

### 실습: turtlesim의 /kill 서비스 호출

turtlesim_node를 실행한 상태에서:

```
$ ros2 service list
/clear
/kill
/reset
/spawn
/turtle1/set_pen
/turtle1/teleport_absolute
/turtle1/teleport_relative
...

$ ros2 service type /kill
turtlesim/srv/Kill

$ ros2 interface show turtlesim/srv/Kill
string name
---
```

요청에 문자열 `name` 하나를 담고, 응답은 비어 있다(데이터 없이 "처리 완료"
신호만 돌아온다). 화면의 거북이 이름 `turtle1`으로 호출하면:

```
$ ros2 service call /kill turtlesim/srv/Kill "{name: 'turtle1'}"
requester: making request: turtlesim.srv.Kill_Request(name='turtle1')

response:
turtlesim.srv.Kill_Response()
```

호출 즉시 turtlesim 화면에서 거북이가 사라졌다. 응답 내용은 비어 있지만
응답 자체가 돌아왔다는 것이 "요청이 처리됐다"는 확인이다.

주의: 서비스 이름은 `/kill`(소문자), 자료형은 `turtlesim/srv/Kill`(대문자 K)로
대소문자가 다르다. 이름을 손으로 재구성하지 말고 **확인 명령의 출력을 그대로
복사해서 쓰는 것**이 실수를 막는 방법이다.

## 3. demo_nodes_cpp의 add_two_ints_server 실습 (과정 기록)

응답에 데이터가 담기는 서비스의 예로, 두 정수를 더해주는 데모 서버를 실행하고
같은 4단계 절차로 호출했다.

터미널 1에서 서버 실행:

```bash
ros2 run demo_nodes_cpp add_two_ints_server
```

터미널 2에서 절차대로:

```
$ ros2 service list
/add_two_ints
/add_two_ints_server/describe_parameters
/add_two_ints_server/get_parameter_types
...(이하 파라미터 서비스)

$ ros2 service type /add_two_ints
example_interfaces/srv/AddTwoInts

$ ros2 interface show example_interfaces/srv/AddTwoInts
int64 a
int64 b
---
int64 sum

$ ros2 service call /add_two_ints example_interfaces/srv/AddTwoInts "{a: 2, b: 3}"
requester: making request: example_interfaces.srv.AddTwoInts_Request(a=2, b=3)

response:
example_interfaces.srv.AddTwoInts_Response(sum=5)
```

- 요청에 `a`, `b` 두 정수를 담아 보내면 응답에 `sum`이 담겨 돌아온다.
  `/kill`과 달리 `---` 아래에 응답 데이터가 있는 완전한 요청-응답 구조다.
- `service list`에 함께 보이는 `/노드이름/describe_parameters` 등 6개는 ROS2가
  모든 노드에 자동으로 붙이는 파라미터 서비스다 (turtlesim에도 같은 세트가 있다).
- 노드 이름(`add_two_ints_server`)과 서비스 이름(`/add_two_ints`)은 별개다.
  서비스 이름은 반드시 `service list`에서 확인한다.

## 4. 파이썬에서의 서비스 처리와 비동기 호출

### 서버·클라이언트 생성 API

rclpy에서 서버·클라이언트 생성은 구독자·발행자 생성과 같은 패턴이다:

```python
self.create_subscription(Pose, '/turtle1/pose', self.pose_callback, 10)  # 구독자
self.create_service(Empty, '/quit', self.quit_callback)                  # 서비스 서버
self.kill_client = self.create_client(Kill, '/kill')                     # 서비스 클라이언트
```

서버 콜백은 `(request, response)`를 받아 `response`를 반환해야 한다.

### 왜 비동기(call_async)인가 — 데드락 문제

노드는 기본적으로 싱글 스레드다("전화선이 하나"). 콜백 안에서 다른 노드의
서비스를 **동기 방식으로 호출하고 응답을 기다리면**, 기다리는 동안:

1. 다른 콜백(pose 구독 등)이 처리되지 못해 로봇 제어가 멈추고,
2. 최악의 경우 기다리는 응답 자체를 받아줄 스레드가 없어 **영원히 풀리지 않는
   데드락**이 된다.

해결책이 **비동기 호출**이다:

```python
future = self.kill_client.call_async(req)     # 요청만 보내고 즉시 리턴
future.add_done_callback(self.kill_done)      # 응답 도착 시 실행할 콜백 예약
```

`call_async`는 미래에 도착할 결과를 담는 `Future` 객체를 즉시 반환하고,
노드는 하던 일(벽 회피)을 계속한다. 응답이 도착하면 예약해둔 콜백이 호출된다.
"보내놓고 끊어, 오면 알려줘" 방식이다. 지시서 요구사항 3번("호출 결과가
반환되는 동안에도 하던 일을 계속 수행")이 이것으로 충족된다.

### 예외 없이 정상 종료하는 방법

`rclpy.spin()`은 콜백에서 예외가 발생하면 밖으로 전파한다. 이를 이용해
콜백에서 `raise SystemExit`으로 spin을 빠져나오고, `main()`에서 try/except로
잡아 정리 후 종료하면 처리되지 않은 예외 없이 끝난다:

```python
try:
    rclpy.spin(node)
except (KeyboardInterrupt, SystemExit):   # Ctrl+C 또는 /quit에 의한 종료
    pass
node.destroy_node()
rclpy.shutdown()
```

`KeyboardInterrupt`(Ctrl+C)와 `SystemExit`(/quit 처리 완료) 둘 다 잡으므로
어느 경로로 종료해도 트레이스백이 출력되지 않는다.

## 5. 구현: turtle_move_control.py에 /quit 서버 + /kill 클라이언트 추가

문제10의 제어 노드에 다음을 추가 구현했다.

- `/quit` 서비스 서버: 자료형은 `std_srvs/srv/Empty`를 사용했다.
  "호출됐다는 사실 자체가 신호"이므로 요청·응답 모두 빈 자료형이면 충분하다.
  (int 값을 받는 설계도 가능하지만, 쓰지 않을 값의 검사 거리만 늘어난다)
- `/kill` 클라이언트: `/quit`을 받으면 `call_async`로 turtlesim의 `/kill`을
  호출해 거북이를 지우고, 응답이 도착하면 `SystemExit`으로 종료한다.

```python
import rclpy
from rclpy.node import Node
from turtlesim.msg import Pose
from geometry_msgs.msg import Twist
from std_srvs.srv import Empty
from turtlesim.srv import Kill


class TurtleMoveControl(Node):
    def __init__(self):
        super().__init__('turtle_move_control')
        self.margin = 2.0
        self.wall = 11.09
        self.subscription = self.create_subscription(
            Pose, '/turtle1/pose', self.pose_callback, 10)      # 구독자
        self.publisher = self.create_publisher(
            Twist, '/turtle1/cmd_vel', 10)                      # 발행자
        self.create_service(Empty, '/quit', self.quit_callback) # 서비스 서버
        self.kill_client = self.create_client(Kill, '/kill')    # 서비스 클라이언트

    def pose_callback(self, msg):
        cmd = Twist()
        if msg.x < self.margin or msg.x > self.wall - self.margin or \
           msg.y < self.margin or msg.y > self.wall - self.margin:
            cmd.linear.x = 1.0      # 위험: 천천히 전진하며
            cmd.angular.z = 1.5     #       왼쪽으로 곡선 회전
        else:
            cmd.linear.x = 2.0      # 안전: 직진
            cmd.angular.z = 0.0
        self.publisher.publish(cmd)

    def quit_callback(self, request, response):
        self.get_logger().info('quit 요청 받음!')
        req = Kill.Request()                        # 요청 객체 생성
        req.name = 'turtle1'                        # string name 필드 채우기
        future = self.kill_client.call_async(req)   # 비동기 호출: 보내고 즉시 리턴
        future.add_done_callback(self.kill_done)    # 응답 도착 시 kill_done 예약
        return response                             # /quit 응답은 바로 돌려줌

    def kill_done(self, future):
        self.get_logger().info('거북이 제거 완료, 종료합니다')
        raise SystemExit                            # spin을 빠져나가는 신호


def main(args=None):
    rclpy.init(args=args)
    node = TurtleMoveControl()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, SystemExit):
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### 지시서에 없는 사항에 대한 가정

- `/quit`의 자료형은 지시서에 지정되지 않아 `std_srvs/srv/Empty`로 정했다.
- 지울 거북이 이름은 기본 거북이인 `turtle1`로 고정했다.

## 6. 실행 결과

turtlesim과 제어 노드를 실행한 뒤, 세 번째 터미널에서 `/quit`을 호출했다:

```
$ ros2 service call /quit std_srvs/srv/Empty "{}"
requester: making request: std_srvs.srv.Empty_Request()

response:
std_srvs.srv.Empty_Response()
```

제어 노드 터미널의 출력:

```
$ ros2 run my_robot_controller turtle_move_control
[INFO] [1783946995.484923845] [turtle_move_control]: quit 요청 받음!
[INFO] [1783947986.488738462] [turtle_move_control]: 거북이 제거 완료, 종료합니다
$
```

- `/quit` 호출 즉시 빈 응답이 돌아왔고 (서버 동작 확인),
- 비동기로 호출한 `/kill`의 응답이 도착해 `kill_done`이 실행됐으며,
- turtlesim 화면의 거북이가 사라져 빈 화면이 됐고,
- 제어 노드는 **트레이스백 없이** 프롬프트로 복귀했다 — 처리되지 않은 예외
  없이 정상 종료됐다.

## 7. 실습 중 겪은 문제와 배운 점

| 문제                                                    | 원인                                                             | 배운 점                                                                                   |
| ------------------------------------------------------- | ---------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `waiting for service to become available...`에서 멈춤 | 서비스 이름 대소문자 오타(`/Kill`), 또는 서버 노드가 꺼져 있음 | 이름은`service list` 출력에서 복사한다. 서비스는 받는 쪽이 켜져 있어야 연결된다         |
| `The passed service type is invalid`                  | 자료형 앞에`/`를 붙이거나 소문자로 씀                          | 서비스 이름은`/`로 시작, 자료형은 `/` 없이 시작                                       |
| 노드가 실행 직후 조용히 종료                            | 수정 후`colcon build`를 안 돌려 오타가 있는 옛 빌드가 실행됨   | 실행되는 것은`install/`의 사본이다. 수정 → 빌드 → source → 실행 순서를 지킨다        |
| 홈 디렉토리에`build/install/log` 생성됨               | `~/ros2_ws`가 아닌 홈에서 `colcon build` 실행                | `colcon build`는 실행한 위치에 결과물을 만든다. 반드시 워크스페이스 최상위에서 실행한다 |

## 8. 산출물

| 파일                   | 내용                                     |
| ---------------------- | ---------------------------------------- |
| `11_service.md`      | 본 문서                                  |
| `my_robot_ws.tar.gz` | 워크스페이스 소스 (`ros2_ws/src`) 압축 |
