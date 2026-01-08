import asyncio
from playwright.async_api import async_playwright
import socket
import requests
import subprocess
import os

async def click_confirm_if_popup_exists(page, timeout=3000):
    """
    '확인' 버튼을 가진 팝업이 뜨면 해당 버튼을 찾아 클릭한다.
    나타나지 않으면(TimeoutError) 아무 처리도 하지 않는다.
    """
    try:
        await page.wait_for_selector("role=button[name='확인']", timeout=timeout)
        await page.get_by_role("button", name="확인").click()
        print("알림 팝업의 '확인' 버튼을 클릭했습니다.")
    except TimeoutError:
        print("알림 팝업(확인 버튼)이 나타나지 않았습니다.")

# TCP ping 함수
def tcp_ping(host, port=80, timeout=5):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False

# 인터넷 접속 확인 함수
def check_internet_connection(test_url="https://www.daum.net"):
    try:
        response = requests.get(test_url, timeout=10, verify=False)
        print(f"[DEBUG] 응답 코드: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] 인터넷 요청 실패: {e}")
        return False

# 메인 자동화 시나리오
async def run_test():
    internet_url = "https://www.daum.net"
    daum_test_path = "D:/dlp_new_automation/test_services/mail/daum_mail/test_daum_mail_compare.py"



    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # GUI로 보여줌
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()

        # ✅ 사용자 입력: 제품 웹 UI 주소
        await page.goto("https://xxx.xxx.xxx.xxx:xxxx/login")  # 예: http://192.168.0.1/admin

        # ✅ 사용자 입력: 로그인 입력 필드 및 로그인 동작
        await page.fill("input[name='j_username']", "id")
        await page.fill("input[name='j_password']", "password")
        # await page.get_by_role("button", name="로그인").click()

        try:
            # "로그인" 또는 "Login" 텍스트를 가진 버튼 중 하나 클릭 시도
            login_button = page.locator("button:has-text('로그인'), button:has-text('Login')")
            await login_button.first.click()
            print("[INFO] 로그인 버튼 클릭 성공")
        except Exception as e:
            print("[ERROR] 로그인 버튼 클릭 실패:", e)
            await page.screenshot(path="login_click_failed.png")
            content = await page.content()
            with open("login_page_debug.html", "w", encoding="utf-8") as f:
                f.write(content)
            raise
        # await click_confirm_if_popup_exists(page)

        # 페이지 로딩 대기
        # 알림 팝업 처리
        await click_confirm_if_popup_exists(page, timeout=5000)

        # ✅ 사용자 입력: 특정 버튼 클릭 페이지로 이동
        await page.goto("https://xxx.xxx.xxx.xxx:xxxx/system/serversetting")  # 재기동 페이지 이동

        # ✅ 사용자 입력: SW 재기동 버튼 클릭
        await page.get_by_role("button", name="코어 재기동").click()
        await page.get_by_role("button", name="재기동", exact=True).click()
        await asyncio.sleep(10)
        await page.get_by_role("button", name="확인").click()

        # 재기동 대기 시간 (예: 60초)
        print("SW 재기동 중... 대기 중...")
        await asyncio.sleep(10)  # 실제 상황에 맞게 조정 필요

        # ✅ 사용자 입력: www.naver.com 의 IP 주소 (재기동 후 ping 대상)
        host_ip = socket.gethostbyname('www.daum.net')

        # TCP Ping 테스트 (예: 5초 간격으로 최대 10회 재시도)
        for i in range(10):
            if tcp_ping(host_ip, port=80):
                print(f"[PASS] TCP 연결 성공 ({i+1}회 시도)")
                break
            else:
                print(f"[INFO] TCP 연결 실패... 재시도 중 ({i+1}/10)")
                await asyncio.sleep(5)
        else:
            print("[FAIL] TCP 연결 실패. 네트워크 장애로 간주.")
            return "FAIL"

        await browser.close()

        # ✅ 3. 인터넷 확인 + Daum 테스트 실행
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(ignore_https_errors=True)
            page = await context.new_page()

            print(f"[INFO] 인터넷 접속 확인 시작: {internet_url}")
            for j in range(15):
                try:
                    await asyncio.sleep(10)
                    await page.goto(internet_url)
                    if check_internet_connection(internet_url):
                        print(f"[PASS] 인터넷 연결 정상 ({j + 1}회 시도)")
                        print(">>> 최종 결과: PASS")
                        return "PASS"

                        # # ✅ Daum 테스트 실행
                        # print(f"[INFO] Daum 메일 로깅 발생 테스트 실행: {daum_test_path}")
                        # try:
                        #     subprocess.run(["pytest", daum_test_path], check=True)
                        #     print(">>> dlp logging test result: PASS")
                        #     await browser.close()
                        #     return "PASS"
                        # except subprocess.CalledProcessError as e:
                        #     print(">>> dlp logging test result: FAIL")
                        #     await browser.close()
                        #     return "FAIL"
                except Exception as e:
                    print(f"[FAIL] 인터넷 연결 실패... 재시도 중 ({j + 1}/15): {e}")
                    await asyncio.sleep(5)

            await browser.close()
            print(">>> 최종 결과: FAIL (인터넷 연결 안 됨)")
            return "FAIL"

async def repeat_test(n):
    results = []
    for k in range(n):
        print(f"\n========== [테스트 반복 {k+1}/{n}] ==========")
        try:
            result = await run_test()
            results.append((k+1, result))
        except Exception as e:
            print(f"[ERROR] 테스트 {k+1} 실패 : {e}")
            results.append((k+1, "FAIL"))
        await asyncio.sleep(3)
    for m, result in results:
        print(f" - 반복 {m}: {result}")

    # ✅ 요약 출력
    print("\n========== [테스트 요약] ==========")
    for i, result in results:
        print(f"반복 {i}: {result}")

    total_pass = sum(1 for _, r in results if r == "PASS")
    total_fail = n - total_pass
    print(f"\n총 반복 횟수: {n}")
    print(f"성공: {total_pass}회")
    print(f"실패: {total_fail}회")

# 실행
asyncio.run(repeat_test(100))

