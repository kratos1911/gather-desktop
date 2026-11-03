param([string]$Account, [switch]$Upload, [switch]$Library, [switch]$Pdf, [switch]$Recovery, [switch]$Performance, [switch]$Docx, [switch]$DocxCompat)
$ErrorActionPreference = 'Stop'
if (([int]$Library.IsPresent+[int]$Pdf.IsPresent+[int]$Recovery.IsPresent+[int]$Performance.IsPresent+[int]$Docx.IsPresent+[int]$DocxCompat.IsPresent) -gt 1) { throw 'Choose one image variant.' }
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$registry = 'asia-south1-docker.pkg.dev'
$project = 'gather-development-511211'
$sourceImage = 'gather-inference:pilot-configured'
$targetImage = "$registry/$project/gather-pilot-images/inference:pilot-20261021"
$expected = (Get-Content -Raw -LiteralPath (Join-Path $repoRoot 'tests/inference/results/pilot-configured-20261021.json') | ConvertFrom-Json).image
if ($Library) {
    $sourceImage='gather-library:pilot-candidate'
    $targetImage="$registry/$project/gather-pilot-images/library:pilot-20261031"
    $expected=(Get-Content -Raw -LiteralPath (Join-Path $repoRoot 'output/library-image/verification.json') | ConvertFrom-Json).image
}
if ($Pdf) {
    $sourceImage='gather-library:pdf-candidate'
    $targetImage="$registry/$project/gather-pilot-images/library:pdf-pilot-20261031"
    $expected=(Get-Content -Raw -LiteralPath (Join-Path $repoRoot 'output/pdf-pilot/image-verification.json') | ConvertFrom-Json).image
}
if ($Recovery) {
    $sourceImage='gather-library:recovery-candidate'
    $targetImage="$registry/$project/gather-pilot-images/library:recovery-pilot-20261031"
    $expected=(Get-Content -Raw -LiteralPath (Join-Path $repoRoot 'output/recovery-fix/image-verification.json') | ConvertFrom-Json).image
}
if ($Performance) {
    $sourceImage='gather-library:performance-candidate'
    $targetImage="$registry/$project/gather-pilot-images/library:performance-pilot-20261101"
    $expected=(Get-Content -Raw -LiteralPath (Join-Path $repoRoot 'output/processing-speed/image-verification.json') | ConvertFrom-Json).image
}
if ($Docx) {
    $sourceImage='gather-library:docx-candidate'
    $targetImage="$registry/$project/gather-pilot-images/library:docx-pilot-20261102"
    $expected=(Get-Content -Raw -LiteralPath (Join-Path $repoRoot 'output/docx-pilot/image-verification.json') | ConvertFrom-Json).image
}
if ($DocxCompat) {
    $sourceImage='gather-library:docx-compat-candidate'
    $targetImage="$registry/$project/gather-pilot-images/library:docx-compat-20261103"
    $expected=(Get-Content -Raw -LiteralPath (Join-Path $repoRoot 'output/docx-compatibility/image-verification.json') | ConvertFrom-Json).image
}
$dockerEndpoint = (& docker context inspect desktop-linux --format '{{.Endpoints.docker.Host}}').Trim()
if ($LASTEXITCODE -ne 0 -or $dockerEndpoint -ne 'npipe:////./pipe/dockerDesktopLinuxEngine') {
    throw 'Expected local Docker Desktop Linux engine; no upload attempted.'
}
$imageId = (& docker --host $dockerEndpoint image inspect $sourceImage --format '{{.Id}}').Trim()
if ($LASTEXITCODE -ne 0 -or $imageId -ne $expected) {
    throw 'Local image differs from the verified pilot candidate; no upload attempted.'
}
Write-Host "Verified image: $imageId"
Write-Host "Destination: $targetImage"
if (-not $Upload) {
    Write-Host 'Preview only. Run with -Account <personal-email> -Upload to send the image.'
    return
}
if (-not $Account -or $Account -notmatch '^[^\s@]+@[^\s@]+$') {
    throw 'Specify the signed-in personal Gather account using -Account.'
}
if (($Pdf -or $Recovery -or $Performance -or $Docx -or $DocxCompat) -and $Account -ne 'kpanigrahi5602@gmail.com') { throw 'Gather pilot upload requires the approved personal Gather account.' }
$gcloudCommand = (Get-Command gcloud.cmd -ErrorAction Stop).Source
$authRoot = Join-Path $repoRoot 'output/registry-upload-auth'
$authDirectory = Join-Path $authRoot ([guid]::NewGuid().ToString('N'))
$configFile = Join-Path $authDirectory 'config.json'
New-Item -ItemType Directory -Path $authDirectory -Force | Out-Null
$token = $null
$encoded = $null
try {
    # Only this Windows user can read the temporary access-token file.
    $sid = [System.Security.Principal.WindowsIdentity]::GetCurrent().User
    $acl = Get-Acl -LiteralPath $authDirectory
    $acl.SetAccessRuleProtection($true, $false)
    $rule = [System.Security.AccessControl.FileSystemAccessRule]::new(
        $sid, 'FullControl', 'ContainerInherit,ObjectInherit', 'None', 'Allow')
    $acl.SetAccessRule($rule)
    Set-Acl -LiteralPath $authDirectory -AclObject $acl
    $token = ((& $gcloudCommand auth print-access-token "--account=$Account" "--project=$project" --quiet) | Out-String).Trim()
    if ($LASTEXITCODE -ne 0 -or $token.Length -lt 20 -or $token.Length -gt 8192 -or $token -match '\s') {
        throw 'Could not obtain a valid short-lived access token; no upload attempted.'
    }
    $encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes('oauth2accesstoken:' + $token))
    $auths = @{}
    $auths[$registry] = @{auth=$encoded}
    $config = @{auths=$auths} | ConvertTo-Json -Depth 4
    [IO.File]::WriteAllText($configFile, $config, [Text.UTF8Encoding]::new($false))
    # Explicit engine + isolated config preserve existing account/helper settings.
    & docker --config $authDirectory --host $dockerEndpoint image tag $sourceImage $targetImage
    if ($LASTEXITCODE -ne 0) { throw 'Image tagging failed.' }
    & docker --config $authDirectory --host $dockerEndpoint push $targetImage
    if ($LASTEXITCODE -ne 0) { throw 'Push failed. Review the error before retrying.' }
    $digests = & docker --config $authDirectory --host $dockerEndpoint image inspect $targetImage --format '{{json .RepoDigests}}'
    if ($LASTEXITCODE -ne 0) { throw 'Push completed but local digest lookup failed; check the repository before retrying.' }
    $receipt = @{target=$targetImage; source_image=$imageId; registry_digests=($digests | ConvertFrom-Json)}
    $receiptPath = Join-Path $repoRoot $(if($DocxCompat){'output/docx-compatibility/upload-receipt.json'}elseif($Docx){'output/docx-pilot/upload-receipt.json'}elseif($Performance){'output/processing-speed/upload-receipt.json'}elseif($Recovery){'output/recovery-fix/upload-receipt.json'}elseif($Pdf){'output/pdf-pilot/upload-receipt.json'}elseif($Library){'output/library-upload-receipt.json'}else{'output/pilot-upload-receipt.json'})
    [IO.File]::WriteAllText($receiptPath, ($receipt | ConvertTo-Json -Depth 4), [Text.UTF8Encoding]::new($false))
    Write-Host "Upload completed. Receipt: $receiptPath"
} finally {
    $token = $null
    $encoded = $null
    $config = $null
    if (Test-Path -LiteralPath $configFile) { Remove-Item -LiteralPath $configFile -Force }
    if ((Test-Path -LiteralPath $authDirectory) -and
            @(Get-ChildItem -LiteralPath $authDirectory -Force).Count -eq 0) {
        Remove-Item -LiteralPath $authDirectory
    }
}
