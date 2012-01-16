from setuptools import setup, find_packages

requirements = [
        'Django >= 1.3',
        'djblets',
    ]

dependency_links = [
  'https://github.com/downloads/campbellr/taskw/taskw-0.1.8-campbellr2.tar.gz',
        ]
with open('README') as f:
    long_description = f.read()

setup(
        name='taskweb',
        version='0.1',
        install_requires=requirements,
        dependency_links=dependency_links,
        description="Django-based web front-end to taskwarrior",
        long_description=long_description,
        author="Ryan Campbell",
        author_email="campbellr@gmail.com",
        url="http://github.com/campbellr/taskweb",
        packages=find_packages(),
        zip_safe=False,
        include_package_data=True,
        )
