import subprocess
import sys
import os
import paramiko
import time
import shutil
import json
import stat  # 디렉터리 여부 판별용


# ---- 작업 디렉토리 고정 (어디서 실행해도 dlp_new_automation 기준이 되도록) ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)


def run_tests_and_generate_report():
    env = os.environ.copy()
    env["PATH"] += ";C:\\allure\\allure-2.32.0\\bin"

    try:
        # 테스트 결과 저장 디렉토리 생성
        results_dir = "allure-results"
        os.makedirs(results_dir, exist_ok=True)

        # 1. 테스트 반복 실행
        for i in range(1, 2):
            print(f"{i}번째 테스트를 실행합니다...")
            result_dir = f"{results_dir}/run_{i}"
            os.makedirs(result_dir, exist_ok=True)

            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "-v", f"--alluredir={result_dir}"],
                env=env
            )

            if proc.returncode != 0:
                print(f"{i}번째 테스트에서 오류 발생(returncode={proc.returncode}). 반복을 중단합니다.")
                break

        # 2. Allure 리포트 생성 및 병합
        # ❗ allure-results 는 지우면 안 됨 (여기에 테스트 결과가 들어있음)
        if os.path.exists("allure-report"):
            shutil.rmtree("allure-report")

        print("Allure 리포트를 생성합니다...")

        # run_1 ~ run_49 중 실제로 존재하는 디렉터리만 사용
        result_dirs = [f"{results_dir}/run_{i}" for i in range(1, 50)]
        valid_results = [d for d in result_dirs if os.path.exists(d)]

        if not valid_results:
            print("유효한 테스트 결과가 없습니다. 리포트 생성 중단!")
            return

        generate_command = [
            "C:\\allure\\allure-2.32.0\\bin\\allure.bat",
            "generate",
            "--clean",
            "-o",
            "allure-report",
        ]
        generate_command.extend(valid_results)

        subprocess.run(generate_command, check=True, env=env)

    except Exception as e:
        print(f"테스트/리포트 실행 중 오류 발생: {e}")
        sys.exit(1)


def ensure_remote_directory_exists(sftp, remote_directory):
    """
    원격 서버에 디렉토리가 없으면 생성하는 함수입니다.
    """
    directories = remote_directory.split('/')
    path = ''
    for directory in directories:
        if directory:  # 빈 문자열 방지
            path += f'/{directory}'
            try:
                sftp.stat(path)  # 디렉토리가 존재하는지 확인
            except FileNotFoundError:
                sftp.mkdir(path)  # 디렉토리가 없으면 생성


# ----------------- 여기서부터 index.html 생성 함수 -----------------

