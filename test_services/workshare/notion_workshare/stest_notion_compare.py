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
@allure.step("Notion Login Test")
def test_notion_login():
    with sync_playwright() as p:
        # 브라우저 및 컨텍스트 생성
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            # 노션 홈페이지 진입
            page.goto("https://www.notion.com/")
            time.sleep(1)

            # 아이디 및 패스워드 입력
            page.get_by_role("link", name="Log in").click()

            page.get_by_placeholder("이메일 주소를 입력하세요").click()
            page.get_by_placeholder("이메일 주소를 입력하세요").fill("soosankeum@gmail.com")
            page.get_by_role("button", name="계속", exact=True).click()
            time.sleep(1)
            page.get_by_placeholder("비밀번호를 입력하세요").click()
            page.get_by_placeholder("비밀번호를 입력하세요").fill("iwilltakeyou01!")
            page.get_by_role("button", name="비밀번호로 계속하기").click()
            time.sleep(3)

            # # 로그인 성공 여부 확인
            # page.get_by_test_id("MyLoginProfileLayer").locator("img").click()
            # page.locator("#tippy-7").get_by_text("dlptest1").click()
            # page.wait_for_selector("role=link[name='dlptest1']", timeout=3000)
            # assert page.get_by_role("link", name="dlptest1").is_visible() == True, "login failed. can't find the profile."
            # time.sleep(2)

            # 세션 상태 저장
            os.makedirs("session", exist_ok=True)
            session_path = os.path.join("session", "notionstorageState.json")
            context.storage_state(path=session_path)

        except Exception as e:
            # # 실패 시 스크린샷 경로 설정
            # screenshot_path = get_screenshot_path("test_nate_login")  # 공통 함수 호출
            # page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # # page.screenshot(path=screenshot_path, full_page=True)
            # print(f"Screenshot taken at : {screenshot_path}")
            # allure.attach.file(screenshot_path, name="login_failure_screenshot", attachment_type=allure.attachment_type.JPG)


            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.NORMAL)
