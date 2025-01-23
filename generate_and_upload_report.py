import subprocess
import sys
import os
import paramiko
import time


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
            subprocess.run(["pytest", "-v", f"--alluredir={result_dir}"], check=False, env=env)

        # 2. Allure 리포트 생성 및 병합
        print("Allure 리포트를 생성합니다...")
        result_dirs = [f"{results_dir}/run_{i}" for i in range(1, 2)]
        generate_command = ["C:\\allure\\allure-2.32.0\\bin\\allure.bat", "generate", "--clean", "-o", "allure-report"]
        generate_command.extend(result_dirs)

        subprocess.run(generate_command, check=True, env=env)

        # # 1. 테스트 10회 반복
        # for i in range(1, 11):
        #     print(f"{i}번째 테스트를 실행합니다...")
        #     result_dir = f"allure-results/run_{i}"
        #     os.makedirs(result_dir, exist_ok=True)  # 고유 결과 디렉토리 생성
        #
        #     result = subprocess.run(["pytest", "-v", f"--alluredir={result_dir}"], check=False, env=env)
        #     if result.returncode != 0:
        #         print(f"{i}번째 테스트에서 오류가 발생했습니다. 계속 진행합니다...")
        #
        # # 2. Allure 결과 병합
        # print("테스트 결과를 병합합니다...")
        # subprocess.run(["C:\\allure\\allure-2.32.0\\bin\\allure.bat", "merge", "allure-results/run_*", "-o",
        #                 "allure-results"], check=False, env=env)

        # # 1. 테스트 코드 실행
        # print("테스트를 실행합니다...")
        # result = subprocess.run(["pytest", "-v", "--alluredir=allure-results"], check=False, env=env)

        # # 2. Allure 리포트 생성
        # print("Allure 리포트를 생성합니다...")
        # subprocess.run(["C:\\allure\\allure-2.32.0\\bin\\allure.bat", "generate", "allure-results", "--clean", "-o",
        #                 "allure-report"], check=False, env=env)
        # print("Allure generate command output:", result.stdout)
        # print("Allure generate command error:", result.stderr)

    except subprocess.CalledProcessError as e:
        print(f"오류 발생: {e}")
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
        remote_path = "/var/www/html/allure-report"  # 원격 서버 경로

        # 리포트 폴더의 파일들 전송
        for root, dirs, files in os.walk(local_path):
            for filename in files:
                local_file = os.path.join(root, filename)
                relative_path = os.path.relpath(local_file, local_path)
                remote_file = os.path.join(remote_path, relative_path).replace("\\", "/")

                # 원격 경로에 폴더가 없으면 생성
                ensure_remote_directory_exists(sftp, os.path.dirname(remote_file))
                sftp.put(local_file, remote_file)
                print(f"{local_file} -> {remote_file} 전송 완료")

        print("Allure 리포트가 성공적으로 전송되었습니다.")

    except Exception as e:
        print(f"오류 발생: {e}")
    finally:
        sftp.close()
        ssh.close()


if __name__ == "__main__":

    repeat_count = 2
    interval = 5

    for _ in range(repeat_count):
        try:

            # 테스트 및 리포트 생성 실행
            run_tests_and_generate_report()

            # 리포트를 서버로 전송
            upload_report()
        except Exception as e:
            # 에러 처리
            print(F"에러 발생: {e}")

        time.sleep(interval)

    print("모든 작업 완료")