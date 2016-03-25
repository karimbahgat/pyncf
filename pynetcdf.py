"""
PyNetCDF

Pure Python NetCDF file reading and writing.

Note: Currently only support for reading, no writing, and the Classic and 64-bit formats.

# Introduction

Inspired by the pyshp library, which provides simple pythonic and dependency free data access to vector data,
I decided to create a library for an increasingly popular file format in the raster part of the GIS world,
namely, NetCDF. From landuse to climate data, data sought after by gis practioners are increasingly often
found only in the NetCDF format. Existing NetCDF libraries for python all rely on interfacing with
underlying c based implementations and can be hard to setup outside the context of a full GDAL stack.
But most of the complexity of the format is in reading the metadata in the header, which makes it easy
to implement in python without having to suffer from the slowness of python. Reading the actual data,
which NetCDF can store a lot of, is where one might argue that a C implementation is needed for reasons
of speed. But given that the main purpose of the format data model is to provide efficient access to
any part of its vast data without having to read all of it via byte offset pointers, this too can be
easily and relatively efficiently implemented in python without significant slowdowns. Besides, in
many cases, the main use of NetCDF is not for storing enormously vast raster arrays, but rather for
storing multiple relatively small raster arrays on different themes, and of providing variations of
these across some dimension, such as time. All of this makes it feasible and desirable with a pure
python implementation for reading and writing NetCDF files, expanding access to the various data
sources now using this format to a much broader set of users and applications, especially in portable
environments. 

Based on description at:
http://www.unidata.ucar.edu/software/netcdf/docs/file_format_specifications.html

Karim Bahgat, 2016
"""

import struct

