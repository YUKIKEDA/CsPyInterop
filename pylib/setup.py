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
