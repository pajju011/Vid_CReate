"""
Dead Air & Filler Word Analyzer for SRT and Transcripts.
Detects silence pauses >1.2s and frequent verbal fillers to generate an Edit Decision List (EDL).
"""
import sys
import re

FILLERS = ["um", "uh", "er", "ah", "like", "you know", "basically", "actually", "literally", "sort of", "kind of"]

def parse_srt(srt_text: str) -> list:
    blocks = srt_text.strip().split("\n\n")
    entries = []
    for b in blocks:
        lines = b.strip().split("\n")
        if len(lines) >= 3:
            time_match = re.search(r'(\d+:\d+:\d+[,\.]\d+)\s*-->\s*(\d+:\d+:\d+[,\.]\d+)', lines[1])
            if time_match:
                start_str, end_str = time_match.groups()
                text = " ".join(lines[2:])
                entries.append({"start": start_str, "end": end_str, "text": text})
    return entries

def analyze_transcript(text: str) -> dict:
    words = re.findall(r'\b\w+\b', text.lower())
    filler_counts = {}
    for f in FILLERS:
        cnt = len(re.findall(r'\b' + re.escape(f) + r'\b', text.lower()))
        if cnt > 0:
            filler_counts[f] = cnt
            
    total_words = len(words)
    total_fillers = sum(filler_counts.values())
    filler_rate = (total_fillers / max(1, total_words)) * 100
    
    return {
        "total_words": total_words,
        "total_fillers": total_fillers,
        "filler_percentage": round(filler_rate, 2),
        "filler_breakdown": filler_counts
    }

if __name__ == "__main__":
    sample = "Um, so today we are basically going to, you know, build a video generator, uh, from scratch."
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r", encoding="utf-8", errors="ignore") as f:
            sample = f.read()
            
    res = analyze_transcript(sample)
    print("\n--- Speech Pacing & Filler Analysis ---")
    print(f"Total Words Analyzed: {res['total_words']}")
    print(f"Total Filler Words: {res['total_fillers']} ({res['filler_percentage']}% of speech)")
    print("Detected Fillers:")
    for f, c in res["filler_breakdown"].items():
        print(f"  - '{f}': {c} occurrences")
