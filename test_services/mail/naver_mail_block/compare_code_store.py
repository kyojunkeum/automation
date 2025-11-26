import os
import time
import json

import pytest
from playwright.sync_api import Page, sync_playwright



def default_path():
    os.chdir(os.path.dirname(__file__))

def change_format_json_file(file_path):
    # 파일이 비어있는지 확인
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as x:
        if x.read().strip() == '':
            return  # 파일이 비어있으면 아무 작업도 수행하지 않음

    # JSON 형식을 올바르게 변환
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as x:
        data = x.readlines()
        for i, sp_str in enumerate(data):
            if sp_str.strip() == "}]{":
                data[i] = "},{\n"
            elif sp_str.strip() == "}{":
                data[i] = "},{\n"

    with open(file_path, 'w', encoding='utf-8', errors='ignore') as x:
        x.write("[\n")
        x.writelines(data)
        x.write("]\n")
    print(f"Formatted JSON file saved at: {file_path}")

def dlp_login(page):
    with sync_playwright() as p:
        # 브라우저 및 컨텍스트 생성
        browser = p.chromium.launch(headless=False, ignore_https_errors=True)
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        try:
            # dlp 홈페이지 진입
            page.goto("https://172.16.150.185:8443/")
            time.sleep(2)

            # 아이디 및 패스워드 입력
            page.get_by_placeholder("아이디").fill("intsoosan")
            page.get_by_placeholder("비밀번호").fill("dkswjswmd4071*")
            page.get_by_role("button", name="로그인").click()

            # 세션 상태 저장
            os.makedirs("session", exist_ok=True)
            session_path = os.path.join("session", "dlpstorageState.json")
            context.storage_state(path=session_path)

        except Exception as e:
            pytest.fail(f"Test failed: {str(e)}")

        finally:
            browser.close()

def get_table_data(page: Page, table_id):
    # 테이블 요소 가져오기
    table = page.query_selector(f'#{table_id}')
    tbody = table.query_selector('tbody')
    tr_elements = tbody.query_selector_all('tr') if tbody else []

    return tr_elements


