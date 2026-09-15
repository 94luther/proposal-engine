"""Render any HTML to PDF, prove the render is current, and proof every page.

    python render-pdf.py "<page.html>" [out.pdf] [--allow-dashes]

The one renderer every skill uses. Never paste a raw msedge command into a skill again.

Three failures this script exists to stop:

1. Edge silently writes nothing when the output path is relative. Absolute only.
2. Edge returns before the PDF is finished. Read a proof too early and you review the PREVIOUS
   render, then chase a bug you already fixed. This waits for the file, then verifies that a
   distinctive string taken from the CURRENT html is actually inside the PDF text.
3. A dash slips into copy. House rule: zero dashes of any kind in anything a person reads. The check runs on the rendered text, so it catches what the browser produced.

Overflow is not detectable from text, so open every proof PNG afterwards. A page that is too tall
is cut off silently with no error anywhere.

  --allow-dashes   skip the dash check. Only for pages nobody reads as prose, never for anything
                   going to a customer or into a tender.

Exit 0 clean. Exit 1 means do not send it.

Honest limit: the staleness net samples ten passages, so a single edited sentence can slip past
it. The real protection is that the old PDF is deleted before every render, so a file that exists
afterwards was written by this run. Treat the probes as a second line, not the first.
"""
import html as htmllib
import pathlib, re, subprocess, sys, time

EDGE = pathlib.Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
CHROME = pathlib.Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

try:
    import pymupdf
except ImportError:
    import fitz as pymupdf


def browser():
    for b in (EDGE, CHROME):
        if b.exists():
            return b
    raise SystemExit("no headless browser found")


def norm(s: str):
    """Compare on ascii letters and digits ALONE, with every space removed.

    Spaces cannot be trusted on either side. Letter-spaced uppercase headings come out of a PDF
    as separated characters ("E X H I B I T"), and a line wrap inserts a break mid sentence. Both
    made this check cry stale on a perfectly current render, so whitespace is discarded entirely.
    """
    s = htmllib.unescape(s)
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def probe_strings(src: str, n=10):
    """Distinctive runs of words, each from ONE html text node, spread across the document.

    Each probe must come from a single node. A probe built from the whole document can straddle
    a page boundary, and that text never appears contiguously in the pdf, which would fail a
    perfectly good render.

    Several probes, not one. A single probe only catches staleness if the edit happened to land
    on that exact sentence, which is a coin toss. Sampling evenly across the file means any real
    edit is very likely to sit on top of one of them.
    """
    # title, script and style carry text that never prints, so they must not become probes
    body = re.sub(r"<(script|style|title)[^>]*>.*?</\1>", " ", src, flags=re.S | re.I)
    body = re.sub(r"<!--.*?-->", " ", body, flags=re.S)
    cands = []
    for node in re.split(r"<[^>]+>", body):
        for sentence in re.split(r"[.!?]", node):
            words = htmllib.unescape(sentence).split()
            if len(words) < 8:
                continue
            t = norm(sentence)          # words counted BEFORE spaces are discarded
            if 40 <= len(t) <= 100:
                cands.append(t)
    if not cands:
        return []
    step = max(1, len(cands) // n)
    return cands[::step][:n]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    if not args:
        print(__doc__)
        return 2
    src = pathlib.Path(args[0]).resolve()
    if not src.exists():
        print(f"NOT FOUND: {src}")
        return 2
    pdf = pathlib.Path(args[1]).resolve() if len(args) > 1 else src.with_suffix(".pdf")
    proofs = src.parent / "_extracted"
    proofs.mkdir(parents=True, exist_ok=True)

    raw = src.read_text(encoding="utf-8")
    probes = probe_strings(raw)
    # Remove the old pdf first. A survivor is exactly what gets reviewed by mistake when a render
    # fails, and a file whose timestamp sits in the future would jam the wait loop below forever.
    pdf.unlink(missing_ok=True)
    started = time.time()

    subprocess.run([str(browser()), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=20000", "--run-all-compositor-stages-before-draw",
                    f"--print-to-pdf={pdf}", src.as_uri()],
                   capture_output=True, timeout=180)

    for _ in range(40):
        if pdf.exists() and pdf.stat().st_size > 20000:
            break
        time.sleep(0.5)
    else:
        print("RENDER FAILED, no fresh pdf appeared")
        return 1
    time.sleep(1.5)

    if pdf.stat().st_mtime < started - 1:
        print("STALE PDF, the file on disk is older than this render. Delete it and run again.")
        return 1

    doc = pymupdf.open(pdf)
    full = "\n".join(doc[i].get_text() for i in range(doc.page_count))
    flat = norm(full)

    missing = [p for p in probes if p not in flat]
    if missing:
        print(f"STALE PDF, {len(missing)} of {len(probes)} checks are not in it. "
              f"The html on disk is not what rendered.")
        for m in missing[:3]:
            print(f"  missing: {m[:70]}")
        print("  delete the pdf and run again")
        return 1

    for i in range(doc.page_count):
        doc[i].get_pixmap(dpi=80).save(str(proofs / f"proof{i+1}.png"))

    offences = ([] if "--allow-dashes" in flags
                else [ln.strip() for ln in full.split("\n")
                      if re.search(r"[\u2013\u2014]|\S - \S", ln)])

    print(f"pdf        {pdf}")
    print(f"pages      {doc.page_count}")
    print(f"verified   {len(probes)} passages from the current html are in the pdf")
    print(f"proofs     {proofs}\\proof1.png .. proof{doc.page_count}.png")
    print(f"dashes     {'skipped' if '--allow-dashes' in flags else len(offences)}")
    for o in offences[:10]:
        print(f"   > {o}")
    print("\nNow OPEN every proof png. Overflow is cut off silently and never raises an error.")
    return 1 if offences else 0


if __name__ == "__main__":
    sys.exit(main())
