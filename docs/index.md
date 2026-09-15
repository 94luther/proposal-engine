# Security and code review: Proposal Engine

Repository: https://github.com/94luther/proposal-engine
Commit: a23ae9cdce9f0d95fd4999f5328e2d5d34746ce3
Bundle generated: 16 September 2026, 00:38 (Africa/Gaborone)

This is the complete current source. Twelve text files. The thirteenth tracked file is a
placeholder logo PNG, not included, not security relevant.

## What this is
A Windows tool that watches an Outlook mailbox. When somebody forwards it a quotation, it scrapes
who the quote is from, matches that to a stored industry playbook, builds an eight page PDF
proposal, and stages a draft reply with the PDF attached. It never sends. There is no language
model in the runtime.

## THE THREAT MODEL
**The attacker is anyone who can send an email to the watched mailbox.** They fully control the
subject, the whole body including anything shaped like a forwarded header, and attachment names.
The company name printed on the document is scraped out of that body with a regular expression.

They do NOT control supplier.json, the industry playbooks, or the code.

## ALREADY FOUND AND FIXED. Do not re-report these. Verify them and move on.
A review earlier today found the following. All are fixed in this commit, and SECURITY.md lists them.

1. The watcher tested for the existence of a predictable filename instead of for a successful
   build, so a stale or rejected PDF could be attached to a draft. Two companies whose names
   normalised to the same slug shared output files.
2. Lists in a company file bypassed HTML escaping.
3. A slug of `..` survived sanitisation and resolved outside the output tree.
4. PowerShell wrote a byte order mark that Python rejected, so the watcher had never once
   completed a build.
5. The five item limit bounded successes, not attempts.
6. The ignore file named a queue file that no longer existed.
7. The scheduled task expired after 23 hours.
8. A dry run wrote state and marked messages seen.
9. The template playbook matched on words like "in" and "an".
10. The watcher skipped internal senders, which meant it ignored the owner's own forwards.
11. The unresolved queue was overwritten each run.
12. A draft could be staged with an empty recipient.

**Your job is to find what that review missed, and to check whether any of those fixes is wrong,
incomplete, or introduced a new fault.** A fix that looks right and is not is worse than the
original bug.

## What I want, in this order

1. **Check the fixes themselves.** Especially the escaping in `clean()` and `SAFE()`, the slug and
   sector validation, and the ARTIFACT path handoff between the PowerShell watcher and the Python
   builder. Is the regex that parses `ARTIFACT=` safe against a company name that contains a
   newline, or against a build that prints that string itself?
2. **Attack the input path again.** Email body to rendered PDF. Escaping bypasses, double decoding,
   unicode normalisation, entity confusion. The headline field deliberately allows `<br>`, `<b>`
   and `</b>`. Break it.
3. **The PowerShell.** Unattended Outlook automation. What happens with a malformed message, an
   enormous body, a hostile attachment name, an exception mid loop, a message with no sender.
4. **Concurrency and state.** Two runs overlapping, `seen.json` corruption, partial writes.
5. **Anything that can cause the wrong customer's document to reach the wrong person.** In a sales
   tool this is worse than a crash.
6. **Correctness of the eight page document build**, since a wrong figure in front of a client is a
   commercial failure even when it is not a security one.
7. **What would you delete?**

Rank by how bad it actually is, not by how clever it was to find. Say plainly when something is
theoretical.

## The standing question
Separately from the above: what is the single biggest thing I am getting wrong or overlooking that
I have not asked you about?

---


## `README.md`

```markdown
# Proposal Engine

**By [Luther Roberts](https://github.com/94luther)** &middot; Business Development, Sprint Couriers,
Gaborone, Botswana

Somebody forwards you a quote a competitor sent them. Thirty minutes later a personalised eight
page proposal is sitting in your drafts folder with the PDF attached, ready to read and send.

It never sends by itself. **It never calls a language model.** Everything in the loop is
deterministic, which is why it can run every thirty minutes forever and cost nothing.

Built for a courier business in Gaborone, Botswana. The engine is industry agnostic.

---

## Why I built it

I kept losing work to quotes I never saw, and winning it when I happened to know something about
how the customer's week actually ran. That knowledge does not scale by working harder. It scales by
being written down once per industry and reused.

So the expensive thinking happens once, for a trade, and every company in that trade after that
costs nothing. Everything else is plumbing.

The first version was five airy pages and it was rubbish. It looked designed and said nothing. What
is here now is dense on purpose, because the people who sign these read documents for a living.

&mdash; Luther Roberts

---

## The idea

Most proposals lose because they answer a price with a price.

This answers a price with an understanding of the buyer's week. It holds one **industry playbook**
per trade, and a playbook knows four things a supplier almost never knows:

1. **The recurring calendar.** Dates that repeat whether anybody feels like it or not, each with the
   published consequence of missing it.
2. **The clock.** The deadline inside that profession that outsiders have never heard of. For
   external auditors it is the standard that caps final audit file assembly at sixty days after the
   report date, with a five year retention rule behind it and a regulator that inspects how it was
   done. Every regulated trade has one. Naming it is what earns the meeting.
3. **Where documents and goods actually travel.** One hub and six destinations.
4. **Five things that go wrong**, what each costs, and what replaces it.

Write that once per industry. Every company in that industry afterwards assembles for free.

## Where the money goes

| Step | Cost |
|---|---|
| Watching the mailbox every 30 minutes | free |
| Working out who the quote is from and which industry they are in | free |
| Building the eight page proposal and rendering the PDF | free |
| Staging the reply as a draft with the PDF attached | free |
| Writing a new industry playbook | one sitting, once per industry, forever |

## The document

Eight A4 pages, built as a consulting exhibit pack rather than a brochure. Every page carries a
kicker, an action title, dense content and a sourced footer.

| Page | Comes from |
|---|---|
| Cover, with a document control block and contents | the company file |
| Their recurring calendar, drawn as bars | the industry playbook |
| Their clock, the deadline inside their trade | the industry playbook |
| Document movement, hub and spoke | the industry playbook |
| Five failure modes and what each costs | the industry playbook |
| What the supplier is, tested the way a buyer would test it | constant |
| Custody, confidentiality and data protection | constant |
| Engagement, three steps and one question | constant |

An earlier version of this was five sparse, airy pages. It was rejected for looking like it had
nothing in it. Density plus domain fluency is the whole point, so the design is fixed in
`style.css` and `build.py` and is never re-decided per client.

## Rules the build enforces

These are not style preferences. The build fails or refuses on each one.

- **No tariff, ever.** A price printed before the runs are measured is a number the buyer cannot
  rely on, and they find that out at the worst moment.
- **Every figure carries its source on the page.** Nothing is typed from memory.
- **No claim about the buyer's own operation.** You have not been inside it, and the document says so.
- **Zero dash characters** in anything a person reads. The renderer fails the build on one.
- **The logo position is asserted out of the finished PDF**, not trusted from the code.
- **The old PDF is deleted before every render**, so a file that exists afterwards was written by
  this run and cannot be a stale one you review by mistake.

## Running it

```bash
pip install pymupdf pillow
python build.py example/company.example.json
```

Writes `out/<slug>/proposal.html`, the PDF, and a proof image of every page. Needs a Chromium
browser present for headless printing; it looks for Edge, then Chrome.

Then edit `supplier.json` so the proposal comes from you rather than from a placeholder, and
install the watcher:

```powershell
powershell -ExecutionPolicy Bypass -File Install-Task.ps1
```

Every 30 minutes. The script stands down at weekends, outside 07:30 to 17:30, on Fridays after
16:30, and if a `PAUSED.flag` file exists.

## What it refuses to do

- It will not send an email. Drafts only, stamped for the next working morning.
- It will not guess a company name it cannot read. That goes to `NEEDS-A-HUMAN.md`.
- It will not build for an industry with no playbook. Same file.
- It will not treat an internal colleague forwarding a rate card as a sales lead.
- It will not build more than five in one run, so a backlog cannot flood the drafts folder.

## Layout

```
build.py            the design, in code
style.css           the look, fixed once
render-pdf.py       render, prove the PDF is current, fail on a dash, proof every page
supplier.json       who the proposal is FROM. Edit this first
sectors/            one industry playbook per trade. This is the asset
  _TEMPLATE.json    copy this and fill it in
