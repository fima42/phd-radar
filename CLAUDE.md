# phd-radar

For a radar run, read `instructions/manager.md` and follow it; it points to the rules and the stream instructions.
Scheduled runs never change `config/`, `instructions/` or `scripts/`. Never print or commit API keys.

Scheduled tasks run one stream each ("the academia / policy / society stream" in the prompt's first line). Where a prompt says `instructions/<stream>.md` or `<week>`, read the instruction file of that stream and use the current ISO week (`date +%G-W%V`, Europe/Amsterdam).
