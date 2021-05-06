from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from setuptools import setup, find_packages
import osaka

setup(
    name="osaka",
    version=osaka.__version__,
    long_description=osaka.__description__,
    url=osaka.__url__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "requests>=2.7.0",
        "easywebdav==1.2.0",
        "filechunkio==1.6.0",
        "azure-storage-blob==1.4.0",
        "awscli>=1.17.1",
        "boto3>=1.11.1",
        "google-cloud-storage>=0.22.0",
        "six>=1.10.0",
        "configparser>=3.5.0",
        "future>=0.17.1",
        "backoff>=1.3.1",
        "mock>=4.0.3",
    ],
    entry_points={"console_scripts": ["osaka = osaka.__main__:main"]},
)
