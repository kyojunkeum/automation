import os
import time
import json
from datetime import datetime

import allure
import pytest
from playwright.sync_api import sync_playwright, BrowserContext


def get_screenshot_path(test_name):
    screenshot_dir = os.path.join(os.getcwd(), "report", "screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(screenshot_dir, f"{test_name}_failed_{timestamp}.jpg")
    # return os.path.join(screenshot_dir, f"{test_name}_failed_{timestamp}.png")

def save_result_to_json(policy, date, plugin_name_kor, service_kor, pattern_count, keyword_count, file_count,
                             compare_result, plugin_name, service_name, case_id):
    result = {
        plugin_name: {
            "정책": policy,
            "발생일시": date,
            "타입": plugin_name_kor,
            "서비스": service_kor,
            "개인정보 검출수": pattern_count,
            "키워드 검출수": keyword_count,
            "파일 검출수": file_count,
            "상세 이력": compare_result,
            "서비스 이름": service_name,
            "자동화 테스트 케이스 ID": case_id
        }
    }

    # JSON 파일 경로 설정
    file_dir = os.path.join(os.path.dirname(__file__), "result")
    os.makedirs(file_dir, exist_ok=True)
    file_path = os.path.join(os.path.dirname(__file__), "result", f"{case_id}_result.json")

    # JSON 파일이 존재하면 기존 내용에 추가, 없으면 새 파일 생성
    if os.path.exists(file_path):
        with open(file_path, 'r+', encoding='utf-8') as f:
            data = json.load(f)
            data.append(result)
            f.seek(0)
            json.dump(data, f, indent=4, ensure_ascii=False)
    else:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump([result], f, indent=4, ensure_ascii=False)

    print(f"Result saved to JSON for case_id: {case_id}")

    return file_path


@allure.severity(allure.severity_level.TRIVIAL)
@allure.step("Naver Login Test")
def test_naver_login():
    with sync_playwright() as p:
        # 브라우저 및 컨텍스트 생성
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            # 네이버 홈페이지 진입
            page.goto("https://www.naver.com/")
            page.get_by_role("link", name="NAVER 로그인").click()
            time.sleep(1)

            # 아이디 및 패스워드 입력
            page.get_by_label("아이디 또는 전화번호").fill("soosan_kjkeum")
            page.get_by_label("비밀번호").fill("iwilltakeyou01!")
            page.get_by_role("button", name="로그인").click()

            # 로그인 성공 여부 확인
            page.wait_for_selector("role=link[name='프로필 설정']", timeout=3000)
            assert page.get_by_role("link", name="프로필 설정").is_visible() == True, "login failed. can't find the profile."
            time.sleep(2)

            # 세션 상태 저장
            os.makedirs("session", exist_ok=True)
            session_path = os.path.join("session", "naverstorageState.json")
            context.storage_state(path=session_path)

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_naver_login")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="login_failure_screenshot", attachment_type=allure.attachment_type.JPG)


            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.NORMAL)
