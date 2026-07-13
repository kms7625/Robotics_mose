# 인체는 신경계, 로봇은 토픽 — ROS2 토픽 (문제7)

---

## 1. 토픽(Topic)이란

인체에서 눈이 본 정보가 신경을 타고 뇌로, 뇌의 명령이 신경을 타고 손발로 전달되듯, ROS2에서
노드들 사이의 데이터 전달 통로 역할을 하는 것이 **토픽**이다.

- 한 노드가 토픽에 데이터를 **게시(Publish)**하면, 그 토픽을 **구독(Subscribe)**하는 노드들이
  데이터를 받는다.
- 게시자와 구독자는 **서로의 존재를 몰라도 된다** — 토픽이라는 "채널" 이름만 맞으면 통신이
  성립한다. 구독 대상은 상대 노드가 아니라 토픽이므로, 게시자를 다른 프로그램으로 바꿔도
  구독자는 그대로 동작한다.
- 1:1 전용 회선이 아니라 **방송 채널**에 가깝다. 하나의 토픽에 여러 게시자와 여러 구독자가
  동시에 붙을 수 있다(N:M 통신). 이는 아래 실험으로 직접 확인했다.

## 2. rqt_graph로 확인

talker/listener 노드를 실행한 상태에서 `rqt_graph`를 실행하고, 모드를 **Nodes only**에서
**Nodes/Topics (active)**로 바꾸면 다음 구조가 보인다.

```
[talker] ──→ (/chatter) ──→ [listener]
```

- Nodes only 모드에서는 노드끼리 직접 연결된 것처럼 보이지만, Nodes/Topics (active) 모드로
  바꾸면 두 노드 사이에 `/chatter`라는 **토픽이 중간에 존재**함이 드러난다.
- 연결선의 **방향(화살표)**: talker → `/chatter` (게시), `/chatter` → listener (구독).
  화살표 방향이 곧 데이터가 흐르는 방향이다.

저장 이미지: `rqt_graph_chatter.png`

## 3. ros2 topic 명령 3종

talker/listener가 실행 중인 상태에서 실행한 결과와 의미:

### 3.1 `ros2 topic list` — 활성 토픽 전체 목록

```
/chatter
/parameter_events
/rosout
```

`/chatter` 외의 두 토픽은 ROS2가 시스템용으로 자동 생성하는 것이다. `/rosout`은 모든 노드의
로그가 모이는 토픽으로, 문제5~6에서 쓴 `get_logger()`의 로그도 여기로 흐른다.

### 3.2 `ros2 topic info /chatter` — 토픽의 상세 정보

```
Type: std_msgs/msg/String
Publisher count: 1
Subscription count: 1
```

- `Type` — 이 토픽에 흐르는 메시지의 유형 (여기서는 문자열)
- `Publisher count` — 게시자 수 (talker 1개)
- `Subscription count` — 구독자 수 (listener 1개)

### 3.3 `ros2 topic echo /chatter` — 토픽에 흐르는 실제 데이터 확인

```
data: 'Hello World: 500'
---
data: 'Hello World: 501'
---
data: 'Hello World: 502'
---
```

talker가 게시 중인 메시지를 실시간으로 엿들을 수 있다. `echo` 명령 자체도 임시 구독자로 토픽에
붙는 것이므로, echo 실행 중에 `topic info`를 확인하면 Subscription count가 1 증가해 보인다.
종료는 Ctrl+C.

## 4. ROS2 기본 메시지 유형 — std_msgs

`ros2 topic info /chatter`에서 확인한 `std_msgs/msg/String`의 `std_msgs`는 "standard
messages", 즉 ROS2가 기본 제공하는 메시지 패키지다. `ros2 interface list | grep std_msgs`로
확인하면 다음과 같은 유형들이 있다.

| 유형 | 용도 | 라인트레이서 예시 |
|------|------|-------------------|
| `String` | 문자열 | 상태 메시지 |
| `Int32`, `Int64` 등 | 정수 | 엔코더 펄스 카운트 |
| `Float32`, `Float64` | 실수 | 속도(m/s) — 소수점이 필요하므로 정수형이 아닌 실수형 |
| `Bool` | 참/거짓 | "선을 벗어났는가" 판정 |

## 5. 게시자/구독자 수 변화 실험

talker/listener의 수를 바꿔가며 각 상황에서 `ros2 topic info /chatter`를 실행했다.

