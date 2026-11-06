import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.entities import Project
from app.db.session import SessionLocal

@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c

def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

def test_projects_crud(client):
    # Create project
    res = client.post("/api/projects", json={
        "name": "Endpoint Audit Project",
        "project_type": "prompt_to_video",
        "platform": "instagram_reels"
    })
    assert res.status_code == 201
    proj_id = res.json()["id"]

    # List projects
    res = client.get("/api/projects")
    assert res.status_code == 200
    assert any(p["id"] == proj_id for p in res.json())

    # Get single project
    res = client.get(f"/api/projects/{proj_id}")
    assert res.status_code == 200
    assert res.json()["id"] == proj_id

    # Get project clips
    res = client.get(f"/api/projects/{proj_id}/clips")
    assert res.status_code == 200

def test_providers_and_settings(client):
    res = client.get("/api/providers")
    assert res.status_code == 200
    data = res.json()
    assert "video" in data
    assert "llm" in data

    res = client.get("/api/settings")
    assert res.status_code == 200

def test_storage_endpoints(client):
    res = client.get("/api/storage/stats")
    assert res.status_code == 200
    data = res.json()
    assert "media_storage_path" in data
    assert "free_gb" in data

def test_privacy_endpoints(client):
    res = client.get("/api/privacy/status")
    assert res.status_code == 200

    res = client.post("/api/privacy/settings", json={
        "privacy_mode": "cloud_assisted",
        "allow_cloud_transfers": True
    })
    assert res.status_code == 200
    assert res.json()["privacy_mode"] == "cloud_assisted"

    res = client.get("/api/privacy/audit-logs")
    assert res.status_code == 200

def test_generation_storyboard_endpoint(client):
    res = client.post("/api/generation/storyboard", json={
        "prompt": "Futuristic AI fitness tracker glowing on a runner wrist",
        "target_platform": "instagram_reels",
        "duration_seconds": 15.0,
        "aspect_ratio": "9:16",
        "visual_style": "cinematic",
        "voiceover_enabled": True,
        "voice_selection": "energetic_male",
        "caption_style": "bold_yellow",
        "background_music": "upbeat_synth",
        "language": "en",
        "num_scenes": 3,
        "quality": "standard"
    })
    assert res.status_code == 200
    data = res.json()
    assert "scenes" in data
    assert len(data["scenes"]) == 3

def test_trigger_prompt_to_video_endpoint(client):
    res = client.post("/api/generation/video", json={
        "prompt": "Futuristic AI smartwatch cinematic macro",
        "target_platform": "instagram_reels",
        "duration_seconds": 15.0,
        "aspect_ratio": "9:16",
        "visual_style": "cinematic",
        "voiceover_enabled": True,
        "voice_selection": "energetic_male",
        "caption_style": "bold_yellow",
        "background_music": "upbeat_synth",
        "language": "en",
        "num_scenes": 2,
        "quality": "standard"
    })
    assert res.status_code == 202
    data = res.json()
    assert "id" in data
    assert data["job_type"] == "prompt_to_video"
    assert data["status"] in ("pending", "running")
