import os
import time
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
        "expected": {"pattern_count": "0", "keyword_count": "0", "file_count": "1"},
    }
]

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
            allure.attach.file(screenshot_path, name="dooray_login_failure_screenshot",
                               attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.NORMAL)
@allure.step("Dooray mail Normal Test")
@pytest.mark.dependency(name="dooray_mail_normal")
def test_dooray_mail_normal(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "dooraystorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메일 페이지로 이동
            page.goto(f"{DOORAY_BASE_URL}/mail/systems/inbox")
            time.sleep(3)

            # 메일쓰기 클릭 시 새 창이 열리는 것을 대기
            with page.expect_popup() as page1_info:
                page.get_by_test_id("openNewMailWriteForm").click()
            page1 = page1_info.value
            time.sleep(2)

            # 수신자 입력
            page1.get_by_test_id("MemberAutocompleteInput_TextField").first.click()
            page1.get_by_test_id("MemberAutocompleteInput_TextField").first.fill(EMAIL_RECEIVER)
            page1.wait_for_timeout(3000)  # 입력 후 잠시 대기
            print("수신자 정보를 입력하였습니다.")

            # 제목 입력
            page1.get_by_test_id("MailWriteHeader_BottomLinedTextField").click()
            page1.get_by_test_id("MailWriteHeader_BottomLinedTextField").fill("기본로깅테스트")

            # 본문 입력
            page1.get_by_role("application").locator("div").nth(3).click()
            page1.get_by_role("application").locator("div").nth(1).fill("기본로깅테스트\n\n")
            time.sleep(1)

            # 보내기 클릭
            page1.get_by_test_id("MailWriteFooter_ContainedButton").click()
            time.sleep(1)
            page1.get_by_test_id("MailWritePreviewModal_ContainedButton").click()

            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_DOORAY_MAIL,
                test_cases=NORMAL_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_dooray_mail_normal_send")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="dooray_mail_normal_send_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Dooray mail Pattern Test")
@pytest.mark.dependency(name="dooray_mail_pattern")
def test_dooray_mail_pattern(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "dooraystorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메일 페이지로 이동
            page.goto(f"{DOORAY_BASE_URL}/mail/systems/inbox")
            time.sleep(3)

            # 메일쓰기 클릭 시 새 창이 열리는 것을 대기
            with page.expect_popup() as page1_info:
                page.get_by_test_id("openNewMailWriteForm").click()
            page1 = page1_info.value
            time.sleep(2)

            # 수신자 입력
            page1.get_by_test_id("MemberAutocompleteInput_TextField").first.click()
            page1.get_by_test_id("MemberAutocompleteInput_TextField").first.fill(EMAIL_RECEIVER)
            page1.wait_for_timeout(1000)  # 입력 후 잠시 대기
            print("수신자 정보를 입력하였습니다.")


            # 제목 입력
            page1.get_by_test_id("MailWriteHeader_BottomLinedTextField").click()
            page1.get_by_test_id("MailWriteHeader_BottomLinedTextField").fill("개인정보로깅테스트")

            # 본문 클릭
            page1.get_by_role("application").locator("div").nth(3).click()

            # 기존 내용 모두 삭제
            target_box = page1.get_by_role("application").locator("div").nth(1)
            target_box.click()

            # 패턴 리스트 여러 개를 줄바꿈으로 입력
            target_box.fill("\n".join(DLP_PATTERNS))
            time.sleep(1)

            # 보내기 클릭
            page1.get_by_test_id("MailWriteFooter_ContainedButton").click()
            time.sleep(1)
            page1.get_by_test_id("MailWritePreviewModal_ContainedButton").click()

            # 5초 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_DOORAY_MAIL,
                test_cases=PATTERN_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_dooray_mail_pattern_send")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="dooray_mail_pattern_send_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Dooray mail Keyword Test")
@pytest.mark.dependency(name="dooray_mail_keyword")
def test_dooray_mail_keyword(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "dooraystorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메일 페이지로 이동
            page.goto(f"{DOORAY_BASE_URL}/mail/systems/inbox")
            time.sleep(3)

            # 메일쓰기 클릭 시 새 창이 열리는 것을 대기
            with page.expect_popup() as page1_info:
                page.get_by_test_id("openNewMailWriteForm").click()
            page1 = page1_info.value
            time.sleep(2)

            # 수신자 입력
            page1.get_by_test_id("MemberAutocompleteInput_TextField").first.click()
            page1.get_by_test_id("MemberAutocompleteInput_TextField").first.fill(EMAIL_RECEIVER)
            page1.wait_for_timeout(1000)  # 입력 후 잠시 대기
            print("수신자 정보를 입력하였습니다.")


            # 제목 입력
            page1.get_by_test_id("MailWriteHeader_BottomLinedTextField").click()
            page1.get_by_test_id("MailWriteHeader_BottomLinedTextField").fill("키워드로깅테스트")

            # 본문 클릭
            page1.get_by_role("application").locator("div").nth(3).click()

            # 기존 내용 모두 삭제
            target_box = page1.get_by_role("application").locator("div").nth(1)
            target_box.click()

            # 패턴 리스트 여러 개를 줄바꿈으로 입력
            target_box.fill("\n".join(DLP_KEYWORDS))
            time.sleep(1)

            # 보내기 클릭
            page1.get_by_test_id("MailWriteFooter_ContainedButton").click()
            time.sleep(1)
            page1.get_by_test_id("MailWritePreviewModal_ContainedButton").click()

            # 5초 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_DOORAY_MAIL,
                test_cases=KEYWORD_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_dooray_mail_keyword_send")
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="dooray_mail_keyword_send_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.BLOCKER)
@allure.step("Dooray mail attach Test")
@pytest.mark.dependency(name="dooray_mail_attach")
def test_dooray_mail_attach(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "dooraystorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메일 페이지로 이동
            page.goto(f"{DOORAY_BASE_URL}/mail/systems/inbox")
            time.sleep(3)

            # 메일쓰기 클릭 시 새 창이 열리는 것을 대기
            with page.expect_popup() as page1_info:
                page.get_by_test_id("openNewMailWriteForm").click()
            page1 = page1_info.value
            time.sleep(2)

            # 수신자 입력
            page1.get_by_test_id("MemberAutocompleteInput_TextField").first.click()
            page1.get_by_test_id("MemberAutocompleteInput_TextField").first.fill(EMAIL_RECEIVER)
            page1.wait_for_timeout(1000)  # 입력 후 잠시 대기
            print("수신자 정보를 입력하였습니다.")

            # 제목 입력
            page1.get_by_test_id("MailWriteHeader_BottomLinedTextField").click()
            page1.get_by_test_id("MailWriteHeader_BottomLinedTextField").fill("첨부파일로깅테스트")

            # 파일 첨부
            with page1.expect_file_chooser() as fc_info:
                page1.get_by_test_id("MailWriteHeader_GhostButton").click()
            file_chooser = fc_info.value
            # 파일 1개 첨부
            file_chooser.set_files(DLP_FILE)
            # # 파일 2개 첨부
            # file_chooser.set_files(DLP_FILES)
            print("파일을 첨부하였습니다.")

            # 5초 대기
            page.wait_for_timeout(10000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_DOORAY_MAIL,
                test_cases=FILE_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_dooray_mail_attach_send")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="dooray_mail_attach_send_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")


        finally:
            browser.close()



