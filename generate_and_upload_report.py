import subprocess
import sys
import os
import paramiko


def run_tests_and_generate_report():
    env = os.environ.copy()
    env["PATH"] += ";C:\\allure\\allure-2.32.0\\bin"

    try:
        # 1. 테스트 코드 실행
        print("테스트를 실행합니다...")
        result = subprocess.run(["pytest", "-v", "--alluredir=allure-results"], check=False, env=env)

        # 2. Allure 리포트 생성
        print("Allure 리포트를 생성합니다...")
        subprocess.run(["C:\\allure\\allure-2.32.0\\bin\\allure.bat", "generate", "allure-results", "--clean", "-o",
                        "allure-report"], check=False, env=env)
        print("Allure generate command output:", result.stdout)
        print("Allure generate command error:", result.stderr)

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
    password = "qkfwjswmd138**"  # 비밀번호를 필요에 따라 입력

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
    # 테스트 및 리포트 생성 실행
    run_tests_and_generate_report()

    # 리포트를 서버로 전송
    upload_report()
