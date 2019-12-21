# encoding: utf-8
 
# Pretty-printers for Boost (http://www.boost.org)
 
# Copyright (C) 2009 R�diger Sonderfeld <ruediger@c-plusplus.de>
 
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
 
#
# Inspired _but not copied_ from libstdc++'s pretty printers
#
 
import gdb
import re
 
class static:
    "Creates a 'static' method"
    def __init__(self, function):
        self.__call__ = function
 
boost_pretty_printers = [ ]
def register_pretty_printer(pretty_printer):
    "Registers a Pretty Printer"
    boost_pretty_printers.append(pretty_printer)
    return pretty_printer
 
@register_pretty_printer
class BoostIteratorRange:
    "Pretty Printer for boost::iterator_range (Boost.Range)"
    @static
    def supports(typename):
        return re.compile('^boost::iterator_range<.*>$').search(typename)
 
    class _iterator:
        def __init__(self, begin, end):
            self.item = begin
            self.end = end
            self.count = 0
 
        def __iter__(self):
            return self
 
        def advance(self):
            if self.item == self.end:
                raise StopIteration
            count = self.count
            self.count = self.count + 1
            elem = self.item.dereference()
            self.item = self.item + 1
            return ('[%d]' % count, elem)

        def next(self):
            return self.advance()

        def __next__(self):
            return self.advance()

 
    def __init__(self, typename, value):
        self.typename = typename
        self.value = value
 
    def children(self):
        return self._iterator(self.value['m_Begin'], self.value['m_End'])
 
    def to_string(self):
        begin = self.value['m_Begin']
        end = self.value['m_End']
        return '%s of length %d' % (self.typename, int(end - begin))
 
    def display_hint(self):
        return 'array'
 
@register_pretty_printer
class BoostOptional:
    "Pretty Printer for boost::optional (Boost.Optional)"
    regex = re.compile('^boost::optional<(.*)>$')
 
    @static
    def supports(typename):
        return BoostOptional.regex.search(typename)
 
    def __init__(self, typename, value):
        self.typename = typename
        self.value = value
 
    class _iterator:
        def __init__(self, member, empty):
            self.member = member
            self.done = empty
 
        def __iter__(self):
            return self
 
        def advance(self):
            if(self.done):
                raise StopIteration
            self.done = True
            return ('value', self.member.dereference())
 
        def next(self):
            return self.advance()

        def __next__(self):
            return self.advance()

 
    def children(self):
        initialized = self.value['m_initialized']
        if(not initialized):
            return self._iterator('', True)
        else:
            match = BoostOptional.regex.search(self.typename)
            if match:
                try:
                    membertype = gdb.lookup_type(match.group(1)).pointer()
                    member = self.value['m_storage']['dummy_']['data'].address.cast(membertype)
                    return self._iterator(member, False)
                except:
                    return self._iterator('', True)

    def display_hint(self):
        return "#" + self.to_string()
 
    def to_string(self):
        initialized = self.value['m_initialized']
        if(not initialized):
            return "<uninitialized optional>"
        else:
            return "<initialized optional>"
 
@register_pretty_printer
class BoostReferenceWrapper:
    "Pretty Printer for boost::reference_wrapper (Boost.Ref)"
    regex = re.compile('^boost::reference_wrapper<(.*)>$')
 
    @static
    def supports(typename):
        return BoostReferenceWrapper.regex.search(typename)
 
    def __init__(self, typename, value):
        self.typename = typename
        self.value = value
 
    def to_string(self):
        return '(%s) %s' % (self.typename, self.value['t_'].dereference())
 
@register_pretty_printer
class BoostTribool:
    "Pretty Printer for boost::logic::tribool (Boost.Tribool)"
    regex = re.compile('^boost::logic::tribool$')
 
    @static
    def supports(typename):
        return BoostTribool.regex.search(typename)
 
    def __init__(self, typename, value):
        self.typename = typename
        self.value = value
 
    def to_string(self):
        state = self.value['value']
        if(state == 0):
            return 'false'
        elif(state == 1):
            return 'true'
        else:
            return 'indeterminate'
 
