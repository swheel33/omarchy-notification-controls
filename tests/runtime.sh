#!/bin/bash
set -euo pipefail
if [[ ${NOTIFICATION_TEST_PRIVATE_BUS:-} != "1" ]]; then
  exec env NOTIFICATION_TEST_PRIVATE_BUS=1 dbus-run-session -- bash "$0"
fi
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
work=$(mktemp -d /tmp/opencode/notification-plugin-test.XXXXXX)
printf 'Test artifacts: %s\n' "$work"
plugin_id=$(jq -r .id "$root/manifest.json")
plugin_dir="$work/home/.config/omarchy/plugins/$plugin_id"
mkdir -p "$plugin_dir" "$work/home/.local/state/omarchy"
cp "$root/"{NotificationService.qml,Panel.qml,NotificationLogic.js,manifest.json,catalog.py} "$plugin_dir/"
cp -a "$root/components" "$plugin_dir/"
export OMARCHY_PATH=${OMARCHY_TEST_PATH:-$OMARCHY_PATH}
export PATH="$OMARCHY_PATH/bin:$PATH"
omarchy-plugin-catalog | jq --arg id "$plugin_id" '{version:1, plugins:[{id:$id}], disabledPlugins:[.[] | select(.firstParty and .id != "omarchy.bar" and .id != "omarchy.menu") | .id],bar:{layout:{left:[],center:[],right:[]}}}' > "$work/home/.config/omarchy/shell.json"
mkdir -p "$work/home/.config/omarchy/extensions"
cp "$root/menu.json" "$work/home/.config/omarchy/extensions/omarchy-menu.jsonc"
cat > "$work/hyprland.lua" <<'LUA'
hl.monitor({ output = "", mode = "1280x800@60", position = "auto", scale = 1 })
hl.config({ misc = { disable_hyprland_logo = true, disable_splash_rendering = true }, animations = { enabled = false } })
LUA
export HOME="$work/home" XDG_CONFIG_HOME="$work/home/.config" XDG_STATE_HOME="$work/home/.local/state" XDG_DATA_HOME="$work/home/.local/share"
export WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-$(hyprctl instances -j | jq -r '.[0].wl_socket')} AQ_DRM_DEVICES=/dev/null
unset HYPRLAND_INSTANCE_SIGNATURE
Hyprland -c "$work/hyprland.lua" > "$work/compositor.log" 2>&1 &
compositor=$!
shell_pid=""
cleanup() {
  if [[ -n $shell_pid ]]; then kill "$shell_pid" 2>/dev/null || true; wait "$shell_pid" 2>/dev/null || true; fi
  kill "$compositor" 2>/dev/null || true
  wait "$compositor" 2>/dev/null || true
}
trap cleanup EXIT
for attempt in {1..100}; do
  HYPRLAND_INSTANCE_SIGNATURE=$(hyprctl instances -j | jq -r --argjson pid "$compositor" '.[] | select(.pid == $pid) | .instance')
  test_display=$(hyprctl instances -j | jq -r --argjson pid "$compositor" '.[] | select(.pid == $pid) | .wl_socket')
  if [[ -n $HYPRLAND_INSTANCE_SIGNATURE && -n $test_display && -S $XDG_RUNTIME_DIR/$test_display ]]; then break; fi
  kill -0 "$compositor" 2>/dev/null || { cat "$work/compositor.log"; exit 1; }
  sleep 0.1
done
[[ -n $HYPRLAND_INSTANCE_SIGNATURE && -n $test_display ]] || exit 1
export HYPRLAND_INSTANCE_SIGNATURE WAYLAND_DISPLAY="$test_display"
hyprctl output create headless NOTIFICATION-TEST
hyprctl eval 'hl.monitor({output="NOTIFICATION-TEST",mode="1280x800@60",position="0x0",scale=1})'
hyprctl seterror disable
hyprctl -j monitors > "$work/monitors.json"
start_shell() {
  QS_DISABLE_FILE_WATCHER=1 quickshell -n -p "$OMARCHY_PATH/shell" >> "$work/shell.log" 2>&1 &
  shell_pid=$!
  for attempt in {1..100}; do
    if omarchy-shell notifications status 2>/dev/null | jq -e '.ready and .catalogLoaded' >/dev/null 2>&1; then return; fi
    kill -0 "$shell_pid" 2>/dev/null || { cat "$work/shell.log"; return 1; }
    sleep 0.1
  done
  cat "$work/shell.log"
  omarchy-shell shell listPlugins || true
  omarchy-shell notifications status || true
  return 1
}
start_shell
hyprctl eval 'hl.monitor({output="WAYLAND-1",disabled=true})'
hyprctl dismissnotify -1
omarchy-shell notifications status
omarchy-notification-send --app-name 'Plugin Test' -u normal 'Plugin normal delivery' 'This popup is delivered by the replacement plugin.'
for attempt in {1..50}; do
  if omarchy-shell notifications status | jq -e '.popups == 1' >/dev/null; then break; fi
  sleep 0.1
