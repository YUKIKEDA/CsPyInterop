# Cython + 組み込み Python + pythonnet による Python と C# の相互運用

本ドキュメントでは、**Cython** で Python モジュールをネイティブ拡張（.pyd）にコンパイルし、**組み込み Python（Windows Embeddable Package）** を同梱したうえで、C# から Python を呼び出す方法を解説する。呼び出し方は **同一プロセス（pythonnet）** と **別プロセス（Process.Start）** の二通りを扱う。

---

## 1. 概要

### 1.1 構成の特徴

| 要素 | 役割 |
|------|------|
| **Cython** | .py を C に変換し .pyd（ネイティブ拡張）にビルド。ソースコードの保護・実行速度向上 |
| **組み込み Python** | ユーザー環境に Python がなくても動作するよう、ランタイムをアプリに同梱 |
| **pythonnet** | C# から CPython を同一プロセス内で初期化し、Python モジュールを直接 import して呼び出す |
| **Process.Start** | 別プロセス方式では、同梱の python.exe を起動し、stdin/stdout や引数でデータをやり取りする |

### 1.2 メリット

- **リバースエンジニアリング対策**: ロジックは .pyd に含まれ、.py の逆コンパイルは困難
- **Python 未インストール環境で動作**: Embeddable Package を同梱すればユーザーは Python を入れなくてよい
- **追加インストール不要**: NumPy 等の依存をビルド時に site-packages へ同梱
- **ビルド時間が現実的**: Cython はモジュール単位のコンパイルで、Nuitka/PyInstaller より大幅に短い

---

## 2. 前提環境・ツール

### 2.1 必要なもの

| 種別 | ツール・バージョン |
|------|--------------------|
| ビルド環境 | Python 3.x（開発用）、C コンパイラ（Visual Studio Build Tools など） |
| Python パッケージ | Cython, setuptools |
| .NET | .NET 6 以降（または .NET Framework 4.x 以上） |
| NuGet | pythonnet 3.x |

### 2.2 バージョン整合性

- **pythonnet** は **CPython のバージョン** と **ビット幅（32/64bit）** に合わせる必要がある
- Embeddable Package、Cython でビルドした .pyd、pythonnet はすべて **同一の Python バージョン・ビット幅** で統一すること

---

## 3. 手順

### 3.1 組み込み Python の準備