@allure.step("Notion board Normal Test")
def test_notion_normal_board(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "notionstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메일 페이지로 이동
            page.goto("https://www.notion.so/")

            # 게시글 클릭 시 새 창이 열리는 것을 대기
            page.get_by_label("시작하기").get_by_label("하위 페이지 추가").click()
            page.get_by_label("전체 페이지로 열기").click()
            time.sleep(1)

            # 제목 입력
            page.get_by_role("heading", name="새 페이지").click()
            page.get_by_label("입력하여 텍스트 편집 시작").fill("아이콘 추가\n커버 추가\n댓글 추가\n기본로깅제목\n시작하기\n글쓰기에 도움 받기\n표\n양식\n템플릿")

            # 본문 입력
            page.locator(".notion-page-content").click()
            page.get_by_label("입력하여 텍스트 편집 시작").fill("아이콘 추가\n커버 추가\n댓글 추가\n기본로깅제목\n기본로깅테스트본문")

            # 3초 대기
            page.wait_for_timeout(3000)

            # # 보내기 성공 여부 확인
            # page.locator("p").filter(has_text="메일이 성공적으로 발송되었습니다").click()
            # page.wait_for_selector("has_text=메일이 성공적으로 발송되었습니다", timeout=3000)
            # assert page.locator("has_text=메일이 성공적으로 발송되었습니다").is_visible() == True, "failed to send."
            # page.wait_for_timeout(2000)  # 2초 대기 (time.sleep 대신 사용)

        except Exception as e:
            # # 실패 시 스크린샷 경로 설정
            # screenshot_path = get_screenshot_path("test_nate_normal_send")  # 공통 함수 호출
            # page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # # page.screenshot(path=screenshot_path, full_page=True)
            # print(f"Screenshot taken at : {screenshot_path}")
            # allure.attach.file(screenshot_path, name="nate_normal_send_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Notion board Pattern Test")
def test_notion_pattern_board(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "notionstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메일 페이지로 이동
            page.goto("https://www.notion.so/")

            # 게시글 클릭 시 새 창이 열리는 것을 대기
            page.get_by_label("시작하기").get_by_label("하위 페이지 추가").click()
            page.get_by_label("전체 페이지로 열기").click()
            time.sleep(1)

            # 제목 입력
            page.get_by_role("heading", name="새 페이지").click()
            page.get_by_label("입력하여 텍스트 편집 시작").fill("아이콘 추가\n커버 추가\n댓글 추가\n개인정보테스트\n시작하기\n글쓰기에 도움 받기\n표\n양식\n템플릿")

            # 본문 입력
            page.locator(".notion-page-content").click()
            page.get_by_label("입력하여 텍스트 편집 시작").fill("아이콘 추가\n커버 추가\n댓글 추가\n개인정보테스트\nkjkeum@nate.com")

            # 3초 대기
            page.wait_for_timeout(3000)

            # # 보내기 성공 여부 확인
            # page.wait_for_selector("text=관리자에 의해 차단되었습니다. 관리자에 문의 하세요", timeout=3000)
            # assert page.locator("text=관리자에 의해 차단되었습니다. 관리자에 문의 하세요").is_visible() == True, "failed to block."
            # page.wait_for_timeout(2000)  # 2초 대기 (time.sleep 대신 사용)

        except Exception as e:
            # # 실패 시 스크린샷 경로 설정
            # screenshot_path = get_screenshot_path("test_nate_pattern_send")  # 공통 함수 호출
            # page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # # page.screenshot(path=screenshot_path, full_page=True)
            # print(f"Screenshot taken at : {screenshot_path}")
            # allure.attach.file(screenshot_path, name="nate_pattern_send_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Notion board Keyword Test")
def test_notion_keyword_board(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "notionstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메일 페이지로 이동
            page.goto("https://www.notion.so/")

            # 게시글 클릭 시 새 창이 열리는 것을 대기
            page.get_by_label("시작하기").get_by_label("하위 페이지 추가").click()
            page.get_by_label("전체 페이지로 열기").click()
            time.sleep(1)

            # 제목 입력
            page.get_by_role("heading", name="새 페이지").click()
            page.get_by_label("입력하여 텍스트 편집 시작").fill("아이콘 추가\n커버 추가\n댓글 추가\n키워드테스트\n시작하기\n글쓰기에 도움 받기\n표\n양식\n템플릿")

            # 본문 입력
            page.locator(".notion-page-content").click()
            page.get_by_label("입력하여 텍스트 편집 시작").fill("아이콘 추가\n커버 추가\n댓글 추가\n키워드테스트\n키워드테스트")

            # 3초 대기
            page.wait_for_timeout(3000)

            # # 보내기 성공 여부 확인
            # page.wait_for_selector("text=관리자에 의해 차단되었습니다. 관리자에 문의 하세요", timeout=3000)
            # assert page.locator("text=관리자에 의해 차단되었습니다. 관리자에 문의 하세요").is_visible() == True, "failed to block."
            # page.wait_for_timeout(2000)  # 2초 대기

        except Exception as e:
            # # 실패 시 스크린샷 경로 설정
            # screenshot_path = get_screenshot_path("test_nate_keyword_send")
            # page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # # page.screenshot(path=screenshot_path, full_page=True)
            # print(f"Screenshot taken at : {screenshot_path}")
            # allure.attach.file(screenshot_path, name="nate_keyword_send_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

def compare_ui_and_values(page, row_index, expected_values):
    """
    UI 데이터와 values 를 비교하는 함수
    :param page: Playwright Page 객체
    :param row_index: 비교할 행 번호 (1부터 시작)
    :param expected_values: 딕셔너리 형태의 기대 값
    """
    row_selector = f"table tr:nth-child({row_index})"
    ui_policy = page.locator(f"{row_selector} td:nth-child(4)").text_content().strip()
    ui_service = page.locator(f"{row_selector} td:nth-child(6)").text_content().strip()

    assert expected_values["policy"] == ui_policy, \
        f"정책명 불일치: 기대값({expected_values['policy']}) != UI({ui_policy})"
    assert expected_values["service"] == ui_service, \
        f"서비스명 불일치: 기대값({expected_values['service']}) != UI({ui_service})"

@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Notion board Dlp Logging check")
def test_compare_result_notion_board():
    with sync_playwright() as p:
        # 브라우저 실행
        browser = p.chromium.launch(headless=False)

        # BrowserContext 생성 (HTTPS 오류 무시 설정)
        context = browser.new_context(ignore_https_errors=True)

        # Context에서 새로운 페이지 생성
        page = context.new_page()

        try:

            # DLP 서비스 로그인
            page.goto("https://172.16.150.187:8443/login")  # DLP 제품 URL
            page.fill("input[name='j_username']", "intsoosan")
            page.fill("input[name='j_password']", "dkswjswmd4071*")
            page.get_by_role("button", name="LOGIN").click()
            time.sleep(2)

            # 알림 팝업 처리
            click_confirm_if_popup_exists(page, timeout=5000)

            # 서비스 로그 페이지로 이동
            page.goto("https://172.16.150.187:8443/log/service")

            # 상세 검색
            page.get_by_role("link", name="상세검색").click()
            time.sleep(1)
            # 서비스 선택
            page.locator("#selectedDetail").select_option("service")
            # 두레이게시판 선택
            page.locator("#tokenfield2-tokenfield").click()
            page.get_by_text("[업무공유] Notion").click()
            # 검색 클릭
            page.get_by_role("button", name="검색").click()
            time.sleep(5)

            # 딕셔너리 기댓값과 UI 데이터를 비교
            test_cases = [
                {"row_index": 1, "expected": {"policy": "0", "service": "0"}},  # 일반 로깅
            ]

            for case in test_cases:
                compare_ui_and_values(page, case["row_index"], case["expected"])

            print("모든 값이 일치합니다.")


        except Exception as e:

            # 실패 시 스크린샷 저장
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_dooray_board")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="dooray_board_failure_screenshot",
                               attachment_type=allure.attachment_type.JPG)

            raise

        finally:
            browser.close()


