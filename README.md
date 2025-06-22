# AutoTranslator
1. 개발 환경
운영체제
macOS (m1기반)

주요 라이브러리 및 프레임워크
paddleocr: OCR(문자 인식) 엔진, 중국어 감지용

googletrans: 구글 번역 API 비공식 버전

selenium: 이미지 다운로드를 위한 웹 자동화

beautifulsoup4, requests: HTML 파싱 및 이미지 요청

Pillow (PIL): 이미지 처리

chromedriver + webdriver-manager: 크롬 브라우저 자동 제어

2. 필수 설치 명령어
Python 설치 확인
bash
복사
편집
python3 --version
가상환경 생성 및 진입 (권장)
bash
복사
편집
python3 -m venv venv
source venv/bin/activate
필수 라이브러리 설치
bash
복사
편집
pip install paddleocr
pip install "paddlepaddle==2.5.1" -f https://paddlepaddle.org.cn/whl/macos.html  # Apple Silicon용
pip install googletrans==4.0.0rc1
pip install selenium beautifulsoup4 requests pillow webdriver-manager
⚠️ 주의:

paddleocr 설치 시 CPU/GPU, macOS/Windows 환경에 따라 paddlepaddle 버전 달라질 수 있음.

macOS에서 AppleSDGothicNeo.ttc 폰트를 기본으로 사용함.

3. 작동 방식 요약
1단계: 상세 이미지 다운로드
Selenium으로 알리바바 상품 페이지 진입

img 태그에서 .jpg, .png 확장자 이미지 주소 추출

이미지 요청하여 downloaded_images 폴더에 저장

2단계: 이미지 번역
각 이미지에 대해 PaddleOCR로 텍스트 영역 감지

각 텍스트에 대해:

중국어 삭제: 텍스트 박스 영역을 배경색으로 덮음

한국어 번역: googletrans를 사용해 번역

번역된 문장 삽입:

글자 크기는 감지된 텍스트 높이에 비례

글자 색은 원래 텍스트 색상과 유사하게 설정

폰트는 macOS 기본 폰트(AppleSDGothicNeo.ttc) 사용

최종 결과
번역된 이미지는 translated_images 폴더에 저장

4. 발생했던 주요 이슈 및 해결 방법
문제	설명	해결 방법
googletrans 번역 실패	구글 차단, 요청 과도	짧은 텍스트 단위로 분할, 오류 무시
OCR 결과가 틀림	각도 있는 글자 감지 오류	use_angle_cls=True 설정
글자 위에 그대로 한국어 씀	중국어가 안 지워짐	→ 텍스트 박스를 배경색으로 덮고 다시 그림
배경색이 어색하게 덮임	중국어 영역 지움 후 얼룩	해당 박스의 평균 배경색을 추출해서 덮기
폰트 깨짐	Windows나 mac에서 폰트 경로 다름	macOS 내장 폰트(AppleSDGothicNeo.ttc) 지정
번역글자 크기 안 맞음	OCR 글자 크기 추정 어려움	박스 높이 기준으로 폰트 크기 설정

5. 전체 기능 소스 구조
AlibabaImageTranslator 클래스 중심

__init__: 초기 설정, 폴더 준비, OCR/번역 초기화

download_images: 이미지 수집

translate_images: OCR → 번역 → 이미지 처리

_translate_text: 구글 번역 처리

_get_dominant_text_color: 원래 텍스트 색상 추정

run: 전체 파이프라인 실행

6. 최종 코드 주요 특징
기존 중국어 완전히 제거 (박스 배경색으로 덮음)

번역문 같은 위치, 같은 크기, 유사한 색상으로 표시

OCR 텍스트 감지 박스는 투명 (테두리 없음)

번역 실패 시 [번역 오류]로 표기

너무 작거나 왜곡된 텍스트는 무시

7. 사용법
bash
복사
편집
python alibaba_translator.py
실행 후 아래처럼 입력:
---------------------------------------------
ex)
🔗 알리바바 상품 URL을 입력하세요:
https://detail.1688.com/offer/123456789.html
