#!/usr/bin/env python3
"""
Generates the multi-page requirements portal from portal-page-template.html + a
decomposition JSON file. Pages are written one file at a time (a simple loop) rather
than hand-authoring the whole set in a single generation pass.

Usage:
    python3 build_portal.py <template_path> <data_json_path> <output_dir> [options]

Options:
    --inline       Embed the full dataset in every page (pre-1.1 behaviour). By default
                   the data is written once to portal-data.js and every page loads it,
                   which keeps the portal ~12x smaller for large decompositions.
    --zip PATH     Also package the portal into a .zip at PATH (pages link to each
                   other with relative hrefs, so they must be delivered together).
    --check        Run the quality gate first and refuse to build if it fails.
    --single-file  Write ONE self-contained index.html with every view inside it (switched via
                   the URL hash, e.g. index.html#stories). Nothing to unzip, works when opened
                   on its own, and can be published as a single web page.
    --model-metrics
                   Keep the readiness / completeness percentages written in the data. By default
                   they are recomputed from the data (see quality_gate.compute_readiness), along
                   with each traceability row's "covered" flag.

Produces 12 pages in <output_dir> (plus portal-data.js unless --inline), or a single
index.html with --single-file:
    index.html, business-context.html, customer-journey.html, requirements.html,
    stories.html, open-questions.html, traceability.html, architecture.html,
    ui-flow.html, assumptions.html, decisions.html, risks.html
"""
import argparse
import json
import os
import sys
import zipfile

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

DATA_FILENAME = "portal-data.js"
SINGLE_VIEW = "__single__"
DATA_SCRIPT_ANCHOR = "<script>\n/* Replace this fallback"


def safe_json_for_script(data):
    """Serialise data so it cannot terminate or alter the surrounding <script>.

    json.dumps alone is not safe inside HTML: a value containing "</script>" closes the
    tag and turns the rest of the string into live markup. Escaping "<", ">" and "&"
    as \\u sequences keeps the JSON identical once parsed, and U+2028/U+2029 are escaped
    because older JS engines treat them as line terminators inside string literals.
    """
    s = json.dumps(data, ensure_ascii=False)
    return (s.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
             .replace("\u2028", "\\u2028").replace("\u2029", "\\u2029"))


def build(template_path, data_path, output_dir, inline=False, zip_path=None, check=False,
          single_file=False, model_metrics=False):
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # Validate the data parses before touching any files.
    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        import quality_gate
    except ImportError:
        quality_gate = None

    if check:
        if quality_gate is None:
            raise SystemExit("--check needs quality_gate.py next to build_portal.py.")
        if quality_gate.run(data_path) != 0:
            raise SystemExit("Quality gate failed — portal not generated.")

    if not model_metrics:
        if quality_gate is None:
            print("  note: quality_gate.py not found — using the percentages written in the data")
        else:
            data = quality_gate.apply_computed(data)

    if DATA_SCRIPT_ANCHOR not in template:
        raise RuntimeError("Template anchor not found — template may have changed shape.")

    payload = f"window.PORTAL_DATA = {safe_json_for_script(data)};"
    os.makedirs(output_dir, exist_ok=True)
    written = []

    if single_file:
        # Remove pages from an earlier multi-page build so the folder isn't misleading.
        for name in list(FILENAMES.values()) + [DATA_FILENAME]:
            p = os.path.join(output_dir, name)
            if os.path.exists(p):
                os.remove(p)
        page = template.replace("__CURRENT_VIEW__", SINGLE_VIEW)
        page = page.replace(DATA_SCRIPT_ANCHOR, f"<script>{payload}</script>\n" + DATA_SCRIPT_ANCHOR, 1)
        out_path = os.path.join(output_dir, "index.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(page)
        written.append(out_path)
        print(f"  wrote {out_path} ({len(page)} chars)")
        print(f"Done. Single-file portal with {len(PAGES)} views written to {out_path}")
        _zip(zip_path, written)
        return written

    if inline:
        data_tag = f"<script>{payload}</script>\n"
        stale = os.path.join(output_dir, DATA_FILENAME)
        if os.path.exists(stale):
            os.remove(stale)
    else:
        data_file = os.path.join(output_dir, DATA_FILENAME)
        with open(data_file, "w", encoding="utf-8") as f:
            f.write(payload + "\n")
        written.append(data_file)
        print(f"  wrote {data_file} ({len(payload)} chars)")
        data_tag = f'<script src="{DATA_FILENAME}"></script>\n'

    # One file per iteration — keeps each write small and independently verifiable.
    for view_id in PAGES:
        page = template.replace("__CURRENT_VIEW__", view_id)
        page = page.replace(DATA_SCRIPT_ANCHOR, data_tag + DATA_SCRIPT_ANCHOR, 1)
        out_path = os.path.join(output_dir, FILENAMES[view_id])
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(page)
        written.append(out_path)
        print(f"  wrote {out_path} ({len(page)} chars)")

    print(f"Done. {len(PAGES)} pages written to {output_dir}")

    _zip(zip_path, written)
    return written


def _zip(zip_path, files):
    if not zip_path:
        return
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, os.path.basename(p))
    print(f"Packaged portal into {zip_path} — extract it, then open index.html.")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Build the multi-page requirements portal.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    parser.add_argument("template_path")
    parser.add_argument("data_json_path")
    parser.add_argument("output_dir")
    parser.add_argument("--inline", action="store_true",
                        help="embed the data in every page instead of portal-data.js")
    parser.add_argument("--zip", dest="zip_path", metavar="PATH",
                        help="also package the portal into a .zip")
    parser.add_argument("--check", action="store_true",
                        help="run the quality gate first; abort on failure")
    parser.add_argument("--single-file", action="store_true",
                        help="write one self-contained index.html containing every view")
    parser.add_argument("--model-metrics", action="store_true",
                        help="keep the readiness/completeness numbers written in the data")
    args = parser.parse_args(argv)
    if args.single_file and args.inline:
        parser.error("--single-file already embeds the data; drop --inline")
    build(args.template_path, args.data_json_path, args.output_dir,
          inline=args.inline, zip_path=args.zip_path, check=args.check,
          single_file=args.single_file, model_metrics=args.model_metrics)


if __name__ == "__main__":
    main()
