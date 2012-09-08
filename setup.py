from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.readlines()

with open('README') as f:
    long_description = f.read()

setup(
        name='taskweb',
        version='0.2',
        install_requires=requirements,
        description="Django-based web front-end to taskwarrior",
        long_description=long_description,
        author="Ryan Campbell",
        author_email="campbellr@gmail.com",
        url="http://github.com/campbellr/taskweb",
        packages=find_packages(),
        zip_safe=False,
        include_package_data=True,
        )
