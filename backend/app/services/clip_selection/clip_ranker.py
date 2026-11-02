import math
import re
from typing import List, Dict, Any, Optional

HOOK_KEYWORDS = [
    "how", "why", "what", "imagine", "have you", "stop", "secret", "never",
    "best", "truth", "revealed", "mind-blowing", "future", "money", "mistake",
    "transform", "nobody", "crazy", "warning", "fastest", "discover"
]

class ClipRankingEngine:
    def evaluate_hook_strength(self, text: str) -> float:
        """Score opening hook based on curiosity, questions, and trigger words."""
        cleaned = text.lower()
        score = 0.3 # base score
        if "?" in text[:60]:
            score += 0.35 # Questions make great hooks
        if any(kw in cleaned[:40] for kw in HOOK_KEYWORDS):
            score += 0.30
        if "!" in text[:60]:
            score += 0.15
        return min(1.0, score)

    def evaluate_duration_fit(self, duration: float, target_duration: float = 30.0) -> float:
        """Gaussian bell curve penalty for deviation from optimal short duration."""
        # Optimal range is 20s to 45s
        if duration < 10.0 or duration > 90.0:
            return 0.1
        diff = abs(duration - target_duration)
        return max(0.2, math.exp(-0.5 * (diff / 12.0) ** 2))

    def evaluate_coherence(self, start_text: str, end_text: str) -> float:
        """Reward complete sentences starting with capital and ending with punctuation."""
        score = 0.5
        if start_text and start_text[0].isupper():
            score += 0.25
        if end_text and end_text[-1] in (".", "!", "?"):
            score += 0.25
        return min(1.0, score)

    def generate_candidate_clips(
        self,
        transcript_segments: List[Dict[str, Any]],
        scene_cuts: List[float],
        video_duration: float,
        target_duration: float = 30.0,
        num_clips: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Produce top-ranked non-overlapping candidate clips aligned with sentence
        and speech pause boundaries.
        """
        if not transcript_segments:
            # Fallback if no transcript is available: partition video into target_duration segments
            candidates = []
            cur = 0.0
            clip_idx = 1
            while cur < video_duration and len(candidates) < num_clips:
                clip_end = min(video_duration, cur + target_duration)
                if clip_end - cur < 5.0:
                    break
                candidates.append({
                    "start_time": round(cur, 2),
                    "end_time": round(clip_end, 2),
                    "duration": round(clip_end - cur, 2),
                    "score": 0.70,
                    "title": f"Highlight Moment #{clip_idx}",
                    "hook": "Key visual moment",
                    "reason": "Optimal visual duration segment"
                })
                cur += target_duration
                clip_idx += 1
            return candidates

        raw_candidates = []
        n = len(transcript_segments)

        for i in range(n):
            start_seg = transcript_segments[i]
            clip_start = start_seg.get("start", 0.0)

            # Accumulate subsequent segments to reach optimal target duration
            for j in range(i, n):
                end_seg = transcript_segments[j]
                clip_end = end_seg.get("end", clip_start + 1.0)
                duration = clip_end - clip_start

                if 12.0 <= duration <= 60.0:
                    combined_text = " ".join(s.get("text", "") for s in transcript_segments[i:j+1])
                    start_text = start_seg.get("text", "")
                    end_text = end_seg.get("text", "")

                    s_hook = self.evaluate_hook_strength(start_text)
                    s_dur = self.evaluate_duration_fit(duration, target_duration)
                    s_coh = self.evaluate_coherence(start_text, end_text)

                    # Normalized weighted total score
                    total_score = round(0.40 * s_hook + 0.35 * s_dur + 0.25 * s_coh, 3)

                    # Extract concise title and hook
                    words = combined_text.split()
                    title = " ".join(words[:5]) + ("..." if len(words) > 5 else "")
                    hook_sentence = words[:8]

                    raw_candidates.append({
                        "start_time": round(clip_start, 2),
                        "end_time": round(clip_end, 2),
                        "duration": round(duration, 2),
                        "score": total_score,
                        "title": title.capitalize(),
                        "hook": " ".join(hook_sentence),
                        "reason": f"High hook score ({s_hook:.2f}) and balanced narrative flow"
                    })

        # Sort all raw candidates by score descending
        raw_candidates.sort(key=lambda c: c["score"], reverse=True)

        # Non-maximum suppression (prevent picking heavily overlapping segments)
        selected: List[Dict[str, Any]] = []
        for cand in raw_candidates:
            overlap = False
            for sel in selected:
                # Check overlap
                intersection = max(0.0, min(cand["end_time"], sel["end_time"]) - max(cand["start_time"], sel["start_time"]))
                min_len = min(cand["duration"], sel["duration"])
                if min_len > 0 and (intersection / min_len) > 0.35:
                    overlap = True
                    break
            if not overlap:
                selected.append(cand)
                if len(selected) >= num_clips:
                    break

        # If selected is empty (e.g. video was very short), return at least one clip
        if not selected and transcript_segments:
            first_seg = transcript_segments[0]
            last_seg = transcript_segments[-1]
            dur = max(1.0, last_seg.get("end", 5.0) - first_seg.get("start", 0.0))
            selected.append({
                "start_time": round(first_seg.get("start", 0.0), 2),
                "end_time": round(last_seg.get("end", dur), 2),
                "duration": round(dur, 2),
                "score": 0.80,
                "title": "Complete Short Highlight",
                "hook": first_seg.get("text", "")[:40],
                "reason": "Complete spoken segment"
            })

        return selected

clip_ranker = ClipRankingEngine()

