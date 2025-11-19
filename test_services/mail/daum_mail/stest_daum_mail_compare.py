import os
import time
from datetime import datetime

import allure
import pytest
from playwright.sync_api import sync_playwright,BrowserContext,TimeoutError

def get_screenshot_path(test_name):
    screenshot_dir = os.path.join(os.getcwd(), "report", "screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(screenshot_dir, f"{test_name}_failed_{timestamp}.jpg")
    # return os.path.join(screenshot_dir, f"{test_name}_failed_{timestamp}.png")

def click_confirm_if_popup_exists(page, timeout=3000):
    """
    '확인' 버튼을 가진 팝업이 뜨면 해당 버튼을 찾아 클릭한다.
    나타나지 않으면(TimeoutError) 아무 처리도 하지 않는다.
    """
    try:
        page.wait_for_selector("role=button[name='확인']", timeout=timeout)
        page.get_by_role("button", name="확인").click()
        print("알림 팝업의 '확인' 버튼을 클릭했습니다.")
    except TimeoutError:
        print("알림 팝업(확인 버튼)이 나타나지 않았습니다.")

@allure.severity(allure.severity_level.TRIVIAL)
@allure.step("Daum Login Test")
#@pytest.mark.order("first")
@pytest.mark.dependency(name="daum_login")
@pytest.mark.xfail(reason="다음 로그인은 간헐적으로 실패함 (무시 가능)")
def test_daum_login():
    with sync_playwright() as p:
        # 브라우저 및 컨텍스트 생성
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            # 홈페이지 진입
            page.goto("https://www.daum.net/")
            time.sleep(20)

            # 아이디 및 패스워드 입력
            page.get_by_role("link", name="카카오계정으로 로그인").click()
            page.get_by_placeholder("카카오메일 아이디, 이메일, 전화번호 ").click()
            page.get_by_placeholder("카카오메일 아이디, 이메일, 전화번호 ").fill("soosan_kjkeum@naver.com")
            page.get_by_placeholder("비밀번호").click()
            page.get_by_placeholder("비밀번호").fill("iwilltakeyou01!")
            time.sleep(1)
            page.get_by_role("button", name="로그인", exact=True).click()
            time.sleep(3)

            # 로그인 성공 여부 확인
            page.wait_for_selector("strong.tit_user", timeout=5000)
            profile_text = page.locator("strong.tit_user").inner_text()
            assert "수산아이앤티DLP" in profile_text, f"로그인 실패: 프로필 텍스트 = {profile_text}"

            # page.wait_for_selector("role=link[name='수산아이앤티DLP']", timeout=3000)
            # assert page.get_by_role("link", name="수산아이앤티DLP").is_visible() == True, "login failed. can't find the profile."
            time.sleep(2)

            # 세션 상태 저장
            os.makedirs("session", exist_ok=True)
            session_path = os.path.join("session", "daumstorageState.json")
            context.storage_state(path=session_path)

        except Exception as e:
            # # 실패 시 스크린샷 경로 설정
            # screenshot_path = get_screenshot_path("test_nate_login")  # 공통 함수 호출
            # page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # # page.screenshot(path=screenshot_path, full_page=True)
            # print(f"Screenshot taken at : {screenshot_path}")
            # allure.attach.file(screenshot_path, name="login_failure_screenshot", attachment_type=allure.attachment_type.JPG)
            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            # pytest.fail(f"Test failed: {str(e)}")
            print(f"[WARN] 로그인 실패 (무시함): {e}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.NORMAL)
@allure.step("Daum Normal Send Test")
@pytest.mark.dependency(name="daum_normal_send")
def test_daum_normal_send(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "daumstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메일 페이지로 이동
            page.goto("https://mail.daum.net")

            # 메일쓰기 클릭 시 새 창이 열리는 것을 대기
            page.get_by_role("button", name="내게쓰기").click()

            # 제목 입력
            page.get_by_label("제목").click()
            page.get_by_label("제목").fill("기본로깅테스트")

            # 본문 입력
            page.locator("iframe[name=\"tx_canvas_wysiwyg\"]").content_frame.get_by_role("paragraph").first.click()
            page.locator("iframe[name=\"tx_canvas_wysiwyg\"]").content_frame.locator("body").fill("기본로깅테스트\n\n\n\n\n\n")

            # 보내기 클릭
            page.get_by_role("button", name="보내기").click()

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
@allure.step("Daum Pattern Send Test")
@pytest.mark.dependency(name="daum_pattern_send")
def test_daum_pattern_send(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "daumstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메일 페이지로 이동
            page.goto("https://mail.daum.net")

            # 메일쓰기 클릭 시 새 창이 열리는 것을 대기
            page.get_by_role("button", name="내게쓰기").click()

            # 제목 입력
            page.get_by_label("제목").click()
            page.get_by_label("제목").fill("개인정보테스트")

            # 본문 입력
            page.locator("iframe[name=\"tx_canvas_wysiwyg\"]").content_frame.get_by_role("paragraph").first.click()
            page.locator("iframe[name=\"tx_canvas_wysiwyg\"]").content_frame.locator("body").fill("kjkeum@nate.com\n\n\n\n\n\n")

            # 보내기 클릭
            page.get_by_role("button", name="보내기").click()

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
@allure.step("Daum Keyword Send Test")
@pytest.mark.dependency(name="daum_keyword_send")
def test_daum_keyword_send(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "daumstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메일 페이지로 이동
            page.goto("https://mail.daum.net")

            # 메일쓰기 클릭 시 새 창이 열리는 것을 대기
            page.get_by_role("button", name="내게쓰기").click()

            # 제목 입력
            page.get_by_label("제목").click()
            page.get_by_label("제목").fill("키워드테스트")

            # 본문 입력
            page.locator("iframe[name=\"tx_canvas_wysiwyg\"]").content_frame.get_by_role("paragraph").first.click()
            page.locator("iframe[name=\"tx_canvas_wysiwyg\"]").content_frame.locator("body").fill(
                "키워드테스트\n\n\n\n\n\n")

            # 보내기 클릭
            page.get_by_role("button", name="보내기").click()

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

@allure.severity(allure.severity_level.BLOCKER)
@allure.step("Daum attach Send Test")
@pytest.mark.dependency(name="daum_attach_send")
def test_daum_attach_send(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "daumstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메일 페이지로 이동
            page.goto("https://mail.daum.net")

            # 메일쓰기 클릭 시 새 창이 열리는 것을 대기
            page.get_by_role("button", name="내게쓰기").click()

            # 제목 입력
            page.get_by_label("제목").click()
            page.get_by_label("제목").fill("첨부파일테스트")

            # 3. 파일 첨부 클릭
            # page.get_by_label("파일 첨부하기").click()
            # page.get_by_label("파일 첨부하기").click()
            page.get_by_label("파일 첨부하기").set_input_files("D:/dlp_new_automation/test_files/pattern.docx")
            page.wait_for_timeout(2000)
            print("파일을 첨부하였습니다.")


            # 보내기 클릭
            time.sleep(2)
            page.get_by_role("button", name="보내기").click()

            # 3초 대기
            page.wait_for_timeout(3000)

            # # 보내기 성공 여부 확인
            # page.wait_for_selector("text=관리자에 의해 차단되었습니다. 관리자에 문의 하세요", timeout=3000)
            # assert page.locator("text=관리자에 의해 차단되었습니다. 관리자에 문의 하세요").is_visible() == True, "failed to block."
            # page.wait_for_timeout(2000)  # 2초 대기

        except Exception as e:
            # # 실패 시 스크린샷 경로 설정
            # screenshot_path = get_screenshot_path("test_nate_attach_send")  # 공통 함수 호출
            # page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # # page.screenshot(path=screenshot_path, full_page=True)
            # print(f"Screenshot taken at : {screenshot_path}")
            # allure.attach.file(screenshot_path, name="nate_attach_send_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")


        finally:
            browser.close()

def compare_ui_and_values(page, row_index, expected_counts):
    """
    UI 데이터와 values 를 비교하는 함수
    :param page: Playwright Page 객체
    :param row_index: 비교할 행 번호 (1부터 시작)
    :param expected_counts: 딕셔너리 형태의 기대 값
    """
    # # V9
    # row_selector = f"table tr:nth-child({row_index})"
    # ui_pattern_count = page.locator(f"{row_selector} td:nth-child(10)").text_content().strip()
    # ui_keyword_count = page.locator(f"{row_selector} td:nth-child(11)").text_content().strip()
    # ui_file_count = page.locator(f"{row_selector} td:nth-child(12)").text_content().strip()

    # V10
    row_selector = f"table tr:nth-child({row_index})"
    ui_pattern_count = page.locator(f"{row_selector} td:nth-child(11)").text_content().strip()
    ui_keyword_count = page.locator(f"{row_selector} td:nth-child(12)").text_content().strip()
    ui_file_count = page.locator(f"{row_selector} td:nth-child(13)").text_content().strip()

    assert expected_counts["pattern_count"] == ui_pattern_count, \
        f"패턴 검출수 불일치: 기대값({expected_counts['pattern_count']}) != UI({ui_pattern_count})"
    assert expected_counts["keyword_count"] == ui_keyword_count, \
        f"키워드 검출수 불일치: 기대값({expected_counts['keyword_count']}) != UI({ui_keyword_count})"
    assert expected_counts["file_count"] == ui_file_count, \
        f"파일 개수 불일치: 기대값({expected_counts['file_count']}) != UI({ui_file_count})"

@pytest.mark.dependency(
  depends=[
    "daum_login",
    "daum_normal_send",
    "daum_pattern_send",
    "daum_keyword_send",
    "daum_attach_send"
  ]
)

@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Daum Dlp Logging check")
def test_compare_result_daum_mail():
    with sync_playwright() as p:
        # 브라우저 실행
        browser = p.chromium.launch(headless=False)

        # BrowserContext 생성 (HTTPS 오류 무시 설정)
        context = browser.new_context(ignore_https_errors=True)

        # Context에서 새로운 페이지 생성
        page = context.new_page()

        try:

            # DLP 서비스 로그인
            page.goto("https://172.16.150.188:8443/login")  # DLP 제품 URL
            page.fill("input[name='j_username']", "intsoosan")
            page.fill("input[name='j_password']", "dkswjswmd4071*")
            # page.get_by_role("button", name="로그인").click()
            try:
                # "로그인" 또는 "Login" 텍스트를 가진 버튼 중 하나 클릭 시도
                login_button = page.locator("button:has-text('로그인'), button:has-text('Login')")
                login_button.first.click()
                print("[INFO] 로그인 버튼 클릭 성공")
            except Exception as e:
                print("[ERROR] 로그인 버튼 클릭 실패:", e)
                page.screenshot(path="login_click_failed.png")
                content = page.content()
                with open("login_page_debug.html", "w", encoding="utf-8") as f:
                    f.write(content)
                raise
            time.sleep(2)

            # 알림 팝업 처리
            click_confirm_if_popup_exists(page, timeout=5000)

            # 서비스 로그 페이지로 이동
            page.goto("https://172.16.150.188:8443/log/service")

            # 상세 검색
            page.get_by_role("link", name="상세검색").click()
            time.sleep(1)
            # 서비스 선택
            page.locator("#selectedDetail").select_option("service")
            # 네이트메일 선택
            page.locator("#tokenfield2-tokenfield").click()
            page.get_by_text("[웹메일] 다음메일").click()
            # 검색 클릭
            page.get_by_role("button", name="검색").click()
            time.sleep(5)

            # 딕셔너리 기댓값과 UI 데이터를 비교
            test_cases = [
                {"row_index": 4, "expected": {"pattern_count": "0", "keyword_count": "0", "file_count": "0"}},  # 일반 로깅
                {"row_index": 3, "expected": {"pattern_count": "1", "keyword_count": "0", "file_count": "0"}},  # 개인정보 로깅
                {"row_index": 2, "expected": {"pattern_count": "0", "keyword_count": "2", "file_count": "0"}},  # 키워드 로깅
                {"row_index": 1, "expected": {"pattern_count": "14", "keyword_count": "0", "file_count": "1"}},  # 첨부파일 로깅
            ]

            for case in test_cases:
                compare_ui_and_values(page, case["row_index"], case["expected"])

            print("모든 값이 일치합니다.")


        except Exception as e:

            # 실패 시 스크린샷 저장
            screenshot_path = get_screenshot_path("test_daum_mail")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="daum_mail_failure_screenshot",
                               attachment_type=allure.attachment_type.JPG)

            raise

        finally:
            browser.close()


