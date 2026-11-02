import sys
import time
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.utils.sample_media import create_sample_video

def main():
    print("=" * 60)
    print("TESTING FASTAPI API ENDPOINTS & ASYNC QUEUE DISPATCH")
    print("=" * 60)

    client = TestClient(app)

    # 1. Health check
    res = client.get("/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("[1] GET /health -> OK:", res.json())

    # 2. Providers and Settings
    res = client.get("/api/providers")
    assert res.status_code == 200, f"Providers failed: {res.text}"
    print("[2] GET /api/providers -> OK:", res.json())

    # 3. Storyboard Generation
    storyboard_payload = {
        "prompt": "Futuristic AI robotics revolutionizing healthcare in 15 seconds.",
        "target_platform": "instagram_reels",
        "duration_seconds": 15.0,
        "num_scenes": 3,
        "aspect_ratio": "9:16",
        "visual_style": "cinematic"
    }
    res = client.post("/api/generation/storyboard", json=storyboard_payload)
    assert res.status_code == 200, f"Storyboard failed: {res.text}"
    storyboard = res.json()
    assert len(storyboard["scenes"]) == 3
    print(f"[3] POST /api/generation/storyboard -> OK: Created {len(storyboard['scenes'])} scenes for '{storyboard['title']}'")

    # 4. Uploads endpoint with real video file
    sample_upload = settings.TEMP_DIR / "sample_api_test.mp4"
    create_sample_video(sample_upload, duration=6.0, width=1920, height=1080)

    with open(sample_upload, "rb") as f:
        res = client.post(
            "/api/uploads",
            files={"file": ("sample_test.mp4", f, "video/mp4")}
        )
    assert res.status_code == 201, f"Upload failed: {res.text}"
    asset = res.json()
    asset_id = asset["id"]
    project_id = asset["project_id"]
    print(f"[4] POST /api/uploads -> OK: Created Asset {asset_id} in Project {project_id}")

    # 5. Video analysis via background queue
    res = client.post(f"/api/videos/{asset_id}/analyze?target_clip_duration=4.0")
    assert res.status_code == 202, f"Analyze trigger failed: {res.text}"
    job_id = res.json()["id"]
    print(f"[5] POST /api/videos/{asset_id}/analyze -> Enqueued Job {job_id}")

    # Poll job status
    print("  -> Waiting for analysis background job...")
    completed = False
    for _ in range(30):
        time.sleep(1.0)
        res = client.get(f"/api/jobs/{job_id}")
        assert res.status_code == 200
        job_data = res.json()
        print(f"     Status: {job_data['status']} ({job_data['progress']}%) - {job_data['current_step']}")
        if job_data["status"] == "completed":
            completed = True
            break
        elif job_data["status"] == "failed":
            raise RuntimeError(f"Analysis job failed: {job_data.get('error_message')}")

    assert completed, "Analysis job timed out!"

    # 6. Check candidate clips
    res = client.get(f"/api/projects/{project_id}/clips")
    assert res.status_code == 200
    clips = res.json()
    assert len(clips) > 0, "No clips found after analysis!"
    print(f"[6] GET /api/projects/{project_id}/clips -> OK: Found {len(clips)} candidate clips")
    target_clip = clips[0]

    # 7. Render clip into Short via background queue
    res = client.post(f"/api/clips/{target_clip['id']}/render")
    assert res.status_code == 202
    render_job_id = res.json()["id"]
    print(f"[7] POST /api/clips/{target_clip['id']}/render -> Enqueued Job {render_job_id}")

    print("  -> Waiting for clip render background job...")
    render_completed = False
    for _ in range(40):
        time.sleep(1.0)
        res = client.get(f"/api/jobs/{render_job_id}")
        assert res.status_code == 200
        job_data = res.json()
        print(f"     Status: {job_data['status']} ({job_data['progress']}%) - {job_data['current_step']}")
        if job_data["status"] == "completed":
            render_completed = True
            break
        elif job_data["status"] == "failed":
            raise RuntimeError(f"Render job failed: {job_data.get('error_message')}")

    assert render_completed, "Render job timed out!"

    # 8. Check download endpoint for rendered Short
    res = client.get(f"/api/projects/{project_id}")
    assert res.status_code == 200
    proj_detail = res.json()
    rendered_clip = next(c for c in proj_detail["clips"] if c["id"] == target_clip["id"])
    download_url = rendered_clip["download_url"]
    print(f"[8] Rendered clip download URL: {download_url}")

    res = client.get(download_url)
    assert res.status_code == 200, f"Download failed: {res.status_code}"
    assert len(res.content) > 1000, "Downloaded media file is too small or empty!"
    print(f"  -> Successfully downloaded rendered MP4 ({len(res.content)} bytes)")

    print("=" * 60)
    print("ALL FASTAPI ENDPOINTS & BACKGROUND QUEUE DISPATCHERS VERIFIED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()

