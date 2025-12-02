from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import sys
import setuptools
import pybind11
import os

class get_pybind_include:
    def __str__(self):
        return pybind11.get_include()

ext_modules = [
    Extension(
        'game_accelerator',
        ['game_accelerator.cpp'],
        include_dirs=[
            get_pybind_include(),
        ],
        language='c++',
        extra_compile_args=['-O3', '-std=c++17'],
    ),
]

# Set compiler to g++ on Windows
if sys.platform == 'win32':
    os.environ['CC'] = 'g++'
    os.environ['CXX'] = 'g++'

setup(
    name='game_accelerator',
    version='1.0',
    author='Game Dev',
    description='C++ accelerated game functions',
    ext_modules=ext_modules,
    install_requires=['pybind11>=2.6.0'],
    cmdclass={'build_ext': build_ext},
    zip_safe=False,
)
