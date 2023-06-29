from setuptools import setup, find_packages

with open('requirements.txt') as f:
  requirements = f.read().splitlines()

with open("README.md", "r", encoding="utf-8") as fh:
  long_description = fh.read()

setup(
    name='good_cache',
    version='0.1.32',
    url='https://github.com/arunsundaram50/good-cache.git',
    author='Arun Sundaram',
    author_email='arun_co@yahoo.com',
    long_description=long_description,
    long_description_content_type="text/markdown",
    description='Efficient function output caching based on input files and other parameters to the function.',
    packages=find_packages(where="src"),  # Specifies the src directory
    package_dir={"": "src"},  # Specifies the package directory
    install_requires=requirements,
)
