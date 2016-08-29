from setuptools import setup, find_packages

setup(
    name='trellio',
    packages=find_packages(),
    version='1.0.1',
    description='Python 3.5 Asyncio based microframework for microservice architecture',
    author='Abhishek Verma',
    author_email='ashuverma1989@gmail.com',
    url='https://github.com/technomaniac/trellio',
    keywords=['asyncio', 'microservice', 'microframework', 'aiohttp'],
    install_requires=['aiohttp', 'cchardet', 'multidict', 'python-json-logger', 'setproctitle==1.1.9', 'PyYAML']
)
