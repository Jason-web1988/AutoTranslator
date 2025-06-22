import os
import time
import requests
from collections import Counter
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont, UnidentifiedImageError
from googletrans import Translator

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from paddleocr import PaddleOCR


class AlibabaImageTranslator:
    def __init__(self, url: str):
        self.url = url
        self.download_dir = "downloaded_images"
        self.translated_dir = "translated_images"

        # macOS 내장 한글 폰트 (Apple SD Gothic Neo)
        self.font_path = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
        if not os.path.exists(self.font_path):
            raise FileNotFoundError(f"❌ 폰트 파일이 존재하지 않습니다: {self.font_path}")

        self.translator = Translator()
        self.ocr = PaddleOCR(use_angle_cls=True, lang='ch')
        self._prepare_folders()

    def _prepare_folders(self):
        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(self.translated_dir, exist_ok=True)

    def download_images(self):
        print("📥 [1단계] 상세 이미지 다운로드 중...")

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(self.url)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        imgs = soup.find_all("img")
        count = 0

        for img in imgs:
            src = img.get("src")
            if not src:
                continue
            if src.startswith("//"):
                src = "https:" + src
            if not any(ext in src.lower() for ext in [".jpg", ".jpeg", ".png"]):
                continue
            try:
                img_data = requests.get(src, timeout=5).content
                img_path = os.path.join(self.download_dir, f"image_{count}.jpg")
                with open(img_path, "wb") as f:
                    f.write(img_data)
                print(f"  ✔ 저장됨: {img_path}")
                count += 1
            except Exception as e:
                print("  ⚠️ 이미지 다운로드 실패:", e)

        driver.quit()

    def _translate_text(self, text: str) -> str:
        try:
            translated = self.translator.translate(text, src="zh-cn", dest="ko").text
            return translated
        except Exception as e:
            print("  ❌ 번역 실패:", e)
            return "[번역 오류]"

    def _get_dominant_text_color(self, img, box):
        x_min = int(min(pt[0] for pt in box))
        y_min = int(min(pt[1] for pt in box))
        x_max = int(max(pt[0] for pt in box))
        y_max = int(max(pt[1] for pt in box))

        crop = img.crop((x_min, y_min, x_max, y_max)).convert("RGB")
        pixels = crop.getdata()
        filtered_pixels = [p for p in pixels if sum(p) / 3 < 220]

        if not filtered_pixels:
            return (0, 0, 0)

        most_common = Counter(filtered_pixels).most_common(1)[0][0]
        return most_common

    def translate_images(self):
        print("\n🌐 [2단계] 이미지 내 텍스트 번역 중...")
        files = [f for f in os.listdir(self.download_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))]

        for fname in files:
            img_path = os.path.join(self.download_dir, fname)
            out_path = os.path.join(self.translated_dir, fname)

            try:
                img = Image.open(img_path).convert("RGB")
            except (UnidentifiedImageError, Exception) as e:
                print(f"  ⚠️ 이미지 손상 또는 읽기 불가: {fname} -> {e}")
                continue

            try:
                result = self.ocr.ocr(img_path, cls=True)
                if not result or not result[0]:
                    print(f"  ⏭ 텍스트 없음: {fname}")
                    continue

                draw = ImageDraw.Draw(img)

                for line in result[0]:
                    if len(line) < 2:
                        continue
                    box, (text, _) = line

                    x_min = int(min(pt[0] for pt in box))
                    y_min = int(min(pt[1] for pt in box))
                    x_max = int(max(pt[0] for pt in box))
                    y_max = int(max(pt[1] for pt in box))

                    width = x_max - x_min
                    height = y_max - y_min

                    if width < 10 or height < 10:
                        continue

                    # 텍스트 영역 배경색 계산 (덮기 용)
                    crop = img.crop((x_min, y_min, x_max, y_max)).convert("RGB")
                    pixels = crop.getdata()
                    avg_bg = tuple(
                        sum(p[i] for p in pixels) // len(pixels) for i in range(3)
                    )

                    # 기존 중국어 영역 배경색으로 덮기 (중국어 없애기)
                    draw.rectangle([x_min, y_min, x_max, y_max], fill=avg_bg)

                    # 번역된 텍스트 번역
                    translated = self._translate_text(text)

                    # 글자 색상 결정 (기존 텍스트 색상과 비슷하게)
                    text_color = self._get_dominant_text_color(img, box)

                    # 폰트 크기를 기존 텍스트 높이에 맞춤
                    font_size = max(10, int(height * 0.8))
                    font = ImageFont.truetype(self.font_path, font_size)

                    # 번역문 그리기 (약간 패딩 주기)
                    draw.text((x_min + 2, y_min + 2), translated, font=font, fill=text_color)

                img.save(out_path)
                print(f"  ✅ 번역 완료: {out_path}")

            except Exception as e:
                print(f"  ⚠️ OCR 처리 실패 ({fname}): {e}")
                continue

    def run(self):
        self.download_images()
        self.translate_images()
        print("\n🎉 모든 작업 완료! 번역된 이미지는 translated_images 폴더에 저장되었습니다.")


if __name__ == "__main__":
    product_url = input("🔗 알리바바 상품 URL을 입력하세요:\n")
    translator = AlibabaImageTranslator(product_url)
    translator.run()
