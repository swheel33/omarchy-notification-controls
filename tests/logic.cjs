const assert = require('node:assert/strict')
const fs = require('node:fs')
const vm = require('node:vm')
const logic = require('../NotificationLogic.js')

const native = { app: 'Slack', desktopEntry: 'com.slack.Slack', source: '' }
const nativeKey = logic.sourceKeyFor(native)
assert.equal(nativeKey, 'desktop:com.slack.slack')
assert.equal(logic.sourceMode({ [nativeKey]: 'off' }, nativeKey), 'off')

// Removing or hiding a launcher must neither deactivate a policy nor make it
// impossible to select in the settings UI.
const catalog = logic.buildApplicationCatalog([
  { id: 'com.slack.Slack', label: 'Slack', command: ['slack'] }
]).applications
const modes = { [nativeKey]: 'off' }
assert.equal(logic.sourceList(catalog, {}, modes).length, 1)
const orphan = logic.sourceList([], {}, modes)
assert.equal(orphan[0].key, nativeKey)
assert.equal(logic.sourceMode(modes, orphan[0].key), 'off')

// A sender without a desktop entry remains an independently controllable
// source; a launcher-name collision must not misattribute it to another app.
const nameless = logic.observedSource({ app: 'Build monitor', desktopEntry: '' })
assert.equal(nameless.key, 'name:build%20monitor')
assert.match(nameless.label, /reported name/)
assert.equal(logic.sourceList([], { [nameless.key]: nameless }, {}).length, 1)

const web = logic.observedSource({ app: 'Chromium', desktopEntry: 'chromium', source: 'https://example.com' })
assert.equal(web.key, 'origin:https%3A%2F%2Fexample.com')
assert.equal(web.fallbackKey, 'desktop:chromium')
assert.equal(logic.sourceMode({ 'desktop:chromium': 'off' }, web.key, web.fallbackKey), 'off')
assert.equal(logic.sourceMode({ 'desktop:chromium': 'off', [web.key]: 'normal' }, web.key, web.fallbackKey), 'normal')
assert.equal(logic.sourceMode({ [web.key]: 'history' }, web.key, web.fallbackKey), 'history')

// Settings round-trip preserves explicit Normal (which overrides a browser's
// policy), named senders, website identities, and browser inheritance.
const settings = logic.parseSettings(JSON.stringify({ version: 4, dnd: true,
  modes: { [web.key]: 'normal', [nameless.key]: 'off' },
  sources: { [web.key]: web, [nameless.key]: nameless } }))
assert.equal(settings.dnd, true)
assert.equal(settings.modes[web.key], 'normal')
assert.equal(settings.sources[web.key].fallbackKey, 'desktop:chromium')
assert.equal(settings.sources[nameless.key].label, nameless.label)
assert.deepEqual(logic.normalizedSources({ fake: web }), {})

assert.equal(logic.deliveryTarget('off', false, true, false), 'drop')
assert.equal(logic.deliveryTarget('history', false, false, false), 'history')
assert.equal(logic.deliveryTarget('normal', true, false, false), 'history')
assert.equal(logic.deliveryTarget('normal', true, true, true), 'popup')

// Exercise actual service methods under the third-party facade (no appLibrary)
// before the asynchronous desktop catalog completes.
const qml = fs.readFileSync(require.resolve('../NotificationService.qml'), 'utf8')
const names = ['applicationMode', 'applicationForKey', 'applicationKeyFor',
  'handleNotification', 'drainPendingNotifications', 'setApplicationMode']
const functions = names.map(name => {
  const match = qml.match(new RegExp('  function ' + name + '\\([^]*?^  \\}', 'm'))
  assert.ok(match, name)
  return match[0]
}).join('\n')
const routed = []
const context = { NotificationLogic: logic, Qt: { callLater: fn => fn() },
  settingsLoaded: false, settingsWritable: true, catalogLoaded: false,
  shell: { appLibrary: null }, applicationKeys: {}, observedSources: {},
  applicationModes: {}, pendingNotifications: [],
  scheduleSettingsSave() {},
  processNotification(n) { routed.push(context.applicationMode(context.applicationKeyFor(n))) } }
context.service = context
Object.defineProperty(context, 'routingReady', { get() { return this.settingsLoaded } })
vm.createContext(context)
vm.runInContext(functions, context)
const notification = { ...native, tracked: false, closed: { connect() {} } }
context.handleNotification(notification)
assert.equal(routed.length, 0)
context.applicationModes = modes
context.settingsLoaded = true
context.drainPendingNotifications()
assert.deepEqual(routed, ['off'])
assert.equal(context.pendingNotifications.length, 0)
assert.equal(context.catalogLoaded, false)
assert.equal(context.setApplicationMode(nativeKey, 'normal'), true)
assert.equal(context.applicationMode(nativeKey), 'normal')
context.handleNotification(notification)
assert.deepEqual(routed, ['off', 'normal'])
console.log('Notification identity, persistence, inheritance, and clone startup checks passed.')
