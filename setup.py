# -*- coding: utf-8 -*-
import ast
import re
from os import getcwd, path

from pip.download import PipSession
from pip.req import parse_requirements
from setuptools import setup, find_packages

if not path.dirname(__file__):  # setup.py without /path/to/
    _dirname = getcwd()  # /path/to/
else:
    _dirname = path.dirname(path.dirname(__file__))


def read(name, default=None, debug=True):
    try:
        filename = path.join(_dirname, name)
        with open(filename) as f:
            return f.read()
    except Exception as e:
        err = "%s: %s" % (type(e), str(e))
        if debug:
            print(err)
        return default


def lines(name):
    txt = read(name)
    return map(
        lambda l: l.lstrip().rstrip(),
        filter(lambda t: not t.startswith('#'), txt.splitlines() if txt else [])
    )


install_reqs = parse_requirements("./requirements/base.txt", session=PipSession())
install_requires = [str(ir.req).split('==')[0] for ir in install_reqs]

with open('trellio/__init__.py', 'rb') as i:
    version = str(ast.literal_eval(re.compile(r'__version__\s+=\s+(.*)').search(i.read().decode('utf-8')).group(1)))

setup(
    name='trellio',
    packages=find_packages(exclude=['examples', 'tests']),
    version=version,
    description='Python 3 asyncio based micro-framework for micro-service architecture',
    author='Abhishek Verma, Nirmal Singh',
    author_email='ashuverma1989@gmail.com, nirmal.singh.cer08@itbhu.ac.in',
    url='https://github.com/technomaniac/trellio',
    keywords=['asyncio', 'microservice', 'microframework', 'aiohttp'],
    package_data={'requirements': ['*.txt']},
    install_requires=install_requires
)
