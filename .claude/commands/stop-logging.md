---
description: Stop automatic conversation logging for this project
---

# Stop Conversation Logging

Turn off the background logger started by `/start-logging` for this project. Existing logs in `conversation-log/` are kept. Use this when the project is finished, or any time you want logging to pause. Run `/start-logging` again to resume.

## Steps

1. Run:

```bash
python3 tools/conversation-log.py stop
```

2. Run `python3 tools/conversation-log.py status` and confirm it reports that logging is not running.

## Report

Tell the user, in plain words, that logging is stopped, that the existing logs were kept, and how to resume (`/start-logging`).
