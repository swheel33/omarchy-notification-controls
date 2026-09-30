# Notification Controls

A replacement for Omarchy's built-in notifications plugin, providing Normal, History only, and Off delivery policies plus global Do Not Disturb. Runs inside the existing Omarchy shell; no second notification daemon and no patched Omarchy installation are required.

## Status

Local development version. Automated checks cover independent source discovery, settings persistence, browser inheritance, and startup without the shell's application library. Live desktop verification is pending.

## Open settings

```bash
omarchy shell shell summon hotwheels.notifications
```

The manifest uses `omarchy.clonedFrom: omarchy.notifications`, so enabling it through Omarchy's plugin manager replaces the built-in service. Existing notification IPC calls and DND controls retain their targets.

## Source identity

- Native notifications use their `desktop-entry` identity, whether or not the application appears in the launcher.
- Senders without a desktop entry appear as separate **reported name** sources after their first notification. These are deliberately not guessed from potentially ambiguous launcher names.
- Browser website notifications use their origin. Newly observed origins inherit the sending browser's policy until explicitly configured; choosing Normal explicitly overrides a blocked browser.
- Installed web apps are discovered from desktop files. Standard Omarchy launchers, stock HEY and Zoom handlers, Chromium `--app` launchers, and explicit `OMARCHY_WEBAPP_ORIGIN` metadata are supported. No webapp installer changes are needed. Other custom handlers are still configurable when their website first sends a notification.
- Source names and policies remain available after hiding or removing a launcher. The catalog enriches the settings UI; delivery never waits for it.
- History-only delivery follows Omarchy's existing transient-notification behavior: ephemeral notifications are discarded rather than archived.

The plugin stores DND, modes, and observed source identities in `~/.local/state/omarchy/notification-controls.json`. It imports existing `notifications.json` preferences on first use. Notification bodies are not stored in this settings file; popup/history storage uses Omarchy's existing directories.

## Development and installation

This checkout's plugin ID is `hotwheels.notifications`. To prepare the supported replacement slot on this machine:

```bash
omarchy plugin clone omarchy.notifications
```

Copy the plugin runtime files (`manifest.json`, `Service.qml`, `Panel.qml`, `NotificationLogic.js`, `catalog.py`, and `components/`) into `~/.config/omarchy/plugins/hotwheels.notifications/`, then restart the shell while the desktop is unlocked:

```bash
omarchy plugin validate ~/.config/omarchy/plugins/hotwheels.notifications
omarchy restart shell
omarchy shell notifications status
omarchy shell shell summon hotwheels.notifications
```

Run offline tests with `bash ./test`. Python 3 provides desktop-file discovery and URL/IDNA normalization; Node is needed only for tests. IPC uses the supported Quickshell `IpcHandler`, which works with both older shell clients and the newer socket client's fallback.

To return to the built-in service while retaining the plugin and its preferences:

```bash
omarchy plugin disable hotwheels.notifications
```

## Maintenance

The notification service and card originate from Omarchy, incorporating upstream through `8b4eae66` and the controls from PR #7545. This plugin carries that implementation rather than intercepting another daemon. Future upstream fixes to notification delivery and rendering need to be incorporated here. Shared `qs.Commons` and `qs.Ui` components come from the installed shell.

Licensed under MIT; see `LICENSE`.
