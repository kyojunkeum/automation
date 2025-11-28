import os
import time
import allure
import pytest
from playwright.sync_api import sync_playwright,TimeoutError
from base import *
from pathlib import Path

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
@allure.step("Copilot Free Login Test")
def test_copilot_free_login():
    with sync_playwright() as p:
        # 브라우저 및 컨텍스트 생성
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            # 코파일럿 홈페이지 진입
            page.goto(f"{COPILOT_BASE_URL}/")
            time.sleep(3)

            # 로그인 버튼 클릭
            page.get_by_test_id("composer-input").click()
            page.get_by_test_id("sidebar-settings-button").click()
            page.get_by_test_id("connect-account-button").click()
            page.get_by_test_id("msa-sign-in-button").click()


            # 아이디 및 패스워드 입력
            id_box = page.get_by_role("textbox", name="전자 메일, 전화 또는 Skype를 입력하세요")
            id_box.fill(COPILOT_ID)
            page.get_by_role("button", name="다음").click()
            time.sleep(1)
            page.get_by_role("button", name="암호 사용").click()
            time.sleep(1)
            pw_box = page.get_by_role("textbox", name="암호")
            pw_box.fill(COPILOT_PASSWORD)
            time.sleep(1)
            page.get_by_test_id("primaryButton").click()
            time.sleep(1)
            page.get_by_test_id("secondaryButton").click()
            time.sleep(3)

            # 세션 상태 저장
            os.makedirs("session", exist_ok=True)
            session_path = os.path.join("session", "copilotfreestorageState.json")
            context.storage_state(path=session_path)

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_copilot_free_login")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="copilot_free_login_failure_screenshot", attachment_type=allure.attachment_type.JPG)


            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()


@allure.severity(allure.severity_level.NORMAL)
@allure.step("Copilot Free Normal Test")
def test_copilot_free_normal(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "copilotfreestorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메신저 페이지로 이동
            page.goto(f"{COPILOT_BASE_URL}")
            time.sleep(3)

            # 새 채팅 열기
            page.get_by_role("button", name="새로운 채팅 시작").click()
            time.sleep(1)

            # 메시지 입력
            page.get_by_test_id("composer-input").fill("\n".join(DLP_NORMAL))
            time.sleep(1)

            # 메시지 전송
            page.get_by_test_id("submit-button").click()
            time.sleep(5)

            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_COPILOT,
                test_cases=NORMAL_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_copilot_free_normal")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="copilot_free_normal_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()


@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Copilot Free Pattern Test")
def test_copilot_free_pattern(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "copilotfreestorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메신저 페이지로 이동
            page.goto(f"{COPILOT_BASE_URL}")
            time.sleep(3)

            # 새 채팅 열기
            page.get_by_role("button", name="새로운 채팅 시작").click()
            time.sleep(1)

            # 메시지 입력
            page.get_by_test_id("composer-input").fill("\n".join(DLP_PATTERNS))
            time.sleep(1)

            # 메시지 전송
            page.get_by_test_id("submit-button").click()
            time.sleep(5)

            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_COPILOT,
                test_cases=PATTERN_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_copilot_free_pattern")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="copilot_free_pattern_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()


@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Copilot Free Keyword Test")
def test_copilot_free_keyword(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "copilotfreestorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메신저 페이지로 이동
            page.goto(f"{COPILOT_BASE_URL}")
            time.sleep(3)

            # 새 채팅 열기
            page.get_by_role("button", name="새로운 채팅 시작").click()
            time.sleep(1)

            # 메시지 입력
            page.get_by_test_id("composer-input").fill("\n".join(DLP_KEYWORDS))
            time.sleep(1)

            # 메시지 전송
            page.get_by_test_id("submit-button").click()
            time.sleep(5)

            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_COPILOT,
                test_cases=KEYWORD_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_copilot_free_keyword")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="copilot_free_keyword_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Copilot Free Attach Test")
def test_copilot_free_attach(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "copilotfreestorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메신저 페이지로 이동
            page.goto(f"{COPILOT_BASE_URL}")
            time.sleep(3)

            # 새 채팅 열기
            page.get_by_role("button", name="새로운 채팅 시작").click()
            time.sleep(1)

            # 파일 첨부
            # 1) 첨부 UI 열기
            page.get_by_test_id("composer-create-button").click()
            time.sleep(0.5)

            # 2) file chooser 기다리기 → 클릭
            with page.expect_file_chooser(timeout=5000) as fc_info:
                page.get_by_test_id("add-images-files").click()
            time.sleep(1)
            # 3) file chooser 객체 얻기
            file_chooser = fc_info.value
            time.sleep(1)
            # 4) 파일 첨부
            file_chooser.set_files(DLP_FILE)
            time.sleep(5)

            # 메시지 전송
            page.get_by_test_id("submit-button").click()

            # 대기
            page.wait_for_timeout(10000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_COPILOT,
                test_cases=FILE_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_copilot_free_attach")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="copilot_free_attach_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()