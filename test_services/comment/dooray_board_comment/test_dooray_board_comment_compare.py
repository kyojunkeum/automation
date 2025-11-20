import os
import time
from datetime import datetime

import allure
import pytest
from playwright.sync_api import sync_playwright,BrowserContext,TimeoutError

import requests

ES_URL = "http://172.16.150.187:9200"
# 월이 바뀌어도 log-2025-12, log-2026-01 ... 전부 포함
ES_INDEX_PATTERN = "log-*/session"
DOORAY_SERVICE_NAME = "두레이 게시판-댓글"   # 실제 ServiceName 값

def get_screenshot_path(test_name):
    screenshot_dir = os.path.join(os.getcwd(), "report", "screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(screenshot_dir, f"{test_name}_failed_{timestamp}.jpg")
    # return os.path.join(screenshot_dir, f"{test_name}_failed_{timestamp}.png")

def click_confirm_if_popup_exists(page, timeout=3000):
    """
    '확인' 버튼을 가진 팝업이 뜨면 해당 버튼을 찾아 클릭한다.
    나타나지 않으면(TimeoutError) 아무 처리도 하지 않는다.
    """
    try:
        page.wait_for_selector("role=button[name='확인']", timeout=timeout)
        page.get_by_role("button", name="확인").click()
        print("알림 팝업의 '확인' 버튼을 클릭했습니다.")
    except TimeoutError:
        print("알림 팝업(확인 버튼)이 나타나지 않았습니다.")

def search_dooray_logs_from_es(size: int = 10):
    """
    ES에서 두레이 게시판-댓글 로그를 최근순으로 조회한다.
    ServiceName 기준 필터 + @timestamp 내림차순 정렬.
    """
    query = {
        "query": {
            "bool": {
                "must": [
                    # keyword 필드가 아니라 ServiceName 자체가 keyword 타입이므로 그대로 사용
                    {"term": {"ServiceName": DOORAY_SERVICE_NAME}}
                ]
            }
        },
        "sort": [
            {"@timestamp": {"order": "desc"}}
        ],
        "size": size
    }

    resp = requests.get(
        f"{ES_URL}/{ES_INDEX_PATTERN}/_search",
        json=query,
        timeout=10
    )
    resp.raise_for_status()
    data = resp.json()
    return data["hits"]["hits"]  # 각 hit: {"_index", "_type", "_id", "_source", ...}


def extract_counts_from_es_source(src: dict):
    # 패턴 카운트
    pattern_total = 0
    if isinstance(src.get("PatternParsedInfo"), dict):
        pattern_total += src["PatternParsedInfo"].get("total", 0)

    # 필요하면 예외/인코딩 패턴까지 합산
    for key in ("EncodePatternParsedInfo", "EncodeExceptionPatternParsedInfo", "ExceptionPatternParsedInfo"):
        if isinstance(src.get(key), dict):
            pattern_total += src[key].get("total", 0)

    # 키워드 카운트
    keyword_total = 0
    if isinstance(src.get("KeywordParsedInfo"), dict):
        # ① 전체 매칭 수 (지금 예시: 6)
        keyword_total = src["KeywordParsedInfo"].get("total", 0)
        # ② 키워드 종류 개수로 쓰고 싶으면 아래로 교체
        # keyword_total = len(src["KeywordParsedInfo"].get("parse", []))

    # 첨부파일 카운트
    file_total = int(src.get("SendFileCount", 0))

    return str(pattern_total), str(keyword_total), str(file_total)


def compare_es_and_values(doc: dict, expected: dict):
    """
    기존 compare_ui_and_values(page, row_index, expected) 와 동일 컨셉.
    - doc: ES hit 하나 ({"_source": {...}} 형태)
    - expected: {"pattern_count": "0", "keyword_count": "0", "file_count": "0"} 형태
    """
    src = doc.get("_source", {})

    pattern_count, keyword_count, file_count = extract_counts_from_es_source(src)

    exp_pattern = expected["pattern_count"]
    exp_keyword = expected["keyword_count"]
    exp_file = expected["file_count"]

    assert pattern_count == exp_pattern, \
        f"pattern_count mismatch: expected={exp_pattern}, actual={pattern_count}, MessageID={src.get('MessageID')}"
    assert keyword_count == exp_keyword, \
        f"keyword_count mismatch: expected={exp_keyword}, actual={keyword_count}, MessageID={src.get('MessageID')}"
    assert file_count == exp_file, \
        f"file_count mismatch: expected={exp_file}, actual={file_count}, MessageID={src.get('MessageID')}"


# ===== 여기부터 ES 기반 테스트 =====


def compare_result_dooray_board_comment_es():
    """
    ES(log-*/session)에서 두레이 게시판-댓글 로그를 조회하여
    패턴/키워드/파일 카운트가 기대값과 일치하는지 검증한다.
    """
    # ES에서 최근 10건 가져오기 (필요 시 조정 가능)
    hits = search_dooray_logs_from_es(size=10)

    test_cases = [
        {
            "hit_index": 9,
            "label": "일반 로깅",
            "expected": {"pattern_count": "0", "keyword_count": "0", "file_count": "0"},
        },
        {
            "hit_index": 7,
            "label": "개인정보 로깅",
            "expected": {"pattern_count": "2", "keyword_count": "0", "file_count": "0"},
        },
        {
            "hit_index": 3,
            "label": "키워드 로깅",
            "expected": {"pattern_count": "0", "keyword_count": "2", "file_count": "0"},
        },
        # {
        #     "hit_index": 1,
        #     "label": "첨부파일 로깅",
        #     "expected": {"pattern_count": "14", "keyword_count": "0", "file_count": "1"},
        # },
    ]

    assert len(hits) >= 4, f"ES 검색 결과가 4건 미만입니다. hits={len(hits)}"

    for case in test_cases:
        idx = case["hit_index"]
        label = case["label"]
        expected = case["expected"]

        assert idx < len(hits), f"{label} 테스트를 위한 hit_index={idx} 가 ES 결과 범위를 벗어났습니다. hits={len(hits)}"

        with allure.step(f"ES hit_index={idx} ({label}) 검증"):
            compare_es_and_values(hits[idx], expected)

@allure.severity(allure.severity_level.TRIVIAL)
@allure.step("Dooray Login Test")
def test_dooray_login():
    with sync_playwright() as p:
        # 브라우저 및 컨텍스트 생성
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            # 두레이 홈페이지 진입
            page.goto("https://ewalkerdlp.dooray.com/")
            time.sleep(1)

            # 아이디 및 패스워드 입력
            page.get_by_placeholder("아이디").click()
            page.get_by_placeholder("아이디").fill("dlptest1")
            page.get_by_placeholder("비밀번호").click()
            page.get_by_placeholder("비밀번호").fill("S@@san_1004!")
            time.sleep(1)
            page.get_by_role("button", name="로그인").click()
            time.sleep(3)

            # # 로그인 성공 여부 확인
            # page.get_by_test_id("MyLoginProfileLayer").locator("img").click()
            # page.locator("#tippy-7").get_by_text("dlptest1").click()
            # page.wait_for_selector("role=link[name='dlptest1']", timeout=3000)
            # assert page.get_by_role("link", name="dlptest1").is_visible() == True, "login failed. can't find the profile."
            # time.sleep(2)

            # 세션 상태 저장
            os.makedirs("session", exist_ok=True)
            session_path = os.path.join("session", "dooraystorageState.json")
            context.storage_state(path=session_path)

        except Exception as e:
            # # 실패 시 스크린샷 경로 설정
            # screenshot_path = get_screenshot_path("test_nate_login")  # 공통 함수 호출
            # page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # # page.screenshot(path=screenshot_path, full_page=True)
            # print(f"Screenshot taken at : {screenshot_path}")
            # allure.attach.file(screenshot_path, name="login_failure_screenshot", attachment_type=allure.attachment_type.JPG)


            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.NORMAL)
