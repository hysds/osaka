
from setuptools import setup, find_packages
import osaka


def readme():
    with open("README.md") as f:
        return f.read()


setup(
    name="osaka",
    version=osaka.__version__,
    description=osaka.__description__,
    long_description_content_type="text/markdown",
    long_description=readme(),
    url=osaka.__url__,
    packages=find_packages(exclude=["tests.*", "tests"]),
    include_package_data=True,
    zip_safe=False,
    python_requires='>=3.10',
    install_requires=[
        "requests>=2.31.0",
        "easywebdav>=1.2.0",
        "azure-storage-blob>=12.18.0",
        "azure-identity>=1.15.0",  # For DefaultAzureCredential
        "awscli>=1.29.0",
        "boto3>=1.32.0",
        "google-cloud-storage>=2.13.0",
        "backoff>=2.2.1",
        "future>=1.0.0",  # Required for Python 2/3 compatibility
        'moto>=4.1.0',
        'mock>=5.1.0',
    ],
    extras_require={
        'test': [
            'pytest>=7.4.0',
            'pytest-cov>=4.1.0',
        ],
    },
    entry_points={
        "console_scripts": ["osaka = osaka.__main__:main"]
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
    ],
)
