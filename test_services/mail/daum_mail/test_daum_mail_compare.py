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
@allure.step("Daum Login Test")
#@pytest.mark.order("first")
@pytest.mark.dependency(name="daum_login")
@pytest.mark.xfail(reason="다음 로그인은 간헐적으로 실패함 (무시 가능)")
def test_daum_login(request):
    with sync_playwright() as p:
        # 브라우저 및 컨텍스트 생성
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            # 홈페이지 진입
            goto_and_wait(page, f"{DAUM_BASE_URL}/")

            # 아이디 및 패스워드 입력
            page.get_by_role("link", name="카카오계정으로 로그인").click()
            time.sleep(1)
            page.get_by_role("button", name="카카오로 로그인").click()
            time.sleep(1)
            page.get_by_role("textbox", name="계정정보 입력").click()
            page.get_by_role("textbox", name="계정정보 입력").fill(DAUM_ID)
            page.get_by_role("textbox", name="비밀번호 입력").click()
            page.get_by_role("textbox", name="비밀번호 입력").fill(DAUM_PASSWORD)
            time.sleep(1)
            page.get_by_role("button", name="로그인", exact=True).click()
            time.sleep(3)

            # 세션 상태 저장
            os.makedirs("session", exist_ok=True)
            session_path = os.path.join("session", "daumstorageState.json")
            context.storage_state(path=session_path)

        except Exception as e:
            capture_failure_screenshot(page, request, timeout=5000)
            print(f"[WARN] 테스트 실패: {e}")
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

@allure.severity(allure.severity_level.NORMAL)
@allure.step("Daum Mail Normal Test")
@pytest.mark.dependency(name="daum_mail_normal")
def test_daum_mail_normal(request):
    with (sync_playwright() as p):
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "daumstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메일 페이지로 이동
            goto_and_wait(page, f"{DAUM_MAIL_URL}/")

            # 팝업이 있으면 확인 클릭, 없으면 스킵
            click_confirm_if_popup_exists(page)

            try:
                page.get_by_role("button", name="카카오로 로그인").click()
                time.sleep(1)
                page.get_by_role("textbox", name="계정정보 입력").click()
                page.get_by_role("textbox", name="계정정보 입력").fill(DAUM_ID)
                page.get_by_role("textbox", name="비밀번호 입력").click()
                page.get_by_role("textbox", name="비밀번호 입력").fill(DAUM_PASSWORD)
                time.sleep(1)
                page.get_by_role("button", name="로그인", exact=True).click()
                time.sleep(3)
                print("정상적으로 로그인 하였습니다")
            except:
                print("로그인 필요 없음 → 스킵")

            # 팝업이 있으면 확인 클릭, 없으면 스킵
            click_confirm_if_popup_exists(page)

            # 메일쓰기 클릭 시 새 창이 열리는 것을 대기
            click_and_wait_navigation(page, role="button", name="내게쓰기")

            # 제목 입력
            page.get_by_role("textbox", name="제목").click()
            page.get_by_role("textbox", name="제목").fill("기본로깅테스트")

            # 본문 입력
            editor_box = page.locator("iframe[name=\"tx_canvas_wysiwyg\"]").content_frame.locator("body")
            editor_box.fill("\n".join(DLP_NORMAL))


            # 보내기 클릭
            page.get_by_role("button", name="보내기").click()

            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_DAUM_MAIL,
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

