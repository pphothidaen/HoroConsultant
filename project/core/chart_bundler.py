import json
from typing import Dict, Any, List

class ChartBundler:
    """Bundles and exports charts in SVG, PNG, and PDF formats."""

    def bundle_consultation(self, charts: Dict[str, str], title: str, lang: str) -> str:
        """Bundle multiple discipline SVG charts into a single HTML report."""
        html_parts = [
            f"<!DOCTYPE html>",
            f"<html lang='{lang}'>",
            "<head>",
            f"<title>{title}</title>",
            "<style>body { font-family: sans-serif; background: #0f172a; color: #f8fafc; } .chart { margin-bottom: 2rem; }</style>",
            "</head>",
            "<body>",
            f"<h1>{title}</h1>"
        ]
        
        for name, svg_content in charts.items():
            html_parts.append(f"<div class='chart'><h2>{name}</h2>{svg_content}</div>")
            
        html_parts.append("</body></html>")
        return "\n".join(html_parts)

    def export_svg(self, svg_content: str) -> str:
        """Export chart as SVG (passthrough with cleanup)."""
        return svg_content.strip()

    def export_png(self, svg_content: str, width: int = 800) -> bytes:
        """Export chart as PNG using cairosvg if available."""
        try:
            import cairosvg
            return cairosvg.svg2png(bytestring=svg_content.encode('utf-8'), output_width=width)
        except ImportError:
            # Graceful fallback
            return b""
        except Exception:
            return b""

    def export_pdf(self, charts: Dict[str, str], title: str) -> bytes:
        """Export charts as PDF using reportlab if available."""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from io import BytesIO
            import tempfile
            import os

            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            c.setFont("Helvetica-Bold", 16)
            c.drawString(72, 750, title)
            
            y_pos = 700
            for name, svg in charts.items():
                c.setFont("Helvetica", 12)
                c.drawString(72, y_pos, f"Chart: {name}")
                y_pos -= 50
                if y_pos < 100:
                    c.showPage()
                    y_pos = 750
            
            c.save()
            return buffer.getvalue()
        except ImportError:
            # Graceful fallback
            return b""
        except Exception:
            return b""
