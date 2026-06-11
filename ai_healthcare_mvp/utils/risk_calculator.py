import math

def ai_health_risk_score(steps, pain, medicine, sleep, mood):
    try:
        steps = float(steps or 0)
        pain = float(pain or 0)
        sleep = float(sleep or 0)

        pain_score = min(max(pain / 10, 0), 1)

        steps_score = (
            0.1 if steps > 10000 else
            0.3 if steps > 6000 else
            0.5 if steps > 3000 else 0.9
        )

        med_score = 0.05 if medicine == "Yes" else 0.35

        sleep_score = 0.1 if sleep >= 7 else 0.4 if sleep >= 5 else 0.7

        mood = (mood or "").lower()
        mood_score = (
            0.1 if mood in ["happy", "energetic", "relaxed"] else
            0.6 if mood in ["sad", "tired", "stressed"] else 0.3
        )

        total = (
            0.55 * pain_score +
            0.15 * steps_score +
            0.10 * med_score +
            0.10 * sleep_score +
            0.10 * mood_score
        )

        risk = round(math.pow(total, 1.4) * 100, 2)

        if risk >= 65:
            return "High", risk, "Immediate consultation advised"
        elif risk >= 40:
            return "Moderate", risk, "Monitor closely"
        return "Low", risk, "Maintain routine"

    except Exception:
        return "Low", 0, "Invalid input"