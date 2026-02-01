# Python 環境構築手順と利用方法（開発: 仮想環境 / 配布: 組み込み Python）

本ドキュメントでは、**開発環境では仮想環境（venv）**、**配布環境では組み込み Python（Windows Embeddable Package）** を使う構成の環境構築手順と、C# アプリケーションからの利用方法をまとめる。

---

## 1. 概要

### 1.1 組み込み Python とは

Windows Embeddable Package は、Python.org が提供する「アプリケーションに同梱して配布するための最小構成の Python ランタイム」である。

| 特徴 | 説明 |
|------|------|
| **pip なし** | パッケージマネージャは含まれない。依存はビルド時に別環境で用意し、site-packages として同梱する |
| **スタンドアロン** | ユーザー環境に Python をインストールしていなくても動作する |
| **軽量** | 必要な DLL と zip のみで構成され、サイズが小さい |

### 1.2 本プロジェクトでの構成

| 環境 | Python の扱い | 用途 |
|------|----------------|------|
| **開発環境** | **仮想環境（venv）** | 日常の開発・テスト・Cython ビルド。同一バージョンの Python を使用する |
| **配布環境** | **組み込み Python（Windows Embeddable Package）** | アプリ同梱用。ユーザーに Python をインストールさせずに配布する |

- 配布用フォルダ: `pylib/python-3.13.1-embed-amd64`（Python 3.13.1 64bit）
- 利用形態: **同一プロセス（pythonnet）** または **別プロセス（Process.Start）**

---

## 2. 環境構築手順

### 2.1 開発環境（仮想環境）の構築

開発時は **仮想環境（venv）** を使い、配布用の組み込み Python とは別に依存を管理する。

1. **同一バージョンの Python をインストール**  
   配布で使う組み込み Python と同じバージョン・ビット幅（例: 3.13 64bit）の Python を、[Python.org](https://www.python.org/downloads/) から通常インストール版でインストールする。

2. **仮想環境の作成と有効化**
   ```powershell
   cd pylib   # またはプロジェクト内の Python 用ディレクトリ
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **依存のインストール**
   ```powershell
   pip install -r requirements.txt
   pip install Cython setuptools   # Cython ビルド用
   ```

4. **開発・テスト**  
   この仮想環境上でスクリプトの実行・テストや Cython のビルドを行う。ビルドした .pyd 等は後述の手順で組み込み Python の `Lib/site-packages` にコピーする。

**重要**: 仮想環境の Python と配布用の組み込み Python は **同一バージョン・同一ビット幅** にすること（.pyd の互換性のため）。

### 2.2 配布用・組み込み Python のダウンロードと配置

1. [Python.org のダウンロードページ](https://www.python.org/downloads/) にアクセス
2. 「Windows embeddable package (64-bit)」をダウンロード（開発環境と同じバージョンを選ぶ）
3. ZIP を解凍し、アプリの適切なフォルダに配置（例: プロジェクトルートの `pylib/python-3.13.1-embed-amd64/`）

### 2.3 `_pth` ファイルの編集（site-packages 有効化）

組み込み Python はデフォルトで `site-packages` を参照しない。`python313._pth`（バージョンに応じて `python311._pth` 等）を編集し、以下を追加する。

**編集後の例（Python 3.13）:**

```
python313.zip
.
Lib
Lib\site-packages
import site
```

- `Lib` と `Lib\site-packages` を追加
- `import site` のコメントを外す（既に有効ならそのまま）

### 2.4 Lib/site-packages フォルダの作成

```
pylib/python-3.13.1-embed-amd64/
├── Lib/
│   └── site-packages/   ← このフォルダを作成
├── python313._pth
├── python313.dll
└── ...
```

### 2.5 配布用・依存パッケージのインストール（get-pip.py は不要）

組み込み Python には **pip を入れない**。依存は **`build-cython.ps1 -Deploy`** 実行時に、**pyproject.toml の runtime 依存**（`dependencies`）を uv で組み込み Python の `Lib/site-packages` へ自動インストールする。追加の手動インストールは不要である。

- 依存の定義は **pyproject.toml の `dependencies`** に書く（例: `numpy>=2.4.2`）。`-Deploy` がその一覧を `uv export --no-dev --no-emit-project` で取得し、`uv pip install --target ...` で組み込み側にインストールする。
- **-Deploy を使わず**に依存だけ手動で入れたい場合は、次を参考にすること。

**手動で入れる場合（参考）**

- **uv を使う例**: プロジェクトルートで `uv pip install --target pylib/python-3.13.1-embed-amd64/Lib/site-packages numpy`（pyproject.toml の依存を同様に `--target` で指定）。
- **venv + pip の例**: 仮想環境を有効化し、`pip install --target pylib/python-3.13.1-embed-amd64/Lib/site-packages numpy`。または venv の site-packages から必要なパッケージをコピーする。

### 2.6 Cython による .pyd のビルドと配置

自前モジュールを Cython でネイティブ拡張（.pyd）にコンパイルし、配布用の組み込み Python に配置するまでの手順。**ビルドは開発用の仮想環境（2.1）で行う。**

#### 2.6.1 ビルド環境の準備

| 種別 | 必要なもの |
|------|------------|
| 開発用 Python | **uv** で管理する Python（`.python-version` / `pyproject.toml`）。組み込み Python と **同一バージョン・ビット幅** にすること |
| C コンパイラ | Visual Studio Build Tools 等（`cl.exe` が使えること） |
| Python パッケージ | Cython, setuptools（`uv sync --group dev` で開発依存としてインストールされる） |

**重要**: uv が使う Python と組み込み Python のバージョン・ビット幅を一致させること。組み込みが 3.13 64bit なら、`.python-version` も 3.13 にすること。

#### 2.6.2 setup.py の作成

**pylib 直下**に `setup.py` を置く（`pylib/setup.py`）。`build_ext --inplace` で .pyd を `pylib/linalg/` に出力するため、setup.py は pylib で実行する。

```python
# pylib/setup.py
"""Cython ビルド用 setup.py（pylib で実行し、build_ext --inplace で .pyd を pylib/linalg に生成）"""
from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension("linalg.decomposition", ["linalg/decomposition.py"]),
]

