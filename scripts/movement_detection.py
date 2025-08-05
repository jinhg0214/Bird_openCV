
# 움직임을 감지하면 카메라를 해상도를 바꾸어 촬영하는 프로그램

'''
카메라를 껐다 키는 방식으로 구현해봤는데 

카메라를 껐다 키는 과정이 매우 오래걸려서, 움직임을 인식하면 프리징이 걸려버림

이 방법은 폐기

'''

import cv2
import time

##########################################################

last_time = 0
interval = 10 # 캡처 최소 간격 (초)

frame_w = 640
frame_h = 360
frame_HD_w = 1920
frame_HD_h = 1080

# Background substraction 관련 변수
bg_history = 500 # 배경 학습 프레임 수 300~800 이 적당했음
bg_varThreshold = 50 # 픽셀이 배경과 다르다고 판단하는 민감도 16~50

# 움직임 감지 관련 변수
bird_size = 500

##########################################################
# 1. 초기화
capture = cv2.VideoCapture(0)

capture.set(cv2.CAP_PROP_FRAME_WIDTH, frame_w) # 저해상도로 촬영
capture.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_h)

if not capture.isOpened():
    print("카메라를 열 수 없습니다.")
    exit()

# 2. background substraction 초기화
fgbg = cv2.createBackgroundSubtractorMOG2(history=bg_history, varThreshold=bg_varThreshold, detectShadows=True)

# 3. Main Loop
while True:
    # 3-1. 저화질 카메라 영상 받아 배경 제거
    ret, frame = capture.read()     # 카메라로부터 현재 영상을 받아 frame에 저장, 잘 받았다면 ret가 참

    # 배경 제거 적용, 모폴로지 연산 적용
    fgmask = fgbg.apply(frame)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)) # 3x3 타원을 이용하여 확대
    fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)

    # 윤곽선 검출
    contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 움직임 감지
    detected = False

    # 검출한 윤곽선이 해당 조건을 만족하는지 체크
    for cnt in contours:
        area = cv2.contourArea(cnt)

        if area > bird_size: # 새로 추정되는 최소 면적 
            ############### 디버깅용. 카메라에서 초록색 사각형을 출력해줌
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

            detected = True

    # 3-3. detected가 True이고, 설정한 시간만큼의 interval이 지났다면
    if detected and (time.time() - last_time > interval):
        # 1) 기본 카메라 종료
        capture.release()

        # 2) 고해상도 카메라 재시작
        capture = cv2.VideoCapture(0)
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, frame_HD_w)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_HD_h)

        for _ in range(3):  # 더미 프레임 버리기
            capture.read()

        # 3) 프레임 읽기
        ret2, frame2 = capture.read() 
        if ret2 and frame2 is not None:
            filename = f"bird_hd_{int(time.time())}.jpg"
            cv2.imwrite(filename, frame2) # 촬영 시도
            print(f"[INFO] 새 감지됨! 이미지 저장")
            last_hd_time = time.time()
        else:
            print("[WARN] 고해상도 프레임 읽기 실패")

        # 4) 다시 저해상도 카메라 재시작
        capture.release()
        capture = cv2.VideoCapture(0)
        capture.set(cv2.CAP_PROP_FRAME_WIDTH, frame_w)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_h)

        for _ in range(3):  # 더미 프레임 버리기
            capture.read()

    
    # cv2.imshow("original", frame)   # frame(카메라 영상)을 original 이라는 창에 띄워줌 
    cv2.imshow("Mask", fgmask)

    if cv2.waitKey(1) == ord('q'):  # 키보드의 q 를 누르면 무한루프가 멈춤
            break

# 99. destroy
capture.release()
cv2.destroyAllWindows()

'''
1. 초기화
2. Background Substraction 초기화
3. Main Loop
    3-1. 저화질 카메라 영상을 받아서, Background Substraction을 적용함
    3-2. 윤곽선 검출을 시도하여, 움직임이 감지되었는지 체크
        3-2-1. 만약 감지되었다면, detected 를 True 로 설정
    3-3. detected가 True이고, 설정한 시간만큼의 interval이 지났다면
        3-3-1. 카메라 해상도로르 고화질로 변경. set만 변경하는게 아니라 아예 완전히 껐다 킴
        3-3-2. 촬영
        3-3-3. 다시 카메라 해상도를 저화질로 변경
        3-3-4. last_time을 현재 시간으로 갱신 
    3-4. 화면 출력
    3-5. 입력키 확인. 종료키가 눌렸는지 체크한다
'''