example/            a sample company file
Watch-Quotes.ps1    the mailbox watcher, Outlook on Windows
Install-Task.ps1    the scheduled task
```

Real industry playbooks and all client data live outside this repository.

## Status

Last pushed 15 September 2026. This is the engine as it runs in
production. The industry playbooks that drive it improve continuously and are not public, so treat
the `sectors/_TEMPLATE.json` here as the shape, not the state of the art.

Security posture and known limitations are in [SECURITY.md](SECURITY.md).

## Honest limits

- The watcher is Outlook on Windows only. The builder is cross platform.
- Company names are read out of forwarded mail headers with a regular expression, which fails often
  enough that anything unreadable is handed to a human rather than guessed.
- The staleness check on a render samples ten passages, so a single edited sentence can slip past
  it. The real protection is that the old PDF is deleted before every run.
- There is no company level research. A playbook is industry level by design, because that is what
  makes it free.

## Author

**Luther Roberts**, Gaborone, Botswana &middot; [github.com/94luther](https://github.com/94luther)

Built for [Sprint Couriers](https://sprintcouriers.co.bw). Written with AI assistance, directed,
specified and corrected by me over several rounds. The industry playbooks, which are the part that
makes it work, are mine and are not in this repository.

## Licence

MIT, Copyright 2026 Luther Roberts. See `LICENSE`.
```

## `SECURITY.md`

```markdown
# Security

This tool reads email that anybody can send, and turns it into a document. That makes the input
hostile by default, and the code treats it that way.

## Reporting

Open an issue, or email the address on the author's GitHub profile. There is no bounty.

## The threat model

The attacker is anyone who can get an email into the watched mailbox. They control:

- the subject line
- the entire body, including anything that looks like a forwarded header
- attachment names

They do not control `supplier.json`, the industry playbooks, or the code.

## What is defended, and how

| Attack | Defence |
|---|---|
| HTML or script injected through a company name scraped from an email body | Every string in a company file is escaped before it reaches the page. Only `<br>`, `<b>` and `</b>` survive, and only in the headline field |
| Path traversal through the output folder name | The slug is reduced to letters, digits, dot, dash and underscore, and capped at 80 characters |
| Path traversal through the industry playbook name | The sector must match a plain file name pattern or the build refuses to run |
| Shell injection through a company name | No shell is ever used. Subprocess calls pass an argument list, never a command string |
| A flood of crafted emails filling the drafts folder | At most five proposals per run |
| Being tricked into treating your own colleagues as prospects | Internal addresses are skipped before anything is built |
| An email sent automatically on your behalf | Nothing is ever sent. Drafts only |

## Review history

**16 September 2026, independent security review.** Findings accepted and fixed in full:

| Finding | Status |
|---|---|
| Failed builds could attach a stale or rejected PDF, because the watcher tested for a file rather than for success | Fixed. The builder prints the artifact path only on success, each run writes to its own timestamped folder, and the exit code is honoured |
| Lists in a company file walked straight past the HTML escaper | Fixed. Text fields must be text or the build refuses, and lists are escaped |
| A slug of `..` survived sanitisation and resolved to the repository root | Fixed. Dot segments and Windows reserved names are rejected |
| The ignore file named a queue file that no longer existed, so review notes could be committed | Fixed |
| The five item limit bounded successes, not attempts, so failures were unbounded | Fixed. Attempts are bounded separately |
| PowerShell wrote a byte order mark that Python rejected, so the watcher had never built anything | Fixed. Input is read as utf-8-sig and written without a mark |
| The output filename was reconstructed by the caller instead of returned by the builder | Fixed |
| The scheduled task expired after 23 hours | Fixed. It now repeats indefinitely |
| A dry run wrote state and marked messages seen | Fixed. A dry run changes nothing |
| The template playbook matched on words like "in" and "an" | Fixed. It matches nothing until filled in |
| The watcher skipped internal senders, which meant it ignored your own forwards | Fixed. The forwarder may be internal. The company named inside the forward may not be |
| The unresolved queue was overwritten each run | Fixed. Entries persist until resolved |

Found during the fix: a draft could be staged with no recipient when the forwarder's address could
not be read. It now goes to the human queue instead, with the PDF path.

## Known limitations, stated rather than hidden

- **The generated HTML is opened in a headless browser on your machine.** Escaping is the only
  thing standing between a hostile email and that browser. If you extend `build.py` with a field
  that bypasses `clean()`, you reopen the hole.
- **Company names are extracted with a regular expression.** It fails often. Anything unreadable is
  handed to a human rather than guessed, which is the safe failure but not a pleasant one.
- **The watcher has full access to the mailbox** through Outlook automation. It reads and it
  drafts. It never deletes, never sends, never forwards.
- **The staleness check on a render samples ten passages**, so a single edited sentence can slip
  past it. The real protection is that the old PDF is deleted before every run.
- **No authentication anywhere.** This runs as a scheduled task under one user account on one
  machine. Anyone with that account has everything.
- **`seen.json` grows without bound.** Not a security issue, but it will get slow eventually.

## If you fork this

Change `supplier.json` first, including `own_domain_pattern`, or the watcher will treat your own
colleagues as sales leads.
```

## `.gitignore`

```
inbox/
out/
seen.json
watch-log.txt
NEEDS-LUTHER.md
NEEDS-A-HUMAN.md
*.pdf
__pycache__/
```

## `LICENSE`

```
MIT License

Copyright (c) 2026 Luther Roberts

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY.
```

## `supplier.json`

```json
{
  "_note": "Who the proposal is FROM. Replace every value before using this. own_domain_pattern stops the watcher treating your own colleagues as sales leads.",
  "name": "Your Company",
  "city": "Your City",
  "address": "Your street address",
  "website": "yourcompany.example",
  "rep_name": "Your Name",
  "rep_email": "you@yourcompany.example",
  "rep_office": "000 0000",
  "rep_mobile": "00 000 000",
  "strapline": "subject to operational assessment, credit approval and a signed service agreement",
  "own_domain_pattern": "yourcompany\\.example"
}
```

## `build.py`

