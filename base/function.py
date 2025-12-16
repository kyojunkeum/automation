from typing import List, Dict, Sequence, Union
import requests
import allure
from base.config import ES_URL, ES_INDEX_PATTERN
import time
from requests.exceptions import ConnectionError, ReadTimeout
from playwright.sync_api import Page, BrowserContext, TimeoutError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
import os
from datetime import datetime



def goto_and_wait(page: Page, url: str, timeout: int = 15000, retries: int = 2):
    """
    URL 이동 후 networkidle까지 대기.
    실패하면 지정된 횟수만큼 재시도.
    """
    attempt = 0

    while attempt <= retries:
        try:
            print(f"[goto_and_wait] 페이지 이동 시도 {attempt+1}/{retries+1}: {url}")
            page.goto(url, wait_until="networkidle", timeout=timeout)
            print("[goto_and_wait] 페이지 로드 성공")
            return page

        except TimeoutError:
            attempt += 1
            print(f"[goto_and_wait] 로드 실패 (Timeout). 재시도: {attempt}/{retries}")

            if attempt > retries:
                print("[goto_and_wait] 모든 재시도 실패 → 예외 발생")
                raise

            # 재시도 전 잠깐 대기
            time.sleep(2)

def click_and_wait_navigation(page: Page, selector=None, role=None, name=None,
                              timeout: int = 15000):
    """
    클릭 → 같은 탭에서 페이지 이동(expect_navigation) → 로드될 때까지 대기.
    새 창(pop-up)이 아니라, 현재 탭에서 리디렉션되는 경우에 사용.
    """
    with page.expect_navigation(wait_until="networkidle", timeout=timeout):
        if selector:
            page.locator(selector).click()
        else:
            page.get_by_role(role, name=name).click()

    return page  # 같은 Page 그대로 반환

def click_confirm_if_popup_exists(page, timeout=3000):
    """
    '확인' 버튼이 포함된 팝업이 뜨면 자동으로 클릭하고,
    없으면 스킵한다.

    다양한 팝업 UI 패턴 지원:
    - role=button name='확인'
    - 텍스트 '확인'
    - data-testid 등 fallback locator
    """

    confirm_locators = [
        page.get_by_role("button", name="확인"),
        page.locator("button:has-text('확인')"),
        page.locator("text=확인"),  # fallback
    ]

    for locator in confirm_locators:
        try:
            locator.wait_for(timeout=timeout)
            locator.click()
            print("✔ [DEBUG] 팝업 '확인' 버튼 클릭됨")
            return True
        except TimeoutError:
            continue
        except Exception:
            continue

    print("▶ [DEBUG] 팝업 없음 또는 '확인' 버튼 미발견 → 스킵")
    return False

def safe_send_with_popup_retry(page, max_retry=3, wait_sec=3):
    """
    '보내기' 버튼을 누르고, 팝업이 뜨면 '확인' 클릭 후 다시 시도.
    최대 max_retry 회 반복.
    """
    for attempt in range(1, max_retry + 1):
        print(f"▶ [DEBUG] 보내기 시도 {attempt}/{max_retry}")

        # 1) 보내기 버튼 클릭
        try:
            page.get_by_label("보내기", exact=True).click(timeout=2000)
            print("✔ [DEBUG] '보내기' 버튼 클릭")
        except Exception:
            print("▶ [DEBUG] '보내기' 버튼 없음 → 종료")
            return False

        # 2) 팝업 확인 처리
        popup_clicked = click_confirm_if_popup_exists(page, timeout=2500)

        # 팝업이 있었다면 wait
        if popup_clicked:
            print(f"⏳ [DEBUG] 팝업 처리 후 {wait_sec}초 대기")
            page.wait_for_timeout(wait_sec * 1000)
            continue  # → 다시 보내기 버튼 누름

        # 팝업이 없으면 성공으로 간주
        print("✔ [DEBUG] 팝업 없음 → 보내기 성공 완료")
        return True

    print("❗ [DEBUG] 최대 재시도 도달 → 종료")
    return False

