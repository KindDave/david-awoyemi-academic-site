<#
.SYNOPSIS
  Deploy the LMS courses into the running Moodle container: brand the site, create categories,
  restore the course packages, and finish the post-import configuration.

.DESCRIPTION
  Run from anywhere after `docker compose up -d` in lms/docker has started Moodle.

    powershell -File lms/scripts/deploy_moodle.ps1                # everything, with embedded videos
    powershell -File lms/scripts/deploy_moodle.ps1 -NoMedia       # small packages, video callouts only
    powershell -File lms/scripts/deploy_moodle.ps1 -Only id-553-intro-instructional-design

  Steps per course: copy the .imscc into the container, restore it with moodle_restore_cc.php
  (Moodle's own CLI cannot restore Common Cartridge), then run moodle_admin.php postimport,
  which converts assignment pages into Assignment activities, sets quiz/forum options, enables
  self-enrolment with the key from the spec, and enrols the test student.

  Re-running restores a second copy of a course; delete the old one in Moodle first if you
  want a clean replacement.
#>
[CmdletBinding()]
param(
  [switch]$NoMedia,
  [string]$Only = "",
  [string]$Container = "docker-moodle-1"
)
$ErrorActionPreference = "Stop"
$env:PATH += ";C:\Program Files\Docker\Docker\resources\bin"
$lms = Resolve-Path (Join-Path $PSScriptRoot "..")
$repo = Resolve-Path (Join-Path $lms "..")
$php = "/opt/bitnami/php/bin/php"

function Exec-Moodle([string[]]$cmd) {
  & docker exec -u daemon $Container @cmd 2>&1
}

$courses = @{
  "art-integrated-genai-literacy" = @{
    fullname = "Art-Integrated GenAI Literacy for Music and Theater Educators"; shortname = "GENAI101"
    category = "AI Literacy and Emerging Technology"; enrolkey = "genai-pilot-2026"; key = "genai" }
  "id-553-intro-instructional-design" = @{
    fullname = "ID 553: Introduction to the Principles of Instructional Design"; shortname = "ID553"
    category = "Instructional Design"; enrolkey = "id553-2026"; key = "id553" }
}

Write-Host "== preparing container"
docker exec $Container bash -c "mkdir -p /tmp/lms && chown daemon:daemon /tmp/lms" | Out-Null
foreach ($f in "moodle_admin.php", "moodle_restore_cc.php") { docker cp (Join-Path $lms "scripts\$f") "${Container}:/tmp/lms/$f" }
docker cp (Join-Path $repo "assets\images\brand-logo.png") "${Container}:/tmp/lms/brand-logo.png"

Write-Host "== site setup (theme, logo, categories)"
$setup = Exec-Moodle @($php, "/tmp/lms/moodle_admin.php", "setup", "--logo=/tmp/lms/brand-logo.png")
$setup | Write-Host
$cats = ($setup | Where-Object { $_ -like "CATEGORIES_JSON=*" }) -replace "^CATEGORIES_JSON=", "" | ConvertFrom-Json

foreach ($slug in $courses.Keys) {
  if ($Only -and $slug -ne $Only) { continue }
  $c = $courses[$slug]
  $pkg = if ($NoMedia) { "$slug.imscc" } else { "$slug-with-media.imscc" }
  $pkgPath = Join-Path $lms "dist\$pkg"
  if (-not (Test-Path $pkgPath)) { throw "package not found: $pkgPath (run build_cartridge.py$(if (-not $NoMedia) { ' --with-media' }))" }

  # Spec for post-import, derived from course.json.
  $course = Get-Content (Join-Path $lms "courses\$slug\course.json") -Raw | ConvertFrom-Json
  $items = $course.modules | ForEach-Object { $_.items }
  $spec = @{
    fullname    = $c.fullname; shortname = $c.shortname; category = $c.category; enrolkey = $c.enrolkey
    assignments = @($items | Where-Object { $_.type -eq "assignment" } | ForEach-Object { @{ title = $_.title; points = $(if ($_.points) { $_.points } else { 100 }) } })
    surveys     = @($items | Where-Object { $_.type -eq "quiz" -and ($_.title -match "Assessment|Survey") } | ForEach-Object { $_.title })
  }
  $specPath = Join-Path $env:TEMP "$slug.spec.json"
  $spec | ConvertTo-Json -Depth 5 | Set-Content -Path $specPath -Encoding utf8

  Write-Host "== $slug: copying package ($([math]::Round((Get-Item $pkgPath).Length/1MB,1)) MB)"
  docker cp $pkgPath "${Container}:/tmp/lms/$($c.key).imscc"
  docker cp $specPath "${Container}:/tmp/lms/$($c.key).spec.json"
  docker exec $Container bash -c "chown daemon:daemon /tmp/lms/*" | Out-Null

  Write-Host "== $slug: restoring into category '$($c.category)' (id $($cats.($c.category)))"
  Exec-Moodle @($php, "/tmp/lms/moodle_restore_cc.php", "--file=/tmp/lms/$($c.key).imscc",
    "--categoryid=$($cats.($c.category))", "--fullname=$($c.fullname)", "--shortname=$($c.shortname)") | Write-Host

  Write-Host "== $slug: post-import configuration"
  Exec-Moodle @($php, "/tmp/lms/moodle_admin.php", "postimport", "--course=$($c.fullname)", "--spec=/tmp/lms/$($c.key).spec.json") | Write-Host
}

Write-Host "== done. Open http://localhost (admin credentials are in lms/docker/.env)."
