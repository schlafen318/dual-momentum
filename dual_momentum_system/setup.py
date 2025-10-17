"""
Setup script for the Dual Momentum Backtesting Framework.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file) as f:
        requirements = [
            line.strip() for line in f
            if line.strip() and not line.startswith('#')
        ]

setup(
    name="dual_momentum_framework",
    version="1.0.0",
    description="Enterprise-grade dual momentum backtesting framework with plugin architecture",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Dual Momentum Framework Team",
    author_email="",
    url="https://github.com/yourusername/dual_momentum_framework",
    packages=find_packages(include=['src', 'src.*']),
    package_dir={'': '.'},
    include_package_data=True,
    install_requires=requirements,
    extras_require={
        'dev': [
            'pytest>=7.4.0',
            'pytest-cov>=4.1.0',
            'pytest-asyncio>=0.21.0',
            'pytest-mock>=3.11.0',
            'black>=23.7.0',
            'ruff>=0.0.290',
            'mypy>=1.5.0',
        ]
    },
    python_requires='>=3.10',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Financial and Insurance Industry',
        'Intended Audience :: Developers',
        'Topic :: Office/Business :: Financial :: Investment',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
    ],
    keywords='backtesting trading momentum quantitative-finance algorithmic-trading',
    project_urls={
        'Documentation': 'https://github.com/yourusername/dual_momentum_framework',
        'Source': 'https://github.com/yourusername/dual_momentum_framework',
        'Tracker': 'https://github.com/yourusername/dual_momentum_framework/issues',
    },
)
