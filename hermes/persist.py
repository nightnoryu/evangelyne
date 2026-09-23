#!/usr/bin/env python3
"""Save and restore portable Hermes settings. Run with the pinned Hermes image."""

import argparse
import copy
import json
import os
from pathlib import Path
import re
import tempfile

import yaml


HOME = Path(os.environ.get("HERMES_HOME", Path(__file__).resolve().parent))
SNAPSHOT = Path(__file__).resolve().parent / "persisted"
CONFIG_FILE = HOME / "config.yaml"
JOBS_FILE = HOME / "cron" / "jobs.json"

# These belong to the installation, not to the portable assistant definition.
LOCAL_CONFIG_KEYS = {
    "model", "custom_providers", "known_builtin_toolsets",
    "known_plugin_toolsets", "onboarding", "_config_version",
}
JOB_FIELDS = {
    "name", "prompt", "skills", "schedule", "enabled", "deliver",
    "enabled_toolsets", "context_from", "script", "no_agent",
    "monitor_script", "monitor_url", "workdir", "attach_to_session",
    "failure_deliver", "reasoning_effort",
}
PROVIDER_FIELDS = {
    "model", "provider", "model_provider", "base_url",
    "model_snapshot", "provider_snapshot",
}
SECRET_KEY = re.compile(r"(?:^key$|api[_-]?key|secret|password|token|authorization|cookie)$", re.I)
ENV_REF = re.compile(r"\$\{(?:env:)?[A-Za-z_][A-Za-z0-9_]*\}")


def atomic_write(path, content, mode=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        if mode is None:
            mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
        os.fchmod(fd, mode)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def read_config(path):
    data = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a YAML mapping")
    return data


def validate_config(data):
    forbidden = LOCAL_CONFIG_KEYS.intersection(data)
    if forbidden:
        raise ValueError(f"Local-only config keys in snapshot: {', '.join(sorted(forbidden))}")

    def walk(value, path=()):
        if isinstance(value, dict):
            for key, child in value.items():
                key = str(key)
                here = path + (key,)
                if key in PROVIDER_FIELDS and path[:1] != ("mcp_servers",):
                    raise ValueError(f"Provider setting in snapshot: {'.'.join(here)}")
                if SECRET_KEY.search(key) and child not in (None, ""):
                    if not isinstance(child, str) or not ENV_REF.search(child):
                        raise ValueError(f"Use an environment reference for {'.'.join(here)}")
                walk(child, here)
        elif isinstance(value, list):
            for item in value:
                walk(item, path)

    walk(data)


def portable_config(data):
    result = {key: copy.deepcopy(value) for key, value in data.items()
              if key not in LOCAL_CONFIG_KEYS}
    validate_config(result)
    return result


def portable_delivery(value, origin=None):
    if value == "origin":
        platform = (origin or {}).get("platform")
        if not platform or platform == "cli":
            return "local"
        return platform  # Home channel is selected from the local .env.
    if value and re.search(r":-?\d", value):
        raise ValueError("Concrete chat IDs cannot be saved; use a platform home channel")
    return value or "local"


def portable_job(job):
    spec = {key: copy.deepcopy(job[key]) for key in JOB_FIELDS if key in job and job[key] is not None}
    spec["schedule"] = job["schedule"].get("display") or job["schedule"].get("expr")
    spec["deliver"] = portable_delivery(job.get("deliver"), job.get("origin"))
    repeat = job.get("repeat")
    if isinstance(repeat, dict) and repeat.get("times") is not None:
        spec["repeat"] = repeat["times"]
    validate_job(spec)
    return spec


def validate_job(spec):
    if not isinstance(spec, dict) or not isinstance(spec.get("name"), str):
        raise ValueError("Each cron job needs a name")
    if set(spec) - JOB_FIELDS - {"repeat"}:
        raise ValueError(f"Unsupported fields in cron job {spec['name']}")
    if not isinstance(spec.get("schedule"), str) or not spec["schedule"]:
        raise ValueError(f"Cron job {spec['name']} needs a schedule")
    if spec.get("deliver") == "origin":
        raise ValueError("Use a platform home channel instead of origin")
    portable_delivery(spec.get("deliver"))
    if spec.get("failure_deliver"):
        portable_delivery(spec["failure_deliver"])


def read_jobs(path):
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["jobs"] if isinstance(data, dict) else data


def reject_local_secrets(*values):
    env_file = HOME / ".env"
    if not env_file.exists():
        return
    rendered = json.dumps(values, ensure_ascii=False)
    for line in env_file.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if separator and SECRET_KEY.search(key) and len(value) >= 8 and value in rendered:
            raise ValueError(f"Local secret {key} appears in the portable snapshot")


def save():
    config = portable_config(read_config(CONFIG_FILE))
    jobs = [portable_job(job) for job in read_jobs(JOBS_FILE)]
    names = [job["name"] for job in jobs]
    if len(names) != len(set(names)):
        raise ValueError("Cron job names must be unique for restore")
    reject_local_secrets(config, jobs)
    atomic_write(SNAPSHOT / "config.yaml", yaml.safe_dump(config, allow_unicode=True, sort_keys=False))
    atomic_write(SNAPSHOT / "jobs.json", json.dumps(jobs, ensure_ascii=False, indent=2) + "\n")
    print(f"Saved {len(jobs)} cron jobs and portable config to {SNAPSHOT}")


def merge(base, overlay):
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merge(base[key], value)
        else:
            base[key] = copy.deepcopy(value)
    return base


def apply():
    config = read_config(SNAPSHOT / "config.yaml")
    validate_config(config)
    jobs = json.loads((SNAPSHOT / "jobs.json").read_text(encoding="utf-8"))
    if not isinstance(jobs, list):
        raise ValueError("Persisted jobs must be a list")
    for job in jobs:
        validate_job(job)
    names = [job["name"] for job in jobs]
    if len(names) != len(set(names)):
        raise ValueError("Persisted cron job names must be unique")
    reject_local_secrets(config, jobs)

    live = read_config(CONFIG_FILE)
    merged = merge(live, config)
    if merged != read_config(CONFIG_FILE):
        atomic_write(CONFIG_FILE, yaml.safe_dump(merged, allow_unicode=True, sort_keys=False), mode=0o640)

    # Hermes creates IDs, calculates next runs, and locks its own cron database.
    from cron.jobs import create_job, load_jobs, pause_job, resume_job, update_job

    existing = {job["name"]: job for job in load_jobs()}
    for spec in jobs:
        name = spec["name"]
        current = existing.get(name)
        if current is None:
            fields = {key: value for key, value in spec.items() if key != "enabled"}
            fields["paused"] = not spec.get("enabled", True)
            create_job(**fields)
            print(f"Created cron job: {name}")
            continue
        current_spec = portable_job(current)
        changes = {key: value for key, value in spec.items()
                   if key not in {"enabled", "repeat"} and current_spec.get(key) != value}
        if "repeat" in spec and current_spec.get("repeat") != spec["repeat"]:
            changes["repeat"] = spec["repeat"]
        if changes:
            update_job(current["id"], changes)
        if spec.get("enabled", True) != current.get("enabled", True):
            (resume_job if spec.get("enabled", True) else pause_job)(current["id"])
        print(f"Reconciled cron job: {name}")
    print("Portable settings applied; local credentials and AI providers were preserved")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("save", "apply"))
    args = parser.parse_args()
    (save if args.action == "save" else apply)()
