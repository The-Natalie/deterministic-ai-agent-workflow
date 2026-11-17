---
description: Start the project's dev server(s) in separate Terminal windows and open the app in Chrome
---

# Start Dev Server

Start the app's development server(s) in their own Terminal window(s), outside this agent session, wait until the app responds, and open it in Chrome. The servers keep running until you close their windows (or press Ctrl+C in them). Use this whenever you want to see the project running; use `/init-project` only for one-time setup (installing dependencies, migrations).

macOS only. On any other system, print the commands and URL and let the user run them.

## 1. Find out how to start the app

Read the project's `AGENTS.md` (`## Commands`, and any access points or ports it lists).

Work out:

- each server to run: a name, the exact start command, and the folder it runs from (the project root unless stated)
- each server's port
- the URL to open in the browser (the frontend, or the app's main page)

If one command starts everything (for example `npm run dev` that runs backend and frontend together), that is one server. If the project lists separate backend and frontend commands, they are separate servers, but still ONE app: start them all and open the browser once.

**If the dev command, port, or URL is not documented, stop. Do not guess.** Report what is missing and what the project's config files suggest, and ask the user to confirm.

## 2. Skip servers that are already running

For each server's port, check whether something is already listening:

```bash
lsof -nP -iTCP:<port> -sTCP:LISTEN
```

If it is, do not start that server again. If all are running, skip to step 4.

## 3. Start each remaining server in its own Terminal window

Use one `osascript` call per server, running the command in the project root. Escape any double quotes in the command for AppleScript:

```bash
osascript <<'OSA'
tell application "Terminal"
  activate
  do script "cd '<absolute project root>' && <start command>"
end tell
OSA
```

Each server gets its own window so its log stays readable and it can be restarted on its own. The first time, macOS may ask to allow control of Terminal; tell the user to click Allow. If the call is blocked (for example by a sandbox), report the exact error and print the commands for the user to run by hand.

## 4. Wait, then open Chrome

Wait up to 60 seconds for the app to respond:

```bash
for i in $(seq 1 60); do curl -s -o /dev/null "<url>" && break; sleep 1; done
```

If it responds, open it once, in a new Chrome tab:

```bash
open -a "Google Chrome" "<url>" || open "<url>"
```

If it does not respond within 60 seconds, do not open the browser; tell the user to check the Terminal window(s) for errors.

## Report

Tell the user, briefly:

- which servers were started (or were already running) and their ports
- the URL opened in Chrome
- how to stop: close the Terminal window(s), or press Ctrl+C in each
- anything that failed, with the exact error
