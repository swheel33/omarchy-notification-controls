#!/usr/bin/python3
"""Desktop metadata for notification sources, independent of the shell menu."""

import configparser
import ipaddress
import json
import locale
import os
from pathlib import Path
import shlex
from urllib.parse import urlsplit


def origin(url):
  try:
    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
      return ""
    host = parsed.hostname.encode("idna").decode("ascii").lower()
    if ":" in host:
      host = "[" + ipaddress.IPv6Address(host).compressed + "]"
    port = parsed.port
    if port and port != {"http": 80, "https": 443}[parsed.scheme]:
      host += ":" + str(port)
    return parsed.scheme + "://" + host
  except (ValueError, UnicodeError):
    return ""


def command_origin(command):
  handlers = {
    "omarchy-webapp-handler-hey": "https://app.hey.com",
    "omarchy-webapp-handler-zoom": "https://app.zoom.us",
  }
  for i, part in enumerate(command):
    if part.startswith("OMARCHY_WEBAPP_ORIGIN="):
      return origin(part.split("=", 1)[1])
    executable = Path(part).name
    if executable == "omarchy-launch-webapp" and i + 1 < len(command):
      return origin(command[i + 1])
    if executable in handlers:
      return handlers[executable]
    if part.startswith("--app="):
      return origin(part[6:])
  return ""


def applications():
  home = Path.home()
  data_home = Path(os.environ.get("XDG_DATA_HOME", home / ".local/share"))
  data_dirs = os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":")
  language = (locale.getlocale()[0] or "").split(".")[0]
  seen = set()
  entries = []
  for base in [data_home] + [Path(d) for d in data_dirs if d]:
    directory = base / "applications"
    for path in sorted(directory.rglob("*.desktop")):
      desktop_id = str(path.relative_to(directory)).replace("/", "-")[:-8]
      if desktop_id in seen:
        continue
      seen.add(desktop_id)
      config = configparser.ConfigParser(interpolation=None, strict=False)
      config.optionxform = str
      try:
        config.read(path, encoding="utf-8")
        entry = config["Desktop Entry"]
        if entry.get("Type") != "Application" or entry.get("Hidden", "").lower() == "true":
          continue
        command = shlex.split(entry.get("Exec", ""))
        web_origin = command_origin(command)
        # Feed canonical origins to the shared JS catalog without changing any
        # launchers or requiring the PR's webapp-install metadata changes.
        if web_origin:
          command = ["env", "OMARCHY_WEBAPP_ORIGIN=" + web_origin] + command
        label = entry.get("Name[" + language + "]", entry.get("Name[" + language.split("_")[0] + "]", entry.get("Name", desktop_id)))
        entries.append({"id": desktop_id, "label": label,
          "appIcon": entry.get("Icon", ""), "startupClass": entry.get("StartupWMClass", ""),
          "command": command})
      except (OSError, UnicodeError, configparser.Error, KeyError, ValueError):
        continue
  return entries


if __name__ == "__main__":
  print(json.dumps(applications()))
