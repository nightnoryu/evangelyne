# Evangelyne

Evangelyne is a personal engineering assistant built on [Hermes Agent](https://github.com/NousResearch/hermes-agent).
It runs as a Docker Compose gateway, with a Russian-language assistant persona, reusable skills, scheduled jobs, and portable configuration.

> An AI colleague that remembers, thinks with you, and occasionally
> taps you on the shoulder when something deserves your attention.

## ✨ What’s included

- **Hermes gateway** managed by Docker Compose.
- **Assistant persona** in `hermes/SOUL.md`.
- **Skills** for YouTrack risk reviews, Obsidian inbox triage, task planning, customer interviews, and skill authoring.
- **Portable settings** for Hermes configuration and cron jobs in `hermes/persisted/`.

## 🚀 Set up

1. Create local configuration files:

   ```sh
   cp hermes/.env.example hermes/.env
   cp compose.override.example.yml compose.override.yml
   ```

2. Add your Telegram credentials and allowed user IDs to `hermes/.env`. Configure any required
   AI provider and MCP credentials in Hermes locally; secrets and provider settings are not committed.
3. Edit `compose.override.yml` for your user ID, timezone, and notes folder. The example mounts
   an Obsidian vault into the container.
4. Restore portable settings and start the gateway:

   ```sh
   docker compose run --rm --user "$(id -u):$(id -g)" --entrypoint python evangelyne-hermes /opt/data/persist.py apply
   docker compose up -d
   ```

## 🔄 Save settings

After changing Hermes settings or cron jobs, save the portable configuration and review it before committing:

```sh
docker compose run --rm --user "$(id -u):$(id -g)" --entrypoint python evangelyne-hermes /opt/data/persist.py save
git diff -- hermes/persisted
```

Run `apply` again to update existing jobs; it does not duplicate them. Restart a running gateway after applying changes.
Credentials, AI providers, user profiles, chat IDs, and cron run history remain local.

## 📜 License

Distributed under the MIT License. See [License](/LICENSE) for more information.
