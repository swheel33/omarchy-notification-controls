# Development

- Do not add automated tests or test harnesses to this repository. Verify changes directly in the running UI.
- The application launcher defines the settings list. Show one row per application; resolve helpers internally. Incoming senders and saved rules must not create extra rows.
- Keep visible native launchers separate. Attach hidden helpers only through unambiguous executable or window-class metadata; do not group by package or name prefix.
