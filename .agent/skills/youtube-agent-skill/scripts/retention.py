"""
Audience Retention CSV Analyzer.
Reads time/percentage points from YouTube Studio exports to identify Hook Leaks and Drop Cliffs.
"""
import sys
import csv

def analyze_retention_points(points: list) -> dict:
    """
    points: list of tuples (second: float, retention_pct: float)
    """
    if not points:
        return {"error": "No retention data provided"}
        
    points.sort(key=lambda p: p[0])
    
    # 1. 30-Second Hook Score (Standard YouTube metric)
    ret_30s = None
    for sec, pct in points:
        if sec >= 30:
            ret_30s = pct
            break
    if ret_30s is None and points:
        ret_30s = points[-1][1]
        
    hook_leak = ret_30s < 60.0
    
    # 2. Drop Cliffs (where retention drops by >5% in <5 seconds)
    cliffs = []
    for i in range(1, len(points)):
        t_prev, p_prev = points[i-1]
        t_curr, p_curr = points[i]
        dt = t_curr - t_prev
        dp = p_prev - p_curr
        if dt <= 10 and dp >= 5.0:
            cliffs.append({
                "timestamp": f"{int(t_curr // 60)}:{int(t_curr % 60):02d}",
                "drop_percentage": round(dp, 1)
            })
            
    return {
        "retention_at_30s": round(ret_30s, 1),
        "hook_health": "Strong (>70%)" if ret_30s >= 70 else "Average (60-70%)" if ret_30s >= 60 else "Hook Leak (<60%)",
        "drop_cliffs_detected": len(cliffs),
        "cliffs": cliffs[:5]
    }

if __name__ == "__main__":
    demo_data = [
        (0, 100.0), (5, 92.0), (15, 80.0), (30, 68.0),
        (45, 65.0), (60, 52.0), (90, 48.0), (120, 42.0)
    ]
    res = analyze_retention_points(demo_data)
    print("\n--- Audience Retention Diagnosis ---")
    print(f"30-Second Retention: {res['retention_at_30s']}% ({res['hook_health']})")
    print(f"Drop Cliffs Detected: {res['drop_cliffs_detected']}")
    for c in res["cliffs"]:
        print(f"  [!] Drop at {c['timestamp']}: -{c['drop_percentage']}%")
