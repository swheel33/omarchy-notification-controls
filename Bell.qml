import QtQuick
import qs.Commons
import qs.Ui

BarWidget {
  id: root

  readonly property var host: bar ? bar.shell : null
  readonly property var notificationService: host ? host.serviceFor(moduleName) : null
  readonly property bool dnd: notificationService ? notificationService.doNotDisturb : false

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  function openSettings() {
    if (host) host.toggle(moduleName, "{}")
  }

  function toggleDnd() {
    if (notificationService) notificationService.setDoNotDisturb(!dnd)
  }

  BarIconButton {
    id: button
    bar: root.bar
    text: root.dnd ? "󰂛" : "󰂚"
    active: root.dnd
    tooltipText: "Notifications" + (root.dnd ? " — Do not disturb" : "") + "\nRight-click to toggle Do not disturb"
    activeFocusOnTab: true

    Accessible.role: Accessible.Button
    Accessible.name: "Notification settings"
    Accessible.description: root.dnd ? "Do not disturb is on" : "Do not disturb is off"
    Accessible.onPressAction: root.openSettings()
    Keys.onReturnPressed: root.openSettings()
    Keys.onSpacePressed: root.openSettings()

    onPressed: function(mouseButton) {
      if (mouseButton === Qt.RightButton) root.toggleDnd()
      else if (mouseButton === Qt.LeftButton) root.openSettings()
    }
  }
}
