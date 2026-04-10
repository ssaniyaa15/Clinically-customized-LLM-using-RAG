from chatbot.urgency_detector import detect_urgency


def test_detect_urgency_emergency() -> None:
    out = detect_urgency("I have chest pain and can't breathe", "Please call emergency services.")
    assert out.level == "emergency"
    assert out.notify_clinician is True


def test_detect_urgency_urgent() -> None:
    out = detect_urgency("I have high fever and confusion", "Seek immediate care.")
    assert out.level == "urgent"
    assert out.notify_clinician is False


def test_detect_urgency_watch() -> None:
    out = detect_urgency("I have mild fever and headache", "Monitor at home.")
    assert out.level == "watch"


def test_detect_urgency_normal() -> None:
    out = detect_urgency("Need refill timing info", "Follow your treatment plan.")
    assert out.level == "normal"
    assert out.notify_clinician is False

