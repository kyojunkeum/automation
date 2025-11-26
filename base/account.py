import os

# ============================
# DLP 제품 접속 정보
# ============================
DLP_ADMIN_ID = os.getenv("DLP_ADMIN_ID", "intsoosan")
DLP_ADMIN_PASSWORD = os.getenv("DLP_ADMIN_PASSWORD", "dkswjswmd4071*")

# ============================
# Elasticsearch 접속 정보
# ============================
# server_config 에 포함됨, 추후 ID/PW 정보 추가되면 이곳에 추가!

# ============================
# allure Test Server 접속 정보
# ============================
ALLURE_ID = os.getenv("ALLURE_ID", "root")
ALLURE_PASSWORD = os.getenv("ALLURE_PASSWORD", "dkswjswmd138*")


# ============================
# 테스트 메일 수신자 이메일
# ============================
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", "soosan_kjkeum@nate.com")

# ============================
# Dooray 접속 정보
# ============================
DOORAY_ID = os.getenv("DOORAY_ID", "dlptest1")
DOORAY_PASSWORD = os.getenv("DOORAY_PASSWORD", "S@@san_1004!")

# ============================
# NATE_MAIL 접속 정보
# ============================
NATE_ID = os.getenv("NATE_ID", "soosan_kjkeum")
NATE_PASSWORD = os.getenv("NATE_PASSWORD", "iwilltakeyou02@")

# ============================
# DAUM_MAIL 접속 정보
# ============================
DAUM_ID = os.getenv("DAUM_ID", "soosan_kjkeum@naver.com")
DAUM_PASSWORD = os.getenv("DAUM_PASSWORD", "iwilltakeyou01!")

# ============================
# YAHOO_MAIL 접속 정보
# ============================
# YAHOO_ID = os.getenv("YAHOO_ID", "soosan_kjkeum")
# YAHOO_PASSWORD = os.getenv("YAHOO_PASSWORD", "iwilltakeyou01!")

# ============================
# OUTLOOK_MAIL (브라우저) 접속 정보
# ============================
OUTLOOK_ID = os.getenv("OUTLOOK_ID", "soosan_kjkeum@naver.com")
OUTLOOK_PASSWORD = os.getenv("OUTLOOK_PASSWORD", "iwilltakeyou01!")