setup(
    name="cspyinterop",
    ext_modules=cythonize(extensions),
)
```

複数モジュールをビルドする場合は `Extension(...)` を追加する。

#### 2.6.3 ビルドコマンド

**プロジェクトルートで** `build-cython.ps1` を実行する。uv で開発依存を同期してから pylib で `build_ext --inplace` を実行する。

```powershell
# ビルドのみ（.pyd は pylib 内の各パッケージディレクトリに生成される）
.\build-cython.ps1
```

- `--inplace`: ソースと同じ場所に .pyd を生成する
- 生成例: `pylib/linalg/decomposition.cp313-win_amd64.pyd`（cp313 = Python 3.13, win_amd64 = 64bit）
- `pylib/setup.py` に Extension を追加したパッケージは、ビルド後に自動でデプロイ対象に含まれる

#### 2.6.4 デプロイ（組み込み Python へのコピー）

ビルドとデプロイを一括で行うには **`-Deploy`** を付けて実行する。デプロイ先は **固定**で、`pylib/python-3.13.1-embed-amd64/Lib/site-packages` とする。

```powershell
# ビルド ＋ (1) pyproject.toml の依存を組み込み Python にインストール ＋ (2) .pyd をコピー
.\build-cython.ps1 -Deploy
```

**-Deploy 時に実行される処理:**

1. **依存のインストール**  
   `pyproject.toml` の **runtime 依存**（`dependencies` のみ。開発用グループは含まない）を、`uv export --no-dev --no-emit-project` で取得し、組み込み Python の `Lib/site-packages` へ `uv pip install --target` でインストールする。プロジェクト本体はインストールされない。
2. **.pyd のコピー**  
   `pylib` 直下で .pyd を含むパッケージ（`tests` を除く）が、それぞれ `*.pyd` と `__init__.py` とともに上記 site-packages へコピーされる。

- パッケージを増やした場合は `pylib/setup.py` に Extension を追加し、ビルドすればデプロイ対象に含まれる。
- **重要**: Embeddable Package の Python バージョンと .pyd のバージョン（cp313 等）を一致させること。

```
pylib/python-3.13.1-embed-amd64/Lib/site-packages/
├── linalg/
│   ├── __init__.py
│   ├── decomposition.cp313-win_amd64.pyd
│   └── (その他 .pyd)
├── numpy/          ← -Deploy で pyproject.toml の依存からインストールされる
└── (その他依存)
```

#### 2.6.5 ビルド・デプロイの流れ

| 操作 | コマンド |
|------|----------|
| ビルドのみ | `.\build-cython.ps1` |
| ビルド＋デプロイ | `.\build-cython.ps1 -Deploy` |

デプロイ先は `pylib/python-3.13.1-embed-amd64/Lib/site-packages` に固定。手動でコピーする必要はない。

---

## 3. C# からの利用方法

### 3.0 C# プロジェクトの前提設定

#### pythonnet の追加

```bash
dotnet add package pythonnet
```

または .csproj に:

```xml
<PackageReference Include="pythonnet" Version="3.0.5" />
```

#### Embeddable Package のビルド出力へのコピー

```xml
<ItemGroup>
  <None Include="pylib/python-3.13.1-embed-amd64\**\*" CopyToOutputDirectory="PreserveNewest" LinkBase="pylib/python-3.13.1-embed-amd64" />
</ItemGroup>
```

プロジェクト構成に応じてパスを調整する。

### 3.1 方式の比較

| 方式 | 概要 | 用途 |
|------|------|------|
| **同一プロセス（pythonnet）** | C# から CPython を初期化し、DLL 経由で Python モジュールを直接呼び出す | オブジェクトをそのまま渡したい、低オーバーヘッドが必要 |
| **別プロセス（Process.Start）** | 同梱の `python.exe` を起動し、引数・stdin/stdout でデータをやり取り | pythonnet を避けたい、プロセス境界で分離したい |

### 3.2 同一プロセス（pythonnet）での利用

#### 前提

- NuGet で `pythonnet` を追加
- Embeddable Package のフォルダをビルド出力にコピー

#### 初期化と呼び出し

```csharp
using Python.Runtime;

