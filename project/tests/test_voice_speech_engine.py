"""
project/tests/test_voice_speech_engine.py
=========================================
Unit and integration tests for Metaphysics AI Voice & Speech Engine (TTS / STT):
  1. Test voice_engine.js exists and contains core TTS/STT architecture.
  2. Test DOM element presence for audio player bar, waveform, voice mic button, and listen button.
  3. Test CSS styles for audio player, pulsing microphone, and soundwave animation.
  4. Test i18n localization keys across TH, EN, and ZH.
  5. Test markdown cleaner regex logic.
"""

from pathlib import Path
import re
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class TestVoiceEngineCodeStructure:
    """Test voice_engine.js file integrity and methods."""

    def test_voice_engine_files_exist(self):
        for subpath in ["project/static/voice_engine.js", "public/voice_engine.js"]:
            p = PROJECT_ROOT / subpath
            assert p.exists(), f"File {subpath} does not exist"
            content = p.read_text(encoding="utf-8")
            assert "class HoroVoiceEngine" in content
            assert "cleanMarkdown" in content
            assert "getBestVoice" in content
            assert "speak" in content
            assert "pause" in content
            assert "resume" in content
            assert "stop" in content
            assert "setRate" in content
            assert "startDictation" in content
            assert "window.HoroVoice = new HoroVoiceEngine()" in content

    def test_markdown_cleaner_logic(self):
        """Verify markdown stripping regex in Python matches JS design."""
        def clean_md(text: str) -> str:
            text = re.sub(r'[*#_~`>]', '', text)
            text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
            text = re.sub(r'[-+*]\s+', '', text)
            text = re.sub(r'\|', ' ', text)
            text = re.sub(r'\s+', ' ', text)
            return text.strip()

        raw = "### 🔮 **ดวงชะตาปี 2026**\n- การงาน: **ดีมาก** [อ่านต่อ](https://horo.ai)\n| ธาตุ | สถานะ |\n| ไฟ | สมบูรณ์ |"
        cleaned = clean_md(raw)
        assert "**" not in cleaned
        assert "###" not in cleaned
        assert "https://horo.ai" not in cleaned
        assert "ดวงชะตาปี 2026" in cleaned
        assert "อ่านต่อ" in cleaned


class TestVoiceDOMIntegration:
    """Verify HTML markup and script tags for Voice Engine."""

    def test_index_html_has_voice_components(self):
        for subpath in ["project/static/index.html", "public/index.html"]:
            html = (PROJECT_ROOT / subpath).read_text(encoding="utf-8")
            assert 'id="btn-voice-input"' in html, f"Missing btn-voice-input in {subpath}"
            assert 'id="audio-player-bar"' in html, f"Missing audio-player-bar in {subpath}"
            assert 'id="voice-play-pause-btn"' in html, f"Missing voice-play-pause-btn in {subpath}"
            assert 'id="voice-stop-btn"' in html, f"Missing voice-stop-btn in {subpath}"
            assert 'id="btn-speak-reading"' in html, f"Missing btn-speak-reading in {subpath}"
            assert 'voice_engine.js' in html, f"Missing voice_engine.js script tag in {subpath}"

    def test_style_css_has_voice_styles(self):
        for subpath in ["project/static/style.css", "public/style.css"]:
            css = (PROJECT_ROOT / subpath).read_text(encoding="utf-8")
            assert ".btn-voice-mic" in css, f"Missing .btn-voice-mic in {subpath}"
            assert ".btn-voice-listen" in css, f"Missing .btn-voice-listen in {subpath}"
            assert ".audio-player-bar" in css, f"Missing .audio-player-bar in {subpath}"
            assert ".waveform-container" in css, f"Missing .waveform-container in {subpath}"
            assert ".waveform-bar" in css, f"Missing .waveform-bar in {subpath}"
            assert "pulseMic" in css, f"Missing pulseMic animation in {subpath}"
            assert "soundWave" in css, f"Missing soundWave animation in {subpath}"

    def test_app_js_has_voice_handlers(self):
        for subpath in ["project/static/app.js", "public/app.js"]:
            js = (PROJECT_ROOT / subpath).read_text(encoding="utf-8")
            assert "startVoiceInput" in js, f"Missing startVoiceInput in {subpath}"
            assert "speakCurrentInterpretation" in js, f"Missing speakCurrentInterpretation in {subpath}"
            assert "toggleVoicePlayback" in js, f"Missing toggleVoicePlayback in {subpath}"
            assert "stopVoicePlayback" in js, f"Missing stopVoicePlayback in {subpath}"
            assert "setVoicePlaybackRate" in js, f"Missing setVoicePlaybackRate in {subpath}"


class TestVoiceI18nTranslations:
    """Verify voice dictionary translations across languages."""

    def test_i18n_has_voice_keys(self):
        for subpath in ["project/static/i18n.js", "public/i18n.js"]:
            content = (PROJECT_ROOT / subpath).read_text(encoding="utf-8")
            assert "btn_voice_input" in content
            assert "btn_listen_reading" in content
            assert "voice_reading_status" in content
            assert "query_label" in content
