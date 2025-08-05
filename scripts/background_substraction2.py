import cv2
import time

##########################################################

save_count = 0
last_hd_time = 0
hd_interval = 10  # FHD 캡처 최소 간격 (초)
frame_w = 640
frame_h = 360
frame_HD_w = 1920
frame_HD_h = 1080

##########################################################


capture = cv2.VideoCapture(0)

# 해상도 변경. 저해상도로 분석하다가, 필요한 경우만 FHD로 촬영 <- 리소스 절약
capture.set(cv2.CAP_PROP_FRAME_WIDTH, frame_w)
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_h)

if not capture.isOpened():
    print("카메라를 열 수 없습니다.")
    exit()

fgbg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=True)
# history : 몇개의 프레임을 배경으로 이용할 것인지
# varThreshold : 해당 픽셀이 배경 모델에 의해 잘 표현되는지를 판단
# detecShadow : 그림자 검출 여부. 제거하면, 윤곽선이 더 정확해짐. 제거하지 않으면, 새의 존재를 더 쉽게 감지함

while True:
    ret, frame = capture.read()
    if not ret:
        break

    # 배경 제거
    fgmask = fgbg.apply(frame)

    # 노이즈 제거를 위한 모폴로지 연산
    # 모폴로지 : 객체의 형태 및 구조에 대해 분석하고 처리하는 기법
    # 모폴로지 연산 중 하나인 Opening을 사용함. 작은 흰색 노이즈 제거 및 객체의 윤곽은 유지하면서 깔끔하게 정리함
    # Closing, Gradient, TopHat 등 존재
    # 참조 : https://jepilyu.tistory.com/83
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)) # 3x3 타원을 이용하여 확대
    fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)

    # 윤곽선 검출
    # 연속된 흰색 영역의 경계선을 찾음
    contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # fgmask : 배경 제거로 얻은 이진 마스크 이미지. 흰색은 움직임이 있는 영역, 검은색은 배경
    # cv2.RETR_EXTERNAL : 가장 바깥 윤곽선맞 찾음. 내부 비어있는 구멍같은 윤곽선은 무시함
    # cv.CHAIN_APPROX_SIMPLE : 메모리 절약 및 속도 향상을 위한 불필요한 점은 생략하고 필요한 점만 저장함 
    # 검출된 윤곽선들은 contours에 저장, 각 윤곽선간의 계층 정보는 '_'로 버림

    detected = False
    for cnt in contours:
        area = cv2.contourArea(cnt)

        if area > 500:  # 새로 추정되는 최소 면적
            x, y, w, h = cv2.boundingRect(cnt)
            
            # 가장자리 면적 제거
            cx = x + w // 2
            cy = y + h // 2

            margin_ratio = 0.15  # 예: 양쪽 15% 제외
            x_min = int(frame_w * margin_ratio)
            x_max = int(frame_w * (1 - margin_ratio))
            y_min = int(frame_h * margin_ratio)
            y_max = int(frame_h * (1 - margin_ratio))
            
            # 중앙에 있는 유효 객체 → 표시 및 저장 대상으로 처리
            if x_min < cx < x_max and y_min < cy < y_max:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                detected = True
            # 가장자리 객체 → 무시
            else:
                pass

    # 새가 감지되면 이미지 저장
    if detected and (time.time() - last_hd_time > hd_interval):

        # 1) 고해상도로 전환
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        time.sleep(0.5) # 전환 후 안정화 대기

        # 확인
        actual_w = capture.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_h = capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
        if int(actual_w) != frame_HD_w or int(actual_h) != frame_HD_h:
            print("[ERROR] 카메라 해상도 전환 실패")
            capture.set(cv2.CAP_PROP_FRAME_WIDTH, frame_w)
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_h)
            continue

        # 2) 더미 프레임 버리기 (카메라 버퍼 안정화)
        for _ in range(3):
            capture.read()

        # 3) 실제 저장용 프레임 읽기
        for attempt in range(5):
            ret2, frame2 = capture.read()
            if ret2 and frame2 is not None:
                cv2.imwrite(f"bird_hd_{int(time.time())}.jpg", frame2)
                print(f"[INFO] 새 감지됨! 이미지 저장")
                save_count += 1
                last_hd_time = time.time()
                break
            time.sleep(0.2)
        else:
            print("[WARN] 고해상도 프레임 읽기 실패. 저장하지 않음.")

        # 4) 다시 저해상도로 복귀
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, frame_w)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_h)
        time.sleep(1)


    # 화면 출력
    cv2.imshow('Original', frame)
    cv2.imshow('Foreground Mask', fgmask)

    if cv2.waitKey(30) & 0xFF == ord('q'):
        break

capture.release()
cv2.destroyAllWindows()