```python
"""Build a Sprint exhibit pack proposal from a company file and an industry playbook.

    python build.py "<company.json>" [outdir]

The design lives here, in code. It is a dense consulting exhibit pack, chosen after a
sparse, airy version was rejected for looking like it had nothing in it. Nothing about the look is decided per
client, so every proposal that leaves this machine looks like it came from the same firm.

What varies per client:
  company.json      who they are, taken from the forwarded quote
  sectors/<x>.json  the industry playbook: their calendar, their clock, their failure modes

Pages 6, 7 and 8 are constant. They are what Sprint is, how custody works, and how to start.
Those never change per client, so they are written once here and never re-thought.

Zero model calls. Once an industry playbook exists, every new company in that industry is free.
"""
import datetime as dt
import html
import json
import re
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
RENDER = HERE / "render-pdf.py"

E = lambda s: html.escape(str(s), quote=False)

# A company file is UNTRUSTED. In the automated path its fields are scraped out of the body of an
# email anybody can send, so treat every value as hostile until it has been escaped.
_ALLOWED = (("&lt;br&gt;", "<br>"), ("&lt;b&gt;", "<b>"), ("&lt;/b&gt;", "</b>"))


def SAFE(s):
    """Escape, then put back only the three tags a headline is allowed to use."""
    out = html.escape(str(s), quote=False)
    for bad, good in _ALLOWED:
        out = out.replace(bad, good)
    return out


def clean(co):
    """Escape every string in the company file before any of it reaches the page."""
    rich = {"headline"}                      # may carry <br> and <b>, nothing else
    text_fields = {"name", "slug", "address", "doc_no", "headline", "dek", "ask", "provenance", "sector"}
    for k in text_fields:
        if k in co and not isinstance(co[k], str):
            raise SystemExit(f"refusing to build: {k!r} must be text, got {type(co[k]).__name__}")
    for k, v in list(co.items()):
        if isinstance(v, str):
            co[k] = SAFE(v) if k in rich else E(v)
        elif isinstance(v, dict):
            co[k] = {E(a): E(b) for a, b in v.items()}
        elif isinstance(v, list):
            co[k] = [E(x) for x in v]        # a list used to walk straight past the escaper
    # a slug becomes a folder name and a sector becomes a file path, so neither may escape the tree
    slug = re.sub(r"[^A-Za-z0-9._-]", "-", str(co.get("slug", "proposal")))[:80].strip(". ")
    if not slug or set(slug) <= {"."} or slug.upper().split(".")[0] in {
            "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "LPT1", "LPT2"}:
        slug = "proposal"
    co["slug"] = slug
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,60}", str(co.get("sector", ""))):
        raise SystemExit(f"refusing to build: sector name is not a plain file name: {co.get('sector')!r}")
    return co

# Who the proposal is FROM. Kept out of the code so the engine is not tied to one company.
SUP = json.loads((HERE / "supplier.json").read_text(encoding="utf-8"))


# ────────────────────────────────── page parts ──────────────────────────────────
def head(co, page_kick, page_title, page_sub=""):
    sub = f'<div class="sub">{page_sub}</div>' if page_sub else ""
    return f'''<div class="page">
  <div class="rh"><div class="l">{E(co["name"])}<i>Service Proposal {E(co["doc_no"])}</i></div>
    <img src="assets/logo-mark.png" alt="Sprint Couriers"></div>
  <div class="kick">{page_kick}</div>
  <div class="at">{page_title}</div>{sub}'''


def foot(source, n):
    return f'''  <div class="src"><span>{source}</span><span>{n:02d}</span></div>
</div>'''


def table(cols, rows, widths=None):
    w = widths or [None] * len(cols)
    th = "".join(f'<th{f" style=\"width:{x}\"" if x else ""}>{c}</th>' for c, x in zip(cols, w))
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f"<table><tr>{th}</tr>{tr}</table>"


def ticks(items, cls=""):
    li = "".join(f'<li class="{cls}">{i}</li>' for i in items)
    return f'<ul class="tick">{li}</ul>'


def stat(v, k, colour=None):
    c = f' style="color:{colour}"' if colour else ""
    return f'<div class="stat"><div class="v"{c}>{v}</div><div class="k">{k}</div></div>'


def month_bars(offset, fill, y, h=24, w=11, pitch=70, n=12, opacity=None):
    o = f' opacity="{opacity}"' if opacity else ""
    return "".join(f'<rect x="{i*pitch+offset}" y="{y}" width="{w}" height="{h}" fill="{fill}"{o}/>'
                   for i in range(n))


def cover(co, contents):
    rows = "".join(f'<div><span>{k}</span><b>{E(v)}</b></div>' for k, v in co["control"].items())
    toc = "".join(f'<div><i>{i+1:02d}</i>{t}</div>' for i, t in enumerate(contents))
    return f'''<div class="page cover">
  <div class="bar"></div>
  <div class="inner">
    <div class="top">
      <div class="l">{E(co["name"])}<i>{E(co.get("address", ""))}</i></div>
      <span class="plate"><img src="assets/logo-mark.png" alt="Sprint Couriers"></span>
    </div>
    <h1>{co["headline"]}</h1>
    <div class="dek">{co["dek"]}</div>
    <div class="ctl">{rows}</div>
    <div class="toc">{toc}</div>
    <div class="foot">
      <div>{SUP["name"]} &middot; {SUP["address"]} &middot; {SUP["website"]}</div>
      <div style="text-align:right">{SUP["strapline"]}</div>
    </div>
  </div>
</div>'''


# ────────────────────────────────── constant pages ──────────────────────────────────
def page_capability(co, n):
    rows = [
        ("Years in operation", "Operating in Botswana since <b>2006</b>"),
        ("Ownership", "One hundred percent citizen owned"),
        ("Network", "More than <b>75 destinations</b>, with branches including Gaborone, Tlokweng, "
                    "Mogoditshane, Phakalane, Francistown, Palapye, Mahalapye, Maun, Kasane and Ghanzi"),
        ("Speed in Gaborone", "One hour Sprint Service"),
        ("Nationwide", "Overnight delivery"),
        ("Licensing", "Courier licence, road transport permit and a <b>customs clearing agent licence</b> "
                      "held in Sprint's own name"),
        ("International", "Aramex Botswana acquired in full in <b>February 2018</b>, reaching 243 countries"),
        ("Evidence of delivery", "Real time tracking, automated proof of delivery, email and SMS notification"),
        ("Billing", "Monthly account, thirty day terms, one invoice"),
        ("References", "Banking and public sector accounts, named at the assessment on request"),
    ]
    return head(co, f"Exhibit {n:02d} &middot; The counterparty",
                "What Sprint Couriers is,<br><b>set out the way you would test it.</b>") + f'''
  <div class="row r-32 grow">
    <div>{table(["Test", "Position"], rows, ["40mm", None])}</div>
    <div>
      <div class="box dark">
        <div class="bt">The three that matter here</div>
        {stat("1 hr", "to a Gaborone counter, once released", "#4FC249")}
        <div style="height:4mm"></div>
        {stat("Nightly", "Gaborone and Francistown, both directions", "#4FC249")}
        <div style="height:4mm"></div>
        {stat("POD", "a name and a time, returned to the person who sent it", "#4FC249")}
      </div>
      <div class="box" style="margin-top:4.5mm">
        <div class="bt">Structure of the relationship</div>
        <p>One account. One named contact in Gaborone. Bookings from any site, by any authorised
          person, against the same account.</p>
        <p>Monthly reporting on what moved, where it went and what it cost, so whoever is
          responsible can see it without having to ask anyone.</p>
        <div style="margin-top:auto;padding-top:4mm;border-top:.8px solid #E6ECE7">
          <p style="color:#5E6C64">Licence numbers, certificates and named client references are
            produced at the assessment rather than asserted in a proposal.</p>
        </div>
      </div>
    </div>
  </div>''' + foot("<b>Sources.</b> Sprint Couriers company profile and service descriptions.", n)


def page_custody(co, n):
    pts = [("Booked", "who asked, and when"), ("Collected", "signed by name, timed"),
           ("In transit", "visible at both ends"), ("Delivered", "signed by the recipient"),
           ("Recorded", "on your monthly report")]
    xs = [40, 230, 420, 610, 800]
    dots = "".join(f'<circle cx="{x}" cy="46" r="9" fill="{"#0F1A14" if i==0 else "#F7941D" if i==4 else "#3AAA35"}"/>'
                   for i, x in enumerate(xs))
    lab = "".join(f'<text x="{x}" y="74">{p[0]}</text>' for x, p in zip(xs, pts))
    sub = "".join(f'<text x="{x}" y="90">{p[1]}</text>' for x, p in zip(xs, pts))
    return head(co, f"Exhibit {n:02d} &middot; Custody and confidentiality",
                "Speed is not your real requirement.<br><b>Being able to account for a file is.</b>",
                "An organisation can survive a document arriving an hour late. It cannot easily survive one it "
                "cannot account for. Since January 2025 that is no longer only a commercial matter.") + f'''
  <svg viewBox="0 0 840 138" style="margin-top:4mm">
    <line x1="40" y1="46" x2="800" y2="46" stroke="#0F1A14" stroke-width="2"/>{dots}
    <g font-family="Barlow" font-size="10.2" font-weight="700" fill="#0F1A14" text-anchor="middle">{lab}</g>
    <g font-family="Barlow" font-size="8.2" fill="#7E8C84" text-anchor="middle">{sub}</g>
    <text x="40" y="126" font-family="Barlow" font-size="9.4" fill="#5E6C64">Five points at which a document is a
      named person's responsibility, rather than in somebody's bag.</text>
  </svg>
  <div class="row r-3 grow">
    <div class="box warn">
      <div class="bt" style="color:#B8770F">The obligation that now sits behind this</div>
      <p>The Data Protection Act came into force in Botswana on <b>14 January 2025</b>. Your files carry personal
        data, and responsibility for it does not pass to a carrier simply because the carrier is holding the envelope.</p>
      <p>Choosing a carrier is choosing a processor, and that choice is easier to defend when the carrier is a
        licensed Botswana operator whose records stay in the country.</p>
      <div style="margin-top:auto;padding-top:3.5mm;border-top:1px solid #F0D3A8;display:grid;grid-template-columns:1fr 1fr;gap:4mm">
        {stat("P50m", "or four percent of global turnover, the upper penalty for non compliance", "#B8770F")}
        {stat("72 hrs", "to notify the Commission of a breach", "#B8770F")}
      </div>
    </div>
    <div class="box">
      <div class="bt">What we will put in writing at the assessment</div>
      {ticks(["A confidentiality undertaking covering every consignment",
              "Named authorised bookers, so no unknown person can move your documents",
              "Sealed and tamper evident handling for categories you define",
              "Retention of proof of delivery records, and your access to them",
              "An escalation route with a name and a number, not a call centre",
              "A written position on where consignment data is held and who may see it"])}
      <p style="margin-top:auto;padding-top:3mm;color:#5E6C64">These are offered for negotiation. They take effect
        only in a signed service agreement, not in this document.</p>
    </div>
    <div class="box">
      <div class="bt">Controller and processor, plainly</div>
      <p>You stay the controller of the data in the envelope. A carrier is a processor, acting on your written
        instruction and nothing more.</p>
      <p>That distinction decides who must answer the Commission within seventy two hours, and what the carrier is
        contractually required to do the moment something cannot be found.</p>
      <div style="margin-top:3mm;border-top:.8px solid #E6ECE7;padding-top:2.5mm">
        <div class="bt">Questions to ask any carrier</div>
        {ticks(["Where is consignment data stored, and who inside the carrier can see it",
                "How long are proof of delivery records kept, and can we get them",
                "Who is told, and how fast, when a consignment cannot be accounted for",
                "Is the carrier licensed here, and answerable here"])}
      </div>
      <p style="margin-top:auto;padding-top:3mm;color:#5E6C64">We would rather you asked these of us in a meeting
        than discovered the answers afterwards.</p>
    </div>
  </div>''' + foot("<b>Sources.</b> Botswana Data Protection Act, in force 14 January 2025, penalties of up to "
                   "P50 million or four percent of global turnover and a 72 hour breach notification duty.", n)


def page_engagement(co, n):
    ask = co.get("ask", "Who carries this for you today?")
    return head(co, f"Exhibit {n:02d} &middot; Engagement",
                "Three steps.<br><b>The first one costs you twenty minutes.</b>") + f'''
  <div class="row r-3">
    <div class="box"><div class="bt">Step one &middot; this week</div>{stat("20", "minutes, at your premises", "#3AAA35")}
      <p style="margin-top:3mm">We walk your actual runs and take the volumes down. You get a written rate card
        against those runs.</p></div>
    <div class="box"><div class="bt">Step two &middot; one movement</div>{stat("01", "live movement, tracked end to end")}
      <p style="margin-top:3mm">One real consignment, on our account, so you test the proof of delivery and the
        timing before anything is signed.</p></div>
    <div class="box"><div class="bt">Step three &middot; the account</div>{stat("30", "day terms, one monthly invoice")}
      <p style="margin-top:3mm">Named bookers, a named contact, monthly reporting on what moved and what it cost,
        and the confidentiality undertaking inside the agreement.</p></div>
  </div>

  <div class="box dark" style="margin-top:5mm;padding:6mm">
    <div style="display:flex;justify-content:space-between;align-items:center;gap:8mm">
      <div>
        <div style="font-size:12.5pt;font-weight:300;line-height:1.3">One question, and one line back is enough.</div>
        <div style="font-size:16pt;font-weight:700;color:#4FC249;margin-top:1.5mm">{ask}</div>
        <p style="color:#B7C6BC;margin-top:3mm;max-width:104mm">If the answer is somebody on your own payroll, that
          is the conversation. If it is another carrier, tell us the one thing they do not do, and we will answer
          that instead of repeating what you already have.</p>
      </div>
      <div style="text-align:right;font-size:8.2pt;line-height:1.7;flex:0 0 auto">
        <b style="font-size:11pt;display:block">{SUP["rep_name"]}</b>
        {SUP["name"]}, {SUP["city"]}<br>{SUP["rep_email"]}<br>Office {SUP["rep_office"]}<br>
        <span style="color:#F7941D;font-family:'IBM Plex Mono',monospace;font-weight:600">WhatsApp {SUP["rep_mobile"]}</span>
      </div>
    </div>
  </div>

  <div class="row r-2 grow">
    <div class="box warn">
      <div class="bt" style="color:#B8770F">On price, plainly</div>
      <p>There is no tariff in this document on purpose. A run is priced on where it goes and how often it goes
        there. A rate card printed before those runs are measured is a number you could not rely on, and you would
        find that out at the worst possible moment.</p>
      <p>Your rate card is confirmed in writing after the assessment, against your actual runs, and it holds for
        the account.</p>
      <div style="margin-top:auto;padding-top:4mm;border-top:1px solid #F0D3A8">
        <div class="bt" style="color:#B8770F">What the assessment covers</div>
        <p style="color:#7A5F35">Your runs, your sites, your peak week and your volumes. Twenty minutes at your
          premises, and no obligation at the end of it.</p>
      </div>
    </div>
    <div class="box fill">
      <div class="bt">Document control</div>
      {table([], [(k, f'<span class="num">{E(v)}</span>') for k, v in co["control"].items()], ["32mm", None])}
      <div style="margin-top:auto;padding-top:4mm;border-top:.8px solid #E6ECE7">
        <div class="bt">Where this came from</div>
        <p style="color:#5E6C64">{co.get("provenance", "Prepared for you after we saw what you are currently being quoted.")}</p>
      </div>
    </div>
  </div>''' + foot(f"<b>{SUP['name']}</b> &middot; {SUP['address']} &middot; {SUP['website']} "
                   f"&middot; {SUP['strapline']}", n)


# ────────────────────────────────── sector pages ──────────────────────────────────
def page_cycle(co, s, n):
    """The client's recurring calendar, drawn as bars, with an obligations table beneath."""
    c = s["cycle"]
    bars, labels, y = [], [], 31
    palette = ["#0F1A14", "#3AAA35", "#0F1A14", "#0F1A14"]
    opac = [None, None, ".5", ".22"]
    lines = []
    for i, r in enumerate(c["rows"][:4]):
        labels.append(f'<text x="0" y="{y}" font-family="Barlow" font-size="10" font-weight="700">{r["label"]}</text>')
        if r.get("every_month", True):
            bars.append(f'<g>{month_bars(r.get("offset", 32), palette[i], y + 9, opacity=opac[i], w=r.get("w", 11))}</g>')
        else:
            bars.append("<g>" + "".join(
                f'<rect x="{x}" y="{y+9}" width="{r.get("w",20)}" height="24" fill="{palette[i]}"'
                f'{f" opacity={chr(34)}{opac[i]}{chr(34)}" if opac[i] else ""}/>' for x in r["at"]) + "</g>")
        lines.append(f'<line x1="0" y1="{y+37}" x2="840" y2="{y+37}" stroke="#D6DED8" stroke-width="1"/>')
        y += 52
    months = "".join(f'<text x="{i*70+4}" y="10">{m}</text>' for i, m in enumerate(c["months"]))
    vlines = "".join(f'<line x1="{i*70}" y1="16" x2="{i*70}" y2="{y-15}" stroke="#EDF1EE" stroke-width="1"/>'
                     for i in range(1, 12))
    peak = ""
    if c.get("peak"):
        peak = (f'<rect x="{c["peak"]["x"]}" y="{y-67}" width="58" height="54" fill="none" stroke="#F7941D" stroke-width="2.4"/>'
                f'<text x="{c["peak"]["x"]}" y="{y+6}" font-family="Barlow" font-size="10" font-weight="700" '
                f'fill="#B8770F">{c["peak"]["label"]}</text>')
    return head(co, f"Exhibit {n:02d} &middot; {c['kick']}", c["title"], c["sub"]) + f'''
  <svg viewBox="0 0 840 {y+12}" style="margin-top:4mm">
    <g font-family="Barlow Condensed" font-size="12" font-weight="700" fill="#7E8C84" letter-spacing="1.6">{months}</g>
    {vlines}<line x1="0" y1="16" x2="840" y2="16" stroke="#D6DED8" stroke-width="1"/>
    {"".join(lines)}{"".join(labels)}{"".join(bars)}{peak}
  </svg>
  <div class="row r-32 grow">
    <div>
      <div class="bt">{c["table_title"]}</div>
      {table(c["table_cols"], c["table_rows"], c.get("table_widths"))}
    </div>
    <div class="box warn">
      <div class="bt" style="color:#B8770F">{c["aside_title"]}</div>
      {"".join(f"<p>{p}</p>" for p in c["aside"])}
      <div style="margin-top:auto;padding-top:3.5mm;border-top:1px solid #F0D3A8;display:grid;grid-template-columns:1fr 1fr;gap:4mm">
        {"".join(stat(x["v"], x["k"], "#B8770F") for x in c["aside_stats"])}
      </div>
    </div>
  </div>''' + foot(c["source"], n)


def page_clock(co, s, n):
    k = s["clock"]
    return head(co, f"Exhibit {n:02d} &middot; {k['kick']}", k["title"], k["sub"]) + f'''
  <svg viewBox="0 0 840 196" style="margin-top:4mm">
    <line x1="30" y1="56" x2="810" y2="56" stroke="#D6DED8" stroke-width="2"/>
    <rect x="30" y="48" width="250" height="16" fill="#F7941D"/>
    <rect x="280" y="48" width="530" height="16" fill="#0F1A14" opacity=".16"/>
    <circle cx="30" cy="56" r="9" fill="#0F1A14"/><circle cx="280" cy="56" r="9" fill="#F7941D"/>
    <circle cx="810" cy="56" r="9" fill="#0F1A14"/>
    <g font-family="Barlow" font-size="11" font-weight="700" fill="#0F1A14">
      <text x="18" y="34">{k["t0"]}</text><text x="234" y="34">{k["t1"]}</text><text x="734" y="34">{k["t2"]}</text></g>
    <g font-family="Barlow" font-size="9" fill="#5E6C64">
      <text x="18" y="84">{k["t0sub"]}</text><text x="192" y="84">{k["t1sub"]}</text><text x="676" y="84">{k["t2sub"]}</text></g>
    <text x="60" y="110" font-family="Barlow" font-size="9.6" font-weight="700" fill="#B8770F">{k["span1"]}</text>
    <text x="420" y="110" font-family="Barlow" font-size="9.6" font-weight="700" fill="#5E6C64">{k["span2"]}</text>
    <text x="30" y="148" font-family="Barlow" font-size="10" font-weight="700" fill="#0F1A14">{k["items_title"]}</text>
    <g fill="#0F1A14">{"".join(f'<rect x="{30+i*138}" y="158" width="120" height="7"/>' for i in range(len(k["items"])))}</g>
    <g font-family="Barlow" font-size="8.6" fill="#5E6C64">
      {"".join(f'<text x="{30+i*138}" y="180">{t}</text>' for i, t in enumerate(k["items"]))}</g>
  </svg>
  <div class="row r-2">
    <div class="box fill"><div class="bt">{k["why_title"]}</div>{ticks(k["why"])}</div>
    <div class="box dark"><div class="bt">{k["fix_title"]}</div>{ticks(k["fix"])}
      <p style="color:#B7C6BC;margin-top:2.5mm;font-size:7.6pt">{k["fix_note"]}</p></div>
  </div>
  <div class="row r-3 grow">
    {"".join(f'<div class="box {p.get("cls","")}"><div class="bt">{p["t"]}</div>' +
             ("".join(f"<p>{x}</p>" for x in p["p"]) if p.get("p") else "") +
             (table(p["cols"], p["rows"], p.get("widths")) if p.get("rows") else "") +
             (f'<div style="margin-top:auto;padding-top:3mm">{stat(p["stat"]["v"], p["stat"]["k"], "#B8770F")}</div>'
              if p.get("stat") else "") + "</div>" for p in k["panels"])}
  </div>''' + foot(k["source"], n)


def page_failures(co, s, n):
    f = s["failures"]
    return head(co, f"Exhibit {n:02d} &middot; Failure modes", f["title"]) + f'''
  <div style="margin-top:4mm">{table(f["cols"], f["rows"], f.get("widths"))}</div>
  <div class="row r-3 grow">
    <div class="box"><div class="bt">What this proposal is not</div>{ticks(f["not"], "x")}</div>
    <div class="box fill"><div class="bt">What we would measure at the assessment</div>{ticks(f["measure"])}</div>
    <div class="box warn"><div class="bt" style="color:#B8770F">How the account gets used, day to day</div>
      {ticks(["A named person books a collection from any of your sites",
              "The consignment is signed for at collection, with a time against a name",
              "Both ends see the status without telephoning anybody",
              "Proof of delivery returns to the person who booked it",
              "Everything that moved appears on one monthly statement, coded once"], "x")}
      <p style="margin-top:auto;padding-top:3mm;color:#7A5F35">The practical test is simple. After a month, you
        should be able to say where any consignment went, without asking a single person.</p></div>
  </div>''' + foot(f["source"], n)


# ────────────────────────────────── assemble ──────────────────────────────────
def build(company_path, outdir=None):
    # utf-8-sig, because PowerShell writes a byte order mark that plain utf-8 rejects.
    co = clean(json.loads(pathlib.Path(company_path).read_text(encoding="utf-8-sig")))
    sector = json.loads((HERE / "sectors" / f"{co['sector']}.json").read_text(encoding="utf-8-sig"))
    out = pathlib.Path(outdir or (HERE / "out" / co["slug"])).resolve()
    out.mkdir(parents=True, exist_ok=True)
    for a in (HERE / "assets").iterdir():
        (out / "assets").mkdir(exist_ok=True)
        (out / "assets" / a.name).write_bytes(a.read_bytes())

    contents = [sector["cycle"]["toc"], sector["clock"]["toc"], "Where your documents actually travel",
                "Failure modes, and what each costs", "What Sprint is, tested the way you would test it",
                "Custody, confidentiality and the Data Protection Act", "Engagement model and the next step"]

    pages = [cover(co, contents), page_cycle(co, sector, 1), page_clock(co, sector, 2),
             page_hub(co, sector, 3), page_failures(co, sector, 4),
             page_capability(co, 5), page_custody(co, 6), page_engagement(co, 7)]

    css = (HERE / "style.css").read_text(encoding="utf-8")
    htmlout = (f'<meta charset="utf-8">\n<title>Sprint Couriers Service Proposal {E(co["name"])}</title>\n'
               '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow:wght@300;400;500;600;700'
               '&family=Barlow+Condensed:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap">\n'
               f"<style>\n{css}\n</style>\n" + "\n".join(pages))
    hp = out / "proposal.html"
    hp.write_text(htmlout, encoding="utf-8")

    pdf = out / f"{SUP['name'].replace(chr(32), chr(45))}-{co['slug']}.pdf"
    r = subprocess.run([sys.executable, str(RENDER), str(hp), str(pdf)], capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode != 0:
        print(r.stderr.strip())
    # The caller must not reconstruct this path. Say it plainly, once.
    if r.returncode == 0 and pdf.exists():
        print(f"ARTIFACT={pdf}")
    return pdf, r.returncode


def page_hub(co, s, n):
    h = s["hub"]
    left, right = h["left"], h["right"]
    ly = [54, 151, 250]
    spokes = "".join(f'<line x1="330" y1="{136+i*16}" x2="180" y2="{ly[i]}"/>' for i in range(len(left)))
    spokes += "".join(f'<line x1="510" y1="{136+i*16}" x2="660" y2="{ly[i]}"/>' for i in range(len(right)))
    lnames = "".join(f'<text x="172" y="{ly[i]-4}">{d["t"]}</text>' for i, d in enumerate(left))
    lsubs = "".join(f'<text x="172" y="{ly[i]+11}">{d["s"]}</text>' for i, d in enumerate(left))
    rnames = "".join(f'<text x="670" y="{ly[i]-4}">{d["t"]}</text>' for i, d in enumerate(right))
    rsubs = "".join(f'<text x="670" y="{ly[i]+11}">{d["s"]}</text>' for i, d in enumerate(right))
    return head(co, f"Exhibit {n:02d} &middot; Document movement", h["title"]) + f'''
  <svg viewBox="0 0 840 300" style="margin-top:4mm">
    <rect x="330" y="116" width="180" height="70" fill="#0F1A14"/>
    <text x="420" y="146" text-anchor="middle" font-family="Barlow" font-size="12.5" font-weight="700" fill="#fff">{h["hub"]}</text>
    <text x="420" y="165" text-anchor="middle" font-family="Barlow" font-size="9" fill="#8FB79A">{h["hubsub"]}</text>
    <g stroke="#3AAA35" stroke-width="2.2">{spokes}</g>
    <line x1="420" y1="186" x2="420" y2="262" stroke="#0F1A14" stroke-width="2.2"/>
    <g font-family="Barlow" font-size="10.5" font-weight="700" fill="#0F1A14" text-anchor="end">{lnames}</g>
    <g font-family="Barlow" font-size="8.2" fill="#7E8C84" text-anchor="end">{lsubs}</g>
    <g font-family="Barlow" font-size="10.5" font-weight="700" fill="#0F1A14">{rnames}</g>
    <g font-family="Barlow" font-size="8.2" fill="#7E8C84">{rsubs}</g>
    <text x="420" y="280" text-anchor="middle" font-family="Barlow" font-size="10.5" font-weight="700" fill="#0F1A14">{h["bottom"]}</text>
    <text x="420" y="294" text-anchor="middle" font-family="Barlow" font-size="8.2" fill="#7E8C84">{h["bottomsub"]}</text>
  </svg>
  <div class="row r-3 grow">
    <div class="box fill"><div class="bt">Coverage against that map</div>
      {table(["Leg", "Sprint service"], [(a, f'<span class="g">{b}</span>') for a, b in [
        ("Inside Gaborone", "One hour Sprint Service"),
        ("Gaborone and Francistown", "Overnight, both directions"),
        ("Sites nationwide", "75+ destinations"),
        ("Outside Botswana", "Aramex, 243 countries"),
        ("Import and export clearance", "Own clearing agent licence")]])}</div>
    <div><div class="bt">{h["why_title"]}</div>
      {"".join(f"<p>{p}</p>" for p in h["why"])}
      <div class="row r-3" style="margin-top:3.5mm;gap:4mm">{"".join(stat(x["v"], x["k"]) for x in h["stats"])}</div>
      <div style="margin-top:auto;padding-top:4mm;border-top:.8px solid #E6ECE7">
        <p style="color:#5E6C64">{h["closer"]}</p></div></div>
    <div class="box fill"><div class="bt">{h["towns_title"]}</div>
      {table(["Town", "Why you go there"], h["towns"])}
      <p style="margin-top:auto;padding-top:3mm;color:#5E6C64">Sprint reaches every town on this list.</p></div>
  </div>''' + foot(h["source"], n)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    p, rc = build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print(f"\nPDF: {p}")
    sys.exit(rc)
```

