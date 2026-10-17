# AbrarAssistant

AbrarAssistant is a Discord bot written in Python that turns a Discord channel into a command console for a local language model and a set of connected services. It reads every message in the channels it can see, asks a locally hosted Ollama model what to do, and then either replies with plain text or performs an action: searching the web, generating a voice note, creating a Google Docs/Sheets/Slides file, reading or writing a file, or describing an attached image. Messages beginning with `$` bypass the model entirely and run as shell commands on a Google Cloud Shell VM. A small React/xterm "activity frontend" and a FastAPI server round it out: the frontend is a terminal-style dashboard meant to be embedded as a Discord Activity, and the server handles the Google OAuth callback for linking a user's Google account. The problem it solves is having one chat interface, reachable from any device with Discord, that can both talk and act.

## Where it is used

In Abrar's setup this bot is the "assistant" member of a private Discord server. It is the quickest way to run a remote shell command from a phone, ask a question that a local model can answer, or kick off a longer task on an external agent swarm without opening a laptop. The same `.env` file is shared with the sibling project `discord-browser-vm`, which reuses the Discord application credentials.

## How it works

### Message flow

1. `main.py` logs in with `discord.py` (prefix `!`, message-content intent on) and registers two cogs on `on_ready`, then syncs slash commands.
2. Every incoming message goes through `on_message`:
   - If the text starts with `$`, the remainder is sent to `CloudShellService.execute_command` in a thread-pool executor and the result is edited into the original "running" message as a code block. The exchange is stored in memory as `Direct Shell: <cmd>`.
   - Otherwise the text is passed to `ai_router`, which builds a prompt containing the user's last five exchanges (from SQLite) plus a strict "action protocol" and sends it to Ollama (`llama3.2:3b`) with `ollama.chat`.
3. The model's reply is scanned with the regex `ACTION:\s*(\w+)\s*(.*)`. If it matches, the action type decides which service runs; otherwise the reply is posted verbatim.
4. The outcome (reply or action result) is written back to the per-user history table so the next prompt has context.

### Action protocol

| Action emitted by the model | What happens |
|---|---|
| `SEARCH [query]` | `SearchService` runs `remote_search.py` on the Cloud Shell VM via `gcloud cloud-shell ssh`, parses the JSON list it prints and posts up to three title/link/snippet results. If the model echoed the literal placeholder `[query]`, the text is just posted. |
| `SPEAK [text]` | `VoiceService` calls the ElevenLabs text-to-speech API (`eleven_multilingual_v2`) and uploads the resulting `speech.mp3`. The prompt tells the model to use this only when the user explicitly asks for audio. |
| `SPREADSHEET title \| data` / `PPT title \| content` | `GoogleWorkspaceService` creates an empty Sheets or Slides document with that title through a service account and posts its URL. The data/content part is accepted but not written into the document. |
| `WRITE_FILE name \| content` / `READ_FILE name` | `FileService` writes/reads files inside `data/`, using only the basename so paths cannot escape the folder. |
| `ANALYZE` | The first attachment is saved to `data/` and sent to a local Ollama model with the image attached; the description is posted. |

### Components

| File | Role |
|---|---|
| `main.py` | Bot entry point, event handlers, `ai_router`, action dispatch, `!ping`. |
| `cogs/oauth_cog.py` | `!login` command: builds a Google OAuth URL (scope `drive.file`, `state` = Discord user id) and posts it in an embed. |
| `cogs/swarm_cog.py` | At start-up scans an external agents directory for folders named `NN_name`, and registers one slash command per folder. Each command runs `run_swarm.py <task> <folder>` in that directory and posts stdout (as a file if longer than 1900 chars). |
| `oauth_server.py` | FastAPI app: serves `activity_frontend/dist` at `/`, `/callback` exchanges the Google authorization code for an access token and keeps it in an in-memory dict keyed by Discord user id, `/api/controller` is a stub that echoes the command it received. |
| `services/shell_service.py` | Remote shell on Google Cloud Shell. Tracks a remote working directory (`cd` is handled specially), refuses interactive programs (`vim`, `top`, ...), filters SSH noise from stderr, 5-minute timeout, and runs a background heartbeat (`gcloud cloud-shell ssh --command=true` every 45 s) so the VM is not shut down for inactivity. |
| `services/search_service.py` | Remote Google search through the Cloud Shell VM (see above). |
| `services/memory_service.py` | SQLite database `data/memory.db` with tables `conversation_history(user_id, message, response)` and `file_map`. |
| `services/google_service.py` | Google Docs/Sheets/Slides creation via a service-account JSON key, or via a user access token when one is passed. |
| `services/voice_service.py`, `services/image_service.py`, `services/pdf_service.py`, `services/file_service.py` | ElevenLabs TTS, Ollama image description, FPDF/PyPDF2 helpers (not wired to a command), sandboxed file I/O. |
| `activity_frontend/` | Vite + React 19 app ("Abrar AI OS"): a full-screen xterm.js terminal that POSTs each typed line to `/api/controller` and prints the returned message. Includes the Discord Embedded App SDK as a dependency. |
| `bot_only.py`, `manager.py` | Minimal debugging bot (logs messages, answers `!ping`) and a legacy two-process launcher. |
| `servers/*.py` | Empty placeholder modules for a planned gateway / hearing / brain / speech split. |

External services: Discord, a local Ollama server, Google Cloud Shell (through the `gcloud` CLI, already authenticated), Google Workspace APIs, ElevenLabs.

