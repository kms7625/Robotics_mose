import rclpy
from rclpy.node import Node
from std_msgs.msg import Int8MultiArray
from geometry_msgs.msg import Twist 
import math

class line_tracking_node(Node):
    def __init__(self):
        super().__init__('line_tracking_node')
        
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

    def rpm_sub_callback(self, msg):
        if len(msg.data) >= 2:
            self.rpm_left = float(msg.data[0])
            self.rpm_right = float(msg.data[1])

    def scan_sub_callback(self, msg):
        if len(msg.data) >= 3:
            # 0.5보다 크면 True, 작으면 False가 명확히 대입됩니다.
            self.left_detected = msg.data[0] > 0
            self.center_detected = msg.data[1] > 0
            self.right_detected = msg.data[2] > 0

    def timer_callback(self):
        msg = Twist()
        
        # 현재 감지된 센서의 총 개수
        detected_sum = int(self.left_detected) + int(self.center_detected) + int(self.right_detected)
        self.count += 1
        self.waring_timer +=1
        # --- 1. 경로를 완전히 이탈한 경우 (감지된 센서가 없음) ---
        if detected_sum == 0:
            if (not self.is_deviated):
                self.is_deviated = True
                self.deviated_distance = 0.0
                self.deviated_angle = 0.0
            

            # 오도메트리 기반 누적 거리/각도 계산
            w_left = self.rpm_left * 2.0 * math.pi / 60.0
            w_right = self.rpm_right * 2.0 * math.pi / 60.0
            
            v_center = self.wheel_radius * (w_right + w_left) / 2.0
            w_center = self.wheel_radius * (w_right - w_left) / self.wheel_tread
            
            self.deviated_distance += v_center * self.dt
            self.deviated_angle += w_center * self.dt

            # 라인을 찾기 위해 천천히 회전하며 전진 (제어 값은 로봇에 맞게 조절)
            msg.linear.x = 0.1   
            msg.angular.z = 0.3
            self.where_go = True
            
            if ((self.count >= (30 * 3))and(self.waring_timer>30*1)):
                self.get_logger().warn('경로 이탈! 라인을 찾는 중...')  
                degree_angle = math.degrees(self.deviated_angle)
                self.get_logger().info(
                    f'[경로 이탈 중] 누적 이동 거리: {self.deviated_distance:.3f}m, 누적 회전: {degree_angle:.1f}°'
                )
                self.count = 0 

        # --- 2. 경로를 만났거나 따라가는 중인 경우 ---
        else:
            self.waring_timer = 0
            if self.is_deviated:
                self.is_deviated = False

            # 직관적이고 안정적인 라인트레이싱 제어 루프
            if self.center_detected and not self.left_detected and not self.right_detected:
                # 중앙만 감지됨 -> 직진
                msg.linear.x = 0.5
                msg.angular.z = 0.0
                self.where_go=False
            elif self.left_detected and not self.right_detected:
                # 왼쪽에 치우침 -> 왼쪽으로 회전
                if (self.where_go):
                    msg.linear.x = 0.2
                    msg.angular.z = -0.5
                else:
                    msg.linear.x = 0.2
                    msg.angular.z = 0.5
            elif self.right_detected and not self.left_detected:
                # 오른쪽에 치우침 -> 오른쪽으로 회전
                if (self.where_go):
                    msg.linear.x = 0.2
                    msg.angular.z = 0.5
                else:
                    msg.linear.x = 0.2
                    msg.angular.z = -0.5
            else:
                # 기타 예외 상황 (세 센서 다 켜짐 등) -> 천천히 전진
                msg.linear.x = 0.3
                msg.angular.z = 0.0

        # 최종 제어 명령 퍼블리시
        self.cmd_vel_pub.publish(msg) 

def main(args=None):
    rclpy.init(args=args)
    node = line_tracking_node()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()