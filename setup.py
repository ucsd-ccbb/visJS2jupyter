from setuptools import setup, find_packages

setup(
    name = "visJS-2-jupyter",
    version = "0.2",
    description= "visJS_2_jupyter is a tool to bring the interactivity of networks created with vis.js into jupyter notebook cells",
    url = "http://visjs.org/docs/network/",
    author="Brin Rosenthal (sbrosenthal@ucsd.edu), Mikayla Webster (m1webste@ucsd.edu), Aaron Gary (agary@ucsd.edu)",
    license = 'MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
    ],
    packages=find_packages()
)
