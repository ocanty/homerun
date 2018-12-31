from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

with open('requirements.txt') as requirements:
    install_requires = requirements.readlines()

setup(
    name='homerun',
    version='0.1.0',
    description='Easy to use Cloudflare dynamic DNS',
    long_description=readme,
    author='Oisin Canty',
    author_email='git@ocanty.com',
    url='https://github.com/ocanty/homerun',
    license=license,
    packages=find_packages(),
    install_requires=install_requires
)