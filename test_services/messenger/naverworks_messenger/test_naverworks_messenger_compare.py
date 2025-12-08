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
        "expected": {"pattern_count": "1", "keyword_count": "0", "file_count": "0"},
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
@allure.step("Naverworks Login Test")
#@pytest.mark.order("first")
@pytest.mark.dependency(name="naverworks_login")
def test_naverworks_login(request):
    with sync_playwright() as p:
        # 브라우저 및 컨텍스트 생성
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            # 네이버웍스 홈페이지 진입
            goto_and_wait(page, f"{NAVERWORKS_BASE_URL}")

            # 아이디 및 패스워드 입력
            with page.expect_popup() as page1_info:
                page.get_by_role("link", name="로그인", exact=True).click()
            page1 = page1_info.value
            time.sleep(1)
            page1.get_by_placeholder("또는 id@group.xxx").click()
            page1.get_by_placeholder("또는 id@group.xxx").fill(NAVERWORKS_ID)
            page1.get_by_role("button", name="로그인", exact=True).click()
            time.sleep(1)
            page1.get_by_placeholder("비밀번호").click()
            page1.get_by_placeholder("비밀번호").fill(NAVERWORKS_PASSWORD)
            time.sleep(1)
            page1.get_by_role("button", name="로그인").click()
            time.sleep(3)

            # 세션 상태 저장
            os.makedirs("session", exist_ok=True)
            session_path = os.path.join("session", "naverworksstorageState.json")
            context.storage_state(path=session_path)

        except Exception as e:
            capture_failure_screenshot(page, request, timeout=5000)
            print(f"[WARN] 테스트 실패: {e}")
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()


@allure.severity(allure.severity_level.NORMAL)
@allure.step("Naverworks Messenger Normal Test")
@pytest.mark.dependency(name="naverworks_messenger_normal")
def test_naverworks_messenger_normal(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "naverworksstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메신저 페이지로 이동
            page.goto(f"{NAVERWORKS_MESSENGER_URL}/")
            time.sleep(3)

            # 메시지 입력
            editor_box = page.locator("#message-input")
            editor_box.fill("\n".join(DLP_NORMAL))

            # Enter로 메시지 전송
            page.keyboard.press("Enter")
            print("✔ [DEBUG] Enter 키로 메시지 전송 완료")

            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_NAVERWORKS_MESSENGER,
                test_cases=NORMAL_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            capture_failure_screenshot(page, request, timeout=5000)
            print(f"[WARN] 테스트 실패: {e}")
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()


@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Naverworks Messenger Pattern Test")
@pytest.mark.dependency(name="naverworks_messenger_pattern")
def test_naverworks_messenger_pattern(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "naverworksstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메신저 페이지로 이동
            page.goto(f"{NAVERWORKS_MESSENGER_URL}/")
            time.sleep(3)

            # 메시지 입력
            editor_box = page.locator("#message-input")
            editor_box.fill("\n".join(DLP_PATTERN))

            # Enter로 메시지 전송
            page.keyboard.press("Enter")
            print("✔ [DEBUG] Enter 키로 메시지 전송 완료")

            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_NAVERWORKS_MESSENGER,
                test_cases=PATTERN_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            capture_failure_screenshot(page, request, timeout=5000)
            print(f"[WARN] 테스트 실패: {e}")
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()


@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Naverworks Messenger Keyword Test")
@pytest.mark.dependency(name="naverworks_messenger_keyword")
def test_naverworks_messenger_keyword(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "naverworksstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메신저 페이지로 이동
            page.goto(f"{NAVERWORKS_MESSENGER_URL}/")
            time.sleep(3)

            # 메시지 입력
            editor_box = page.locator("#message-input")
            editor_box.fill("\n".join(DLP_KEYWORDS))

            # Enter로 메시지 전송
            page.keyboard.press("Enter")
            print("✔ [DEBUG] Enter 키로 메시지 전송 완료")

            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_NAVERWORKS_MESSENGER,
                test_cases=KEYWORD_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            capture_failure_screenshot(page, request, timeout=5000)
            print(f"[WARN] 테스트 실패: {e}")
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.BLOCKER)
@allure.step("Naverworks Messenger Attach Test")
@pytest.mark.dependency(name="naverworks_messenger_attach")
def test_naverworks_messenger_attach(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "naverworksstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메신저 페이지로 이동
            page.goto(f"{NAVERWORKS_MESSENGER_URL}/")
            time.sleep(3)

            # 파일 첨부
            page.get_by_role("button", name="파일첨부").click()

            # '내 PC' 클릭 → 파일 선택창 뜨는 타이밍에 맞춰 파일 지정
            with page.expect_file_chooser(timeout=5000) as fc_info:
                page.get_by_text("내 PC").click()
            time.sleep(1)
            file_chooser = fc_info.value
            file_chooser.set_files(DLP_FILE)
            time.sleep(2)
            print(f"[DEBUG] 파일 첨부 완료: {DLP_FILE}")

            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_NAVERWORKS_MESSENGER,
                test_cases=FILE_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            capture_failure_screenshot(page, request, timeout=5000)
            print(f"[WARN] 테스트 실패: {e}")
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()