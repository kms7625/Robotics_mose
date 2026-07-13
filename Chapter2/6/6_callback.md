# 로봇은 쉬지 않고 계속 움직인다 — 타이머와 콜백 (문제6)

---

## 1. 타이머(Timer)란 무엇인가

### 개념

문제5에서 만든 `logging_node`는 로그를 한 줄 남기고 나서는 `spin()`으로 살아만 있을 뿐 별다른
동작을 하지 않았다. 실제 로봇은 그렇게 가만히 있으면 안 되고, **센서 값을 주기적으로 읽거나
모터 상태를 주기적으로 점검**해야 한다. 일정 시간 간격마다 어떤 동작을 자동으로 반복 실행하게
해주는 것이 ROS2의 **타이머**다.

```python
self.timer = self.create_timer(2.0, self.timer_callback)
```

- `create_timer(주기(초), 콜백함수)` — `Node`가 제공하는 메서드.
- `2.0` — 2초마다 실행하라는 뜻.
- `self.timer_callback` — 2초마다 **호출될 함수를 등록**하는 것. 괄호 없이 이름만 넘기므로, 이
  줄이 실행되는 순간 함수가 즉시 실행되는 게 아니라 "나중에 이 함수를 실행해달라"는 예약일
  뿐이다.

## 2. 콜백(Callback) 함수란

### 개념

일반적인 함수 호출은 `함수이름()`처럼 우리가 직접 부른다. 반면 **콜백 함수**는 우리가 직접
부르지 않고, **특정 이벤트가 발생했을 때 프레임워크(여기서는 ROS2)가 대신 호출해주는 함수**다.

`create_timer`로 등록해두면, `rclpy.spin(node)`가 "계속 실행 상태로 대기"하는 동안 ROS2 내부에서
시간을 계속 재다가, 지정한 주기가 지날 때마다 자동으로 콜백을 호출한다. 즉 코드 어디에도
`timer_callback()`을 직접 부르는 곳은 없다 — 등록만 해두면 `spin()`이 도는 동안 알아서
불려나간다.

## 3. 구현 — 2초 타이머 (1차)

지시서의 첫 요구사항: 2초마다 호출되는 타이머를 만들고, 콜백이 로그에 `"2 seconds passed"`를
남긴다.

```python
import rclpy
from rclpy.node import Node

class timer_node(Node):
  def __init__(self):
    super().__init__('timer_node')
    self.timer = self.create_timer(2.0, self.timer_callback)

  def timer_callback(self):
    self.get_logger().info("2 seconds passed")

def main(args=None):
    rclpy.init(args=args)
    node = timer_node()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

작성 경로: `~/ros2_ws/src/my_robot_controller/my_robot_controller/timer_test.py`

### 실행 결과 (1차)

```
[INFO] [1783650408.846967203] [timer_node]: 2 seconds passed
[INFO] [1783650410.829915350] [timer_node]: 2 seconds passed
[INFO] [1783650412.829319271] [timer_node]: 2 seconds passed
...
```

정확히 2초 간격으로 로그가 찍히는 것을 확인했다.

## 4. 구현 — counter 공유 (2차)

지시서의 두 번째 요구사항: 클래스 속성 `counter`를 0으로 시작해서, **2초마다 1 증가**, **3초마다
1 감소**시키고, 두 콜백이 호출될 때마다 `counter` 값을 로그로 남긴다.

핵심은 두 개의 서로 다른 콜백(2초용, 3초용)이 **같은 상태(counter)를 공유**해야 한다는 점이다.
`self.counter`처럼 `self.`을 붙여 `__init__`에 선언하면, 그 객체에 속한 어떤 메서드에서도 같은
값을 읽고 고칠 수 있다.

```python
import rclpy
from rclpy.node import Node

class timer_node(Node):
  def __init__(self):
    super().__init__('timer_node')
    self.timer2 = self.create_timer(2.0, self.timer2_callback)
    self.timer3 = self.create_timer(3.0, self.timer3_callback)
    self.counter = 0

  def timer2_callback(self):
    self.counter = self.counter+1
    self.get_logger().info(f"2 seconds passed : {self.counter}")

  def timer3_callback(self):
    self.counter = self.counter-1
    self.get_logger().info(f"3 seconds passed : {self.counter}")

def main(args=None):
    rclpy.init(args=args)
    node = timer_node()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### 실행 결과 (2차)

