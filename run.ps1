<#
Run the app loading environment variables from a local `.env` file (if present).

Usage (PowerShell):
  .\run.ps1

This script reads `.env` lines like `KEY=VALUE` and sets them into the process
environment before launching `python app.py`.
#>

$envFile = Join-Path $PSScriptRoot '.env'
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^[\s#]') { return }
        if ($_ -match '^\s*$') { return }
        $parts = $_ -split '=', 2
        if ($parts.Count -eq 2) {
            $k = $parts[0].Trim()
            $v = $parts[1].Trim()
            if ($v.StartsWith('"') -and $v.EndsWith('"')) { $v = $v.Trim('"') }
            if ($v.StartsWith("'") -and $v.EndsWith("'")) { $v = $v.Trim("'") }
            $env:$k = $v
        }
    }
}

python app.py
