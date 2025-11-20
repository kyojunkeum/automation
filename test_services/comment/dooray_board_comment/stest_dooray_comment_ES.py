# ===== 여기부터 ES 기반 검증용 유틸 =====
import requests
import allure

ES_URL = "http://172.16.150.187:9200"
# 월이 바뀌어도 log-2025-12, log-2026-01 ... 전부 포함
ES_INDEX_PATTERN = "log-*/session"
DOORAY_SERVICE_NAME = "두레이 게시판-댓글"   # 실제 ServiceName 값


def search_dooray_logs_from_es(size: int = 10):
    """
    ES에서 두레이 게시판-댓글 로그를 최근순으로 조회한다.
    ServiceName 기준 필터 + @timestamp 내림차순 정렬.
    """
    query = {
        "query": {
            "bool": {
                "must": [
                    # keyword 필드가 아니라 ServiceName 자체가 keyword 타입이므로 그대로 사용
                    {"term": {"ServiceName": DOORAY_SERVICE_NAME}}
                ]
            }
        },
        "sort": [
            {"@timestamp": {"order": "desc"}}
        ],
        "size": size
    }

    resp = requests.get(
        f"{ES_URL}/{ES_INDEX_PATTERN}/_search",
        json=query,
        timeout=10
    )
    resp.raise_for_status()
    data = resp.json()
    return data["hits"]["hits"]  # 각 hit: {"_index", "_type", "_id", "_source", ...}


def extract_counts_from_es_source(src: dict):
    # 패턴 카운트
    pattern_total = 0
    if isinstance(src.get("PatternParsedInfo"), dict):
        pattern_total += src["PatternParsedInfo"].get("total", 0)

    # 필요하면 예외/인코딩 패턴까지 합산
    for key in ("EncodePatternParsedInfo", "EncodeExceptionPatternParsedInfo", "ExceptionPatternParsedInfo"):
        if isinstance(src.get(key), dict):
            pattern_total += src[key].get("total", 0)

    # 키워드 카운트
    keyword_total = 0
    if isinstance(src.get("KeywordParsedInfo"), dict):
        # ① 전체 매칭 수 (지금 예시: 6)
        keyword_total = src["KeywordParsedInfo"].get("total", 0)
        # ② 키워드 종류 개수로 쓰고 싶으면 아래로 교체
        # keyword_total = len(src["KeywordParsedInfo"].get("parse", []))

    # 첨부파일 카운트
    file_total = int(src.get("SendFileCount", 0))

    return str(pattern_total), str(keyword_total), str(file_total)


def compare_es_and_values(doc: dict, expected: dict):
    """
    기존 compare_ui_and_values(page, row_index, expected) 와 동일 컨셉.
    - doc: ES hit 하나 ({"_source": {...}} 형태)
    - expected: {"pattern_count": "0", "keyword_count": "0", "file_count": "0"} 형태
    """
    src = doc.get("_source", {})

    pattern_count, keyword_count, file_count = extract_counts_from_es_source(src)

    exp_pattern = expected["pattern_count"]
    exp_keyword = expected["keyword_count"]
    exp_file = expected["file_count"]

    assert pattern_count == exp_pattern, \
        f"pattern_count mismatch: expected={exp_pattern}, actual={pattern_count}, MessageID={src.get('MessageID')}"
    assert keyword_count == exp_keyword, \
        f"keyword_count mismatch: expected={exp_keyword}, actual={keyword_count}, MessageID={src.get('MessageID')}"
    assert file_count == exp_file, \
        f"file_count mismatch: expected={exp_file}, actual={file_count}, MessageID={src.get('MessageID')}"


# ===== 여기부터 ES 기반 테스트 =====

@allure.severity(allure.severity_level.CRITICAL)
@allure.step("Dooray board comment DLP ES Logging check")
def stest_compare_result_dooray_board_comment_es():
    """
    ES(log-*/session)에서 두레이 게시판-댓글 로그를 조회하여
    패턴/키워드/파일 카운트가 기대값과 일치하는지 검증한다.
    """
    # ES에서 최근 10건 가져오기 (필요 시 조정 가능)
    hits = search_dooray_logs_from_es(size=10)

    test_cases = [
        {
            "hit_index": 7,
            "label": "일반 로깅",
            "expected": {"pattern_count": "0", "keyword_count": "0", "file_count": "0"},
        },
        {
            "hit_index": 5,
            "label": "개인정보 로깅",
            "expected": {"pattern_count": "1", "keyword_count": "0", "file_count": "0"},
        },
        {
            "hit_index": 3,
            "label": "키워드 로깅",
            "expected": {"pattern_count": "0", "keyword_count": "2", "file_count": "0"},
        },
        {
            "hit_index": 1,
            "label": "첨부파일 로깅",
            "expected": {"pattern_count": "14", "keyword_count": "0", "file_count": "1"},
        },
    ]

    assert len(hits) >= 4, f"ES 검색 결과가 4건 미만입니다. hits={len(hits)}"

    for case in test_cases:
        idx = case["hit_index"]
        label = case["label"]
        expected = case["expected"]

        assert idx < len(hits), f"{label} 테스트를 위한 hit_index={idx} 가 ES 결과 범위를 벗어났습니다. hits={len(hits)}"

        with allure.step(f"ES hit_index={idx} ({label}) 검증"):
            compare_es_and_values(hits[idx], expected)

def stest_debug_print_dooray_es_hits():
    hits = search_dooray_logs_from_es(size=10)
    for i, doc in enumerate(hits):
        src = doc["_source"]
        pat, key, file_ = extract_counts_from_es_source(src)

        print("=" * 60)
        print(f"hit_index={i}")
        print(f"@timestamp     = {src.get('@timestamp')}")
        print(f"RuleName       = {src.get('RuleName')}")
        print(f"ResultName     = {src.get('ResultName')}")
        print(f"ServiceName    = {src.get('ServiceName')}")
        print(f"pattern_count  = {pat}")
        print(f"keyword_count  = {key}")
        print(f"file_count     = {file_}")
        print(f"MessageID      = {src.get('MessageID')}")