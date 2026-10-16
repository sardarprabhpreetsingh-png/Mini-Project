import os
import json
import re
import time
from typing import Dict, Any, Optional, List

from backend.config import GEMINI_API_KEY, GEMINI_MODEL


def sanitize_gemini_message(msg: str, api_key: str = "") -> str:
    """
    Removes any API keys or credentials from error message strings to prevent credential leaks.
    """
    if not msg:
        return ""
    if api_key and len(api_key) > 5:
        msg = msg.replace(api_key, "[REDACTED_API_KEY]")
    # Mask any Google API key pattern
    msg = re.sub(r"AIza[0-9A-Za-z\-_]{35}", "[REDACTED_API_KEY]", msg)
    # Mask query parameter keys
    msg = re.sub(r"([?&]key=)[^&\s]+", r"\1[REDACTED_API_KEY]", msg)
    return msg


def parse_gemini_error(error: Exception, model_name: str, api_key: str = "") -> Dict[str, Any]:
    """
    Parses a Gemini API exception into a structured diagnostic report with actionable alternatives.
    Guarantees that the API key is never exposed.
    """
    raw_msg = sanitize_gemini_message(str(error), api_key)
    error_type = type(error).__name__
    status_code = getattr(error, "code", getattr(error, "status_code", None))

    is_404 = (
        status_code == 404
        or "404" in raw_msg
        or "NOT_FOUND" in raw_msg
        or "no longer available" in raw_msg.lower()
        or "not found" in raw_msg.lower()
    )

    is_429 = (
        status_code == 429
        or "429" in raw_msg
        or "RESOURCE_EXHAUSTED" in raw_msg
        or "quota" in raw_msg.lower()
        or "rate limit" in raw_msg.lower()
    )

    is_auth = (
        status_code in [400, 401, 403]
        and ("API_KEY_INVALID" in raw_msg or "permission" in raw_msg.lower() or "unauthenticated" in raw_msg.lower())
    )

    is_503 = (
        status_code == 503
        or "503" in raw_msg
        or "UNAVAILABLE" in raw_msg
        or "high demand" in raw_msg.lower()
    )

    is_network = "timeout" in raw_msg.lower() or "connection" in raw_msg.lower()

    if is_404:
        user_message = (
            f"Configured model '{model_name}' is not found or is no longer available to new users. "
            f"Please update 'GEMINI_MODEL' in your .env file to a supported model such as 'gemini-3.8-flash' or 'gemini-2.5-flash-lite'."
        )
        suggested_alternatives = ["gemini-3.8-flash", "gemini-2.5-flash-lite", "gemini-3.1-flash-lite"]
    elif is_429:
        user_message = (
            f"Gemini API free-tier quota limit exceeded for model '{model_name}'. "
            f"Supported lightweight alternatives with separate quotas include 'gemini-2.5-flash-lite' or 'gemini-3.1-flash-lite'. "
            f"You can configure GEMINI_MODEL=gemini-2.5-flash-lite in project-root .env or upgrade your Google AI Studio quota."
        )
        suggested_alternatives = ["gemini-2.5-flash-lite", "gemini-3.1-flash-lite"]
    elif is_auth:
        user_message = (
            "Gemini API authentication failed. Please verify that GEMINI_API_KEY in project-root .env is valid."
        )
        suggested_alternatives = []
    elif is_503:
        user_message = (
            f"Model '{model_name}' is temporarily experiencing high demand (503 UNAVAILABLE). "
            f"Try again shortly or configure GEMINI_MODEL=gemini-2.5-flash-lite in .env."
        )
        suggested_alternatives = ["gemini-2.5-flash-lite", "gemini-3.1-flash-lite"]
    elif is_network:
        user_message = "Gemini API network connection timed out or failed. Check your internet connection."
        suggested_alternatives = []
    else:
        user_message = f"Gemini API error ({error_type}): {raw_msg}"
        suggested_alternatives = ["gemini-3.8-flash", "gemini-2.5-flash-lite"]

    return {
        "status_code": status_code,
        "error_type": error_type,
        "model_attempted": model_name,
        "user_message": user_message,
        "suggested_alternatives": suggested_alternatives,
        "raw_message": raw_msg
    }


