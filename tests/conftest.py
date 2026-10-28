# tests/e2e/conftest.py


import subprocess
import sys
import time

import pytest
import requests
from playwright.sync_api import sync_playwright


@pytest.fixture(scope="session")
def fastapi_server():
    """Start FastAPI before E2E tests and stop it afterward."""

    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
    ]

    fastapi_process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    server_url = "http://127.0.0.1:8000/"
    timeout = 30
    start_time = time.time()

    print("Starting FastAPI server...")

    try:
        while time.time() - start_time < timeout:
            if fastapi_process.poll() is not None:
                output, _ = fastapi_process.communicate()
                raise RuntimeError(
                    f"FastAPI server exited unexpectedly.\n{output}"
                )

            try:
                response = requests.get(server_url, timeout=1)
                if response.status_code == 200:
                    print("FastAPI server is running.")
                    break
            except requests.RequestException:
                pass

            time.sleep(1)
        else:
            fastapi_process.terminate()
            try:
                output, _ = fastapi_process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                fastapi_process.kill()
                output, _ = fastapi_process.communicate()

            raise RuntimeError(
                f"FastAPI server failed to start within {timeout} seconds.\n"
                f"Server output:\n{output}"
            )

        yield

    finally:
        if fastapi_process.poll() is None:
            fastapi_process.terminate()
            try:
                fastapi_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                fastapi_process.kill()
                fastapi_process.wait()


@pytest.fixture(scope="session")
def playwright_instance_fixture():
    """Manage Playwright's lifecycle."""
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright_instance_fixture):
    """Launch a browser instance."""
    browser = playwright_instance_fixture.chromium.launch(headless=True)
    yield browser
    browser.close()


@pytest.fixture(scope="function")
def page(browser):
    """Create a new browser page for each test."""
    page = browser.new_page()
    yield page
    page.close()
