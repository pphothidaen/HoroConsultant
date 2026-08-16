"""
project/tests/test_pwa_and_report_export.py
===========================================
Regression and unit tests for PWA Offline Engine & Consultation Report Exporter:
  1. Verify manifest.json schema, properties, and static/public sync.
  2. Verify sw.js Service Worker caching structure and static/public sync.
  3. Verify index.html PWA tags and Service Worker registration.
  4. Verify @media print styles in style.css.
  5. Verify exportConsultationReport() definition and DOM elements.
"""

import json
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class TestPWAEngine:
    """Test Progressive Web App (PWA) configuration and assets."""

    def test_manifest_json_validity_and_parity(self):
        static_manifest_path = PROJECT_ROOT / "project" / "static" / "manifest.json"
        public_manifest_path = PROJECT_ROOT / "public" / "manifest.json"

        assert static_manifest_path.exists(), "project/static/manifest.json must exist"
        assert public_manifest_path.exists(), "public/manifest.json must exist"

        static_data = json.loads(static_manifest_path.read_text(encoding="utf-8"))
        public_data = json.loads(public_manifest_path.read_text(encoding="utf-8"))

        assert static_data == public_data, "Static and Public manifest.json must be identical"

        # Check required PWA manifest fields
        assert "name" in static_data
        assert "short_name" in static_data
        assert static_data.get("display") == "standalone"
        assert static_data.get("start_url") == "/"
        assert "theme_color" in static_data
        assert "icons" in static_data and len(static_data["icons"]) >= 2

    def test_service_worker_structure_and_parity(self):
        static_sw_path = PROJECT_ROOT / "project" / "static" / "sw.js"
        public_sw_path = PROJECT_ROOT / "public" / "sw.js"

        assert static_sw_path.exists(), "project/static/sw.js must exist"
        assert public_sw_path.exists(), "public/sw.js must exist"

        static_code = static_sw_path.read_text(encoding="utf-8")
        public_code = public_sw_path.read_text(encoding="utf-8")

        assert static_code == public_code, "Static and Public sw.js must be identical"

        assert "CACHE_NAME" in static_code
        assert "addEventListener('install'" in static_code
        assert "addEventListener('activate'" in static_code
        assert "addEventListener('fetch'" in static_code
        assert "caches.match" in static_code

    def test_index_html_pwa_integration(self):
        for subpath in ["project/static/index.html", "public/index.html"]:
            html_path = PROJECT_ROOT / subpath
            content = html_path.read_text(encoding="utf-8")

            assert 'rel="manifest"' in content, f"Missing manifest link in {subpath}"
            assert 'name="theme-color"' in content, f"Missing theme-color meta in {subpath}"
            assert "navigator.serviceWorker.register" in content, f"Missing SW registration in {subpath}"


class TestConsultationReportExporter:
    """Test Consultation Report Exporter print styles and DOM bindings."""

    def test_style_css_print_media_rules(self):
        for subpath in ["project/static/style.css", "public/style.css"]:
            css_path = PROJECT_ROOT / subpath
            css_content = css_path.read_text(encoding="utf-8")

            assert "@media print" in css_content, f"Missing @media print in {subpath}"
            assert "@page" in css_content, f"Missing @page definition in {subpath}"
            assert "consultation-report-header" in css_content, f"Missing consultation-report-header class in {subpath}"
            assert "break-inside: avoid" in css_content or "page-break-inside: avoid" in css_content

    def test_app_js_export_function_parity(self):
        for subpath in ["project/static/app.js", "public/app.js"]:
            js_path = PROJECT_ROOT / subpath
            js_content = js_path.read_text(encoding="utf-8")

            assert "exportConsultationReport" in js_content, f"Missing exportConsultationReport in {subpath}"
            assert "window.print()" in js_content, f"Missing window.print() call in {subpath}"
            assert "consultation-report-header" in js_content, f"Missing consultation-report-header reference in {subpath}"

    def test_index_html_has_export_button(self):
        for subpath in ["project/static/index.html", "public/index.html"]:
            html_path = PROJECT_ROOT / subpath
            content = html_path.read_text(encoding="utf-8")

            assert 'id="btn-export-report"' in content, f"Missing btn-export-report in {subpath}"
            assert 'id="consultation-report-header"' in content, f"Missing consultation-report-header in {subpath}"
            assert 'id="results-actions-bar"' in content, f"Missing results-actions-bar in {subpath}"
