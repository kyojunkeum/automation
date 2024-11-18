# Python 3.12.3 버전을 포함한 Docker 이미지 사용
FROM python:3.12.3

# 작업 디렉토리를 생성하고 설정
WORKDIR /app

# 요구 패키지 파일 requirements.txt를 이미지에 복사
COPY requirements.txt .

# 패키지 설치
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트의 모든 파일을 컨테이너로 복사
COPY . .

# 기본적으로 실행할 명령을 설정합니다. 예를 들어 main.py를 실행하려면:
CMD ["pytest", "-s", "-v", "--headed", "--html=report.html", "--self-contained-html"]
