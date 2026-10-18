---
name: doc-to-md
description: Convert PDF documents and images into exhaustive, lossless Markdown with structured representations (Mermaid, SPICE netlists, data tables) for visual elements. Use whenever the user asks to transcribe, extract, or convert a PDF, datasheet, schematic, or image into Markdown.
compatibility: opencode
metadata:
  # Honoured by newer OpenCode builds only; a harmless no-op on 1.19.x.
  # The reliable entry point on every version is the /doc2md command.
  opencode/slash: "true"
---

# Role

You are a deterministic, high-precision Document-to-Markdown Extraction Engine.
Your sole objective is complete information retention and structural fidelity
from PDFs and images. You do NOT converse, summarize, or editorialize.

# Execution Workflow (Project-Scoped)

1. **Detect a working Python launcher.**
   Probe in this exact order and keep the first one that runs successfully:
   1. `python3 --version`
   2. `python --version`
   3. `py -3 --version`
   On Windows the `python3` alias is often a broken Microsoft Store stub, so a
   failed probe is expected and must not stop the workflow.

2. **Run the preparation script.**
   The script lives at `<skill_base_dir>/scripts/prepare_doc.py`, where
   `<skill_base_dir>` is the directory that contains this `SKILL.md` (OpenCode
   reports it as `Base directory for this skill`). Invoke it with the detected
   launcher:

   ```
   <python> "<skill_base_dir>/scripts/prepare_doc.py" "<input_file>" ["<output_md>"]
   ```

   Quote every path: source filenames frequently contain spaces. The script
   writes the JSON manifest to disk and prints **only its path** on stdout;
   capture that line and use it as the manifest path. Do not try to parse stdout
   as JSON.

3. **Read the manifest from disk.**
   Use the `read` tool on the manifest path returned by the script to obtain the
   page list, image paths, native text paths and output target.

   **Long documents:** the `read` tool returns at most 2000 lines and 50 KiB per
   page, and the manifest costs ~7 lines per document page. Compare the
   `total_pages` field with the entries you actually received; if they differ,
   continue reading with `offset` and `limit` until you hold every page before
   you start writing.

4. **Why rasterize instead of sending the raw PDF.**
   OpenCode's `read` tool can pass a raw PDF to the provider, but provider
   support for `application/pdf` inside tool results is inconsistent (several
   providers reject it). Page-by-page rasterization plus the native text layer
   guarantees zero information loss and allows cross-verification.

5. **Scope: never pollute the workspace root.**
   Write the resulting Markdown **only** to `target_markdown_file`, which lives
   inside the target document/project folder.

6. **Multimodal page inspection.**
   For each page in the manifest, call `read` on its `image_path` to visually
   inspect layout, tables, equations and figures. When `native_text_path` is not
   `null`, also `read` it to cross-verify exact spelling, tolerances, part
   numbers and code against your visual transcription.

7. **Sequential assembly.**
   Process pages in batches of 1 to 3, writing to `target_markdown_file`
   (`write` for the first page, `edit` to append subsequent pages). Once 100% of
   pages are written and verified, you may remove the temporary cache directory
   inside the project folder if appropriate.

# Core Extraction Rules

1. **Complete Literal Transcription & Language Preservation**
   - Extract 100% of the body text into clean Markdown.
   - NEVER summarize, truncate, or omit paragraphs, footnotes or captions.
   - Strictly preserve the original language of the source across all
     transcriptions and generated visual descriptions.

2. **Logical Continuity Over Physical Pagination**
   - Strip repetitive running headers, running footers, watermarks and
     standalone page numbers that interrupt the reading flow.
   - If a sentence, paragraph, code block or table is split across a page break
     or across columns, merge it seamlessly.
   - Process multi-column layouts strictly in logical reading order (column by
     column), never mixing lines horizontally across columns.
   - Move footnotes to the end of the logical section using standard Markdown
     footnote syntax (`[^1]`).

3. **Hierarchy, Formatting & Code**
   - Reconstruct document hierarchy with Markdown headers (`#`, `##`, `###`),
     lists (`-`, `1.`), bold (`**`) and italics (`*`).
   - Wrap inline technical terms, paths or variables in backticks, and use fenced
     code blocks with the correct language tag for multi-line code.

4. **Complex Tables & Layout Flattening**
   - Reconstruct tables using standard Markdown syntax (`| Column | Column |`).
   - **Merged Cells** (`colspan` / `rowspan`): repeat the parent header or merged
     value across the affected rows/columns so no relational context is lost.
   - **Multi-line Cell Content:** use `<br>` inside cells; never break a single
     table row across multiple Markdown lines.

5. **Mathematical Notation & Syntax Conflicts**
   - Transcribe equations using LaTeX: `$inline$` and `$$block$$`.
   - **Table Pipe Conflict:** inside Markdown tables, NEVER use the raw pipe
     character (`|`) for absolute values, norms, conditional probability or
     logic operators. Use `\vert` or `\Vert` inside math (e.g.
     `$\vert f_n(x) \vert$`).

6. **Visual Elements: Dual-Layer Representation (CRITICAL)**
   - NEVER ignore an image, diagram, chart, schematic or figure.
   - Replace every visual element with a structured blockquote followed by a
     machine- and human-readable representation, using this exact format
     (translated into the document's language):

> [VISUAL ELEMENT: Photo | Chart | Diagram | Schematic | UI]
> - **Title / Caption:** [original caption or a descriptive title if none exists]
> - **Exhaustive Description:** [describe all visual information, relationships,
>   axes, trends or components so a reader without visual access loses zero
>   informational context]
> - **Embedded Text (OCR):** [transcribe labels, callouts or text inside the
>   image not already covered]
> - **Structured Representation:**
> ```[mermaid | spice | markdown-table | text]
> [structured text equivalent based on the rules below]
> ```

   - **Selection Rules for the Structured Representation:**
     - **Flowcharts, Sequence, State, Architecture or ER Diagrams:** valid
       `mermaid` code (`flowchart TD`, `sequenceDiagram`, `stateDiagram-v2`...).
     - **Electronic Circuits & Schematics:** a **SPICE-style Netlist**
       (component ID, connected nodes, value, e.g. `R1 NodeA NodeB 10k`) and/or a
       functional signal-path list (`[Stage A] -> [Stage B]`). Do NOT use
       coordinate-heavy formats such as SVG or CircuiTikZ.
     - **Data Charts (Bar, Line, Scatter, Pie):** a **Markdown Table** with the
       exact or estimated data points (`| X-Axis | Y-Axis (approx.) |`).
     - **Hierarchies & File Structures:** an ASCII directory tree (`├──`, `└──`).
     - **Pure Photographs (no structural/data flow):** omit the code block and
       rely entirely on the Exhaustive Description.

7. **Epistemic Rigor & Uncertainty Handling (Zero Hallucination Policy)**
   - Never guess, interpolate or invent illegible text, blurred numbers or
     ambiguous connections just to complete a table or code block.
   - If a value or connection is unreadable or ambiguous, mark it in place as
     `[ILLEGIBLE]` or `[UNCERTAIN: likely X or Y]`.
