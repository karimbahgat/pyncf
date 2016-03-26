import pipy
 
packpath = "pyncf.py"
pipy.define_upload(packpath,
                   author="Karim Bahgat",
                   author_email="karim.bahgat.norway@gmail.com",
                   license="MIT",
                   name="Pyncf",
                   changes=["First alpha version"],
                   description="Pure Python NetCDF file reader and writer.",
                   url="http://github.com/karimbahgat/pyncf",
                   keywords="GIS spatial file format NetCDF",
                   classifiers=["License :: OSI Approved",
                                "Programming Language :: Python",
                                "Development Status :: 4 - Beta",
                                "Intended Audience :: Developers",
                                "Intended Audience :: Science/Research",
                                'Intended Audience :: End Users/Desktop',
                                "Topic :: Scientific/Engineering :: GIS"],
                   )

#pipy.generate_docs(packpath)
#pypi.upload_test(packpath)
#pypi.upload(packpath)

