import os
from setuptools import setup, find_packages


install_requires = [
        "obspy>=1.3.0", 
        "pygmt>=0.5.0",
        "pandas>=1.3.4",
        ]

setup(name="pysep",
      version='0.1.0',
      description="Rapid Basemaps geographically focused on Alaska",
      url="http://github.com/bch0w/based_alaska",
      author='Bryant Chow',
      license='GPL-3.0',
      python_requires=">=3.7",
      packages=find_packages(),
      install_requires=install_requires,
      zip_safe=False
      )
