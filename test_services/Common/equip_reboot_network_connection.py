import asyncio
import socket
from playwright.async_api import async_playwright
import requests
import subprocess
import paramiko  # SSH 라이브러리

# ✅ TCP ping 함수
def tcp_ping(host, port=80, timeout=5):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False

# ✅ SSH로 재부팅 명령 전송
def reboot_device_ssh(host, username, password):
    print("[INFO] SSH 접속 중...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=host, username=username, password=password)

    print("[INFO] reboot 명령 실행 중...")
    ssh.exec_command("reboot")
    ssh.close()

# 인터넷 접속 확인 함수
def check_internet_connection(test_url="https://www.daum.net"):
    try:
        response = requests.get(test_url, timeout=10, verify=False)
        print(f"[DEBUG] 응답 코드: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] 인터넷 요청 실패: {e}")
        return False

# ✅ 전체 통합 시나리오
async def run_single_test(iteration_num):
    print(f"\n========== [테스트 반복 {iteration_num}] 시작 ==========")

    # ✅ 사용자 입력
    target_ip = "172.16.150.187"
    username = "root"
    password = "dkswjswmd187*"
    network_port = 80
    internet_url = "https://www.daum.net"
    daum_test_path = "D:/dlp_new_automation/test_services/mail/daum_mail/test_daum_mail_compare.py"

    try:
        # 장비 SSH 재부팅
        reboot_device_ssh(target_ip, username, password)

        # ✅ 2. TCP Ping 재시도 (네트워크 복구 확인)
        host_ip = socket.gethostbyname('www.daum.net')
        for i in range(100):
            if tcp_ping(host_ip, port=network_port):
                print(f"[PASS] TCP 연결 성공 ({i + 1}회 시도)")
                break
            else:
                print(f"[INFO] TCP 연결 실패... 재시도 중 ({i + 1}/100)")
                await asyncio.sleep(5)
        else:
            print("[FAIL] TCP 연결 실패. 네트워크 장애로 간주.")
            return

            # ✅ 3. 인터넷 확인 + Daum 테스트 실행
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context(ignore_https_errors=True)
            page = await context.new_page()

            print(f"[INFO] 인터넷 접속 확인 시작: {internet_url}")
            for j in range(10):
                try:
                    await page.goto(internet_url)
                    if check_internet_connection(internet_url):
                        print(f"[PASS] 인터넷 연결 정상 ({j + 1}회 시도)")
                        print(">>> 최종 결과: PASS")

                        # ✅ Daum 테스트 실행
                        print(f"[INFO] Daum 메일 로깅 발생 테스트 실행: {daum_test_path}")
                        subprocess.run(["pytest", daum_test_path], check=True)
                        await browser.close()
                        return "PASS"
                except Exception as e:
                    print(f"[FAIL] 인터넷 연결 실패... 재시도 중 ({j + 1}/10): {e}")
                    await asyncio.sleep(5)

            await browser.close()
            print(">>> 최종 결과: FAIL (인터넷 연결 안 됨)")
            return "FAIL"

    except Exception as e:
        print(f"[ERROR] 테스트 중 예외 발생: {e}")
        return "FAIL"

# ✅ 전체 반복 실행 및 요약 출력
async def repeat_test(n):
    results = []
    for i in range(1, n+1):
        result = await run_single_test(i)
        results.append((i, result))

    # ✅ 요약 출력
    print("\n========== [테스트 요약] ==========")
    for i, result in results:
        print(f"반복 {i}: {result}")

    total_pass = sum(1 for _, r in results if r == "PASS")
    total_fail = n - total_pass
    print(f"\n총 반복 횟수: {n}")
    print(f"성공: {total_pass}회")
    print(f"실패: {total_fail}회")

# ✅ 실행
asyncio.run(repeat_test(50))  # ← 반복 횟수 설정