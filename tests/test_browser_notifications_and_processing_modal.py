"""
Tests for Async Processing Modal and Web Browser Notification System.
Ensures static/public HTML, JS, and CSS parity for long-running process feedback,
background minimization, and native Web Notifications.
"""

from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent

class TestBrowserNotificationsAndProcessingModal:
    @pytest.fixture(autouse=True)
    def setup_files(self):
        self.index_static = (ROOT / "project" / "static" / "index.html").read_text(encoding="utf-8")
        self.index_public = (ROOT / "public" / "index.html").read_text(encoding="utf-8")
        self.app_static = (ROOT / "project" / "static" / "app.js").read_text(encoding="utf-8")
        self.app_public = (ROOT / "public" / "app.js").read_text(encoding="utf-8")
        self.css_static = (ROOT / "project" / "static" / "style.css").read_text(encoding="utf-8")
        self.css_public = (ROOT / "public" / "style.css").read_text(encoding="utf-8")

    def test_html_contains_async_process_modal_and_toast(self):
        for name, html in [("static", self.index_static), ("public", self.index_public)]:
            assert 'id="async-process-modal"' in html, f"{name} index.html missing #async-process-modal"
            assert 'id="toast-container"' in html, f"{name} index.html missing #toast-container"
            assert 'minimizeAsyncProcessModal' in html, f"{name} index.html missing minimize button"
            assert 'id="async-process-progress"' in html, f"{name} index.html missing progress element"

    def test_js_contains_notification_and_modal_functions(self):
        required_functions = [
            "requestNotificationPermission",
            "sendBrowserNotification",
            "showProcessingModal",
            "hideProcessingModal",
            "minimizeAsyncProcessModal",
            "playNotificationChime",
            "showInAppToast",
        ]
        for fn in required_functions:
            assert fn in self.app_static, f"project/static/app.js missing function: {fn}"
            assert fn in self.app_public, f"public/app.js missing function: {fn}"

    def test_css_contains_toast_and_modal_styling(self):
        required_classes = [
            ".toast-container",
            ".toast-notification",
            ".toast-slide-in",
        ]
        for cls in required_classes:
            assert cls in self.css_static, f"project/static/style.css missing {cls}"
            assert cls in self.css_public, f"public/style.css missing {cls}"
