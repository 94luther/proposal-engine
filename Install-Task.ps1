# Installs the proposal factory watcher: every 30 minutes, working hours only, zero tokens.
$name = "Proposal-Factory"
$ps   = Join-Path $PSScriptRoot "Watch-Quotes.ps1"
$act  = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$ps`""
$trg  = New-ScheduledTaskTrigger -Once -At (Get-Date).Date.AddHours(7).AddMinutes(30) `
          -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration (New-TimeSpan -Hours 23)
$set  = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
          -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 10) -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName $name -Action $act -Trigger $trg -Settings $set -Force -RunLevel Limited | Out-Null
Write-Output "installed: $name, every 30 minutes, the script itself stands down outside working hours"
Get-ScheduledTask -TaskName $name | Select-Object TaskName, State | Format-Table -AutoSize
