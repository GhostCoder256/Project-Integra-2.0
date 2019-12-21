# Pretty-printers for char arrays
 
# Copyright (C) 2010-2013 WinGDB.com
 
# Boost Software License - Version 1.0 - August 17th, 2003
 
# Permission is hereby granted, free of charge, to any person or organization
# obtaining a copy of the software and accompanying documentation covered by
# this license (the "Software") to use, reproduce, display, distribute,
# execute, and transmit the Software, and to prepare derivative works of the
# Software, and to permit third-parties to whom the Software is furnished to
# do so, all subject to the following:
 
# The copyright notices in the Software and this entire statement, including
# the above license grant, this restriction and the following disclaimer,
# must be included in all copies of the Software, in whole or in part, and
# all derivative works of the Software, unless such copies or derivative
# works are solely in the form of machine-executable object code generated by
# a source language processor.
 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE, TITLE AND NON-INFRINGEMENT. IN NO EVENT
# SHALL THE COPYRIGHT HOLDERS OR ANYONE DISTRIBUTING THE SOFTWARE BE LIABLE
# FOR ANY DAMAGES OR OTHER LIABILITY, WHETHER IN CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

# This visualizer displays some part of the array at the beginning as a string.
# Up to 64 characters are displayed.

import gdb
import re
 
class CharArrayPrinter:
    "Pretty Printer for char arrays"
 
    def __init__(self, value):
        self.d_value = value
 
    class _iterator:
        def __init__(self, value, bEmpty):
            self.d_value = value
            self.d_current = 0
            if bEmpty:
                self.d_size = 0
            else:    
                self.d_size = self.d_value.type.sizeof
 
        def __iter__(self):
            return self
 
        def advance(self):
            if self.d_current == self.d_size:
                raise StopIteration
            itemValue = self.d_value [ self.d_current ]
            self.d_current = self.d_current + 1
            return ( '[%d]' % ( self.d_current, ), itemValue )
 
        def next(self):
            return self.advance()

        def __next__(self):
            return self.advance()

    def children(self):
        try:
            return self._iterator(self.d_value, False)
        except:
            return self._iterator('', True)

    def display_hint(self):
        return "#" + self.to_string()
 
    def to_string(self):
        size = self.d_value.type.sizeof
        suffix = '"'
        if size > 64:
            size = 64
            suffix = ' ... "'
        v = self.d_value.string ( "ascii", "ignore", size ).replace ( "\x00", "\\\\000" )
        return '"' + v + suffix
 
def find_pretty_printer(value):
    "Find a pretty printer suitable for value"
    
    type = value.type.unqualified().strip_typedefs()

    if type.code == gdb.TYPE_CODE_ARRAY:
        itemType = type.target().unqualified().strip_typedefs()
        if ( itemType.code == gdb.TYPE_CODE_INT or itemType.code == gdb.TYPE_CODE_CHAR ) and itemType.sizeof == 1:
            return CharArrayPrinter ( value )
        else:
            return None
    else:
       return None

def register_charArray_printers(obj):
    "Register char array printers."
    if obj == None:
        obj = gdb
    obj.pretty_printers.append(find_pretty_printer)
 