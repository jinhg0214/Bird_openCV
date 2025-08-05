
# 움직임을 감지하면 카메라를 해상도를 바꾸어 촬영하는 프로그램

import cv2
import time
import threading
import queue
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# ----------------------------- 설정 -----------------------------
FRAME_W, FRAME_H = 1920, 1080               # 원본 프레임 해상도
RESIZE_W, RESIZE_H = 640, 360               # 감지용 프레임 해상도
CAPTURE_INTERVAL = 5                        # 감지 후 저장 최소 간격 (초)
BG_HISTORY = 500                            # 배경 학습 프레임 수
BG_THRESHOLD = 50                           # 배경 차이 민감도
MIN_AREA = 500                              # 움직임 인식 최소 면적

# 경로 설정 (중복 제거 및 에러 처리 추가)
try:
    current_file_path = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file_path)))
    SAVE_DIR = os.path.join(project_root, "images")
    
    # 폴더 생성
    os.makedirs(SAVE_DIR, exist_ok=True)
    print(f"[INFO] 저장 경로 설정 완료: {SAVE_DIR}")
    
except Exception as e:
    print(f"[ERROR] 경로 설정 실패: {e}")
    sys.exit(1)

# ----------------------------- 함수 정의 -----------------------------

# 카메라 초기화
def initialize_camera():
    cap = cv2.VideoCapture(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_H)
    if not cap.isOpened():
        raise IOError("카메라를 열 수 없습니다.")
     # 실제 설정된 해상도 확인
    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[INFO] 카메라 해상도: {actual_w}x{actual_h}")
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

# ----------------------------- 저장 스레드 관련 -----------------------------
save_queue = queue.Queue(maxsize=10) # 최대 10프레임만 저장
stop_thread = threading.Event()  # 스레드 종료 신호

def save_worker():
    # 이미지 저장 작업을 처리하는 워크 스레드
    while not stop_thread.is_set():
        try:
            # 1초 타임아웃으로 큐에서 작업 가져오기
            frame, timestamp = save_queue.get()

            filename = os.path.join(SAVE_DIR, f"bird_hd_{timestamp}.jpg")
            success = cv2.imwrite(filename, frame)

            if success:
                print(f"[INFO] 새 감지됨! 이미지 저장 → {filename}")
            else:
                print(f"[ERROR] 이미지 저장 실패: {filename}")

            print(f"[INFO] 새 감지됨! 이미지 저장 → {filename}")

            save_queue.task_done()
        except queue.Empty:
            continue  # 타임아웃 시 계속 진행
        except Exception as e:
            print(f"[ERROR] 저장 중 오류 발생: {e}")

# 저장 스레드 시작
save_thread = threading.Thread(target=save_worker, daemon=True)
save_thread.start()

# ----------------------------- 메인 루프 -----------------------------
def main():
    try:
        cap = initialize_camera()
        fgbg = initialize_background_subtractor()
        last_capture_time = 0

        print("[INFO] 프로그램 시작. 'q'를 눌러 종료하세요.")
        print(f"[INFO] 움직임 감지 최소 면적: {MIN_AREA}")
        print(f"[INFO] 캡처 간격: {CAPTURE_INTERVAL}초")

        while True:
            ret, frame = cap.read()
            if not ret:
                print("[WARN] 프레임 수신 실패")
                break

            frame_small = cv2.resize(frame, (RESIZE_W, RESIZE_H))
            detected, fgmask = detect_motion(frame_small, fgbg)

            if detected and (time.time() - last_capture_time > CAPTURE_INTERVAL):
                timestamp = int(time.time())
                
                try:
                    save_queue.put_nowait((frame.copy(), timestamp))
                    last_capture_time = time.time()
                    print(f"[DEBUG] 움직임 감지! 큐에 추가 (큐 크기: {save_queue.qsize()})")

                except queue.Full:
                    print("[WARN] 저장 큐가 가득 찼습니다. 프레임을 건너뜁니다.")

            cv2.imshow("Motion Detection", frame_small)
            cv2.imshow("Foreground Mask", fgmask)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("[INFO] 프로그램 종료")
                break

        cap.release()
        cv2.destroyAllWindows()

    except KeyboardInterrupt:
        print("\n[INFO] Ctrl+C로 프로그램 종료")

    except Exception as e:
        print(f"[ERROR] 예상치 못한 오류: {e}")
        
    finally:
        # 정리 작업
        print("[INFO] 리소스 정리 중...")
        
        # 스레드 종료 신호
        stop_thread.set()
        
        # 큐의 남은 작업 완료 대기 (최대 5초)
        try:
            save_queue.join()
        except:
            pass
            
        # 카메라 해제
        try:
            cap.release()
        except:
            pass
            
        # 윈도우 정리
        cv2.destroyAllWindows()
        
        print("[INFO] 프로그램 종료 완료")

# ----------------------------- 실행 -----------------------------
if __name__ == "__main__":
    main()
