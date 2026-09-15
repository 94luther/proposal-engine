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