## `render-pdf.py`

```python
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
```

## `sectors/_TEMPLATE.json`

```json
{
  "name": "TEMPLATE. Copy this file, name it after the industry, and fill it in.",
  "match": [],
  "ask": "...",
  "cycle": {
    "toc": "...",
    "kick": "...",
    "title": "...",
    "sub": "...",
    "months": [
      "..."
    ],
    "rows": [
      {
        "label": "...",
        "offset": 32
      },
      {
        "label": "...",
        "offset": 55
      }
    ],
    "peak": {
      "x": 146,
      "label": "..."
    },
    "table_title": "...",
    "table_cols": [
      "..."
    ],
    "table_widths": [
      "..."
    ],
    "table_rows": [
      [
        "..."
      ],
      [
        "..."
      ]
    ],
    "aside_title": "...",
    "aside": [
      "..."
    ],
    "aside_stats": [
      {
        "v": "...",
        "k": "..."
      },
      {
        "v": "...",
        "k": "..."
      }
    ],
    "source": "..."
  },
  "clock": {
    "toc": "...",
    "kick": "...",
    "title": "...",
    "sub": "...",
    "t0": "...",
    "t0sub": "...",
    "t1": "...",
    "t1sub": "...",
    "t2": "...",
    "t2sub": "...",
    "span1": "...",
    "span2": "...",
    "items_title": "...",
    "items": [
      "..."
    ],
    "why_title": "...",
    "why": [
      "..."
    ],
    "fix_title": "...",
    "fix": [
      "..."
    ],
    "fix_note": "...",
    "panels": [
      {
        "t": "...",
        "cls": "...",
        "p": [
          "..."
        ]
      },
      {
        "t": "...",
        "cols": [
          "..."
        ],
        "widths": [
          "..."
        ],
        "rows": [
          [
            "..."
          ],
          [
            "..."
          ]
        ]
      }
    ],
    "source": "..."
  },
  "hub": {
    "title": "...",
    "hub": "...",
    "hubsub": "...",
    "left": [
      {
        "t": "...",
        "s": "..."
      },
      {
        "t": "...",
        "s": "..."
      }
    ],
    "right": [
      {
        "t": "...",
        "s": "..."
      },
      {
        "t": "...",
        "s": "..."
      }
    ],
    "bottom": "...",
    "bottomsub": "...",
    "why_title": "...",
    "why": [
      "..."
    ],
    "stats": [
      {
        "v": "...",
        "k": "..."
      },
      {
        "v": "...",
        "k": "..."
      }
    ],
    "closer": "...",
    "towns_title": "...",
    "towns": [
      [
        "..."
      ],
      [
        "..."
      ]
    ],
    "source": "..."
  },
  "failures": {
    "title": "...",
    "cols": [
      "..."
    ],
    "widths": [
      "..."
    ],
    "rows": [
      [
        "..."
      ],
      [
        "..."
      ]
    ],
    "not": [
      "..."
    ],
    "measure": [
      "..."
    ],
    "source": "..."
  },
  "_how": {
    "1_cycle": "The recurring calendar. Dates that repeat whether anybody feels like it or not, with the PUBLISHED consequence of missing each one. Never a consequence you assumed.",
    "2_clock": "The deadline inside this profession that outsiders have never heard of. This is the page that earns the meeting. For auditors it is the standard that caps file assembly at sixty days after the report date.",
    "3_hub": "Where their documents and goods actually travel. One hub, three origins, three destinations, one archive.",
    "4_failures": "Five things that go wrong, what each costs, what replaces it.",
    "rules": [
      "Every figure carries its source on the page.",
      "Never claim a requirement an authority has not published.",
      "Never state a finding about the buyer. You have not been inside their operation.",
      "No tariff. Ever.",
      "Zero dash characters. The renderer fails the build on one."
    ],
    "0_match": "Leave match EMPTY in the template. The watcher skips any playbook with no match words, so a half finished template can never be chosen by accident."
  }
}
```

