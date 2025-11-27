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
def test_naverworks_login():
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
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_naverworks_login")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="naverworks_login_failure_screenshot",
                               attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.NORMAL)
@allure.step("Naverworks Survey Normal Test")
@pytest.mark.dependency(name="naverworks_survey_normal")
def test_naverworks_survey_normal(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "naverworksstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 드라이브 페이지로 이동
            page.goto(f"{NAVERWORKS_SURVEY_URL}")
            time.sleep(3)

            # 새설문 등록
            page.get_by_role("button", name="새 설문").click()
            page.get_by_role("button", name="사내용 설문").click()
            with page.expect_popup() as page1_info:
                page.get_by_role("link", name="새 설문").click()
            page1 = page1_info.value
            time.sleep(2)

            # 제목 입력
            page1.get_by_role("textbox", name="설문 제목을 입력하세요").click()
            page1.get_by_role("textbox", name="설문 제목을 입력하세요").fill("기본로깅테스트")
            time.sleep(1)
            page1.get_by_role("textbox", name="설문 설명을 입력하세요").click()
            page1.get_by_role("textbox", name="설문 설명을 입력하세요").fill("\n".join(DLP_NORMAL))
            time.sleep(1)

            page1.get_by_role("button", name="구성 추가").click()
            time.sleep(0.5)
            page1.get_by_text("객관식").click()
            time.sleep(0.5)
            page1.get_by_role("button", name="추가", exact=True).click()
            time.sleep(0.5)
            page1.get_by_role("button", name="완료").click()

            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_NAVERWORKS_SURVEY,
                test_cases=NORMAL_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_naverworks_survey_normal")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="naverworks_survey_normal_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Naverworks Survey Pattern Test")
@pytest.mark.dependency(name="naverworks_survey_pattern")
def test_naverworks_survey_pattern(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "naverworksstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 드라이브 페이지로 이동
            page.goto(f"{NAVERWORKS_SURVEY_URL}")
            time.sleep(3)

            # 새설문 등록
            page.get_by_role("button", name="새 설문").click()
            page.get_by_role("button", name="사내용 설문").click()
            with page.expect_popup() as page1_info:
                page.get_by_role("link", name="새 설문").click()
            page1 = page1_info.value
            time.sleep(2)

            # 제목 입력
            page1.get_by_role("textbox", name="설문 제목을 입력하세요").click()
            page1.get_by_role("textbox", name="설문 제목을 입력하세요").fill("개인정보로깅테스트")
            time.sleep(1)
            page1.get_by_role("textbox", name="설문 설명을 입력하세요").click()
            page1.get_by_role("textbox", name="설문 설명을 입력하세요").fill("\n".join(DLP_PATTERNS))
            time.sleep(1)

            page1.get_by_role("button", name="구성 추가").click()
            time.sleep(0.5)
            page1.get_by_text("객관식").click()
            time.sleep(0.5)
            page1.get_by_role("button", name="추가", exact=True).click()
            time.sleep(0.5)
            page1.get_by_role("button", name="완료").click()

            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_NAVERWORKS_SURVEY,
                test_cases=PATTERN_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_naverworks_survey_pattern")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="naverworks_survey_pattern_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Naverworks Survey Keyword Test")
@pytest.mark.dependency(name="naverworks_survey_keyword")
def test_naverworks_survey_keyword(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "naverworksstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 드라이브 페이지로 이동
            page.goto(f"{NAVERWORKS_SURVEY_URL}")
            time.sleep(3)

            # 새설문 등록
            page.get_by_role("button", name="새 설문").click()
            page.get_by_role("button", name="사내용 설문").click()
            with page.expect_popup() as page1_info:
                page.get_by_role("link", name="새 설문").click()
            page1 = page1_info.value
            time.sleep(2)

            # 제목 입력
            page1.get_by_role("textbox", name="설문 제목을 입력하세요").click()
            page1.get_by_role("textbox", name="설문 제목을 입력하세요").fill("키워드로깅테스트")
            time.sleep(1)
            page1.get_by_role("textbox", name="설문 설명을 입력하세요").click()
            page1.get_by_role("textbox", name="설문 설명을 입력하세요").fill("\n".join(DLP_KEYWORDS))
            time.sleep(1)

            page1.get_by_role("button", name="구성 추가").click()
            time.sleep(0.5)
            page1.get_by_text("객관식").click()
            time.sleep(0.5)
            page1.get_by_role("button", name="추가", exact=True).click()
            time.sleep(0.5)
            page1.get_by_role("button", name="완료").click()

            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_NAVERWORKS_SURVEY,
                test_cases=KEYWORD_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_naverworks_survey_keyword")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="naverworks_survey_keyword_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.BLOCKER)
@allure.step("Naverworks Survey Attach Test")
@pytest.mark.dependency(name="naverworks_survey_attach")
def test_naverworks_survey_attach(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "naverworksstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 드라이브 페이지로 이동
            page.goto(f"{NAVERWORKS_SURVEY_URL}")
            time.sleep(3)

            # 새설문 등록
            page.get_by_role("button", name="새 설문").click()
            page.get_by_role("button", name="사내용 설문").click()
            with page.expect_popup() as page1_info:
                page.get_by_role("link", name="새 설문").click()
            page1 = page1_info.value
            time.sleep(2)

            # 제목 입력
            page1.get_by_role("textbox", name="설문 제목을 입력하세요").click()
            page1.get_by_role("textbox", name="설문 제목을 입력하세요").fill("첨부파일로깅테스트")
            time.sleep(1)
            page1.get_by_role("textbox", name="설문 설명을 입력하세요").click()
            time.sleep(1)
            with page1.expect_file_chooser(timeout=5000) as fc_info:
                page1.get_by_role("button", name="Choose File").click()
            file_chooser = fc_info.value
            # 한 개 파일 첨부
            file_chooser.set_files(DLP_FILE)
            # # 여러 파일 첨부(2개)
            # file_chooser.set_files(DLP_FILES)
            time.sleep(1)

            page1.get_by_role("button", name="구성 추가").click()
            time.sleep(0.5)
            page1.get_by_text("객관식").click()
            time.sleep(0.5)
            page1.get_by_role("button", name="추가", exact=True).click()
            time.sleep(0.5)
            page1.get_by_role("button", name="완료").click()

            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_NAVERWORKS_SURVEY,
                test_cases=FILE_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_naverworks_survey_attach")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="naverworks_survey_attach_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()