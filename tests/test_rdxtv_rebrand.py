"""Regression tests for RdxTv rebrand, Telegram templates, and Aurora UI theme."""
import os
import unittest
from pathlib import Path

for key, value in {
    "API_ID": "1", "API_HASH": "test", "BOT_TOKEN": "1:test", "ADMINS": "1",
    "LOG_CHANNEL": "-1001", "BIN_CHANNEL": "-1002",
    "DATABASE_URL": "mongodb://localhost:27017", "URL": "https://example.com",
    "UPI_ID": "test@upi", "UPI_NAME": "Test Merchant", "RECEIPT_SEND_USERNAME": "@admin",
}.items():
    os.environ.setdefault(key, value)

from Script import script
from web.brand import BRAND_CSS, BRAND_MARKUP
from web.web_assets import CSS, build_page, form_wrapper


class RdxTvRebrandTests(unittest.TestCase):
    def test_telegram_script_templates_format_cleanly_with_rdxtv_brand(self):
        start_msg = script.START_TXT.format("@User", "Good Evening")
        self.assertIn("RdxTv", start_msg)
        self.assertNotIn("Fast Finder", start_msg)

        status_msg = script.STATUS_TXT.format(*range(21))
        self.assertIn("RdxTv", status_msg)

        user_status_msg = script.USER_STATUS_TXT.format(*range(10))
        self.assertIn("RdxTv", user_status_msg)

        plan_msg = script.PLAN_TXT.format(10, "@admin")
        self.assertIn("RdxTv", plan_msg)

        help_msg = script.HELP_TXT.format("Admin")
        self.assertIn("RdxTv", help_msg)

        log_msg = script.LOG_INDEX_TXT.format("Movies", "-100123", "PRIMARY", 100, 95, 3, 1, 1)
        self.assertIn("RdxTv", log_msg)

        cap_msg = script.FILE_CAPTION.format(file_name="Sample.mkv")
        self.assertIn("RdxTv", cap_msg)

    def test_web_brand_and_aurora_theme_tokens(self):
        self.assertIn("Rdx", BRAND_MARKUP)
        self.assertIn("Tv", BRAND_MARKUP)
        self.assertIn("linear-gradient(135deg,#6366f1 0%,#06b6d4 100%)", BRAND_CSS)
        self.assertIn("--accent:#6366f1", CSS)
        self.assertIn("--accent-cyan:#06b6d4", CSS)
        self.assertNotIn("#e50914", CSS.lower())
        self.assertNotIn("nflxext.com", CSS.lower())

        guest_html = build_page("Sign In - RdxTv", form_wrapper("Sign In", "<form></form>"), "login-bg").text
        self.assertIn("<h2>Sign In</h2>", guest_html)
        self.assertNotIn("hub-banner", guest_html)
        self.assertIn('aria-label="RdxTv home"', guest_html)

    def test_miniapp_template_uses_rdxtv_brand_and_theme(self):
        miniapp = (Path(__file__).resolve().parents[1] / "web" / "miniapp.html").read_text(encoding="utf-8")
        self.assertIn("<title>RdxTv</title>", miniapp)
        self.assertIn('aria-label="RdxTv"', miniapp)
        self.assertNotIn("Fast Finder", miniapp)
        self.assertNotIn("#e50914", miniapp.lower())


if __name__ == "__main__":
    unittest.main()