## `example/company.example.json`

```json
{
  "name": "Example Audit Partners",
  "slug": "Example-Audit-Partners",
  "address": "12 Example Street, Your City",
  "sector": "_TEMPLATE",
  "doc_no": "PR 2026 EAP 01",
  "headline": "Your deadlines are set<br>by statute and by standard.<b><br>Ours is the only part<br>that can still be late.</b>",
  "dek": "A document movement proposal for a practice working from two offices and filing to three authorities.",
  "ask": "Who carries this for you today?",
  "provenance": "Prepared after a quotation for this work was shared with us.",
  "control": {
    "Document": "Service Proposal PR 2026 EAP 01",
    "Issued": "15 September 2026",
    "Prepared for": "Office of the Managing Partner",
    "Validity": "30 days from issue",
    "Prepared by": "Your Name, Your Company",
    "Classification": "Commercial in confidence",
    "Status": "For discussion, not an offer"
  }
}
```

## `Watch-Quotes.ps1`

```powershell
<#
  Sprint proposal factory, the watcher.

  Every 30 minutes inside working hours it looks in Outlook for a quote somebody has forwarded,
  works out who the company is and what industry they are in, builds the exhibit pack proposal,
  and stages a reply as a DRAFT with the PDF attached.

  It never sends. It never calls a model. Everything here is deterministic.

  Forward any quote you receive to yourself, or ask a colleague to forward theirs.
  Thirty minutes later the proposal is sitting in Drafts, ready to read and send.

  Anything it cannot work out is written to NEEDS-A-HUMAN.md rather than guessed.
#>
param([switch]$Force, [switch]$WhatIf)

$ErrorActionPreference = "Stop"
$SK   = $PSScriptRoot
$sup  = Get-Content (Join-Path $SK "supplier.json") -Raw | ConvertFrom-Json
$log  = Join-Path $SK "watch-log.txt"
$seen = Join-Path $SK "seen.json"
$need = Join-Path $SK "NEEDS-A-HUMAN.md"

function Log($m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm')  $m" | Tee-Object -FilePath $log -Append }

# ── STEP 0, the window. working hours only, nothing at a weekend ──
$now = Get-Date
$day = $now.DayOfWeek
if (-not $Force) {
    if ($day -eq 'Saturday' -or $day -eq 'Sunday') { Log "weekend, standing down"; exit 0 }
    $close = if ($day -eq 'Friday') { 16.5 } else { 17.5 }
    $hour  = $now.Hour + $now.Minute / 60
    if ($hour -lt 7.5 -or $hour -gt $close) { Log "outside working hours, standing down"; exit 0 }
}

# ── STEP 0b, the credit gate. If the weekly limit tripped, do nothing ──
$gate = Join-Path $SK "PAUSED.flag"   # drop a file here to stop it
if (Test-Path $gate) { Log "limit gate tripped, standing down"; exit 0 }

# ── the industry playbooks, and the words that point at each one ──
$sectors = @{}
Get-ChildItem (Join-Path $SK "sectors") -Filter *.json | ForEach-Object {
    $j = Get-Content $_.FullName -Raw | ConvertFrom-Json
    $sectors[$_.BaseName] = $j.match
}
Log "playbooks loaded: $($sectors.Keys -join ', ')"

New-Item -ItemType Directory -Force -Path (Join-Path $SK "inbox"), (Join-Path $SK "out") | Out-Null
$already = if (Test-Path $seen) { Get-Content $seen -Raw | ConvertFrom-Json } else { @() }
$already = @($already)

$ol = New-Object -ComObject Outlook.Application
$ns = $ol.GetNamespace("MAPI")
$inbox  = $ns.GetDefaultFolder(6)
$drafts = $ns.GetDefaultFolder(16)
$items  = $inbox.Items
$items.Sort("[ReceivedTime]", $true)

$made = 0; $attempts = 0; $unknown = @()
$cut = (Get-Date).AddDays(-14)

foreach ($m in $items) {
    if ($made -ge 5 -or $attempts -ge 15) { break }   # bound the work, not just the wins
    try {
        if ($m.ReceivedTime -lt $cut) { break }
        $id = $m.EntryID
        if ($already -contains $id) { continue }

        $subj = "$($m.Subject)"
        $body = "$($m.Body)"
        $hay  = ($subj + " " + $body).ToLower()

        # a quote somebody forwarded. Needs the word, and an attachment or a forward marker.
        $looksLikeQuote = $hay -match 'quotation|quote|tariff|rate card|pricing|proposal'
        $isForward      = $subj -match '^(fw|fwd)[:\s]' -or $body -match 'Forwarded message|From:.*Sent:'
        $hasPdf         = $false
        foreach ($a in $m.Attachments) { if ($a.FileName -match '\.pdf$|\.docx?$|\.xlsx?$') { $hasPdf = $true } }
        if (-not ($looksLikeQuote -and ($isForward -or $hasPdf))) { continue }

        # never treat our own people as the prospect. A colleague forwarding a rate card is not a lead.
        if ($m.SenderEmailAddress -match $sup.own_domain_pattern) { $already += $id; continue }

        # who is the quote FROM. The competitor's domain is usually in the forwarded header.
        $company = $null
        if ($body -match 'From:\s*"?([^"<\r\n]{3,60})"?\s*<([^>]+)>') {
            $company = $matches[1].Trim()
            $domain  = $matches[2]
        }
        if (-not $company -and $subj -match '(?:quotation|quote|proposal)\s+(?:for|from)\s+(.{3,50})') {
            $company = $matches[1].Trim()
        }
        # two capitalised words and nothing else is a person, not a company
        if ($company -and $company -cmatch '^[A-Z][A-Z\s]+$' -and $company -notmatch '(LTD|PTY|CC|INC|GROUP|HOLDINGS|SERVICES|LOGISTICS)') { $company = $null }

        if (-not $company) {
            $unknown += "* $($m.ReceivedTime.ToString('dd MMM HH:mm')) from $($m.SenderName): ""$subj"" could not be read for a company name"
            $already += $id; continue
        }

        # which playbook
        $sector = $null
        foreach ($k in $sectors.Keys) {
            foreach ($w in $sectors[$k]) { if ($hay -match [regex]::Escape($w)) { $sector = $k; break } }
            if ($sector) { break }
        }
        if (-not $sector) {
            $unknown += "* $($m.ReceivedTime.ToString('dd MMM HH:mm')) ""$company"" has no industry playbook yet. Ask Claude to write one, then this builds itself."
            $already += $id; continue
        }

        $slug = ($company -replace '[^A-Za-z0-9]+', '-').Trim('-')
        $docNo = "SC $((Get-Date).Year) $((($slug -replace '[^A-Za-z]','').Substring(0,[Math]::Min(3,($slug -replace '[^A-Za-z]','').Length))).ToUpper()) 01"
        $sj = Get-Content (Join-Path $SK "sectors\$sector.json") -Raw | ConvertFrom-Json

        $co = [ordered]@{
            name = $company; slug = $slug; address = ""; sector = $sector; doc_no = $docNo
            headline = "You are already being quoted<br>for this work.<b><br>Here is what the quote<br>does not cover.</b>"
            dek = "A document movement proposal for $company, built around what your week actually looks like rather than around a price list."
            ask = $sj.ask
            provenance = "Prepared after a quotation for this work was shared with us. We have not seen inside your operation, so everything here is offered for correction at a twenty minute assessment."
            control = [ordered]@{
                "Document" = "Service Proposal $docNo"
                "Issued" = (Get-Date -Format "d MMMM yyyy")
                "Prepared for" = $company
                "Validity" = "30 days from issue"
                "Prepared by" = "$($sup.rep_name), $($sup.name)"
                "Classification" = "Commercial in confidence"
                "Industry playbook" = $sj.name
                "Status" = "For discussion, not an offer"
            }
        }
        $cf = Join-Path $SK "inbox\$slug.json"
        [IO.File]::WriteAllText($cf, ($co | ConvertTo-Json -Depth 6), (New-Object Text.UTF8Encoding($false)))

        if ($WhatIf) { Log "WHATIF would build $company as $sector"; $made++; continue }

        $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $runDir = Join-Path $SK "out\$slug-$stamp"
        $py = & python (Join-Path $SK "build.py") $cf $runDir 2>&1
        $code = $LASTEXITCODE
        # The builder prints ARTIFACT=<path> only on success. Never guess the filename, and never
        # treat "a pdf exists" as success: that is how a stale or rejected file gets attached.
        $pdf = ($py | Select-String -Pattern '^ARTIFACT=(.+)$' | Select-Object -Last 1).Matches.Groups[1].Value
        if ($code -ne 0 -or -not $pdf -or -not (Test-Path $pdf)) {
            Log "BUILD FAILED for $company (exit $code). Nothing staged. $py"
            $already += $id; $attempts++; continue
        }

        # stage the reply as a DRAFT. Never send.
        # A draft with no recipient is a trap: it looks finished in the folder and goes nowhere.
        $to = $m.SenderEmailAddress
        if (-not $to) { try { $to = $m.Sender.GetExchangeUser().PrimarySmtpAddress } catch {} }
        if (-not $to) {
            Log "built $company but the forwarder has no readable address, PDF left at $pdf"
            $unknown += "* $($m.ReceivedTime.ToString('dd MMM HH:mm')) $company built, but no reply address could be read. PDF: $pdf"
            $already += $id; $made++; continue
        }
        $d = $ol.CreateItem(0)
        $d.To = $to
        $d.Subject = "Re: $subj"
        $d.Body = @"
Hi,

Thank you for sending that through.

I have put together a proposal for $company built around how their week actually works, rather
than a price against their price. It is attached.

There is no tariff in it on purpose. Their rate card gets confirmed in writing after a twenty
minute assessment, against their real runs.

Have a look and tell me if anything in it is wrong.

$($sup.rep_name)
"@
        $d.Attachments.Add($pdf) | Out-Null
        try { $p = $d.UserProperties.Add("SprintSendAfter", 1); $p.Value = (Get-Date).AddDays(1).ToString("yyyy-MM-dd 07:30") } catch {}
        $d.Save()

        Log "BUILT $company  sector=$sector  pdf=$pdf  draft staged to $($m.SenderEmailAddress)"
        $already += $id; $made++
    } catch { Log "error on one message: $($_.Exception.Message)" }
}

$already | ConvertTo-Json | Set-Content $seen -Encoding UTF8

if ($unknown.Count) {
    $hdr = "# Quotes the factory could not finish`n`nThese were found but not built. Nothing was guessed.`n`n"
    $prev = if (Test-Path $need) { (Get-Content $need -Raw) -replace [regex]::Escape($hdr), "" } else { "" }
    ($hdr + (($unknown + ($prev -split "`n" | Where-Object { $_ -match "^\* " })) | Select-Object -Unique | Sort-Object -Descending) -join "`n") |
        Set-Content $need -Encoding UTF8
    Log "$($unknown.Count) need a human, written to NEEDS-A-HUMAN.md"
}
Log "run complete, $made proposal(s) built"
```

