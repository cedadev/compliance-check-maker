from setuptools import setup, find_packages
from check_maker import __version__


def readme():
    with open('README.md') as f:
        return f.read()

def license():
    with open('LICENSE') as f:
        return f.read()


reqs = [line.strip() for line in open('requirements.txt')]

GIT_REPO = "https://github.com/cedadev/compliance-check-maker"

setup(
    name                 = "compliance-check-maker",
    version              = __version__,
    description          = "Tool to write project-specific plugins and data specifications for the IOOS compliance checker",
    long_description     = readme(),
    license              = license(),
    author               = "Ag Stephens",
    author_email         = "ag.stephens@stfc.ac.uk",
    url                  = GIT_REPO,
    packages             = find_packages(),
    install_requires     = reqs,
    tests_require        = ['pytest'],
    classifiers          = [
        'Development Status :: 2 - ???',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: BSD 3-Clause License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering',
    ],
    include_package_data = True,
    scripts=['write_checkers.py'],
    entry_points         = {
        'console_scripts': [
            'write-checkers = write_checkers:main'
        ],
    },
    package_data         = {
        'checklib': ['test/example_data/*/*'],
    }
)
