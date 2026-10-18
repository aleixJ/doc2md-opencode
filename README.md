# doc2md-opencode

Convert PDFs and images into exhaustive, lossless Markdown for **OpenCode**, using
an Agent Skill plus a slash command.

Every generated file stays inside the folder of the document being processed
(pages, native text and cache go to `<doc_dir>/.doc2md_cache/<stem>/`, and the
final `.md` is written next to the source). Nothing is written to the workspace
root.

## What it does

- Rasterizes each PDF page to PNG and extracts the native text layer for
  cross-verification (avoids provider inconsistencies when sending raw PDFs).
- Reconstructs headings, lists, tables (with merged-cell flattening), LaTeX math
  and code blocks.
- Replaces every image/diagram/schematic with a structured blockquote containing
  a Mermaid graph, a SPICE netlist, a data table or an ASCII tree.
- Preserves the original language and never hallucinates illegible content
  (marks it `[ILLEGIBLE]` / `[UNCERTAIN]`).

## Requirements

- OpenCode (the Python helper and both installers are verified on 1.19.x; the
  skill and command only use v1-stable features).
- Python 3.8+.
- [PyMuPDF](https://pymupdf.readthedocs.io/):

  ```sh
  python -m pip install -r requirements.txt
  ```

  On Windows use `python`; on macOS/Linux use `python3`.

## Install

### One-liner (copy-only, no network)

Windows (PowerShell):

```powershell
./install.ps1 -Project "C:\path\to\your\project"
# or globally:
./install.ps1 -Global
```

macOS / Linux:

```sh
./install.sh --path /path/to/your/project
# or globally:
./install.sh --global
```

### Manual

Copy `.opencode/skills/doc-to-md/` and `.opencode/commands/doc2md.md` into your
project's `.opencode/` directory, or into `~/.config/opencode/` for a global
install. See [docs/INSTALL.md](docs/INSTALL.md) for details.

## Usage

```
/doc2md path/to/document.pdf
/doc2md "docs/Circuit Schematic.pdf" "docs/circuit-schematic.md"
```

`$1` is the input file and `$2` is an optional output path. If `$2` is omitted,
the Markdown is written next to the source with the same name. Quote any path
that contains spaces.

The skill is also auto-selectable by the model from `available_skills`. The
`metadata.opencode/slash: "true"` flag in `SKILL.md` registers an extra
`/doc-to-md` alias **only on newer OpenCode builds**; on 1.19.x it is ignored,
so use `/doc2md` as the entry point on every version.

## Configuration (optional)

The skill works with OpenCode defaults; no configuration is required. If you want
to pin permissions or image limits, copy `examples/opencode.example.jsonc` to your
project as `opencode.jsonc`.

Project config is discovered from the working directory upwards, and both of
these placements work on OpenCode 1.19+ and v2:

- `<project>/opencode.jsonc`
- `<project>/.opencode/opencode.jsonc`

## Version compatibility

| Feature | v1 | v2 | Notes |
| --- | --- | --- | --- |
| `.opencode/skills/<name>/SKILL.md` | yes | yes | same path |
| `.opencode/commands/*.md` | yes | yes | same path |
| `$1` / `$2` | yes | yes | substituted in the command **body** only |
| `.opencode/opencode.jsonc` | yes | yes | merged with the root config |
| `permission` (singular) | yes | accepted (deprecated) | used in the example config |
| `attachment.image` | yes | accepted (deprecated) | used in the example config |
| `media.image` | **no** | yes | unknown top-level key on v1, raises `ConfigInvalidError` |
| `skills: ["path"]` (array) | **no** | yes | v1 needs `{"paths": [...], "urls": [...]}` |
| `metadata.opencode/slash` | **no** | yes | inert on v1, use `/doc2md` |

## Security

- The scripts do not access the network.
- The install scripts only copy files.
- No credentials, tokens or absolute personal paths are stored in this repo.

## License

MIT (c) 2026 aleixj. See [LICENSE](LICENSE).
