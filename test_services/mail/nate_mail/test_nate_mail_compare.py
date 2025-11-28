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
@allure.step("Nate Login Test")
#@pytest.mark.order("first")
@pytest.mark.dependency(name="nate_login")
def test_nate_login():
    with sync_playwright() as p:
        # 브라우저 및 컨텍스트 생성
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            # 네이트 홈페이지 진입
            goto_and_wait(page, f"{NATE_BASE_URL}/")

            # 아이디 및 패스워드 입력
            page.get_by_label("아이디 or @이하 모두 입력").click()
            page.get_by_label("아이디 or @이하 모두 입력").fill(NATE_ID)
            page.get_by_role("textbox", name="비밀번호 비밀번호").click()
            page.get_by_role("textbox", name="비밀번호").fill(NATE_PASSWORD)
            time.sleep(1)
            page.get_by_role("button", name="로그인").click()
            time.sleep(3)

            # 세션 상태 저장
            os.makedirs("session", exist_ok=True)
            session_path = os.path.join("session", "natestorageState.json")
            context.storage_state(path=session_path)

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_nate_login")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="nate_login_failure_screenshot", attachment_type=allure.attachment_type.JPG)


            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.NORMAL)
@allure.step("Nate Mail Normal Test")
@pytest.mark.dependency(name="nate_mail_normal")
def test_nate_mail_normal(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "natestorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메일 페이지로 이동
            goto_and_wait(page, f"{NATE_MAIL_URL}/")
            print("▶ 메일 페이지 로드 완료")

            # 메일쓰기 클릭 시 새 창이 열리는 것을 대기
            click_and_wait_navigation(page, role="link", name="내게쓰기")


            # 제목 입력
            page.get_by_text("제목을 입력해주세요").click()
            page.get_by_label("제목").fill("기본로깅테스트")


            # 본문 입력
            editor_box = page.locator("iframe[title=\"에디터\"]").content_frame.locator("#wc_pc")
            editor_box.click()
            editor_box.fill("\n".join(DLP_NORMAL))

            # 보내기 클릭
            page.get_by_role("button", name="보내기").click()

            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_NATE_MAIL,
                test_cases=NORMAL_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_nate_mail_normal")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="nate_mail_normal_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Nate Mail Pattern Test")
@pytest.mark.dependency(name="nate_mail_pattern")
def test_nate_mail_pattern(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "natestorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메일 페이지로 이동
            goto_and_wait(page, f"{NATE_MAIL_URL}/")

            # 메일쓰기 클릭 시 새 창이 열리는 것을 대기
            click_and_wait_navigation(page, role="link", name="내게쓰기")

            # 제목 입력
            page.get_by_text("제목을 입력해주세요").click()
            page.get_by_label("제목").fill("개인정보로깅테스트")

            # 본문 입력
            editor_box = page.locator("iframe[title=\"에디터\"]").content_frame.locator("#wc_pc")
            editor_box.click()
            editor_box.fill("\n".join(DLP_PATTERNS))

            # 보내기 클릭
            page.get_by_role("button", name="보내기").click()

            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_NATE_MAIL,
                test_cases=PATTERN_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_nate_mail_pattern")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="nate_mail_pattern_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Nate Mail Keyword Test")
@pytest.mark.dependency(name="nate_mail_keyword")
def test_nate_mail_keyword(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "natestorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메일 페이지로 이동
            goto_and_wait(page, f"{NATE_MAIL_URL}/")

            # 메일쓰기 클릭 시 새 창이 열리는 것을 대기
            click_and_wait_navigation(page, role="link", name="내게쓰기")

            # 제목 입력
            page.get_by_text("제목을 입력해주세요").click()
            page.get_by_label("제목").fill("키워드로깅테스트")

            # 본문 입력
            editor_box = page.locator("iframe[title=\"에디터\"]").content_frame.locator("#wc_pc")
            editor_box.click()
            editor_box.fill("\n".join(DLP_KEYWORDS))

            # 보내기 클릭
            page.get_by_role("button", name="보내기").click()

            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_NATE_MAIL,
                test_cases=KEYWORD_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_nate_mail_keyword")
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="nate_mail_keyword_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.BLOCKER)
@allure.step("Nate Mail Attach Test")
@pytest.mark.dependency(name="nate_mail_attach")
def test_nate_mail_attach(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "natestorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메일 페이지로 이동
            goto_and_wait(page, f"{NATE_MAIL_URL}/")

            # 메일쓰기 클릭 시 새 창이 열리는 것을 대기
            click_and_wait_navigation(page, role="link", name="내게쓰기")
            # page.get_by_role("link", name="내게쓰기").click()
            # time.sleep(1)

            # 제목 입력
            page.get_by_text("제목을 입력해주세요").click()
            page.get_by_label("제목").fill("첨부파일로깅테스트")

            # 본문 입력
            editor_box = page.locator("iframe[title=\"에디터\"]").content_frame.locator("#wc_pc")
            editor_box.click()
            editor_box.fill("첨부파일로깅테스트")

            # 3. 파일 첨부 iframe 진입
            page.get_by_role("button", name="파일첨부하기").click()
            page.wait_for_selector('iframe#jsfile_iframe')
            file_frame = page.frame_locator('iframe#jsfile_iframe')
            file_input = file_frame.locator('input[type="file"]')
            file_input.set_input_files(DLP_FILE)
            page.wait_for_timeout(2000)
            print("파일을 첨부하였습니다.")

            # 보내기 클릭
            time.sleep(2)
            try:
                page.get_by_role("button", name="보내기").click(timeout=2000)
                print("✔ [DEBUG] 완료 클릭")
            except:
                print("▶ [DEBUG] 완료 없음 → 스킵")


            # 5초 대기
            page.wait_for_timeout(10000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_NATE_MAIL,
                test_cases=FILE_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_nate_mail_attach")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="nate_mail_attach_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")


        finally:
            browser.close()