def get_screenshot_path(test_name):
    screenshot_dir = os.path.join(os.getcwd(), "report", "screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(screenshot_dir, f"{test_name}_failed_{timestamp}.jpg")

def capture_failure_screenshot(page, request, timeout: int = 5000):
    """
    실패 시 스크린샷 + allure 첨부를 한 번에 처리하는 헬퍼.

    - 테스트 함수 시그니처에 `request` fixture 만 추가해 두면
      request.node.name 으로 현재 테스트 이름을 자동 사용한다.
    """
    test_name = request.node.name  # pytest가 주입하는 request fixture

    screenshot_path = get_screenshot_path(test_name)

    try:
        # Playwright 스크린샷 (timeout 조절 가능)
        page.screenshot(
            path=screenshot_path,
            type="jpeg",
            quality=80,
            timeout=timeout,
        )
        print(f"Screenshot taken at : {screenshot_path}")

        # Allure 첨부
        allure.attach.file(
            screenshot_path,
            name=f"{test_name}_failure_screenshot",
            attachment_type=allure.attachment_type.JPG,
        )

    except PlaywrightTimeoutError as te:
        # 폰트 로딩/렌더링 딜레이 등으로 스크린샷 타임아웃 나는 경우
        print(f"[WARN] Screenshot timeout for {test_name}: {te}")

    except Exception as e:
        # 그 외 스크린샷 관련 예외
        print(f"[WARN] Screenshot capture failed for {test_name}: {e}")

    return screenshot_path

def search_logs_from_es(
    service_name: Union[str, Sequence[str]],
    size: int = 1,
    es_url: str = ES_URL,
    index_pattern: str = ES_INDEX_PATTERN,
    timeout: int = 10,
    max_retries: int = 3,          # ✅ 재시도 횟수 추가
    retry_interval: float = 1.0,   # ✅ 재시도 간격(초)
):
    """
        service_name: str  또는 [str, str, ...]
          - str     : 한 개 서비스명
          - list/tuple : 여러 서비스명(한글/영어 등)을 OR 조건으로 검색
        """

    # 항상 리스트 형태로 맞추기
    if isinstance(service_name, str):
        service_names = [service_name]
    else:
        service_names = list(service_name)

    should_clauses = [
        {"term": {"ServiceName": name}}
        for name in service_names
    ]

    query = {
        "query": {
            "bool": {
                "should": should_clauses,
                "minimum_should_match": 1,
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

from typing import Dict, Any

def compare_es_doc_with_expected(src: dict, expected: Dict[str, Any]):
    """
    ES 한 건(_source)과 기대값 딕셔너리 비교.

    expected 예시:
    {
        "pattern_count": "0",
        "keyword_count": "2",
        "file_count": "0",
        # 선택사항:
        # "tags": ["sns"]  또는 "tags": "sns"
    }
    """
    # 기존 카운트 비교
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

    # 🔹 tags 비교 (하나라도 맞으면 PASS)
    if "tags" in expected:
        exp_tags = expected["tags"]

        # expected: 문자열 1개 → 리스트로 변환
        if isinstance(exp_tags, str):
            exp_tags_list = [exp_tags]
        else:
            exp_tags_list = list(exp_tags)

        actual_tags = src.get("tags", [])
        if isinstance(actual_tags, str):
            actual_tags_list = [actual_tags]
        else:
            actual_tags_list = list(actual_tags)

        # OR 조건: expected 중 하나라도 actual 안에 있으면 PASS
        ok = any(tag in actual_tags_list for tag in exp_tags_list)

        assert ok, (
            f"tags OR-mismatch: expected any of {exp_tags_list}, "
            f"actual={actual_tags_list}, "
            f"MessageID={src.get('MessageID')}"
        )


def assert_es_logs(
    service_name: Union[str, Sequence[str]],
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
