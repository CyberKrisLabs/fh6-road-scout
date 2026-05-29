#Requires -Version 5.1
<#
.SYNOPSIS
    Bulk-creates GitHub issues from the Horizon Scout phase .md files.

.DESCRIPTION
    Reads every .md file in the target phase directory (or all phases), parses the
    YAML frontmatter (title, labels, milestone), and creates a GitHub issue for each
    one using the gh CLI. Milestones and labels are created automatically if missing.

.PARAMETER Repo
    GitHub repository in owner/name format (e.g. "CyberKrisLabs/fh6-road-scout").

.PARAMETER Phase
    Phase directory name to upload, or "all" to upload every phase.
    Valid values: all, phase-1-scaffold-ui-shell, phase-2-road-sampler,
                  phase-3-calibration, phase-4-scanner-engine,
                  phase-5-results-export, phase-6-polish-packaging

.PARAMETER DryRun
    Print what would be created without actually calling gh.

.EXAMPLE
    .\create-issues.ps1 -Repo "CyberKrisLabs/fh6-road-scout" -Phase "phase-1-scaffold-ui-shell"
    .\create-issues.ps1 -Repo "CyberKrisLabs/fh6-road-scout" -Phase all
    .\create-issues.ps1 -Repo "CyberKrisLabs/fh6-road-scout" -Phase all -DryRun
#>

param(
    [Parameter(Mandatory)]
    [string]$Repo,

    [Parameter(Mandatory)]
    [ValidateSet(
        'all',
        'phase-1-scaffold-ui-shell',
        'phase-2-road-sampler',
        'phase-3-calibration',
        'phase-4-scanner-engine',
        'phase-5-results-export',
        'phase-6-polish-packaging'
    )]
    [string]$Phase,

    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    Write-Error 'gh CLI not found. Install from https://cli.github.com/'
    exit 1
}

gh auth status | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Error 'gh is not authenticated. Run: gh auth login'
    exit 1
}

$baseDir = $PSScriptRoot

$allPhases = @(
    'phase-1-scaffold-ui-shell',
    'phase-2-road-sampler',
    'phase-3-calibration',
    'phase-4-scanner-engine',
    'phase-5-results-export',
    'phase-6-polish-packaging'
)

$targetPhases = if ($Phase -eq 'all') { $allPhases } else { @($Phase) }

function Ensure-Milestone {
    param([string]$MilestoneRepo, [string]$MilestoneTitle)
    $json = gh api "repos/$MilestoneRepo/milestones"
    $milestones = $json | ConvertFrom-Json
    $match = $milestones | Where-Object { $_.title -eq $MilestoneTitle } | Select-Object -First 1
    if ($match) { return }
    Write-Host "    Creating milestone: $MilestoneTitle" -ForegroundColor Yellow
    if (-not $DryRun) {
        gh api "repos/$MilestoneRepo/milestones" -X POST -f "title=$MilestoneTitle" | Out-Null
    }
}

function Ensure-Labels {
    param([string]$LabelRepo, [string[]]$Labels)
    $json = gh api "repos/$LabelRepo/labels?per_page=100"
    $existing = ($json | ConvertFrom-Json) | Select-Object -ExpandProperty name
    foreach ($label in $Labels) {
        if ($existing -notcontains $label) {
            Write-Host "    Creating label: $label" -ForegroundColor Yellow
            if (-not $DryRun) {
                gh api "repos/$LabelRepo/labels" -X POST -f "name=$label" -f 'color=0075ca' | Out-Null
            }
        }
    }
}

