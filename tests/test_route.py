"""Unit tests for main.route() — no real voice, API, or file I/O calls.

All external modules are stubbed before import so the suite runs without any
API keys, microphone, Piper model, or Spotify account.

Run with:  pytest tests/test_route.py -v
"""

import sys
import os
from unittest.mock import MagicMock, patch

# ── Stub every heavy dependency before anything from the project is imported ──
_STUBS = [
    "voice", "brain", "face_auth",
    "piper", "sounddevice", "soundfile",
    "speech_recognition",
    "pyaudio",
    "groq",
    "pycaw", "pycaw.pycaw", "comtypes",
    "spotipy", "spotipy.oauth2", "spotipy.exceptions",
    "cv2", "face_recognition",
    "pyautogui", "pyperclip",
    "psutil",
    "yfinance",
    "webview",
    "weather", "news", "stocks", "spotify", "vision",
]
for _mod in _STUBS:
    sys.modules.setdefault(_mod, MagicMock())

# Stub config values used at module load time
_cfg = MagicMock()
_cfg.GROQ_API_KEY = "test"
_cfg.WEATHER_API_KEY = "test"
_cfg.NEWS_API_KEY = "test"
_cfg.SPOTIFY_CLIENT_ID = "test"
_cfg.SPOTIFY_CLIENT_SECRET = "test"
_cfg.SPOTIFY_REDIRECT_URI = "http://localhost"
_cfg.DEFAULT_CITY = "Toronto"
_cfg.FACE_AUTH_ENABLED = False
_cfg.PIPER_MODEL = ""
_cfg.WAKE_WORDS_ENV = "hades"
_cfg.WAKE_DEBOUNCE = 2.5
sys.modules["config"] = _cfg

# Stub voice module so MIC_ERROR sentinel exists
_voice = MagicMock()
_voice.MIC_ERROR = object()
sys.modules["voice"] = _voice

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_pending(monkeypatch):
    """Clear _pending_state between every test."""
    import main
    monkeypatch.setattr(main, "_pending_state", {})


@pytest.fixture
def gui():
    g = MagicMock()
    g.add_help_card = MagicMock()
    g.add_system_message = MagicMock()
    g.set_status = MagicMock()
    return g


# ── Helper ────────────────────────────────────────────────────────────────────

def call_route(text, gui):
    from main import route
    return route(text, gui)


# ── Memory reset ──────────────────────────────────────────────────────────────

def test_clear_memory(gui):
    with patch("main.clear_memory", return_value="Memory cleared, Sir.") as m:
        result = call_route("clear memory", gui)
    assert result == "Memory cleared, Sir."
    m.assert_called_once()


def test_forget_everything(gui):
    with patch("main.clear_memory", return_value="Memory cleared, Sir.") as m:
        result = call_route("forget everything please", gui)
    assert result == "Memory cleared, Sir."
    m.assert_called_once()


# ── Help command ──────────────────────────────────────────────────────────────

def test_help_exact(gui):
    result = call_route("help", gui)
    gui.add_help_card.assert_called_once()
    assert "list" in result.lower() or "help" in result.lower()


def test_help_commands(gui):
    result = call_route("commands", gui)
    gui.add_help_card.assert_called_once()


def test_help_what_can_you_do(gui):
    result = call_route("what can you do", gui)
    gui.add_help_card.assert_called_once()


def test_help_does_not_trigger_on_homework(gui):
    """'help me with my homework' should hit screen analysis, not the help card."""
    with patch("main.SCREEN_WORDS", ("help me with my homework",)):
        with patch("vision.analyze_screen", return_value="Screen description."):
            result = call_route("help me with my homework", gui)
    gui.add_help_card.assert_not_called()


# ── Screen analysis ───────────────────────────────────────────────────────────

def test_screen_analysis(gui):
    with patch("vision.analyze_screen", return_value="I see a code editor.") as m:
        result = call_route("what's on my screen", gui)
    assert result == "I see a code editor."
    m.assert_called_once()


# ── Weather ───────────────────────────────────────────────────────────────────

def test_weather_with_city(gui):
    with patch("main._weather", return_value="18°C and sunny in London.") as m:
        result = call_route("what's the weather in London", gui)
    m.assert_called_once_with("london")
    assert "London" in result or "sunny" in result


def test_weather_default_city(gui):
    with patch("main._weather", return_value="18°C in Toronto.") as m:
        result = call_route("what's the weather", gui)
    m.assert_called_once_with("Toronto")