@allure.step("Dooray board Comment normal Test")
def test_dooray_normal_board_comment(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "dooraystorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메일 페이지로 이동
            page.goto("https://ewalkerdlp.dooray.com/home")

            # 자유게시판으로 이동
            page.get_by_role("link", name="자유게시판").click()

            # 가장 위에 게시글 클릭
            page.locator("div[role='gridcell']").nth(2).click()
            # page.get_by_role("gridcell", name="기본로깅테스트 [4]").click()

            # 댓글창 클릭
            comment_box = page.locator("div.dooray-flavored-html-editor-content-editable[contenteditable='true']")
            comment_box.click()
            # 혹시 기존 내용이 있으면 지우고
            comment_box.press("Control+A")
            comment_box.press("Delete")
            # 댓글 입력
            comment_box.fill("기본댓글로깅테스트")

            # 저장 클릭
            page.get_by_role("button", name="저장").click()

            # 3초 대기
            page.wait_for_timeout(3000)

        except Exception as e:
            # # 실패 시 스크린샷 경로 설정
            # screenshot_path = get_screenshot_path("test_nate_normal_send")  # 공통 함수 호출
            # page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # # page.screenshot(path=screenshot_path, full_page=True)
            # print(f"Screenshot taken at : {screenshot_path}")
            # allure.attach.file(screenshot_path, name="nate_normal_send_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Dooray board comment Pattern Test")
def test_dooray_pattern_board_comment(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "dooraystorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메일 페이지로 이동
            page.goto("https://ewalkerdlp.dooray.com/home")

            # 자유게시판으로 이동
            page.get_by_role("link", name="자유게시판").click()

            # 가장 위에 게시글 클릭
            page.locator("div[role='gridcell']").nth(2).click()

            # 댓글창 클릭
            comment_box = page.locator("div.dooray-flavored-html-editor-content-editable[contenteditable='true']")
            comment_box.click()
            # 혹시 기존 내용이 있으면 지우고
            comment_box.press("Control+A")
            comment_box.press("Delete")
            # 댓글 입력
            comment_box.fill("kjkeum@nate.com")

            # 저장 클릭
            page.get_by_role("button", name="저장").click()

            # 3초 대기
            page.wait_for_timeout(3000)

            # # 보내기 성공 여부 확인
            # page.wait_for_selector("text=관리자에 의해 차단되었습니다. 관리자에 문의 하세요", timeout=3000)
            # assert page.locator("text=관리자에 의해 차단되었습니다. 관리자에 문의 하세요").is_visible() == True, "failed to block."
            # page.wait_for_timeout(2000)  # 2초 대기 (time.sleep 대신 사용)

        except Exception as e:
            # # 실패 시 스크린샷 경로 설정
            # screenshot_path = get_screenshot_path("test_nate_pattern_send")  # 공통 함수 호출
            # page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # # page.screenshot(path=screenshot_path, full_page=True)
            # print(f"Screenshot taken at : {screenshot_path}")
            # allure.attach.file(screenshot_path, name="nate_pattern_send_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Dooray board comment Keyword Send Test")
def test_dooray_keyword_board_comment(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "dooraystorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메일 페이지로 이동
            page.goto("https://ewalkerdlp.dooray.com/home")

            # 자유게시판으로 이동
            page.get_by_role("link", name="자유게시판").click()

            # 가장 위에 게시글 클릭
            page.locator("div[role='gridcell']").nth(2).click()

            # 댓글창 클릭
            comment_box = page.locator("div.dooray-flavored-html-editor-content-editable[contenteditable='true']")
            comment_box.click()
            # 혹시 기존 내용이 있으면 지우고
            comment_box.press("Control+A")
            comment_box.press("Delete")
            # 댓글 입력
            comment_box.fill("키워드테스트키워드테스트일지매일지매일지매수산아이앤티")

            # 저장 클릭
            page.get_by_role("button", name="저장").click()

            # 3초 대기
            page.wait_for_timeout(3000)

            # # 보내기 성공 여부 확인
            # page.wait_for_selector("text=관리자에 의해 차단되었습니다. 관리자에 문의 하세요", timeout=3000)
            # assert page.locator("text=관리자에 의해 차단되었습니다. 관리자에 문의 하세요").is_visible() == True, "failed to block."
            # page.wait_for_timeout(2000)  # 2초 대기

        except Exception as e:
            # # 실패 시 스크린샷 경로 설정
            # screenshot_path = get_screenshot_path("test_nate_keyword_send")
            # page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # # page.screenshot(path=screenshot_path, full_page=True)
            # print(f"Screenshot taken at : {screenshot_path}")
            # allure.attach.file(screenshot_path, name="nate_keyword_send_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

# @allure.severity(allure.severity_level.BLOCKER)
# @allure.step("Dooray board comment attach Test")
# def stest_dooray_attach_board_comment(request):
#     with sync_playwright() as p:
#         # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
#         session_path = os.path.join("session", "dooraystorageState.json")
#         browser = p.chromium.launch(headless=False)
#         context = browser.new_context(storage_state=session_path)
#         page = context.new_page()
#
#         try:
#
#             # 세션 유지한 채로 메일 페이지로 이동
#             page.goto("https://ewalkerdlp.dooray.com/home")
#
#             # 자유게시판으로 이동
#             page.get_by_role("link", name="자유게시판").click()
#
#             # 가장 위에 게시글 클릭
#             page.locator("div[role='gridcell']").nth(2).click()
#
#             # 파일 첨부
#             with page.expect_file_chooser() as fc_info:
#                 page.get_by_role("button", name="첨부").click()
#             file_chooser = fc_info.value
#             file_chooser.set_files(r"D:/backup/dlp_new_automation/test_files/pattern.docx")
#
#             # # 저장 클릭
#             # page.get_by_role("button", name="저장").click()
#
#             # # 저장 클릭
#             # page.get_by_test_id("HomeBoardArticleEditorSaveButton_ButtonComponent").click()
#
#             # 3초 대기
#             page.wait_for_timeout(3000)
#
#             # # 보내기 성공 여부 확인
#             # page.wait_for_selector("text=관리자에 의해 차단되었습니다. 관리자에 문의 하세요", timeout=3000)
#             # assert page.locator("text=관리자에 의해 차단되었습니다. 관리자에 문의 하세요").is_visible() == True, "failed to block."
#             # page.wait_for_timeout(2000)  # 2초 대기
#
#         except Exception as e:
#             # # 실패 시 스크린샷 경로 설정
#             # screenshot_path = get_screenshot_path("test_nate_attach_send")  # 공통 함수 호출
#             # page.screenshot(path=screenshot_path, type="jpeg", quality=80)
#             # # page.screenshot(path=screenshot_path, full_page=True)
#             # print(f"Screenshot taken at : {screenshot_path}")
#             # allure.attach.file(screenshot_path, name="nate_attach_send_failure_screenshot", attachment_type=allure.attachment_type.JPG)
#
#             # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
#             pytest.fail(f"Test failed: {str(e)}")
#
#
#         finally:
#             browser.close()

# def compare_ui_and_values(page, row_index, expected_counts):
#     """
#     UI 데이터와 values 를 비교하는 함수
#     :param page: Playwright Page 객체
#     :param row_index: 비교할 행 번호 (1부터 시작)
#     :param expected_counts: 딕셔너리 형태의 기대 값
#     """
#     row_selector = f"table tr:nth-child({row_index})"
#     ui_pattern_count = page.locator(f"{row_selector} td:nth-child(11)").text_content().strip()
#     ui_keyword_count = page.locator(f"{row_selector} td:nth-child(12)").text_content().strip()
#     ui_file_count = page.locator(f"{row_selector} td:nth-child(13)").text_content().strip()
#
#     assert expected_counts["pattern_count"] == ui_pattern_count, \
#         f"패턴 검출수 불일치: 기대값({expected_counts['pattern_count']}) != UI({ui_pattern_count})"
#     assert expected_counts["keyword_count"] == ui_keyword_count, \
#         f"키워드 검출수 불일치: 기대값({expected_counts['keyword_count']}) != UI({ui_keyword_count})"
#     assert expected_counts["file_count"] == ui_file_count, \
#         f"파일 개수 불일치: 기대값({expected_counts['file_count']}) != UI({ui_file_count})"
#
# @allure.severity(allure.severity_level.CRITICAL)
# @allure.step("Dooray board comment Dlp Logging check")
# def stest_compare_result_dooray_board_comment():
#     with sync_playwright() as p:
#         # 브라우저 실행
#         browser = p.chromium.launch(headless=False)
#
#         # BrowserContext 생성 (HTTPS 오류 무시 설정)
#         context = browser.new_context(ignore_https_errors=True)
#
#         # Context에서 새로운 페이지 생성
#         page = context.new_page()
#
#         try:
#
#             # DLP 서비스 로그인
#             page.goto("https://172.16.150.187:8443/login")  # DLP 제품 URL
#             page.fill("input[name='j_username']", "intsoosan")
#             page.fill("input[name='j_password']", "dkswjswmd4071*")
#             page.get_by_role("button", name="LOGIN").click()
#             time.sleep(2)
#
#             # 알림 팝업 처리
#             click_confirm_if_popup_exists(page, timeout=5000)
#
#             # 서비스 로그 페이지로 이동
#             page.goto("https://172.16.150.187:8443/log/service")
#
#             # 상세 검색
#             page.get_by_role("link", name="상세검색").click()
#             time.sleep(1)
#             # 서비스 선택
#             page.locator("#selectedDetail").select_option("service")
#             # 두레이게시판 선택
#             page.locator("#tokenfield2-tokenfield").click()
#             page.get_by_text("[SNS] 두레이 게시판").click()
#             # 검색 클릭
#             page.get_by_role("button", name="검색").click()
#             time.sleep(5)
#
#             # 딕셔너리 기댓값과 UI 데이터를 비교
#             test_cases = [
#                 {"row_index": 7, "expected": {"pattern_count": "0", "keyword_count": "0", "file_count": "0"}},  # 일반 로깅
#                 {"row_index": 5, "expected": {"pattern_count": "1", "keyword_count": "0", "file_count": "0"}},  # 개인정보 로깅
#                 {"row_index": 3, "expected": {"pattern_count": "0", "keyword_count": "2", "file_count": "0"}},  # 키워드 로깅
#                 {"row_index": 1, "expected": {"pattern_count": "14", "keyword_count": "0", "file_count": "1"}},  # 첨부파일 로깅
#             ]
#
#             for case in test_cases:
#                 compare_ui_and_values(page, case["row_index"], case["expected"])
#
#             print("모든 값이 일치합니다.")
#
#
#         except Exception as e:
#
#             # 실패 시 스크린샷 저장
#             # 실패 시 스크린샷 경로 설정
#             screenshot_path = get_screenshot_path("test_dooray_board_comment")  # 공통 함수 호출
#             page.screenshot(path=screenshot_path, type="jpeg", quality=80)
#             # page.screenshot(path=screenshot_path, full_page=True)
#             print(f"Screenshot taken at : {screenshot_path}")
#             allure.attach.file(screenshot_path, name="dooray_board_comment_failure_screenshot",
#                                attachment_type=allure.attachment_type.JPG)
#
#             raise
#
#         finally:
#             browser.close()




# def debug_print_dooray_es_hits():
#     hits = search_dooray_logs_from_es(size=10)
#     for i, doc in enumerate(hits):
#         src = doc["_source"]
#         pat, key, file_ = extract_counts_from_es_source(src)
#
#         print("=" * 60)
#         print(f"hit_index={i}")
#         print(f"@timestamp     = {src.get('@timestamp')}")
#         print(f"RuleName       = {src.get('RuleName')}")
#         print(f"ResultName     = {src.get('ResultName')}")
#         print(f"ServiceName    = {src.get('ServiceName')}")
#         print(f"pattern_count  = {pat}")
#         print(f"keyword_count  = {key}")
#         print(f"file_count     = {file_}")
#         print(f"MessageID      = {src.get('MessageID')}")