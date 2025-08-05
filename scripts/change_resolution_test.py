import cv2
import time

def open_camera(width, height):
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    time.sleep(1)  # 안정화 대기
    actual_w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    actual_h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    if int(actual_w) != width or int(actual_h) != height:
        print(f"[ERROR] 원하는 해상도 {width}x{height} 설정 실패 (실제: {int(actual_w)}x{int(actual_h)})")
        cap.release()
        return None
    return cap

# 초기 저해상도 열기
frame_w, frame_h = 640, 360
frame_HD_w, frame_HD_h = 1920, 1080
capture = open_camera(frame_w, frame_h)
if capture is None:
    exit()

last_hd_time = 0
hd_interval = 10  # FHD 캡처 최소 간격 (초)

while True:
    ret, frame = capture.read()
    if not ret:
        print("프레임 읽기 실패")
        break

    cv2.imshow('Frame', frame)

    key = cv2.waitKey(30) & 0xFF
    if key == 27:  # ESC 키 종료
        break
    elif key == 13:  # Enter 키 해상도 토글 예시
        current_w = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        current_h = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        capture.release()
        if (current_w, current_h) == (frame_w, frame_h):
            capture = open_camera(frame_HD_w, frame_HD_h)
            if capture is not None:
                print("고해상도 모드로 전환")
            else:
                # 실패 시 다시 저해상도 열기
                capture = open_camera(frame_w, frame_h)
        else:
            capture = open_camera(frame_w, frame_h)
            if capture is not None:
                print("저해상도 모드로 전환")
            else:
                # 실패 시 다시 고해상도 열기
                capture = open_camera(frame_HD_w, frame_HD_h)

capture.release()
cv2.destroyAllWindows()
