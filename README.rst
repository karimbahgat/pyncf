PyNetCDF
========

Pure Python NetCDF file reading and writing.

Introduction
------------

Inspired by the pyshp library, which provides simple pythonic and
dependency free data access to vector data, I wanted to create a library
for an increasingly popular file format in the raster part of the GIS
world, namely, NetCDF. From landuse to climate data, data sought after
by GIS practioners are increasingly often found only in the NetCDF
format.

My problem was that existing NetCDF libraries for python all rely on
interfacing with underlying C based implementations and can be hard to
setup outside the context of a full GDAL stack.

But most of the complexity of the format is in reading the metadata in
the header, which makes it easy to implement in python and should not
have to suffer from the slowness of python. Reading the actual data,
which NetCDF can store a lot of, is where one might argue that a C
implementation is needed for reasons of speed. But given that the main
purpose of the format data model is to provide efficient access to any
part of its vast data without having to read all of it via byte offset
pointers, this too can be easily and relatively efficiently implemented
in python without significant slowdowns. Besides, in many cases, the
main use of NetCDF is not for storing enormously vast raster arrays, but
rather for storing multiple relatively small raster arrays on different
themes, and of providing variations of these across some dimension, such
as time.

All of this makes it feasible and desirable with a pure python
implementation for reading and writing NetCDF files, expanding access to
the various data sources now using this format to a much broader set of
users and applications, especially in portable environments.

Status
------

Basic metadata and data extraction functional, but has not been tested
very extensively, so likely to contain some issues. No file writing
implemented yet. Only Classic and 64-bit formats supported so far,
though NetCDF-4 should be easy to implement.

Author
------

Karim Bahgat, 2016

Based on the file format description at:
http://www.unidata.ucar.edu/software/netcdf/docs/file\_format\_specifications.html

Changes
-------

0.1.0 (2016-03-26)
~~~~~~~~~~~~~~~~~~

-  First alpha version