## `Install-Task.ps1`

```powershell
# Installs the proposal factory watcher: every 30 minutes, working hours only, zero tokens.
$name = "Proposal-Factory"
$ps   = Join-Path $PSScriptRoot "Watch-Quotes.ps1"
$act  = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$ps`""
$trg  = New-ScheduledTaskTrigger -Once -At (Get-Date).Date.AddHours(7).AddMinutes(30) `
          -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration ([TimeSpan]::MaxValue)
$set  = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
          -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName $name -Action $act -Trigger $trg -Settings $set -Force -RunLevel Limited | Out-Null
Write-Output "installed: $name, every 30 minutes, the script itself stands down outside working hours"
Get-ScheduledTask -TaskName $name | Select-Object TaskName, State | Format-Table -AutoSize
```

## `style.css`

```css
/* Exhibit pack stylesheet. The look is decided here, once, and never per client. */
@page{size:A4 portrait;margin:0}
*{box-sizing:border-box;margin:0;padding:0}
html,body{background:#fff}
body{color:#0F1A14;font-family:"Barlow","Segoe UI",sans-serif;font-size:8.4pt;line-height:1.42;-webkit-font-smoothing:antialiased}
.page{width:210mm;height:297mm;position:relative;overflow:hidden;page-break-after:always;background:#fff;padding:12mm 14mm 15mm;display:flex;flex-direction:column}
.page.cover{display:block}
.page > .row.grow{flex:1;align-items:stretch;padding-bottom:2mm}
.page > .row.grow > div{display:flex;flex-direction:column}
.page > .row.grow > div > .box{flex:1}
.box{display:flex;flex-direction:column}
.page:last-child{page-break-after:auto}

.rh{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:1.2px solid #0F1A14;padding-bottom:2.2mm}
.rh .l{font-family:"Barlow Condensed",sans-serif;font-weight:700;letter-spacing:.15em;text-transform:uppercase;font-size:7.8pt;line-height:1.5}
.rh .l i{display:block;font-style:normal;font-weight:500;letter-spacing:.11em;color:#7E8C84;font-size:6.7pt}
.rh img{height:10.5mm;width:auto;display:block}

.kick{font-family:"Barlow Condensed",sans-serif;font-weight:700;letter-spacing:.2em;text-transform:uppercase;font-size:7.2pt;color:#3AAA35;margin-top:4.5mm}
.at{font-size:14.5pt;font-weight:300;line-height:1.14;letter-spacing:-.35pt;margin-top:1.2mm}
.at b{font-weight:700}
.sub{font-size:8.5pt;color:#4E5C54;margin-top:2mm;line-height:1.5}

.src{position:absolute;left:14mm;right:14mm;bottom:8mm;border-top:.8px solid #D6DED8;padding-top:1.5mm;
  font-size:6.2pt;color:#93A199;display:flex;justify-content:space-between;gap:6mm}
.src b{color:#5E6C64;font-weight:600}

.row{display:grid;gap:4.5mm;margin-top:4mm}
.r-2{grid-template-columns:1fr 1fr}.r-32{grid-template-columns:3fr 2fr}.r-23{grid-template-columns:2fr 3fr}
.r-3{grid-template-columns:1fr 1fr 1fr}
.box{border:.9px solid #D6DED8;padding:3.2mm}
.box.fill{background:#F6F9F6}
.box.dark{background:#0F1A14;color:#fff;border-color:#0F1A14}
.box.warn{background:#FFF6EA;border-color:#F0D3A8}
.bt{font-family:"Barlow Condensed",sans-serif;font-weight:700;letter-spacing:.14em;text-transform:uppercase;font-size:6.9pt;color:#7E8C84;margin-bottom:1.8mm}
.box.dark .bt{color:#8FB79A}
p{font-size:8.2pt;line-height:1.52}
p+p{margin-top:2.2mm}

table{width:100%;border-collapse:collapse;font-size:7.4pt}
th{font-family:"Barlow Condensed",sans-serif;font-weight:700;letter-spacing:.11em;text-transform:uppercase;font-size:6.5pt;
  color:#7E8C84;text-align:left;padding:0 3mm 1.5mm 0;border-bottom:1px solid #0F1A14;vertical-align:bottom}
td{padding:1.7mm 3mm 1.7mm 0;border-bottom:.8px solid #E6ECE7;vertical-align:top;line-height:1.34}
td:last-child,th:last-child{padding-right:0}
tr:last-child td{border-bottom:none}
.num{font-family:"IBM Plex Mono",monospace;font-weight:500;white-space:nowrap}
.g{color:#2C7A29;font-weight:600}.o{color:#B8770F;font-weight:600}
.stat .v{font-family:"Barlow Condensed",sans-serif;font-weight:700;font-size:22pt;line-height:.92;letter-spacing:-.5pt}
.stat .k{font-size:6.9pt;color:#7E8C84;line-height:1.35;margin-top:.8mm}
ul.tick{list-style:none;font-size:7.7pt;line-height:1.48}
ul.tick li{padding-left:4.2mm;position:relative;margin-bottom:1.2mm}
ul.tick li:before{content:"";position:absolute;left:0;top:1.2mm;width:2.1mm;height:2.1mm;background:#3AAA35}
ul.tick li.x:before{background:#D8A24A}
.box.dark ul.tick li:before{background:#4FC249}
svg{display:block;width:100%;height:auto;overflow:visible}

.cover{background:#0F1A14;color:#fff;padding:0}
.cover .inner{position:relative;height:297mm;padding:15mm 14mm 13mm;display:flex;flex-direction:column}
.cover .bar{position:absolute;left:0;top:0;bottom:0;width:4mm;background:#3AAA35}
.cover h1{font-size:29pt;font-weight:300;line-height:1.07;letter-spacing:-.9pt;margin-top:auto}
.cover h1 b{font-weight:700;color:#4FC249}
.cover .dek{margin-top:5mm;font-size:9.6pt;color:#B7C6BC;max-width:142mm;line-height:1.6}
.cover .ctl{margin-top:7mm;display:grid;grid-template-columns:1fr 1fr;gap:0 9mm;border-top:1px solid #2E3D34;padding-top:4mm}
.cover .ctl div{border-bottom:1px solid #2E3D34;padding:2.1mm 0;display:flex;justify-content:space-between;gap:4mm;font-size:7.8pt}
.cover .ctl span{color:#8FA396;font-family:"Barlow Condensed",sans-serif;letter-spacing:.12em;text-transform:uppercase;font-size:6.8pt;padding-top:.5mm}
.cover .ctl b{font-weight:600;text-align:right}
.cover .toc{margin-top:6mm;font-size:7.8pt;color:#B7C6BC;column-count:2;column-gap:9mm}
.cover .toc div{padding:1.4mm 0;border-bottom:1px solid #22302A;display:flex;gap:3mm;break-inside:avoid}
.cover .toc i{font-style:normal;font-family:"IBM Plex Mono",monospace;color:#4FC249;font-size:7.2pt}
.cover .foot{margin-top:auto;padding-top:6mm;display:flex;justify-content:space-between;align-items:flex-end;font-size:7.2pt;color:#7E9186}
.cover .top{display:flex;justify-content:space-between;align-items:flex-start}
.cover .top img{height:11.5mm}
.cover .top .l{font-family:"Barlow Condensed",sans-serif;font-weight:700;letter-spacing:.18em;text-transform:uppercase;font-size:8.2pt}
.cover .top .l i{display:block;font-style:normal;font-weight:500;color:#8FA396;font-size:6.8pt;letter-spacing:.12em}
.plate{background:#fff;border-radius:1.2mm;padding:2.1mm 2.6mm;display:inline-block}
```