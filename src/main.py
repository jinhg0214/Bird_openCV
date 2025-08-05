import cv2
import time
import threading
import queue
import os
import sys
from ultralytics import YOLO
import firebase_manager # Firebase 모듈 임포트
import yaml # YAML 파싱을 위한 라이브러리

# ----------------------------- 설정 로드 -----------------------------
try:
    # 현재 스크립트의 절대 경로를 기준으로 프로젝트 루트를 찾습니다.
    current_file_path = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(current_file_path))
    CONFIG_PATH = os.path.join(project_root, "config", "app_config.yaml")

    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    print(f"[INFO] 설정 파일 로드 완료: {CONFIG_PATH}")

    # 설정 값 할당
    FRAME_W = config['camera']['frame_width']
    FRAME_H = config['camera']['frame_height']
    RESIZE_W = config['camera']['resize_width']
    RESIZE_H = config['camera']['resize_height']

    CAPTURE_INTERVAL = config['detection']['capture_interval']
    FIREBASE_UPLOAD_COOLDOWN = config['detection']['firebase_upload_cooldown']
    MIN_AREA = config['detection']['min_area']

    BG_HISTORY = config['background_subtraction']['history']
    BG_THRESHOLD = config['background_subtraction']['threshold']

    CONF_THRESHOLD = config['yolo']['confidence_threshold']
    VALID_BIRD_SPECIES = config['yolo']['valid_bird_species']

except Exception as e:
    print(f"[ERROR] 설정 파일 로드 또는 파싱 실패: {e}")
    sys.exit(1)

# ----------------------------- 경로 설정 -----------------------------
try:
    # MODEL_PATH는 그대로 유지
    MODEL_PATH = os.path.join(project_root, "models", "bird_detect_320.pt")
    print(f"[INFO] 모델 경로: {MODEL_PATH}")

except Exception as e:
    print(f"[ERROR] 경로 설정 실패: {e}")
    sys.exit(1)

# ----------------------------- 모델 로딩 -----------------------------
try:
    model = YOLO(MODEL_PATH)
    print("[INFO] YOLO 모델 로딩 완료.")
except Exception as e:
    print(f"[ERROR] YOLO 모델 로딩 실패: {e}")
    sys.exit(1)

# ----------------------------- 스레드 관련 -----------------------------
analysis_queue = queue.Queue(maxsize=10)
stop_thread = threading.Event()
last_successful_bird_upload_time = 0 # Firebase 업로드 쿨다운 관리를 위한 전역 변수

def analysis_worker():
    """YOLO 분석, 새 필터링, 쿨다운 적용 및 Firebase 업로드를 처리하는 워커 스레드"""
    global last_successful_bird_upload_time # 전역 변수 수정 선언

    while not stop_thread.is_set():
        try:
            frame, timestamp = analysis_queue.get(timeout=1)

            # YOLO 모델로 객체 탐지
            results = model.predict(source=[frame], conf=CONF_THRESHOLD, save=False, verbose=False)

            bird_detected_in_frame = False
            detected_species_name = None
            
            # 결과에서 유효한 새 종류 필터링
            if len(results) > 0 and len(results[0].boxes) > 0:
                for box in results[0].boxes:
                    cls = int(box.cls[0])
                    class_name = model.names[cls]
                    
                    if class_name in VALID_BIRD_SPECIES: # 유효한 새 종류인지 확인
                        bird_detected_in_frame = True
                        detected_species_name = class_name # 탐지된 정확한 새 이름 사용
                        detected_confidence = box.conf[0] # 탐지된 객체의 confidence 값 저장
                        
                        # 바운딩 박스 그리기 (선택 사항, 디버깅용)
                        # x1, y1, x2, y2 = map(int, box.xyxy[0])
                        # conf = box.conf[0]
                        # label = f"{class_name}: {conf:.2f}"
                        # cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        # cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                        break # 유효한 새가 하나라도 탐지되면 충분
            
            if bird_detected_in_frame:
                # 쿨다운 적용: 마지막 성공적인 업로드 이후 충분한 시간이 지났는지 확인
                if (time.time() - last_successful_bird_upload_time) > FIREBASE_UPLOAD_COOLDOWN:
                    print(f"[INFO] '{detected_species_name}' 객체 탐지! Firebase 업로드 조건 충족.")
                    
                    # 이미지를 JPEG 형식으로 인코딩 (Firebase 업로드용)
                    is_success, im_buf_arr = cv2.imencode(".jpg", frame)
                    if is_success:
                        # Firebase에 업로드
                        upload_result = firebase_manager.upload_detection_data(im_buf_arr, detected_species_name, detected_confidence)
                        if upload_result:
                            last_successful_bird_upload_time = time.time() # 성공 시 시간 갱신
                            print(f"[INFO] Firebase 업로드 성공. 다음 업로드까지 {FIREBASE_UPLOAD_COOLDOWN}초 쿨다운.")
                        else:
                            print("[WARN] Firebase 업로드 실패.")
                    else:
                        print("[ERROR] 프레임 JPEG 인코딩 실패.")
                else:
                    time_since_last_upload = time.time() - last_successful_bird_upload_time
                    remaining_cooldown = max(0, FIREBASE_UPLOAD_COOLDOWN - time_since_last_upload)
                    print(f"[INFO] '{detected_species_name}' 객체 탐지되었으나, 쿨다운 ({remaining_cooldown:.1f}초 남음) 중입니다. 스킵.")
            else:
                print("[INFO] 움직임은 감지되었으나, YOLO 모델이 유효한 새 객체를 탐지하지 못했습니다.")

            analysis_queue.task_done()

        except queue.Empty:
            continue
        except Exception as e:
            print(f"[ERROR] 분석 스레드에서 오류 발생: {e}")

