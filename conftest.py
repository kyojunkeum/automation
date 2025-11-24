# conftest.py
import os
from base.config import HOST_IP, DUT_IP, DLP_BASE_URL, ES_URL


def pytest_sessionstart(session):
    # 1) 콘솔 출력
    print("=" * 60)
    print(f"[PYTEST] Host IP = {HOST_IP}")
    print(f"[PYTEST] DUT  IP = {DUT_IP}")
    print("=" * 60)

    # 2) Allure environment.properties 생성
    results_dir = os.getenv("ALLURE_RESULTS_DIR", "allure-results")
    os.makedirs(results_dir, exist_ok=True)

    env_path = os.path.join(results_dir, "environment.properties")

    with open(env_path, "w", encoding="utf-8") as f:
        f.write(f"HOST_IP={HOST_IP}\n")
        f.write(f"DUT_IP={DUT_IP}\n")
        f.write(f"DLP_BASE_URL={DLP_BASE_URL}\n")
        f.write(f"ES_URL={ES_URL}\n")

    print(f"[PYTEST] Allure environment file written to: {env_path}")
