import os
import time
import json
import requests
import hashlib
import numpy as np
from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from mtcnn import MTCNN

# ───────────────────────────────────────────────────────────
# 0) 환경 설정 변수
# ───────────────────────────────────────────────────────────
categories = [
    "Korean K-pop idol profile picture",
    "African actor profile picture",
    "Eurpiean actress profile picture",
    "Hispanic actress profile picture",
    "American model profile picture"
]

MAX_IMAGES_PER_CATEGORY = 15

# 얼굴 바운딩박스 최소 크기(px) - 원본 좌표 기준
MIN_FACE_SIZE = 200

# 리사이즈 저장 크기(px)
TARGET_FACE_SIZE = (224, 224)

# 최종 이미지를 저장할 루트 폴더
BASE_OUTPUT_DIR = "dataset_bing_highres_frontal"

# 얼굴 검출용 축소 크기 기준 (짧은 변이 이 값을 넘으면 비율 유지해서 리사이즈)
DETECT_SHORT_MAX = 800  

# ───────────────────────────────────────────────────────────
# 1) MTCNN 얼굴 검출기 초기화
# ───────────────────────────────────────────────────────────
detector = MTCNN()

# ───────────────────────────────────────────────────────────
# 2) 정면(face frontal) 여부 엄격히 판별 함수
#    - 눈 높이 차이(eye_diff) < 15px
#    - 코 위치가 눈 중심으로부터 20px 이내
# ───────────────────────────────────────────────────────────
def is_frontal_strict(face):
    keypoints = face["keypoints"]
    left_eye = keypoints["left_eye"]
    right_eye = keypoints["right_eye"]
    nose = keypoints["nose"]
    
    eye_diff = abs(left_eye[1] - right_eye[1])
    nose_center = (left_eye[0] + right_eye[0]) / 2
    center_offset = abs(nose[0] - nose_center)
    
    return (eye_diff < 15) and (center_offset < 20)

# ───────────────────────────────────────────────────────────
# 3) 이미지 축소 함수 (MTCNN 검출 전용)
# ───────────────────────────────────────────────────────────
def resize_for_detection(pil_img, short_max=DETECT_SHORT_MAX):
    w, h = pil_img.size
    if min(w, h) > short_max:
        if w < h:
            new_w = short_max
            new_h = int(h * (short_max / w))
        else:
            new_h = short_max
            new_w = int(w * (short_max / h))
        return pil_img.resize((new_w, new_h), Image.LANCZOS)
    return pil_img

# ───────────────────────────────────────────────────────────
# 4) 얼굴 영역 크롭 함수 (numpy array 기준)
# ───────────────────────────────────────────────────────────
def crop_face_numpy(image_np, box):
    x, y, w, h = box
    x, y = max(x, 0), max(y, 0)
    return image_np[y : y + h, x : x + w]

# ───────────────────────────────────────────────────────────
# 5) 중복 방지용 해시 함수
# ───────────────────────────────────────────────────────────
def hash_image(image_data):
    return hashlib.md5(image_data).hexdigest()

