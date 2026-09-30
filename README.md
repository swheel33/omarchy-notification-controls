# Notification Controls

A replacement for Omarchy's built-in notifications plugin, providing Normal, History only, and Off delivery policies plus global Do Not Disturb. Runs inside the existing Omarchy shell; no second notification daemon and no patched Omarchy installation are required.

## Status

Working local plugin, verified in isolated graphical sessions against the installed Omarchy 4.0.4-1 and pristine upstream `quattro` at `8b4eae66`. Checks cover first-run loading, keyboard selection in the panel, Normal / History only / Off, DND, restart persistence, and browser-origin policy overrides. Panel and toast screenshots have been inspected. The plugin is enabled on this machine's regular desktop as well.

## Open settings

```bash
omarchy shell shell summon hotwheels.notification-controls
```

The manifest uses `omarchy.clonedFrom: omarchy.notifications`, so enabling it through Omarchy's plugin manager replaces the built-in service. Existing notification IPC calls and DND controls retain their targets.

On this machine, **Setup → Notifications** opens the panel through the user menu extension. `menu.json` contains that entry for merging into `~/.config/omarchy/extensions/omarchy-menu.jsonc`; preserve any existing entries when installing elsewhere.

## Source identity

- Native notifications use their `desktop-entry` identity, whether or not the application appears in the launcher.
- Senders without a desktop entry appear as separate **reported name** sources after their first notification. These are deliberately not guessed from potentially ambiguous launcher names.
- Browser website notifications use their origin. Newly observed origins inherit the sending browser's policy until explicitly configured; choosing Normal explicitly overrides a blocked browser.
- Installed web apps are discovered from desktop files. Standard Omarchy launchers, stock HEY and Zoom handlers, Chromium `--app` launchers, and explicit `OMARCHY_WEBAPP_ORIGIN` metadata are supported. No webapp installer changes are needed. Other custom handlers are still configurable when their website first sends a notification.
- Source names and policies remain available after hiding or removing a launcher. The catalog enriches the settings UI; delivery never waits for it.
- History-only delivery follows Omarchy's existing transient-notification behavior: ephemeral notifications are discarded rather than archived.

The plugin stores DND, modes, and observed source identities in `~/.local/state/omarchy/notification-controls.json`. It imports existing `notifications.json` preferences on first use. Notification bodies are not stored in this settings file; popup/history storage uses Omarchy's existing directories.

## Development and installation

This checkout's plugin ID is `hotwheels.notification-controls`. It began as a built-in clone and retains the supported `clonedFrom` replacement metadata. Copy the plugin runtime files (`manifest.json`, `NotificationService.qml`, `Panel.qml`, `NotificationLogic.js`, `catalog.py`, and `components/`) into `~/.config/omarchy/plugins/hotwheels.notification-controls/`, then enable it:

```bash
omarchy plugin validate ~/.config/omarchy/plugins/hotwheels.notification-controls
omarchy shell shell rescanPlugins
omarchy plugin enable hotwheels.notification-controls
omarchy shell notifications status
omarchy shell shell summon hotwheels.notification-controls
```

Run offline tests with `bash ./test`. Python 3 provides desktop-file discovery and URL/IDNA normalization; Node is needed only for tests. IPC uses the supported Quickshell `IpcHandler`, which works with both older shell clients and the newer socket client's fallback.

Run `bash tests/runtime.sh` for graphical verification in a disposable nested Hyprland with a private D-Bus session and temporary HOME. It does not unlock the real desktop or run another notification daemon on the real session bus. It requires Hyprland, Quickshell, `grim`, and `wtype`, saves screenshots and logs under `/tmp/opencode/notification-plugin-test.*`, and cleans up its own processes. Set `OMARCHY_TEST_PATH` to a pristine Omarchy checkout to test a different host version.

The shell can retain a `keepLoaded` service and cached QML across plugin rescans. After editing runtime files, restart the shell while unlocked; an IPC rescan alone is not proof that the edited code is active. Always target the intended `WAYLAND_DISPLAY` when multiple compositors are running.

To return to the built-in service while retaining the plugin and its preferences:

```bash
omarchy plugin disable hotwheels.notification-controls
```

## Maintenance

The notification service and card originate from Omarchy, incorporating upstream through `8b4eae66` and the controls from PR #7545. This plugin carries that implementation rather than intercepting another daemon. Future upstream fixes to notification delivery and rendering need to be incorporated here. Shared `qs.Commons` and `qs.Ui` components come from the installed shell.

Licensed under MIT; see `LICENSE`.
