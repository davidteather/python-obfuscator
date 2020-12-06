from distutils.core import setup
import os.path
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="python_obfuscator",
    packages=setuptools.find_packages(),
    version="0.0.1",
    license="MIT",
    description="It's a python obfuscator.",
    author="David Teather",
    author_email="contact.davidteather@gmail.com",
    url="https://github.com/davidteather/tiktok-api",
    long_description=long_description,
    long_description_content_type="text/markdown",
    download_url="https://github.com/davidteather/python-obfuscator/tarball/master",
    keywords=["obfuscator"],
    install_requires=["regex"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    entry_points={"console_scripts": ["pyobfuscate=python_obfuscator.cli:cli"]},
)
