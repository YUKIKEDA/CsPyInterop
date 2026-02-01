"""
PyTorch を用いた機械学習サンプル

このモジュールは、簡単な回帰モデルを訓練し、予測を行うサンプルを提供します。
C# などの他言語から利用しやすいように、入出力はリスト／辞書形式としています。
"""

from typing import Dict, List, Union

import torch
import torch.nn as nn


# モジュール内で保持するモデル（訓練後に使用）
_model: nn.Module | None = None
_device: torch.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 入力特徴数（このサンプルでは 2: x1, x2）
INPUT_SIZE = 2
OUTPUT_SIZE = 1


class RegressionModel(nn.Module):
    """2 特徴量 → 1 スカラーを予測する簡単な MLP"""

    def __init__(self, input_size: int = INPUT_SIZE, hidden_size: int = 16):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, OUTPUT_SIZE),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


def _get_or_create_model() -> nn.Module:
    """訓練済みモデルを返す。未訓練なら先に train_regression_sample を呼ぶ必要がある。"""
    global _model
    if _model is None:
        raise RuntimeError(
            "モデルがまだ訓練されていません。先に train_regression_sample() を呼んでください。"
        )
    return _model


def _make_synthetic_data(n_samples: int = 200, seed: int = 42) -> tuple[torch.Tensor, torch.Tensor]:
    """y = 2*x1 + 3*x2 + 1 + ノイズ の合成データを生成"""
    torch.manual_seed(seed)
    x = torch.rand(n_samples, INPUT_SIZE) * 4 - 2  # [-2, 2] の範囲
    # 正解: y = 2*x1 + 3*x2 + 1
    y = 2.0 * x[:, 0] + 3.0 * x[:, 1] + 1.0 + 0.1 * torch.randn(n_samples)
    return x, y


def train_regression_sample(
    epochs: int = 200,
    learning_rate: float = 0.01,
    n_samples: int = 200,
) -> Dict[str, float]:
    """
    合成データで回帰モデルを訓練し、モジュール内にモデルを保持します。

    正解式: y = 2*x1 + 3*x2 + 1（+ ノイズ）

    Parameters
    ----------
    epochs : int
        訓練エポック数
    learning_rate : float
        学習率
    n_samples : int
        合成データのサンプル数

    Returns
    -------
    Dict[str, float]
        "final_loss": 最終エポックの損失（MSE）
        "epochs": 実行したエポック数
    """
    global _model, _device

    x, y = _make_synthetic_data(n_samples=n_samples)
    x, y = x.to(_device), y.to(_device)

    _model = RegressionModel().to(_device)
    optimizer = torch.optim.Adam(_model.parameters(), lr=learning_rate)
    criterion = nn.MSELoss()

    _model.train()
    for _ in range(epochs):
        optimizer.zero_grad()
        pred = _model(x)
        loss = criterion(pred, y)
        loss.backward()
        optimizer.step()

    final_loss = loss.item()
    return {"final_loss": final_loss, "epochs": float(epochs)}


def predict_dict(
    features: Union[List[List[float]], List[float]],
) -> Dict[str, List[float]]:
    """
    訓練済み回帰モデルで予測します。
    1 サンプルは [x1, x2] の 2 特徴量です。

    Parameters
    ----------
    features : List[List[float]] or List[float]
        入力特徴量。複数サンプルの場合は [[x1,x2], ...]、1 サンプルの場合は [x1, x2]。

    Returns
    -------
    Dict[str, List[float]]
        "result": 各サンプルの予測値のリスト

    Examples
    --------
    >>> train_regression_sample(epochs=100)
    >>> r = predict_dict([[1.0, 0.0], [0.0, 1.0]])  # 2 サンプル
    >>> # 真の値は 2*1+3*0+1=3, 2*0+3*1+1=4 に近い
    >>> r = predict_dict([1.0, 0.0])  # 1 サンプル
    """
    model = _get_or_create_model()

    if isinstance(features[0], (int, float)):
        features = [list(features)]
    x = torch.tensor(features, dtype=torch.float32, device=_device)

    model.eval()
    with torch.no_grad():
        pred = model(x)

    if pred.dim() == 0:
        pred = pred.unsqueeze(0)
    return {"result": pred.cpu().tolist()}


def device_info() -> Dict[str, str]:
    """
    利用可能な PyTorch デバイス情報を辞書で返します。

    Returns
    -------
    Dict[str, str]
        "cuda_available": "True" or "False"
        "device_name": 使用デバイス名（例: "cuda", "cpu"）
    """
    cuda_available = torch.cuda.is_available()
    device = "cuda" if cuda_available else "cpu"
    return {
        "cuda_available": str(cuda_available),
        "device_name": device,
    }


if __name__ == "__main__":
    print("=== PyTorch 機械学習サンプル（回帰） ===\n")

    print("デバイス:", device_info())
    print()

    print("合成データでモデルを訓練します...")
    train_result = train_regression_sample(epochs=200)
    print(f"訓練完了: final_loss={train_result['final_loss']:.6f}, epochs={train_result['epochs']:.0f}\n")

    # 予測: 真の式は y = 2*x1 + 3*x2 + 1
    test_inputs = [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [-1.0, 0.5]]
    pred_result = predict_dict(test_inputs)
    print("予測テスト（真の値: y = 2*x1 + 3*x2 + 1）:")
    for inp, out in zip(test_inputs, pred_result["result"]):
        expected = 2 * inp[0] + 3 * inp[1] + 1
        print(f"  入力 {inp} -> 予測 {out:.4f} (真の値 {expected})")
