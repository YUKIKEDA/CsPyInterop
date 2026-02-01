// pythonnet で組み込み Python の pylib（linalg.decomposition）を利用するサンプル

using System;

namespace CsConsoleApp;

internal static class Program
{
    private static int Main(string[] args)
    {
        try
        {
            // サンプル行列: 2x3
            double[][] matrix =
            [
                [1.0, 2.0, 3.0],
                [4.0, 5.0, 6.0],
            ];

            Console.WriteLine("=== pylib linalg.decomposition.svd_dict の呼び出しサンプル ===\n");
            Console.WriteLine("入力行列 (2x3):");
            foreach (double[] row in matrix)
                Console.WriteLine("  [{0}]", string.Join(", ", row));

            // 特異値 S のみ取得
            double[] singularValues = PythonInterop.CallSvdDict(matrix);
            Console.WriteLine("\n特異値 S: [{0}]", string.Join(", ", singularValues));

            // U, S, Vt すべて取得
            var result = PythonInterop.CallSvdDictFull(matrix);
            Console.WriteLine("\nU の行数: {0}, 列数: {1}", result.U.Length, result.U[0].Length);
            Console.WriteLine("Vt の行数: {0}, 列数: {1}", result.Vt.Length, result.Vt[0].Length);

            // PyTorch 機械学習サンプル: 回帰モデルの訓練と予測（真の式: y = 2*x1 + 3*x2 + 1）
            Console.WriteLine("\n=== pylib ml.pytorch_sample（回帰モデル訓練・予測） ===\n");
            double finalLoss = PythonInterop.CallTrainRegressionSample(epochs: 200);
            Console.WriteLine("訓練完了: final_loss = {0:F6}", finalLoss);

            double[][] testInputs = [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [-1.0, 0.5]];
            double[] predictions = PythonInterop.CallPredictDict(testInputs);
            Console.WriteLine("予測（真の値: y = 2*x1 + 3*x2 + 1）:");
            for (int i = 0; i < testInputs.Length; i++)
            {
                double x1 = testInputs[i][0], x2 = testInputs[i][1];
                double expected = 2 * x1 + 3 * x2 + 1;
                Console.WriteLine("  入力 [{0}, {1}] -> 予測 {2:F4} (真の値 {3})", x1, x2, predictions[i], expected);
            }

            PythonInterop.Shutdown();
            Console.WriteLine("\n正常終了しました。");
            return 0;
        }
        catch (Exception ex)
        {
            Console.Error.WriteLine("エラー: {0}", ex.Message);
            if (ex.InnerException != null)
                Console.Error.WriteLine("  Inner: {0}", ex.InnerException.Message);
            return 1;
        }
    }
}