def get_service_log_detail_pattern(page: Page, plugin_name_kor, service_name='', file_type=''):
    print("DLP 로그 상세이력 가져오기")
    body = ''
    result = {}
    subject = ''

    # 개인정보 검출 내역 조회
    pm_all_count = page.locator('#patternMatchedInfo').inner_text()
    pm_title_tab = page.locator('#pm_title_tab').inner_text()
    pm_body_tab = page.locator('#pm_body_tab').inner_text()
    pm_attach_tab = page.locator('#pm_attach_tab').inner_text()
    pm_title_dis = page.locator('#pm_title_dis').inner_text()
    pm_body_dis = page.locator('#pm_body_dis').inner_text()
    pm_attach_dis = page.locator('#pm_attach_dis').inner_text()

    # 키워드 검출 내역 조회
    kw_all_count = page.locator('#keywordMatchedInfo').inner_text()
    kw_title_tab = page.locator('#kw_title_tab').inner_text()
    kw_body_tab = page.locator('#kw_body_tab').inner_text()
    kw_attach_tab = page.locator('#kw_attach_tab').inner_text()
    kw_title_dis = page.locator('#kw_title_dis').inner_text()
    kw_body_dis = page.locator('#kw_body_dis').inner_text()
    kw_attach_dis = page.locator('#kw_attach_dis').inner_text()

    # 메일, SNS, workshare: 본문 및 제목 조회
    if plugin_name_kor in ['메일', 'SNS', 'workshare']:
        # 제목 조회 후 저장
        subject = page.locator('#subject').inner_text()
        frame_name = ''

        # 프레임 선택
        if plugin_name_kor == '메일':
            frame_name = 'mailbody'
        elif plugin_name_kor == 'SNS':
            frame_name = 'snsbody'
        elif plugin_name_kor == 'workshare':
            frame_name = 'worksharebody'

        # 프레임 이동
        page.frame_locator(f'iframe[name="{frame_name}"]').locator('body').wait_for()
        body = page.frame_locator(f'iframe[name="{frame_name}"]').locator('body').inner_text()

    # 메신저: 제목 없이 본문 내 대화 내용 출력
    elif plugin_name_kor == '메신저':
        event_time = page.locator(
            '//*[@id="detail_service_body"]/div[1]/div[1]/div/div/div/div/div[2]/div[1]/div[2]/div/label').inner_text()
        event_time_body = page.locator('//*[@id="chatbody"]/li[1]/span[1]').inner_text()
        if event_time == event_time_body:
            subject = ''
            body = page.locator('//*[@id="chatbody"]/li[1]/div').inner_text()
        else:
            print("-> 메신저 본문 최상위 메시지의 발생 일시값과 상세 이력의 발생일시가 서로 일치하지 않음")
            return False

    # comment: 본문만 가져오기
    elif plugin_name_kor == 'comment':
        frame_name = 'commentbody'
        page.frame_locator(f'iframe[name="{frame_name}"]').locator('body').wait_for()
        body = page.frame_locator(f'iframe[name="{frame_name}"]').locator('body').inner_text()

    # 결과를 dict에 추가
    result.update({
        "개인정보 검출 내역": pm_all_count,
        "개인정보 제목 개수": pm_title_tab,
        "개인정보 본문 개수": pm_body_tab,
        "개인정보 첨부파일 개수": pm_attach_tab,
        "개인정보 제목 내용": pm_title_dis,
        "개인정보 본문 내용": pm_body_dis,
        "개인정보 첨부파일 내용": pm_attach_dis,
        "키워드 검출 내역": kw_all_count,
        "키워드 제목 개수": kw_title_tab,
        "키워드 본문 개수": kw_body_tab,
        "키워드 첨부파일 개수": kw_attach_tab,
        "키워드 제목 내용": kw_title_dis,
        "키워드 본문 내용": kw_body_dis,
        "키워드 첨부파일 내용": kw_attach_dis,
        "제목": subject,
        "내용": body
    })

    # 야후 메일의 경우 첨부파일 리스트 추가
    if service_name == '야후메일' and file_type == 'attachfile' or service_name == 'SMTP' and file_type == 'attachfile':
        page.frame_locator('iframe[name="file_list"]').locator('body').wait_for()
        file_rows = page.locator('#file_list tbody tr')
        if file_rows.count() > 0:
            first_row = file_rows.first
            result["파일 리스트 파일명"] = first_row.locator('td').nth(1).inner_text()
            result["파일 분석 여부"] = first_row.locator('td').nth(3).inner_text()
            result["추출텍스트"] = first_row.locator('td').nth(4).inner_text()
            result["개인정보 검출"] = first_row.locator('td').nth(5).inner_text()
            result["키워드 검출"] = first_row.locator('td').nth(6).inner_text()

    # 프레임을 부모로 이동 후 닫기 버튼 클릭
    page.frame_locator('iframe').locator('button:has-text("닫기")').click()
    print("-> 가져오기 완료")
    return result

