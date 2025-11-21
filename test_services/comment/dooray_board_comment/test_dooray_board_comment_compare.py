import os
import time
from datetime import datetime

import allure
import pytest
from playwright.sync_api import sync_playwright,TimeoutError

from base.testbasis import (
    DOORAY_BASE_URL,
    DOORAY_ID,
    DOORAY_PASSWORD,
    DLP_PATTERNS,
    DLP_KEYWORDS,
    DLP_FILES,
    SERVICE_NAME_DOORAY_BOARD_COMMENT,
)
from base.function import assert_es_logs, assert_es_logs_with_retry

NORMAL_LOGGING_CASE = [
    {
        "hit_index": 0,
        "label": "기본 로깅",
        "expected": {"pattern_count": "0", "keyword_count": "0", "file_count": "0"},
    }
]

PATTERN_LOGGING_CASE = [
    {
        "hit_index": 0,
        "label": "패턴 로깅",
        "expected": {"pattern_count": "14", "keyword_count": "0", "file_count": "0"},
    }
]

KEYWORD_LOGGING_CASE = [
    {
        "hit_index": 0,
        "label": "키워드 로깅",
        "expected": {"pattern_count": "0", "keyword_count": "6", "file_count": "0"},
    }
]

FILE_LOGGING_CASE = [
    {
        "hit_index": 0,
        "label": "파일 로깅",
        "expected": {"pattern_count": "3", "keyword_count": "3", "file_count": "2"},
    }
]

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
            page.goto(f"{DOORAY_BASE_URL}/")
            time.sleep(1)

            # 아이디 및 패스워드 입력
            page.get_by_placeholder("아이디").click()
            page.get_by_placeholder("아이디").fill(DOORAY_ID)
            page.get_by_placeholder("비밀번호").click()
            page.get_by_placeholder("비밀번호").fill(DOORAY_PASSWORD)
            time.sleep(1)
            page.get_by_role("button", name="로그인").click()
            time.sleep(3)

            # 세션 상태 저장
            os.makedirs("session", exist_ok=True)
            session_path = os.path.join("session", "dooraystorageState.json")
            context.storage_state(path=session_path)

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_dooray_login")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="dooray_login_failure_screenshot", attachment_type=allure.attachment_type.JPG)


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
            page.goto(f"{DOORAY_BASE_URL}/home")

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

            # 5초 대기
            page.wait_for_timeout(5000)

            # # ===== 여기서 ES 검증 호출 =====
            # assert_es_logs(
            #     service_name=SERVICE_NAME_DOORAY_BOARD_COMMENT,
            #     test_cases=NORMAL_LOGGING_CASE,
            #     size=1,
            # )

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAME_DOORAY_BOARD_COMMENT,
                test_cases=NORMAL_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_dooray_board_comment_normal_send")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="dooray_board_comment_normal_send_failure_screenshot", attachment_type=allure.attachment_type.JPG)

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
            page.goto(f"{DOORAY_BASE_URL}/home")

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
            comment_box.fill("\n".join(DLP_PATTERNS))

            # 저장 클릭
            page.get_by_role("button", name="저장").click()

            # 3초 대기
            page.wait_for_timeout(5000)

            # # ===== 여기서 ES 검증 호출 =====
            # assert_es_logs(
            #     service_name=SERVICE_NAME_DOORAY_BOARD_COMMENT,
            #     test_cases=PATTERN_LOGGING_CASE,
            #     size=1,
            # )

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAME_DOORAY_BOARD_COMMENT,
                test_cases=PATTERN_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )


        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_dooray_board_comment__pattern_send")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="dooray_board_comment_pattern_send_failure_screenshot", attachment_type=allure.attachment_type.JPG)

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
            page.goto(f"{DOORAY_BASE_URL}/home")

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
            comment_box.fill("\n".join(DLP_KEYWORDS))

            # 저장 클릭
            page.get_by_role("button", name="저장").click()

            # 3초 대기
            page.wait_for_timeout(5000)

            # # ===== 여기서 ES 검증 호출 =====
            # assert_es_logs(
            #     service_name=SERVICE_NAME_DOORAY_BOARD_COMMENT,
            #     test_cases=KEYWORD_LOGGING_CASE,
            #     size=1,
            # )

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAME_DOORAY_BOARD_COMMENT,
                test_cases=KEYWORD_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_dooray_board_comment_keyword_send")
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="dooray_board_comment_keyword_send_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.BLOCKER)
@allure.step("Dooray board comment attach Test")
def stest_dooray_attach_board_comment(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "dooraystorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메일 페이지로 이동
            page.goto(f"{DOORAY_BASE_URL}/home")

            # 자유게시판으로 이동
            page.get_by_role("link", name="자유게시판").click()

            # 가장 위에 게시글 클릭
            page.locator("div[role='gridcell']").nth(2).click()

            # 스크롤하여 첨부 버튼을 보이게 하기
            page.get_by_role("button", name="첨부").scroll_into_view_if_needed()

            # 파일 첨부
            with page.expect_file_chooser() as fc_info:
                page.get_by_role("button", name="첨부").click()
            file_chooser = fc_info.value
            # # 한 개 파일
            # file_chooser.set_files(r"D:/backup/dlp_new_automation/test_files/pattern.docx")

            # 수정: 요소화 + 여러 파일(2개) 첨부
            file_chooser.set_files(DLP_FILES)


            # # 저장 클릭
            # page.get_by_role("button", name="저장").click()

            # 3초 대기
            page.wait_for_timeout(5000)

            # # ===== 여기서 ES 검증 호출 =====
            # assert_es_logs(
            #     service_name=SERVICE_NAME_DOORAY_BOARD_COMMENT,
            #     test_cases=FILE_LOGGING_CASE,
            #     size=1,
            # )

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAME_DOORAY_BOARD_COMMENT,
                test_cases=FILE_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # # 실패 시 스크린샷 경로 설정
            # screenshot_path = get_screenshot_path("test_dooray_board_comment_attach_send")  # 공통 함수 호출
            # page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # # page.screenshot(path=screenshot_path, full_page=True)
            # print(f"Screenshot taken at : {screenshot_path}")
            # allure.attach.file(screenshot_path, name="dooray_board_comment_attach_send_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")


        finally:
            browser.close()