# pstack for Claude Code and Codex

This is Robert Goldman's unofficial adaptation of [Lauren Tan's pstack](https://github.com/cursor/plugins/tree/main/pstack), pinned initially to upstream commit `7022c81efb48d8b5eb15498ce6043a3bd74b694c`. Both packages ship all 47 skills, their resources, the existing Bun helpers, the logo, and the MIT license. Original Cursor source remains in `pstack/`.

## Install

Claude Code:

```bash
claude plugin marketplace add rgoldman73-dev/cursor-plugins
claude plugin install pstack@rgoldman-pstack
```

Codex:

```bash
codex plugin marketplace add rgoldman73-dev/cursor-plugins
codex plugin add pstack@rgoldman-pstack
```

Start a new session. In Claude Code, begin with `/pstack:setup-pstack` and `/pstack:poteto-mode`. In Codex, select the qualified `pstack:setup-pstack` and `pstack:poteto-mode` entries from the skill picker. Use qualified entries when another plugin provides `teach`, `tdd`, or a similarly named skill.

For local development, replace the GitHub shorthand in the marketplace-add commands with this checkout's absolute path. These commands add only this fork's pstack marketplace, not every original Cursor plugin in the repository.

## What changed

- Claude package: `ports/claude/pstack/.claude-plugin/plugin.json`, standard skill frontmatter, and two named Claude agents (`poteto-agent`, `comment-sicko`). Comment Sicko has review tools and no Write/Edit tools.
- Codex package: `ports/codex/pstack/.codex-plugin/plugin.json`, UI metadata and preserved explicit invocation policies. The two agent files are role prompts for available collaboration tools, not registered Codex agent types.
- Every skill loads a host adapter that maps tool names, optional dependencies, history access, scheduling, and authorization to the current host.
- Model defaults inherit the parent. Setup records confirmed host model choices in project `.pstack/models.json`, rather than writing Cursor global rules. Budget preference and model identity are separate.
- Project skills go to `.claude/skills/` or `.agents/skills/`. Worktree audits scan transcripts only when an explicitly scoped `PSTACK_TRANSCRIPTS_DIR` is supplied.

## Compatibility limits

The packages do not provision Cursor cloud agents, foreign-provider models, webhook services, optional `deslop`/control plugins, or schedulers. Where those features are unavailable, the host adapter requires serial execution, an equivalent installed driver, a saved handoff, or a clear unverified result. Same-model reviewers are never described as a multi-model panel. Conversation mode persists by instruction, not a Cursor `mode` registration.

`make-bot-ui` retains its external Cursor webhook integration and requires an existing approved endpoint. Benny templates remain in the original `pstack/automations/` tree and are not installed as Claude or Codex automations. Bugbot signature handling in the GitHub watcher remains intact because it recognizes external review events. Bun helpers still require Bun and, for GitHub operations, authenticated `gh`.

Workflows operate within the user's scope and host approvals. Installing the package grants no authority to merge, deploy, send messages, delete data, write memory, or read unrelated chats.

## Maintain and verify

Edit upstream `pstack/` content or `scripts/port-templates/`, then regenerate:

```bash
python3 scripts/build-pstack-ports.py
python3 scripts/build-pstack-ports.py --check
claude plugin validate .claude-plugin/marketplace.json --strict
claude plugin validate ports/claude/pstack --strict
```

The builder stages in a temporary directory, preserves executable modes, and emits real files, not symlinks. Check mode compares every output file and executable bit. Do not edit `ports/` directly. When updating upstream source, update the pinned commit in the builder and review the adapter mappings before rebuilding. `.github/workflows/check-pstack-ports.yml` gates generated-file drift.

Verified on 2026-10-02 with Claude Code 2.1.285 and Codex CLI 0.159.3: strict Claude manifest checks, temporary-profile installs in both hosts, installed resource integrity, and Codex app-server discovery of all 47 qualified skills without parsing errors. Native installation and discovery were tested; every operational playbook was not executed against a live project or external service. The author's MIT copyright is preserved in both packages.

Packaging references: [Claude plugin manifest](https://code.claude.com/docs/en/plugins-reference), [Claude marketplaces](https://code.claude.com/docs/en/plugin-marketplaces), [OpenAI plugin packaging](https://developers.openai.com/plugins/build/plugins).