# ───────────────────────────────────────────────────────────
# 6) Undetectable ChromeDriver 반환 함수
# ───────────────────────────────────────────────────────────
def get_undetectable_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        })
        """
    })
    return driver

# ───────────────────────────────────────────────────────────
# 7) Bing 이미지 검색 → 원본 다운로드 → 얼굴 검출 → 크롭 → 저장
#    (정면 얼굴만 통과)
# ───────────────────────────────────────────────────────────
def download_images_bing(query, download_path, max_images=10):
    driver = get_undetectable_driver()
    print(f"[INFO] Bing 검색 시작: '{query}'")

    search_url = (
        f"https://www.bing.com/images/search?"
        f"q={query.replace(' ', '+')}"
        f"&form=HDRSC2&first=1&tsc=ImageBasicHover"
    )
    driver.get(search_url)
    time.sleep(2)

    # 충분히 로딩되도록 스크롤
    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

    thumbnails = driver.find_elements(By.CSS_SELECTOR, "a.iusc")
    print(f"[DEBUG] 썸네일 개수: {len(thumbnails)}")

    os.makedirs(download_path, exist_ok=True)
    seen_hashes = set()
    saved_count = 0

    for thumb in thumbnails:
        if saved_count >= max_images:
            break

        # ① 썸네일의 m 속성에서 JSON 파싱하여 원본 URL 획득
        m_json = thumb.get_attribute("m")
        try:
            info = json.loads(m_json)
            img_url = info.get("murl")
        except Exception as e:
            print(f"[ERROR] JSON 파싱 실패: {e}")
            continue

        if not img_url or not img_url.startswith("http"):
            continue

        print(f"[DEBUG] 원본 이미지 URL: {img_url}")

        # ② 원본 이미지 다운로드
        try:
            resp = requests.get(img_url, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"[ERROR] 이미지 요청 실패: {e}")
            continue

        # ③ Content-Type 검사
        content_type = resp.headers.get("Content-Type", "")
        if not content_type.startswith("image/"):
            print(f"[SKIP] 이미지 아님 (Content-Type: {content_type})")
            continue

        # ④ PIL로 열어서 원본 이미지와 검출용 이미지 생성
        try:
            image_data = resp.content
            pil_orig = Image.open(BytesIO(image_data)).convert("RGB")
        except Exception as e:
            print(f"[ERROR] PIL 열기 실패: {e}")
            continue

        pil_detect = resize_for_detection(pil_orig, short_max=DETECT_SHORT_MAX)
        img_np_detect = np.array(pil_detect)

        # ⑤ 축소 이미지 기준으로 MTCNN 얼굴 검출
        try:
            faces = detector.detect_faces(img_np_detect)
        except Exception as e:
            print(f"[ERROR] MTCNN 검출 에러: {e}")
            continue

        print(f"[DEBUG] 얼굴 검출 개수(축소 기준): {len(faces)}")
        if len(faces) == 0:
            continue

        # 축소 비율 계산
        orig_w, orig_h = pil_orig.size
        det_w, det_h = pil_detect.size
        scale_x = orig_w / det_w
        scale_y = orig_h / det_h

        # ⑥ 축소된 얼굴 좌표 → 원본 좌표로 변환 후 정면 필터링
        for face in faces:
            x_det, y_det, w_det, h_det = face["box"]
            x_orig = int(x_det * scale_x)
            y_orig = int(y_det * scale_y)
            w_orig = int(w_det * scale_x)
            h_orig = int(h_det * scale_y)

            # 얼굴 크기 필터링 (원본 기준)
            if (w_orig < MIN_FACE_SIZE) or (h_orig < MIN_FACE_SIZE):
                print(f"[SKIP] 얼굴 크기 부족(원본 기준) w={w_orig}, h={h_orig}")
                continue

            # 정면 필터링 (얼굴 키포인트는 축소된 face["keypoints"] 기준)
            if not is_frontal_strict(face):
                print("[SKIP] 정면 얼굴 아님")
                continue

            # ⑦ 원본 numpy 배열로 변환 후 크롭
            img_np_orig = np.array(pil_orig)
            face_crop = crop_face_numpy(img_np_orig, (x_orig, y_orig, w_orig, h_orig))
            if face_crop.size == 0:
                print("[SKIP] 잘린 얼굴 이미지가 비어 있음")
                continue

            # ⑧ 중복 방지 (크롭된 원본 영역 해시 사용)
            try:
                cropped_bytes = pil_orig.crop((x_orig, y_orig, x_orig + w_orig, y_orig + h_orig)).tobytes()
                img_hash = hash_image(cropped_bytes)
            except Exception:
                img_hash = None

            if img_hash and (img_hash in seen_hashes):
                print("[SKIP] 중복 이미지")
                continue
            if img_hash:
                seen_hashes.add(img_hash)

            # ⑨ 원본 크롭 저장 (_full.jpg)
            face_pil_full = Image.fromarray(face_crop)
            full_name = f"{query.replace(' ', '_')}_{saved_count + 1}_full.jpg"
            full_path = os.path.join(download_path, full_name)
            try:
                face_pil_full.save(full_path, format="JPEG", quality=95)
            except Exception as e:
                print(f"[ERROR] 원본 얼굴 저장 실패: {e}")
                continue

            # ⑩ 리사이즈 버전 저장 (_resized.jpg)
            face_pil_resized = face_pil_full.resize(TARGET_FACE_SIZE, Image.LANCZOS)
            resized_name = f"{query.replace(' ', '_')}_{saved_count + 1}_resized.jpg"
            resized_path = os.path.join(download_path, resized_name)
            try:
                face_pil_resized.save(resized_path, format="JPEG", quality=90)
            except Exception as e:
                print(f"[ERROR] 리사이즈 저장 실패: {e}")

            print(f"[SAVE] 원본 크롭 → {full_path}")
            print(f"[SAVE] 리사이즈  → {resized_path}")

            saved_count += 1
            break  # 한 이미지당 한 얼굴만 저장

        if saved_count >= max_images:
            break

    driver.quit()
    print(f"[DONE] '{query}' 완료. 총 저장된 얼굴 이미지(원본/리사이즈): {saved_count}\n")


# ───────────────────────────────────────────────────────────
# 8) 메인 실행부
# ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    for cat in categories:
        folder_name = cat.replace(" ", "_")
        out_dir = os.path.join(BASE_OUTPUT_DIR, folder_name)
        download_images_bing(cat, out_dir, max_images=MAX_IMAGES_PER_CATEGORY)