1. [Python.org](https://www.python.org/downloads/) の「Windows embeddable package (64-bit)」をダウンロード
2. 適切なフォルダ（例: `MyApp/python/`）に解凍
3. `python311._pth` を編集し、site-packages を有効化:

   ```
   python311.zip
   .
   Lib
   Lib\site-packages
   import site
   ```

4. `Lib/site-packages` フォルダを作成
5. 必要なパッケージ（NumPy 等）を、同じバージョンの通常 Python で `pip install --target=Lib/site-packages <package>` して同梱

### 3.2 Cython で .pyd をビルド

#### Python モジュールの作成

```python
# my_module.py（ビルド後は .pyd のみ配布）
import numpy as np

def compute(x: float, y: float) -> float:
    arr = np.array([x, y])
    return float(np.sum(arr))

def process_data(data: list) -> dict:
    arr = np.array(data)
    return {"mean": float(np.mean(arr)), "sum": float(np.sum(arr))}
```

#### setup.py（Cython ビルド用）

```python
from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension("my_module", ["my_module.py"]),
]

setup(
    name="my_module",
    ext_modules=cythonize(extensions),
)
```

#### ビルドコマンド

```bash
python setup.py build_ext --inplace
```

- 生成された `my_module.cp311-win_amd64.pyd` を Embeddable Package の `Lib/site-packages/` にコピー
- （ファイル名の `cp311` は Python 3.11、`win_amd64` は 64bit Windows を表す）

### 3.3 C# プロジェクトの設定

#### NuGet で pythonnet を追加

```bash
dotnet add package pythonnet
```

または .csproj に:

```xml
<PackageReference Include="pythonnet" Version="3.0.5" />
```

#### ビルド後に python フォルダを出力へコピー

```xml
<ItemGroup>
  <None Include="python\**\*" CopyToOutputDirectory="PreserveNewest" LinkBase="python" />
</ItemGroup>
```

### 3.4 C# から pythonnet で呼び出す

```csharp
using System;
using System.IO;
using Python.Runtime;

public class PythonInterop
{
    public static void Initialize()
    {
        string appDir = AppContext.BaseDirectory;
        string pythonHome = Path.Combine(appDir, "python");

        Environment.SetEnvironmentVariable("PYTHONHOME", pythonHome, EnvironmentTarget.Process);
        Environment.SetEnvironmentVariable("PATH", pythonHome + ";" + Environment.GetEnvironmentVariable("PATH"), EnvironmentTarget.Process);
        Runtime.PythonDLL = Path.Combine(pythonHome, "python311.dll");  // バージョンに合わせる

        PythonEngine.Initialize();
    }

    public static double Compute(double x, double y)
    {
        using (Py.GIL())
        {
            dynamic sys = Py.Import("sys");
            string sitePackages = Path.Combine(
                AppContext.BaseDirectory, "python", "Lib", "site-packages");
            sys.path.append(sitePackages);

            PyObject module = Py.Import("my_module");
            PyObject result = module.InvokeMethod("compute", x.ToPython(), y.ToPython());
            return result.As<double>();
        }
    }

    public static void Shutdown()
    {
        PythonEngine.Shutdown();
    }
}
```

#### 使用例

```csharp
PythonInterop.Initialize();
try
{
    double result = PythonInterop.Compute(1.0, 2.0);
    Console.WriteLine(result);  // 3.0
}
finally
{
    PythonInterop.Shutdown();
}
```

### 3.5 別プロセスで実行する方法

pythonnet を使わず、C# から **Process.Start** で同梱の `python.exe` を起動し、子プロセスとして Python を実行する方式。ロジックは .pyd にあり、配布する .py は起動用の 1 〜 数行のみで済む。

#### 3.5.1 共通の準備

- 組み込み Python の `python.exe` を同梱する（Embeddable Package に含まれる）
- Cython でビルドした .pyd を `Lib/site-packages` に配置
- 起動用の **run.py** を用意する

#### 3.5.2 起動用 run.py

配布する唯一の .py。中身は最小限にし、どの .pyd を呼ぶかだけを記述する。

```python
# run.py
import my_module
my_module.main()
```

#### 3.5.3 .pyd 側（my_module）の main 関数

コマンドライン引数や stdin から入力を受け取り、stdout やファイルに結果を出す。

```python
# my_module.py（Cython で .pyd にビルド）
import sys
import json
import numpy as np

def main():
    # 引数例: --input "1,2,3"
    data = parse_args(sys.argv)
    result = do_compute(data)
    print(json.dumps(result))  # C# は StandardOutput で受け取る

def parse_args(argv):
    data = []
    for i, arg in enumerate(argv):
        if arg == "--input" and i + 1 < len(argv):
            data = [float(x) for x in argv[i + 1].split(",")]
            break
    # stdin から受け取る場合: data = json.loads(sys.stdin.read())
    return data

def do_compute(data):
    arr = np.array(data)
    return {"mean": float(np.mean(arr)), "sum": float(np.sum(arr))}
```

#### 3.5.4 C# から Process.Start で呼び出す

```csharp
using System;
using System.Diagnostics;
using System.IO;
using System.Text.Json;

public static class PythonSubprocess
{
    public static (double Mean, double Sum) Compute(double[] data)
    {
        string appDir = AppContext.BaseDirectory;
        string pythonExe = Path.Combine(appDir, "python", "python.exe");
        string runScript = Path.Combine(appDir, "run.py");
        string inputStr = string.Join(",", data);

        var startInfo = new ProcessStartInfo
        {
            FileName = pythonExe,
            Arguments = $"\"{runScript}\" --input \"{inputStr}\"",
            UseShellExecute = false,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            CreateNoWindow = false,
            WorkingDirectory = appDir,
        };

        using var process = Process.Start(startInfo);
        string stdout = process.StandardOutput.ReadToEnd();
        string stderr = process.StandardError.ReadToEnd();
        process.WaitForExit();

        if (process.ExitCode != 0)
            throw new InvalidOperationException($"Python error: {stderr}");

        var result = JsonSerializer.Deserialize<ComputeResult>(stdout);
        return (result!.Mean, result.Sum);
    }

    private class ComputeResult
    {
        public double Mean { get; set; }
        public double Sum { get; set; }
    }
}
```

#### 3.5.5 stdin / stdout で JSON を渡す例

より大きなデータを渡す場合は stdin を使う。

**run.py（stdin を受け取る場合）**

```python
# run.py
import sys
import my_module

if __name__ == "__main__":
    input_json = sys.stdin.read()
    my_module.main_from_stdin(input_json)
```

**my_module に追加する関数**

```python
def main_from_stdin(input_json: str):
    data = json.loads(input_json)
    values = data.get("values", [])
    result = do_compute(values)
    print(json.dumps(result))
```

**C# 側**

```csharp
startInfo.RedirectStandardInput = true;
// ...
using var writer = process.StandardInput;
writer.Write(JsonSerializer.Serialize(new { values = new[] { 1.0, 2.0, 3.0 } }));
writer.Close();
string stdout = process.StandardOutput.ReadToEnd();
```

#### 3.5.6 同一プロセス vs 別プロセスの比較

| 観点 | 同一プロセス（pythonnet） | 別プロセス（Process.Start） |
|------|---------------------------|------------------------------|
| **依存** | pythonnet が必要 | pythonnet 不要（標準の Process のみ） |
| **データ渡し** | オブジェクトを直接渡せる | 引数・stdin/stdout・ファイルでシリアライズが必要 |
| **オーバーヘッド** | 低い（同一アドレス空間） | プロセス起動のオーバーヘッドあり |
| **分離** | Python のクラッシュが C# にも影響 | プロセス境界で分離される |
| **配布 .py** | 原則不要 | run.py など起動用の最小限の .py が必要 |

---

## 4. データの受け渡し

**同一プロセス（pythonnet）** では C# オブジェクトを直接 Python に渡せる。**別プロセス** では引数・stdin/stdout・ファイルなど、シリアライズ可能な形式で渡す。

### 4.1 同一プロセス: C# → Python

| C# 型 | Python 側での扱い |
|-------|-------------------|
| `int`, `long` | `int` |
| `double`, `float` | `float` |
| `string` | `str` |
| `bool` | `bool` |
| `int[]`, `double[]` | `list` として渡す場合は `new PyList(...)` 等を利用 |
| 任意のオブジェクト | `.ToPython()` 拡張メソッド（pythonnet が提供） |

```csharp
// 数値
module.InvokeMethod("compute", x.ToPython(), y.ToPython());

// リスト
var list = new PyList();
list.Append(1.ToPython());
list.Append(2.ToPython());
module.InvokeMethod("process_data", list);
```

### 4.2 同一プロセス: Python → C#

| Python 型 | C# での取得方法 |
|-----------|-----------------|
| `int`, `float` | `result.As<int>()`, `result.As<double>()` |
| `str` | `result.As<string>()` |
| `list` | `result.As<IEnumerable<PyObject>>()` 等で要素をループ |
| `dict` | キーでアクセスするか、`AsManagedObject()` で C# 型に変換 |

```csharp
PyObject result = module.InvokeMethod("process_data", list);
double mean = result["mean"].As<double>();
double sum = result["sum"].As<double>();
```

### 4.3 別プロセス: データの受け渡し

| 方式 | 入力 | 出力 |
|------|------|------|
| **コマンドライン引数** | `Arguments` に `--input "1,2,3"` など | 使用しない |
| **stdin** | `RedirectStandardInput` で JSON 等を書き込み | 使用しない |
| **stdout** | 使用しない | `RedirectStandardOutput` で JSON 等を読み取り |
| **ファイル** | 入力ファイルパスを引数で渡す | 出力ファイルパスを引数で渡し、C# で読み込む |

---

## 5. 配布物のディレクトリ構成

```
MyApp/
├── MyApp.exe
├── MyApp.dll
├── Python.Runtime.dll          # 同一プロセスのみ（別プロセスのみなら不要）
├── run.py                      # 別プロセスのみ（起動用 .py）
├── python/
│   ├── python.exe              # 別プロセスのみ（同一プロセスのみなら不要）
│   ├── python311.dll
│   ├── python311.zip
│   ├── python311._pth
│   ├── Lib/
│   │   └── site-packages/
│   │       ├── my_module.cp311-win_amd64.pyd
│   │       ├── numpy/
│   │       └── ...
│   └── ...
└── (その他 .NET の依存 DLL)
```

- **同一プロセスのみ**: `python.exe` は不要。pythonnet が `python311.dll` を直接ロード
- **別プロセスのみ**: `python.exe` と `run.py` を同梱。pythonnet は不要

---

## 6. 注意点・トラブルシューティング

### 6.1 GIL（グローバルインタプリタロック）

- Python の C API を呼ぶ前に必ず `Py.GIL()` を取得する
- マルチスレッドで呼ぶ場合は、各スレッドで `using (Py.GIL()) { ... }` を使う

### 6.2 DLL のロード失敗

- `PYTHONHOME` と `PATH` を正しく設定し、`python311.dll` がロードできる状態にする
- pythonnet のビット幅（AnyCPU の場合は実行環境）と Python のビット幅を一致させる

### 6.3 モジュールの import 失敗

- `sys.path` に `site-packages` を追加する
- .pyd の Python バージョン（cp311 等）が Embeddable Package のバージョンと一致しているか確認

### 6.4 Embeddable Package の制限

- `python.exe` は同梱されているが、`pip` は含まれない
- 依存パッケージはビルド時に別環境でインストールし、`site-packages` をコピーして同梱する

### 6.5 デバッガーで表示される「例外がスローされました」（.NET 8）

Visual Studio でデバッグ実行すると、アプリは正常終了（コード 0）しているにもかかわらず、次の第一次例外が表示されることがある。

| 例外 | 原因 | 対処 |
|------|------|------|
| **MissingMethodException** (Python.Runtime.dll) | pythonnet の CodeGenerator が .NET Framework の `AppDomain.DefineDynamicAssembly` を呼ぶため。.NET Core/.NET 8 には存在せず、pythonnet が内部で catch して別経路で続行している（[Issue #834](https://github.com/pythonnet/pythonnet/issues/834)）。 | 動作には影響しない。表示を消すには: **デバッグ** → **ウィンドウ** → **例外設定** (Ctrl+Alt+E) → **Common Language Runtime Exceptions** の **System.MissingMethodException** の「スローされる」のチェックを外す。 |
| **NotSupportedException** (System.Runtime.Serialization.Formatters.dll) | pythonnet の `PythonEngine.Shutdown()` 内で BinaryFormatter が使われており、.NET 8 では既定で無効なため。本サンプルでは Shutdown を try-catch で囲み無視している。 | 上記と同様に **System.NotSupportedException** の「スローされる」を外すか、そのままでもよい。 |

---

## 7. 参考文献

- [Python.NET (pythonnet)](https://pythonnet.github.io/pythonnet/)
- [Cython Documentation](https://cython.readthedocs.io/)
- [Windows Embeddable Package](https://devblogs.microsoft.com/python/cpython-embeddable-zip-file/)