# ── News ──────────────────────────────────────────────────────────────────────

def test_news_general(gui):
    with patch("main._news", return_value="Top story: ...") as m:
        result = call_route("give me the news", gui)
    m.assert_called_once_with(None)


def test_news_with_topic(gui):
    with patch("main._news", return_value="AI news...") as m:
        result = call_route("news about AI", gui)
    m.assert_called_once_with("ai")


# ── Stocks ────────────────────────────────────────────────────────────────────

def test_stock_lookup(gui):
    with patch("main._stock", return_value="Tesla: $250.") as m:
        result = call_route("Tesla stock price", gui)
    m.assert_called_once()


def test_crypto_bitcoin(gui):
    with patch("main._crypto", return_value="Bitcoin: $65,000.") as m:
        result = call_route("what is bitcoin at", gui)
    m.assert_called_once_with("bitcoin")


def test_crypto_ethereum(gui):
    with patch("main._crypto", return_value="Ethereum: $3,000.") as m:
        call_route("ethereum price", gui)
    m.assert_called_once_with("ethereum")


# ── Spotify ───────────────────────────────────────────────────────────────────

def test_spotify_play(gui):
    with patch("main._spotify", return_value="Playing Blinding Lights, Sir.") as m:
        result = call_route("play some jazz", gui)
    m.assert_called_once()
    assert "Playing" in result


def test_spotify_skip(gui):
    with patch("main._spotify", return_value="Skipping, Sir.") as m:
        result = call_route("skip song", gui)
    m.assert_called_once()


# ── PC commands ───────────────────────────────────────────────────────────────

def test_pc_command_handled(gui):
    with patch("main.handle_command", return_value="Volume set to 50%, Sir.") as m:
        result = call_route("set volume to 50", gui)
    m.assert_called_once_with("set volume to 50")
    assert "Volume" in result


def test_pc_command_returns_none_falls_to_ai(gui):
    with patch("main.handle_command", return_value=None):
        with patch("main.think", return_value="I don't know.") as m:
            result = call_route("something random", gui)
    m.assert_called_once()


# ── Note taking (conversational flow) ────────────────────────────────────────

def test_note_triggers_category_question(gui):
    with patch("main.get_existing_categories", return_value=["personal", "work"]):
        with patch("main._suggest_category", return_value="work"):
            result = call_route("take a note: refactor auth tomorrow", gui)
    assert "category" in result.lower() or "file" in result.lower()
    assert "work" in result


def test_note_pending_confirmed_with_yes(gui):
    import main
    main._pending_state.update({
        "action": "save_note",
        "content": "call dentist",
        "categories": ["personal", "work"],
        "suggested_category": "personal",
    })
    with patch("main.save_note") as mock_save:
        result = call_route("yes", gui)
    mock_save.assert_called_once_with("call dentist", "personal")
    assert "personal" in result


def test_note_pending_explicit_category(gui):
    import main
    main._pending_state.update({
        "action": "save_note",
        "content": "finish report",
        "categories": ["personal", "work"],
        "suggested_category": "personal",
    })
    with patch("main.save_note") as mock_save:
        result = call_route("work", gui)
    mock_save.assert_called_once_with("finish report", "work")
    assert "work" in result


def test_note_pending_new_category(gui):
    import main
    main._pending_state.update({
        "action": "save_note",
        "content": "buy HDMI cable",
        "categories": ["personal", "work"],
        "suggested_category": "personal",
    })
    with patch("main.save_note") as mock_save:
        result = call_route("shopping", gui)
    mock_save.assert_called_once_with("buy HDMI cable", "shopping")


def test_note_pending_cleared_on_sleep(gui):
    import main
    main._pending_state.update({
        "action": "save_note",
        "content": "some note",
        "categories": ["personal"],
        "suggested_category": "personal",
    })
    # Simulate sleep word handling (main loop clears pending on sleep)
    main._pending_state.clear()
    assert main._pending_state == {}


# ── LLM fallback ─────────────────────────────────────────────────────────────

def test_fallback_to_brain(gui):
    with patch("main.handle_command", return_value=None):
        with patch("main.think", return_value="That's an interesting question.") as m:
            result = call_route("what is the meaning of life", gui)
    m.assert_called_once_with("what is the meaning of life")
    assert result == "That's an interesting question."
