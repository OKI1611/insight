# 바이블 인사이트 — 로컬 개발 서버 (wrangler dev)
# 사용법: 저장소 폴더에서  ->  powershell -ExecutionPolicy Bypass -File .\dev-local.ps1
#         (또는 PowerShell 에서  .\dev-local.ps1 )
#
# 왜 이 스크립트가 필요한가:
#   자산 디렉터리가 저장소 루트(./)라서, 저장소 안에서 `wrangler dev`를 그냥 실행하면
#   wrangler가 루트에 쓰는 .wrangler 상태 폴더를 자산 감시기가 감지해 무한 리로드 루프에 빠진다.
#   그래서 작업 디렉터리를 저장소 밖(임시 폴더)에 두고, 자산은 절대경로로 저장소를 가리키게 하여
#   .wrangler 상태가 감시 대상 밖에 생성되도록 한다. (worker + 정적 자산 모두 정상 동작)

param(
  [int]$Port = 8788
)

$ErrorActionPreference = 'Stop'
$repo  = (Split-Path -Parent $PSCommandPath) -replace '\\','/'
$work  = Join-Path $env:TEMP 'insight-wrangler-dev'
New-Item -ItemType Directory -Force $work | Out-Null

# 임시 작업 폴더에 dev 전용 설정 생성 (배포에는 영향 없음 — 배포는 저장소의 wrangler.jsonc 사용)
$cfg = Join-Path $work 'wrangler.dev.jsonc'
@"
{
  "name": "insight",
  "main": "$repo/worker/index.js",
  "compatibility_date": "2024-09-23",
  "assets": { "directory": "$repo", "binding": "ASSETS", "not_found_handling": "404-page" }
}
"@ | Set-Content -Encoding utf8 $cfg

# 로컬 시크릿(.dev.vars)이 저장소에 있으면 임시 작업 폴더로 복사 (wrangler 는 설정 폴더 기준으로 읽음)
$devVars = Join-Path (Split-Path -Parent $PSCommandPath) '.dev.vars'
if (Test-Path $devVars) {
  Copy-Item $devVars (Join-Path $work '.dev.vars') -Force
  Write-Host "[dev-local] .dev.vars 로드됨 (SUPABASE_SERVICE_KEY 등 적용)" -ForegroundColor Green
} else {
  Write-Host "[dev-local] .dev.vars 없음 — 결제/DB API는 키 없이 동작(ping 만 확인 가능). .dev.vars.example 참고." -ForegroundColor Yellow
}

$env:WRANGLER_SEND_METRICS = 'false'
Write-Host "[dev-local] http://localhost:$Port  (Ctrl+C 로 종료)" -ForegroundColor Cyan
Push-Location $work
try {
  wrangler dev --local --port $Port --config $cfg
} finally {
  Pop-Location
}
