import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("catalog", Path(__file__).resolve().parents[1] / "catalog.py")
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)


class CatalogTest(unittest.TestCase):
  def test_origins(self):
    self.assertEqual(catalog.origin("https://user@BÜCHER.example:443/path"), "https://xn--bcher-kva.example")
    self.assertEqual(catalog.origin("http://[2001:db8::1]:80/path"), "http://[2001:db8::1]")
    self.assertEqual(catalog.origin("https://example.com:8443/path"), "https://example.com:8443")
    self.assertEqual(catalog.origin("https://example.com:invalid"), "")
    self.assertEqual(catalog.origin("file:///tmp/test"), "")

  def test_stock_handlers_without_pr_metadata(self):
    self.assertEqual(catalog.command_origin(["omarchy-webapp-handler-hey", "%u"]), "https://app.hey.com")
    self.assertEqual(catalog.command_origin(["omarchy-webapp-handler-zoom", "%u"]), "https://app.zoom.us")
    self.assertEqual(catalog.command_origin(["omarchy-launch-webapp", "https://bücher.example/path"]), "https://xn--bcher-kva.example")
    self.assertEqual(catalog.command_origin(["chromium", "--app=https://example.com/path"]), "https://example.com")

  def test_desktop_precedence_and_hidden_sources(self):
    with tempfile.TemporaryDirectory() as tmp:
      user, system = Path(tmp) / "user", Path(tmp) / "system"
      for root in [user, system]:
        (root / "applications").mkdir(parents=True)
      def write(root, name, extra):
        (root / "applications" / name).write_text("[Desktop Entry]\nType=Application\nName=Example\nExec=example\n" + extra)
      write(system, "background.desktop", "NoDisplay=true\n")
      write(system, "masked.desktop", "")
      write(user, "masked.desktop", "Hidden=true\n")
      (user / "applications" / "web.desktop").write_text('[Desktop Entry]\nType=Application\nName=Books\nExec=omarchy-launch-webapp "https://bücher.example/path"\n')
      with patch.dict(os.environ, {"XDG_DATA_HOME": str(user), "XDG_DATA_DIRS": str(system)}):
        entries = {entry["id"]: entry for entry in catalog.applications()}
      self.assertNotIn("background", entries)
      self.assertNotIn("masked", entries)
      self.assertIn("OMARCHY_WEBAPP_ORIGIN=https://xn--bcher-kva.example", entries["web"]["command"])


if __name__ == "__main__":
  unittest.main()
