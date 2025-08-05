# OpenCV는 영상 촬영만 제공하고, 소리 녹음 기능은 지원하지 않음!
# 소리까지 함께 녹화하려면 OpenCV + PyAudio같은 라이브러리를 쓰거나, ffmpeg를 써야함 
# 소리까지 녹음하는 방법은 폐기

import cv2
import time
from datetime import datetime

# 설정값
WIDTH, HEIGHT = 640, 360
FPS = 15
DURATION = 10  # 저장할 영상 길이 (초)
FRAME_COUNT = FPS * DURATION

# 카메라 초기화
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
cap.set(cv2.CAP_PROP_FPS, FPS)

# 저장할 파일 이름
filename = datetime.now().strftime("bird_%Y%m%d_%H%M%S.mp4")

# fourcc는 플랫폼마다 다름. 윈도우에서는 'mp4v' 추천
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(filename, fourcc, FPS, (WIDTH, HEIGHT))

print(f"[INFO] 영상 저장 시작 → {filename}")

for _ in range(FRAME_COUNT):
    ret, frame = cap.read()
    if not ret:
        print("[WARN] 프레임 수신 실패")
        break

    out.write(frame)
    cv2.imshow('Recording...', frame)

    if cv2.waitKey(1) == ord('q'):
        print("[INFO] 사용자 중지")
        break

print(f"[INFO] 영상 저장 완료 → {filename}")

# 정리
cap.release()
out.release()
cv2.destroyAllWindows()
