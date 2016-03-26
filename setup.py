try: from setuptools import setup
except: from distutils.core import setup

setup(	long_description=open("README.rst").read(), 
	name="""Pyncf""",
	license="""MIT""",
	author="""Karim Bahgat""",
	author_email="""karim.bahgat.norway@gmail.com""",
	py_modules=['pyncf'],
	url="""http://github.com/karimbahgat/pyncf""",
	version="""0.1.0""",
	keywords="""GIS spatial file format NetCDF""",
	classifiers=['License :: OSI Approved', 'Programming Language :: Python', 'Development Status :: 4 - Beta', 'Intended Audience :: Developers', 'Intended Audience :: Science/Research', 'Intended Audience :: End Users/Desktop', 'Topic :: Scientific/Engineering :: GIS'],
	description="""Pure Python NetCDF file reader and writer.""",
	)
