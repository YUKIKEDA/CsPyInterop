"""
線形代数の分解アルゴリズム

このモジュールは、Numpyを用いた行列の分解（特異値分解など）を提供します。
"""

import numpy as np
from typing import Dict, List, Tuple, Union


def svd(matrix: Union[List[List[float]], np.ndarray], 
        full_matrices: bool = True) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    特異値分解（SVD: Singular Value Decomposition）を実行します。
    
    行列 A を A = U * Σ * V^T に分解します。
    
    Parameters
    ----------
    matrix : List[List[float]] or np.ndarray
        分解対象の行列（m x n）
    full_matrices : bool, optional
        True の場合、U は (m x m)、V^T は (n x n) の正方行列になります。
        False の場合、U は (m x k)、V^T は (k x n) になります（k = min(m, n)）。
        デフォルトは True です。
    
    Returns
    -------
    U : np.ndarray
        左特異ベクトル行列（m x m または m x k）
    S : np.ndarray
        特異値の1次元配列（降順にソート済み）
    Vt : np.ndarray
        右特異ベクトルの転置行列（n x n または k x n）
    
    Examples
    --------
    >>> import numpy as np
    >>> A = [[1, 2, 3], [4, 5, 6]]
    >>> U, S, Vt = svd(A)
    >>> print(f"特異値: {S}")
    >>> # 元の行列を再構成
    >>> A_reconstructed = U @ np.diag(S) @ Vt
    """
    # リストの場合はNumpy配列に変換
    A = np.array(matrix, dtype=float)
    
    # 特異値分解を実行
    U, S, Vt = np.linalg.svd(A, full_matrices=full_matrices)
    
    return U, S, Vt


def svd_dict(matrix: Union[List[List[float]], np.ndarray], 
             full_matrices: bool = True) -> Dict[str, List]:
    """
    特異値分解を実行し、結果を辞書形式で返します。
    
    C# などの他言語から利用しやすいように、結果を辞書（dict）で返します。
    
    Parameters
    ----------
    matrix : List[List[float]] or np.ndarray
        分解対象の行列（m x n）
    full_matrices : bool, optional
        True の場合、完全な行列を返します。デフォルトは True です。
    
    Returns
    -------
    result : Dict[str, List]
        以下のキーを持つ辞書:
        - "U": 左特異ベクトル行列（2次元リスト）
        - "S": 特異値の配列（1次元リスト、降順）
        - "Vt": 右特異ベクトルの転置行列（2次元リスト）
    
    Examples
    --------
    >>> A = [[1, 2, 3], [4, 5, 6]]
    >>> result = svd_dict(A)
    >>> print(f"特異値: {result['S']}")
    >>> print(f"U の形状: {len(result['U'])} x {len(result['U'][0])}")
    """
    U, S, Vt = svd(matrix, full_matrices=full_matrices)
    
    return {
        "U": U.tolist(),
        "S": S.tolist(),
        "Vt": Vt.tolist()
    }


def svd_reduced(matrix: Union[List[List[float]], np.ndarray]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    縮約版の特異値分解を実行します（full_matrices=False）。
    
    メモリ効率が良く、大きな行列に適しています。
    
    Parameters
    ----------
    matrix : List[List[float]] or np.ndarray
        分解対象の行列（m x n）
    
    Returns
    -------
    U : np.ndarray
        左特異ベクトル行列（m x k、k = min(m, n)）
    S : np.ndarray
        特異値の1次元配列（降順にソート済み）
    Vt : np.ndarray
        右特異ベクトルの転置行列（k x n）
    
    Examples
    --------
    >>> A = [[1, 2, 3, 4], [5, 6, 7, 8]]
    >>> U, S, Vt = svd_reduced(A)
    >>> print(f"U の形状: {U.shape}")  # (2, 2)
    >>> print(f"Vt の形状: {Vt.shape}")  # (2, 4)
    """
    return svd(matrix, full_matrices=False)


def matrix_rank(matrix: Union[List[List[float]], np.ndarray], 
                tolerance: float = None) -> int:
    """
    特異値分解を用いて行列のランク（階数）を計算します。
    
    Parameters
    ----------
    matrix : List[List[float]] or np.ndarray
        対象の行列
    tolerance : float, optional
        特異値をゼロとみなす閾値。指定しない場合は自動で決定されます。
    
    Returns
    -------
    rank : int
        行列のランク
    
    Examples
    --------
    >>> A = [[1, 2], [2, 4]]  # ランク1の行列
    >>> print(matrix_rank(A))  # 1
    >>> B = [[1, 0], [0, 1]]  # ランク2の行列
    >>> print(matrix_rank(B))  # 2
    """
    A = np.array(matrix, dtype=float)
    
    # 特異値を計算
    _, S, _ = np.linalg.svd(A)
    
    # 閾値を設定
    if tolerance is None:
        tolerance = S.max() * max(A.shape) * np.finfo(float).eps
    
    # 閾値より大きい特異値の数がランク
    rank = np.sum(S > tolerance)
    
    return int(rank)


