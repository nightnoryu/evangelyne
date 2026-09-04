# Evangelyne

Dockerized deployment of [Hermes Agent](https://github.com/NousResearch/hermes-agent),
running as a persistent gateway via Docker Compose.

## Persona

`hermes/SOUL.md` is git-tracked and defines the agent's personality, tone, and
default language. Edit it to shape how the agent talks and behaves.

## Skills

Bundled skills are disabled by default. Custom skills live in `hermes/skills/`.

### Included and git-tracked skills

- `skill-authoring` - skill for writing new skills, [source](https://github.com/joshuadavidthomas/agent-skills)
- `obsidian` - working with Obsidian vault
- `mom-test` - "The Mom Test" interview, [source](https://github.com/wondelai/skills)
- `task-decomposition` - decomposing big goals into small milestones

## Prerequisites

- docker with docker-compose-plugin

## Installation

### 1. Clone

```bash
git clone https://github.com/nightnoryu/evangelyne hermes
cd hermes
```

### 2. Configure secrets

Secrets live in `hermes/.env` (git-ignored). Copy the template and fill it in:

```bash
cp hermes/.env.example hermes/.env
```

| Variable | Purpose |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Bot token from [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_ALLOWED_USERS` | Comma-separated Telegram user IDs allowed to talk to the bot, obtained from [@userinfobot](https://t.me/userinfobot) |
| `TELEGRAM_HOME_CHANNEL` | Default channel/chat ID for proactive messages |
| `OBSIDIAN_VAULT_PATH` | Vault path **inside the container** (`/opt/data/workspace/notes`) |

Only credentials go in `.env`. Everything else is set through `hermes setup`
(next step), never hand-edited.

### 3. Host-specific overrides (optional)

`compose.override.yml` is git-ignored and holds everything that varies per host:
UID/GID mapping, timezone, and volume mounts. Copy the template:

```bash
cp compose.override.example.yml compose.override.yml
```

### 4. Run the setup wizard

A fresh clone has no `hermes/config.yaml`. Generate it by running the
interactive wizard inside a throwaway container:

```bash
docker compose run --rm hermes setup
```

This walks through model/provider selection, credentials, and core settings,
writing `hermes/config.yaml` (git-ignored). Related one-off commands:

```bash
docker compose run --rm hermes model     # change model/provider later
docker compose run --rm hermes doctor    # health check
```

### 5. Start the gateway

```bash
docker compose up -d
```

Verify:

```bash
docker compose logs -f hermes
```

### 6. Next steps

1. In my setup I also configure YouTrack MCP for work - choose whichever MCPs
   are suitable for you.
2. Prompt the agent to ask you questions and fill your user profile
   (`hermes/memories/USER.md`, created at runtime, git-ignored). With this the
   agent will understand your preferences better.
3. If you're working with Obsidian, prompt the agent to set up `AGENTS.md` for
   your vault. This will improve agent's understanding of your vault structure.
