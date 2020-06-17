from setuptools import setup

setup(
    name="BGZipSeek",
    version="0.0.1",
    author="Adam Faulconbridge",
    author_email="afaulconbridge@googlemail.com",
    packages=["bgzipseek"],
    description="TODO.",
    long_description=open("README.md").read(),
    install_requires=[""],
    extras_require={
        "dev": [
            "pytest-cov",
            "flake8",
            "black",
            "pylint",
            "pip-tools",
            "pipdeptree",
            "pre-commit",
        ],
    },
)
