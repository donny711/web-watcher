import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock, call
from io import StringIO

from watcher import (
    get_page_text, get_diff, print_diff, send_email,
    snap_path, load_snap, save_snap, check, parse_interval
)

SAMPLE_HTML = """<html><body>
  <nav>nav stuff</nav>
  <script>alert(1)</script>
  <p>Hello world</p>
  <footer>footer</footer>
</body></html>"""

TMP = tempfile.mkdtemp()


class TestGetPageText(unittest.TestCase):

    @patch("watcher.requests.get")
    def test_returns_text_on_200(self, mock_get):
        r = MagicMock()
        r.status_code = 200
        r.text = SAMPLE_HTML
        mock_get.return_value = r
        result = get_page_text("http://x.com")
        self.assertIn("Hello world", result)
        self.assertNotIn("alert", result)
        self.assertNotIn("nav stuff", result)

    @patch("watcher.requests.get")
    def test_returns_none_on_404(self, mock_get):
        r = MagicMock()
        r.status_code = 404
        mock_get.return_value = r
        self.assertIsNone(get_page_text("http://x.com"))

    @patch("watcher.requests.get")
    def test_returns_none_on_exception(self, mock_get):
        mock_get.side_effect = Exception("timeout")
        self.assertIsNone(get_page_text("http://x.com"))


class TestGetDiff(unittest.TestCase):

    def test_empty_when_same(self):
        self.assertEqual(get_diff("abc", "abc"), [])

    def test_detects_change(self):
        result = get_diff("hello\n", "world\n")
        combined = "\n".join(result)
        self.assertIn("hello", combined)
        self.assertIn("world", combined)

    def test_max_20_lines(self):
        old = "\n".join(f"line {i}" for i in range(60))
        new = "\n".join(f"changed {i}" for i in range(60))
        self.assertLessEqual(len(get_diff(old, new)), 21)


class TestSnapshots(unittest.TestCase):

    def test_snap_path_consistent(self):
        self.assertEqual(snap_path("http://a.com"), snap_path("http://a.com"))

    def test_load_returns_none_if_missing(self):
        import watcher
        original = watcher.SNAPSHOTS_DIR
        watcher.SNAPSHOTS_DIR = TMP
        # use a url that definitely has no snapshot
        self.assertIsNone(load_snap("http://definitely-not-saved-xyzxyz.com"))
        watcher.SNAPSHOTS_DIR = original

    def test_save_and_load(self):
        import watcher
        original = watcher.SNAPSHOTS_DIR
        watcher.SNAPSHOTS_DIR = TMP
        save_snap("http://test.com", "content here")
        self.assertEqual(load_snap("http://test.com"), "content here")
        watcher.SNAPSHOTS_DIR = original


class TestCheck(unittest.TestCase):

    @patch("watcher.get_page_text")
    @patch("watcher.print_diff")
    def test_first_visit_no_notification(self, mock_print, mock_fetch):
        import watcher
        mock_fetch.return_value = "page text"
        original = watcher.SNAPSHOTS_DIR
        watcher.SNAPSHOTS_DIR = TMP
        url = "http://first-visit-test.com"
        # remove snapshot if exists
        p = snap_path(url)
        if os.path.exists(p): os.remove(p)
        check(url)
        mock_print.assert_not_called()
        watcher.SNAPSHOTS_DIR = original

    @patch("watcher.get_page_text")
    @patch("watcher.print_diff")
    def test_change_triggers_notification(self, mock_print, mock_fetch):
        import watcher
        mock_fetch.return_value = "new content"
        original = watcher.SNAPSHOTS_DIR
        watcher.SNAPSHOTS_DIR = TMP
        url = "http://change-test.com"
        save_snap(url, "old content")
        check(url)
        mock_print.assert_called_once()
        watcher.SNAPSHOTS_DIR = original


class TestParseInterval(unittest.TestCase):

    def test_seconds(self): self.assertEqual(parse_interval("30s"), 30)
    def test_minutes(self): self.assertEqual(parse_interval("5m"), 300)
    def test_hours(self):   self.assertEqual(parse_interval("1h"), 3600)
    def test_plain(self):   self.assertEqual(parse_interval("60"), 60)
    def test_invalid(self):
        with self.assertRaises(ValueError):
            parse_interval("xyz")


if __name__ == "__main__":
    unittest.main()
