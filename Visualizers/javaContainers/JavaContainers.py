import com.sun.jdi

from wingdbJavaDebugEngine import IVisualizerManagerCallback
from wingdbJavaDebugEngine import IVisualizerFactory
from wingdbJavaDebugEngine import IVisualizer
from wingdbJavaDebugEngine import IVariableCallback

# -----------------------------------------------------------------------------

class KContainerBaseVisualizer( IVisualizer ):
    def __init__( self, vm ):
        self.d_vm = vm
        
    def isScalar( self ):
        return False

    def getValueString( self, type, value, varCallback ):
        return value.toString()

    def getChildrenCount( self, type, value, varCallback ):
        rawChildrenCount = varCallback.invokeValue( 'size', [] )
        childrenCount = rawChildrenCount.value()
        return childrenCount

# -----------------------------------------------------------------------------

class KStringConvertibleVisualizer( IVisualizer ):
    def __init__( self, vm ):
        self.d_vm = vm
        
    def isScalar( self ):
        return False

    def getValueString( self, type, value, varCallback ):
        str = varCallback.invokeValue( 'toString', [] )
        return str.toString()

    def getChildrenCount( self, type, value, varCallback ):
        return 0

# -----------------------------------------------------------------------------

class KFileVisualizer( IVisualizer ):
    def __init__( self, vm ):
        self.d_vm = vm
        
    def isScalar( self ):
        return False

    def getValueString( self, type, value, varCallback ):
        path = varCallback.invokeValue( 'getPath', [] )
        return path.toString()

    def getChildrenCount( self, type, value, varCallback ):
        return 0

# -----------------------------------------------------------------------------

class KThrowableVisualizer( IVisualizer ):
    def __init__( self, vm ):
        self.d_vm = vm
        
    def isScalar( self ):
        return False

    def getValueString( self, type, value, varCallback ):
        message = varCallback.invokeValue( 'getMessage', [] )
        return message.toString()

    def getChildrenCount( self, type, value, varCallback ):
        return 0

# -----------------------------------------------------------------------------

class KIndexedContainerVisualizer( KContainerBaseVisualizer ):
    def generateChildren( self, type, value, varCallback, childrenCount ):
        for index in range ( 0, childrenCount ):
            vmIndex = self.d_vm.mirrorOf( index )
            childValue = varCallback.invokeValue( 'get', [ vmIndex ] )
            if index == 0:
                childType = childValue.type()
                varCallback.setElementType( childType )
            label = '[' + str( index ) + ']'
            varCallback.addElement( label, childValue )

# -----------------------------------------------------------------------------

class KIterableContainerVisualizer( KContainerBaseVisualizer ):
    def generateChildren( self, type, value, varCallback, childrenCount ):
        iterator = varCallback.invokeValue( 'iterator', [] )
        for index in range ( 0, childrenCount ):
            childValue = varCallback.invokeByValue( iterator, 'next', [] )
            if index == 0:
                childType = childValue.type()
                varCallback.setElementType( childType )
            label = '[' + str( index ) + ']'
            varCallback.addElement( label, childValue )

# -----------------------------------------------------------------------------

class KAssociativeContainerVisualizer( KContainerBaseVisualizer ):
    def __init__( self, vm, storeEntryTypeCallback ):
        super( KAssociativeContainerVisualizer, self ).__init__( vm )
        self.d_storeEntryTypeCallback = storeEntryTypeCallback 
        
    def generateChildren( self, type, value, varCallback, childrenCount ):
        entrySet = varCallback.invokeValue( 'entrySet', [] )
        entryIterator = varCallback.invokeByValue( entrySet, 'iterator', [] )
        for index in range ( 0, childrenCount ):
            childValue = varCallback.invokeByValue( entryIterator, 'next', [] )
            if index == 0:
                childType = childValue.type()
                varCallback.setElementType( childType )
                
                if self.d_storeEntryTypeCallback:
                    associativeTypeName = type.name()
                    entryTypeName = childType.name()
                    self.d_storeEntryTypeCallback.addSupportedEntryType( 
                        associativeTypeName, entryTypeName )
                    self.d_storeEntryTypeCallback = None
                    
            label = '[' + str( index ) + ']'
            varCallback.addElement( label, childValue )

# -----------------------------------------------------------------------------

class KAssociativeContainerEntryVisualizer( KContainerBaseVisualizer ):
    def getValueString( self, type, value, varCallback ):
        entryKey = varCallback.invokeValue( 'getKey', [] )
        valueStr = entryKey.toString()
        entryValue = varCallback.invokeValue( 'getValue', [] )
        if entryValue:
            valueStr += " -> " + entryValue.toString()
        return valueStr.replace ( "\"", "'" )

    def getChildrenCount( self, type, value, varCallback ):
        return 2

    def generateChildren( self, type, value, varCallback, childrenCount ):
        entryKey = varCallback.invokeValue( 'getKey', [] )
        keyType = entryKey.type()
        varCallback.addField( 'key', 'key', keyType, entryKey )
        entryValue = varCallback.invokeValue( 'getValue', [] )
        valueType = entryValue.type()
        varCallback.addField( 'value', 'value', valueType, entryValue )

# -----------------------------------------------------------------------------

