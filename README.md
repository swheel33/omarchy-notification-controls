# Notification Controls

Per-application notification settings for Omarchy. Choose an app from your launcher and decide how its notifications reach you.

This experimental plugin replaces Omarchy's built-in notification service and runs inside the existing Quickshell desktop.

## Usage

Click the bell in the bar to open settings. Right-click it to toggle Do Not Disturb. A muted bell indicates DND is on; hovering shows no tooltip.

Each app has three delivery options:

| Setting | Behavior |
| --- | --- |
| Normal | Show popups and retain notification history. |
| History only | Save notifications without showing popups. |
| Off | Discard new notifications from the app. |

Global DND silences normal popups while retaining history. Omarchy's existing DND exceptions and transient-notification behavior still apply.

You can also open settings from the terminal:

```bash
omarchy shell shell summon hotwheels.notification-controls
```

## Which apps appear?

The application launcher defines the list. Each visible native launcher gets its own name, icon, and setting. Hidden helpers attach to an app only when executable or window-class metadata identifies a clear parent.

Installed web apps have their own settings, matched by website origin. Launchers for the same origin share a setting. Ordinary website notifications use the browser's setting.

Incoming notifications never add rows. Unrecognized senders follow the default notification behavior and DND. Matching depends on the identity supplied by the sending application; an ambiguous sender name is not guessed.

## Install from this checkout

Requires Omarchy with its Quickshell desktop and Python 3. Run these commands from the repository directory:

```bash
plugin="$HOME/.config/omarchy/plugins/hotwheels.notification-controls"
mkdir -p "$plugin"
cp manifest.json NotificationService.qml NotificationLogic.js Panel.qml Bell.qml catalog.py "$plugin/"
cp -r components "$plugin/"
omarchy plugin validate "$plugin"
omarchy shell shell rescanPlugins
omarchy bar put hotwheels.notification-controls --before omarchy.tray
omarchy restart shell
```

The plugin's replacement metadata disables the built-in notification service when enabled. Restart the shell while the desktop is unlocked.

For a **Setup → Notifications** menu entry, merge the entry in `menu.json` into `~/.config/omarchy/extensions/omarchy-menu.jsonc`, preserving any existing entries.

To return to the built-in notification service:

```bash
omarchy plugin disable hotwheels.notification-controls
```

## Storage and development

Preferences and saved application identities live in `~/.local/state/omarchy/notification-controls.json`. Notification history and popup storage use Omarchy's existing notification directories. Removing an app from the launcher removes its settings row; saved rules remain effective internally.

After changing installed plugin code, restart the shell to clear cached QML. Verify changes directly in the running UI; this repository has no automated test suite.

The plugin carries a copy of Omarchy's notification daemon and card implementation. Upstream fixes to those components need to be incorporated here. Shared UI components come from the installed Omarchy shell.

## License

MIT. See [LICENSE](LICENSE).
