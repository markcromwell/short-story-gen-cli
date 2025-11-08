"""
Setup configuration for short-story-gen-cli
"""
from setuptools import setup, find_packages

setup(
    name="storygen",
    version="0.1.0",
    description="AI-powered short story generator CLI",
    author="Mark Cromwell",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=[
        "litellm>=1.45.0",
        "click>=8.0.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "storygen=storygen.cli:main",
        ],
    },
)