@register_pretty_printer
class BoostScopedPtr:
    "Pretty Printer for boost::scoped/intrusive_ptr/array (Boost.SmartPtr)"
 
    regex = re.compile('^boost::(intrusive|scoped)_(ptr|array)<(.*)>$')
    @static
    def supports(typename):
        return BoostScopedPtr.regex.search(typename)  

    class _iterator:
        def __init__(self, member, empty):
            self.member = member
            self.done = empty
 
        def __iter__(self):
            return self
 
        def advance(self):
            if(self.done):
                raise StopIteration
            self.done = True
            return ('value', self.member.dereference())

        def next(self):
            return self.advance()

        def __next__(self):
            return self.advance()

    def __init__(self, typename, value):
        self.typename = typename
        self.value = value

    def children(self):
        if self.value['px'] == 0x0:
            return self._iterator('', True)
        match = BoostScopedPtr.regex.search(self.typename)
        if match:
            try:
                membertype = gdb.lookup_type(match.group(3)).pointer()
                member = self.value['px'].cast(membertype)
                return self._iterator(member, False)
            except:
                return self._iterator('', True)

    def display_hint(self):
        return "#" + self.to_string()
 
    def to_string(self):
        return '%s' % (self.value['px'],)
 
@register_pretty_printer
class BoostSharedPtr:
    "Pretty Printer for boost::shared/weak_ptr/array (Boost.SmartPtr)"
 
    regex = re.compile('^boost::(weak|shared)_(ptr|array)<(.*)>$')
    @static
    def supports(typename):
        return BoostSharedPtr.regex.search(typename)  
 
    class _iterator:
        def __init__(self, member, empty):
            self.member = member
            self.done = empty
 
        def __iter__(self):
            return self
 
        def advance(self):
            if(self.done):
                raise StopIteration
            self.done = True
            return ('value', self.member.dereference())

        def next(self):
            return self.advance()

        def __next__(self):
            return self.advance()

    def __init__(self, typename, value):
        self.typename = typename
        self.value = value

    def children(self):
        if self.value['px'] == 0x0:
            return self._iterator('', True)
        match = BoostSharedPtr.regex.search(self.typename)
        if match:
            try:
                membertype = gdb.lookup_type(match.group(3)).pointer()
                member = self.value['px'].cast(membertype)
                return self._iterator(member, False)
            except:
                return self._iterator('', True)

    def to_string(self):
        if self.value['px'] == 0x0:
            return '%s' % (self.value['px'],)
        countobj = self.value['pn']['pi_'].dereference()
        refcount = countobj['use_count_']
        weakcount = countobj['weak_count_']
        return '(count %d, weak count %d) %s' % (refcount, weakcount,self.value['px'])

    def display_hint(self):
        return "#" + self.to_string()
 
@register_pretty_printer
class BoostArray:
    "Pretty Printer for boost::array (Boost.Array)"
    regex = re.compile('^boost::array<(.*)>$');
    @static
    def supports(typename):
        return BoostArray.regex.search(typename)
 
    def __init__(self, typename, value):
        self.typename = typename
        self.value = value
 
    def to_string(self):
        return self.value['elems']
 
    def display_hint(self):
        return 'array'
 
@register_pretty_printer
class BoostVariant:
    "Pretty Printer for boost::variant (Boost.Variant)"
    regex = re.compile('^boost::variant<(.*)>$');
    @static
    def supports(typename):
        return BoostVariant.regex.search(typename)
 
    def __init__(self, typename, value):
        self.typename = typename
        self.value = value
 
    def to_string(self):
        m = BoostVariant.regex.search(self.typename)
        # TODO this breaks with boost::variant< foo<a,b>, bar >!
        types = map(lambda s: s.strip(), m.group(1).split(','))
        which = int(self.value['which_'])
        type = types[which]
        data = ''
        try:
            ptrtype = gdb.lookup_type(type).pointer()
            data = self.value['storage_']['data_']['buf'].address.cast(ptrtype)
        except:
            data = self.value['storage_']['data_']['buf']
        return '(boost::variant<...>) which (%d) = %s value = %s' % (which,
                                                                     type,
                                                                     data.dereference())

@register_pretty_printer
class BoostPath:
    "Pretty Printer for boost::path"
    regex = re.compile('^boost::filesystem::basic_path<(.*)>$')
 
    @static
    def supports(typename):
        return BoostPath.regex.search(typename)
 
    def __init__(self, typename, value):
        self.typename = typename
        self.value = value
 
    def to_string(self):
        return self.value['m_path']
 
def find_pretty_printer(value):
    "Find a pretty printer suitable for value"
    type = value.type
 
    if type.code == gdb.TYPE_CODE_REF:
       type = type.target()
 
    type = type.unqualified().strip_typedefs()
 
    typename = type.tag
    if typename == None:
        return None
 
    for pretty_printer in boost_pretty_printers:
        if pretty_printer.supports(typename):
            return pretty_printer(typename, value)
 
    return None
 
def register_boost_printers(obj):
    "Register Boost Pretty Printers."
    if obj == None:
        obj = gdb
    obj.pretty_printers.append(find_pretty_printer)
 