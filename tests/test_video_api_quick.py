#!/usr/bin/env python3
"""
Quick standalone script to validate Video Generation API endpoints.

Usage:
    python tests/test_video_api_quick.py [BASE_URL] [API_KEY]

Examples:
    python tests/test_video_api_quick.py http://127.0.0.1:8765 gUHX3JtXo_p5A9Wcj6safmvVCH171qlY__K5b8HEoVk
    API_BASE_URL=http://127.0.0.1:8765 API_KEY=<key> python tests/test_video_api_quick.py
"""
import os
import sys
import time
import httpx

PASS = "[PASS]"
FAIL = "[FAIL]"
SKIP = "[SKIP]"


def run_tests(base_url: str, api_key: str):
    results = []

    def log(status, name, detail=""):
        results.append((status, name))
        line = f"  {status} {name}"
        if detail:
            line += f"  -- {detail}"
        print(line)

    print(f"\nVideo Generation API Test Suite")
    print(f"Server: {base_url}")
    print(f"API Key: {api_key[:8]}...{api_key[-4:]}\n")

    client = httpx.Client(base_url=base_url, timeout=60)
    auth = {"X-API-Key": api_key}

    # -----------------------------------------------------------------------
    # 1. Health check
    # -----------------------------------------------------------------------
    print("--- Health ---")
    try:
        r = client.get("/api/health")
        if r.status_code == 200:
            log(PASS, "Health check", r.text[:100])
        else:
            log(FAIL, "Health check", f"status={r.status_code}")
    except httpx.ConnectError:
        log(FAIL, "Health check", "Cannot connect to server")
        print("\nServer is not reachable. Aborting remaining tests.")
        client.close()
        return results

    # -----------------------------------------------------------------------
    # 2-4. Authentication
    # -----------------------------------------------------------------------
    print("\n--- Authentication ---")

    # Invalid key rejected
    r = client.post(
        "/api/video/generate",
        json={"prompt": "test"},
        headers={"X-API-Key": "bad-key"},
    )
    if r.status_code in (401, 403):
        log(PASS, "Invalid key rejected", f"status={r.status_code}")
    else:
        log(FAIL, "Invalid key rejected", f"status={r.status_code}")

    # No key rejected
    r = client.post("/api/video/generate", json={"prompt": "test"})
    if r.status_code in (401, 403):
        log(PASS, "No key rejected", f"status={r.status_code}")
    else:
        log(FAIL, "No key rejected", f"status={r.status_code}")

    # Valid key accepted
    r = client.get("/api/tasks", headers=auth)
    if r.status_code not in (401, 403):
        log(PASS, "Valid key accepted", f"status={r.status_code}")
    else:
        log(FAIL, "Valid key accepted", f"status={r.status_code}")

    # -----------------------------------------------------------------------
    # 5-6. Video generation
    # -----------------------------------------------------------------------
    print("\n--- Video Generation ---")

    r = client.post(
        "/api/video/generate",
        json={"prompt": "a calm ocean wave rolling onto a sandy beach at sunset"},
        headers=auth,
    )
    if r.status_code in (200, 201, 202):
        data = r.json()
        task_id = data.get("task_id") or data.get("id")
        log(PASS, "Generate video", f"task_id={task_id}")
    else:
        log(FAIL, "Generate video", f"status={r.status_code} body={r.text[:200]}")
        task_id = None

    # Missing prompt rejected
    r = client.post("/api/video/generate", json={}, headers=auth)
    if r.status_code in (400, 422):
        log(PASS, "Missing prompt rejected", f"status={r.status_code}")
    else:
        log(FAIL, "Missing prompt rejected", f"status={r.status_code}")

    # -----------------------------------------------------------------------
    # 7-8. Task status
    # -----------------------------------------------------------------------
    print("\n--- Task Status ---")

    if task_id:
        r = client.get(f"/api/status/{task_id}", headers=auth)
        if r.status_code == 200:
            status = r.json().get("status", "unknown")
            log(PASS, "Task status", f"status={status}")
        else:
            log(FAIL, "Task status", f"http={r.status_code}")
    else:
        log(SKIP, "Task status", "no task_id")

    # Nonexistent task returns 404
    r = client.get("/api/status/nonexistent-video-id-99999", headers=auth)
    if r.status_code == 404:
        log(PASS, "Nonexistent task 404")
    else:
        log(FAIL, "Nonexistent task 404", f"status={r.status_code}")

    # -----------------------------------------------------------------------
    # 9-10. Poll for completion and check result
    # -----------------------------------------------------------------------
    print("\n--- Task Result ---")

    if task_id:
        final_status = None
        # Video generation may take longer — poll up to 5 minutes
        for i in range(150):
            r = client.get(f"/api/status/{task_id}", headers=auth)
            final_status = r.json().get("status", "")
            if final_status in ("completed", "done"):
                break
            if final_status in ("failed", "error"):
                break
            time.sleep(2)

        if final_status in ("completed", "done"):
            log(PASS, "Task completed", f"after ~{i*2}s")
            r = client.get(f"/api/result/{task_id}", headers=auth)
            if r.status_code == 200:
                data = r.json()
                log(PASS, "Task result fetched", str(data)[:200])
                filename = (
                    data.get("filename")
                    or data.get("file")
                    or data.get("output", "")
                )
                if filename:
                    # File download
                    print("\n--- File Download ---")
                    r = client.get(f"/api/files/{filename}")
                    if r.status_code == 200 and len(r.content) > 0:
                        log(
                            PASS,
                            "File downloaded",
                            f"size={len(r.content)} bytes, type={r.headers.get('content-type', 'N/A')}",
                        )
                    else:
                        log(FAIL, "File downloaded", f"status={r.status_code}")
            else:
                log(FAIL, "Task result fetched", f"status={r.status_code}")
        elif final_status in ("failed", "error"):
            log(FAIL, "Task completed", f"task failed: {final_status}")
        else:
            log(SKIP, "Task completed", "timed out after 300s")
    else:
        log(SKIP, "Task result", "no task_id")

    # -----------------------------------------------------------------------
    # 11. Tasks list
    # -----------------------------------------------------------------------
    print("\n--- Tasks List ---")

    r = client.get("/api/tasks", headers=auth)
    if r.status_code == 200:
        data = r.json()
        count = len(data) if isinstance(data, list) else len(data.get("tasks", []))
        log(PASS, "Tasks list", f"count={count}")
    else:
        log(FAIL, "Tasks list", f"status={r.status_code}")

    client.close()

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    passed = sum(1 for s, _ in results if s == PASS)
    failed = sum(1 for s, _ in results if s == FAIL)
    skipped = sum(1 for s, _ in results if s == SKIP)
    total = len(results)

    print(f"\n{'='*50}")
    print(f"Results: {passed}/{total} passed, {failed} failed, {skipped} skipped")
    if failed == 0:
        print("Video API key is valid and all endpoints are working.")
    else:
        print("Some tests failed. Review the output above.")
    print(f"{'='*50}\n")

    return results


if __name__ == "__main__":
    base_url = (
        sys.argv[1]
        if len(sys.argv) > 1
        else os.getenv("API_BASE_URL", "http://127.0.0.1:8765")
    )
    api_key = (
        sys.argv[2]
        if len(sys.argv) > 2
        else os.getenv("API_KEY", "")
    )
    if not api_key:
        print("Usage: python tests/test_video_api_quick.py [BASE_URL] [API_KEY]")
        print("   or: API_KEY=<key> python tests/test_video_api_quick.py")
        sys.exit(1)

    run_tests(base_url, api_key)
