# 파일명: main.py
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()

# 요청 바디로 받을 데이터 모델 정의
class PostData(BaseModel):
    now: str = Field(..., alias="현재시간")
    block_time: str = Field(..., alias="차단일시")
    subject: str = Field(..., alias="제목")
    type_name: str = Field(..., alias="타입")
    service_name: str = Field(..., alias="서비스")
    from_addr: str = Field(..., alias="발신자")
    to_addr: str = Field(..., alias="수신자")
    cc_addr: str = Field(None, alias="참조")
    bcc_addr: str = Field(None, alias="숨은참조")
    reason: str = Field(None, alias="차단/감시 사유")
    user_name: str = Field(None, alias="사용자명")
    user_mail: str = Field(None, alias="사용자메일")
    user_position: str = Field(None, alias="사용자직급")
    source_ip: str = Field(None, alias="발신IP")
    destination_ip: str = Field(None, alias="수신IP")
    group_name: str = Field(None, alias="부서명")
    rule_name: str = Field(None, alias="정책명")
    file_name: str = Field(None, alias="파일명")
    detect_info: str = Field(None, alias="상세검출내역")
    detect_count: str = Field(None, alias="상세검출건수")
    pattern_count: str = Field(None, alias="개인정보 검출수")
    keyword_count: str = Field(None, alias="키워드 검출수")
    file_count: str = Field(None, alias="파일개수")

# 간단한 GET 엔드포인트
@app.get("/api/get")
def read_root():
    return {"message": "Hello World!"}

# JSON 데이터를 받는 POST 엔드포인트
@app.post("/api/post")
def create_post(data: PostData):
    # 데이터를 그대로 리턴하거나, 필요한 처리를 추가할 수 있습니다.
    return {"post": data}

# 개발 환경에서 서버 실행 (테스트용)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="172.16.150.132", port=8000)
