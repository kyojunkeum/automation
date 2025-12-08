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
@allure.step("Notion Login Test")
def test_notion_login(request):
    with sync_playwright() as p:
        # 브라우저 및 컨텍스트 생성
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            # 노션 홈페이지 진입
            goto_and_wait(page, f"{NOTION_BASE_URL}/")

            # 아이디 및 패스워드 입력
            page.get_by_role("link", name="로그인").click()
            time.sleep(1)
            page.get_by_role("textbox", name="이메일 주소를 입력하세요").click()
            page.get_by_role("textbox", name="이메일 주소를 입력하세요").fill(NOTION_ID)
            time.sleep(1)
            page.get_by_role("button", name="계속", exact=True).click()
            time.sleep(1)
            page.get_by_role("textbox", name="비밀번호를 입력하세요").click()
            page.get_by_role("textbox", name="비밀번호를 입력하세요").fill(NOTION_PASSWORD)
            time.sleep(1)
            page.get_by_role("button", name="비밀번호로 계속하기").click()
            time.sleep(3)

            # 세션 상태 저장
            os.makedirs("session", exist_ok=True)
            session_path = os.path.join("session", "notionstorageState.json")
            context.storage_state(path=session_path)

        except Exception as e:
            capture_failure_screenshot(page, request, timeout=5000)
            print(f"[WARN] 테스트 실패: {e}")
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.NORMAL)
@allure.step("Notion Normal Test")
def test_notion_normal(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "notionstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 노션 편집 페이지로 이동
            page.goto("https://www.notion.so/")

            # 게시글 클릭 시 새 창이 열리는 것을 대기
            page.get_by_role("button", name="페이지 추가", exact=True).click()
            time.sleep(1)

            page.get_by_role("textbox", name="입력하여 텍스트 편집 시작").fill(
                "아이콘 추가\n커버 추가\n댓글 추가\n기본로깅테스트\n시작하기\nAI에게 질문하기\nAI 노트\n데이터베이스\n폼\n템플릿")
            page.locator(".notion-page-content").click()
            page.get_by_role("textbox", name="입력하여 텍스트 편집 시작").fill("아이콘 추가\n커버 추가\n댓글 추가\n기본로깅\n기본로깅테스트본문")

            # # 제목 입력
            # page.get_by_role("region", name="사이드 보기").get_by_label("입력하여 텍스트 편집 시작").fill("기본로깅테스트")
            #
            # # 본문 입력
            # page.locator(".layout.layout-center-peek > div:nth-child(4) > .notion-page-content").click()
            # page.get_by_role("region", name="사이드 보기").get_by_label("입력하여 텍스트 편집 시작").fill("\n".join(DLP_NORMAL))


            # 3초 대기
            page.wait_for_timeout(3000)

            # # 보내기 성공 여부 확인
            # page.locator("p").filter(has_text="메일이 성공적으로 발송되었습니다").click()
            # page.wait_for_selector("has_text=메일이 성공적으로 발송되었습니다", timeout=3000)
            # assert page.locator("has_text=메일이 성공적으로 발송되었습니다").is_visible() == True, "failed to send."
            # page.wait_for_timeout(2000)  # 2초 대기 (time.sleep 대신 사용)

        except Exception as e:
            capture_failure_screenshot(page, request, timeout=5000)
            print(f"[WARN] 테스트 실패: {e}")
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
            capture_failure_screenshot(page, request, timeout=5000)
            print(f"[WARN] 테스트 실패: {e}")
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
            capture_failure_screenshot(page, request, timeout=5000)
            print(f"[WARN] 테스트 실패: {e}")
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()
