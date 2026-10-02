#!/usr/bin/env python3
"""Build real, reproducible Claude and Codex packages from the upstream pstack tree."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'pstack'
TEMPLATES = ROOT / 'scripts/port-templates'
UPSTREAM = '7022c81efb48d8b5eb15498ce6043a3bd74b694c'

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n')

def adapt(text, host):
    skill_dir = '.claude/skills' if host == 'claude' else '.agents/skills'
    for old, new in [
        ('~/.cursor/rules/pstack-models.mdc', '.pstack/models.json'),
        ('pstack-models.mdc', '.pstack/models.json'),
        ('.cursor/skills', skill_dir),
        ('~/.cursor/plugins/', 'the host-discovered plugin installation directory'),
        ('~/.cursor/projects/*/', 'unrelated project transcript directories'),
        ("Cursor's built-in `create-skill`", 'the available skill-authoring helper'),
        ('each a Cursor cloud agent', 'each an isolated worker when the host supports one'),
        ("Cursor's built-in babysit skill", 'another similarly named host skill'),
        ('"Comment Sicko"', '"comment-sicko"'),
        ('`generalPurpose`', '`general-purpose`'),
        ("Cursor's built-in `create-skill` skill", 'the available skill-authoring helper'),
        ("Cursor's built-in for authoring SKILL.md files", 'a host-provided helper when available'),
        ('from the Cursor environment', 'from the current host'),
        ('Otherwise inspect the `mcps/` directory Cursor exposes for enabled MCP servers.',
         'Otherwise inspect the documented host configuration without exposing credentials.'),
        ('One Cursor cloud agent per PR', 'One isolated worker per PR, when available,'),
        ('the cloud agent\'s status in the Cursor dashboard', 'the worker status exposed by the current host'),
        ('After a Cursor restart', 'After a host restart'),
        ('a Cursor restart', 'a host restart'),
        ('Do not glob across `~/.cursor/projects/*/`.', 'Never search transcript stores across unrelated projects.'),
        ('~/Library/Application Support/Cursor', 'the host cache directory explicitly approved by the user'),
        ('.cursor/worktrees/myrepo/x', 'a host-managed worktree directory'),
        ('**Just do it.** Use any MCP tool. Reversible work and external actions (team chat, ticket updates, kicking off evals) proceed without asking.',
         '**Act within scope.** Proceed with authorized reversible work. External writes and messages require authorization from the user or host policy.'),
    ]:
        text = text.replace(old, new)
    text = re.sub(r'\b(?:claude-opus-[\w.-]+|gpt-5\.6-sol-[\w.-]+|grok-4\.7-[\w.-]+)\b', 'inherit-parent', text)
    text = re.sub(r'^Transcripts live at .*?Every line is one chat message\.$',
                  'Find project-scoped history through host chat tools or an explicitly supplied transcript path. If unavailable, report that gap and use the current handoff and git state.', text, flags=re.M)
    text = text.replace("If the Task tool rejects a slug, use the default and say so. If it rejects the default, use the closest valid slug of the same family from its error message.",
                        'If a configured model is unavailable, omit the override and report that the parent model was used.')
    text = text.replace('Cursor\'s `/loop` command', 'the host scheduling capability described in the host adapter')
    text = text.replace('from `cursor-team-kit`', 'from an optional control or cleanup plugin, if installed')
    text = text.replace('the `cursor-team-kit` plugin', 'an optional control or cleanup plugin, if installed')
    text = text.replace("`cursor-team-kit` publishes `control-cli` (CLIs and TUIs) and `control-ui` (browser / Electron / web UIs).",
                        'Use an available CLI/PTY or browser control harness appropriate to the surface.')
    # Installed agents use valid host names. Codex receives prompt files, not fictitious registrations.
    if host == 'codex':
        text = text.replace('subagent_type: "poteto-agent"', 'the role prompt `agents/poteto-agent.md`')
        text = text.replace('subagent_type: "comment-sicko"', 'the role prompt `agents/comment-sicko.md`')
    return text

def frontmatter(text, name):
    parts = text.split('---', 2)
    if len(parts) != 3 or parts[0].strip():
        raise ValueError(f'Missing frontmatter: {name}')
    lines = parts[1].strip().splitlines()
    # Remove Cursor presentation and routing metadata, preserve description scalar continuations.
    lines = [line for line in lines if not re.match(r'^(mode|icon|color|reminder|paths|is_background):', line)]
    lines = [f'name: {name}' if line.startswith('name:') else line for line in lines]
    return '---\n' + '\n'.join(lines) + '\n---\n', parts[2].lstrip('\n')

def build(destination, host):
    for component in ('skills', 'agents', 'assets'):
        shutil.copytree(SOURCE / component, destination / component)
    shutil.copy2(SOURCE / 'LICENSE', destination / 'LICENSE')
    adapter = (TEMPLATES / 'host-adapter.md').read_text()
    adapter = adapter.replace('{{HOST}}', 'Claude Code' if host == 'claude' else 'Codex')
    adapter = adapter.replace('{{SKILL_DIR}}', '.claude/skills/' if host == 'claude' else '.agents/skills/')
    adapter = adapter.replace('{{AGENTS}}',
        'Claude Code may dispatch the namespaced installed plugin agents, or its general-purpose agent, through the documented Agent/Task tool.' if host == 'claude' else
        'Codex may use its exposed collaboration tools. It does not register these Markdown files as custom agent types: read `agents/poteto-agent.md` or `agents/comment-sicko.md` and put that role prompt into the delegation brief.')
    (destination / 'references').mkdir()
    (destination / 'references/host-adapter.md').write_text(adapter)
    for path in sorted(destination.rglob('*.md')):
        if path.name == 'host-adapter.md':
            continue
        text = adapt(path.read_text(), host)
        if path.name == 'SKILL.md':
            if path.parent.name == 'setup-pstack':
                text = (TEMPLATES / 'setup-pstack.md').read_text()
            fm, body = frontmatter(text, path.parent.name)
            depth = len(path.relative_to(destination).parts) - 1
            pointer = '../' * depth + 'references/host-adapter.md'
            text = fm + f'\nBefore this workflow, read [the {host} host adapter]({pointer}). It defines tool, model, history, and scheduling compatibility for this port.\n\n' + body
            if host == 'codex':
                write_ui = 'interface:\n  display_name: ' + json.dumps(path.parent.name) + '\n'
                write_ui += '  short_description: "' + ('Apply ' + path.parent.name.replace('-', ' '))[:64] + '"\n'
                if 'disable-model-invocation: true' in fm:
                    write_ui += 'policy:\n  allow_implicit_invocation: false\n'
                ui = path.parent / 'agents/openai.yaml'
                ui.parent.mkdir(exist_ok=True)
                ui.write_text(write_ui)
        elif path.parent.name == 'agents':
            fm, body = frontmatter(text, path.stem)
            if path.stem == 'comment-sicko' and host == 'claude':
                fm = fm.replace('---\n', '---\n', 1).removesuffix('---\n') + 'tools: Read, Grep, Glob, Bash\n---\n'
            text = fm + '\nRead `references/host-adapter.md` from this plugin before applying this role.\n\n' + body
        path.write_text(text.rstrip() + '\n')
    audit = destination / 'skills/poteto-mode/scripts/worktree-audit.sh'
    text = audit.read_text()
    start = text.index('# Transcripts dir:')
    end = text.index('now=$(date +%s)', start)
    text = text[:start] + '# Scan only an explicitly project-scoped transcript directory.\ntranscripts="${PSTACK_TRANSCRIPTS_DIR:-}"\n' + text[end:]
    audit.write_text(text)
    upstream = json.loads((SOURCE / '.cursor-plugin/plugin.json').read_text())
    manifest = {key: upstream[key] for key in ('name', 'description', 'author', 'license', 'keywords')}
    manifest.update(version=upstream['version'] + '-port.1', skills='./skills/',
                    repository='https://github.com/rgoldman73-dev/cursor-plugins',
                    homepage='https://github.com/rgoldman73-dev/cursor-plugins/blob/main/PORTS.md')
    if host == 'claude':
        manifest['agents'] = ['./agents/poteto-agent.md', './agents/comment-sicko.md']
        write_json(destination / '.claude-plugin/plugin.json', manifest)
    else:
        manifest['interface'] = {'displayName': 'pstack', 'shortDescription': 'Rigorous engineering workflows adapted for Codex', 'category': 'Developer tools', 'logo': './assets/logo.png'}
        write_json(destination / '.codex-plugin/plugin.json', manifest)
    write_json(destination / 'UPSTREAM.json', {'repository': 'https://github.com/cursor/plugins', 'commit': UPSTREAM, 'path': 'pstack', 'author': 'Lauren Tan', 'license': 'MIT', 'host': host})
    (destination / 'README.md').write_text(f'# pstack for {host}\n\nAdapted from Lauren Tan\'s MIT-licensed pstack. Read `references/host-adapter.md` before applying workflows. See the fork\'s `PORTS.md` for installation, regeneration, and limitations.\n\nAll upstream skill resources and the Bun helpers are included. Cloud VMs, Cursor automations, models from other providers, and optional control plugins are not provisioned.\n')

def files(root):
    return {str(p.relative_to(root)): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mode & 0o111) for p in root.rglob('*') if p.is_file()}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='pstack-ports-') as tmp:
        for host in ('claude', 'codex'):
            generated = Path(tmp) / host
            build(generated, host)
            target = ROOT / 'ports' / host / 'pstack'
            if args.check:
                if files(generated) != files(target):
                    raise SystemExit(f'{target} differs from generated output; rerun {Path(__file__).name}')
            else:
                if target.exists():
                    shutil.rmtree(target)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(generated, target)
            print(f'{host}: {len(list(generated.glob("skills/*/SKILL.md")))} skills, resources and role prompts; ' + ('verified' if args.check else 'built'))

if __name__ == '__main__':
    main()
