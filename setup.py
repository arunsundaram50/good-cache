from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='good_cache',
    version='0.1.3',
    url='https://github.com/arunsundaram50/good-cache.git',
    author='Arun Sundaram',
    author_email='arun_co@yahoo.com',
    description='Efficient function output caching based on input files and other parameters to the function.',
    packages=find_packages(where="src"),  # Specifies the src directory
    package_dir={"": "src"},  # Specifies the package directory
    install_requires=requirements,
)