function Parse-Frontmatter {
    param([string]$Content)
    $result = @{ Title = ''; Labels = @(); Milestone = ''; Body = '' }

    if (-not $Content.StartsWith('---')) {
        $result.Body = $Content
        return $result
    }

    $lines = $Content -split "`n"
    $fmEnd = -1
    for ($i = 1; $i -lt $lines.Count; $i++) {
        if ($lines[$i].TrimEnd() -eq '---') {
            $fmEnd = $i
            break
        }
    }

    if ($fmEnd -eq -1) {
        $result.Body = $Content
        return $result
    }

    $fmLines = $lines[1..($fmEnd - 1)]
    $bodyLines = $lines[($fmEnd + 1)..($lines.Count - 1)]
    $result.Body = ($bodyLines -join "`n").Trim()

    foreach ($line in $fmLines) {
        if ($line -match '^title:\s*"(.+)"') {
            $result.Title = $Matches[1]
        }
        elseif ($line -match '^milestone:\s*"(.+)"') {
            $result.Milestone = $Matches[1]
        }
        elseif ($line -match '^labels:\s*\[(.+)\]') {
            $labelMatches = [regex]::Matches($Matches[1], '"([^"]+)"')
            foreach ($m in $labelMatches) { $result.Labels += $m.Groups[1].Value }
        }
        elseif ($line -match '^\s*-\s*"(.+)"') {
            $result.Labels += $Matches[1]
        }
    }

    return $result
}

$totalCreated = 0
$totalFailed = 0
$ensuredMilestones = @{}

foreach ($phaseName in $targetPhases) {
    $phaseDir = Join-Path $baseDir $phaseName

    if (-not (Test-Path $phaseDir)) {
        Write-Warning "Phase directory not found, skipping: $phaseDir"
        continue
    }

    $issueFiles = Get-ChildItem -Path $phaseDir -Filter '*.md' | Sort-Object Name

    if ($issueFiles.Count -eq 0) {
        Write-Warning "No .md files in $phaseName - skipping"
        continue
    }

    $issueCount = $issueFiles.Count
    Write-Host ''
    Write-Host "=== $phaseName - $issueCount issues ===" -ForegroundColor Cyan

    foreach ($file in $issueFiles) {
        $content = Get-Content $file.FullName -Raw -Encoding UTF8
        $parsed = Parse-Frontmatter -Content $content

        if (-not $parsed.Title) {
            Write-Warning "Skipping $($file.Name): no title in frontmatter"
            continue
        }

        Write-Host "`n  [$($file.Name)]" -ForegroundColor White
        Write-Host "    Title:     $($parsed.Title)"
        Write-Host "    Labels:    $($parsed.Labels -join ', ')"
        Write-Host "    Milestone: $($parsed.Milestone)"

        if ($DryRun) {
            Write-Host '    [DRY RUN] Would create issue' -ForegroundColor DarkGray
            continue
        }

        try {
            if ($parsed.Labels.Count -gt 0) {
                Ensure-Labels -LabelRepo $Repo -Labels $parsed.Labels
            }

            if ($parsed.Milestone -and -not $ensuredMilestones.ContainsKey($parsed.Milestone)) {
                Ensure-Milestone -MilestoneRepo $Repo -MilestoneTitle $parsed.Milestone
                $ensuredMilestones[$parsed.Milestone] = $true
            }

            $tempFile = [System.IO.Path]::GetTempFileName()
            try {
                [System.IO.File]::WriteAllText($tempFile, $parsed.Body, [System.Text.Encoding]::UTF8)

                $ghArgs = [System.Collections.Generic.List[string]]@(
                    'issue', 'create',
                    '--repo', $Repo,
                    '--title', $parsed.Title,
                    '--body-file', $tempFile
                )
                foreach ($label in $parsed.Labels) {
                    $ghArgs.Add('--label')
                    $ghArgs.Add($label)
                }
                if ($parsed.Milestone) {
                    $ghArgs.Add('--milestone')
                    $ghArgs.Add($parsed.Milestone)
                }

                $issueUrl = & gh @ghArgs
                Write-Host "    Created: $issueUrl" -ForegroundColor Green
                $totalCreated++
            }
            finally {
                Remove-Item $tempFile -Force -ErrorAction SilentlyContinue
            }
        }
        catch {
            Write-Host "    FAILED: $_" -ForegroundColor Red
            $totalFailed++
        }
    }
}

Write-Host ''
Write-Host '--- Summary ---' -ForegroundColor Cyan
Write-Host "Created : $totalCreated" -ForegroundColor Green
if ($totalFailed -gt 0) {
    Write-Host "Failed  : $totalFailed" -ForegroundColor Red
}
Write-Host "Total   : $($totalCreated + $totalFailed)"
