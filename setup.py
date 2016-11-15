from setuptools import setup, find_packages

from trellio import __version__

setup(
    name='trellio',
    packages=find_packages(),
    version=__version__,
    description='Python 3 Asyncio based microframework for microservice architecture',
    author='Abhishek Verma',
    author_email='ashuverma1989@gmail.com',
    url='https://github.com/technomaniac/trellio',
    keywords=['asyncio', 'microservice', 'microframework', 'aiohttp'],
    install_requires=['again', 'async-retrial', 'asyncio-redis', 'aiohttp', 'cchardet', 'multidict', 'python-json-logger',
                      'setproctitle==1.1.9', 'PyYAML', 'uvloop', 'async-timeout', 'jsonstreamer', 'yarl']
)
