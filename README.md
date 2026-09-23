# Evangelyne

Evangelyne is an opinionated engineering assistant built on [Hermes Agent](https://github.com/NousResearch/hermes-agent).

> An AI colleague that remembers, thinks with you, and occasionally
> taps you on the shoulder when something deserves your attention.

## Save and restore Hermes settings

The container stores live state in `hermes/`. The tracked `hermes/persisted/` files
hold portable configuration (including MCP) and cron job definitions. After
changing settings in Hermes, save them and review the diff before committing:

```sh
docker compose run --rm --user "$(id -u):$(id -g)" --entrypoint python evangelyne-hermes /opt/data/persist.py save
git diff -- hermes/persisted
```

On a new installation, set up `hermes/.env` from `hermes/.env.example` and
configure your AI provider locally. Then restore the tracked settings and start
the gateway:

```sh
docker compose run --rm --user "$(id -u):$(id -g)" --entrypoint python evangelyne-hermes /opt/data/persist.py apply
docker compose up -d
```

Run `apply` again to update existing jobs without duplicating them. Restart the
gateway after applying settings to a running installation. `USER.md`, secrets,
AI providers, chat IDs, and cron run history stay local and are never saved by
this workflow.
