import os
from pathlib import Path
import socket

def get_host_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except:
        return "127.0.0.1"
    finally:
        s.close()

HOST_IP = get_host_ip()

# PC IP -> DUT IP 매핑
DUT_MAPPING = {
    "172.16.120.59": "172.16.150.187",
    "172.16.150.124": "172.16.150.188",
    "172.16.150.131": "172.16.150.185",
    "172.16.150.132": "172.16.150.187"
}

# 기본값 지정
DUT_IP = DUT_MAPPING.get(HOST_IP, "172.16.150.187")

# 콘솔에 IP 정보 출력
print("=" * 60)
print(f"[INFO] Test Execution Host IP : {HOST_IP}")
print(f"[INFO] Selected DUT IP        : {DUT_IP}")
print("=" * 60)

# ============================
# DUT 기반 URL 정의 - DLP 제품 접속 URL
# ============================
# DLP_BASE_URL = os.getenv("DLP_BASE_URL", "https://172.16.150.187:8443")
DLP_BASE_URL = f"https://{DUT_IP}:8443"

# ============================
# Elasticsearch 접속 URL 및 인덱스
# ============================
# ES_URL = os.getenv("ES_URL", "http://172.16.150.187:9200")
ES_URL = f"http://{DUT_IP}:9200"
ES_INDEX_PATTERN = os.getenv("ES_INDEX_PATTERN", "log-*/session")

# ============================
# allure Test Server 접속 URL
# ============================
ALLURE_IP = os.getenv("ALLURE_IP", "172.16.150.138")

# ============================
# 서비스 이름 (메일)
# ============================
SERVICE_NAME_DOORAY_MAIL_KO = "두레이 메일"
SERVICE_NAME_DOORAY_MAIL_EN = "Dooray"
SERVICE_NAMES_DOORAY_MAIL = [
    SERVICE_NAME_DOORAY_MAIL_KO,
    SERVICE_NAME_DOORAY_MAIL_EN,
]

SERVICE_NAME_NATE_MAIL_KO = "네이트메일"
SERVICE_NAME_NATE_MAIL_EN = "Nate"
SERVICE_NAMES_NATE_MAIL = [
    SERVICE_NAME_NATE_MAIL_KO,
    SERVICE_NAME_NATE_MAIL_EN,
]

SERVICE_NAME_DAUM_MAIL_KO = "다음메일"
SERVICE_NAME_DAUM_MAIL_EN = "Daum"
SERVICE_NAMES_DAUM_MAIL = [
    SERVICE_NAME_DAUM_MAIL_KO,
    SERVICE_NAME_DAUM_MAIL_EN,
]

SERVICE_NAME_OUTLOOK_MAIL_KO = "Outlook메일"
SERVICE_NAME_OUTLOOK_MAIL_EN = "Outlook"
SERVICE_NAMES_OUTLOOK_MAIL = [
    SERVICE_NAME_OUTLOOK_MAIL_KO,
    SERVICE_NAME_OUTLOOK_MAIL_EN,
]


# ============================
# 서비스 이름 (SNS)
# ============================
SERVICE_NAME_DOORAY_BOARD_KO = "두레이 게시판"
SERVICE_NAME_DOORAY_BOARD_EN = "Doorey Board"
SERVICE_NAMES_DOORAY_BOARD = [
    SERVICE_NAME_DOORAY_BOARD_KO,
    SERVICE_NAME_DOORAY_BOARD_EN,
]

SERVICE_NAME_DOORAY_CALENDAR_KO = "두레이 캘린더"
SERVICE_NAME_DOORAY_CALENDAR_EN = "Doorey Calendar"
SERVICE_NAMES_DOORAY_CALENDAR = [
    SERVICE_NAME_DOORAY_CALENDAR_KO,
    SERVICE_NAME_DOORAY_CALENDAR_EN,
]

SERVICE_NAME_NAVERWORKS_BOARD_KO = "네이버웍스 게시판"
SERVICE_NAME_NAVERWORKS_BOARD_EN = "NaverWorks Board"
SERVICE_NAMES_NAVERWORKS_BOARD = [
    SERVICE_NAME_NAVERWORKS_BOARD_KO,
    SERVICE_NAME_NAVERWORKS_BOARD_EN,
]

SERVICE_NAME_NAVERWORKS_CALENDAR_KO = "네이버웍스 캘린더"
SERVICE_NAME_NAVERWORKS_CALENDAR_EN = "NaverWorks Calendar"
SERVICE_NAMES_NAVERWORKS_CALENDAR = [
    SERVICE_NAME_NAVERWORKS_CALENDAR_KO,
    SERVICE_NAME_NAVERWORKS_CALENDAR_EN,
]

