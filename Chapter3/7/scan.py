import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
# 💡 BoolMultiArray와 이를 구성하기 위한 MultiArrayLayout, MultiArrayDimension 임포트
from std_msgs.msg import Int8MultiArray

class ScanNode(Node):
    def __init__(self):
        super().__init__('scan_node')
        
        self.center_sub = self.create_subscription(LaserScan, '/ir_sensor/center', self.center_callback, 30)
        self.left_sub = self.create_subscription(LaserScan, '/ir_sensor/left', self.left_callback, 30)
        self.right_sub = self.create_subscription(LaserScan, '/ir_sensor/right', self.right_callback, 30)
        
        # 30Hz 타이머 (1/30 초)
        self.scan_timer = self.create_timer(1/30, self.scan_timer_callback)
        
        # 💡 토픽 타입을 LaserScan에서 BoolMultiArray로 변경
        self.scan_pub = self.create_publisher(Int8MultiArray, '/scan_state', 30)  
        
        self.left_detected = False
        self.center_detected = False
        self.right_detected = False
        self.count =0

    def center_callback(self, msg):
        if len(msg.intensities) > 0:
            val = msg.intensities[0]
            if val > 500.0:
                self.center_detected = True
            else:
                self.center_detected = False

    def left_callback(self, msg):
        if len(msg.intensities) > 0:
            val = msg.intensities[0]
            if val > 500.0:
                self.left_detected = True
            else:
                self.left_detected = False
    def right_callback(self, msg):
        if len(msg.intensities) > 0:
            val = msg.intensities[0]
            if val > 500.0:
                self.right_detected = True
            else:
                self.right_detected = False

    def scan_timer_callback(self):
        self.count += 1

        # 💡 1. 메시지 객체 생성
        msg = Int8MultiArray()
        
        # 💡 2. 데이터 매핑 (리스트 형태로 data 필드에 주입)
        msg.data = [int(self.left_detected), int(self.center_detected), int(self.right_detected)]
        if self.count>=(30*5):
            self.count = 0
            self.get_logger().info(f"Scan State Data: {msg.data}")
        
        # 💡 3. 발행
        self.scan_pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = ScanNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()