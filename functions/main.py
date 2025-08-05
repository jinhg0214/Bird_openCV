import firebase_admin
from firebase_admin import credentials, firestore, storage
from firebase_functions import https_fn
from flask_cors import cross_origin
import os

# --- Firebase Admin SDK 초기화 ---
# 로컬(배포 시 분석 포함)과 클라우드 환경 모두에서 동작하는 로직입니다.
firebase_app = None
try:
    # 앱이 이미 초기화되었는지 확인합니다.
    firebase_app = firebase_admin.get_app()
except ValueError:
    # 초기화되지 않았다면, 서비스 계정 키 파일의 존재 여부를 확인합니다.
    service_account_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "service-account-key.json"))

    if os.path.exists(service_account_path):
        # 서비스 계정 키 파일이 있으면 (로컬 환경), 해당 키로 초기화합니다.
        cred = credentials.Certificate(service_account_path)
        firebase_app = firebase_admin.initialize_app(cred, {
            'storageBucket': 'bird-recog-project.appspot.com'
        })
        print("✅ Initialized with Service Account Key.")
    else:
        # 서비스 계정 키 파일이 없으면 (클라우드 배포 환경 또는 로컬 에뮬레이터), 기본 자격 증명으로 초기화합니다.
        # 에뮬레이터 환경에서는 initialize_app()에 인자를 전달하지 않아도 자동으로 설정됩니다.
        firebase_app = firebase_admin.initialize_app(options={'storageBucket': 'bird-recog-project.appspot.com'})
        print("✅ Initialized with Application Default Credentials.")

# Firestore 및 Storage 클라이언트
db = firestore.client(app=firebase_app)
bucket = storage.bucket('bird-recog-project.firebasestorage.app')

@https_fn.on_request()
@cross_origin(origins="*", methods=["POST", "OPTIONS"])
def delete_detection(req: https_fn.Request) -> https_fn.Response:
    """
    Firestore 문서와 연결된 Storage 이미지를 삭제하는 Cloud Function.
    HTTP POST 요청으로 호출하며, JSON 본문에 'docId'를 포함해야 합니다.
    """
    # POST 요청이 아니거나 JSON 데이터가 없는 경우 에러를 반환합니다.
    if req.method != "POST" or not req.is_json:
        return https_fn.Response("Invalid request: Must be a POST request with JSON body.", status=400)

    try:
        data = req.get_json()
        doc_id = data.get("docId")

        if not doc_id:
            return https_fn.Response("Missing 'docId' in request body.", status=400)

        print(f"🗑️ Deletion requested for document ID: {doc_id}")

        # 1. Firestore에서 문서 정보를 가져옵니다.
        doc_ref = db.collection("detections").document(doc_id)
        doc = doc_ref.get()

        if not doc.exists:
            print(f"  - Document not found.")
            return https_fn.Response("Document not found", status=404)

        doc_data = doc.to_dict()
        storage_path = doc_data.get("storagePath")

        # 2. Storage에서 이미지 파일을 삭제합니다.
        if storage_path:
            print(f"  - Deleting image from Storage: {storage_path}")
            blob = bucket.blob(storage_path)
            if blob.exists():
                blob.delete()
                print(f"  - Image deleted successfully.")
            else:
                print(f"  - Image not found in Storage, skipping.")
        else:
            print("  - No 'storagePath' found in document, skipping image deletion.")

        # 3. Firestore에서 문서를 삭제합니다.
        print(f"  - Deleting document from Firestore...")
        doc_ref.delete()
        print(f"  - Document deleted successfully.")

        print("✅ Deletion process completed.")
        # 성공 응답을 반환합니다.
        return https_fn.Response(f"Successfully deleted document {doc_id}", status=200)

    except Exception as e:
        print(f"🔥 An error occurred: {e}")
        # 에러 응답을 반환합니다.
        return https_fn.Response(f"An internal error occurred: {e}", status=500)
