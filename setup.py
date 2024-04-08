# setup.py

from setuptools import setup, find_packages

setup(
    name="pixwise",
    version="0.1.0",
    packages=find_packages("src"),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": [
            "pixwise=pixwise.updater:main",
        ],
    },
    install_requires=[
        # Add your dependencies here
        # For example, 'requests', 'numpy', etc.
        "pytz",
    ],
)
