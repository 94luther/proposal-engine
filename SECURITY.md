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
