import codecs
import os
import errno
import shutil

from setuptools import setup
from setuptools.command.test import test as TestCommand
from ssixa import version as ver


class PyTest(TestCommand):
    def __init__(self, *args, **kwargs):
        TestCommand.__init__(self, *args, **kwargs)
        self.test_suite = True

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []

    def run_tests(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        raise SystemExit(errno)


with codecs.open('README.rst', encoding='utf8') as readme_file:
    README = readme_file.read()

with codecs.open('HISTORY.rst', encoding='utf8') as history_file:
    HISTORY = history_file.read().replace('.. :changelog:', '')

LONG_DESCRIPTION = README + '\n\n' + HISTORY

# requirements
install_requires = list(x.strip() for x in open('requirements.txt'))

# config file location creation
try:
    os.mkdir("/etc/ssixa")
except OSError as exc:
    if exc.errno != errno.EEXIST:
        raise

# data directory creation
try:
    os.mkdir("/var/lib/ssixa")
except OSError as exc:
    if exc.errno != errno.EEXIST:
        raise

# copy static and template files to locations
try:
    if os.path.exists("/var/www/static"):
        shutil.rmtree("/var/www/static")
    shutil.copytree("./ssixa/static/","/var/www/static")
except OSError as exc:
    if exc.errno != errno.EEXIST:
        raise
try:
    if os.path.exists("/var/www/templates"):
        shutil.rmtree("/var/www/templates")
    shutil.copytree("./ssixa/templates/","/var/www/templates")
except OSError as exc:
    if exc.errno != errno.EEXIST:
        raise

version = ver

setup(
    name='ssixa',
    version=version,
    description='SSI Gateway Solution',
    long_description=LONG_DESCRIPTION,
    author='Andreas Gruener',
    author_email='andreas.gruener@hpi.uni-potsdam.de',
    url='',
    packages=[
        'ssixa',
    ],
    zip_safe=False,
    keywords='ssixa',
    classifiers=[
        'Development Status :: 1 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
    ],
    cmdclass={'test': PyTest},
    install_requires=install_requires,
    tests_require=[
        'mock==2.0.0',
        'pytest-mock==1.6.0',
    ],
    entry_points={
    'console_scripts':['ssixa=ssixa.app:main']}
)
