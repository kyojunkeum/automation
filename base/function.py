# common/base.py
from typing import List, Dict
import requests
import allure
from base.config import ES_URL, ES_INDEX_PATTERN
import time
from requests.exceptions import ConnectionError, ReadTimeout

def search_logs_from_es(
    service_name: str,
    size: int = 1,
    es_url: str = ES_URL,
    index_pattern: str = ES_INDEX_PATTERN,
    timeout: int = 10,
    max_retries: int = 3,          # ✅ 재시도 횟수 추가
    retry_interval: float = 1.0,   # ✅ 재시도 간격(초)
):
    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"ServiceName": service_name}}
                ]
            }
        },
        "sort": [
            {"@timestamp": {"order": "desc"}}
        ],
        "size": size
    }

    last_exc = None

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(
                f"{es_url}/{index_pattern}/_search",
                json=query,
                timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["hits"]["hits"]

        except (ConnectionError, ReadTimeout) as e:
            last_exc = e
            print(
                f"[ES] connection failed (attempt {attempt}/{max_retries}) : {e}"
            )
            if attempt < max_retries:
                time.sleep(retry_interval)
            else:
                # 재시도 다 써도 안되면 그대로 예외 발생
                raise

    # 논리상 여기까지 오지는 않지만, 타입 힌트 만족용
    raise last_exc


def extract_counts_from_es_source(src: dict):
    """
    ES 문서(_source)에서 패턴/키워드/파일 카운트 추출.
    기존 코드 그대로 공통화.
    """
    # 패턴 카운트
    pattern_total = 0
    if isinstance(src.get("PatternParsedInfo"), dict):
        pattern_total += src["PatternParsedInfo"].get("total", 0)

    for key in (
        "EncodePatternParsedInfo",
        "EncodeExceptionPatternParsedInfo",
        "ExceptionPatternParsedInfo",
    ):
        if isinstance(src.get(key), dict):
            pattern_total += src[key].get("total", 0)

    # 키워드 카운트
    keyword_total = 0
    if isinstance(src.get("KeywordParsedInfo"), dict):
        keyword_total = src["KeywordParsedInfo"].get("total", 0)
        # keyword_total = len(src["KeywordParsedInfo"].get("parse", []))  # 형태 바꾸고 싶으면 이쪽으로

    # 첨부파일 카운트
    file_total = int(src.get("SendFileCount", 0))

    return str(pattern_total), str(keyword_total), str(file_total)


def compare_es_doc_with_expected(src: dict, expected: Dict[str, str]):
    """
    ES 한 건(_source)과 기대값 딕셔너리 비교.
    """
    pattern_count, keyword_count, file_count = extract_counts_from_es_source(src)

    exp_pattern = expected["pattern_count"]
    exp_keyword = expected["keyword_count"]
    exp_file = expected["file_count"]

    assert pattern_count == exp_pattern, (
        f"pattern_count mismatch: expected={exp_pattern}, actual={pattern_count}, "
        f"MessageID={src.get('MessageID')}"
    )
    assert keyword_count == exp_keyword, (
        f"keyword_count mismatch: expected={exp_keyword}, actual={keyword_count}, "
        f"MessageID={src.get('MessageID')}"
    )
    assert file_count == exp_file, (
        f"file_count mismatch: expected={exp_file}, actual={file_count}, "
        f"MessageID={src.get('MessageID')}"
    )


def assert_es_logs(
    service_name: str,
    test_cases: List[Dict],
    size: int | None = None,   # ← 기본값 None 으로 변경
    # size: int = 1, # 1개만 볼 때
):
    """
    공통 ES 검증 진입점.

    test_cases 예시:
    [
        {
            "hit_index": 3,
            "label": "키워드 로깅",
            "expected": {"pattern_count": "0", "keyword_count": "2", "file_count": "0"},
        },
        ...
    ]
    """
    hits = search_logs_from_es(service_name=service_name, size=size)

    # 필요한 최소 hit 수 자동 계산
    min_hits = max(case["hit_index"] for case in test_cases) + 1
    assert len(hits) >= min_hits, (
        f"ES 검색 결과가 {min_hits}건 미만입니다. "
        f"hits={len(hits)}, service_name={service_name}"
    )

    for case in test_cases:
        idx = case["hit_index"]
        label = case.get("label", "")
        expected = case["expected"]

        assert idx < len(hits), (
            f"{label} 테스트를 위한 hit_index={idx} 가 "
            f"ES 결과 범위를 벗어났습니다. hits={len(hits)}"
        )

        src = hits[idx].get("_source", {})

        with allure.step(f"[ES] {service_name} hit_index={idx} ({label}) 검증"):
            compare_es_doc_with_expected(src, expected)

def assert_es_logs_with_retry(
    service_name,
    test_cases,
    size=1,
    max_attempts=3,       # 최대 재시도 횟수
    interval_sec=5        # 재시도 간격(초)
):
    """
    ES 인덱싱 지연을 고려해 최대 max_attempts 회 재시도하여 검증한다.
    - 한 번이라도 성공하면 PASS
    - 모두 실패하면 마지막 에러를 raise
    """
    last_err = None

    for attempt in range(1, max_attempts + 1):
        try:
            print(f"[ES 검증] {attempt}/{max_attempts}차 시도 중...")

            # 기존 ES 검증 로직 호출
            assert_es_logs(
                service_name=service_name,
                test_cases=test_cases,
                size=size,
            )

            print(f"[ES 검증] {attempt}회째에 성공")
            return  # 성공하면 즉시 종료

        except AssertionError as e:
            last_err = e
            print(f"[ES 검증 실패] {attempt}/{max_attempts}회 (AssertionError): {e}")

        except requests.RequestException as e:
            last_err = e
            print(f"[ES 연결 실패] {attempt}/{max_attempts}회 (RequestException): {e}")

        # 마지막 시도가 아니라면 interval_sec 만큼 기다린 후 재시도
        if attempt < max_attempts:
            time.sleep(interval_sec)

    # 3회 모두 실패 → 테스트 실패 처리
    raise AssertionError(
        f"ES 검증이 {max_attempts}번 시도 후에도 실패했습니다.\n"
        f"마지막 에러: {last_err}"
    )

# def compare_ui_and_values(page, row_index, expected_counts):
#     """
#     UI 데이터와 values 를 비교하는 함수
#     :param page: Playwright Page 객체
#     :param row_index: 비교할 행 번호 (1부터 시작)
#     :param expected_counts: 딕셔너리 형태의 기대 값
#     """
#     row_selector = f"table tr:nth-child({row_index})"
#     ui_pattern_count = page.locator(f"{row_selector} td:nth-child(11)").text_content().strip()
#     ui_keyword_count = page.locator(f"{row_selector} td:nth-child(12)").text_content().strip()
#     ui_file_count = page.locator(f"{row_selector} td:nth-child(13)").text_content().strip()
#
#     assert expected_counts["pattern_count"] == ui_pattern_count, \
#         f"패턴 검출수 불일치: 기대값({expected_counts['pattern_count']}) != UI({ui_pattern_count})"
#     assert expected_counts["keyword_count"] == ui_keyword_count, \
#         f"키워드 검출수 불일치: 기대값({expected_counts['keyword_count']}) != UI({ui_keyword_count})"
#     assert expected_counts["file_count"] == ui_file_count, \
#         f"파일 개수 불일치: 기대값({expected_counts['file_count']}) != UI({ui_file_count})"
#
# @allure.severity(allure.severity_level.CRITICAL)
# @allure.step("Dooray board comment Dlp Logging check")
# def stest_compare_result_dooray_board_comment():
#     with sync_playwright() as p:
#         # 브라우저 실행
#         browser = p.chromium.launch(headless=False)
#
#         # BrowserContext 생성 (HTTPS 오류 무시 설정)
#         context = browser.new_context(ignore_https_errors=True)
#
#         # Context에서 새로운 페이지 생성
#         page = context.new_page()
#
#         try:
#
#             # DLP 서비스 로그인
#             page.goto("https://172.16.150.187:8443/login")  # DLP 제품 URL
#             page.fill("input[name='j_username']", "intsoosan")
#             page.fill("input[name='j_password']", "dkswjswmd4071*")
#             page.get_by_role("button", name="LOGIN").click()
#             time.sleep(2)
#
#             # 알림 팝업 처리
#             click_confirm_if_popup_exists(page, timeout=5000)
#
#             # 서비스 로그 페이지로 이동
#             page.goto("https://172.16.150.187:8443/log/service")
#
#             # 상세 검색
#             page.get_by_role("link", name="상세검색").click()
#             time.sleep(1)
#             # 서비스 선택
#             page.locator("#selectedDetail").select_option("service")
#             # 두레이게시판 선택
#             page.locator("#tokenfield2-tokenfield").click()
#             page.get_by_text("[SNS] 두레이 게시판").click()
#             # 검색 클릭
#             page.get_by_role("button", name="검색").click()
#             time.sleep(5)
#
#             # 딕셔너리 기댓값과 UI 데이터를 비교
#             test_cases = [
#                 {"row_index": 7, "expected": {"pattern_count": "0", "keyword_count": "0", "file_count": "0"}},  # 일반 로깅
#                 {"row_index": 5, "expected": {"pattern_count": "1", "keyword_count": "0", "file_count": "0"}},  # 개인정보 로깅
#                 {"row_index": 3, "expected": {"pattern_count": "0", "keyword_count": "2", "file_count": "0"}},  # 키워드 로깅
#                 {"row_index": 1, "expected": {"pattern_count": "14", "keyword_count": "0", "file_count": "1"}},  # 첨부파일 로깅
#             ]
#
#             for case in test_cases:
#                 compare_ui_and_values(page, case["row_index"], case["expected"])
#
#             print("모든 값이 일치합니다.")
#
#
#         except Exception as e:
#
#             # 실패 시 스크린샷 저장
#             # 실패 시 스크린샷 경로 설정
#             screenshot_path = get_screenshot_path("test_dooray_board_comment")  # 공통 함수 호출
#             page.screenshot(path=screenshot_path, type="jpeg", quality=80)
#             # page.screenshot(path=screenshot_path, full_page=True)
#             print(f"Screenshot taken at : {screenshot_path}")
#             allure.attach.file(screenshot_path, name="dooray_board_comment_failure_screenshot",
#                                attachment_type=allure.attachment_type.JPG)
#
#             raise
#
#         finally:
#             browser.close()