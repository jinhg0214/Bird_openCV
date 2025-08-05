
import firebase_admin
from firebase_admin import credentials, firestore, storage
import datetime
import uuid  # 파일명 중복을 피하기 위해 사용
import os

# =====================================================================================
# 설정 섹션: 이 부분을 자신의 환경에 맞게 수정해주세요.
# =====================================================================================

# 1. Firebase 서비스 계정 키 파일의 경로
#    - Firebase 콘솔에서 다운로드한 JSON 파일의 이름을 여기에 입력하세요.
#    - 이 스크립트와 같은 폴더에 JSON 파일을 두는 것이 가장 간단합니다.
SERVICE_ACCOUNT_KEY_PATH = "../bird-recog-project-firebase-adminsdk-fbsvc-bb66ea8203.json"

# 2. Firebase Storage 버킷 이름
#    - Firebase 콘솔 > Storage 메뉴 상단에서 확인 가능합니다. (예: 'my-project.appspot.com')
STORAGE_BUCKET = "bird-recog-project.firebasestorage.app"

# 3. 업로드할 테스트 이미지 파일 경로
#    - 프로젝트의 'images' 폴더에 있는 이미지 중 하나를 사용합니다.
TEST_IMAGE_PATH = "../images/detected_1751874241.jpg"

# 4. 테스트용으로 사용할 새의 종류 (YOLO가 판별했다고 가정)
TEST_SPECIES = "crow"

# =====================================================================================

def initialize_firebase():
    """Firebase Admin SDK를 초기화합니다."""
    try:
        if not os.path.exists(SERVICE_ACCOUNT_KEY_PATH):
            print(f"🔥 [에러] 서비스 계정 키 파일이 없습니다: '{SERVICE_ACCOUNT_KEY_PATH}'")
            print("    => Firebase 콘솔에서 키 파일을 다운로드하고, 위 경로에 맞게 파일명을 수정해주세요.")
            return False

        cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
        firebase_admin.initialize_app(cred, {
            'storageBucket': STORAGE_BUCKET
        })
        print("✅ Firebase 앱이 성공적으로 초기화되었습니다.")
        return True
    except Exception as e:
        print(f"🔥 [에러] Firebase 초기화 실패: {e}")
        print("    => 서비스 계정 키 파일 경로와 Storage 버킷 이름이 올바른지 확인해주세요.")
        return False

def upload_to_firebase(local_image_path, detected_species):
    """
    이미지와 메타데이터를 Firebase에 업로드합니다.
    
    :param local_image_path: 로컬에 저장된 이미지 파일 경로
    :param detected_species: YOLO가 탐지한 새의 종류
    """
    if not os.path.exists(local_image_path):
        print(f"🔥 [에러] 업로드할 이미지 파일이 없습니다: '{local_image_path}'")
        return

    print(f"🚀 '{detected_species}' 탐지! Firebase 업로드를 시작합니다...")

    try:
        # Firestore와 Storage 클라이언트를 가져옵니다.
        db = firestore.client()
        bucket = storage.bucket()

        # --- 1. Cloud Storage에 이미지 업로드 ---
        # 파일명 중복을 피하기 위해 UUID로 새로운 파일명 생성
        # 예: detections/crow/crow_a1b2c3d4.jpg
        destination_blob_name = f"detections/{detected_species}/{detected_species}_{uuid.uuid4()}.jpg"
        
        blob = bucket.blob(destination_blob_name)

        print(f"  [1/3] 이미지를 Storage에 업로드 중...")
        print(f"        - 대상 경로: {destination_blob_name}")
        blob.upload_from_filename(local_image_path)

        # --- 2. 업로드된 이미지의 공개 URL 가져오기 ---
        # 공개적으로 접근 가능하도록 설정해야 URL이 동작합니다.
        blob.make_public()
        image_url = blob.public_url
        print(f"  [2/3] 이미지 공개 URL 생성 완료.")
        print(f"        - URL: {image_url}")

        # --- 3. Firestore에 메타데이터 저장 ---
        # 'detections' 라는 컬렉션에 새로운 문서를 추가합니다.
        doc_ref = db.collection('detections').document()
        
        metadata = {
            'species': detected_species,
            'timestamp': datetime.datetime.now(datetime.timezone.utc),  # 항상 UTC 시간으로 저장하는 것이 좋음
            'imageUrl': image_url,
            'storagePath': destination_blob_name,
            'sourceDevice': 'PC (Windows Test)' # 실제 Pi에서는 'Raspberry Pi 4B' 등으로 변경
        }
        
        print(f"  [3/3] Firestore에 메타데이터 저장 중...")
        doc_ref.set(metadata)

        print(f"🎉 업로드 성공! Firestore 문서 ID: {doc_ref.id}")
        print("   => Firebase 콘솔에서 Storage와 Firestore에 데이터가 잘 들어갔는지 확인해보세요.")

    except Exception as e:
        print(f"🔥 [에러] 업로드 중 문제가 발생했습니다: {e}")

# --- 메인 실행 블록 ---
if __name__ == "__main__":
    print("==================================================")
    print("     Firebase 업로드 테스트 스크립트 실행")
    print("==================================================")
    
    if initialize_firebase():
        upload_to_firebase(TEST_IMAGE_PATH, TEST_SPECIES)
    
    print("스크립트 실행이 완료되었습니다.")

