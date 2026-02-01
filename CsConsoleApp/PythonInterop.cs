using System;
using System.IO;
using Python.Runtime;

namespace CsConsoleApp;

/// <summary>
/// pythonnet を用いて組み込み Python の pylib モジュール（linalg.decomposition 等）を利用するサンプル。
/// 組み込み Python は pylib/python-3.13.1-embed-amd64 に配置し、ビルド出力にコピーされていることを前提とする。
/// デバッガーで MissingMethodException / NotSupportedException が表示されても、pythonnet 内部で処理されており動作に影響しない。非表示にするには doc の「6.5 デバッガーで表示される例外」を参照。
/// </summary>
public class PythonInterop
{
    private const string EmbedFolderName = "python-3.13.1-embed-amd64";
    private const string PythonDllName = "python313.dll";
    private static bool _initialized;

    /// <summary>
    /// 組み込み Python を初期化する。呼び出し前に一度だけ実行する。
    /// </summary>
    public static void Initialize()
    {
        if (_initialized)
            return;

        string appDir = AppContext.BaseDirectory;
        string pythonHome = Path.Combine(appDir, "pylib", EmbedFolderName);

        if (!Directory.Exists(pythonHome))
            throw new InvalidOperationException(
                $"組み込み Python が見つかりません: {pythonHome}\n" +
                "setup-python.md に従い、pylib に Windows Embeddable Package を配置し、ビルドでコピーされるようにしてください。");

        Environment.SetEnvironmentVariable("PYTHONHOME", pythonHome, EnvironmentVariableTarget.Process);
        Environment.SetEnvironmentVariable("PATH",
            pythonHome + Path.PathSeparator + Environment.GetEnvironmentVariable("PATH"),
            EnvironmentVariableTarget.Process);
        Runtime.PythonDLL = Path.Combine(pythonHome, PythonDllName);

        PythonEngine.Initialize();
        _initialized = true;
    }

    /// <summary>
    /// Python ランタイムを終了する。アプリ終了前に呼ぶ。
    /// .NET 8 では pythonnet の Shutdown が BinaryFormatter で例外を出すことがあるため、失敗時は無視する（プロセス終了で解放される）。
    /// </summary>
    public static void Shutdown()
    {
        if (_initialized)
        {
            try
            {
                PythonEngine.Shutdown();
            }
            catch (NotSupportedException)
            {
                // BinaryFormatter 無効化による Shutdown 内エラー。プロセス終了でリソースは解放されるため無視する。
            }
            _initialized = false;
        }
    }

    /// <summary>
    /// pylib の linalg.decomposition.svd_dict を呼び出し、特異値分解の結果（辞書）を返すサンプル。
    /// </summary>
    /// <param name="matrix">分解対象の行列（2次元配列）</param>
    /// <returns>特異値 S の配列（C# 側で扱いやすい形）</returns>
    public static double[] CallSvdDict(double[][] matrix)
    {
        if (!_initialized)
            Initialize();

        using (Py.GIL())
        {
            AddSitePackagesToSysPath();

            PyObject decomp = Py.Import("linalg.decomposition");
            PyObject svdDictFn = decomp.GetAttr("svd_dict");
            using PyList matrixPy = CreatePyMatrix(matrix);
            PyObject resultPy = svdDictFn.Invoke(matrixPy);
            svdDictFn.Dispose();
            decomp.Dispose();

            // 辞書の "S"（特異値のリスト）を取得
            PyObject sPy = resultPy.GetItem("S".ToPython());
            double[] s = sPy.As<double[]>();
            sPy.Dispose();
            resultPy.Dispose();

            return s;
        }
    }

    /// <summary>
    /// 特異値分解の結果を辞書風に取得する（U, S, Vt すべて）。
    /// </summary>
    public static SvdResult CallSvdDictFull(double[][] matrix)
    {
        if (!_initialized)
            Initialize();

        using (Py.GIL())
        {
            AddSitePackagesToSysPath();

            PyObject decomp = Py.Import("linalg.decomposition");
            PyObject svdDictFn = decomp.GetAttr("svd_dict");
            using PyList matrixPy = CreatePyMatrix(matrix);
            PyObject resultPy = svdDictFn.Invoke(matrixPy);
            svdDictFn.Dispose();
            decomp.Dispose();

            double[] s = resultPy.GetItem("S".ToPython()).As<double[]>();
            double[][] u = PyObjectTo2DDoubleArray(resultPy.GetItem("U".ToPython()));
            double[][] vt = PyObjectTo2DDoubleArray(resultPy.GetItem("Vt".ToPython()));
            resultPy.Dispose();

            return new SvdResult(u, s, vt);
        }
    }

    /// <summary>
    /// sys.path に pylib の site-packages を追加する。dynamic を使わず PyObject API で行い、RuntimeBinderException / MissingMethodException を防ぐ。
    /// </summary>
    private static void AddSitePackagesToSysPath()
    {
        string pythonHome = Path.Combine(AppContext.BaseDirectory, "pylib", EmbedFolderName);
        string sitePackages = Path.Combine(pythonHome, "Lib", "site-packages");
        using PyObject sys = Py.Import("sys");
        using PyObject path = sys.GetAttr("path");
        using PyObject append = path.GetAttr("append");
        using PyObject arg = sitePackages.ToPython();
        append.Invoke(arg);
    }

    /// <summary>
    /// 2次元 C# 配列を Python の list of list に変換する。
    /// </summary>
    private static PyList CreatePyMatrix(double[][] rows)
    {
        var outer = new PyList();
        foreach (double[] row in rows)
        {
            var inner = new PyList();
            foreach (double x in row)
                inner.Append(x.ToPython());
            outer.Append(inner);
        }
        return outer;
    }

    /// <summary>
    /// Python の list of list (float) を C# の double[][] に変換する。
    /// </summary>
    private static double[][] PyObjectTo2DDoubleArray(PyObject pyList)
    {
        using var _ = pyList;
        int n = (int)pyList.Length();
        var result = new double[n][];
        for (int i = 0; i < n; i++)
        {
            PyObject row = pyList.GetItem(i);
            result[i] = row.As<double[]>();
            row.Dispose();
        }
        return result;
    }

    public readonly record struct SvdResult(double[][] U, double[] S, double[][] Vt);
}
