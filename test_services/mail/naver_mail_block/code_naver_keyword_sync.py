import pytest
import os
from playwright.sync_api import sync_playwright
from datetime import datetime

@pytest.mark.order(4)
def test_naver_keyword_send(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "naverstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:
            # 스크린샷 찍을 수 있도록 설정
            request.node.page = page

            # 메일 페이지로 이동
            page.goto("https://mail.naver.com")

            # 메일쓰기 클릭 시 새 창이 열리는 것을 대기
            page.get_by_role("link", name="메일 쓰기").click()

            # 받는사람 입력
            page.get_by_label("받는사람").click()
            page.get_by_label("받는사람").fill("soosan_kjkeum@naver.com")

            # 제목 입력
            page.get_by_label("제목", exact=True).click()
            page.get_by_label("제목", exact=True).fill("키워드테스트")

            # 본문 입력
            page.get_by_role("main").locator("iframe").content_frame.get_by_label("본문 내용").click()
            page.get_by_role("main").locator("iframe").content_frame.get_by_label("본문 내용").fill("키워드테스트")

            # 보내기 클릭
            page.get_by_role("button", name="보내기").click()

            # 3초 대기
            page.wait_for_timeout(3000)

            # 보내기 성공 여부 확인
            page.wait_for_selector("text=관리자에 의해 차단되었습니다. 관리자에 문의 하세요", timeout=10000)
            assert page.locator("text=관리자에 의해 차단되었습니다. 관리자에 문의 하세요").is_visible(), "차단에 실패했습니다."
            page.wait_for_timeout(2000)  # 2초 대기


        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            os.makedirs("screenshot", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join("screenshot", f"screenshot_keyword_passed_{timestamp}.png")
            request.node.screenshot_path = screenshot_path
            page.screenshot(path=screenshot_path)

            # 실패 시 실패 로그 기록
            pytest.fail(f"Test failed: {str(e)}")
        finally:
            browser.close()