def build_index_html(sftp, base_remote_path="/var/www/html/allure-report"):
    """
    서버에 존재하는 모든 타임스탬프 리포트 폴더를 읽어서
    /allure-report/index.html 을 생성한다.

    - 각 폴더의 widgets/summary.json 을 읽어서 통계(total, passed, failed 등)를 가져옴
    - 전체 합계를 상단에 표시
    - 아래에 실행별 토글(details) 목록을 만든다.
    """
    runs = []

    # 1) 하위 디렉토리(타임스탬프 폴더) 목록 수집
    for name in sftp.listdir(base_remote_path):
        run_dir = f"{base_remote_path}/{name}"

        # 디렉터리인지 확인
        try:
            attr = sftp.stat(run_dir)
        except IOError:
            continue
        if not stat.S_ISDIR(attr.st_mode):
            continue

        summary_path = f"{run_dir}/widgets/summary.json"

        try:
            with sftp.open(summary_path, "r") as f:
                summary = json.load(f)
        except IOError:
            # summary.json 없는 폴더는 무시
            continue

        statis = summary.get("statistic", {})
        runs.append({
            "name": name,
            "total": statis.get("total", 0),
            "passed": statis.get("passed", 0),
            "failed": statis.get("failed", 0),
            "broken": statis.get("broken", 0),
            "skipped": statis.get("skipped", 0),
        })

    # 폴더가 하나도 없으면 기본 안내 페이지 생성
    if not runs:
        empty_html = """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <title>Allure Report Dashboard</title>
</head>
<body>
  <h1>Allure Report Dashboard</h1>
  <p>아직 생성된 리포트가 없습니다.</p>
</body>
</html>
"""
        with sftp.open(f"{base_remote_path}/index.html", "w") as f:
            f.write(empty_html)
        return

    # 최신순 정렬 (타임스탬프 문자열이기 때문에 역순 정렬로 충분)
    runs.sort(key=lambda r: r["name"], reverse=True)

    # 전체 합계 계산
    total_all = sum(r["total"] for r in runs)
    passed_all = sum(r["passed"] for r in runs)
    failed_all = sum(r["failed"] for r in runs)
    broken_all = sum(r["broken"] for r in runs)
    skipped_all = sum(r["skipped"] for r in runs)

    # 2) HTML 문자열 생성
    html_parts = []
    html_parts.append("""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8" />
  <title>Allure Report Dashboard</title>
  <style>
    body { font-family: sans-serif; max-width: 900px; margin: 20px auto; }
    h1 { margin-bottom: 5px; }
    .meta { color: #666; font-size: 13px; margin-bottom: 15px; }
    .summary-box { padding: 10px 12px; border-radius: 8px; background: #f5f5f5; margin-bottom: 20px; }
    .summary-box span { margin-right: 10px; }
    .good { color: #4caf50; font-weight: bold; }
    .bad { color: #f44336; font-weight: bold; }
    .broken { color: #ff9800; font-weight: bold; }
    .skipped { color: #9e9e9e; }
    details.run { border: 1px solid #ddd; border-radius: 6px; margin: 6px 0; padding: 6px 10px; }
    details.run[open] { border-color: #4caf50; }
    details.run summary { cursor: pointer; }
  </style>
</head>
<body>
  <h1>DLP Test Results Dashboard</h1>
""")

    html_parts.append(
        f'  <div class="summary-box">\n'
        f'    <div>전체 테스트 수: <strong>{total_all}</strong></div>\n'
        f'    <div>\n'
        f'      <span class="good">Passed: {passed_all}</span>\n'
        f'      <span class="bad">Failed: {failed_all}</span>\n'
        f'      <span class="broken">Broken: {broken_all}</span>\n'
        f'      <span class="skipped">Skipped: {skipped_all}</span>\n'
        f'    </div>\n'
        f'  </div>\n'
    )

    html_parts.append('  <p class="meta">아래 목록에서 실행별 리포트를 펼쳐서 확인하세요.</p>\n')

    # 실행별 토글 목록
    for r in runs:
        name = r["name"]
        html_parts.append(
            f'  <details class="run">\n'
            f'    <summary>\n'
            f'      {name} '
            f'      <span class="good">P:{r["passed"]}</span>\n'
            f'      <span class="bad">F:{r["failed"]}</span>\n'
            f'      <span class="broken">B:{r["broken"]}</span>\n'
            f'      <span class="skipped">S:{r["skipped"]}</span>\n'
            f'    </summary>\n'
            f'    <p class="meta">\n'
            f'      <a href="{name}/">▶ 이 실행의 리포트 열기</a>\n'
            f'    </p>\n'
            f'  </details>\n'
        )

    html_parts.append("</body>\n</html>\n")

    html_content = "".join(html_parts)

    # 3) index.html 을 서버에 기록
    with sftp.open(f"{base_remote_path}/index.html", "w") as f:
        f.write(html_content)


# ----------------- 여기까지 index.html 생성 함수 -----------------


def upload_report():
    hostname = "172.16.150.138"
    username = "root"
    password = "dkswjswmd138*"  # 비밀번호를 필요에 따라 입력

    # SSH 클라이언트 설정
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # SSH 연결
        ssh.connect(hostname, username=username, password=password)

        # SFTP 세션 생성
        sftp = ssh.open_sftp()
        local_path = "allure-report"  # 로컬 Allure 리포트 폴더

        # 타임스탬프 기반 하위 디렉토리 생성 (예: 2025-11-20_101530)
        timestamp = time.strftime("%Y-%m-%d_%H%M%S")
        base_remote_path = "/var/www/html/allure-report"
        remote_path = f"{base_remote_path}/{timestamp}"

        # 리포트 폴더의 파일들 전송
        for root, dirs, files in os.walk(local_path):
            for filename in files:
                local_file = os.path.join(root, filename)
                relative_path = os.path.relpath(local_file, local_path)
                remote_file = os.path.join(remote_path, relative_path).replace("\\", "/")

                ensure_remote_directory_exists(sftp, os.path.dirname(remote_file))
                sftp.put(local_file, remote_file)
                print(f"{local_file} -> {remote_file} 전송 완료")

        print("Allure 리포트가 성공적으로 전송되었습니다.")

        # 🔥 여기서 index.html 새로 생성
        build_index_html(sftp, base_remote_path=base_remote_path)

    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        try:
            sftp.close()
        except Exception:
            pass
        ssh.close()


if __name__ == "__main__":

    repeat_count = 1
    interval = 5

    for _ in range(repeat_count):
        try:
            # 테스트 및 리포트 생성 실행
            run_tests_and_generate_report()

            # 리포트를 서버로 전송 + index.html 갱신
            upload_report()
        except Exception as e:
            print(f"에러 발생: {e}")

        time.sleep(interval)

    print("모든 작업 완료")
