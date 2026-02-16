"""
Pytest configuration and shared fixtures for the Generation API tests.

Configure via environment variables:
    API_BASE_URL  - Base URL of the server (default: http://127.0.0.1:8765)
    API_KEY       - API key for authenticated endpoints
"""
import os
import pytest
import httpx

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8765")
API_KEY = os.getenv("API_KEY", "")


@pytest.fixture(scope="session")
def base_url():
    return API_BASE_URL.rstrip("/")


@pytest.fixture(scope="session")
def api_key():
    key = API_KEY
    if not key:
        pytest.skip("API_KEY environment variable not set")
    return key


@pytest.fixture(scope="session")
def auth_headers(api_key):
    return {"X-API-Key": api_key}


@pytest.fixture(scope="session")
def client(base_url):
    with httpx.Client(base_url=base_url, timeout=60) as c:
        yield c


@pytest.fixture(scope="session")
def auth_client(base_url, auth_headers):
    with httpx.Client(base_url=base_url, headers=auth_headers, timeout=120) as c:
        yield c
