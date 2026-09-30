# Notification Controls

A replacement for Omarchy's built-in notifications plugin, providing Normal, History only, and Off delivery policies plus global Do Not Disturb. Runs inside the existing Omarchy shell; no second notification daemon and no patched Omarchy installation are required.

## Status

Working local plugin, enabled on this machine's regular desktop. The grouped application list has been inspected in the running UI on Omarchy 4.0.4-1. The original replacement daemon was also verified against pristine upstream `quattro` at `8b4eae66`.

## Open settings

```bash
omarchy shell shell summon hotwheels.notification-controls
```

The manifest uses `omarchy.clonedFrom: omarchy.notifications`, so enabling it through Omarchy's plugin manager replaces the built-in service. Existing notification IPC calls and DND controls retain their targets.

On this machine, **Setup → Notifications** opens the panel through the user menu extension. `menu.json` contains that entry for merging into `~/.config/omarchy/extensions/omarchy-menu.jsonc`; preserve any existing entries when installing elsewhere.

The bell before the system tray opens settings on left-click and toggles Do Not Disturb on right-click. It changes to a muted bell while DND is on. Omarchy appends new user menu entries after built-in entries; its menu extension format currently has no placement field.

## Application list

- Related native launchers and helpers share one application row and delivery setting. The catalog uses executable ownership, shared application names, and companion-package metadata; unrelated applications bundled in one package stay separate when their names differ.
- Only applications visible in Omarchy's launcher appear in settings, using a visible launcher's name and icon. The list uses Quickshell's application entries and Omarchy's own launcher exclusion rules. Incoming notifications never create rows.
- Native notifications resolve through their desktop ID. Senders without a desktop entry join an application only when their name uniquely matches its metadata. Unmatched senders follow normal notification behavior and DND.
- Installed web apps have their own settings, matched by website origin. Ordinary website notifications use their browser's setting. Standard Omarchy launchers, stock HEY and Zoom handlers, Chromium `--app` launchers, and explicit `OMARCHY_WEBAPP_ORIGIN` metadata are supported.
- Hidden helpers contribute identities to their parent app, without separate rows or helper descriptions. Hiding or removing an app removes it from the list; existing saved rules remain effective internally.
- Existing conflicting delivery preferences remain effective and show as different saved settings. Choosing a delivery mode replaces those preferences with one application-wide setting.
- History-only delivery follows Omarchy's existing transient-notification behavior: ephemeral notifications are discarded rather than archived.

The plugin stores DND, modes, and application grouping metadata in `~/.local/state/omarchy/notification-controls.json`. Saved identities load before routing starts, so policies also cover helpers before the desktop scan completes and after launcher removal. It imports existing `notifications.json` preferences on first use. Notification bodies are not stored in this settings file; popup/history storage uses Omarchy's existing directories.

## Development and installation

This checkout's plugin ID is `hotwheels.notification-controls`. It began as a built-in clone and retains the supported `clonedFrom` replacement metadata. Copy the plugin runtime files (`manifest.json`, `NotificationService.qml`, `Panel.qml`, `Bell.qml`, `NotificationLogic.js`, `catalog.py`, and `components/`) into `~/.config/omarchy/plugins/hotwheels.notification-controls/`, then place it on the bar:

```bash
omarchy plugin validate ~/.config/omarchy/plugins/hotwheels.notification-controls
omarchy shell shell rescanPlugins
omarchy bar put hotwheels.notification-controls --before omarchy.tray
omarchy shell notifications status
omarchy shell shell summon hotwheels.notification-controls
```

Python 3 provides desktop-file discovery and URL/IDNA normalization. IPC uses the supported Quickshell `IpcHandler`, which works with both older shell clients and the newer socket client's fallback.

When upgrading from the earlier service-only version, disable it once before `bar put` so Omarchy moves its configuration from `plugins[]` into the bar layout.

Verify changes directly in the running UI. This repository intentionally has no automated test suite.

The shell can retain a `keepLoaded` service and cached QML across plugin rescans. After editing runtime files, restart the shell while unlocked; an IPC rescan alone is not proof that the edited code is active. Always target the intended `WAYLAND_DISPLAY` when multiple compositors are running.

To return to the built-in service while retaining the plugin and its preferences:

```bash
omarchy plugin disable hotwheels.notification-controls
```

## Maintenance

The notification service and card originate from Omarchy, incorporating upstream through `8b4eae66` and the controls from PR #7545. This plugin carries that implementation rather than intercepting another daemon. Future upstream fixes to notification delivery and rendering need to be incorporated here. Shared `qs.Commons` and `qs.Ui` components come from the installed shell.

Licensed under MIT; see `LICENSE`.
