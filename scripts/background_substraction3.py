import cv2
import time

save_count = 0
last_hd_time = 0
hd_interval = 10  # FHD 캡처 최소 간격 (초)

low_w, low_h = 640, 360
hd_w, hd_h = 1920, 1080

capture = cv2.VideoCapture(0)
capture.set(cv2.CAP_PROP_FRAME_WIDTH, low_w)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, low_h)

if not capture.isOpened():
    print("카메라를 열 수 없습니다.")
    exit()

fgbg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=True)
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))

while True:
    ret, frame = capture.read()
    if not ret:
        break

    fgmask = fgbg.apply(frame)
    fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    detected = False
    for cnt in contours:
        if cv2.contourArea(cnt) > 500:
            detected = True
            break  # 하나만 감지되면 충분

    if detected and (time.time() - last_hd_time > hd_interval):
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, hd_w)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, hd_h)
        time.sleep(5)

        for _ in range(10):
            capture.read()

        ret2, frame2 = capture.read()
        if ret2 and frame2 is not None:
            cv2.imwrite(f"bird_hd_{int(time.time())}.jpg", frame2)
            print(f"[INFO] 새 감지됨! 이미지 저장")
            save_count += 1
            last_hd_time = time.time()
        else:
            print("[WARN] 고해상도 프레임 읽기 실패")

        capture.set(cv2.CAP_PROP_FRAME_WIDTH, low_w)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, low_h)
        time.sleep(5)

    cv2.imshow('Original', frame)
    cv2.imshow('Foreground Mask', fgmask)

    if cv2.waitKey(30) & 0xFF == ord('q'):
        break

capture.release()
cv2.destroyAllWindows()
