# -*- coding: utf-8 -*-
"""
Tests for Sewa Setu fixes.

Each test is designed to FAIL against the original (buggy) code and PASS
after the corresponding fix is applied.

Run: pytest tests/test_fixes.py -v
"""

import os
import sys
import importlib
import pytest

# Allow importing app from the app directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))


# ---------------------------------------------------------------------------
# FIX 1: sanitize() truncates Indian-language names
# ---------------------------------------------------------------------------

class TestFix1_NameTruncation:
    """sanitize() must preserve full Indian-language names, not truncate at 20 bytes."""

    def test_hindi_name_preserved(self):
        """A Hindi name like 'राम प्रसाद शर्मा' is 16 chars but 48 UTF-8 bytes.
        The old sanitize() truncated to 20 bytes, destroying the name.
        The fix must increase the default limit so real names are preserved."""
        from app import sanitize
        hindi_name = "राम प्रसाद शर्मा"
        # Call with NO explicit maxlen — exposes the default=20 bug
        result = sanitize(hindi_name)
        assert result == hindi_name, (
            f"Hindi name was corrupted: expected '{hindi_name}', got '{result}'"
        )

    def test_assamese_name_preserved(self):
        """An Assamese name should be preserved fully."""
        from app import sanitize
        name = "প্ৰমিলা দেৱী"
        result = sanitize(name)
        assert result == name, (
            f"Assamese name was corrupted: expected '{name}', got '{result}'"
        )

    def test_english_name_preserved(self):
        """English names should still work fine."""
        from app import sanitize
        name = "Runu Dutta"
        result = sanitize(name)
        assert result == name

    def test_name_limited_by_characters_not_bytes(self):
        """Names should be limited by character count, not byte count."""
        from app import sanitize
        # A 50-char Hindi string is 150 UTF-8 bytes; it should NOT be truncated
        name = "क" * 50  # 50 chars, 150 bytes
        result = sanitize(name)
        assert len(result) == 50, (
            f"Name was truncated to {len(result)} chars — likely byte-truncated"
        )


# ---------------------------------------------------------------------------
# FIX 2: SQL injection in /status/reset
# ---------------------------------------------------------------------------

class TestFix2_SQLInjection:
    """The /status/reset endpoint must use parameterized queries."""

    def test_reset_uses_parameterized_queries(self):
        """Verify the source code does NOT use string formatting for SQL in reset_password."""
        import inspect
        from app import reset_password
        source = inspect.getsource(reset_password)
        # The old code used: "SELECT mobile FROM portal_users WHERE mobile = '%s'" % mobile
        assert "% mobile" not in source, (
            "reset_password still uses string formatting for SQL — SQL injection vulnerability!"
        )
        assert "'%s'" not in source, (
            "reset_password uses '%s' string interpolation instead of parameterized queries"
        )


# ---------------------------------------------------------------------------
# FIX 3: IDOR — any logged-in user can view any application
# ---------------------------------------------------------------------------

class TestFix3_IDOR:
    """view_application must verify the logged-in user owns the requested application."""

    def test_view_application_checks_ownership(self):
        """Verify the source code checks portal_mobile against the application's mobile."""
        import inspect
        from app import view_application
        source = inspect.getsource(view_application)
        assert "portal_mobile" in source, (
            "view_application does not check portal_mobile — IDOR vulnerability!"
        )


# ---------------------------------------------------------------------------
# FIX 4: Broken deemed-approval cron (wrong config path)
# ---------------------------------------------------------------------------

class TestFix4_BrokenCron:
    """The deemed_approval.py script must reference the correct config file."""

    def test_cron_script_references_correct_config(self):
        """The script should reference 'app.ini', not 'settings.ini'."""
        script_path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'scripts', 'deemed_approval.py'
        )
        with open(script_path, 'r') as f:
            content = f.read()
        assert "settings.ini" not in content, (
            "deemed_approval.py still references 'settings.ini' — cron is broken!"
        )
        assert "app.ini" in content, (
            "deemed_approval.py does not reference 'app.ini'"
        )


# ---------------------------------------------------------------------------
# FIX 5: Approve/Reject checks logged_in instead of admin
# ---------------------------------------------------------------------------

class TestFix5_AdminAuth:
    """admin_approve and admin_reject must check session['admin'], not just logged_in."""

    def test_approve_checks_admin(self):
        """admin_approve must check for admin session, not just logged_in."""
        import inspect
        from app import admin_approve
        source = inspect.getsource(admin_approve)
        assert '"admin"' in source or "'admin'" in source, (
            "admin_approve does not check for admin session — any citizen can approve!"
        )

    def test_reject_checks_admin(self):
        """admin_reject must check for admin session, not just logged_in."""
        import inspect
        from app import admin_reject
        source = inspect.getsource(admin_reject)
        assert '"admin"' in source or "'admin'" in source, (
            "admin_reject does not check for admin session — any citizen can reject!"
        )
