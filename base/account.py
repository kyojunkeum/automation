# base/account.py
import os

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
# 서비스 이름 (ServiceName 필드)
# ============================
SERVICE_NAME_DOORAY_BOARD_COMMENT = "두레이 게시판-댓글"
# 나중에 다른 서비스도 추가 가능
# SERVICE_NAME_NATE_MAIL = "네이트 메일"
# SERVICE_NAME_SLACK = "슬랙"