def condition_number(matrix: Union[List[List[float]], np.ndarray]) -> float:
    """
    特異値分解を用いて行列の条件数を計算します。
    
    条件数は最大特異値と最小特異値の比で、行列の数値的安定性を示します。
    条件数が大きいほど、数値計算が不安定になります。
    
    Parameters
    ----------
    matrix : List[List[float]] or np.ndarray
        対象の行列
    
    Returns
    -------
    cond : float
        条件数（最大特異値 / 最小特異値）
    
    Examples
    --------
    >>> A = [[1, 0], [0, 0.001]]
    >>> print(condition_number(A))  # 約1000（条件数が大きい = 不安定）
    """
    A = np.array(matrix, dtype=float)
    
    # 特異値を計算
    _, S, _ = np.linalg.svd(A)
    
    # 最小特異値がゼロの場合は無限大
    if S[-1] == 0:
        return float('inf')
    
    # 条件数 = 最大特異値 / 最小特異値
    cond = S[0] / S[-1]
    
    return float(cond)


def low_rank_approximation(matrix: Union[List[List[float]], np.ndarray], 
                           rank: int) -> np.ndarray:
    """
    特異値分解を用いて行列の低ランク近似を計算します。
    
    元の行列を指定されたランクで近似します。データ圧縮や
    ノイズ除去に利用できます。
    
    Parameters
    ----------
    matrix : List[List[float]] or np.ndarray
        対象の行列（m x n）
    rank : int
        近似のランク（1 ≤ rank ≤ min(m, n)）
    
    Returns
    -------
    approximation : np.ndarray
        低ランク近似された行列
    
    Examples
    --------
    >>> A = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    >>> A_approx = low_rank_approximation(A, rank=2)
    >>> print(f"元の行列のランク: {matrix_rank(A)}")
    >>> print(f"近似行列のランク: {matrix_rank(A_approx)}")
    """
    A = np.array(matrix, dtype=float)
    
    # 特異値分解
    U, S, Vt = np.linalg.svd(A, full_matrices=False)
    
    # 指定されたランクまでの成分のみを使用
    S_truncated = np.zeros_like(S)
    S_truncated[:rank] = S[:rank]
    
    # 行列を再構成
    approximation = U @ np.diag(S_truncated) @ Vt
    
    return approximation


if __name__ == "__main__":
    # サンプル実行
    print("=== 特異値分解のサンプル ===\n")
    
    # テスト行列
    A = [[1, 2, 3],
         [4, 5, 6]]
    
    print("元の行列 A:")
    print(np.array(A))
    print()
    
    # 特異値分解
    U, S, Vt = svd(A)
    
    print("左特異ベクトル U:")
    print(U)
    print()
    
    print("特異値 S:")
    print(S)
    print()
    
    print("右特異ベクトルの転置 Vt:")
    print(Vt)
    print()
    
    # 行列の再構成
    # full_matrices=True の場合、Σ を適切なサイズに調整する必要がある
    Sigma = np.zeros((U.shape[1], Vt.shape[0]))
    Sigma[:len(S), :len(S)] = np.diag(S)
    A_reconstructed = U @ Sigma @ Vt
    
    print("再構成された行列 A (U * Σ * Vt):")
    print(A_reconstructed)
    print()
    
    # 辞書形式での取得
    result = svd_dict(A, full_matrices=False)
    print("辞書形式の結果（縮約版）:")
    print(f"特異値: {result['S']}")
    print()
    
    # ランクの計算
    rank = matrix_rank(A)
    print(f"行列のランク: {rank}")
    print()
    
    # 条件数の計算
    cond = condition_number(A)
    print(f"条件数: {cond:.2f}")
    print()
    
    # 低ランク近似
    A_large = [[1, 2, 3, 4],
               [5, 6, 7, 8],
               [9, 10, 11, 12]]
    
    print("元の行列（3x4）:")
    print(np.array(A_large))
    print()
    
    A_approx = low_rank_approximation(A_large, rank=2)
    print("ランク2での近似:")
    print(A_approx)