```
[INFO] [1783652304.983524781] [timer_node]: 2 seconds passed : 1
[INFO] [1783652305.968689032] [timer_node]: 3 seconds passed : 0
[INFO] [1783652306.966977900] [timer_node]: 2 seconds passed : 1
[INFO] [1783652308.969730372] [timer_node]: 2 seconds passed : 2
[INFO] [1783652308.970828222] [timer_node]: 3 seconds passed : 1
[INFO] [1783652310.967568288] [timer_node]: 2 seconds passed : 2
[INFO] [1783652311.967333207] [timer_node]: 3 seconds passed : 1
[INFO] [1783652312.968252390] [timer_node]: 2 seconds passed : 2
[INFO] [1783652314.968175885] [timer_node]: 2 seconds passed : 3
[INFO] [1783652314.969051323] [timer_node]: 3 seconds passed : 2
[INFO] [1783652316.968032047] [timer_node]: 2 seconds passed : 3
[INFO] [1783652317.968055876] [timer_node]: 3 seconds passed : 2
[INFO] [1783652318.967928001] [timer_node]: 2 seconds passed : 3
[INFO] [1783652320.967889578] [timer_node]: 2 seconds passed : 4
[INFO] [1783652320.969216714] [timer_node]: 3 seconds passed : 3
```

지시서의 결과예시와 동일한 패턴(2초/3초 콜백이 번갈아 또는 겹쳐 호출되며 `counter`가 증감)으로
동작함을 확인했다.

## 5. 시행착오

이번 실습에서는 "정의(definition)"와 "호출(call)"을 혼동하는 실수를 여러 차례 거쳐 바로잡았다.

1. `create_timer(2.0, self.timer_callback)`에서 콜백 이름만 넘겼는데, `__init__` 안에서
   `self.timer_callback("2 seconds passed")`처럼 **직접 호출**해버린 시도가 있었다. 이러면
   객체 생성 시점에 딱 한 번만 실행되고, "2초마다 반복"되지 않는다. `create_timer`에 이름만
   넘기는 것과 직접 호출하는 것은 다르다는 점을 확인했다.
2. `def timer_callback(self):`처럼 **메서드로 정의**하지 않고, 클래스 밖에 독립 함수로 정의하거나
   아예 정의 자체를 빠뜨린 채 호출만 한 시도가 있었다. `self.이름`으로 접근하려면 그 이름이
   반드시 클래스 안에 메서드로 정의되어 있어야 한다.
3. `create_timer`에 넘긴 콜백 이름(`self.timer2_callback`)과 실제 정의한 메서드 이름
   (`timer_callback2`)의 철자 순서가 어긋나 있던 적이 있었다. 파이썬은 이름이 글자 하나까지
   정확히 일치해야 같은 대상으로 인식한다.
4. `self.counter +1`처럼 연산만 하고 대입하지 않아 값이 실제로는 바뀌지 않은 적이 있었다.
   `self.counter = self.counter + 1`로 명시적으로 재대입해야 한다.
5. `f"counter"`처럼 중괄호 없이 f-string을 쓴 적이 있었다. f-string이라도 `{}`로 감싼 부분만
   변수 값으로 치환되고, 감싸지 않은 문자열은 그냥 리터럴 텍스트로 출력된다. `f"...{self.counter}"`
   형태로 고쳐야 값이 보간된다.
6. 로그를 남기는 순서도 중요했다 — `self.counter`를 먼저 증가/감소시킨 뒤 로그를 남겨야, 콜백이
   처음 호출됐을 때부터 결과예시(`... : 1`)와 같은 값이 찍힌다. 로그를 먼저 남기고 나중에
   값을 바꾸면 "바뀌기 전" 값이 찍힌다.

## 6. setup.py 등록

문제5와 동일한 방식으로 `entry_points`에 등록했다.

```python
entry_points={
    'console_scripts': [
        'logging_node = my_robot_controller.logging:main',
        'timer_node = my_robot_controller.timer_test:main'
    ],
},
```

`timer_node`(entry_points에 등록한 실행 명령 이름), `timer_node` 클래스 이름,
`super().__init__('timer_node')`로 지정한 ROS 노드 이름이 모두 같은 문자열을 쓰고 있지만, 이 셋은
개념적으로는 서로 다른 것(패키지 실행 명령 / 파이썬 클래스 / ROS 노드 식별자)이며 우연히 같은
이름을 붙였을 뿐이다.

## 7. 제출물

- 워크스페이스 `src` 압축 파일: `my_robot_ws_src.tar.gz`
  (`~/ros2_ws`에서 `tar -czvf my_robot_ws_src.tar.gz src`로 생성)