# ----------------------------- 초기화 관련 -----------------------------
def initialize_camera():
    cap = cv2.VideoCapture(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_H)
    if not cap.isOpened():
        raise IOError("카메라를 열 수 없습니다.")
    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[INFO] 카메라 해상도: {actual_w}x{actual_h}")
    return cap

def initialize_background_subtractor():
    return cv2.createBackgroundSubtractorMOG2(history=BG_HISTORY, varThreshold=BG_THRESHOLD, detectShadows=True)

# ----------------------------- 움직임 감지 관련 -----------------------------
def detect_motion(frame_small, fgbg):
    fgmask = fgbg.apply(frame_small)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    fgmask = cv2.morphologyEx(fgmask, cv2.MORPH_OPEN, kernel)
    contours, _ = cv2.findContours(fgmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    motion_detected = False
    for cnt in contours:
        if cv2.contourArea(cnt) > MIN_AREA:
            motion_detected = True
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(frame_small, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
    return motion_detected, fgmask

# ----------------------------- 메인 루프 -----------------------------
def main():
    cap = None
    try:
        # Firebase 초기화
        if not firebase_manager.initialize_firebase():
            print("[ERROR] Firebase 초기화에 실패하여 프로그램을 종료합니다.")
            sys.exit(1)

        cap = initialize_camera()
        fgbg = initialize_background_subtractor()
        last_capture_time = 0

        # 분석 스레드 시작
        analysis_thread = threading.Thread(target=analysis_worker, daemon=True)
        analysis_thread.start()

        print("[INFO] 프로그램 시작. 'q'를 눌러 종료하세요.")

        while True:
            ret, frame = cap.read()
            if not ret:
                print("[WARN] 프레임 수신 실패")
                break

            frame_small = cv2.resize(frame, (RESIZE_W, RESIZE_H))
            detected, fgmask = detect_motion(frame_small, fgbg)

            # CAPTURE_INTERVAL은 움직임 감지 후 분석 큐에 넣는 간격
            if detected and (time.time() - last_capture_time > CAPTURE_INTERVAL):
                # timestamp는 이제 사용되지 않지만, 큐 인터페이스 유지를 위해 남겨둠
                timestamp = int(time.time()) 
                try:
                    analysis_queue.put_nowait((frame.copy(), timestamp))
                    last_capture_time = time.time()
                    print(f"[DEBUG] 움직임 감지! 분석 큐에 추가 (큐 크기: {analysis_queue.qsize()})")
                except queue.Full:
                    print("[WARN] 분석 큐가 가득 찼습니다. 프레임을 건너뜁니다.")

            # cv2.imshow("Motion Detection", frame_small)
            # cv2.imshow("Foreground Mask", fgmask)

            # if cv2.waitKey(1) & 0xFF == ord('q'):
            #     break

    except (KeyboardInterrupt, SystemExit):
        print("[INFO] 프로그램 종료 요청...")
    except Exception as e:
        print(f"[ERROR] 메인 루프에서 예상치 못한 오류 발생: {e}")
    finally:
        print("[INFO] 리소스 정리 중...")
        stop_thread.set()
        if 'analysis_thread' in locals() and analysis_thread.is_alive():
            analysis_thread.join(timeout=5)
        
        if cap:
            cap.release()
        cv2.destroyAllWindows()
        print("[INFO] 프로그램이 성공적으로 종료되었습니다.")

# ----------------------------- 실행 -----------------------------
if __name__ == "__main__":
    main()
