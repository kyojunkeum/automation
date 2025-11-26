import os
import time
from datetime import datetime
import allure
import pytest
from playwright.sync_api import sync_playwright,TimeoutError
from base import *


NORMAL_LOGGING_CASE = [
    {
        "hit_index": 0,
        "label": "기본 로깅",
        "expected": {"pattern_count": "0", "keyword_count": "0", "file_count": "0", "tags" : ["comment"]},
    }
]

PATTERN_LOGGING_CASE = [
    {
        "hit_index": 0,
        "label": "패턴 로깅",
        "expected": {"pattern_count": "15", "keyword_count": "0", "file_count": "0"},
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
        "expected": {"pattern_count": "0", "keyword_count": "0", "file_count": "1"},
    }
]

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
def test_dooray_board_comment_normal(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "dooraystorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 게시판 페이지로 이동
            page.goto(f"{DOORAY_BASE_URL}/home")
            time.sleep(3)


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
            comment_box.fill("\n".join(DLP_NORMAL))
            time.sleep(1)

            # 저장 클릭
            page.get_by_role("button", name="저장").click()

            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_DOORAY_BOARD_COMMENT,
                test_cases=NORMAL_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_dooray_board_comment_normal")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="dooray_board_comment_normal_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Dooray board comment Pattern Test")
def test_dooray_board_comment_pattern(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "dooraystorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메일 페이지로 이동
            page.goto(f"{DOORAY_BASE_URL}/home")
            time.sleep(3)


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

            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_DOORAY_BOARD_COMMENT,
                test_cases=PATTERN_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )


        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_dooray_board_comment__pattern")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="dooray_board_comment_pattern_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Dooray board comment Keyword Send Test")
def test_dooray_board_comment_keyword(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "dooraystorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메일 페이지로 이동
            page.goto(f"{DOORAY_BASE_URL}/home")
            time.sleep(3)


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

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_DOORAY_BOARD_COMMENT,
                test_cases=KEYWORD_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_dooray_board_comment_keyword")
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="dooray_board_comment_keywordd_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.BLOCKER)
@allure.step("Dooray board comment attach Test")
def test_dooray_board_comment_attach(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "dooraystorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메일 페이지로 이동
            page.goto(f"{DOORAY_BASE_URL}/home")
            time.sleep(3)


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
            # 한 개 파일 첨부
            file_chooser.set_files(DLP_FILE)

            # # 여러 파일(2개) 첨부
            # file_chooser.set_files(DLP_FILES)

            # # 저장 클릭
            # page.get_by_role("button", name="저장").click()

            # 대기
            page.wait_for_timeout(10000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_DOORAY_BOARD,
                test_cases=FILE_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_dooray_board_comment_attach")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="dooray_board_comment_attach_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")


        finally:
            browser.close()