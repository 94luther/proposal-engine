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
