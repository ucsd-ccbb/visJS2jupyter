from setuptools import setup, find_packages

setup(name = 'visJS2jupyter',
	packages=find_packages(exclude=[]),
	install_requires=['matplotlib','networkx','py2cytoscape']

)
