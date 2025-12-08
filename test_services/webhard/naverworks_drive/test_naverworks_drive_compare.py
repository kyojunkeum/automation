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
        "expected": {"pattern_count": "0", "keyword_count": "0", "file_count": "1"},
    }
]

PATTERN_LOGGING_CASE = [
    {
        "hit_index": 0,
        "label": "패턴 로깅",
        "expected": {"pattern_count": "14", "keyword_count": "0", "file_count": "1"},
    }
]

KEYWORD_LOGGING_CASE = [
    {
        "hit_index": 0,
        "label": "키워드 로깅",
        "expected": {"pattern_count": "0", "keyword_count": "1", "file_count": "1"},
    }
]

MIX_LOGGING_CASE = [
    {
        "hit_index": 0,
        "label": "파일 로깅",
        "expected": {"pattern_count": "3", "keyword_count": "3", "file_count": "1"},
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

@allure.severity(allure.severity_level.BLOCKER)
@allure.step("Naverworks Drive Normal Test")
@pytest.mark.dependency(name="naverworks_drive_normal")
def test_naverworks_drive_normal(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "naverworksstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 드라이브 페이지로 이동
            page.goto(f"{NAVERWORKS_DRIVE_URL}/")
            time.sleep(3)

            # 테스트 페이지로 진입
            page.get_by_title("테스트").click()
            time.sleep(2)

            # 파일 첨부
            page.get_by_role("button", name="새로 만들기").click()
            time.sleep(1)

            # "파일 올리기" 클릭 → file chooser 대기 후 파일 첨부
            with page.expect_file_chooser(timeout=5000) as fc_info:
                page.locator("a").filter(has_text="파일 올리기").click()
            time.sleep(1)
            file_chooser = fc_info.value
            file_chooser.set_files(DLP_FILE)
            print(f"[DEBUG] file chooser로 파일 첨부 완료: {DLP_FILE}")

            # 팝업에 덮어쓰기 버튼이 있으면 클릭, 없으면 스킵
            overwrite_btn = page.get_by_role("button", name="덮어쓰기")

            try:
                overwrite_btn.wait_for(timeout=2000)
                overwrite_btn.click()
                print("✔ [DEBUG] '덮어쓰기' 버튼을 클릭했습니다.")
            except:
                print("▶ [DEBUG] '덮어쓰기' 버튼이 없어 스킵합니다.")


            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_NAVERWORKS_DRIVE,
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

@allure.severity(allure.severity_level.BLOCKER)
@allure.step("Naverworks Drive Pattern Test")
@pytest.mark.dependency(name="naverworks_drive_pattern")
def test_naverworks_drive_pattern(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "naverworksstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 드라이브 페이지로 이동
            page.goto(f"{NAVERWORKS_DRIVE_URL}/")
            time.sleep(3)

            # 테스트 페이지로 진입
            page.get_by_title("테스트").click()
            time.sleep(2)

            # 파일 첨부
            page.get_by_role("button", name="새로 만들기").click()
            time.sleep(1)

            # "파일 올리기" 클릭 → file chooser 대기 후 파일 첨부
            with page.expect_file_chooser(timeout=5000) as fc_info:
                page.locator("a").filter(has_text="파일 올리기").click()
            time.sleep(1)
            file_chooser = fc_info.value
            file_chooser.set_files(DLP_FILE_PATTERN)
            print(f"[DEBUG] file chooser로 파일 첨부 완료: {DLP_FILE_PATTERN}")

            # 팝업에 덮어쓰기 버튼이 있으면 클릭, 없으면 스킵
            overwrite_btn = page.get_by_role("button", name="덮어쓰기")

            try:
                overwrite_btn.wait_for(timeout=2000)
                overwrite_btn.click()
                print("✔ [DEBUG] '덮어쓰기' 버튼을 클릭했습니다.")
            except:
                print("▶ [DEBUG] '덮어쓰기' 버튼이 없어 스킵합니다.")


            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_NAVERWORKS_DRIVE,
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


allure.severity(allure.severity_level.BLOCKER)
@allure.step("Naverworks Drive Keyword Test")
@pytest.mark.dependency(name="naverworks_drive_keyword")
def test_naverworks_drive_keyword(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "naverworksstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 드라이브 페이지로 이동
            page.goto(f"{NAVERWORKS_DRIVE_URL}/")
            time.sleep(3)

            # 테스트 페이지로 진입
            page.get_by_title("테스트").click()
            time.sleep(2)

            # 파일 첨부
            page.get_by_role("button", name="새로 만들기").click()
            time.sleep(1)

            # "파일 올리기" 클릭 → file chooser 대기 후 파일 첨부
            with page.expect_file_chooser(timeout=5000) as fc_info:
                page.locator("a").filter(has_text="파일 올리기").click()
            time.sleep(1)
            file_chooser = fc_info.value
            file_chooser.set_files(DLP_FILE_KEYWORD)
            print(f"[DEBUG] file chooser로 파일 첨부 완료: {DLP_FILE_KEYWORD}")

            # 팝업에 덮어쓰기 버튼이 있으면 클릭, 없으면 스킵
            overwrite_btn = page.get_by_role("button", name="덮어쓰기")

            try:
                overwrite_btn.wait_for(timeout=2000)
                overwrite_btn.click()
                print("✔ [DEBUG] '덮어쓰기' 버튼을 클릭했습니다.")
            except:
                print("▶ [DEBUG] '덮어쓰기' 버튼이 없어 스킵합니다.")


            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_NAVERWORKS_DRIVE,
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


allure.severity(allure.severity_level.BLOCKER)
@allure.step("Naverworks Drive Mix Test")
@pytest.mark.dependency(name="naverworks_drive_mix")
def test_naverworks_drive_mix(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "naverworksstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 드라이브 페이지로 이동
            page.goto(f"{NAVERWORKS_DRIVE_URL}/")
            time.sleep(3)

            # 테스트 페이지로 진입
            page.get_by_title("테스트").click()
            time.sleep(2)

            # 파일 첨부
            page.get_by_role("button", name="새로 만들기").click()
            time.sleep(1)

            # "파일 올리기" 클릭 → file chooser 대기 후 파일 첨부
            with page.expect_file_chooser(timeout=5000) as fc_info:
                page.locator("a").filter(has_text="파일 올리기").click()
            time.sleep(1)
            file_chooser = fc_info.value
            file_chooser.set_files(DLP_FILE_MIX)
            print(f"[DEBUG] file chooser로 파일 첨부 완료: {DLP_FILE_MIX}")

            # 팝업에 덮어쓰기 버튼이 있으면 클릭, 없으면 스킵
            overwrite_btn = page.get_by_role("button", name="덮어쓰기")

            try:
                overwrite_btn.wait_for(timeout=2000)
                overwrite_btn.click()
                print("✔ [DEBUG] '덮어쓰기' 버튼을 클릭했습니다.")
            except:
                print("▶ [DEBUG] '덮어쓰기' 버튼이 없어 스킵합니다.")


            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_NAVERWORKS_DRIVE,
                test_cases=MIX_LOGGING_CASE,
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