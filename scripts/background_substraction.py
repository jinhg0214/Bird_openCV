
# 배경 제거 
import cv2

capture = cv2.VideoCapture(0)
if not capture.isOpened():
    print("카메라를 열 수 없습니다.")

fgbg1 = cv2.createBackgroundSubtractorMOG2() # MOG2 방식을 이용해 분석함
fgbg2 = cv2.createBackgroundSubtractorKNN() # KNN 방식

# MOG : Mixture of Gaussians
# 정적인 배경에서 표화적, 조명 변화나 나뭇잎 흔들림과 같은 반복적인 움직임에 강함

# KNN : K-Nearest Neighbors 
# 빠르게 변하는 배경에 강함. 그림자 감지 기능이 내장됨, 메모리 사용량이 많고, 계산량도 더 큼

while True:
    ret, frame = capture.read() # 카메라 읽기. 성공적으로 읽었다면 True, 아니면 False를 리턴함
    if not ret:
        break
    # 실제 영상 데이터는 Numpy 배열 형태로 frame에 저장됨

    # 배경 제거 적용
    fgmask1 = fgbg1.apply(frame) # 현재 프레임에 Background Subtraction 적용
    fgmask2 = fgbg2.apply(frame) # 현재 프레임에 Background Subtraction 적용

    # 결과 출력
    cv2.imshow('Webcam - Original', frame) #
    cv2.imshow('Webcam - Foreground Mask MOG', fgmask1)
    cv2.imshow('Webcam - Foreground Mask KNN', fgmask2)

    # ESC 누르면 종료
    if cv2.waitKey(30) & 0xFF == 27:
        break

# 자원 해제 후 종료
capture.release()
cv2.destroyAllWindows()