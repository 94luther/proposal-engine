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

$already = if (Test-Path $seen) { Get-Content $seen -Raw | ConvertFrom-Json } else { @() }
$already = @($already)

$ol = New-Object -ComObject Outlook.Application
$ns = $ol.GetNamespace("MAPI")
$inbox  = $ns.GetDefaultFolder(6)
$drafts = $ns.GetDefaultFolder(16)
$items  = $inbox.Items
$items.Sort("[ReceivedTime]", $true)

$made = 0; $unknown = @()
$cut = (Get-Date).AddDays(-14)

foreach ($m in $items) {
    if ($made -ge 5) { break }
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
        $co | ConvertTo-Json -Depth 6 | Set-Content $cf -Encoding UTF8

        if ($WhatIf) { Log "WHATIF would build $company as $sector"; $already += $id; $made++; continue }

        $py = & python (Join-Path $SK "build.py") $cf 2>&1
        $pdf = Join-Path $SK "out\$slug\Sprint-Couriers-$slug.pdf"
        if (-not (Test-Path $pdf)) { Log "BUILD FAILED for $company : $py"; $already += $id; continue }

        # stage the reply as a DRAFT. Never send.
        $d = $ol.CreateItem(0)
        $d.To = $m.SenderEmailAddress
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
    ($hdr + ($unknown -join "`n")) | Set-Content $need -Encoding UTF8
    Log "$($unknown.Count) need a human, written to NEEDS-A-HUMAN.md"
}
Log "run complete, $made proposal(s) built"
