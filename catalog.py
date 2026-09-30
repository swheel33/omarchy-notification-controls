#!/usr/bin/python3
"""Desktop metadata for notification sources, independent of the shell menu."""

import configparser
import ipaddress
import json
import locale
import os
from pathlib import Path
import shlex
import shutil
import subprocess
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


def executable(command):
  """Unwrap env assignments, but never identify an app as its interpreter."""
  parts = list(command)
  if parts and Path(parts[0]).name == "env":
    parts.pop(0)
    while parts and ("=" in parts[0] or parts[0] == "--"):
      parts.pop(0)
  if not parts or parts[0].startswith("-"):
    return "", ""
  name = Path(parts[0]).name
  # These programs dispatch other applications. Their package is not the app.
  dispatchers = {"sh", "bash", "dash", "zsh", "fish", "node", "ruby", "perl",
    "java", "wine", "wine64", "xdg-open", "xdg-terminal-exec", "gtk-launch", "gio"}
  if name in dispatchers or name.startswith(("python", "omarchy-launch-")):
    return "", ""
  if name in ("flatpak", "snap"):
    if len(parts) > 2 and parts[1] == "run":
      app = next((part for part in parts[2:] if not part.startswith("-")), "")
      if app:
        return name + ":" + app, ""
    return "", ""
  path = shutil.which(parts[0])
  return (str(Path(path).resolve()) if path else parts[0]), name


def package_owners(paths, database=Path("/var/lib/pacman/local")):
  """Read ownership in one pass instead of spawning pacman for every launcher."""
  wanted = {path.lstrip("/") for path in paths if path.startswith("/")}
  owners = {}
  if not wanted:
    return owners
  for package in database.glob("*/files"):
    try:
      matched = wanted.intersection(package.read_text().splitlines())
      if not matched:
        continue
      description = (package.parent / "desc").read_text().splitlines()
      name = description[description.index("%NAME%") + 1]
      for path in matched:
        owners["/" + path] = name
    except (OSError, ValueError, IndexError):
      continue
  return owners


def applications():
  home = Path.home()
  omarchy = Path(os.environ["OMARCHY_PATH"])
  desktops = ":".join(os.environ.get(key, "") for key in ("XDG_CURRENT_DESKTOP", "XDG_SESSION_DESKTOP", "DESKTOP_SESSION"))
  # The stock scanner can exit 1 when its final optional Nix directory is absent.
  hidden = set(subprocess.run([str(omarchy / "shell/services/hidden-entries.sh"), desktops], text=True, stdout=subprocess.PIPE).stdout.splitlines())
  hidden.update(line.strip().removesuffix(".desktop") for line in (omarchy / "default/omarchy/launcher.hides").read_text().splitlines())
  data_home = Path(os.environ.get("XDG_DATA_HOME", home / ".local/share"))
  data_dirs = os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":")
  language = (locale.getlocale()[0] or "").split(".")[0]
  seen = set()
  entries = []
  for base in [data_home] + [Path(d) for d in data_dirs if d] + [home / ".nix-profile/share"]:
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
          "command": command, "name": entry.get("Name", label),
          "visible": desktop_id not in hidden and entry.get("NoDisplay", "").lower() != "true"})
      except (OSError, UnicodeError, configparser.Error, KeyError, ValueError):
        continue
  commands = {entry["id"]: executable(entry["command"]) for entry in entries if not command_origin(entry["command"])}
  owners = package_owners([path for path, name in commands.values()])
  families = {}
  for entry in entries:
    path, name = commands.get(entry["id"], ("", ""))
    owner = owners.get(path, "")
    if owner and entry["visible"]:
      families.setdefault(owner, set()).add(entry["name"].split()[0].casefold())
  for entry in entries:
    path, name = commands.get(entry["id"], ("", ""))
    owner = owners.get(path, "")
    if owner and not entry["visible"] and owner not in families:
      # Companion packages such as fcitx5-qt6 can contain only helpers.
      parents = [package for package, names in families.items()
        if owner.startswith(package + "-") and names == {entry["name"].split()[0].casefold()}]
      if len(parents) == 1:
        owner = parents[0]
    # Omarchy ships unrelated app launchers; that shared package isn't an app.
    # A package can ship unrelated applications (for example Qt tools).
    # Use it as a family only when its visible launchers agree on a name.
    if owner.startswith("omarchy") or len(families.get(owner, set())) != 1:
      owner = ""
    entry["applicationId"] = ("package:" + owner if owner else "executable:" + path) if path else ""
    entry["executable"] = name
  return entries


if __name__ == "__main__":
  print(json.dumps(applications()))
