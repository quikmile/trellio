from pip.req import parse_requirements
from pip.download import PipSession
from setuptools import setup, find_packages

install_reqs = parse_requirements("requirements.txt", session=PipSession())
install_requires = [str(ir.req) for ir in install_reqs]

setup(
    name='trellio',
    packages=find_packages(),
    version='0.1',
    description='Python 3.5 Asyncio based microframework for microservice architecture',
    author='Abhishek Verma',
    author_email='ashuverma1989@gmail.com',
    url='https://github.com/technomaniac/trellio',  # use the URL to the github repo
    keywords=['asyncio', 'microservice', 'microframework', 'aiohttp'],  # arbitrary keywords
    install_requires=install_requires
)
