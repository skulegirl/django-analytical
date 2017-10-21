import os

try:
    from setuptools import setup, Command
except ImportError:
    from distutils.core import setup, Command

os.environ['DJANGO_SETTINGS_MODULE'] = 'analytical.tests.settings'

cmdclass = {}

try:
    from sphinx.setup_command import BuildDoc

    cmdclass['build_sphinx'] = BuildDoc
except ImportError:
    pass


class TestCommand(Command):
    description = "run package tests"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from analytical.tests.utils import run_tests

        run_tests()


cmdclass['test'] = TestCommand


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


import analytical as package  # noqa

setup(
    name='django-analytical',
    version=package.__version__,
    license=package.__license__,
    description='Analytics service integration for Django projects',
    long_description=read('README.rst'),
    author=package.__author__,
    author_email=package.__email__,
    packages=[
        'analytical',
        'analytical.templatetags',
        'analytical.tests',
        'analytical.tests.templatetags',
    ],
    keywords=['django', 'analytics'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.7',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.11',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    platforms=['any'],
    url='https://github.com/jcassee/django-analytical',
    download_url='https://github.com/jcassee/django-analytical/archive/master.zip',
    cmdclass=cmdclass,
    install_requires=[
        'Django>=1.7.0',
    ],
)