done
omarchy-shell notifications status | jq -e '.popups == 1 and .pending == 0'
sleep 0.5
grim -o NOTIFICATION-TEST "$work/normal.png"
omarchy-shell notifications dismiss 'Plugin normal delivery'
omarchy-shell shell summon "$plugin_id"
sleep 0.5
wtype 'Plugin Test'
sleep 0.5
grim -o NOTIFICATION-TEST "$work/panel-normal.png"
for step in 1 2 3; do
  wtype -k Tab
  sleep 0.15
done
wtype -k space
sleep 0.5
grim -o NOTIFICATION-TEST "$work/panel-history.png"
omarchy-shell notifications listApplications > "$work/sources-after-keyboard.json"
jq -e 'any(.[]; .key == "name:plugin%20test" and .mode == "history")' "$work/sources-after-keyboard.json"
omarchy-shell shell hide "$plugin_id"
key='name:plugin%20test'
omarchy-shell notifications setApplicationMode "$key" history
omarchy-notification-send --app-name 'Plugin Test' -u normal 'Plugin history delivery' 'Saved without a popup.'
for attempt in {1..50}; do
  if grep -rl 'Plugin history delivery' "$HOME/.local/state/omarchy/notifications/history" >/dev/null; then break; fi
  sleep 0.1
done
grep -rl 'Plugin history delivery' "$HOME/.local/state/omarchy/notifications/history" > "$work/history-evidence.txt"
omarchy-shell notifications status | jq -e '.popups == 0'
omarchy-shell notifications setApplicationMode "$key" off
sleep 0.4
omarchy-notification-send --app-name 'Plugin Test' -u normal 'Plugin off delivery' 'Must not be stored.'
sleep 0.4
! grep -r 'Plugin off delivery' "$HOME/.local/state/omarchy/notifications/"
omarchy-shell notifications status | jq -e '.popups == 0 and .pending == 0'
kill "$shell_pid"
wait "$shell_pid" || true
shell_pid=""
start_shell
omarchy-shell notifications listApplications | jq -e --arg key "$key" 'any(.[]; .key == $key and .mode == "off")'
omarchy-notification-send --app-name 'Plugin Test' -u normal 'Plugin restart blocked' 'Must remain blocked after restart.'
sleep 0.4
omarchy-shell notifications status | jq -e '.popups == 0 and .pending == 0'
! grep -r 'Plugin restart blocked' "$HOME/.local/state/omarchy/notifications/"
omarchy-shell notifications setApplicationMode "$key" normal
omarchy-shell notifications setDnd true
omarchy-notification-send --app-name 'Plugin Test' -u normal 'Plugin DND delivery' 'History under global DND.'
sleep 0.5
grep -rl 'Plugin DND delivery' "$HOME/.local/state/omarchy/notifications/history"
omarchy-shell notifications status | jq -e '.popups == 0'
omarchy-shell notifications setDnd false
omarchy-notification-send --app-name Chromium -u normal 'Browser baseline' 'Browser-wide source.'
sleep 0.4
omarchy-shell notifications dismiss 'Browser baseline'
omarchy-shell notifications setApplicationMode 'name:chromium' off
omarchy-notification-send --app-name Chromium -u normal 'Website inherits blocked browser' '<a href="https://app.hey.com">app.hey.com</a> A website notification.'
sleep 0.4
omarchy-shell notifications status | jq -e '.popups == 0'
! grep -r 'Website inherits blocked browser' "$HOME/.local/state/omarchy/notifications/"
omarchy-shell notifications setApplicationMode 'origin:https%3A%2F%2Fapp.hey.com' normal
omarchy-notification-send --app-name Chromium -u normal 'Website explicit normal' '<a href="https://app.hey.com">app.hey.com</a> Website policy overrides browser.'
sleep 0.4
omarchy-shell notifications status | jq -e '.popups == 1'
omarchy-shell notifications dismiss 'Website explicit normal'
omarchy-shell notifications setApplicationMode 'origin:https%3A%2F%2Fapp.hey.com' history
omarchy-notification-send --app-name Chromium -u normal 'Website explicit history' '<a href="https://app.hey.com">app.hey.com</a> Saved without a popup.'
sleep 0.5
grep -rl 'Website explicit history' "$HOME/.local/state/omarchy/notifications/history"
omarchy-shell notifications status | jq -e '.popups == 0'
omarchy-shell shell summon omarchy.menu '{"menu":"setup"}'
sleep 0.6
grim -o NOTIFICATION-TEST "$work/setup-menu.png"
omarchy-shell shell hide omarchy.menu
if grep -E 'TypeError|ReferenceError|service plugin load failed' "$work/shell.log"; then exit 1; fi
printf 'Live routing, keyboard controls, persistence, DND, and browser checks passed.\n'
