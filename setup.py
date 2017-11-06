from setuptools import setup

setup(
    name = "visJS2jupyter",
    packages = ["visJS2jupyter"],
    version = "0.1.8",
    description= "visJS2jupyter is a tool to bring the interactivity of networks created with vis.js into Jupyter notebook cells",
	long_description="0.1.8 update: visJS2jupyter is now compatible with both networkx 1.11 and 2.0. Additionally, igraph is no longer needed to install visJS2jupyter.",
    url = "https://github.com/ucsd-ccbb/visJS2jupyter",
    author="Brin Rosenthal (sbrosenthal@ucsd.edu), Mikayla Webster (m1webste@ucsd.edu), Aaron Gary (agary@ucsd.edu), Julia Len (jlen@ucsd.edu)",
    author_email="sbrosenthal@ucsd.edu",
    keywords = ['Jupyter notebook', 'interactive', 'network'],
    license = 'MIT',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
    ]
)