| 상황 | Publisher count | Subscription count |
|------|-----------------|--------------------|
| talker 1, listener 2 | 1 | 2 |
| talker 2, listener 1 | 2 | 1 |
| talker 2, listener 2 | 2 | 2 |

노드를 띄우는 수만큼 게시자/구독자 수가 그대로 늘어난다. 즉 **토픽은 두 노드 사이의 1:1
통신이 아니라, 하나의 채널에 여러 게시자와 여러 구독자가 동시에 붙는 N:M 통신 구조**다.

관찰한 동작:

- **talker 1, listener 2**: 두 listener가 **같은 메시지를 각자 복사본으로** 받는다. 나눠 받는
  것이 아니다.
- **talker 2, listener 1**: listener는 **두 talker의 메시지를 전부** 받는다 — 각 talker의
  카운터(예: `Hello World: 705`와 `Hello World: 12`)가 도착 순서대로 섞여 출력된다. 구독자는
  "누가 보냈는지"를 가리지 않고 토픽에 게시되는 모든 메시지를 받는다.

시사점: 실제 로봇에서 한 토픽에 게시자를 여럿 두면(예: 자동주행 노드와 수동조종 노드가 같은
`/cmd_vel`에 게시) 명령이 충돌할 수 있으므로 설계 시 주의해야 한다.

## 6. turtlesim 실험 — 거북이 2마리, 조종기 1개

demo 노드를 모두 종료한 후, `turtlesim_node` 2개와 `turtle_teleop_key` 1개를 실행했다.

### 6.1 관찰 결과

**방향키를 누르면 두 거북이가 똑같이 움직인다** — 두 거북이 창이 동일한 궤적을 그린다.

저장 이미지: `turtlesim_two_windows.png`

### 6.2 토픽 정보

```
$ ros2 topic info /turtle1/cmd_vel
Type: geometry_msgs/msg/Twist
Publisher count: 1
Subscription count: 2
```

- 게시자 1: `turtle_teleop_key`
- 구독자 2: 두 개의 `turtlesim_node`

### 6.3 토픽 내용 (왼쪽 방향키를 눌렀을 때)

```
linear:
  x: 0.0
  y: 0.0
  z: 0.0
angular:
  x: 0.0
  y: 0.0
  z: 2.0
---
```

`geometry_msgs/msg/Twist`는 실제 로봇 세계의 표준 속도 명령 형식이다.

- `linear` (x, y, z) — 직진 속도. 모두 0이므로 전진/후진 없음
- `angular` (x, y, z) — 회전 속도. `z: 2.0`은 반시계 방향 회전

### 6.4 세 노드 사이에 벌어지는 일 (정리)

1. `turtle_teleop_key` **노드**가 방향키 입력을 Twist 메시지로 변환해 `/turtle1/cmd_vel`
   **토픽에 게시**한다.
2. 두 `turtlesim_node`는 teleop 노드가 아니라 `/turtle1/cmd_vel` **토픽을 구독**하고 있다.
3. 토픽에 올라온 메시지를 두 노드가 **각자 복사본으로** 받아, 각자의 거북이를 움직인다.
   그래서 두 거북이가 동일한 궤적을 그린다.

토픽이 중간에서 전달자 역할을 하므로, 게시자와 구독자는 서로를 직접 알 필요가 없다.

## 7. 라인트레이서 운반 로봇과의 연결

이번에 본 `geometry_msgs/msg/Twist`가 우리 라인트레이서에서도 그대로 쓰인다. IR 센서 노드가
"선이 왼쪽에 있다"고 판단하면, 제어 노드가 `linear.x`(전진)와 `angular.z`(좌회전)를 조합한
Twist 메시지를 게시하고, 모터 노드가 이를 구독해 좌우 바퀴의 속도 차(차동 구동)로 변환하는
구조가 된다.

## 8. 제출물

- 본 문서: `7_topic.md`
- rqt_graph 그래프 이미지: `rqt_graph_chatter.png`
- 두 turtlesim 실행 화면: `turtlesim_two_windows.png`

**가정**: 지시서의 "토픽의 내용 캡쳐"는 `ros2 topic echo /turtle1/cmd_vel`의 텍스트 출력을
본 문서 6.3절에 수록하는 것으로 갈음했다. 실습 중 `topic info` 실행 시점에는 echo 노드를
종료한 상태였으므로 Subscription count는 2로 확인되었다 (echo 실행 중이었다면 3).