@allure.step("Naver Normal Send Test")
def test_naver_normal_send(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "naverstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메일 페이지로 이동
            page.goto("https://mail.naver.com")

            # 메일쓰기 클릭 시 새 창이 열리는 것을 대기
            page.get_by_role("link", name="메일 쓰기").click()

            # 받는사람 입력
            page.get_by_label("받는사람").click()
            page.get_by_label("받는사람").fill("soosan_kjkeum@naver.com")

            # 제목 입력
            page.get_by_label("제목", exact=True).click()
            page.get_by_label("제목", exact=True).fill("기본로깅테스트")

            # 본문 입력
            page.get_by_role("main").locator("iframe").content_frame.get_by_label("본문 내용").click()
            page.get_by_role("main").locator("iframe").content_frame.get_by_label("본문 내용").fill("기본로깅테스트")

            # 보내기 클릭
            page.get_by_role("button", name="보내기").click()

            # 3초 대기
            page.wait_for_timeout(3000)

            # 보내기 성공 여부 확인
            page.wait_for_selector("text=메일이 저장되었습니다", timeout=3000)
            assert page.locator("text=메일이 저장되었습니다").is_visible() == True, "failed to send."
            page.wait_for_timeout(2000)  # 2초 대기 (time.sleep 대신 사용)

            # JSON 파일에 결과 저장
            file_path = save_result_to_json(
                policy="정상 발송",
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                plugin_name_kor="메일",
                service_kor="네이버메일",
                pattern_count="0",
                keyword_count="0",
                file_count="0",
                compare_result="성공",
                plugin_name="mail",
                service_name="naver_mail",
                case_id="naver_normal_send"
            )
            print(f"json file saved at : {file_path}")

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_naver_normal_send")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="normal_send_failure_screenshot", attachment_type=allure.attachment_type.JPG)

            # JSON 파일에 결과 저장
            file_path = save_result_to_json(
                policy="발송 실패",
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                plugin_name_kor="메일",
                service_kor="네이버메일",
                pattern_count="0",
                keyword_count="0",
                file_count="0",
                compare_result="실패",
                plugin_name="mail",
                service_name="naver_mail",
                case_id="naver_normal_send"
            )
            print(f"json file saved at : {file_path}")

            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Naver Pattern Send Test")
def test_naver_pattern_send(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "naverstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 메일 페이지로 이동
            page.goto("https://mail.naver.com")

            # 메일쓰기 클릭 시 새 창이 열리는 것을 대기
            page.get_by_role("link", name="메일 쓰기").click()

            # 받는사람 입력
            page.get_by_label("받는사람").click()
            page.get_by_label("받는사람").fill("soosan_kjkeum@naver.com")

            # 제목 입력
            page.get_by_label("제목", exact=True).click()
            page.get_by_label("제목", exact=True).fill("개인정보테스트")

            # 본문 입력
            page.get_by_role("main").locator("iframe").content_frame.get_by_label("본문 내용").click()
            page.get_by_role("main").locator("iframe").content_frame.get_by_label("본문 내용").fill("kjkeum@naver.com")

            # 보내기 클릭
            page.get_by_role("button", name="보내기").click()

            # 3초 대기
            page.wait_for_timeout(3000)

            # 보내기 성공 여부 확인
            page.wait_for_selector("text=관리자에 의해 차단되었습니다. 관리자에 문의 하세요", timeout=3000)
            assert page.locator("text=관리자에 의해 차단되었습니다. 관리자에 문의 하세요").is_visible() == True, "failed to block."
            page.wait_for_timeout(2000)  # 2초 대기 (time.sleep 대신 사용)

        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_naver_pattern_send")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="pattern_send_failure_screenshot", attachment_type=allure.attachment_type.JPG)


            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Naver Keyword Send Test")
def test_naver_keyword_send(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "naverstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

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
            page.wait_for_selector("text=관리자에 의해 차단되었습니다. 관리자에 문의 하세요", timeout=3000)
            assert page.locator("text=관리자에 의해 차단되었습니다. 관리자에 문의 하세요").is_visible() == True, "failed to block."
            page.wait_for_timeout(2000)  # 2초 대기


        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_naver_keyword_send")
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="keyword_send_failure_screenshot", attachment_type=allure.attachment_type.JPG)


            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.BLOCKER)
@allure.step("Naver attach Send Test")
def test_naver_attach_send(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "naverstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 메일 페이지로 이동
            page.goto("https://mail.naver.com")

            # 메일쓰기 클릭 시 새 창이 열리는 것을 대기
            page.get_by_role("link", name="메일 쓰기").click()

            # 받는사람 입력
            page.get_by_label("받는사람").click()
            page.get_by_label("받는사람").fill("soosan_kjkeum@naver.com")

            # 제목 입력
            page.get_by_label("제목", exact=True).click()
            page.get_by_label("제목", exact=True).fill("첨부파일테스트")

            # 본문 입력
            page.get_by_role("main").locator("iframe").content_frame.get_by_label("본문 내용").click()
            page.get_by_role("main").locator("iframe").content_frame.get_by_label("본문 내용").fill("첨부파일테스트")

            # # 파일 첨부
            # page.wait_for_selector("text=내 PC", timeout=20000)  # "내 PC" 텍스트가 나타날 때까지 최대 10초간 기다립니다
            # file_input = page.get_by_text("내 PC")
            # file_input.set_input_files("../../test_files/test.jpg")
            # page.wait_for_timeout(2000)

            # 파일 첨부
            time.sleep(3)  # 파일 업로드 대기
            page.get_by_label("내 PC에서 업로드").set_input_files("D:\\backup\\dlp_new_automation\\test_files\\pattern.docx")
            page.wait_for_timeout(3000)
            # page.get_by_text("내 PC에서 업로드").click()
            # time.sleep(2)
            # file_path = "D:\\backup\\dlp_new_automation\\test_files\\pattern.docx"
            # pyautogui.write(file_path)  # 파일 경로 입력
            # pyautogui.press('enter')  # Enter 키로 "열기" 버튼 클릭

            # 보내기 클릭
            page.get_by_role("button", name="보내기").click()
            page.wait_for_timeout(3000)

            # 보내기 성공 여부 확인
            page.wait_for_selector("text=관리자에 의해 차단되었습니다. 관리자에 문의 하세요", timeout=3000)
            assert page.locator("text=관리자에 의해 차단되었습니다. 관리자에 문의 하세요").is_visible() == True, "failed to block."
            page.wait_for_timeout(2000)  # 2초 대기


        except Exception as e:
            # 실패 시 스크린샷 경로 설정
            screenshot_path = get_screenshot_path("test_naver_attach_send")  # 공통 함수 호출
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            # page.screenshot(path=screenshot_path, full_page=True)
            print(f"Screenshot taken at : {screenshot_path}")
            allure.attach.file(screenshot_path, name="attach_send_failure_screenshot", attachment_type=allure.attachment_type.JPG)


            # pytest.fail로 스크린샷 경로와 함께 실패 메시지 기록
            pytest.fail(f"Test failed: {str(e)}")


        finally:
            browser.close()

def compare_ui_and_json(page, row_index, expected_counts):
    """
    UI 데이터와 JSON 데이터를 비교하는 함수
    :param page: Playwright Page 객체
    :param row_index: 비교할 행 번호 (1부터 시작)
    :param expected_counts: JSON 데이터에서 가져온 예상 값 (딕셔너리 형태)
    """
    row_selector = f"table tr:nth-child({row_index})"
    ui_pattern_count = page.locator(f"{row_selector} td:nth-child(9)").text_content().strip()
    ui_keyword_count = page.locator(f"{row_selector} td:nth-child(10)").text_content().strip()
    ui_file_count = page.locator(f"{row_selector} td:nth-child(11)").text_content().strip()

    assert expected_counts["pattern_count"] == ui_pattern_count, \
        f"패턴 검출수 불일치: JSON({expected_counts['pattern_count']}) != UI({ui_pattern_count})"
    assert expected_counts["keyword_count"] == ui_keyword_count, \
        f"키워드 검출수 불일치: JSON({expected_counts['keyword_count']}) != UI({ui_keyword_count})"
    assert expected_counts["file_count"] == ui_file_count, \
        f"파일 개수 불일치: JSON({expected_counts['file_count']}) != UI({ui_file_count})"

@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Naver Dlp Logging check")
def test_compare_result_naver_mail():
    with sync_playwright() as p:
        # 브라우저 실행
        browser = p.chromium.launch(headless=False)

        # BrowserContext 생성 (HTTPS 오류 무시 설정)
        context = browser.new_context(ignore_https_errors=True)

        # Context에서 새로운 페이지 생성
        page = context.new_page()

        try:

            # DLP 서비스 로그인
            page.goto("https://172.16.150.185:8443/login")  # DLP 제품 URL
            page.fill("input[name='j_username']", "intsoosan")
            page.fill("input[name='j_password']", "dkswjswmd4071*")
            page.click("#btn_Login")
            time.sleep(2)
            page.get_by_role("button", name="확인").click()
            time.sleep(2)

            # 서비스 로그 페이지로 이동
            page.goto("https://172.16.150.185:8443/log/service")

            # 상세 검색
            page.get_by_role("link", name="상세검색").click()
            time.sleep(1)
            # 서비스 선택
            page.locator("#selectedDetail").select_option("service")
            # 네이버메일 선택
            page.locator("#tokenfield2-tokenfield").click()
            page.get_by_text("[웹메일] 네이버메일").click()
            # 검색 클릭
            page.get_by_role("button", name="검색").click()
            time.sleep(5)

            # JSON 데이터와 UI 데이터를 비교
            test_cases = [
                {"row_index": 8, "expected": {"pattern_count": "0", "keyword_count": "0", "file_count": "0"}},  # 일반 로깅
                {"row_index": 6, "expected": {"pattern_count": "1", "keyword_count": "0", "file_count": "0"}},  # 개인정보 로깅
                {"row_index": 4, "expected": {"pattern_count": "0", "keyword_count": "2", "file_count": "0"}},  # 키워드 로깅
                {"row_index": 2, "expected": {"pattern_count": "14", "keyword_count": "0", "file_count": "1"}},  # 첨부파일 로깅
            ]

            for case in test_cases:
                compare_ui_and_json(page, case["row_index"], case["expected"])

            print("모든 값이 일치합니다.")


        except Exception as e:

            # 실패 시 스크린샷 저장

            screenshot_path = get_screenshot_path("test_compare_result_naver_mail")
            page.screenshot(path=screenshot_path, type="jpeg", quality=80)
            print(f"Screenshot saved at: {screenshot_path}")

            raise

        finally:
            browser.close()