def verify_gemini_model_availability(
    model_name: Optional[str] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Verifies that the configured Gemini model is accessible and ready to generate content with the API key.
    If unavailable, reports the exact error and identifies supported alternatives.
    Does NOT silently switch models.
    """
    target_model = model_name or GEMINI_MODEL
    key_to_use = api_key or GEMINI_API_KEY

    if not key_to_use:
        return {
            "available": False,
            "model": target_model,
            "error": "GEMINI_API_KEY environment variable is not configured.",
            "suggested_alternatives": []
        }

    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=key_to_use)
        client.models.generate_content(
            model=target_model,
            contents="ping",
            config=types.GenerateContentConfig(
                max_output_tokens=10,
                thinking_config=types.ThinkingConfig(thinking_budget=128)
            )
        )
        return {
            "available": True,
            "model": target_model,
            "message": f"Model '{target_model}' verified and ready for generation.",
            "suggested_alternatives": []
        }
    except Exception as e:
        diag = parse_gemini_error(e, target_model, key_to_use)
        return {
            "available": False,
            "model": target_model,
            "error": diag["user_message"],
            "status_code": diag["status_code"],
            "suggested_alternatives": diag["suggested_alternatives"]
        }


def build_fallback_feedback(
    transcript: str,
    analysis: Dict[str, Any],
    reason: str = "",
    error_details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generates intelligent rule-based coaching feedback based directly on the calculated measurements
    when Gemini API key is missing or encounters a network/quota issue.
    """
    pacing = analysis.get("pacing", {})
    fillers = analysis.get("fillers", {})
    pauses = analysis.get("pauses", {})
    repetitions = analysis.get("repetitions", {})
    score = analysis.get("score", {})

    wpm = pacing.get("wpm", 0)
    filler_count = fillers.get("total_fillers", 0)
    filler_ratio = fillers.get("filler_ratio_percent", 0.0)
    flow = pauses.get("flow_rating", "Continuous")
    consecutive_repeats = repetitions.get("consecutive_repeats_count", 0)

    # Strengths based on real data
    strengths = []
    if 125 <= wpm <= 165:
        strengths.append(f"Ideal speaking rate of {wpm} WPM kept the listener engaged without feeling rushed.")
    elif wpm > 0:
        strengths.append(f"Clear steady momentum maintained across {analysis.get('word_count', 0)} spoken words.")

    if filler_ratio <= 2.5:
        strengths.append(f"Very low filler word usage ({filler_ratio}% of words), displaying solid verbal discipline.")
    else:
        strengths.append("Audible speech segments were recognized and transcribed with clear lexical articulation.")

    if consecutive_repeats == 0:
        strengths.append("Zero stammering or consecutive repeated words detected in your phrases.")

    if pauses.get("pause_count", 0) > 0:
        strengths.append(f"Integrated {pauses.get('pause_count')} natural breath pauses to separate distinct thoughts.")

    # Weaknesses / Areas for improvement
    weaknesses = []
    if wpm > 165:
        weaknesses.append(f"Your pace of {wpm} WPM is above the recommended 130-160 WPM range. Important points may get lost.")
    elif 0 < wpm < 120:
        weaknesses.append(f"Your tempo of {wpm} WPM is deliberate but might cause the audience's attention to drift.")

    if filler_ratio > 3.0:
        top_fillers = list(fillers.get("breakdown", {}).keys())[:3]
        weaknesses.append(f"Detected {filler_count} filler words ({', '.join(top_fillers) if top_fillers else 'um/uh'}), accounting for {filler_ratio}% of spoken words.")

    if consecutive_repeats > 0:
        weaknesses.append(f"Detected {consecutive_repeats} repeated words in quick succession, indicating hesitation or cognitive search.")

    if pauses.get("pause_count", 0) == 0 and analysis.get("word_count", 0) > 30:
        weaknesses.append("Lack of distinct pauses between ideas; speech came across as one continuous breath.")

    if not weaknesses:
        weaknesses.append("Maintain vocal projection and practice varying inflection to emphasize key takeaways.")

    # Actionable exercises
    actionable_exercises = [
        {
            "title": "The 'Power Pause' Drill",
            "instruction": "Whenever you feel the urge to say a filler word like 'um' or 'actually', close your lips and take a silent 1-second breath. Silence projects confidence."
        },
        {
            "title": "Metronome Pacing Practice",
            "instruction": "Practice reading a 150-word passage in exactly 60 seconds to internalize the target rate of 140-150 WPM."
        },
        {
            "title": "Thought-Chunking Technique",
            "instruction": "Divide your key points into short 5-7 word phrases. Pause for half a second after each chunk to give the listener time to absorb your message."
        }
    ]

    # Rephrasing suggestions if filler words exist
    rephrasing_suggestions = []
    top_breakdown = fillers.get("breakdown", {})
    if top_breakdown:
        most_common_filler = max(top_breakdown, key=top_breakdown.get)
        rephrasing_suggestions.append({
            "original": f"Using '{most_common_filler}' as a conversational bridge",
            "improved": "Replace with a purposeful 1-second pause",
            "reason": f"Eliminates verbal clutter and signals composure (appeared {top_breakdown[most_common_filler]} times)."
        })

    summary = (
        f"Your presentation scored {score.get('score', 75)}/100 ({score.get('level', 'Proficient')}). "
        f"You spoke {analysis.get('word_count', 0)} words at {wpm} WPM with {filler_count} filler words. "
        + ("Focus on grounding your pacing and trading filler words for deliberate pauses." if filler_count > 2 or wpm > 165 else "Overall strong clarity and delivery fundamentals.")
    )

    fallback_notice = (
        "Generated by SpeakSense Heuristic Speech Engine. "
        + ("Configure GEMINI_API_KEY in .env for generative AI coaching." if not GEMINI_API_KEY else f"Notice: {reason}")
    )

    result = {
        "source": "heuristic_fallback",
        "is_ai_available": False,
        "model_used": "SpeakSense Rule Engine",
        "notice": fallback_notice,
        "summary": summary,
        "delivery_assessment": f"Pacing evaluated at {wpm} WPM ({pacing.get('status', 'Measured')}). {pacing.get('message', '')}",
        "structure_and_clarity": f"Speech flow is {flow} with a vocabulary diversity of {repetitions.get('vocabulary_diversity_ratio', 0.5):.2f}.",
        "strengths": strengths[:4],
        "weaknesses": weaknesses[:4],
        "actionable_exercises": actionable_exercises,
        "rephrasing_suggestions": rephrasing_suggestions
    }

    if error_details:
        result["error_details"] = error_details

    return result


def generate_ai_feedback(
    transcript: str,
    analysis: Dict[str, Any],
    model_override: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calls Google Gemini API using the official google-genai SDK to generate
    tailored speech coaching based STRICTLY on the measured metrics.
    Falls back gracefully to the heuristic engine if the API key is missing or an error occurs.
    """
    model_to_use = model_override or GEMINI_MODEL

    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY not configured. Using SpeakSense heuristic coaching engine.")
        return build_fallback_feedback(
            transcript,
            analysis,
            reason="GEMINI_API_KEY environment variable is not set."
        )

    try:
        from google import genai
        from google.genai import types
        from google.genai.errors import ServerError, ClientError
    except ImportError as ie:
        print(f"google-genai SDK import error: {ie}. Using heuristic fallback.")
        return build_fallback_feedback(
            transcript,
            analysis,
            reason="The google-genai package is not available."
        )

    client = genai.Client(api_key=GEMINI_API_KEY)

    # Build prompt embedding true measurements
    pacing = analysis.get("pacing", {})
    fillers = analysis.get("fillers", {})
    pauses = analysis.get("pauses", {})
    repetitions = analysis.get("repetitions", {})
    score = analysis.get("score", {})

    system_instruction = (
        "You are SpeakSense AI, a world-class speech and executive communication coach. "
        "You provide constructive, encouraging, measurable, and highly actionable feedback to help "
        "speakers improve their public speaking, presentation delivery, and interview skills.\n"
        "CRITICAL RULES:\n"
        "1. Base your assessment ONLY on the provided transcript and the exact calculated measurements.\n"
        "2. Never fabricate statistics; always reference the provided numbers.\n"
        "3. Return your entire output as a single, valid JSON object without surrounding markdown fences."
    )

    user_prompt = f"""
Here are the exact speech measurements and transcript from the user's audio:

[MEASURED DATA]
- Total Words: {analysis.get('word_count', 0)}
- Audio Duration: {analysis.get('duration_formatted', '0s')} ({analysis.get('duration_seconds', 0)}s)
- Speaking Speed: {pacing.get('wpm', 0)} WPM (Target: 130-160 WPM, Pacing Status: {pacing.get('status', 'Unknown')})
- Filler Words Count: {fillers.get('total_fillers', 0)} ({fillers.get('filler_ratio_percent', 0)}% of words)
- Filler Words Breakdown: {json.dumps(fillers.get('breakdown', {}))}
- Consecutive Repeated Words: {json.dumps(repetitions.get('consecutive_repeats', {}))}
- Frequent Words: {json.dumps(repetitions.get('frequent_words', {}))}
- Pause Count: {pauses.get('pause_count', 0)}
- Average Pause Duration: {pauses.get('avg_pause_duration_sec', 0)}s
- Calculated Score: {score.get('score', 75)}/100 ({score.get('level', 'Proficient')})

[FULL TRANSCRIPT]
"{transcript}"

Analyze this speech and return a JSON object with EXACTLY this structure:
{{
  "summary": "2-3 sentences summarizing the speaker's overall effectiveness, citing their WPM and score.",
  "delivery_assessment": "1-2 paragraphs assessing tempo, energy, and articulation.",
  "structure_and_clarity": "1-2 paragraphs evaluating how clearly ideas are communicated and structured.",
  "strengths": [
    "Specific strength 1 with reference to transcript or stats",
    "Specific strength 2 with reference to transcript or stats",
    "Specific strength 3"
  ],
  "weaknesses": [
    "Specific weakness 1 to work on",
    "Specific weakness 2 to work on"
  ],
  "actionable_exercises": [
    {{
      "title": "Exercise Name",
      "instruction": "Concrete step-by-step guidance on how to practice this."
    }}
  ],
  "rephrasing_suggestions": [
    {{
      "original": "exact weak or filler-laden phrase from transcript",
      "improved": "impactful professional alternative",
      "reason": "why this improves clarity"
    }}
  ]
}}
"""

    max_attempts = 2
    last_error = None

    for attempt in range(max_attempts):
        try:
            # Set max_output_tokens=4000 to prevent truncated JSON when reasoning tokens are generated
            # Bounding thinking budget to 512 keeps response times snappy and prevents runaway tokens
            gen_config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3,
                max_output_tokens=4000,
                thinking_config=types.ThinkingConfig(thinking_budget=512),
                response_mime_type="application/json"
            )

            response = client.models.generate_content(
                model=model_to_use,
                contents=user_prompt,
                config=gen_config
            )

            raw_text = response.text or ""
            if not raw_text and getattr(response, "candidates", None) and response.candidates:
                parts = getattr(response.candidates[0].content, "parts", [])
                raw_text = "".join([getattr(p, "text", "") for p in parts if getattr(p, "text", "")])

            # Clean any accidental markdown code fences
            cleaned_text = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
            cleaned_text = re.sub(r"\s*```$", "", cleaned_text.strip())

            # Find outermost JSON object
            json_match = re.search(r"\{.*\}", cleaned_text, re.DOTALL)
            if json_match:
                feedback_data = json.loads(json_match.group(0))
            else:
                feedback_data = json.loads(cleaned_text)

            feedback_data["source"] = "gemini_ai"
            feedback_data["is_ai_available"] = True
            feedback_data["model_used"] = model_to_use
            feedback_data["notice"] = f"Powered by Google Gemini ({model_to_use})."

            return feedback_data

        except ServerError as se:
            # 503 UNAVAILABLE or demand spike - retry once if attempts remain
            last_error = se
            if attempt < max_attempts - 1:
                time.sleep(1.5)
                continue
            break
        except ClientError as ce:
            # 404, 429, 401, 403 - permanent/quota errors, do not retry blindly
            last_error = ce
            break
        except Exception as e:
            last_error = e
            if attempt < max_attempts - 1:
                time.sleep(1.0)
                continue
            break

    # If all attempts failed, diagnose error cleanly without exposing the API key
    diag = parse_gemini_error(last_error, model_to_use, GEMINI_API_KEY)
    print(f"Gemini API request failed for model '{model_to_use}': {diag['user_message']}. Falling back to rule-based engine.")

    return build_fallback_feedback(
        transcript,
        analysis,
        reason=diag["user_message"],
        error_details=diag
    )