# ============================
# 서비스 이름 (COMMENT)
# ============================
SERVICE_NAME_DOORAY_BOARD_COMMENT_KO = "두레이 게시판-댓글"
SERVICE_NAME_DOORAY_BOARD_COMMENT_EN = "Doorey Board"
SERVICE_NAMES_DOORAY_BOARD_COMMENT = [
    SERVICE_NAME_DOORAY_BOARD_COMMENT_KO,
    SERVICE_NAME_DOORAY_BOARD_COMMENT_EN,
]

# ============================
# 서비스 이름 (WEBHARD)
# ============================
SERVICE_NAME_DOORAY_DRIVE_KO = "두레이 드라이브"
SERVICE_NAME_DOORAY_DRIVE_EN = "Doorey Drive"
SERVICE_NAMES_DOORAY_DRIVE = [
    SERVICE_NAME_DOORAY_DRIVE_KO,
    SERVICE_NAME_DOORAY_DRIVE_EN,
]


# ============================
# 서비스별 접속 URL
# ============================
DOORAY_BASE_URL = os.getenv("DOORAY_BASE_URL", "https://ewalkerdlp.dooray.com")
NATE_BASE_URL = os.getenv("NATE_BASE_URL", "https://www.nate.com")
NATE_MAIL_URL = os.getenv("NATE_MAIL_URL", "https://mail3.nate.com")
DAUM_BASE_URL = os.getenv("DAUM_BASE_URL", "https://www.daum.net")
DAUM_MAIL_URL = os.getenv("DAUM_MAIL_URL", "https://mail.daum.net")
OUTLOOK_BASE_URL = os.getenv("OUTLOOK_BASE_URL", "https://outlook.office.com")
OUTLOOK_MAIL_URL = os.getenv("OUTLOOK_MAIL_URL", "https://outlook.live.com/mail/0/")
NAVERWORKS_BASE_URL = os.getenv("NAVERWORKS_BASE_URL", "https://naver.worksmobile.com")
NAVERWORKS_BOARD_URL = os.getenv("NAVERWORKS_BOARD_URL", "https://board.worksmobile.com")
NAVERWORKS_CALENDAR_URL = os.getenv("NAVERWORKS_CALENDAR_URL", "https://calendar.worksmobile.com")
# YAHOO_BASE_URL = os.getenv("YAHOO_BASE_URL", "https://mail.yahoo.com") 홈페이지 자동화 브라우저로 로그인 시 사용 불가
# ============================
# DLP 패턴, 키워드, 파일첨부 요소화
# ============================
# 일반 로깅 테스트 값들
DLP_NORMAL = [
    "기본로깅테스트",
    "Basic Logging Test",
]

# 패턴 테스트 값들 (개인정보, 민감정보, 계좌번호 등)
DLP_PATTERNS = [
    "950621-1554381",
    "02-750-0901",
    "010-8212-4071",
    "192.168.0.121",
    "kjkeum@soosan.co.kr",
    "216502-04-268317",
    "KR7726840",
    "D58493043",
    "경기00-852223-51",
    "4221-5500-1007-2121",
    "751214-5265498",
    "207-81-51341",
    "110111-1518830",
    "81233745079",
]

# 키워드 테스트 값들
# 키워드 로깅 테스트
DLP_KEYWORDS = [
    "키워드테스트",
    "일지매",
    "일지매",
    "일지매",
    "수산아이앤티",
    "수산아이앤티",
]

# account.py -> base -> dlp_new_automation
BASE_DIR = Path(__file__).resolve().parent.parent
# dlp_new_automation/test_files
TEST_FILES_DIR = BASE_DIR / "test_files"

# 두레이 첨부파일 1개 일반 (상대 경로 기반)
DLP_FILE = [
    str(TEST_FILES_DIR / "test.jpeg"),
]

DLP_FILE_PATTERN = [
    str(TEST_FILES_DIR / "pattern.docx")
]

DLP_FILE_KEYWORD = [
    str(TEST_FILES_DIR / "keyword_test.docx")
]

DLP_FILE_MIX = [
    str(TEST_FILES_DIR / "pattern_keyword.pptx")
]


# 두레이 첨부파일 2개 (상대 경로 기반)
DLP_FILES = [
    str(TEST_FILES_DIR / "test.jpeg"),
    str(TEST_FILES_DIR / "evernote.pdf"),
]




