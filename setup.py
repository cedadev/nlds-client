import os
from setuptools import setup, find_packages

with open(os.path.join(os.path.dirname(__file__), "README.md")) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name="nlds_client",
    version="0.0.2",
    packages=find_packages(),
    install_requires=[
        "requests",
        "requests_oauthlib",
        "click",
    ],
    include_package_data=True,
    license="LICENSE.txt",  # example license
    description=("Client libary and command line for CEDA Near-Line Data Store"),
    long_description=README,
    url="http://www.ceda.ac.uk/",
    author="Neil Massey",
    author_email="neil.massey@stfc.ac.uk",
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: RestAPI",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    entry_points={
        "console_scripts": ["nlds=nlds_client.nlds_client:main"],
    },
)
