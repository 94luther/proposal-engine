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
