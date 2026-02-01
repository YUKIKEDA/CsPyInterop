# CsPyInterop

C#（.NET 8）から **pythonnet** で組み込み Python を呼び出し、プロジェクト内の Python ライブラリ（`pylib`）を利用するサンプルです。  
サンプルでは `pylib/linalg/decomposition` の特異値分解（SVD）を C# から呼び出しています。

## 概要

| 項目 | 内容 |
|------|------|
| C# 側 | .NET 8（x64）、pythonnet 3.0.5 |
| Python 側 | 組み込み Python（Windows Embeddable Package）3.13.1 64bit |
| 利用形態 | 同一プロセス内で pythonnet により Python を初期化し、`pylib` のモジュールを呼び出し |

- **開発時**: 仮想環境（venv）で Python スクリプトの開発・テスト・Cython ビルドを行う
- **実行時**: アプリに同梱した組み込み Python の `pylib`（および site-packages）を参照して動作

## 必要環境

- **.NET 8 SDK**
- **Python 3.13 64bit**（開発用: 通常インストール版 / 配布用: Windows Embeddable Package）
- **Windows x64**（本サンプルは x64 前提）

## プロジェクト構成

```
CsPyInterop/
├── CsConsoleApp/           # C# コンソールアプリ
│   ├── Program.cs          # エントリポイント（SVD 呼び出しサンプル）
│   ├── PythonInterop.cs    # pythonnet による Python 初期化・pylib 呼び出し
│   └── CsConsoleApp.csproj
├── pylib/                  # Python ライブラリ（C# から利用）
│   ├── linalg/
│   │   └── decomposition.py  # 特異値分解など
│   ├── python-3.13.1-embed-amd64/  # 組み込み Python（手動配置）
│   └── ...
├── setup-python.md         # Python 環境構築の詳細手順
└── pyproject.toml          # Python 依存（uv/pip 用）
```

## セットアップ

### 1. 組み込み Python の配置

1. [Python.org](https://www.python.org/downloads/) から **Windows embeddable package (64-bit)**（Python 3.13.x）をダウンロード
2. ZIP を解凍し、`pylib/python-3.13.1-embed-amd64/` に配置
3. `python313._pth` を編集し、`Lib` と `Lib\site-packages` を追加、`import site` を有効化

### 2. site-packages の用意

組み込み Python には pip が含まれないため、依存（NumPy 等）は別環境でインストールし、`pylib/python-3.13.1-embed-amd64/Lib/site-packages` にコピーする必要があります。

**詳細な手順**（仮想環境の作成、`_pth` の編集、依存のインストールとコピー、Cython ビルドなど）は ** [setup-python.md](setup-python.md) ** を参照してください。

## ビルド・実行

```powershell
cd CsConsoleApp
dotnet run
```

初回は組み込み Python と site-packages のセットアップが済んでいる必要があります。未設定の場合は「組み込み Python が見つかりません」などのエラーになります。

### 実行例

サンプルは 2×3 の行列に対して特異値分解（SVD）を実行し、特異値 S および U, Vt の次元を表示します。

```
=== pylib linalg.decomposition.svd_dict の呼び出しサンプル ===

入力行列 (2x3):
  [1, 2, 3]
  [4, 5, 6]

特異値 S: [9.508032, 0.772869, ...]

U の行数: 2, 列数: 2
Vt の行数: 3, 列数: 3

正常終了しました。
```

## Python 側の開発・テスト

- `pylib` 配下の Python コードは、開発時は **venv** で実行・テストすることを推奨します。
- `pyproject.toml` の `requires-python = ">=3.13"` および依存に合わせ、同一バージョンの Python で仮想環境を作成し、`pytest` 等でテストできます。
- 組み込み Python と venv の Python は **同一バージョン・同一ビット幅** にすると、.pyd 等の互換性が保たれます。

## 参考

- [pythonnet](https://github.com/pythonnet/pythonnet) — .NET から CPython を呼び出すライブラリ
- [Python Windows Embeddable Package](https://docs.python.org/3/using/windows.html#embedded-distribution)
- プロジェクト内ドキュメント: [setup-python.md](setup-python.md)、[doc/](doc/)
