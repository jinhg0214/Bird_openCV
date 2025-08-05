import firebase_admin
from firebase_admin import credentials, firestore, storage
import datetime
import uuid
import os

# =====================================================================================
# Firebase 설정
# =====================================================================================

# 서비스 계정 키 파일의 경로
# 이 파일은 프로젝트 루트에 있다고 가정하고, src/firebase_manager.py의 위치를 기준으로 경로를 설정합니다.
# 예: C:/Github/Bird/bird-recog-project-firebase-adminsdk-fbsvc-bb66ea8203.json
_SERVICE_ACCOUNT_KEY_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "bird-recog-project-firebase-adminsdk-fbsvc-bb66ea8203.json"))

# Firebase Storage 버킷 이름
# 예: bird-recog-project.firebasestorage.app
_STORAGE_BUCKET = "bird-recog-project.firebasestorage.app"

# =====================================================================================

def initialize_firebase():
    """Firebase Admin SDK를 초기화합니다."""
    try:
        if not os.path.exists(_SERVICE_ACCOUNT_KEY_PATH):
            print(f"🔥 [에러] 서비스 계정 키 파일이 없습니다: '{_SERVICE_ACCOUNT_KEY_PATH}'")
            print("    => Firebase 콘솔에서 키 파일을 다운로드하고, 위 경로에 맞게 파일명을 수정해주세요.")
            return False

        cred = credentials.Certificate(_SERVICE_ACCOUNT_KEY_PATH)
        firebase_admin.initialize_app(cred, {
            'storageBucket': _STORAGE_BUCKET
        })
        print("Firebase 앱이 성공적으로 초기화되었습니다.")
        return True
    except Exception as e:
        print(f"🔥 [에러] Firebase 초기화 실패: {e}")
        print("    => 서비스 계정 키 파일 경로와 Storage 버킷 이름이 올바른지 확인해주세요.")
        return False

def upload_detection_data(image_data, detected_species, confidence, source_device="Raspberry Pi 4B"):
    """
    탐지된 이미지 데이터와 메타데이터를 Firebase에 업로드합니다.
    
    :param image_data: 이미지 파일의 바이너리 데이터 (예: cv2.imencode 결과)
    :param detected_species: YOLO가 탐지한 새의 종류 (문자열)
    :param confidence: 탐지된 객체의 confidence 값 (float)
    :param source_device: 데이터를 전송하는 장치 (기본값: Raspberry Pi 4B)
    :return: 업로드 성공 시 이미지 URL과 Firestore 문서 ID를 포함하는 딕셔너리, 실패 시 None
    """
    if not detected_species:
        print("탐지된 새 종류가 없어 Firebase 업로드를 건너뜁니다.")
        return None

    print(f"🚀 '{detected_species}' 탐지! Firebase 업로드를 시작합니다...")

    try:
        db = firestore.client()
        bucket = storage.bucket()

        # --- 1. Cloud Storage에 이미지 업로드 ---
        # 파일명 중복을 피하기 위해 UUID와 현재 시간을 사용
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        # 탐지율을 파일명에 포함 (정수 형태로 변환 후 세 자리로 포맷)
        confidence_int = int(confidence * 100) # 0.95 -> 95
        destination_blob_name = f"detections/{detected_species}/{timestamp_str}_{confidence_int:03d}.jpg"
        
        blob = bucket.blob(destination_blob_name)

        print(f"  [1/3] 이미지를 Storage에 업로드 중...")
        print(f"        - 대상 경로: {destination_blob_name}")
        
        # 이미지 데이터를 직접 업로드 (파일 경로 대신)
        blob.upload_from_string(image_data.tobytes(), content_type='image/jpeg')

        # --- 2. 업로드된 이미지의 공개 URL 가져오기 ---
        blob.make_public()
        image_url = blob.public_url
        print(f"  [2/3] 이미지 공개 URL 생성 완료.")
        print(f"        - URL: {image_url}")

        # --- 3. Firestore에 메타데이터 저장 ---
        doc_ref = db.collection('detections').document()
        
        # Firestore에 저장할 UTC 시간 (ISO 8601 형식)
        timestamp_iso = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

        metadata = {
            'species': detected_species,
            'timestamp': timestamp_iso,
            'imageUrl': image_url,
            'storagePath': destination_blob_name,
            'sourceDevice': source_device,
            'confidence': f"{float(confidence):.2f}" # confidence를 소수점 2자리 문자열로 저장
        }
        
        print(f"  [3/3] Firestore에 메타데이터 저장 중...")
        doc_ref.set(metadata)

        print(f"🎉 업로드 성공! Firestore 문서 ID: {doc_ref.id}")
        return {"imageUrl": image_url, "firestoreDocId": doc_ref.id}

    except Exception as e:
        print(f"🔥 [에러] Firebase 업로드 중 문제가 발생했습니다: {e}")
        return None

# 이 파일이 직접 실행될 경우 테스트 코드
if __name__ == "__main__":
    print("==================================================")
    print("     Firebase Manager 모듈 테스트 실행")
    print("==================================================")
    
    # 테스트용 이미지 데이터 생성 (실제로는 OpenCV에서 프레임을 받아옴)
    import numpy as np
    import cv2

    # 간단한 검은색 이미지 생성
    dummy_image = np.zeros((480, 640, 3), dtype=np.uint8)
    # 이미지에 텍스트 추가
    cv2.putText(dummy_image, "TEST IMAGE", (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
    
    # 이미지를 JPEG 형식으로 인코딩
    is_success, im_buf_arr = cv2.imencode(".jpg", dummy_image)
    if not is_success:
        print("더미 이미지 인코딩 실패!")
        exit()

    if initialize_firebase():
        # 테스트 업로드
        result = upload_detection_data(im_buf_arr, "test_bird", 0.95, "Local Test Script") # confidence 추가
        if result:
            print(f"테스트 업로드 결과: {result}")
        else:
            print("테스트 업로드 실패.")
    
    print("스크립트 실행이 완료되었습니다.")
