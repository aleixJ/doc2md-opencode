---
description: Convert a PDF or image into exhaustive Markdown via the doc-to-md skill
agent: build
---
Use the `skill` tool to load the doc-to-md skill: skill({ name: "doc-to-md" }), then follow it strictly.

Input file: $1
Output Markdown (optional): $2

If the input file is empty, ask the user for it before doing anything else.

Execution steps:
1. Resolve this skill's script at <skill_base_dir>/scripts/prepare_doc.py, where <skill_base_dir> is the directory that contains SKILL.md (reported when the skill is loaded).
2. Detect a working Python launcher by probing, in order: `python3 --version`, `python --version`, `py -3 --version`. Keep the first that succeeds.
3. Run the script with the input file (and the output path if provided), quoting every path because source names may contain spaces. It writes the JSON manifest to disk and prints only its path; capture that line and use it as the manifest path.
4. Use the `read` tool on the manifest path returned in step 3. If `total_pages` is larger than the number of entries you received, continue reading with `offset`/`limit` before writing anything.
5. Process the document page by page exactly as the skill specifies, then write the final Markdown to `target_markdown_file` (inside the document's own folder). Never write to the workspace root.
