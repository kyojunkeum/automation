# base/testbasis.py
import os
from pathlib import Path

# ============================
# DLP 제품 접속 정보
# ============================
DLP_BASE_URL = os.getenv("DLP_BASE_URL", "https://172.16.150.187:8443")
DLP_ADMIN_ID = os.getenv("DLP_ADMIN_ID", "intsoosan")
DLP_ADMIN_PASSWORD = os.getenv("DLP_ADMIN_PASSWORD", "dkswjswmd4071*")

# ============================
# Dooray 접속 정보
# ============================
DOORAY_BASE_URL = os.getenv("DOORAY_BASE_URL", "https://ewalkerdlp.dooray.com")
DOORAY_ID = os.getenv("DOORAY_ID", "dlptest1")
DOORAY_PASSWORD = os.getenv("DOORAY_PASSWORD", "S@@san_1004!")

# ============================
# Elasticsearch 접속 정보
# ============================
ES_URL = os.getenv("ES_URL", "http://172.16.150.187:9200")
ES_INDEX_PATTERN = os.getenv("ES_INDEX_PATTERN", "log-*/session")

# ============================
# DLP 패턴, 키워드, 파일첨부 요소화
# ============================
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

# testbasis.py -> base -> dlp_new_automation
BASE_DIR = Path(__file__).resolve().parent.parent
# dlp_new_automation/test_files
TEST_FILES_DIR = BASE_DIR / "test_files"
# 두레이 첨부파일 2개 (상대 경로 기반)
DLP_FILES = [
    str(TEST_FILES_DIR / "pattern_keyword.pptx"),
    str(TEST_FILES_DIR / "test.jpeg"),
]

# ============================
# 서비스 이름 (ServiceName 필드)
# ============================
SERVICE_NAME_DOORAY_BOARD_COMMENT = "두레이 게시판-댓글"
# 나중에 다른 서비스도 추가 가능
# SERVICE_NAME_NATE_MAIL = "네이트 메일"
# SERVICE_NAME_SLACK = "슬랙"