## Setup

Requirements: Python 3.10+, Node.js 18+, [Ollama](https://ollama.com) running locally with `llama3.2:3b` pulled (and an image-capable model if you want `ANALYZE`), the `gcloud` CLI logged in to an account with Cloud Shell, FFmpeg is not required.

```bash
cd ~/Workspace/AbrarAssistant
python3 -m venv venv && source venv/bin/activate
pip install discord.py python-dotenv ollama fastapi uvicorn requests \
            google-api-python-client google-auth elevenlabs fpdf PyPDF2

# frontend
cd activity_frontend && npm install && npm run build && cd ..
```

Create `.env` in the project root (the code loads it by absolute path, so keep it there):

```ini
DISCORD_BOT_TOKEN=your-bot-token
DISCORD_CLIENT_ID=000000000000000000
DISCORD_CLIENT_SECRET=your-client-secret
DISCORD_PUBLIC_KEY=your-public-key
ELEVENLABS_API_KEY=your-elevenlabs-key
ELEVENLABS_VOICE_ID=your-voice-id
GOOGLE_DOCS_API_KEY_PATH=~/secrets/service-account.json
GOOGLE_SPREADSHEETS_API_KEY_PATH=~/secrets/service-account.json
GOOGLE_SLIDES_API_KEY_PATH=~/secrets/service-account.json
GOOGLE_SHELL_API_KEY_PATH=~/secrets/service-account.json
GOOGLE_CLIENT_ID=your-oauth-client-id
GOOGLE_CLIENT_SECRET=your-oauth-client-secret
GOOGLE_REDIRECT_URI=https://example.com/callback
GOOGLE_CSE_ID=your-cse-id
GOOGLE_SEARCH_API_KEY=your-search-key
```

For remote search, copy `data/remote_search.py` to the home directory of your Cloud Shell VM (it needs `requests` and `beautifulsoup4` there). For the swarm commands, point `agents_dir` in `cogs/swarm_cog.py` at a directory containing numbered agent folders and a `run_swarm.py`.

## Usage

```bash
source venv/bin/activate
python main.py                         # the bot
uvicorn oauth_server:app --host 0.0.0.0 --port 8000   # OAuth callback + activity frontend
```

Example interactions in Discord:

```
$ ls -la                 -> runs on the Cloud Shell VM, output in a code block
$ cd projects            -> changes the remembered remote directory
What is a mutex?         -> plain-text answer from the local model
Search the latest Python release   -> model emits ACTION: SEARCH ..., top 3 results posted
Say "good morning" out loud        -> ACTION: SPEAK ..., an mp3 voice note is uploaded
Create a spreadsheet called Budget -> ACTION: SPREADSHEET ..., link to the new sheet
(attach an image) describe this    -> ACTION: ANALYZE, description of the image
!login                   -> embed with a "Sign in with Google" link
!ping                    -> Pong!
/<agent-name> task:"..." -> runs that agent folder's task through run_swarm.py
```

## Project structure

```
AbrarAssistant/
├── main.py                 # bot entry point and action dispatch
├── oauth_server.py         # FastAPI: Google OAuth callback, activity frontend, /api/controller stub
├── bot_only.py             # minimal debug bot
├── manager.py              # legacy multi-process launcher
├── cogs/
│   ├── oauth_cog.py        # !login
│   └── swarm_cog.py        # dynamic slash commands for external agent folders
├── services/
│   ├── shell_service.py    # Google Cloud Shell remote shell + keep-alive
│   ├── search_service.py   # remote Google search via Cloud Shell
│   ├── memory_service.py   # SQLite conversation history
│   ├── google_service.py   # Docs / Sheets / Slides creation
│   ├── voice_service.py    # ElevenLabs TTS
│   ├── image_service.py    # Ollama image description
│   ├── pdf_service.py      # FPDF / PyPDF2 helpers
│   └── file_service.py     # sandboxed read/write in data/
├── activity_frontend/      # Vite + React xterm dashboard (build output served by oauth_server)
│   ├── index.html
│   ├── vite.config.ts
│   └── src/{index.jsx, AIOSDashboard.jsx}
├── servers/                # empty placeholders
├── config/.env             # secondary env file (subset of keys)
└── data/                   # runtime files: memory.db, uploads, speech.mp3, remote_search.py
```

## Limitations and notes

- Several paths are absolute (`.env`, `data/`, `activity_frontend/dist`, the agents directory). Move the project and you must edit them.
- The bot responds to every message in every channel it can read; there is no allow-list of users or channels, and `$` gives anyone in the channel a shell on the Cloud Shell VM. Keep it in a private server.
- `oauth_server.py` only starts its web server when run as a script and then exits immediately because the thread is a daemon; run it with `uvicorn` as shown above. Tokens it collects are kept in memory and are not yet used by the bot's Google actions.
- `/api/controller` is a stub: the activity frontend terminal echoes commands back rather than executing them.
- The image analysis service logs "LLaVA" but is configured with `llama3.2:1b`; use a model that accepts images or the request will fail with "I had trouble reading that image."
- Spreadsheet and presentation actions create empty, titled documents; the content after `|` is ignored.
- Action detection is a plain regex on the model output, so a chatty model can trigger an action by accident, or echo the protocol text verbatim.
- `main_backup.py` and `manager.py` are earlier iterations kept for reference and are not needed to run the bot.
