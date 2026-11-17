"""
Title & Thumbnail Packaging Linter — Checks title length, mobile truncation, and text overlap.
"""
import sys

def lint_package(title: str, thumb_text: str = "") -> dict:
    title = title.strip()
    thumb_text = thumb_text.strip()
    
    char_len = len(title)
    word_count = len(title.split())
    
    issues = []
    strengths = []
    
    # 1. Mobile Truncation Check (<50 chars is safe on mobile)
    if char_len <= 50:
        strengths.append(f"Mobile-safe length ({char_len} chars): Will not truncate on YouTube mobile feeds.")
    elif char_len <= 65:
        issues.append(f"Borderline length ({char_len} chars): May truncate on smaller phone screens. Keep key words at the start.")
    else:
        issues.append(f"Severe mobile truncation ({char_len} chars): Viewers on mobile will only see the first 50 characters.")

    # 2. Text Redundancy Between Title and Thumbnail
    if thumb_text:
        title_words = set(w.lower() for w in title.split())
        thumb_words = set(w.lower() for w in thumb_text.split())
        overlap = title_words.intersection(thumb_words)
        # remove trivial stopwords
        overlap = {w for w in overlap if len(w) > 3}
        if overlap:
            issues.append(f"Redundant text: Both title and thumbnail repeat '{', '.join(overlap)}'. Thumbnail text should complement, not repeat the title.")
        else:
            strengths.append("High synergy: Title and thumbnail deliver separate, complementary information.")

    # 3. All-Caps or Clickbait Shouting
    if title.isupper():
        issues.append("All caps: Can trigger spam filtering and reduce long-term browse CTR.")
    
    score = 100 - (len(issues) * 20)
    score = max(20, min(100, score))
    
    return {
        "title": title,
        "thumbnail_text": thumb_text,
        "score": score,
        "strengths": strengths,
        "issues": issues
    }

if __name__ == "__main__":
    t = sys.argv[1] if len(sys.argv) > 1 else "How I Built an AI Video Generator in 7 Days"
    th = sys.argv[2] if len(sys.argv) > 2 else "It actually works!"
    res = lint_package(t, th)
    print(f"\nTitle: \"{res['title']}\"")
    print(f"Thumbnail Text: \"{res['thumbnail_text']}\"")
    print(f"Package Score: {res['score']}/100")
    if res["strengths"]:
        print("\nStrengths:")
        for s in res["strengths"]:
            print(f"  [+] {s}")
    if res["issues"]:
        print("\nOptimization Opportunities:")
        for i in res["issues"]:
            print(f"  [-] {i}")
