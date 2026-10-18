# Installation

`doc2md-opencode` ships two OpenCode artifacts:

- a skill: `.opencode/skills/doc-to-md/` (with `SKILL.md` and
  `scripts/prepare_doc.py`);
- a command: `.opencode/commands/doc2md.md`.

You can install them per-project or globally. Both methods are copy-only.

## 1. Python dependency

```sh
python -m pip install -r requirements.txt
```

Use `python3` instead of `python` on macOS/Linux.

The skill itself probes `python3` -> `python` -> `py -3`, so you do not need to
know in advance which launcher exists.

## 2. Copy the artifacts

### Automatic

Windows (PowerShell):

```powershell
./install.ps1 -Project "C:\path\to\your\project"
./install.ps1 -Global
```

macOS / Linux:

```sh
./install.sh --path /path/to/your/project
./install.sh --global
```

### Manual

Project install (OpenCode discovers these when started inside the project):

```text
<your-project>/.opencode/
├── commands/doc2md.md
└── skills/doc-to-md/
    ├── SKILL.md
    └── scripts/prepare_doc.py
```

Global install (available in every project):

```text
~/.config/opencode/
├── commands/doc2md.md
└── skills/doc-to-md/
    ├── SKILL.md
    └── scripts/prepare_doc.py
```

## 3. Verify

```sh
python .opencode/skills/doc-to-md/scripts/prepare_doc.py "/path/to/file.pdf"
```

The command prints the path to a generated `manifest.json`. Open it to confirm
the page list, and check that `<doc_dir>/.doc2md_cache/<stem>/` now contains the
rendered pages.

Then, inside OpenCode:

```text
/doc2md /path/to/file.pdf
```

## Notes per version

- **Config location (1.19+ and v2):** an optional `opencode.jsonc` is read from
  the project root *and* from `.opencode/opencode.jsonc`; both are merged.
- **Keys to avoid on OpenCode 1.19:** `media.*` and a bare `skills` array. Use
  `attachment.image` and `{"skills": {"paths": [], "urls": []}}` instead.
- **`metadata.opencode/slash`:** only registers a `/doc-to-md` alias on newer
  builds; on 1.19.x use the `/doc2md` command.

No configuration is required for the skill to function.