def get_service_log_detail_attachfile(page: Page, service_name_kor='', service_id=''):
    print("DLP 로그 상세이력 가져오기(첨부파일)")
    result = {}

    # 개인정보 검출 내역 가져오기
    pm_all_count = page.locator('#patternMatchedInfo').inner_text()
    pm_attach_dis = page.locator('#pm_attach_dis').inner_text()

    # 키워드 검출 내역 가져오기
    kw_all_count = page.locator('#keywordMatchedInfo').inner_text()
    kw_attach_dis = page.locator('#kw_attach_dis').inner_text()

    # 파일 리스트의 값 가져오기
    rows = page.locator('#file_list_wrapper tbody tr')
    if rows.count() > 0:
        first_row_cells = rows.nth(0).locator('td')
        body_file_name = first_row_cells.nth(1).inner_text()

    # 상세내역 클릭
    page.locator('#detailViewBtn').click()
    page.wait_for_timeout(500)

    # 상세내역에서 개인정보, 키워드, 본문 내용 가져오기
    pm_tab = page.locator('#pm_tab').inner_text()
    pm_dis = page.locator('#pm_dis').inner_text()
    keyword_tab = page.locator('#keyword_tab').inner_text()
    # 키워드 검출 탭 클릭
    page.locator('#keyword_tab').click()
    page.wait_for_timeout(500)
    keyword_dis = page.locator('#keyword_dis').inner_text()
    fileExtractText = page.locator('#fileExtractText').inner_text()

    # dict에 결과 추가
    result["개인정보 검출 내역"] = pm_all_count
    result["개인정보 본문"] = pm_attach_dis
    result["키워드 검출 내역"] = kw_all_count
    result["키워드 본문"] = kw_attach_dis
    result["본문 파일명"] = body_file_name

    # 특정 서비스의 파일 이름 조건 확인 후 추가
    if service_name_kor in ['원드라이브(기타)', '미스리메신저'] or service_id == 'check_note':
        result["파일 리스트 파일명"] = ''
    else:
        result["파일 리스트 파일명"] = body_file_name

    result["파일 분석 여부"] = first_row_cells.nth(3).inner_text()
    result["추출텍스트"] = first_row_cells.nth(4).inner_text()
    result["개인정보 검출"] = first_row_cells.nth(5).inner_text()
    result["키워드 검출"] = first_row_cells.nth(6).inner_text()
    result["상세 개인정보 검출 개수"] = pm_tab
    result["상세 개인정보 본문"] = pm_dis
    result["상세 키워드 검출 개수"] = keyword_tab
    result["상세 키워드 본문"] = keyword_dis
    result["상세 본문"] = fileExtractText

    # 상세 내역 -> 닫기 버튼 클릭
    page.locator('#detail_file_body_modal button:has-text("닫기")').click()

    # 프레임 이동 후 닫기 클릭
    page.locator('#detail_service_body_modal button:has-text("닫기")').click()
    print("-> 가져오기 완료")
    return result

def get_service_log(page: Page, event_date, plugin_name_kor, service_name_kor, pattern_count, keyword_count,
                    file_count, file_type, subject='', body='', case_id='', service_id=''):
    print("-" * 50)
    print("DLP 서비스 로그 가져오기")
    body_list = []
    filter_plugin_name = ''

    # 로그/통계 메뉴 클릭
    page.get_by_role("link", name=" 로그/통계").click()

    # 상세 검색 클릭
    page.get_by_role("link", name="상세검색").click()
    page.wait_for_timeout(1000)  # Playwright에서는 time.sleep 대신 wait_for_timeout을 사용

    # 선택 상세(타입)
    page.locator("#selectedDetail").select_option("service")
    page.wait_for_timeout(1000)

    # 타입 선택을 위한 필드 클릭 및 필터 플러그인 이름 설정
    page.locator("#tokenfield2-tokenfield").click()
    page.get_by_text("[웹메일] 네이버메일").click()

   # 검색 버튼 클릭
    page.get_by_role("button", name="검색").click()
    page.wait_for_timeout(1000)

    # 차단만 보기 클릭
    page.get_by_role("link", name = "차단만 보기")
    page.wait_for_timeout(1000)

    # 전체 테이블 내용 가져오기
    paginate = page.query_selector_all('#log_list_paginate > ul > li')
    num = 4
    for page_num in range(len(paginate) - 4):
        tr_elements = get_table_data(page, 'log_list')
        for td in tr_elements:
            # device type에 따라 발생일시 컬럼 정보가 event_date와 일치하는지 확인
            body_list = [td.nth(1).inner_text(), td.nth(3).inner_text(), td.nth(4).inner_text(),
                         td.nth(8).inner_text(), td.nth(9).inner_text(), td.nth(10).inner_text()]

            td.nth(0).click()  # 검색된 로그 클릭
            page.wait_for_timeout(1000)

            # 상세 로그 가져오기
            if file_type == 'attachfile':
                if service_name_kor in ['야후메일', 'SMTP']:
                    log_detail = get_service_log_detail_pattern(page, plugin_name_kor, service_name_kor, file_type)
                else:
                    log_detail = get_service_log_detail_attachfile(page, service_name_kor, service_id)
            else:
                log_detail = get_service_log_detail_pattern(page, plugin_name_kor, service_name_kor, file_type)

            return body_list, log_detail

        page.click(f'//*[@id="log_list_paginate"]/ul/li[{num}]')
        num += 1

    print('-> 서비스 로그를 정상적으로 가져오지 못함\n')
    return body_list, '서비스 로그를 정상적으로 가져오지 못함'


