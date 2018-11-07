from setuptools import setup, find_packages
import osaka

setup(
    name='osaka',
    version=osaka.__version__,
    long_description=osaka.__description__,
    url=osaka.__url__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'requests>=2.7.0', 'easywebdav==1.2.0', 'fabric==1.10.1',
        'filechunkio==1.6.0','azure-storage==0.20.0', 'boto3>=1.2.6',
        'google-cloud-storage>=0.22.0', 'six>=1.10.0'
    ],
    entry_points={
          'console_scripts': [
              'osaka = osaka.__main__:main'
          ]
      }
)
