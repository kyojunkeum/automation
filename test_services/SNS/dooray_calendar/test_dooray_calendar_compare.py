import os
import time
from datetime import datetime
import allure
import pytest
from playwright.sync_api import sync_playwright,BrowserContext,TimeoutError
from base import *

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
#@pytest.mark.order("first")
@pytest.mark.dependency(name="dooray_login")
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
@allure.step("Dooray calendar Normal Test")
@pytest.mark.dependency(name="dooray_calendar_normal")
def test_dooray_calendar_normal(request):
    with (sync_playwright() as p):
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "dooraystorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 캘린더 페이지로 이동
            page.goto(f"{DOORAY_BASE_URL}/calendar")
            time.sleep(3)

            # 새 일정 클릭 시 새 창이 열리는 것을 대기
            with page.expect_popup() as page1_info:
                page.get_by_test_id("open-new-schedule-dialog-button").click()
            page1 = page1_info.value
            time.sleep(1)

            # 제목 입력
            page1.get_by_test_id("CalendarWidgetScheduleFormSubject_BottomLinedTextField").click()
            page1.get_by_test_id("CalendarWidgetScheduleFormSubject_BottomLinedTextField").fill("기본로깅테스트")

            # 본문 입력
            editor_box = page1.get_by_test_id("DoorayMDEditor").get_by_role("textbox")
            editor_box.click()
            editor_box.fill("기본로깅테스트")
            time.sleep(1)

            # 저장 클릭
            page1.get_by_test_id("DetailContentEditToolbar_ContainedButton").click()
            time.sleep(1)

            # 확인 클릭
            confirm_button = page1.locator('data-testid=ConfirmDialog_ContainedButton')
            if confirm_button.is_visible():
                confirm_button.click()

                # 대기
                page.wait_for_timeout(5000)

                # ===== 여기서 ES 검증 반복 호출 =====
                assert_es_logs_with_retry(
                    service_name=SERVICE_NAME_DOORAY_CALENDAR,
                    test_cases=NORMAL_LOGGING_CASE,
                    size=1,
                    max_attempts=3,  # 총 3번 시도
                    interval_sec=5  # 시도 간 5초 대기
                )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_dooray_calendar_normal")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="dooray_calendar_normal_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Dooray calendar Pattern Test")
@pytest.mark.dependency(name="dooray_calendar_pattern")
def test_dooray_calendar_pattern(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "dooraystorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 캘린더 페이지로 이동
            page.goto(f"{DOORAY_BASE_URL}/calendar")
            time.sleep(3)

            # 새 일정 클릭 시 새 창이 열리는 것을 대기
            with page.expect_popup() as page1_info:
                page.get_by_test_id("open-new-schedule-dialog-button").click()
            page1 = page1_info.value
            time.sleep(1)

            # 제목 입력
            page1.get_by_test_id("CalendarWidgetScheduleFormSubject_BottomLinedTextField").click()
            page1.get_by_test_id("CalendarWidgetScheduleFormSubject_BottomLinedTextField").fill("개인정보로깅테스트")

            # 본문 입력
            editor_box = page1.get_by_test_id("DoorayMDEditor").get_by_role("textbox")
            editor_box.click()
            editor_box.fill("\n".join(DLP_PATTERNS))
            time.sleep(2)

            # 저장 클릭
            page1.get_by_test_id("DetailContentEditToolbar_ContainedButton").click()
            time.sleep(1)

            # 확인 클릭
            confirm_button = page1.locator('data-testid=ConfirmDialog_ContainedButton')
            if confirm_button.is_visible():
                confirm_button.click()

                # 대기
                page.wait_for_timeout(5000)

                # ===== 여기서 ES 검증 반복 호출 =====
                assert_es_logs_with_retry(
                    service_name=SERVICE_NAME_DOORAY_CALENDAR,
                    test_cases=PATTERN_LOGGING_CASE,
                    size=1,
                    max_attempts=3,  # 총 3번 시도
                    interval_sec=5  # 시도 간 5초 대기
                )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_dooray_calendar_pattern")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="dooray_calendar_pattern_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Dooray calendar Keyword Test")
@pytest.mark.dependency(name="dooray_calendar_keyword")
def test_dooray_calendar_keyword(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "dooraystorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 캘린더 페이지로 이동
            page.goto(f"{DOORAY_BASE_URL}/calendar")
            time.sleep(3)

            # 새 일정 클릭 시 새 창이 열리는 것을 대기
            with page.expect_popup() as page1_info:
                page.get_by_test_id("open-new-schedule-dialog-button").click()
            page1 = page1_info.value
            time.sleep(1)

            # 제목 입력
            page1.get_by_test_id("CalendarWidgetScheduleFormSubject_BottomLinedTextField").click()
            page1.get_by_test_id("CalendarWidgetScheduleFormSubject_BottomLinedTextField").fill("키워드로깅테스트")

            # 본문 입력
            editor_box = page1.get_by_test_id("DoorayMDEditor").get_by_role("textbox")
            editor_box.click()
            editor_box.fill("\n".join(DLP_KEYWORDS))
            time.sleep(2)

            # 저장 클릭
            page1.get_by_test_id("DetailContentEditToolbar_ContainedButton").click()
            time.sleep(1)

            # 확인 클릭
            confirm_button = page1.locator('data-testid=ConfirmDialog_ContainedButton')
            if confirm_button.is_visible():
                confirm_button.click()

                # 대기
                page.wait_for_timeout(5000)

                # ===== 여기서 ES 검증 반복 호출 =====
                assert_es_logs_with_retry(
                    service_name=SERVICE_NAME_DOORAY_CALENDAR,
                    test_cases=KEYWORD_LOGGING_CASE,
                    size=1,
                    max_attempts=3,  # 총 3번 시도
                    interval_sec=5  # 시도 간 5초 대기
                )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_dooray_calendar_keyword")
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="dooray_calendar_keyword_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.BLOCKER)
@allure.step("Dooray calendar attach Test")
@pytest.mark.dependency(name="dooray_calendar_attach")
def test_dooray_calendar_attach(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "dooraystorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 캘린더 페이지로 이동
            page.goto(f"{DOORAY_BASE_URL}/calendar")
            time.sleep(3)

            # 새 일정 클릭 시 새 창이 열리는 것을 대기
            with page.expect_popup() as page1_info:
                page.get_by_test_id("open-new-schedule-dialog-button").click()
            page1 = page1_info.value
            time.sleep(1)

            # 제목 입력
            page1.get_by_test_id("CalendarWidgetScheduleFormSubject_BottomLinedTextField").click()
            page1.get_by_test_id("CalendarWidgetScheduleFormSubject_BottomLinedTextField").fill("첨부파일로깅테스트")
            time.sleep(1)

            # 파일 첨부
            with page1.expect_file_chooser() as fc_info:
                page1.get_by_test_id("DetailContentEditToolbar_GhostButton").click()
            file_chooser = fc_info.value
            # 한 개 파일 첨부
            file_chooser.set_files(DLP_FILE)

            # # 여러 파일 첨부(2개)
            # file_chooser.set_files(DLP_FILES)


            print("파일을 첨부하였습니다.")
            time.sleep(2)

            # 대기
            page.wait_for_timeout(10000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAME_DOORAY_CALENDAR,
                test_cases=FILE_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )


        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_dooray_calendar_attach")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="dooray_calendar_attach_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")


        finally:
            browser.close()



