param([string]$File = "output/BasicModular.ldr")
$f = Get-Content $File
$parts = @($f | Where-Object { $_ -match '^1\s' })
$files = @($f | Where-Object { $_ -match '^0 FILE' })
$nofiles = @($f | Where-Object { $_ -match '^0 NOFILE' })
$steps = @($f | Where-Object { $_ -match '^0 STEP' })
Write-Host "=== Validation: $File ==="
Write-Host "Lines: $($f.Count)"
Write-Host "Parts: $($parts.Count)"
Write-Host "Submodels: $($files.Count) FILE / $($nofiles.Count) NOFILE $(if($files.Count -eq $nofiles.Count){'PASS'}else{'FAIL'})"
Write-Host "STEP markers: $($steps.Count)"
$partNames = $parts | ForEach-Object { ($_ -split '\s+')[-1] } | Sort-Object -Unique
Write-Host "Unique parts ($($partNames.Count)): $($partNames -join ', ')"
$colors = $parts | ForEach-Object { ($_ -split '\s+')[1] } | Sort-Object -Unique
Write-Host "Unique colors ($($colors.Count)): $($colors -join ', ')"
$ys = $parts | ForEach-Object { [double]($_ -split '\s+')[3] }
$yStats = $ys | Measure-Object -Min -Max
Write-Host "Y range: $($yStats.Minimum) to $($yStats.Maximum)"
$badRefs = @($parts | Where-Object { $_ -notmatch '\.dat$' -and $_ -notmatch '\.ldr$' })
Write-Host "Bad part refs: $($badRefs.Count) $(if($badRefs.Count -eq 0){'PASS'}else{'FAIL'})"
