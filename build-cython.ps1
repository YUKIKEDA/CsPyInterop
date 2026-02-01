# Cython ビルドスクリプト
# 開発依存（Cython, setuptools）で .py を .pyd にコンパイルし、pylib 内の各パッケージに --inplace で出力する。
# 実行: プロジェクトルートで .\build-cython.ps1 [ -Deploy ]
#   -Deploy : ビルド後、
#             (1) pyproject.toml の依存を組み込み Python の site-packages にインストール、
#             (2) 組み込み Python（pylib/python-3.13.1-embed-amd64）の Lib/site-packages へ .pyd をコピーする。
# 前提: Visual Studio Build Tools 等で C コンパイラが利用できること。Deploy 時は組み込み Python の配置済みを前提とする。

param(
    [switch]$Deploy
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$PylibRoot = Join-Path $ProjectRoot "pylib"

# 組み込み Python の site-packages
$EmbedSitePackages = Join-Path $PylibRoot "python-3.13.1-embed-amd64\Lib\site-packages"

# pylib 直下で .pyd を含むパッケージディレクトリ名を列挙（tests と組み込み Python 用ディレクトリを除く）
function Get-BuiltPackageNames {
    Get-ChildItem -Path $PylibRoot -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -ne "tests" -and $_.Name -notmatch "python.*-embed-" } |
        Where-Object {
            $null -ne (Get-ChildItem -Path $_.FullName -Filter "*.pyd" -File -ErrorAction SilentlyContinue | Select-Object -First 1)
        } |
        ForEach-Object { $_.Name }
}

# 開発依存を同期（Cython, setuptools）
Set-Location $ProjectRoot
uv sync --group dev
if ($LASTEXITCODE -ne 0) { throw "uv sync --group dev failed" }

# pylib で setup.py を実行（.pyd は各パッケージディレクトリに生成される）
Set-Location $PylibRoot
uv run python setup.py build_ext --inplace
if ($LASTEXITCODE -ne 0) { throw "build_ext --inplace failed" }

Set-Location $ProjectRoot
$packages = @(Get-BuiltPackageNames)
Write-Host "Cython build completed. Built packages: $($packages -join ', ')" -ForegroundColor Green

# -Deploy 指定時: 
# (1) pyproject.toml の依存を組み込み Python にインストール、
# (2) .pyd をデプロイ
if ($Deploy) {
    $EmbedRoot = Join-Path $PylibRoot "python-3.13.1-embed-amd64"
    if (-not (Test-Path $EmbedRoot)) {
        throw "組み込み Python が見つかりません: $EmbedRoot`nsetup-python.md に従い、Windows Embeddable Package を配置してください。"
    }
    New-Item -ItemType Directory -Path $EmbedSitePackages -Force | Out-Null

    # pyproject.toml の依存（runtime のみ、プロジェクト本体は除く）を組み込み Python の site-packages にインストール
    $ReqFile = Join-Path $ProjectRoot "embed-requirements.txt"
    try {
        uv export --no-dev --no-emit-project -o $ReqFile
        if ($LASTEXITCODE -ne 0) { throw "uv export failed" }
        Write-Host "Installing pyproject.toml dependencies into embed site-packages..." -ForegroundColor Cyan
        uv pip install --target $EmbedSitePackages -r $ReqFile
        if ($LASTEXITCODE -ne 0) { throw "uv pip install --target failed" }
        Write-Host "Dependencies installed." -ForegroundColor Green
    } finally {
        if (Test-Path $ReqFile) { Remove-Item $ReqFile -Force }
    }

    foreach ($pkg in $packages) {
        $srcDir = Join-Path $PylibRoot $pkg
        $destDir = Join-Path $EmbedSitePackages $pkg
        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        Copy-Item -Path (Join-Path $srcDir "*.pyd") -Destination $destDir -Force -ErrorAction SilentlyContinue
        $initPy = Join-Path $srcDir "__init__.py"
        if (Test-Path $initPy) {
            Copy-Item -Path $initPy -Destination $destDir -Force
        }
        Write-Host "Deployed $pkg -> $destDir" -ForegroundColor Green
    }
}