// 初期化
string appDir = AppContext.BaseDirectory;
string pythonHome = Path.Combine(appDir, "pylib/python-3.13.1-embed-amd64");

Environment.SetEnvironmentVariable("PYTHONHOME", pythonHome, EnvironmentVariableTarget.Process);
Environment.SetEnvironmentVariable("PATH", pythonHome + ";" + Environment.GetEnvironmentVariable("PATH"), EnvironmentVariableTarget.Process);
Runtime.PythonDLL = Path.Combine(pythonHome, "python313.dll");

PythonEngine.Initialize();

// 呼び出し
using (Py.GIL())
{
    dynamic sys = Py.Import("sys");
    string sitePackages = Path.Combine(pythonHome, "Lib", "site-packages");
    sys.path.append(sitePackages);

    // 例1: 単純な関数（数値等を渡す）
    // PyObject module = Py.Import("my_module");
    // PyObject result = module.InvokeMethod("compute", 1.0.ToPython(), 2.0.ToPython());
    // double value = result.As<double>();

    // 例2: linalg.decomposition（特異値分解）
    dynamic decomp = Py.Import("linalg.decomposition");
    PyObject result = decomp.InvokeMethod("svd_dict", CreatePyMatrix(new[] {
        new[] { 1.0, 2.0, 3.0 },
        new[] { 4.0, 5.0, 6.0 },
    }));
    var S = result["S"].As<List<double>>();  // 特異値の取得
}

PythonEngine.Shutdown();

// 補助: 2次元配列を Python の list の list に変換（同一クラス内のメソッド）
static PyObject CreatePyMatrix(double[][] rows)
{
    var outer = new PyList();
    foreach (var row in rows)
    {
        var inner = new PyList();
        foreach (var x in row) inner.Append(x.ToPython());
        outer.Append(inner);
    }
    return outer;
}
```

### 3.3 別プロセス（Process.Start）での利用

#### 起動用 run.py（最小限の .py）

```python
# run.py
import my_module
my_module.main()
```

#### C# から起動

```csharp
string pythonExe = Path.Combine(appDir, "pylib/python-3.13.1-embed-amd64", "python.exe");
string runScript = Path.Combine(appDir, "run.py");

var startInfo = new ProcessStartInfo
{
    FileName = pythonExe,
    Arguments = $"\"{runScript}\" --input \"{inputPath}\"",
    UseShellExecute = false,
    RedirectStandardOutput = true,
    RedirectStandardError = true,
    WorkingDirectory = appDir,
};

using var process = Process.Start(startInfo);
string stdout = process.StandardOutput.ReadToEnd();
string stderr = process.StandardError.ReadToEnd();
process.WaitForExit();
```

---

## 4. 配布物のディレクトリ構成例（配布環境）

開発は仮想環境で行い、配布時には以下のように組み込み Python を同梱する。

```
MyApp/
├── MyApp.exe
├── MyApp.dll
├── Python.Runtime.dll           # 同一プロセスのみ
├── run.py                       # 別プロセスのみ
├── pylib/python-3.13.1-embed-amd64/
│   ├── python.exe               # 別プロセスのみ
│   ├── python313.dll
│   ├── python313.zip
│   ├── python313._pth
│   ├── Lib/
│   │   └── site-packages/
│   │       ├── linalg/                  # Cython ビルドしたパッケージ
│   │       │   ├── decomposition.cp313-win_amd64.pyd
│   │       │   └── __init__.py
│   │       ├── numpy/
│   │       └── ...
│   └── (その他 DLL 等)
└── ...
```

---

## 5. 注意点・トラブルシューティング

### 5.1 バージョン・ビット幅の一致

- pythonnet、Embeddable Package、.pyd は **同一の Python バージョン・ビット幅（32/64bit）** で統一する
- AnyCPU の C# アプリは実行時の環境に合わせるため、64bit Python を使う場合は x64 で実行すること

### 5.2 DLL のロード失敗

- `PYTHONHOME` と `PATH` を、Embeddable Package のフォルダを指すように設定する
- `Runtime.PythonDLL` は `python313.dll`（バージョンに合わせる）の絶対パスを指定する

### 5.3 モジュールの import 失敗

- `sys.path` に `Lib/site-packages` のパスを追加する
- .pyd の Python バージョン（cp313 等）が Embeddable Package と一致しているか確認する

### 5.4 GIL（同一プロセス利用時）

- Python の C API を呼ぶ前に必ず `Py.GIL()` を取得する
- マルチスレッドでは各スレッドで `using (Py.GIL()) { ... }` を使う

---

## 6. 参考リンク

- [Windows Embeddable Package（Microsoft Blog）](https://devblogs.microsoft.com/python/cpython-embeddable-zip-file/)
- [Python.NET (pythonnet)](https://pythonnet.github.io/pythonnet/)
- [Cython Documentation](https://cython.readthedocs.io/)
- [Python Standalone Builds](https://gregoryszorc.com/docs/python-build-standalone/main/)（代替として利用可能）
