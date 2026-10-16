import re
import math
from typing import Dict, Any, List, Optional
from collections import Counter

from backend.config import (
    DEFAULT_FILLER_WORDS,
    DEFAULT_TARGET_WPM_MIN,
    DEFAULT_TARGET_WPM_MAX,
    DEFAULT_PAUSE_THRESHOLD_SEC
)

# Common grammatical stop words to ignore when looking for content-word repetitions
COMMON_STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", 
    "of", "with", "by", "from", "up", "about", "into", "over", "after",
    "is", "am", "are", "was", "were", "be", "been", "being", "have", "has", 
    "had", "do", "does", "did", "can", "could", "will", "would", "shall", 
    "should", "may", "might", "must", "it", "its", "this", "that", "these",
    "those", "there", "here", "i", "you", "he", "she", "we", "they", "me",
    "him", "her", "us", "them", "my", "your", "his", "our", "their"
}


def clean_text_words(text: str) -> List[str]:
    """Extract individual words in lowercase without punctuation."""
    return re.findall(r"\b[a-zA-Z']+\b", text.lower())


def analyze_pacing(word_count: int, duration_sec: float) -> Dict[str, Any]:
    """
    Computes speaking speed in Words Per Minute (WPM) and evaluates pacing status.
    """
    if duration_sec <= 0 or word_count == 0:
        return {
            "wpm": 0,
            "status": "Inconclusive",
            "status_color": "neutral",
            "message": "Not enough speech data to calculate pacing."
        }

    duration_min = duration_sec / 60.0
    wpm = round(word_count / duration_min, 1)

    if wpm < 110:
        status = "Very Slow"
        status_color = "warning"
        message = "Pacing is slower than average; speech may feel hesitant."
    elif 110 <= wpm < 130:
        status = "Deliberate"
        status_color = "info"
        message = "Steady and deliberate pace. Clear, though slightly conservative."
    elif 130 <= wpm <= 165:
        status = "Optimal"
        status_color = "success"
        message = "Ideal conversational and presentation tempo. Engaging and easy to follow."
    elif 165 < wpm <= 185:
        status = "Fast"
        status_color = "warning"
        message = "Slightly fast. Keep energy while ensuring clear articulation."
    else:
        status = "Very Fast"
        status_color = "danger"
        message = "Speaking tempo is rushed. Practice introducing pauses to let ideas land."

    return {
        "wpm": wpm,
        "status": status,
        "status_color": status_color,
        "message": message,
        "target_range": f"{DEFAULT_TARGET_WPM_MIN} - {DEFAULT_TARGET_WPM_MAX} WPM"
    }