class KContainerVisualizerFactory( IVisualizerFactory ):
    def __init__( self, visualizerManagerCallback ):
        self.d_visualizerManagerCallback = visualizerManagerCallback
        
        self.d_stringConvertibleTypes = frozenset( [ 'java.lang.StringBuilder', 'java.lang.StringBuffer' ] )
        self.d_fileTypes = frozenset( [ 'java.io.File' ] )
        self.d_throwableTypes = frozenset( [ 'java.lang.Throwable' ] )
        
        self.d_indexedTypes = frozenset( [ 'java.util.List', 'java.util.AbstractList'
            , 'java.util.AbstractSequentialList', 'java.util.ArrayList'
            , 'java.util.Vector', 'java.util.LinkedList', 'java.util.Stack' ] )
            
        self.d_iterableTypes = frozenset( [ 'java.util.BlockingDeque', 'java.util.BlockingQueue'
            , 'java.util.Deque', 'java.util.List', 'java.util.NavigableSet'
            , 'java.util.Queue', 'java.util.Set', 'java.util.SortedSet'
            , 'java.util.AbstractCollection', 'java.util.AbstractQueue'
            , 'java.util.concurrent.ArrayBlockingQueue'
            , 'java.util.concurrent.ConcurrentLinkedQueue'
            , 'java.util.concurrent.DelayQueue', 'java.util.concurrent.LinkedBlockingDeque'
            , 'java.util.concurrent.LinkedBlockingQueue' 
            , 'java.util.concurrent.PriorityBlockingQueue', 'java.util.concurrent.PriorityQueue'
            , 'java.util.concurrent.SynchronousQueue'
            , 'java.util.AbstractSet'
            , 'java.util.concurrent.ConcurrentSkipListSet'
            , 'java.util.concurrent.CopyOnWriteArraySet' 
            , 'java.util.EnumSet', 'java.util.HashSet', 'java.util.LinkedHashSet' 
            , 'java.util.TreeSet', 'java.util.ArrayDeque' ] )
            
        self.d_associativeTypes = frozenset( [ 'java.util.Map', 'javax.script.Bindings'
            , 'java.util.ConcurrentMap', 'java.util.concurrent.ConcurrentNavigableMap'
            , 'javax.xml.ws.handler.LogicalMessageContext', 'javax.xml.ws.handler.MessageContext'
            , 'java.util.NavigableMap', 'javax.xml.ws.handler.soap.SOAPMessageContext'
            , 'java.util.SortedMap', 'java.util.AbstractMap', 'java.util.jar.Attributes'
            , 'java.security.AuthProvider', 'java.util.concurrent.ConcurrentHashMap'
            , 'java.util.concurrent.ConcurrentSkipListMap', 'java.util.EnumMap'
            , 'java.util.HashMap', 'java.util.Hashtable', 'java.util.IdentityHashMap'
            , 'java.util.LinkedHashMap', 'javax.print.attribute.standard.PrinterStateReasons'
            , 'java.util.Properties', 'java.security.Provider', 'java.awt.RenderingHints'
            , 'javax.script.SimpleBindings', 'javax.management.openmbean.TabularDataSupport'
            , 'java.util.TreeMap', 'javax.swing.UIDefaults', 'java.util.WeakHashMap' ] )

        # names of entry-type for associative containers are unpredictable, so we detect their
        # names dynamically - when user wants to show associative container the first time, we get
        # its entry-typename and store in self.d_associativeEntryTypes
        self.d_associativeEntryTypes = set()
        
        # in d_entryTypesStoredFor keep all associative types for which their entry types have been
        # stored ( in self.d_associativeEntryTypes )
        self.d_entryTypesStoredFor = set()

    def getSupportedTypes( self ):
        result = list ( self.d_stringConvertibleTypes ) \
            + list( self.d_fileTypes ) \
            + list( self.d_throwableTypes ) \
            + list( self.d_indexedTypes ) \
            + list( self.d_iterableTypes ) \
            + list( self.d_associativeTypes ) \
            + list( self.d_associativeEntryTypes )
        return result

    def allocVisualizer( self, vm, typeName ):
        if typeName in self.d_stringConvertibleTypes:
            return KStringConvertibleVisualizer( vm )
        elif typeName in self.d_fileTypes:
            return KFileVisualizer( vm )
        elif typeName in self.d_throwableTypes:
            return KThrowableVisualizer( vm )
        elif typeName in self.d_indexedTypes:
            return KIndexedContainerVisualizer( vm )
        elif typeName in self.d_iterableTypes:
            return KIterableContainerVisualizer( vm )
        elif typeName in self.d_associativeTypes:
            storeEntryTypeCallback = None
            if typeName not in self.d_entryTypesStoredFor:
                # name of entry-type for this associative container wasn't stored yet
                # it will be stored in addSupportedEntryType called as callback
                # from newly created KAssociativeContainerVisualizer object
                storeEntryTypeCallback = self
            return KAssociativeContainerVisualizer( vm, storeEntryTypeCallback )
        elif typeName in self.d_associativeEntryTypes:
            return KAssociativeContainerEntryVisualizer( vm )
        else:
            return None
            
    def addSupportedEntryType( self, associativeTypeName, entryTypeName ):
        assert associativeTypeName not in self.d_entryTypesStoredFor
        self.d_entryTypesStoredFor.add( associativeTypeName )
        self.d_associativeEntryTypes.add( entryTypeName )
        self.d_visualizerManagerCallback.addSupportedEntryType( self, entryTypeName )

# -----------------------------------------------------------------------------

def register_java_containers( visualizerManagerCallback ):
    return KContainerVisualizerFactory( visualizerManagerCallback )
