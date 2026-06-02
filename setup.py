"""setup.py — allows pip install -e . for local development."""

from setuptools import setup, find_packages

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

with open("requirements.txt") as f:
    # Strip comments and blank lines; ignore platform-conditional extras
    install_requires = [
        line.split(";")[0].strip()
        for line in f
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="hades-assistant",
    version="1.0.0",
    description="HADES — Human Assistance and Decision Engineering System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="ShubhamMohta29",
    python_requires=">=3.10",
    packages=find_packages(exclude=["tests*", "docs*"]),
    include_package_data=True,
    package_data={
        "": ["frontend/*.html", "frontend/*.css", "frontend/*.js"],
    },
    install_requires=install_requires,
    entry_points={
        "console_scripts": [
            "hades = main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: Microsoft :: Windows",
    ],
)
