from app.services.clip_selection.clip_ranker import clip_ranker

def test_hook_scoring():
    q_score = clip_ranker.evaluate_hook_strength("What if everything you knew about AI was wrong?")
    assert q_score >= 0.70

    b_score = clip_ranker.evaluate_hook_strength("The numbers on the spreadsheet.")
    assert b_score < q_score

def test_duration_fit():
    # Ideal duration around 30s
    score_30 = clip_ranker.evaluate_duration_fit(30.0, target_duration=30.0)
    score_5 = clip_ranker.evaluate_duration_fit(5.0, target_duration=30.0)
    assert score_30 > score_5
    assert score_30 == 1.0

def test_candidate_generation():
    segments = [
        {"start": 0.0, "end": 6.0, "text": "Why do most video editors struggle with pacing?"},
        {"start": 6.0, "end": 18.0, "text": "They spend too much time trimming silence instead of crafting hooks."},
        {"start": 18.0, "end": 32.0, "text": "ClipForge automates the entire workflow seamlessly."}
    ]
    candidates = clip_ranker.generate_candidate_clips(
        transcript_segments=segments,
        scene_cuts=[0.0, 6.0, 18.0],
        video_duration=35.0,
        target_duration=30.0,
        num_clips=2
    )
    assert len(candidates) > 0
    top = candidates[0]
    assert "start_time" in top
    assert "end_time" in top
    assert top["score"] > 0.5
    assert top["duration"] >= 12.0

