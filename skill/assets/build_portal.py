#!/usr/bin/env python3
"""
Generates the multi-page requirements portal from portal-page-template.html + a
decomposition JSON file. Run one file at a time (a simple loop) rather than trying
to hand-author the whole set in a single generation pass.

Usage:
    python3 build_portal.py <template_path> <data_json_path> <output_dir>

Produces 10 files in <output_dir>:
    index.html, business-context.html, requirements.html, stories.html,
    open-questions.html, traceability.html, architecture.html, assumptions.html,
    decisions.html, risks.html
"""
import json
import sys
import os

PAGES = [
    "overview", "business", "journey", "requirements", "stories", "questions",
    "traceability", "architecture", "uiflow", "assumptions", "decisions", "risks",
]

FILENAMES = {
    "overview": "index.html",
    "business": "business-context.html",
    "journey": "customer-journey.html",
    "requirements": "requirements.html",
    "stories": "stories.html",
    "questions": "open-questions.html",
    "traceability": "traceability.html",
    "architecture": "architecture.html",
    "uiflow": "ui-flow.html",
    "assumptions": "assumptions.html",
    "decisions": "decisions.html",
    "risks": "risks.html",
}

DATA_SCRIPT_ANCHOR = "<script>\n/* Replace this fallback"


def build(template_path, data_path, output_dir):
    with open(template_path, "r") as f:
        template = f.read()

    # Validate the data parses before touching any files.
    with open(data_path, "r") as f:
        data = json.load(f)

    data_script = f"<script>window.PORTAL_DATA = {json.dumps(data)};</script>\n"
    if DATA_SCRIPT_ANCHOR not in template:
        raise RuntimeError("Template anchor not found — template may have changed shape.")

    os.makedirs(output_dir, exist_ok=True)

    written = []
    # One file per iteration — keeps each write small and independently verifiable,
    # rather than generating all pages as one large blob.
    for view_id in PAGES:
        page = template.replace("__CURRENT_VIEW__", view_id)
        page = page.replace(DATA_SCRIPT_ANCHOR, data_script + DATA_SCRIPT_ANCHOR)
        out_path = os.path.join(output_dir, FILENAMES[view_id])
        with open(out_path, "w") as f:
            f.write(page)
        written.append(out_path)
        print(f"  wrote {out_path} ({len(page)} chars)")

    print(f"Done. {len(written)} pages written to {output_dir}")
    return written


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    build(sys.argv[1], sys.argv[2], sys.argv[3])
