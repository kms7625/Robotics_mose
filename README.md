# Robotics_mose — SW파일럿 로보틱스 과정 기록

ROS2 Humble 기반 **라인트레이싱 운반 로봇** 개발을 목표로 한 학습·과제 기록 저장소입니다.
제조 공정 간 운송 자동화 프로토타입을 최종 목표로, 구동 이론부터 ROS2 실습, 로봇 모델링까지 단계별로 진행하고 있습니다.

## 환경

- ROS2 Humble / Ubuntu 22.04 (arm64 VM)
- Python (rclpy), colcon
- 도구: turtlesim, RViz2, URDF/xacro

## 구성

| 폴더 | 내용 |
| --- | --- |
| `Chapter1/` | 하드웨어·제어 이론 9문제 — DC모터, 바퀴, IR센서, 엔코더, P제어 등 |
| `Chapter2/` | 리눅스 + ROS2 실습 13문제 — 노드 → 토픽 → 서비스 → 런치 → turtle_follow 종합 |
| `Chapter3/` | 로봇 모델링 — RViz2/TF, URDF·xacro 2륜 차동구동 로봇 모델 |

## 목표 로봇 요구사항 (발췌)

검은 선 인식 자율주행, 주행 로깅(1초 1회, CSV), 배터리 30분, 적재 1kg 등 R1~R10 정의.

## 진행 상태

- 과정1~3 문서 완료, URDF 2륜 로봇 모델 RViz2 검증까지 진행
- 다음 단계: Gazebo 시뮬레이션, 로깅(CSV)·USB 전송 구현
