"""
ml.pytorch_sample モジュールのテストコード

pytest を使用して PyTorch 機械学習サンプルをテストします。
実行方法: pytest pylib/tests/ml/test_pytorch_sample.py -v
"""

import pytest

from ml import pytorch_sample


class TestTrainRegressionSample:
    """train_regression_sample のテスト"""

    def test_train_returns_dict(self):
        result = pytorch_sample.train_regression_sample(epochs=10, n_samples=50)
        assert "final_loss" in result
        assert "epochs" in result
        assert result["epochs"] == 10

    def test_train_reduces_loss(self):
        result = pytorch_sample.train_regression_sample(epochs=100, n_samples=100)
        assert result["final_loss"] < 1.0


class TestPredictDict:
    """predict_dict のテスト（訓練後に実行）"""

    @pytest.fixture(autouse=True)
    def trained_model(self):
        """各テスト前にモデルを訓練"""
        pytorch_sample.train_regression_sample(epochs=150, n_samples=100)

    def test_predict_returns_dict(self):
        result = pytorch_sample.predict_dict([[1.0, 0.0]])
        assert "result" in result
        assert isinstance(result["result"], list)

    def test_predict_single_sample(self):
        # 真の値: y = 2*1 + 3*0 + 1 = 3
        result = pytorch_sample.predict_dict([1.0, 0.0])
        assert len(result["result"]) == 1
        assert 2.0 <= result["result"][0] <= 4.0

    def test_predict_batch(self):
        # [[1,0], [0,1], [1,1]] -> 真の値 3, 4, 6 付近
        result = pytorch_sample.predict_dict(
            [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]
        )
        assert len(result["result"]) == 3
        for v in result["result"]:
            assert isinstance(v, (int, float))

    def test_predict_approximates_true_formula(self):
        # 十分訓練したモデルは y ≈ 2*x1 + 3*x2 + 1 に近い
        pytorch_sample.train_regression_sample(epochs=300, n_samples=200)
        result = pytorch_sample.predict_dict([[1.0, 0.0], [0.0, 1.0]])
        # 真の値 3, 4
        assert abs(result["result"][0] - 3.0) < 0.5
        assert abs(result["result"][1] - 4.0) < 0.5


class TestPredictDictWithoutTrain:
    """訓練前に predict を呼ぶとエラー"""

    def test_predict_raises_without_train(self):
        # 未訓練状態を強制して RuntimeError を確認
        orig = pytorch_sample._model
        try:
            pytorch_sample._model = None
            with pytest.raises(RuntimeError, match="訓練されていません"):
                pytorch_sample.predict_dict([[1.0, 0.0]])
        finally:
            pytorch_sample._model = orig


class TestDeviceInfo:
    """device_info のテスト"""

    def test_device_info_keys(self):
        info = pytorch_sample.device_info()
        assert "cuda_available" in info
        assert "device_name" in info

    def test_device_name_is_cuda_or_cpu(self):
        info = pytorch_sample.device_info()
        assert info["device_name"] in ("cuda", "cpu")
