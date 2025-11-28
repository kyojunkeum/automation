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
@allure.step("Naverworks Board Normal Test")
@pytest.mark.dependency(name="naverworks_board_normal")
def test_naverworks_board_normal(request):
    with (sync_playwright() as p):
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "naverworksstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 게시판 페이지로 이동
            page.goto(f"{NAVERWORKS_BOARD_URL}/")
            time.sleep(3)

            # 자유게시판에 글쓰기
            page.get_by_role("button", name="글쓰기").click()
            page.locator("label").filter(has_text="자유게시판").click()
            page.get_by_role("button", name="확인").click()
            time.sleep(1)

            # 제목 입력
            page.get_by_placeholder("제목을 입력하세요").click()
            page.get_by_placeholder("제목을 입력하세요").fill("기본로깅테스트")

            # 본문 입력
            editor_box = page.locator("#articleEditor iframe").content_frame.locator(".workseditor-content")
            editor_box.click()
            editor_box.fill("\n".join(DLP_NORMAL))
            time.sleep(1)

            # 저장 클릭
            page.get_by_role("button", name="등록", exact=True).click()
            time.sleep(1)
            page.get_by_text("게시글 등록 알림 보내기").click()
            page.get_by_role("button", name="확인").click()

            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_NAVERWORKS_BOARD,
                test_cases=NORMAL_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_naverworks_board_normal")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="naverworks_board_normal_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Naverworks Board Pattern Test")
@pytest.mark.dependency(name="naverworks_board_pattern")
def test_naverworks_board_pattern(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "naverworksstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 게시판 페이지로 이동
            page.goto(f"{NAVERWORKS_BOARD_URL}/")
            time.sleep(3)

            # 자유게시판에 글쓰기
            page.get_by_role("button", name="글쓰기").click()
            page.locator("label").filter(has_text="자유게시판").click()
            page.get_by_role("button", name="확인").click()
            time.sleep(1)

            # 제목 입력
            page.get_by_placeholder("제목을 입력하세요").click()
            page.get_by_placeholder("제목을 입력하세요").fill("개인정보로깅테스트")

            # 본문 입력
            editor_box = page.locator("#articleEditor iframe").content_frame.locator(".workseditor-content")
            editor_box.click()
            editor_box.fill("\n".join(DLP_PATTERNS))
            time.sleep(1)

            # 저장 클릭
            page.get_by_role("button", name="등록", exact=True).click()
            time.sleep(1)
            page.get_by_text("게시글 등록 알림 보내기").click()
            page.get_by_role("button", name="확인").click()

            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_NAVERWORKS_BOARD,
                test_cases=PATTERN_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_naverworks_board_pattern")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="naverworks_board_pattern_failure_screenshot",
                               attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Naverworks Board Keyword Test")
@pytest.mark.dependency(name="naverworks_board_keyword")
def test_naverworks_board_keyword(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "naverworksstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 게시판 페이지로 이동
            page.goto(f"{NAVERWORKS_BOARD_URL}/")
            time.sleep(3)

            # 자유게시판에 글쓰기
            page.get_by_role("button", name="글쓰기").click()
            page.locator("label").filter(has_text="자유게시판").click()
            page.get_by_role("button", name="확인").click()
            time.sleep(1)

            # 제목 입력
            page.get_by_placeholder("제목을 입력하세요").click()
            page.get_by_placeholder("제목을 입력하세요").fill("키워드로깅테스트")

            # 본문 입력
            editor_box = page.locator("#articleEditor iframe").content_frame.locator(".workseditor-content")
            editor_box.click()
            editor_box.fill("\n".join(DLP_KEYWORDS))
            time.sleep(1)

            # 저장 클릭
            page.get_by_role("button", name="등록", exact=True).click()
            time.sleep(1)
            page.get_by_text("게시글 등록 알림 보내기").click()
            page.get_by_role("button", name="확인").click()

            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_NAVERWORKS_BOARD,
                test_cases=KEYWORD_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_naverworks_board_keyword")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="naverworks_board_keyword_failure_screenshot",
                               attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.BLOCKER)
@allure.step("Naverworks Board Attach Test")
@pytest.mark.dependency(name="naverworks_board_attach")
def test_naverworks_board_attach(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "naverworksstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 게시판 페이지로 이동
            page.goto(f"{NAVERWORKS_BOARD_URL}/")
            time.sleep(3)

            # 자유게시판에 글쓰기
            page.get_by_role("button", name="글쓰기").click()
            page.locator("label").filter(has_text="자유게시판").click()
            page.get_by_role("button", name="확인").click()
            time.sleep(1)

            # 제목 입력
            page.get_by_placeholder("제목을 입력하세요").click()
            page.get_by_placeholder("제목을 입력하세요").fill("첨부파일로깅테스트")

            # 본문 입력
            editor_box = page.locator("#articleEditor iframe").content_frame.locator(".workseditor-content")
            editor_box.click()
            editor_box.fill("첨부파일로깅테스트")
            time.sleep(1)

            # 파일 첨부 버튼 클릭
            page.get_by_role("button", name="파일첨부 파일첨부").click()
            time.sleep(1)
            # '내 PC' 클릭 → 파일 선택창 뜨는 타이밍에 맞춰 파일 지정
            with page.expect_file_chooser() as fc_info:
                page.get_by_role("link", name="내 PC").click()
                time.sleep(1)
            file_chooser = fc_info.value
            file_chooser.set_files(DLP_FILE)
            print(f"✔ [DEBUG] 파일 첨부 완료: {DLP_FILE}")

            # 저장 클릭
            try:
                page.get_by_role("button", name="등록", exact=True).click()
                time.sleep(1)
                page.get_by_text("게시글 등록 알림 보내기").click()
                page.get_by_role("button", name="확인").click()
                print("✔ [DEBUG] 완료 클릭")
            except:
                print("▶ [DEBUG] 완료 없음 → 스킵")

            # 대기
            page.wait_for_timeout(10000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_NAVERWORKS_BOARD,
                test_cases=FILE_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_naverworks_board_attach")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="naverworks_board_attach_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")


        finally:
            browser.close()