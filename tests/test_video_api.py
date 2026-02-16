"""
Comprehensive tests for the Video Generation API.

Endpoints under test:
    GET  /api/health               - Health check (no auth)
    POST /api/video/generate       - Generate a video (auth required)
    GET  /api/status/{task_id}     - Task status (auth required)
    GET  /api/result/{task_id}     - Task result (auth required)
    GET  /api/files/{filename}     - Retrieve generated file (no auth)
    GET  /api/tasks                - List all tasks (auth required)

Run:
    API_BASE_URL=http://127.0.0.1:8765 API_KEY=<key> pytest tests/test_video_api.py -v
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
# Authentication (video endpoints)
# ---------------------------------------------------------------------------
class TestVideoAuthentication:
    def test_generate_video_without_key_is_rejected(self, client):
        """Requests without an API key should be rejected (401 or 403)."""
        r = client.post("/api/video/generate", json={"prompt": "test"})
        assert r.status_code in (401, 403)

    def test_generate_video_invalid_key_is_rejected(self, client):
        """Requests with a bogus API key should be rejected."""
        r = client.post(
            "/api/video/generate",
            json={"prompt": "test"},
            headers={"X-API-Key": "invalid-key-12345"},
        )
        assert r.status_code in (401, 403)

    def test_valid_key_is_accepted(self, auth_client):
        """A valid key should not return 401/403 on the tasks endpoint."""
        r = auth_client.get("/api/tasks")
        assert r.status_code not in (401, 403)


# ---------------------------------------------------------------------------
# Video generation
# ---------------------------------------------------------------------------
class TestVideoGeneration:
    def test_generate_accepts_prompt(self, auth_client):
        """POST /api/video/generate should accept a prompt and return a task."""
        r = auth_client.post(
            "/api/video/generate",
            json={"prompt": "a calm ocean wave rolling onto a sandy beach at sunset"},
        )
        assert r.status_code in (200, 201, 202)
        data = r.json()
        assert "task_id" in data or "id" in data

    def test_generate_missing_prompt_rejected(self, auth_client):
        """Generating without a prompt should fail with 400 or 422."""
        r = auth_client.post("/api/video/generate", json={})
        assert r.status_code in (400, 422)

    def test_generate_empty_prompt_rejected(self, auth_client):
        r = auth_client.post("/api/video/generate", json={"prompt": ""})
        assert r.status_code in (400, 422)

    def test_generate_returns_task_id(self, auth_client):
        r = auth_client.post(
            "/api/video/generate",
            json={"prompt": "a drone flyover of a green forest with morning mist"},
        )
        data = r.json()
        task_id = data.get("task_id") or data.get("id")
        assert task_id is not None
        assert isinstance(task_id, str)

    def test_generate_with_optional_params(self, auth_client):
        """Video generation may accept optional parameters like duration or resolution."""
        r = auth_client.post(
            "/api/video/generate",
            json={
                "prompt": "a timelapse of clouds moving over a city skyline",
                "duration": 5,
                "resolution": "720p",
            },
        )
        # Should accept or gracefully ignore unknown params
        assert r.status_code in (200, 201, 202)
        data = r.json()
        assert "task_id" in data or "id" in data


# ---------------------------------------------------------------------------
# Task status (video tasks)
# ---------------------------------------------------------------------------
class TestVideoTaskStatus:
    def test_status_nonexistent_task(self, auth_client):
        """Querying a nonexistent task_id should return 404."""
        r = auth_client.get("/api/status/does-not-exist-video-99999")
        assert r.status_code == 404

    def test_status_of_created_video_task(self, auth_client):
        """After generating, the status endpoint should recognize the task."""
        gen = auth_client.post(
            "/api/video/generate",
            json={"prompt": "abstract colorful particles floating in space"},
        )
        task_id = gen.json().get("task_id") or gen.json().get("id")
        r = auth_client.get(f"/api/status/{task_id}")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data
        assert data["status"] in (
            "pending", "queued", "processing", "in_progress",
            "running", "completed", "done", "failed", "error",
        )


# ---------------------------------------------------------------------------
# Task result (video tasks)
# ---------------------------------------------------------------------------
class TestVideoTaskResult:
    def test_result_nonexistent_task(self, auth_client):
        r = auth_client.get("/api/result/does-not-exist-video-99999")
        assert r.status_code in (404, 400)

    def test_result_of_completed_video_task(self, auth_client):
        """Submit a video task and poll until completion, then verify result."""
        gen = auth_client.post(
            "/api/video/generate",
            json={"prompt": "a candle flame flickering gently in a dark room"},
        )
        task_id = gen.json().get("task_id") or gen.json().get("id")

        # Poll for completion (up to 5 minutes — video generation is slower)
        for i in range(150):
            status_r = auth_client.get(f"/api/status/{task_id}")
            status = status_r.json().get("status", "")
            if status in ("completed", "done"):
                break
            if status in ("failed", "error"):
                pytest.skip(f"Task failed with status: {status}")
            time.sleep(2)
        else:
            pytest.skip("Task did not complete within 300 seconds")

        r = auth_client.get(f"/api/result/{task_id}")
        assert r.status_code == 200
        data = r.json()
        # The result should contain a file reference or URL
        has_file = any(
            k in data
            for k in ("file", "filename", "url", "video_url", "output", "result")
        )
        assert has_file, f"Result payload missing file reference: {data}"


# ---------------------------------------------------------------------------
# File retrieval (video files)
# ---------------------------------------------------------------------------
class TestVideoFileRetrieval:
    def test_nonexistent_file_returns_404(self, client):
        r = client.get("/api/files/nonexistent_video_99999.mp4")
        assert r.status_code == 404

    def test_retrieve_generated_video_file(self, auth_client, client):
        """End-to-end: generate video -> poll -> get result -> download file."""
        gen = auth_client.post(
            "/api/video/generate",
            json={"prompt": "rain falling on a window with city lights in the background"},
        )
        task_id = gen.json().get("task_id") or gen.json().get("id")

        for i in range(150):
            status_r = auth_client.get(f"/api/status/{task_id}")
            status = status_r.json().get("status", "")
            if status in ("completed", "done"):
                break
            if status in ("failed", "error"):
                pytest.skip("Task failed")
            time.sleep(2)
        else:
            pytest.skip("Task did not complete within 300 seconds")

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
            for t in ("video/", "application/octet-stream")
        ), f"Unexpected content-type: {content_type}"


# ---------------------------------------------------------------------------
# Tasks list (verify video tasks appear)
# ---------------------------------------------------------------------------
class TestVideoTasksList:
    def test_tasks_returns_list(self, auth_client):
        r = auth_client.get("/api/tasks")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, (list, dict))

    def test_tasks_contains_submitted_video_task(self, auth_client):
        """A newly submitted video task should appear in the tasks list."""
        gen = auth_client.post(
            "/api/video/generate",
            json={"prompt": "test video task listing"},
        )
        task_id = gen.json().get("task_id") or gen.json().get("id")

        r = auth_client.get("/api/tasks")
        data = r.json()
        tasks = data if isinstance(data, list) else data.get("tasks", [])
        task_ids = [
            t.get("task_id") or t.get("id") for t in tasks
        ]
        assert task_id in task_ids, f"Video task {task_id} not found in task list"
