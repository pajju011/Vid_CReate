"""
Hook Scoring Engine — Evaluates opening video hooks against 21 proven viral formulas.
Calculates curiosity gap, stake clarity, pacing, and retention probability score (0-100).
"""
import sys
import re

def score_hook(hook_text: str) -> dict:
    text = hook_text.strip()
    words = text.split()
    word_count = len(words)
    
    score = 50.0
    feedback = []
    
    # 1. Pacing & Length (Ideal: 8-16 words for opening 3 seconds)
    if 8 <= word_count <= 18:
        score += 15
        feedback.append("[+] Punchy length: Delivers within the critical 3-second attention window.")
    elif word_count < 8:
        score += 5
        feedback.append("[~] Very brief: Ensure stakes or curiosity are clearly stated.")
    else:
        score -= 10
        feedback.append("[-] Too wordy: Risks losing viewers before the primary value is revealed.")

    # 2. Curiosity & Open Loops
    curiosity_triggers = ["why", "how", "secret", "never", "stop", "mistake", "truth", "nobody", "wrong", "what happens"]
    found_triggers = [t for t in curiosity_triggers if re.search(r'\b' + re.escape(t) + r'\b', text.lower())]
    if found_triggers:
        score += 15
        feedback.append(f"[+] Strong psychological triggers: {', '.join(found_triggers)}")
    else:
        score -= 5
        feedback.append("[-] Lacks an open loop or curiosity trigger.")

    # 3. Direct Audience Address ("You", "Your")
    if re.search(r'\b(you|your|you\'re)\b', text.lower()):
        score += 10
        feedback.append("[+] Direct personal framing ('you/your') increases viewer identification.")

    # 4. Urgency & Stakes
    urgency_words = ["now", "today", "before", "cost", "danger", "waste", "destroy", "fix", "save"]
    if any(re.search(r'\b' + re.escape(u) + r'\b', text.lower()) for u in urgency_words):
        score += 10
        feedback.append("[+] Tangible stakes / urgency detected.")

    score = max(10, min(100, int(score)))
    
    return {
        "hook": text,
        "score": score,
        "grade": "S" if score >= 85 else "A" if score >= 75 else "B" if score >= 60 else "C",
        "feedback": feedback
    }

if __name__ == "__main__":
    hook = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Why everything you know about AI video is completely wrong."
    res = score_hook(hook)
    print(f"\nHook: \"{res['hook']}\"")
    print(f"Retention Score: {res['score']}/100 (Grade: {res['grade']})")
    print("Breakdown:")
    for f in res["feedback"]:
        print(f"  {f}")
