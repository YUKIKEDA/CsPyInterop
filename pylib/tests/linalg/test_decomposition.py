"""
linalg.decomposition モジュールのテストコード

pytest を使用して特異値分解関連の関数をテストします。
実行方法: pytest pylib/tests/linalg/test_decomposition.py -v
"""

import pytest
import numpy as np
from numpy.testing import assert_array_almost_equal, assert_almost_equal

from linalg.decomposition import (
    svd,
    svd_dict,
    svd_reduced,
    matrix_rank,
    condition_number,
    low_rank_approximation
)


class TestSVD:
    """svd 関数のテストクラス"""
    
    def test_svd_basic_2x3_matrix(self):
        """基本的な2x3行列のSVD"""
        A = [[1, 2, 3],
             [4, 5, 6]]
        
        U, S, Vt = svd(A)
        
        # 形状の確認（full_matrices=True）
        assert U.shape == (2, 2)
        assert S.shape == (2,)
        assert Vt.shape == (3, 3)
        
        # 特異値は降順
        assert S[0] >= S[1]
        
        # 行列の再構成
        Sigma = np.zeros((2, 3))
        Sigma[:2, :2] = np.diag(S)
        A_reconstructed = U @ Sigma @ Vt
        
        assert_array_almost_equal(A_reconstructed, A, decimal=10)
    
    def test_svd_square_matrix(self):
        """正方行列のSVD"""
        A = [[1, 2],
             [3, 4]]
        
        U, S, Vt = svd(A)
        
        assert U.shape == (2, 2)
        assert S.shape == (2,)
        assert Vt.shape == (2, 2)
        
        # 再構成
        A_reconstructed = U @ np.diag(S) @ Vt
        assert_array_almost_equal(A_reconstructed, A, decimal=10)
    
    def test_svd_full_matrices_false(self):
        """full_matrices=False のテスト"""
        A = [[1, 2, 3, 4],
             [5, 6, 7, 8]]
        
        U, S, Vt = svd(A, full_matrices=False)
        
        # 縮約版の形状
        assert U.shape == (2, 2)
        assert S.shape == (2,)
        assert Vt.shape == (2, 4)
        
        # 再構成
        A_reconstructed = U @ np.diag(S) @ Vt
        assert_array_almost_equal(A_reconstructed, A, decimal=10)
    
    def test_svd_with_numpy_array(self):
        """Numpy配列を入力とするテスト"""
        A = np.array([[1.5, 2.5],
                      [3.5, 4.5],
                      [5.5, 6.5]])
        
        U, S, Vt = svd(A)
        
        assert U.shape == (3, 3)
        assert S.shape == (2,)
        assert Vt.shape == (2, 2)
    
    def test_svd_identity_matrix(self):
        """単位行列のSVD"""
        A = [[1, 0, 0],
             [0, 1, 0],
             [0, 0, 1]]
        
        U, S, Vt = svd(A)
        
        # 単位行列の特異値はすべて1
        assert_array_almost_equal(S, [1, 1, 1], decimal=10)
    
    def test_svd_rank_deficient_matrix(self):
        """ランク落ちした行列のSVD"""
        A = [[1, 2],
             [2, 4]]  # ランク1の行列
        
        U, S, Vt = svd(A)
        
        # 2番目の特異値はほぼゼロ
        assert S[0] > 1e-10
        assert S[1] < 1e-10


class TestSVDDict:
    """svd_dict 関数のテストクラス"""
    
    def test_svd_dict_returns_dict(self):
        """辞書形式で結果が返されることを確認"""
        A = [[1, 2, 3],
             [4, 5, 6]]
        
        result = svd_dict(A)
        
        assert isinstance(result, dict)
        assert "U" in result
        assert "S" in result
        assert "Vt" in result
    
    def test_svd_dict_returns_lists(self):
        """結果がリスト形式であることを確認"""
        A = [[1, 2, 3],
             [4, 5, 6]]
        
        result = svd_dict(A)
        
        assert isinstance(result["U"], list)
        assert isinstance(result["S"], list)
        assert isinstance(result["Vt"], list)
        
        # Uは2次元リスト
        assert isinstance(result["U"][0], list)
    
    def test_svd_dict_values_match_svd(self):
        """svd_dict の結果が svd と一致することを確認"""
        A = [[1, 2],
             [3, 4],
             [5, 6]]
        
        U, S, Vt = svd(A, full_matrices=False)
        result = svd_dict(A, full_matrices=False)
        
        assert_array_almost_equal(result["U"], U, decimal=10)
        assert_array_almost_equal(result["S"], S, decimal=10)
        assert_array_almost_equal(result["Vt"], Vt, decimal=10)
    
    def test_svd_dict_full_matrices_parameter(self):
        """full_matrices パラメータが機能することを確認"""
        A = [[1, 2, 3],
             [4, 5, 6]]
        
        result_full = svd_dict(A, full_matrices=True)
        result_reduced = svd_dict(A, full_matrices=False)
        
        # full版は正方行列
        assert len(result_full["U"]) == 2
        assert len(result_full["U"][0]) == 2
        assert len(result_full["Vt"]) == 3
        assert len(result_full["Vt"][0]) == 3
        
        # 縮約版は最小サイズ
        assert len(result_reduced["U"]) == 2
        assert len(result_reduced["U"][0]) == 2
        assert len(result_reduced["Vt"]) == 2
        assert len(result_reduced["Vt"][0]) == 3


