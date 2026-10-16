import pytest
from backend.services.analyzer import analyze_filler_words
from backend.config import DEFAULT_FILLER_WORDS

def test_instruction_7_known_transcript():
    """
    Instruction 7:
    Verify that: 'Um, I think, uh, we should, you know, basically start now.'
    results in exactly 4 filler occurrences: 'Um', 'uh', 'you know', and 'basically'.
    """
    transcript = "Um, I think, uh, we should, you know, basically start now."
    res = analyze_filler_words(transcript)

    assert res["total_fillers"] == 4
    assert res["breakdown"]["um"] == 1
    assert res["breakdown"]["uh"] == 1
    assert res["breakdown"]["you know"] == 1
    assert res["breakdown"]["basically"] == 1

    matched_words = [o["word"] for o in res["occurrences"]]
    assert matched_words == ["Um", "uh", "you know", "basically"]


def test_case_insensitivity_variants():
    """
    Test uppercase, lowercase, and mixed-case variants of single and multi-word fillers.
    """
    transcript = "UM, um, Um, uM! UH, Uh. YOU KNOW, You Know, you know. I MEAN, i mean. SORT OF, sort of."
    res = analyze_filler_words(transcript)

    assert res["breakdown"]["um"] == 4
    assert res["breakdown"]["uh"] == 2
    assert res["breakdown"]["you know"] == 3
    assert res["breakdown"]["i mean"] == 2
    assert res["breakdown"]["sort of"] == 2
    assert res["total_fillers"] == 13


def test_repeated_fillers():
    """
    Test consecutive and repeated fillers in sequence.
    """
    transcript = "Um um um, uh uh. Basically basically, you know you know."
    res = analyze_filler_words(transcript)

    assert res["breakdown"]["um"] == 3
    assert res["breakdown"]["uh"] == 2
    assert res["breakdown"]["basically"] == 2
    assert res["breakdown"]["you know"] == 2
    assert res["total_fillers"] == 9


def test_punctuation_around_fillers():
    """
    Test fillers surrounded by various punctuation marks (commas, periods, question marks, brackets, dashes).
    """
    transcript = "Um! What, uh? We (you know), basically: did it; I mean... sort of—right?"
    res = analyze_filler_words(transcript)

    assert res["breakdown"]["um"] == 1
    assert res["breakdown"]["uh"] == 1
    assert res["breakdown"]["you know"] == 1
    assert res["breakdown"]["basically"] == 1
    assert res["breakdown"]["i mean"] == 1
    assert res["breakdown"]["sort of"] == 1
    assert res["breakdown"]["right"] == 1
    assert res["total_fillers"] == 7


def test_multiword_fillers_priority_and_boundaries():
    """
    Test that multi-word phrases are counted as single occurrences and do not fragment.
    """
    transcript = "You know, I mean, that is sort of to be honest a great idea."
    res = analyze_filler_words(transcript)

    assert res["breakdown"]["you know"] == 1
    assert res["breakdown"]["i mean"] == 1
    assert res["breakdown"]["sort of"] == 1
    assert res["breakdown"]["to be honest"] == 1
    assert res["total_fillers"] == 4


def test_substring_false_positives():
    """
    Instruction 6 & 3:
    Words containing filler-like substrings must NOT trigger false positive matches.
    e.g. 'summer' (um), 'umbrella' (um), 'understand' (er, um), 'other' (er), 'verb' (er),
    'dislike' (like), 'hum' (um), 'meaning' (i mean), 'brother' (er), 'basic' (basically), 'actual' (actually).
    """
    negative_corpus = (
        "Summer umbrella understand other her verb dislike likely hum drum plump "
        "brother father hero errand error humming basic actual literal meaning sort"
    )
    res = analyze_filler_words(negative_corpus)

    assert res["total_fillers"] == 0, f"Expected 0 fillers, but found: {res['breakdown']}"
    assert res["breakdown"] == {}
    assert len(res["occurrences"]) == 0


def test_empty_and_whitespace_transcripts():
    """
    Test that empty, null, or whitespace-only inputs return 0 fillers gracefully.
    """
    for empty_input in ["", "   ", "\n\t  \r\n"]:
        res = analyze_filler_words(empty_input)
        assert res["total_fillers"] == 0
        assert res["filler_ratio_percent"] == 0.0
        assert res["breakdown"] == {}
        assert res["occurrences"] == []


def test_transcripts_with_no_fillers():
    """
    Test speech transcripts with valid content but zero filler words.
    """
    clean_speech = "The annual engineering symposium was held on Tuesday morning in London."
    res = analyze_filler_words(clean_speech)

    assert res["total_fillers"] == 0
    assert res["filler_ratio_percent"] == 0.0
    assert res["breakdown"] == {}
    assert res["rating"] == "Excellent"


def test_custom_configurable_vocabulary():
    """
    Test passing a custom filler list overrides the default vocabulary cleanly.
    """
    transcript = "Um, I think, like, this is basically right, honestly."
    
    # Custom list only checking ['like', 'honestly']
    custom = ["like", "honestly"]
    res = analyze_filler_words(transcript, custom_fillers=custom)

    assert res["total_fillers"] == 2
    assert "like" in res["breakdown"]
    assert "honestly" in res["breakdown"]
    assert "um" not in res["breakdown"]
    assert "basically" not in res["breakdown"]


def test_required_vocabulary_is_present():
    """
    Verify that all vocabulary words explicitly specified by the user are supported by default:
    'um', 'uh', 'erm', 'er', 'hmm', 'basically', 'actually', 'literally', 'you know', 'I mean', 'sort of'
    """
    required_words = [
        "um", "uh", "erm", "er", "hmm", "basically", "actually",
        "literally", "you know", "i mean", "sort of"
    ]
    for word in required_words:
        assert word in DEFAULT_FILLER_WORDS, f"Required word '{word}' missing from DEFAULT_FILLER_WORDS"

    # Test sentence containing all 11 required words
    sentence = (
        "Um, uh, erm, er, hmm, basically, actually, literally, you know, I mean, sort of."
    )
    res = analyze_filler_words(sentence)
    assert res["total_fillers"] == 11
    for word in required_words:
        assert res["breakdown"].get(word, 0) == 1, f"Expected 1 for '{word}', got {res['breakdown'].get(word)}"


def test_diagnostics_information():
    """
    Instruction 5:
    Verify that diagnostics are returned, identifying detected fillers, unmatched fillers, and occurrence details.
    """
    transcript = "Um, I think basically we should start."
    res = analyze_filler_words(transcript)

    assert "diagnostics" in res
    diag = res["diagnostics"]
    assert "detected_fillers" in diag
    assert "unmatched_fillers" in diag
    assert "detection_rule" in diag
    assert "um" in diag["detected_fillers"]
    assert "basically" in diag["detected_fillers"]
    assert "uh" in diag["unmatched_fillers"]
    assert len(res["occurrences"]) == 2
