import os
from setuptools import setup, find_packages

current_directory = os.path.dirname(__file__)

with open(os.path.join(current_directory, 'requirements.txt')) as fp:
    install_requires = fp.readlines()

with open(os.path.join(current_directory, 'test-requirements.txt')) as fp:
    tests_require = fp.readlines()

setup(
    name='neoalchemy',
    version='0.0.1',
    description='A SQLAlchemy-like object graph mapper for neo4j',
    long_description=open('README.rst').read(),
    author='Zach Kanzler',
    author_email='they4kman@gmail.com',
    zip_safe=True,
    url='http://github.com/they4kman/neoalchemy',
    license='MIT',
    packages=find_packages(),
    keywords='graph neo4j py2neo ORM',
    tests_require=tests_require,
    test_suite='nose.collector',
    install_requires=install_requires,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Database',
    ])
