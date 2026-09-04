---
name: obsidian
description: Read, search, create, and edit notes in the Obsidian vault.
required_environment_variables:
  - OBSIDIAN_VAULT_PATH
---

# Obsidian Vault

Use this skill for filesystem-first Obsidian vault work: reading notes, listing notes, searching note files, creating notes, appending content, and adding wikilinks.

## Vault path

Use a known or resolved vault path before calling file tools.

The documented vault-path convention is the `OBSIDIAN_VAULT_PATH` environment variable, for example from `${HERMES_HOME:-~/.hermes}/.env`. If it is unset, use `~/Documents/Obsidian Vault`.

File tools do not expand shell variables. Do not pass paths containing `$OBSIDIAN_VAULT_PATH` to `read_file`, `write_file`, `patch`, or `search_files`; resolve the vault path first and pass a concrete absolute path. Vault paths may contain spaces, which is another reason to prefer file tools over shell commands.

If the vault path is unknown, `terminal` is acceptable for resolving `OBSIDIAN_VAULT_PATH` or checking whether the fallback path exists. Once the path is known, switch back to file tools.

## Vault rules (AGENTS.md)

Before modifying notes, load the vault-level rules from `<vault_path>/AGENTS.md`. It contains:

- Folder structure and naming conventions (e.g., `000 Inbox`, `100 Проекты`, `200 Развитие`)
- Content rules for TODOs, monthly evaluations, project notes
- Agent behavior: when to ask, when to create, what not to touch

Do not create top-level folders, move notes between folders, or delete notes without explicit user permission — even if AGENTS.md is missing, follow these defaults.

## Read a note

Use `read_file` with the resolved absolute path to the note. Prefer this over `cat` because it provides line numbers and pagination.

## List notes

Use `search_files` with `target: "files"` and the resolved vault path. Prefer this over `find` or `ls`.

- To list all markdown notes, use `pattern: "*.md"` under the vault path.
- To list a subfolder, search under that subfolder's absolute path.

## Search

Use `search_files` for both filename and content searches. Prefer this over `grep`, `find`, or `ls`.

- For filenames, use `search_files` with `target: "files"` and a filename `pattern`.
- For note contents, use `search_files` with `target: "content"`, the content regex as `pattern`, and `file_glob: "*.md"` when you want to restrict matches to markdown notes.

## Create a note

Use `write_file` with the resolved absolute path and the full markdown content. Prefer this over shell heredocs or `echo` because it avoids shell quoting issues and returns structured results.

## Append to a note

Always use a two-step file-tool workflow:

1. **Read** the target note with `read_file` to see its current content.
2. **Edit** using one of these approaches (pick based on the situation):

   - **`patch` (preferred):** Find a stable anchor — the last heading, a trailing blank line, or the final paragraph — and replace it with the anchor plus the new content. This is safe and preserves everything else.
   - **`write_file`:** Use only when the note is small or the changes are so extensive that rewriting the whole file is cleaner than a fragile patch.
   - **`terminal` with `echo >> file`:** Last resort when the note has no stable anchor and is too large to rewrite. Use only with absolute paths and careful quoting.

## Targeted edits

Use `patch` for focused note changes when the current content gives you stable context. Prefer this over shell text rewriting.

## Wikilinks

Obsidian links notes with `[[Note Name]]` syntax. When creating notes, use these to link related content.
