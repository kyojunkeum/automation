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
        "expected": {"pattern_count": "0", "keyword_count": "0", "file_count": "0", "tags" : ["comment"]},
    }
]

PATTERN_LOGGING_CASE = [
    {
        "hit_index": 0,
        "label": "패턴 로깅",
        "expected": {"pattern_count": "14", "keyword_count": "0", "file_count": "0", "tags" : ["comment"]},
    }
]

KEYWORD_LOGGING_CASE = [
    {
        "hit_index": 0,
        "label": "키워드 로깅",
        "expected": {"pattern_count": "0", "keyword_count": "6", "file_count": "0", "tags" : ["comment"]},
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
@allure.step("Naverworks Board Comment Normal Test")
@pytest.mark.dependency(name="naverworks_board_comment_normal")
def test_naverworks_board_comment_normal(request):
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

            # 자유게시판으로 이동
            page.get_by_role("button", name="자유게시판").click()
            time.sleep(1)

            # 가장 위에 게시글 클릭
            page.locator(".sbj > a").first.click()
            time.sleep(1)

            # 댓글창 입력
            comment_box = page.locator("#commentInput_9")
            comment_box.click()
            comment_box.fill("\n".join(DLP_NORMAL))
            time.sleep(1)
            page.get_by_role("button", name="입력").click()

            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_NAVERWORKS_BOARD_COMMENT,
                test_cases=NORMAL_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_naverworks_board_comment_normal")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="naverworks_board_comment_normal_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Naverworks Board Comment Pattern Test")
@pytest.mark.dependency(name="naverworks_board_comment_pattern")
def test_naverworks_board_comment_pattern(request):
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

            # 자유게시판으로 이동
            page.get_by_role("button", name="자유게시판").click()
            time.sleep(1)

            # 가장 위에 게시글 클릭
            page.locator(".sbj > a").first.click()
            time.sleep(1)

            # 댓글창 입력
            comment_box = page.locator("#commentInput_9")
            comment_box.click()
            comment_box.fill("\n".join(DLP_PATTERNS))
            time.sleep(1)
            page.get_by_role("button", name="입력").click()

            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_NAVERWORKS_BOARD_COMMENT,
                test_cases=PATTERN_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_naverworks_board_comment_pattern")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="naverworks_board_comment_pattern_failure_screenshot",
                               attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Naverworks Board Comment Keyword Test")
@pytest.mark.dependency(name="naverworks_board_comment_keyword")
def test_naverworks_board_comment_keyword(request):
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

            # 자유게시판으로 이동
            page.get_by_role("button", name="자유게시판").click()
            time.sleep(1)

            # 가장 위에 게시글 클릭
            page.locator(".sbj > a").first.click()
            time.sleep(1)

            # 댓글창 입력
            comment_box = page.locator("#commentInput_9")
            comment_box.click()
            comment_box.fill("\n".join(DLP_KEYWORDS))
            time.sleep(1)
            page.get_by_role("button", name="입력").click()

            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_NAVERWORKS_BOARD_COMMENT,
                test_cases=KEYWORD_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_naverworks_board_comment_keyword")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="naverworks_board_comment_keyword_failure_screenshot",
                               attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.BLOCKER)
@allure.step("Naverworks Board Comment Attach Test")
@pytest.mark.dependency(name="naverworks_board_comment_attach")
def test_naverworks_board_comment_attach(request):
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

            # 자유게시판으로 이동
            page.get_by_role("button", name="자유게시판").click()
            time.sleep(1)

            # 가장 위에 게시글 클릭
            page.locator(".sbj > a").first.click()
            time.sleep(1)

            # 댓글창 입력
            comment_box = page.locator("#commentInput_9")
            comment_box.click()
            comment_box.fill("첨부파일로깅테스트")
            time.sleep(1)

            # 파일 첨부
            page.locator(".btn_attach_image").click()

            # "내 PC" 클릭
            try:
                page.get_by_role("button", name="내 PC").click()
                print("[DEBUG] '내 PC' 버튼 클릭 완료")
            except Exception:
                print("[WARN] '내 PC' 버튼을 찾지 못했습니다(무시).")

            # 파일 선택(file chooser) 발생 → 파일 첨부
            try:
                with page.expect_file_chooser(timeout=5000) as fc_info:
                    page.get_by_role("button", name="입력").click()
                file_chooser = fc_info.value

                file_chooser.set_files(DLP_FILE)
                print(f"[DEBUG] 파일 첨부 완료: {DLP_FILE}")

            except Exception as e:
                print(f"[ERROR] 파일 첨부 실패: {e}")
                raise

            # 대기
            page.wait_for_timeout(10000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_NAVERWORKS_BOARD_COMMENT,
                test_cases=FILE_LOGGING_CASE,
                size=1,
                max_attempts=3,  # 총 3번 시도
                interval_sec=5  # 시도 간 5초 대기
            )

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_naverworks_board_comment_attach")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="naverworks_board_comment_attach_failure_screenshot",
                               attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()
