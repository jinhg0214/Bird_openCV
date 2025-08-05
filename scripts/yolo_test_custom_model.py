import cv2
from ultralytics import YOLO

# 학습시킨 모델 로딩
model = YOLO("C:/Github/Bird/models/my_model.pt")

# 웹캠 비디오 캡처 객체 생성
cap = cv2.VideoCapture(0) # 0번 카메라

# 프레임 크기 설정
frame_width = 1280
frame_height = 720
cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)


if not cap.isOpened():
    print("웹캠을 열 수 없습니다.")
    exit()

while True:
    # 프레임 읽기
    ret, frame = cap.read()

    if not ret:
        print("프레임을 읽을 수 없습니다.")
        break

    # YOLO 모델을 사용하여 객체 탐지
    # conf: confidence threshold (신뢰도 임계값)
    results = model.predict(source=[frame], conf=0.5, save=False)

    # 결과에서 바운딩 박스, 클래스, 신뢰도 정보 추출
    if len(results) > 0:
        for result in results:
            if len(result.boxes) > 0:
                for box in result.boxes:
                    # 바운딩 박스 좌표
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    # 신뢰도
                    conf = box.conf[0]
                    # 클래스 ID
                    cls = int(box.cls[0])
                    # 클래스 이름
                    class_name = model.names[cls]

                    # 화면에 바운딩 박스 그리기
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                    # 클래스 이름과 신뢰도 표시
                    label = f"{class_name}: {conf:.2f}"
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)


    # 결과 화면에 표시
    cv2.imshow("YOLOv5 Custom Model Test", frame)

    # 'q' 키를 누르면 종료
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 자원 해제
cap.release()
cv2.destroyAllWindows()