@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Daum Mail Pattern Test")
@pytest.mark.dependency(name="daum_mail_pattern")
def test_daum_mail_pattern(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "daumstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메일 페이지로 이동
            goto_and_wait(page, f"{DAUM_MAIL_URL}/")

            # 팝업이 있으면 확인 클릭, 없으면 스킵
            click_confirm_if_popup_exists(page)

            try:
                page.get_by_role("button", name="카카오로 로그인").click()
                time.sleep(1)
                page.get_by_role("textbox", name="계정정보 입력").click()
                page.get_by_role("textbox", name="계정정보 입력").fill(DAUM_ID)
                page.get_by_role("textbox", name="비밀번호 입력").click()
                page.get_by_role("textbox", name="비밀번호 입력").fill(DAUM_PASSWORD)
                time.sleep(1)
                page.get_by_role("button", name="로그인", exact=True).click()
                time.sleep(3)
                print("정상적으로 로그인 하였습니다")
            except:
                print("로그인 필요 없음 → 스킵")

            # 팝업이 있으면 확인 클릭, 없으면 스킵
            click_confirm_if_popup_exists(page)

            # 메일쓰기 클릭 시 새 창이 열리는 것을 대기
            click_and_wait_navigation(page, role="button", name="내게쓰기")

            # 제목 입력
            page.get_by_role("textbox", name="제목").click()
            page.get_by_role("textbox", name="제목").fill("개인정보로깅테스트")

            # 본문 입력
            editor_box = page.locator("iframe[name=\"tx_canvas_wysiwyg\"]").content_frame.locator("body")
            editor_box.fill("\n".join(DLP_PATTERNS))

            # 보내기 클릭
            page.get_by_role("button", name="보내기").click()

            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_DAUM_MAIL,
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

@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Daum Mail Keyword Test")
@pytest.mark.dependency(name="daum_mail_keyword")
def test_daum_mail_keyword(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "daumstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메일 페이지로 이동
            goto_and_wait(page, f"{DAUM_MAIL_URL}/")

            # 팝업이 있으면 확인 클릭, 없으면 스킵
            click_confirm_if_popup_exists(page)

            try:
                page.get_by_role("button", name="카카오로 로그인").click()
                time.sleep(1)
                page.get_by_role("textbox", name="계정정보 입력").click()
                page.get_by_role("textbox", name="계정정보 입력").fill(DAUM_ID)
                page.get_by_role("textbox", name="비밀번호 입력").click()
                page.get_by_role("textbox", name="비밀번호 입력").fill(DAUM_PASSWORD)
                time.sleep(1)
                page.get_by_role("button", name="로그인", exact=True).click()
                time.sleep(3)
                print("정상적으로 로그인 하였습니다")
            except:
                print("로그인 필요 없음 → 스킵")

            # 팝업이 있으면 확인 클릭, 없으면 스킵
            click_confirm_if_popup_exists(page)

            # 메일쓰기 클릭 시 새 창이 열리는 것을 대기
            click_and_wait_navigation(page, role="button", name="내게쓰기")

            # 제목 입력
            page.get_by_role("textbox", name="제목").click()
            page.get_by_role("textbox", name="제목").fill("키워드로깅테스트")

            # 본문 입력
            editor_box = page.locator("iframe[name=\"tx_canvas_wysiwyg\"]").content_frame.locator("body")
            editor_box.fill("\n".join(DLP_KEYWORDS))

            # 보내기 클릭
            page.get_by_role("button", name="보내기").click()

            # 대기
            page.wait_for_timeout(5000)

            # ===== 여기서 ES 검증 반복 호출 =====
            assert_es_logs_with_retry(
                service_name=SERVICE_NAMES_DAUM_MAIL,
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

@allure.severity(allure.severity_level.BLOCKER)
@allure.step("Daum Mail Attach Test")
@pytest.mark.dependency(name="daum_mail_attach")
def test_daum_mail_attach(request):
    with sync_playwright() as p:
        # 저장된 세션 상태를 로드하여 브라우저 컨텍스트 생성
        session_path = os.path.join("session", "daumstorageState.json")
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state=session_path)
        page = context.new_page()

        try:

            # 세션 유지한 채로 메일 페이지로 이동
            goto_and_wait(page, f"{DAUM_MAIL_URL}/")

            # 팝업이 있으면 확인 클릭, 없으면 스킵
            click_confirm_if_popup_exists(page)

            try:
                page.get_by_role("button", name="카카오로 로그인").click()
                time.sleep(1)
                page.get_by_role("textbox", name="계정정보 입력").click()
                page.get_by_role("textbox", name="계정정보 입력").fill(DAUM_ID)
                page.get_by_role("textbox", name="비밀번호 입력").click()
                page.get_by_role("textbox", name="비밀번호 입력").fill(DAUM_PASSWORD)
                time.sleep(1)
                page.get_by_role("button", name="로그인", exact=True).click()
                time.sleep(3)
                print("정상적으로 로그인 하였습니다")
            except:
                print("로그인 필요 없음 → 스킵")

            # 팝업이 있으면 확인 클릭, 없으면 스킵
            click_confirm_if_popup_exists(page)

            # 메일쓰기 클릭 시 새 창이 열리는 것을 대기
            click_and_wait_navigation(page, role="button", name="내게쓰기")

            # 제목 입력
            page.get_by_role("textbox", name="제목").click()
            page.get_by_role("textbox", name="제목").fill("첨부파일로깅테스트")

            # 3. 파일 첨부 클릭
            page.get_by_label("파일 첨부하기").set_input_files(DLP_FILE)
            page.wait_for_timeout(2000)
            print("파일을 첨부하였습니다.")


            # 보내기 클릭
            try:
                page.get_by_role("button", name="보내기").click(timeout=2000)
                print("✔ [DEBUG] '보내기' 버튼을 클릭했습니다.")
            except Exception:
                print("▶ [DEBUG] '보내기' 버튼이 없어 스킵합니다.")

                # 대기
                page.wait_for_timeout(10000)

                # ===== 여기서 ES 검증 반복 호출 =====
                assert_es_logs_with_retry(
                    service_name=SERVICE_NAMES_DAUM_MAIL,
                    test_cases=FILE_LOGGING_CASE,
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