def get_result(page, test_info, case_id, plugin_name, service_name, result_value, event_date, dlp_client_address):
    # Plugin name formatting
    if plugin_name == '메일':
        plugin_name = 'mail'

    # Error and failure handling
    error_message = test_info.error if test_info.error else None
    failure_message = test_info.failure if test_info.failure else None
    ok = not error_message and not failure_message

    # Determine test result
    if not ok or result_value == 0:
        if result_value == 0:
            typ, msg = 'FAIL', f'{event_date} 서비스 로그 혹은 서비스 상세 이력 값이 서로 다름'
        else:
            typ = 'ERROR' if error_message else 'FAIL'
            msg = error_message if error_message else failure_message
            msg = msg.split('\n')[1].strip()  # 첫 번째 줄 이후 메시지만 가져오기

        print(f"{dlp_client_address} - {plugin_name} - {service_name} - {case_id} 테스트 실패.....")
        print(f"{typ}: {test_info.name} - {msg}")
        print(f"{dlp_client_address} - {plugin_name} - {service_name} - {case_id} 테스트 성공!!!!!")

# DLP 로그인 및 로그 비교를 위한 함수
def compare_result_json_and_dlp(case, page: Page, plugin_name, service_name, file_path):
    # DLP 로그인
    dlp_login(page)
    default_path()

    # JSON 파일 읽기
    with open(file_path, 'r', encoding='utf-8') as json_file:
        json_data = json.load(json_file)

        for entry in json_data:
            if entry[plugin_name]["서비스 이름"] == service_name:
                service_id = entry[plugin_name]["서비스 이름"]
                case_id = entry[plugin_name]["자동화 테스트 케이스 ID"]
                event_date = entry[plugin_name]["발생일시"]
                plugin_name_kor = entry[plugin_name]["타입"]
                service_name_kor = entry[plugin_name]["서비스"]
                pattern_count = entry[plugin_name]["개인정보 검출수"]
                keyword_count = entry[plugin_name]["키워드 검출수"]
                file_count = entry[plugin_name]["파일 검출수"]

                # 파일 관련 처리
                if 'attachfile' in case_id or 'folder' in case_id or 'filename' in case_id:
                    file_type = 'attachfile'
                    subject = ''
                    body = ''
                else:
                    file_type = ''
                    subject = entry[plugin_name].get("상세 이력", {}).get("제목", "")
                    body = entry[plugin_name].get("상세 이력", {}).get("내용", "")

                # DLP 서비스 로그를 가져와 JSON 데이터와 비교
                dlp_service_log, dlp_log_detail = get_service_log(page, event_date, plugin_name_kor,
                                                                  service_name_kor, pattern_count, keyword_count,
                                                                  file_count, file_type, subject, body, case_id,
                                                                  service_id)

                # JSON 서비스 로그와 DLP 서비스 로그 비교
                json_service_log = [
                    entry[plugin_name]["정책"],
                    entry[plugin_name]["타입"],
                    entry[plugin_name]["서비스"],
                    entry[plugin_name]["개인정보 검출수"],
                    entry[plugin_name]["키워드 검출수"],
                    entry[plugin_name]["파일 검출수"]
                ]

                # 로그 테이블 및 상세 이력 비교
                if dlp_service_log == json_service_log:
                    json_log_detail = entry[plugin_name].get("상세 이력", {})
                    if dlp_log_detail == json_log_detail:
                        result_value = 1
                    else:
                        print(f"{event_date} 서비스 로그 상세 이력 값이 동일하지 않음")
                        print(f'json log :\n {json_log_detail}')
                        print(f'dlp log :\n {dlp_log_detail}')
                        result_value = 0
                else:
                    print(f"{event_date} 서비스 로그 테이블 값이 동일하지 않음")
                    print(f'json log :\n {json_service_log}')
                    print(f'dlp log :\n {dlp_service_log}')
                    result_value = 0

    json_file.close()

