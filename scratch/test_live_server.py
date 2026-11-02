import subprocess
import time
import httpx
import sys

def main():
    print("Starting uvicorn server process...")
    cmd = [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--app-dir", "backend",
        "--host", "127.0.0.1",
        "--port", "8000"
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        # Wait for server to boot
        time.sleep(3)
        with httpx.Client(base_url="http://127.0.0.1:8000", trust_env=False, timeout=10) as client:
            res = client.get("/health")
            print("Health check response:", res.status_code, res.json())
            assert res.status_code == 200

            res_prov = client.get("/api/providers")
            print("Providers response:", res_prov.status_code, res_prov.json())
            assert res_prov.status_code == 200

            res_story = client.post(
                "/api/generation/storyboard",
                json={
                    "prompt": "Futuristic smart watch with biometric AI",
                    "target_platform": "instagram_reels",
                    "duration_seconds": 15.0,
                    "num_scenes": 3,
                    "aspect_ratio": "9:16",
                    "visual_style": "cinematic"
                }
            )
            print("Storyboard response:", res_story.status_code, res_story.json()["title"])
            assert res_story.status_code == 200

            print("ALL LIVE SERVER ENDPOINTS RESPONDED WITH HTTP 200!")
    finally:
        proc.terminate()
        proc.wait(timeout=5)
        print("Uvicorn process cleanly terminated.")

if __name__ == "__main__":
    main()
