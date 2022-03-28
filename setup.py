from setuptools import setup
import os

VERSION = "0.1"


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="datasette-auth0",
    description="Datasette plugin that authenticates users using Auth0",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Simon Willison",
    url="https://github.com/simonw/datasette-auth0",
    project_urls={
        "Issues": "https://github.com/simonw/datasette-auth0/issues",
        "CI": "https://github.com/simonw/datasette-auth0/actions",
        "Changelog": "https://github.com/simonw/datasette-auth0/releases",
    },
    license="Apache License, Version 2.0",
    classifiers=[
        "Framework :: Datasette",
        "License :: OSI Approved :: Apache Software License",
    ],
    version=VERSION,
    packages=["datasette_auth0"],
    entry_points={"datasette": ["auth0 = datasette_auth0"]},
    install_requires=["datasette"],
    extras_require={"test": ["pytest", "pytest-asyncio", "pytest-httpx"]},
    python_requires=">=3.7",
)
