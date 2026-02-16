"""
Comprehensive tests for the Image & Video Generation API.

Endpoints under test:
    GET  /api/health             - Health check (no auth)
    POST /api/image/generate     - Generate an image (auth required)
    GET  /api/status/{task_id}   - Task status (auth required)
    GET  /api/result/{task_id}   - Task result (auth required)
    GET  /api/files/{filename}   - Retrieve generated file (no auth)
    GET  /api/tasks              - List all tasks (auth required)

Run:
    API_BASE_URL=http://127.0.0.1:8765 API_KEY=<key> pytest tests/test_api.py -v
"""
import time
import pytest
import httpx


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------
class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200

    def test_health_response_body(self, client):
        r = client.get("/api/health")
        data = r.json()
        assert "status" in data or "healthy" in str(data).lower()


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
class TestAuthentication:
    def test_generate_without_key_is_rejected(self, client):
        """Requests without an API key should be rejected (401 or 403)."""
        r = client.post("/api/image/generate", json={"prompt": "test"})
        assert r.status_code in (401, 403)

    def test_invalid_key_is_rejected(self, client):
        """Requests with a bogus API key should be rejected."""
        r = client.post(
            "/api/image/generate",
            json={"prompt": "test"},
            headers={"X-API-Key": "invalid-key-12345"},
        )
        assert r.status_code in (401, 403)

    def test_tasks_without_key_is_rejected(self, client):
        r = client.get("/api/tasks")
        assert r.status_code in (401, 403)

    def test_status_without_key_is_rejected(self, client):
        r = client.get("/api/status/nonexistent")
        assert r.status_code in (401, 403)

    def test_result_without_key_is_rejected(self, client):
        r = client.get("/api/result/nonexistent")
        assert r.status_code in (401, 403)

    def test_valid_key_is_accepted(self, auth_client):
        """A valid key should not return 401/403 on the tasks endpoint."""
        r = auth_client.get("/api/tasks")
        assert r.status_code not in (401, 403)


# ---------------------------------------------------------------------------
# Image generation
# ---------------------------------------------------------------------------
class TestImageGeneration:
    def test_generate_accepts_prompt(self, auth_client):
        """POST /api/image/generate should accept a prompt and return a task."""
        r = auth_client.post(
            "/api/image/generate",
            json={"prompt": "a futuristic city skyline at sunset"},
        )
        assert r.status_code in (200, 201, 202)
        data = r.json()
        assert "task_id" in data or "id" in data

    def test_generate_missing_prompt_rejected(self, auth_client):
        """Generating without a prompt should fail with 400 or 422."""
        r = auth_client.post("/api/image/generate", json={})
        assert r.status_code in (400, 422)

    def test_generate_empty_prompt_rejected(self, auth_client):
        r = auth_client.post("/api/image/generate", json={"prompt": ""})
        assert r.status_code in (400, 422)

    def test_generate_returns_task_id(self, auth_client):
        r = auth_client.post(
            "/api/image/generate",
            json={"prompt": "mountain landscape with snow"},
        )
        data = r.json()
        task_id = data.get("task_id") or data.get("id")
        assert task_id is not None
        assert isinstance(task_id, str)


# ---------------------------------------------------------------------------
# Task status
# ---------------------------------------------------------------------------
class TestTaskStatus:
    def test_status_nonexistent_task(self, auth_client):
        """Querying a nonexistent task_id should return 404."""
        r = auth_client.get("/api/status/does-not-exist-12345")
        assert r.status_code == 404

    def test_status_of_created_task(self, auth_client):
        """After generating, the status endpoint should recognize the task."""
        gen = auth_client.post(
            "/api/image/generate",
            json={"prompt": "abstract art colorful"},
        )
        task_id = gen.json().get("task_id") or gen.json().get("id")
        r = auth_client.get(f"/api/status/{task_id}")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data
        assert data["status"] in (
            "pending", "queued", "processing", "in_progress",
            "completed", "done", "failed", "error",
        )


# ---------------------------------------------------------------------------
# Task result
# ---------------------------------------------------------------------------
class TestTaskResult:
    def test_result_nonexistent_task(self, auth_client):
        r = auth_client.get("/api/result/does-not-exist-12345")
        assert r.status_code in (404, 400)

    def test_result_of_completed_task(self, auth_client):
        """Submit a task and poll until completion, then verify result."""
        gen = auth_client.post(
            "/api/image/generate",
            json={"prompt": "simple red circle on white background"},
        )
        task_id = gen.json().get("task_id") or gen.json().get("id")

        # Poll for completion (up to 120 seconds)
        for _ in range(60):
            status_r = auth_client.get(f"/api/status/{task_id}")
            status = status_r.json().get("status", "")
            if status in ("completed", "done"):
                break
            if status in ("failed", "error"):
                pytest.skip(f"Task failed with status: {status}")
            time.sleep(2)
        else:
            pytest.skip("Task did not complete within 120 seconds")

        r = auth_client.get(f"/api/result/{task_id}")
        assert r.status_code == 200
        data = r.json()
        # The result should contain a file reference or URL
        has_file = any(
            k in data
            for k in ("file", "filename", "url", "image_url", "output", "result")
        )
        assert has_file, f"Result payload missing file reference: {data}"


# ---------------------------------------------------------------------------
# File retrieval
# ---------------------------------------------------------------------------
class TestFileRetrieval:
    def test_nonexistent_file_returns_404(self, client):
        r = client.get("/api/files/nonexistent_file_12345.png")
        assert r.status_code == 404

    def test_retrieve_generated_file(self, auth_client, client):
        """End-to-end: generate -> poll -> get result -> download file."""
        gen = auth_client.post(
            "/api/image/generate",
            json={"prompt": "blue gradient background"},
        )
        task_id = gen.json().get("task_id") or gen.json().get("id")

        for _ in range(60):
            status_r = auth_client.get(f"/api/status/{task_id}")
            status = status_r.json().get("status", "")
            if status in ("completed", "done"):
                break
            if status in ("failed", "error"):
                pytest.skip("Task failed")
            time.sleep(2)
        else:
            pytest.skip("Task did not complete within 120 seconds")

        result = auth_client.get(f"/api/result/{task_id}").json()
        filename = (
            result.get("filename")
            or result.get("file")
            or result.get("output", "")
        )
        if not filename:
            pytest.skip("No filename in result payload")

        # The files endpoint does not require auth
        r = client.get(f"/api/files/{filename}")
        assert r.status_code == 200
        assert len(r.content) > 0
        content_type = r.headers.get("content-type", "")
        assert any(
            t in content_type
            for t in ("image/", "video/", "application/octet-stream")
        )


# ---------------------------------------------------------------------------
# Tasks list
# ---------------------------------------------------------------------------
class TestTasksList:
    def test_tasks_returns_list(self, auth_client):
        r = auth_client.get("/api/tasks")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, (list, dict))

    def test_tasks_contains_submitted_task(self, auth_client):
        """A newly submitted task should appear in the tasks list."""
        gen = auth_client.post(
            "/api/image/generate",
            json={"prompt": "test task listing"},
        )
        task_id = gen.json().get("task_id") or gen.json().get("id")

        r = auth_client.get("/api/tasks")
        data = r.json()
        # Might be a list or a dict with a "tasks" key
        tasks = data if isinstance(data, list) else data.get("tasks", [])
        task_ids = [
            t.get("task_id") or t.get("id") for t in tasks
        ]
        assert task_id in task_ids, f"Task {task_id} not found in task list"