class TestSVDReduced:
    """svd_reduced 関数のテストクラス"""
    
    def test_svd_reduced_shape(self):
        """縮約版の形状が正しいことを確認"""
        A = [[1, 2, 3, 4, 5],
             [6, 7, 8, 9, 10]]
        
        U, S, Vt = svd_reduced(A)
        
        assert U.shape == (2, 2)
        assert S.shape == (2,)
        assert Vt.shape == (2, 5)
    
    def test_svd_reduced_reconstruction(self):
        """縮約版でも行列が再構成できることを確認"""
        A = [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
        
        U, S, Vt = svd_reduced(A)
        
        A_reconstructed = U @ np.diag(S) @ Vt
        assert_array_almost_equal(A_reconstructed, A, decimal=10)


class TestMatrixRank:
    """matrix_rank 関数のテストクラス"""
    
    def test_full_rank_matrix(self):
        """フルランクの行列"""
        A = [[1, 0],
             [0, 1]]
        
        rank = matrix_rank(A)
        assert rank == 2
    
    def test_rank_deficient_matrix(self):
        """ランク落ちした行列"""
        A = [[1, 2],
             [2, 4]]  # ランク1
        
        rank = matrix_rank(A)
        assert rank == 1
    
    def test_zero_matrix(self):
        """ゼロ行列"""
        A = [[0, 0],
             [0, 0]]
        
        rank = matrix_rank(A)
        assert rank == 0
    
    def test_rectangular_matrix_rank(self):
        """長方形行列のランク"""
        A = [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]  # 3番目の行は1番目と2番目の線形結合
        
        rank = matrix_rank(A)
        assert rank == 2
    
    def test_rank_with_custom_tolerance(self):
        """カスタム許容誤差でのランク計算"""
        A = [[1, 0],
             [0, 1e-15]]  # 非常に小さい特異値
        
        # デフォルトの許容誤差ではランク2
        rank_default = matrix_rank(A)
        assert rank_default == 2
        
        # 大きい許容誤差ではランク1
        rank_custom = matrix_rank(A, tolerance=1e-10)
        assert rank_custom == 1


class TestConditionNumber:
    """condition_number 関数のテストクラス"""
    
    def test_identity_matrix_condition(self):
        """単位行列の条件数は1"""
        A = [[1, 0],
             [0, 1]]
        
        cond = condition_number(A)
        assert_almost_equal(cond, 1.0, decimal=10)
    
    def test_ill_conditioned_matrix(self):
        """条件数の悪い行列"""
        A = [[1, 0],
             [0, 0.001]]
        
        cond = condition_number(A)
        assert_almost_equal(cond, 1000.0, decimal=5)
    
    def test_singular_matrix_condition(self):
        """特異行列の条件数は非常に大きい"""
        A = [[1, 2],
             [2, 4]]  # 特異行列（ランク落ち）
        
        cond = condition_number(A)
        # 数値誤差により完全にゼロにならない場合があるため、非常に大きい値であることを確認
        assert cond > 1e10
    
    def test_well_conditioned_matrix(self):
        """条件数の良い行列"""
        A = [[2, 0],
             [0, 1]]
        
        cond = condition_number(A)
        assert_almost_equal(cond, 2.0, decimal=10)


class TestLowRankApproximation:
    """low_rank_approximation 関数のテストクラス"""
    
    def test_rank_1_approximation(self):
        """ランク1近似"""
        A = [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9]]
        
        A_approx = low_rank_approximation(A, rank=1)
        
        # 近似行列のランクは1
        rank = matrix_rank(A_approx)
        assert rank == 1
    
    def test_full_rank_approximation_equals_original(self):
        """フルランク近似は元の行列と一致"""
        A = [[1, 2],
             [3, 4]]
        
        A_approx = low_rank_approximation(A, rank=2)
        
        assert_array_almost_equal(A_approx, A, decimal=10)
    
    def test_approximation_reduces_norm(self):
        """低ランク近似は元の行列に近い"""
        A = np.random.rand(5, 5)
        
        A_approx = low_rank_approximation(A, rank=3)
        
        # フロベニウスノルムでの誤差を確認
        error = np.linalg.norm(A - A_approx, 'fro')
        original_norm = np.linalg.norm(A, 'fro')
        
        # 誤差は元のノルムより小さい
        assert error < original_norm
    
    def test_rank_2_approximation_shape(self):
        """ランク2近似の形状"""
        A = [[1, 2, 3, 4],
             [5, 6, 7, 8],
             [9, 10, 11, 12]]
        
        A_approx = low_rank_approximation(A, rank=2)
        
        # 形状は元の行列と同じ
        assert A_approx.shape == (3, 4)
    
    def test_approximation_with_numpy_array(self):
        """Numpy配列での低ランク近似"""
        A = np.array([[1.0, 2.0],
                      [3.0, 4.0],
                      [5.0, 6.0]])
        
        A_approx = low_rank_approximation(A, rank=1)
        
        assert A_approx.shape == A.shape


