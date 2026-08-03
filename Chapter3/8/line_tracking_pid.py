import rclpy
from rclpy.node import Node
from std_msgs.msg import Int8MultiArray
from geometry_msgs.msg import Twist
import math


class PID:
    """단순한 이산시간 PID 컨트롤러"""

    def __init__(self, kp, ki, kd, output_limit):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.output_limit = output_limit  # (min, max)

        self.integral = 0.0
        self.prev_error = 0.0
        self.prev_error_valid = False  # 첫 스텝에서 미분값 튀는 것 방지

    def reset(self):
        self.integral = 0.0
        self.prev_error = 0.0
        self.prev_error_valid = False

    def compute(self, error, dt):
        # 적분 항 (리밋 없음 - ki 계수로 누적 속도를 조절)
        self.integral += error * dt

        # 미분 항
        if self.prev_error_valid:
            derivative = (error - self.prev_error) / dt
        else:
            derivative = 0.0
            self.prev_error_valid = True

        output = (self.kp * error) + (self.ki * self.integral) + (self.kd * derivative)
        output = max(self.output_limit[0], min(self.output_limit[1], output))

        self.prev_error = error
        return output


class line_tracking_pid_node(Node):
    def __init__(self):
        super().__init__('line_tracking_pid_node')

        # motor_rpm 구독 설정
        self.rpm_sub = self.create_subscription(
            Int8MultiArray, 'motor_rpm', self.rpm_sub_callback, 30
        )

        # scan_state 구독 설정
        self.scan_det_sub = self.create_subscription(
            Int8MultiArray, '/scan_state', self.scan_sub_callback, 30
        )

        # 30Hz 타이머 콜백 (dt = 1/30 초)
        self.dt = 1 / 30.0
        self.timer = self.create_timer(self.dt, self.timer_callback)

        # cmd_vel 퍼블리셔 생성
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 30)

        # 내부 저장용 변수들 초기화
        self.rpm_left = 0.0
        self.rpm_right = 0.0

        self.left_detected = False
        self.center_detected = False
        self.right_detected = False
        self.count = 0

        # [로봇 물리 사양 정보] 본인 URDF에 맞게 수정
        self.wheel_radius = 0.5  # 바퀴 반지름 (m)
        self.wheel_tread = 1.0   # 바퀴 간 거리 (m)

        # [경로 이탈 추적용 변수]
        self.is_deviated = False
        self.deviated_distance = 0.0
        self.deviated_angle = 0.0
        self.where_go = False
        self.waring_timer = 0

        # ---------------- PID 관련 설정 (여기 값들 직접 수정해서 튜닝) ----------------
        self.kp = 1.0
        self.ki = 0.1
        self.kd = 0.6
        self.base_speed = 0.5  # 직진 속도 (고정값)

        # angular.z 출력 한계
        self.pid = PID(
            kp=self.kp, ki=self.ki, kd=self.kd,
            output_limit=(-1.5, 1.5),
        )

        # 라인을 잃기 직전의 에러 부호를 기억 (탐색 방향 결정용)
        self.last_error = 0.0

    def rpm_sub_callback(self, msg):
        if len(msg.data) >= 2:
            self.rpm_left = float(msg.data[0])
            self.rpm_right = float(msg.data[1])

    def scan_sub_callback(self, msg):
        if len(msg.data) >= 3:
            self.left_detected = msg.data[0] > 0
            self.center_detected = msg.data[1] > 0
            self.right_detected = msg.data[2] > 0

    def compute_line_error(self):
        """
        L/C/R 3개 on/off 센서로부터 라인의 좌우 편차(error)를 계산.
        error > 0  -> 라인이 오른쪽에 있음 (오른쪽으로 회전해야 함)
        error < 0  -> 라인이 왼쪽에 있음 (왼쪽으로 회전해야 함)
        error == 0 -> 중앙 정렬
        """
        weight_sum = 0.0
        count = 0

        if self.left_detected:
            weight_sum += -1.0
            count += 1
        if self.center_detected:
            weight_sum += 0.0
            count += 1
        if self.right_detected:
            weight_sum += 1.0
            count += 1

        if count == 0:
            return None  # 라인 완전 소실 -> 별도 탐색 로직에서 처리

        return weight_sum / count

    def timer_callback(self):
        msg = Twist()

        detected_sum = int(self.left_detected) + int(self.center_detected) + int(self.right_detected)
        self.count += 1
        self.waring_timer += 1

        # --- 1. 경로를 완전히 이탈한 경우 (감지된 센서가 없음) ---
        if detected_sum == 0:
            if not self.is_deviated:
                self.is_deviated = True
                self.deviated_distance = 0.0
                self.deviated_angle = 0.0
                self.pid.reset()  # 라인을 다시 잡았을 때 적분 항이 튀지 않도록 초기화

            # 오도메트리 기반 누적 거리/각도 계산
            w_left = self.rpm_left * 2.0 * math.pi / 60.0
            w_right = self.rpm_right * 2.0 * math.pi / 60.0

            v_center = self.wheel_radius * (w_right + w_left) / 2.0
            w_center = self.wheel_radius * (w_right - w_left) / self.wheel_tread

            self.deviated_distance += v_center * self.dt
            self.deviated_angle += w_center * self.dt

            # 라인을 찾기 위해 천천히 회전하며 전진
            # 회전 방향은 라인을 잃기 직전의 에러 부호를 따라감
            search_dir = 1.0 if self.last_error >= 0 else -1.0
            msg.linear.x = 0.1
            msg.angular.z = 0.3 * search_dir
            self.where_go = True

            if (self.count >= (30 * 3)) and (self.waring_timer > 30 * 1):
                self.get_logger().warn('경로 이탈! 라인을 찾는 중...')
                degree_angle = math.degrees(self.deviated_angle)
                self.get_logger().info(
                    f'[경로 이탈 중] 누적 이동 거리: {self.deviated_distance:.3f}m, 누적 회전: {degree_angle:.1f}°'
                )
                self.count = 0

        # --- 2. 경로를 만났거나 따라가는 중인 경우 (PID 제어) ---
        else:
            self.waring_timer = 0
            if self.is_deviated:
                self.is_deviated = False
                self.pid.reset()  # 재진입 시 이전 적분값으로 인한 튐 방지

            error = self.compute_line_error()
            self.last_error = error

            # 코드 상단(self.kp/ki/kd)을 직접 수정하면 여기 반영됨
            self.pid.kp = self.kp
            self.pid.ki = self.ki
            self.pid.kd = self.kd

            angular_output = self.pid.compute(error, self.dt)

            msg.linear.x = self.base_speed
            msg.angular.z = angular_output
            self.where_go = False

        self.cmd_vel_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = line_tracking_pid_node()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()