def analyze_filler_words(text: str, custom_fillers: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Detects and counts configurable filler words and phrases using robust word boundaries.
    Avoids substring false positives and handles multi-word phrases correctly.
    Returns total count, per-filler breakdown, detailed occurrences, and diagnostics.
    """
    # 1. Normalize and deduplicate filler vocabulary
    raw_fillers = custom_fillers if custom_fillers and len(custom_fillers) > 0 else DEFAULT_FILLER_WORDS
    seen = set()
    normalized_fillers = []
    for item in raw_fillers:
        cleaned = item.strip().lower()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            normalized_fillers.append(cleaned)

    # Handle empty or whitespace text
    if not text or not text.strip():
        return {
            "total_fillers": 0,
            "filler_ratio_percent": 0.0,
            "rating": "Excellent",
            "rating_color": "success",
            "message": "No speech text provided.",
            "breakdown": {},
            "checked_fillers": normalized_fillers,
            "occurrences": [],
            "diagnostics": {
                "detected_fillers": [],
                "unmatched_fillers": normalized_fillers,
                "occurrences_count": 0,
                "total_words_analyzed": 0,
                "vocabulary_size": len(normalized_fillers),
                "detection_rule": "Word-boundary regex match (\\b...\\b) with case-insensitivity. Substrings inside words are excluded.",
                "note": "Transcript was empty or contained no text."
            }
        }

    # 2. Sort multi-word phrases first (by word count descending), then by character length descending
    # This prevents sub-phrases or single words from greedily fragmenting multi-word expressions
    sorted_fillers = sorted(normalized_fillers, key=lambda f: (len(f.split()), len(f)), reverse=True)

    # 3. Construct unified regex pattern with named groups and word boundaries
    patterns = []
    group_to_canonical = {}
    for idx, filler in enumerate(sorted_fillers):
        gname = f"f_{idx}"
        words = filler.split()
        # Ensure flexible whitespace between words in multi-word fillers (e.g. "you  know")
        phrase_pattern = r"\s+".join(re.escape(w) for w in words)
        patterns.append(rf"(?P<{gname}>\b{phrase_pattern}\b)")
        group_to_canonical[gname] = filler

    combined_pattern = re.compile("|".join(patterns), re.IGNORECASE)

    occurrences: List[Dict[str, Any]] = []
    detected_counts: Dict[str, int] = {}

    # 4. Scan text for non-overlapping matches
    for m in combined_pattern.finditer(text):
        gname = m.lastgroup
        if not gname or gname not in group_to_canonical:
            continue
        canon = group_to_canonical[gname]
        detected_counts[canon] = detected_counts.get(canon, 0) + 1

        start, end = m.start(), m.end()
        snippet_start = max(0, start - 20)
        snippet_end = min(len(text), end + 20)
        context_snippet = text[snippet_start:snippet_end].strip()

        occurrences.append({
            "word": m.group(0),
            "canonical": canon,
            "start": start,
            "end": end,
            "context": context_snippet
        })

    words = clean_text_words(text)
    total_words = len(words)
    total_fillers = len(occurrences)
    filler_ratio_percent = round((total_fillers / total_words * 100), 1) if total_words > 0 else 0.0

    if filler_ratio_percent <= 1.5:
        rating = "Excellent"
        rating_color = "success"
        message = "Extremely clean speech delivery with minimal filler words."
    elif filler_ratio_percent <= 3.5:
        rating = "Good"
        rating_color = "info"
        message = "Healthy speech pattern. Minor fillers that do not distract the listener."
    elif filler_ratio_percent <= 6.0:
        rating = "Moderate"
        rating_color = "warning"
        message = "Noticeable filler words detected. Try replacing fillers with intentional silence."
    else:
        rating = "High Fillers"
        rating_color = "danger"
        message = "Frequent filler words impacting message authority and clarity."

    detected_fillers_list = sorted(list(detected_counts.keys()))
    unmatched_fillers_list = [f for f in normalized_fillers if f not in detected_counts]

    diagnostics = {
        "detected_fillers": detected_fillers_list,
        "unmatched_fillers": unmatched_fillers_list,
        "occurrences_count": total_fillers,
        "total_words_analyzed": total_words,
        "vocabulary_size": len(normalized_fillers),
        "checked_fillers": normalized_fillers,
        "detection_rule": "Word-boundary regex match (\\b...\\b) with case-insensitivity. Substrings inside words are excluded.",
        "note": f"Found {total_fillers} filler occurrence(s) across {len(detected_counts)} distinct filler term(s)."
    }

    return {
        "total_fillers": total_fillers,
        "filler_ratio_percent": filler_ratio_percent,
        "rating": rating,
        "rating_color": rating_color,
        "message": message,
        "breakdown": detected_counts,
        "checked_fillers": normalized_fillers,
        "occurrences": occurrences,
        "diagnostics": diagnostics
    }


def analyze_repetitions(text: str) -> Dict[str, Any]:
    """
    Detects immediate consecutive repeated words (e.g. 'I I', 'the the')
    and frequently overused non-stop words.
    """
    words = clean_text_words(text)
    
    # 1. Consecutive identical words
    consecutive_repeats = []
    for i in range(len(words) - 1):
        if words[i] == words[i + 1] and len(words[i]) > 1:
            consecutive_repeats.append(words[i])

    consecutive_counts = dict(Counter(consecutive_repeats))

    # 2. General overused content words (not in stop words list)
    content_words = [w for w in words if w not in COMMON_STOP_WORDS and len(w) > 2]
    content_counts = Counter(content_words)
    
    # Words spoken 3 or more times (or > 2% of speech)
    threshold = 3 if len(words) > 50 else 2
    frequent_content_words = {
        word: count for word, count in content_counts.items() if count >= threshold
    }
    # Sort descending
    frequent_content_words = dict(
        sorted(frequent_content_words.items(), key=lambda item: item[1], reverse=True)[:8]
    )

    return {
        "consecutive_repeats_count": len(consecutive_repeats),
        "consecutive_repeats": consecutive_counts,
        "frequent_words": frequent_content_words,
        "total_unique_words": len(set(words)),
        "vocabulary_diversity_ratio": round(len(set(words)) / len(words), 2) if words else 0.0
    }


def analyze_pauses(segments: List[Dict[str, Any]], pause_threshold: float = DEFAULT_PAUSE_THRESHOLD_SEC) -> Dict[str, Any]:
    """
    Estimates pauses, silent intervals, and conversational rhythm from Whisper segments.
    """
    if not segments or len(segments) <= 1:
        return {
            "pause_count": 0,
            "total_pause_duration_sec": 0.0,
            "avg_pause_duration_sec": 0.0,
            "long_pauses_count": 0,
            "pause_percentage": 0.0,
            "flow_rating": "Inconclusive",
            "message": "Speech clip is too short to measure pause intervals reliably."
        }

    pauses = []
    for i in range(len(segments) - 1):
        current_end = segments[i].get("end", 0.0)
        next_start = segments[i + 1].get("start", 0.0)
        gap = round(next_start - current_end, 2)
        if gap >= pause_threshold:
            pauses.append(gap)

    total_pause_sec = round(sum(pauses), 2)
    pause_count = len(pauses)
    avg_pause_sec = round(total_pause_sec / pause_count, 2) if pause_count > 0 else 0.0
    long_pauses = [p for p in pauses if p >= 1.5]

    total_speech_span = segments[-1].get("end", 0.0) - segments[0].get("start", 0.0)
    pause_percentage = round((total_pause_sec / total_speech_span * 100), 1) if total_speech_span > 0 else 0.0

    if pause_count == 0:
        flow_rating = "Continuous"
        flow_color = "warning"
        message = "Very few natural pauses detected. Remember to breathe and pause between points."
    elif avg_pause_sec > 2.0 or len(long_pauses) > 4:
        flow_rating = "Fragmented"
        flow_color = "warning"
        message = "Extended silent gaps detected. Practice bridging ideas smoothly."
    else:
        flow_rating = "Natural Rhythm"
        flow_color = "success"
        message = "Balanced pacing with well-distributed natural pauses."

    return {
        "pause_count": pause_count,
        "total_pause_duration_sec": total_pause_sec,
        "avg_pause_duration_sec": avg_pause_sec,
        "long_pauses_count": len(long_pauses),
        "pause_percentage": pause_percentage,
        "flow_rating": flow_rating,
        "flow_color": flow_color,
        "message": message
    }


def compute_overall_score(pacing: Dict[str, Any], fillers: Dict[str, Any], pauses: Dict[str, Any], repetitions: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes an objective, measurable 0-100 communication performance score.
    """
    # 1. Pacing score (30 points)
    wpm = pacing.get("wpm", 0)
    if 130 <= wpm <= 165:
        pacing_score = 30
    elif 115 <= wpm < 130 or 165 < wpm <= 180:
        pacing_score = 25
    elif 95 <= wpm < 115 or 180 < wpm <= 200:
        pacing_score = 18
    elif wpm > 0:
        pacing_score = 10
    else:
        pacing_score = 15

    # 2. Filler word score (30 points)
    ratio = fillers.get("filler_ratio_percent", 0.0)
    if ratio <= 1.0:
        filler_score = 30
    elif ratio <= 2.5:
        filler_score = 26
    elif ratio <= 4.0:
        filler_score = 20
    elif ratio <= 6.5:
        filler_score = 14
    else:
        filler_score = max(5, 30 - int(ratio * 3))

    # 3. Flow & pause rhythm score (20 points)
    flow_rating = pauses.get("flow_rating", "")
    if flow_rating == "Natural Rhythm":
        flow_score = 20
    elif flow_rating == "Continuous":
        flow_score = 14
    elif flow_rating == "Fragmented":
        flow_score = 12
    else:
        flow_score = 15

    # 4. Vocabulary & repetition score (20 points)
    repeats_count = repetitions.get("consecutive_repeats_count", 0)
    diversity = repetitions.get("vocabulary_diversity_ratio", 0.5)
    vocab_score = 20
    if repeats_count > 3:
        vocab_score -= 6
    elif repeats_count > 0:
        vocab_score -= 3
    if diversity < 0.4:
        vocab_score -= 4

    vocab_score = max(8, vocab_score)

    total_score = min(100, max(20, pacing_score + filler_score + flow_score + vocab_score))

    if total_score >= 88:
        level = "Mastery"
        badge = "Exceptional Speaker"
        color = "success"
    elif total_score >= 75:
        level = "Proficient"
        badge = "Clear Communicator"
        color = "info"
    elif total_score >= 60:
        level = "Competent"
        badge = "Promising Delivery"
        color = "warning"
    else:
        level = "Developing"
        badge = "Needs Polish"
        color = "danger"

    return {
        "score": total_score,
        "level": level,
        "badge": badge,
        "color": color,
        "subscores": {
            "pacing": pacing_score,
            "fillers": filler_score,
            "flow": flow_score,
            "vocabulary": vocab_score
        }
    }


def analyze_speech(
    transcript: str,
    duration_sec: float,
    segments: List[Dict[str, Any]],
    custom_fillers: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Master speech analysis orchestrator.
    Combines WPM, fillers, repetitions, pauses, and overall score into a comprehensive report.
    """
    words = clean_text_words(transcript)
    word_count = len(words)

    pacing_data = analyze_pacing(word_count, duration_sec)
    filler_data = analyze_filler_words(transcript, custom_fillers)
    repetition_data = analyze_repetitions(transcript)
    pause_data = analyze_pauses(segments)
    score_data = compute_overall_score(pacing_data, filler_data, pause_data, repetition_data)

    return {
        "word_count": word_count,
        "duration_seconds": round(duration_sec, 2),
        "duration_formatted": f"{int(duration_sec // 60)}m {int(duration_sec % 60)}s" if duration_sec >= 60 else f"{round(duration_sec, 1)}s",
        "pacing": pacing_data,
        "fillers": filler_data,
        "repetitions": repetition_data,
        "pauses": pause_data,
        "score": score_data
    }