class TestEdgeCases:
    """エッジケースのテストクラス"""
    
    def test_single_element_matrix(self):
        """1x1行列"""
        A = [[5.0]]
        
        U, S, Vt = svd(A)
        
        assert U.shape == (1, 1)
        assert S.shape == (1,)
        assert Vt.shape == (1, 1)
        assert_almost_equal(S[0], 5.0)
    
    def test_single_row_matrix(self):
        """1行の行列"""
        A = [[1, 2, 3, 4]]
        
        U, S, Vt = svd(A)
        
        assert U.shape == (1, 1)
        assert S.shape == (1,)
        assert Vt.shape == (4, 4)
    
    def test_single_column_matrix(self):
        """1列の行列"""
        A = [[1],
             [2],
             [3]]
        
        U, S, Vt = svd(A)
        
        assert U.shape == (3, 3)
        assert S.shape == (1,)
        assert Vt.shape == (1, 1)
    
    def test_negative_values(self):
        """負の値を含む行列"""
        A = [[-1, -2],
             [-3, -4]]
        
        U, S, Vt = svd(A)
        
        # 特異値は常に非負
        assert np.all(S >= 0)
        
        # 再構成
        A_reconstructed = U @ np.diag(S) @ Vt
        assert_array_almost_equal(A_reconstructed, A, decimal=10)
    
    def test_large_values(self):
        """大きな値を含む行列"""
        A = [[1e10, 2e10],
             [3e10, 4e10]]
        
        U, S, Vt = svd(A)
        
        # 再構成（大きな値の場合は相対誤差で評価）
        A_reconstructed = U @ np.diag(S) @ Vt
        # 相対誤差が小さいことを確認
        relative_error = np.linalg.norm(A_reconstructed - A) / np.linalg.norm(A)
        assert relative_error < 1e-10


class TestIntegration:
    """統合テスト"""
    
    def test_svd_workflow(self):
        """SVDの典型的なワークフロー"""
        # 元の行列
        A = [[1, 2, 3],
             [4, 5, 6],
             [7, 8, 9],
             [10, 11, 12]]
        
        # SVD実行
        U, S, Vt = svd(A, full_matrices=False)
        
        # ランク計算
        rank = matrix_rank(A)
        assert rank <= min(4, 3)
        
        # 条件数計算
        cond = condition_number(A)
        assert cond > 0
        
        # 低ランク近似
        A_approx = low_rank_approximation(A, rank=2)
        assert A_approx.shape == (4, 3)
    
    def test_dict_format_for_interop(self):
        """C#連携を想定した辞書形式のテスト"""
        A = [[1.0, 2.0, 3.0],
             [4.0, 5.0, 6.0]]
        
        result = svd_dict(A, full_matrices=False)
        
        # 辞書のキーが存在
        assert "U" in result
        assert "S" in result
        assert "Vt" in result
        
        # すべてリスト形式
        assert isinstance(result["U"], list)
        assert isinstance(result["S"], list)
        assert isinstance(result["Vt"], list)
        
        # 特異値の取得（C#でのList<double>への変換を想定）
        singular_values = result["S"]
        assert len(singular_values) == 2
        assert all(isinstance(v, float) for v in singular_values)


if __name__ == "__main__":
    # pytest を直接実行
    pytest.main([__file__, "-v", "--tb=short"])