class NetCDFClassic(object):


    # options
    endian = ">" # big endian


    # Constants

    ZERO = b"\x00\x00\x00\x00"
    STREAMING = b"\xFF\xFF\xFF\xFF"
    NC_DIMENSION = b"\x00\x00\x00\x0A"
    NC_VARIABLE = b"\x00\x00\x00\x0B"
    NC_ATTRIBUTE = b"\x00\x00\x00\x0C"
    PADDING_HEADER = b"\x00"


    # Dictionary loopups

    formatcodes = {b"\x01": "classic format",
                   b"\x02": "64-bit offset format"}

    dtypecodes = {   b"\x00\x00\x00\x01": "NC_BYTE",
                     b"\x00\x00\x00\x02": "NC_CHAR",
                     b"\x00\x00\x00\x03": "NC_SHORT",
                     b"\x00\x00\x00\x04": "NC_INT",
                     b"\x00\x00\x00\x05": "NC_FLOAT",
                     b"\x00\x00\x00\x06": "NC_DOUBLE",
                     }

    dtype_sizes = {"NC_BYTE": 1,
                   "NC_CHAR": 2,
                   "NC_SHORT": 2,
                   "NC_INT": 4,
                   "NC_FLOAT": 4,
                   "NC_DOUBLE": 8,
                   }
               
    tags = {"STREAMING": STREAMING,
            "ZERO": ZERO,
            "ABSENT": ZERO+ZERO,
            "NC_DIMENSION": NC_DIMENSION,
            "NC_ATTRIBUTE": NC_ATTRIBUTE,
            "NC_VARIABLE": NC_VARIABLE,
            "PADDING_HEADER": PADDING_HEADER,
            }


    ################################################

    def __init__(self, filepath):
        self.fileobj = open(filepath, "rb")
        self.fileobj.seek(0)

        self.read_header()


    # Basic reading

    def read_struct_type(self, struct_type, n):
        fmt = self.endian + bytes(n) + struct_type
        size = struct.calcsize(fmt)
        raw = self.read_bytes(size)
        value = struct.unpack(fmt, raw)
        if len(value) == 1:
            value = value[0]
        return value

    def read_chars(self, n):
        fmt = self.endian + bytes(n) + "s"
        size = struct.calcsize(fmt)
        raw = self.read_bytes(size)
        value = struct.unpack(fmt, raw)
        return value[0] # unpack returns a tuple

    def read_short(self, n):
        value = self.read_struct_type("h", n)
        return value

    def read_int(self, n):
        value = self.read_struct_type("i", n)
        return value

    def read_float(self, n):
        value = self.read_struct_type("f", n)
        return value

    def read_double(self, n):
        value = self.read_struct_type("d", n)
        return value

    def read_bytes(self, n):
        raw = self.fileobj.read(n)
        return raw


    # Header specific reading

    def read_chars_header(self, n):
        value = self.read_chars(n)
        self.read_size_leftover_padding_header(n)
        return value

    def read_bytes_header(self, n):
        value = self.read_bytes(n)
        self.read_size_leftover_padding_header(n)
        return value

    def read_short_header(self, n):
        value = self.read_struct_type("h", n)
        size = 2 * n   # a single short value is 2 bytes
        self.read_size_leftover_padding_header(size)
        return value


    # Positioning

    def set_checkpoint(self):
        self.pos = self.fileobj.tell()

    def return_to_checkpoint(self):
        self.fileobj.seek(self.pos, 0) # absolute position

    def read_size_leftover_padding_header(self, size):
        remainder = size % 4 # distance to next 4-byte
        if remainder:
            padding = 4 - remainder
            for _ in range(padding):
                padfound = self.read_tag("PADDING_HEADER")
                if not padfound:
                    raise Exception("Attempted to skip a byte as padding, but the byte did not have the padding signature")

    def round_nearest_4byte_boundary(self, size):
        padding = self.padding_to_nearest_4byte_boundary(size)
        if padding:
            size += padding
        return size

    def padding_to_nearest_4byte_boundary(self, size):
        remainder = size % 4 # distance to next 4-byte
        if remainder:
            padding = 4 - remainder
            return padding
        
    

    # Convenience
    
    def read_tag(self, tag):
        tagcode = self.tags[tag]
        tagsize = len(tagcode)
        raw = self.read_bytes(tagsize)
        if raw == tagcode:
            return tag

    def read_alternatives(self, *alternatives):
        """
        When there are multiple alternative method readings to be tried.
        Returns the first non-None result.
        """
        self.set_checkpoint()
        
        for alt in alternatives:
            result = alt()
            
            if result != None:
                return result

            self.return_to_checkpoint()

        else:
            raise Exception("Did not find any of the required alternatives.")


    # Multi Use

    def read_non_neg(self):
        return self.read_struct_type("I", 1) #unsigned ints

    def read_nelems(self):
        return self.read_non_neg()

    def read_name(self):
        nelems = self.read_nelems()
        namestring = self.read_namestring(nelems)
        return namestring

    def read_namestring(self, nelems): 
        # alternatively just read full string of length nelems
        namestring = self.read_chars(nelems)

        # check has at least one char
        assert len(namestring) > 0

        # validate first character
        self.check_id1(namestring[0])

        # validate subsequent items
        if len(namestring) > 1:
            for char in namestring[1:]:
                self.check_idn(char)

        # possibly decode to utf8
        # ...

        # skip padding to next 4-byte boundary
        self.read_size_leftover_padding_header(nelems)

        return namestring

    def check_id1(self, id1):        
        if self.check_alphanumeric(id1):
            pass
        elif id1 == "_":
            pass
        else:
            raise Exception("ID1 must be either alphanumeric or an underscore")

        return id1

    def check_idn(self, idn):        
        if self.check_alphanumeric(idn):
            pass
        elif idn in "_.@+-": # special 1
            pass
        elif idn in """ !"#$%&\()*,:;<=>?[\\]^'{|}~""": # special 2
            pass
        else:
            raise Exception("IDN must be either alphanumeric or a special character of type 1 or 2")

        return idn

    def check_alphanumeric(self, char):
        if char.isalnum(): # assumes this captures multibyte encoded chars
            return char
        else:
            return False

    def read_nc_type(self):
        nc_type = self.read_bytes(4)
        nc_type = self.dtypecodes[nc_type]
        return nc_type

    def read_values(self, dtype, n):
        if dtype == "NC_BYTE":
            values = self.read_bytes_header(n)
        elif dtype == "NC_CHAR":
            values = self.read_chars_header(n)
        elif dtype == "NC_SHORT":
            values = self.read_short_header(n)
        else:
            struct_type = dict(NC_SHORT="h",
                               NC_INT="i",
                               NC_FLOAT="f",
                               NC_DOUBLE="d",
                               )[dtype]
            values = self.read_struct_type(struct_type, n)
        return values

    ##########
    # Header
    ##########

    def read_header(self):
        self.header = dict()
        self.header.update( magic = self.read_magic(),
                            numrecs = self.read_numrecs()
                            )
        self.header.update( dim_list = self.read_dim_list() )
        self.header.update( gatt_list = self.read_gatt_list() )
        self.header.update( var_list = self.read_var_list() )

        return self.header


    # MISC

    def read_magic(self):
        chars = self.read_chars(3)
        if not chars == "CDF":
            raise Exception("Magic number must start with the characters C, D, F")
        versioncode = self.read_bytes(1)
        version = self.formatcodes[versioncode]
        return chars,version

    def read_numrecs(self):
        numrecs = self.read_alternatives(lambda: self.read_tag("STREAMING"),
                                         self.read_non_neg,
                                         )
        return numrecs


    # DIM LIST

    def read_dim_list(self):
        tag = self.read_alternatives(lambda: self.read_tag("ABSENT"),
                                      lambda: self.read_tag("NC_DIMENSION"),
                                      )
        if tag == "ABSENT":
            dim_list = []
            
        elif tag == "NC_DIMENSION":
            nelems = self.read_nelems()
            dim_list = [self.read_dim() for _ in range(nelems)]
            
        return dim_list

    def read_dim(self):
        dimdict = dict( name = self.read_name(),
                        dim_length = self.read_dim_length(),
                        )
        return dimdict

    def read_dim_length(self):
        dim_length = self.read_non_neg()
        return dim_length


    # GATT LIST

    def read_gatt_list(self):
        gatt_list = self.read_att_list()
        return gatt_list


    # ATT LIST

    def read_att_list(self):
        tag = self.read_alternatives(lambda: self.read_tag("ABSENT"),
                                      lambda: self.read_tag("NC_ATTRIBUTE"),
                                      )
        if tag == "ABSENT":
            att_list = []
            
        elif tag == "NC_ATTRIBUTE":
            nelems = self.read_nelems()
            att_list = [self.read_att() for _ in range(nelems)]
            
        return att_list

    def read_att(self):
        attdict = dict(name = self.read_name(),
                        nc_type = self.read_nc_type(),
                        nelems = self.read_nelems(),
                        )
        attdict["values"] = self.read_values(attdict["nc_type"], attdict["nelems"])
        return attdict


    # VAR LIST

    def read_var_list(self):
        tag = self.read_alternatives(lambda: self.read_tag("ABSENT"),
                                      lambda: self.read_tag("NC_VARIABLE"),
                                      )
        if tag == "ABSENT":
            var_list = []
            
        elif tag == "NC_VARIABLE":
            nelems = self.read_nelems()
            var_list = [self.read_var() for _ in range(nelems)]
            
        return var_list

    def read_var(self):
        vardict = dict( name = self.read_name(),
                        nelems = self.read_nelems(),
                        )
        vardict.update(
                        dimids = self.read_dimids(vardict["nelems"]),
                        vatt_list = self.read_vatt_list(),
                        nc_type = self.read_nc_type(),
                        vsize = self.read_vsize(),
                        begin = self.read_begin(),
                        )
        return vardict

    def read_dimids(self, nelems):
        dimids = [self.read_dimid() for _ in range(nelems)]
        return dimids

    def read_dimid(self):
        dimid = self.read_non_neg()
        return dimid

    def read_vatt_list(self):
        vatt_list = self.read_att_list()
        return vatt_list

    def read_vsize(self):
        vsize = self.read_non_neg()
        return vsize

    def read_begin(self):
        begin = self.read_offset()
        return begin

    def read_offset(self):
        if self.header["magic"][-1] == "classic format":
            offset = self.read_non_neg()
        elif self.header["magic"][-1] == "64-bit offset format":
            offset = self.read_struct_type("q", 1)
        return offset

    ########
    # Data
    ########

    def read_dimension_values(self, dimname):
        # only a single list of values, ie coordinate variables
        # ...
        pass

    def read_2ddata(self, varname, xdim="longitude", ydim="latitude", **extradims):
        """
        Extracts a 2-dimensional grid as a list of lists, with xdim increasing to the right (row values),
        and ydim increasing downwards (rows). 
        Must ensure that extradims fixes all other dimensions at a specified value.
        Possible to mix and mash dimensions, just remember to update the extradims accordingly. 
        """
        varinfo = self.get_varinfo(varname)
        xdiminfo = self.get_diminfo(xdim)
        ydiminfo = self.get_diminfo(ydim)

        # get dtype and size
        dtype = varinfo["nc_type"]
        dtypesize = self.dtype_sizes[dtype]

        # detect if record variable
        recvar = varinfo["name"] in (rv["name"] for rv in self.get_record_variables())

        # however, dont treat as record variable if using the record dimension as one of the two dimensions to extract
        firstdim = self.header["dim_list"][varinfo["dimids"][0]]
        recvar = firstdim["name"] not in (xdim,ydim)

        # calculate record size
        if recvar:
            recsize = self.calc_recsize()

        # TODO: something to do with padding after each record if only one record variable
        # ...

        # calculate product vector
        product_vector = self.calc_product_vector(varname)
        product_vector.append(1) # add 1 to allow the last coordinate to stay as is
        product_vector = product_vector[1:] # skew one to the left, so will line up with one higher dimension
        if recvar: product_vector = product_vector[1:] # skew again because the coordinate vector will drop its record coordinate

        # TODO: ensure that extradims and the x and y dims together contains indexes for all dimensions of the variable
        # ...

        # TODO: allow extradims to reference the actual dimension values by looking it up in its coordinate variable values
        # ...

        # find each value one at a time by computing offsets
        # TODO: calculate number of records if numrecs is STREAMING
        begin = varinfo["begin"]
        rows = []
        xdimlength = xdiminfo["dim_length"] or self.header["numrecs"] # record dimensions have length 0, so must use number of records
        ydimlength = ydiminfo["dim_length"] or self.header["numrecs"] # record dimensions have length 0, so must use number of records
        for y in range(ydimlength):
            row = []
            for x in range(xdimlength):
                indexdict = {xdim:x, ydim:y}
                indexdict.update(**extradims)

                #
                coord = [indexdict[self.header["dim_list"][dimid]["name"]] for dimid in varinfo["dimids"]] # aka index list for desired value
                if recvar: 
                    coord_mod = coord[1:] # drop the record coordinate so doesnt affect calculation
                else:
                    coord_mod = list(coord) 
                #print coord,coord_mod,product_vector
                
                offset = sum(( coordindex*prodvec for coordindex,prodvec in zip(coord_mod,product_vector) ))
                #print offset

                #
                offset *= dtypesize
                #print offset

                #
                offset += begin
                #print begin
                #print offset

                #
                if recvar:
                    recnum = coord[0]
                    offset += recnum * recsize
                    #print offset

                # fetch the data
                self.fileobj.seek(offset, 0)
                n = 1
                if dtype == "NC_CHAR":
                    value = self.read_chars(n)
                elif dtype == "NC_SHORT":
                    value = self.read_short(n)
                elif dtype == "NC_INT":
                    value = self.read_int(n)
                elif dtype == "NC_FLOAT":
                    value = self.read_float(n)
                elif dtype == "NC_DOUBLE":
                    value = self.read_double(n)

                # TODO: handle fill values
                # ...

                # apply transformations to value if given in attributes
                attr = self.get_varattr(varname, "scale_factor")
                if attr is not None:
                    value *= attr

                attr = self.get_varattr(varname, "add_offset")
                if attr is not None:
                    value += attr

                # add value
                    
                row.append(value)

            rows.append(row)
            
        # OPTIMIZATION: alternatively find the byte interval between every value to be read,
        # and instead batch read all values at once using a slice with a step value,
        # potentially implemented via a memoryview for optimal efficiency.
        # ...

        return rows

    def calc_product_vector(self, varname):
        varinfo = self.get_varinfo(varname)
        dimidlengths = [self.header["dim_list"][dimid]["dim_length"] for dimid in varinfo["dimids"]]
        product_vector = []
        prevlength = 1
        for dimidlength in reversed(dimidlengths):
            cumulprod = prevlength * dimidlength
            product_vector.append(cumulprod)
            prevlength = cumulprod
        product_vector = list(reversed(product_vector))

        recvar = self.header["dim_list"][varinfo["dimids"][0]]["dim_length"] == 0
        if recvar:
            product_vector[0] = 0

        return product_vector

    def calc_recsize(self):
        recvars = self.get_record_variables()
        recsize = sum((self.calc_vsize(varinfo["name"]) for varinfo in recvars))
        recsize = self.round_nearest_4byte_boundary(recsize)
        return recsize

    def calc_vsize(self, varname):
        product_vector = self.calc_product_vector(varname)
        varinfo = self.get_varinfo(varname)
        dtypesize = self.dtype_sizes[varinfo["nc_type"]]
        vsize = max(product_vector) * dtypesize
        print "vsize", product_vector, vsize, self.get_varinfo(varname)["vsize"]
        vsize = self.round_nearest_4byte_boundary(vsize)
        return vsize

    #############
    # Meta utilities
    #############

    def get_varinfo(self, varname):
        for vardict in self.header["var_list"]:
            if varname == vardict["name"]:
                return vardict

    def get_varattr(self, varname, attr):
        for attrdict in self.get_varinfo(varname)["vatt_list"]:
            if attr == attrdict["name"]:
                return attrdict["values"]

    def get_diminfo(self, dimname):
        for dimdict in self.header["dim_list"]:
            if dimname == dimdict["name"]:
                return dimdict

    def get_record_dimension(self):
        for dimdict in self.header["dim_list"]:
            if dimdict["dim_length"] == 0:
                return dimdict

    def get_nonrecord_variables(self):
        record_vars = self.get_record_variables()
        nonrecord_vars = [var for var in self.header["var_list"] if var not in record_vars]
        return nonrecord_vars

    def get_record_variables(self):
        record_vars = []
        coord_vars = self.get_coordinate_variables()
        
        for vardict in self.header["var_list"]:
            dimids = vardict["dimids"]
            dimid = dimids[0] # must be first dimension 
            diminfo = self.header["dim_list"][dimid]
            if diminfo["dim_length"] == 0 and vardict["name"] not in (v["name"] for v in coord_vars): 
                # record variables are those whose first dimension has a length of 0, ie unlimited
                # and that are not a coordinate variable
                record_vars.append(vardict)

        return record_vars

    def get_coordinate_variables(self):
        coord_vars = []
        
        for vardict in self.header["var_list"]:
            dimids = vardict["dimids"]
            if len(dimids) == 1:
                dimid = dimids[0]
                diminfo = self.header["dim_list"][dimid]
                if vardict["name"] == diminfo["name"]:
                    # coordinate variables are those with only a single dimension and the same name as that same dimension
                    coord_vars.append(vardict)

        return coord_vars


if __name__ == "__main__":
    filepath = "ECMWF_ERA-40_subset.nc"
    obj = NetCDFClassic(filepath)

    import pprint
    #pprint.pprint(obj.header)

    varname = "tcw" #msl,tcc,p2t,tcw
    varinfo = obj.get_varinfo(varname)
    pprint.pprint(varinfo)
    rows = obj.read_2ddata(varname, time=0) # temperature kalvin
    print repr(rows)[:900]
    print repr(rows[::50])[:900]
    print repr(rows)[-900:]
    print len(rows), len(rows[0])

    import PIL, PIL.Image
    img = PIL.Image.new("F",(len(rows[0]),len(rows)))
    pxls = img.load()
    #img.putdata([v for row in rows for v in row])
    for y,row in enumerate(rows):
        for x,v in enumerate(row):
            #print x,y
            pxls[x,y] = v

    import pythongis as pg
    rast = pg.raster.data.RasterData(image=img, cellwidth=1, cellheight=-1, xy_cell=(0,0), xy_geo=(0,0))
    rast.view(1000,500,gradcolors=[(0,255,0),(255,255,0),(255,0,0)])


    
