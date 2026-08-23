# Current sandbox action safety

The current sandbox catalog has one write tool, `raw_notes_create`. It is low-risk but not idempotent.

## Raw-note creation

Call `raw_notes_create` only after the user explicitly asks to create the note and the project and raw-data record are
unambiguous. Present the title and target before the call. After success, report the returned note ID. Do not retry a
timed-out or interrupted call because the server does not yet provide a persistent idempotency contract.

## Future actions

Mission control, rule-hit disposition, stream control, deletion, and physical-device actions are not available in the
current catalog. Do not improvise them through another transport. When those tools are released, irreversible or
physical actions must use the server-defined plan and confirmation contract.
