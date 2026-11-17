---
description: Start automatic conversation logging for this project (one-time setup)
---

# Start Conversation Logging

Turn on the background logger that saves every conversation you have with your coding agent (Muse or Claude Code) in this project to `conversation-log/` at the project root. Run this **once per project**, near the beginning. You do not need to run it again at the start of each session; it keeps running, and restarts itself when you log in.

## Steps

1. Confirm `tools/conversation-log.py` exists in this project. If it does not, stop and tell the user.
2. Run:

```bash
python3 tools/conversation-log.py start
```

3. Run `python3 tools/conversation-log.py status` and confirm it reports that logging is running.
4. Confirm `conversation-log/` is listed in `.gitignore` (logs contain everything typed, including any secrets, and must not be committed). If it is missing, add it and say so.

## Report

Tell the user, in plain words:
- logging is running and where the logs are (`conversation-log/`)
- it records both Muse and Claude Code sessions for this project automatically
- to stop it, run `/stop-logging` (do this when the project is finished, because the logger otherwise keeps running in the background)
- if the command could not run (for example, a non-macOS system), what to run instead: `python3 tools/conversation-log.py watch` in a spare terminal, or `python3 tools/conversation-log.py once` for a one-time catch-up
