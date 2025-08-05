
# 움직임을 감지하면 카메라를 해상도를 바꾸어 촬영하는 프로그램
# FHD로 촬영하되, OpenCV로 640x360으로 축소한 뒤
# 이를 배경 제거를 이용해 움직임을 감지하고
# 움직임을 감지한 경우, FHD로 촬영하는 프로그램

import cv2
import time

# ----------------------------- 설정 -----------------------------
FRAME_W, FRAME_H = 1920, 1080               # 원본 프레임 해상도
RESIZE_W, RESIZE_H = 640, 360               # 감지용 프레임 해상도
CAPTURE_INTERVAL = 10                       # 감지 후 저장 최소 간격 (초)
BG_HISTORY = 500                            # 배경 학습 프레임 수
BG_THRESHOLD = 50                           # 배경 차이 민감도
MIN_AREA = 500                              # 움직임 인식 최소 면적

# ----------------------------- 함수 정의 -----------------------------

# 카메라 초기화
def initialize_camera():
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_H)
    if not cap.isOpened():
        raise IOError("카메라를 열 수 없습니다.")
    return cap

# 배경 제거 초기화. MOG2 방식 이용
def initialize_background_subtractor():
    return cv2.createBackgroundSubtractorMOG2(
        history=BG_HISTORY,
        varThreshold=BG_THRESHOLD,
        detectShadows=True
    )

# 움직임을 감지하는 함수
def detect_motion(frame_small, fgbg):
    fgmask = fgbg.apply(frame_small)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > MIN_AREA:
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(frame_small, (x, y), (x+w, y+h), (0, 255, 0), 2)
            return True, fgmask
    return False, fgmask

def save_frame(frame):
    timestamp = int(time.time())
    filename = f"bird_hd_{timestamp}.jpg"
    cv2.imwrite(filename, frame)
    print(f"[INFO] 새 감지됨! 이미지 저장 → {filename}")


# ----------------------------- 메인 루프 -----------------------------
def main():
    cap = initialize_camera()
    fgbg = initialize_background_subtractor()
    last_capture_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARN] 프레임 수신 실패")
            break

        frame_small = cv2.resize(frame, (RESIZE_W, RESIZE_H))
        detected, fgmask = detect_motion(frame_small, fgbg)

        if detected and (time.time() - last_capture_time > CAPTURE_INTERVAL):
            save_frame(frame)
            last_capture_time = time.time()

        cv2.imshow("Motion Detection", frame_small)
        cv2.imshow("Foreground Mask", fgmask)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("[INFO] 프로그램 종료")
            break

    cap.release()
    cv2.destroyAllWindows()

# ----------------------------- 실행 -----------------------------
if __name__ == "__main__":
    main()


'''
1. 초기화
    1-1. 카메라 설정 (FHD로 열기, 분석에는 resize 사용)
    1-2. 변수 초기화 

2. 배경 제거 모델 초기화

3. Main Loop
    3-1. 카메라로부터 FHD 프레임을 받아옴
    3-2. 프레임을 640x360으로 resize (감지용)
    3-3. resize된 프레임에 대해 배경 제거 적용
    3-4. 윤곽선 검출 및 면적 필터링을 통해 움직임 유무 판단
        3-4-1. 조건을 만족하면 detected = True
    3-5. detected == True 이고, interval 이상 시간이 지났다면
        3-5-1. FHD 프레임을 저장 (고해상도 촬영)
        3-5-2. last_time 갱신
    3-6. 디버깅 및 시각화를 위한 화면 출력
    3-7. 종료 키 입력 감지 ('q' 누르면 종료)

4. 정리

'''