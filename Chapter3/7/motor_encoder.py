import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Int8MultiArray

class MotorEncoderNode(Node):
    def __init__(self):
        super().__init__('motor_encoder_node')
        
        # 1. /joint_states 토픽을 발행할 Publisher 생성
        self.joint_sub = self.create_subscription(JointState, 'joint_states', self.joint_callback, 30)
        
        self.motor_rpm_pub = self.create_publisher(Int8MultiArray, 'motor_rpm', 30)
        # 3. 0.1초(10Hz)마다 토픽을 발행할 타이머 생성
        self.timer = self.create_timer(1/30, self.timer_callback)
        self.prev_left_wheel_position = 0.0
        self.prev_right_wheel_position = 0.0
        self.left_wheel_position = 0.0
        self.right_wheel_position = 0.0
        self.count = 0
    def joint_callback(self, msg):
        self.left_wheel_position = msg.position[msg.name.index('left_wheel_joint')]
        self.right_wheel_position = msg.position[msg.name.index('right_wheel_joint')]
    
    def timer_callback(self):
        self.count += 1
        left_wheel_rpm = ((self.left_wheel_position - self.prev_left_wheel_position)/(1/30))*60
        right_wheel_rpm = ((self.right_wheel_position - self.prev_right_wheel_position)/(1/30))*60
        if self.count >=(30*5):  # 1초마다 로그 출력
          self.get_logger().info(f'Left Wheel RPM: {left_wheel_rpm:.2f}, Right Wheel RPM: {right_wheel_rpm:.2f}')
          self.count = 0 

        self.prev_left_wheel_position = self.left_wheel_position
        self.prev_right_wheel_position = self.right_wheel_position
        
        msg = Int8MultiArray()
        msg.data = [int(self.left_wheel_position), int(self.right_wheel_position)]
        self.motor_rpm_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = MotorEncoderNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()