from maya.api import OpenMaya as api2
from maya import cmds
from functools import partial

import os
import re
import static_lib
import mahelper


# --------------------------- Basic Maya IO --------------------------- #
# --------------------------------------------------------------------- #


# TODO make api and string friendly
class MIO_BasicIO(object):
    """
    Big convenient class for interacting with the maya api2 and cmds.
    Mostly for fluently switching between maya api2 objects and the maya commands.

    Only used as method container, doesn't need to be instatiated.
    """
    # ----------------------------------Construktor/Destruktor---------------------------------- #

    def __init__(self):
        # -can be used to register callbacks with an MIO instance
        #   or store an instance of the current selection, etc
        # eg:
        #     self.undo_callback = self.registerCallback(
        #         func=someFunction, callback_mode="Undo")

        #     self.redo_callback = self.registerCallback(
        #         func=someOtherFunction, callback_mode="Redo")
        pass

    def __del__(self):
        # -can be used to deregister the any callbacks or any other teardown stuff
        # eg:
        #   self.deregisterCallback(sel_callback=self.undo_callback)
        pass

    # ----------------------------------Callback Methods------------------------------- #

    @staticmethod
    def registerCallback(func, callback_mode):
        """
        Registers a new Maya callback with the given callback_mode string.
        If the given callback is invoked, the given function is called.
        The given function needs to have a buffer for Maya's returning Data.

        Args:
            func ([function]): Callable Function for callback, 
                needs *args-**kwargs for Maya's returning data.
            callback_mode ([String]): A String thats found in the api2.MEventMessage.getEventNames() List.  

        Returns:
            [long]: A Maya identifier for later removal of the callback.
        """

        sel_callback = api2.MEventMessage.addEventCallback(callback_mode, func)

        return sel_callback

    @staticmethod
    def deregisterCallback(sel_callback):
        """
        Deregisters the created Maya callback
        with the returned identifier from the 'registerCallback' function.

        Args:
            sel_callback ([long]): Identifier for Maya callback.

        Returns:
            [bool]: Returns true when successful, false when an error occured.
        """
        try:
            api2.MEventMessage.removeCallback(sel_callback)
            return True
        except Exception:
            return False

    # -------------------------------------GETTERs------------------------------------- #

    @staticmethod
    def get_dagPath(mobject):
        """
        Checks if the given MObject got a Dag Path,
        if you only retrieve the Mobject of scene Nodes the MGlobal.setActiveSelectionList()
        will not select the given objects. You need to get the Dag Path for exact selection.
        But if you give a MObject that doesn't lives in the scene DAG the command will throw an
        Exception 

        Args:
            mobject ([MObject]): Any MObject that is retrieved from various souces.

        Raises:
            RuntimeError: If any given Node or attribute does not exist or 
                          the object does not live in the DAG.

        Returns:
            [MDagPath]: If the Object is in the DAG it will return the path to it,
                        if not the MObject is returned because it's unique enough for selection.
        """
        mfnDag = api2.MFnDagNode(mobject)

        return mfnDag.getPath()

    @staticmethod
    def get_plugValue(plug):
        """
        Take the given plug, retrieve it's apiType and
        get the appropriate Function for retrieving it's value.

        Args:
            plug ([MPlug]): The plug from which the value should be retrieved.

        Raises:
            TypeError: When an unsupported type is given.

        Returns:
            [type]: The value type of the given Plug.
        """
        obj = plug.attribute()
        apiType = obj.apiType()
        #print obj.apiTypeStr

        try:
            apiFunc = _plugType_functions[apiType][0]
        except KeyError:
            raise TypeError("%s: Unsupported Type: %s" %
                            (plug.partialName(True, True, True, False, True, True),
                             static_lib.APIENUM_numToStr.get(apiType, apiType)))

        return apiFunc(plug, obj)

    @staticmethod
    def get_mobj(nodeName):
        """
        Gets the MObject of a Node from String, raises RuntimeError (Maya Style) if the Object
        doesn't exists.

        Args:
            nodeName ([String]): A String of the Nodename.

        Returns:
            [MObject]: Given Node if it exists.
        """
        return api2.MSelectionList().add(nodeName).getDependNode(0)

    @staticmethod
    def get_selectionIter(selection=None):
        """
        Convert a MSelectionList to a MItSelectionList to iterate over it's contents.

        Args:
            selection ([MSelectionList/None]): The MSelectionList which should be iteratet over or None
                                                if the whole Selection is meant.
        Returns:
            [MItSelectionList]: The iterator for the SelectionList or the whole scene.
        """
        if not selection:
            # -return a api2.MItDependencyNodes iterator, which holds all dependency nodes
            #   when no selection is given
            return MIO_MIterDependNodes()

        return api2.MItSelectionList(selection)

    @staticmethod
    def get_fileNameFromPath(filepath):
        """
        Get the file name without extension from a file path.

        Args:
            filepath ([String]): Path to desired file.

        Returns:
            [String]: File name without extension.
        """
        return os.path.splitext(os.path.basename(filepath))[0]

    @staticmethod
    def get_connectedTo_plugs(connections, incoming=True):
        """
        Gets the incoming/ outgoing Attribute Plugs by looping over the Connections and
        and querying the asDest/ asSrc Connections.      

        Args:
            connections ([MPlugArray]): Array containing all plugs with a active connection.
            incoming ([bool], optional): Determines if the incoming or outgoing connections should be retrieved. 
                                       Defaults to True.

        Returns:
            [List]: A List containing MPlugArrays with all Attributes from or to which
                    the Attribute is connected.
        """
        asDst = incoming
        asSrc = False if incoming else True

        newList = []
        for p in connections:
            connectedTo = p.connectedTo(asDst, asSrc)
            if connectedTo:
                if incoming:
                    newList.append((connectedTo, p))
                else:
                    newList.append((p, connectedTo))

        return newList

    @staticmethod
    def get_selection():
        return api2.MGlobal.getActiveSelectionList()

    @classmethod
    def get_names(cls, selection=None, check=None):
        """
        Get node names as a list of strings, if check supplied it only gives the names that
        return True when checked.

        Args:
            selection ([MSelectionList], optional): An api2.MSelectionList which doesn't need to hold anything. 
                                                    Defaults to None and searches for all Nodes.            
            check (Function, optional): Given a function that returns True or False it checks if a given node is legal.
                                        Defaults to True.

        Returns:
            [list]: List containing all node names.
        """
        sel = cls.get_selectionIter(selection)

        names = []
        for s in sel:
            mobj = s.getDependNode()
            mfn = api2.MFnDependencyNode(mobj)

            if check:
                if not check(mobj=mobj, mfn=mfn):
                    continue

            names.append(mfn.name())

        return names

    @classmethod
    def get_fileTextureName(cls, mobj, mfn):
        """
        Gets the file texture path from an attribute plug and returns the filename
        without extension.

        Args:
            mobj ([MObject]): MObject to the Node from which the file texture Path should be retrieved.
            mfn ([MFnFunctionSet]): The Function Set from the given MObject. e.g. MFnDependencyNode.

        Returns:
            [String]: A String containing the pure filename of the texture or 
                        if MPlug.isNull is True return None.
        """
        try:
            filePlug = cls.get_plug(mobj, mfn, "fileTextureName")
        except RuntimeError:
            return None

        return cls.get_fileNameFromPath(filePlug.asString())

    @classmethod
    def get_colorSpace(cls, mobj, mfn):
        """
        Gets the color space from an attribute plug and returns the it as a string.

        Args:
            mobj ([MObject]): MObject to the Node from which the file texture Path should be retrieved.
            mfn ([MFnFunctionSet]): The Function Set from the given MObject. e.g. MFnDependencyNode.

        Returns:
            [String]: A String containing the color space of the texture or 
                        if MPlug.isNull is True return None.
        """
        try:
            filePlug = cls.get_plug(mobj, mfn, "colorSpace")
        except RuntimeError:
            return None

        return filePlug.asString()

    @classmethod
    def get_plug(cls, mobject, mfn, attribute, parent=None):
        """
        Gets the attribute plug of a given MObject.
        Checks if the given attribute is a nested attribute and retrieves it recursively.
        Checks if the given attribute contains a Index (Number in Brackets), if yes remove it from the string
        and get the Plug of the Element with the given Index.

        Args:
            mobject ([MObject]): The Node from which the plug will be retrieved.
            mfn ([MFnFunctionSet]): The Function Set from the given MObject. e.g. MFnDependencyNode.
            attribute ([String]): The name of attribute that should be retrieved, given as standart string.
            parent ([MPlug], optional) : Retrieve the child plug of an attribute from this plug.

        Raises:
            RuntimeError: If any given Node or attributes don't exist.

        Returns:
            [MPlug]: The MPlug to the given attribute.
        """
        # -get the first attribute and leave the rest
        # -returns a list with atleast one string
        attributes = attribute.split(".", 1)

        # -create a Pattern thats searches for literal Brackets and any number in it
        # -store the result in match, None if no match exists
        matchPattern = re.compile(r'\[[0-9]+\]')
        match = matchPattern.search(attribute)

        # -remove the Brackets from the attribute name and
        #   restore it in attribute, if no match reassign it
        attribute = attributes[0].replace(
            match.group(0), "") if match else attributes[0]

        # -get the attribute on the node and retrieve the plug
        attrObj = mfn.attribute(attribute)
        attrPlug = api2.MPlug(mobject, attrObj)

        if attrPlug.isNull:
            raise RuntimeError("(%s): Object does not exist" % attribute)

        if parent:
            attrPlug = parent.child(attrObj)

        if match:
            numIndex = int(match.group(0)[1:-1])
            attrPlug = attrPlug.elementByLogicalIndex(numIndex)

        if len(attributes) > 1:
            attrPlug = cls.get_plug(mobject, mfn, attributes[1], attrPlug)

        return attrPlug

    # -------------------------------------SETTERs------------------------------------- #

    @staticmethod
    def set_plugValue(plug, value):
        """
        Take the given plug, retrieve it's apiType and
        get the appropriate Function for setting it's value.

        Args:
            plug ([MPlug]): The plug which should be set.
            value ([type]): The value which should be set.

        Raises:
            TypeError: When an unsupported type is given.
        """
        obj = plug.attribute()
        apiType = obj.apiType()
        #print obj.apiTypeStr

        try:
            apiFunc = _plugType_functions[apiType][1]
        except KeyError:
            raise TypeError("%s: Unsupported Type: %s" %
                            (plug.partialName(True, True, True, False, True, True),
                             static_lib.APIENUM_numToStr.get(apiType, apiType)))

        return apiFunc(plug, value, obj)

    # --------------------------------Convenient Methods------------------------------- #

    @classmethod
    def create_node(cls, nodeName, nodeType=static_lib.AIDEFAULT, shading=False, string=False):
        """
        Convenient Method for creating Nodes (also as ShadingNodes) and returning the new MObject.
        Defaults creates a new Arnold surface shader. 

        Args:
            nodeName ([String]): A String describing the desired Name for the Node, eg. 'myStandardSurface, etc'
            nodeType ([String]): A String describing the desired Type of the Node, 
                                    eg. 'aiStandardSurface', 'shadingEngine'.
            shading ([Bool]): Determines if node should a created as shading node.
            string ([Bool]): Determine if the return value is a Str.

        Returns:
            [MObject/String]: MObject containing the newly created Node or Name as String.
        """
        if shading:
            nodeStr = cmds.shadingNode(nodeType, name=nodeName, asShader=True)
        else:
            nodeStr = cmds.createNode(nodeType, name=nodeName)

        if string:
            return nodeStr

        return cls.get_mobj(nodeStr)

    @staticmethod
    def multiConnect(srcDestItems, force=False):
        """
        Convenient Method for connecting multiple attributes.
        Connecting of multiple attributes, given a List of MPlugs or Strings. 

        Args:
            srcDestItems ([Tuple]: 
                A Dictionary-like Tuple containing the Source and Destination Attribute which should be connected.
                Can give a Tuple of Strings or MPlugs which will be converted to Strings.
            force ([Bool], optional): If true disconnect any attribute that isn't freeToChange. Defaults to False. 
        """
        if not srcDestItems:
            return

        if not isinstance(srcDestItems[0][0], str):
            srcDestItems = [(str(src), str(dest))
                            for src, dest in srcDestItems]

        with mahelper.undo_chunk():
            print "Successfully connected:"
            for src, dest in srcDestItems:
                print "Src: {0}, Dest: {1}".format(src, dest)
                cmds.connectAttr(src, dest, force=force)

    @classmethod
    def multiSelect(cls, selection, clear=True):
        """
        Convenient Method for selecting multiple nodes, given a MSelectionList or list of Strings.

        Args:
            selection ([MSelectionList/List]): A MSelectionList containing all items which should be selected or
                                               a list containing all the node names.
        """

        if isinstance(selection, api2.MSelectionList):
            selection = cls.get_names(selection)

        with mahelper.undo_chunk():
            cmds.select(cl=clear)
            for node in selection:
                cmds.select(node, add=True)

    # -------------------------------------Methods------------------------------------- #

    @classmethod
    def keywordSelection(cls, keywords, mode=0, selection=None):
        """
        Keyword selection for searching and selection of nodes.
        This function holds different modes, for now there are only two,
        which can be expanded. Every search will be lowercase and string to string
        comparison.

        mode = 0;
        The default mode, when no mode is given or 0, it seaches all Node names and
        compares them to the given keywords. 

        mode = 1;
        The first mode is the File Texture Name search. It looks in the FileTexture Nodes after the 
        image filename and compares it to the given keywords. 

        mode = 2;
        Second mode gets the colorSpace as String and compares them to the keywords.

        Args:
            keywords (l[ist,tuple,set of strings]): An iterable item with search keywords. 
            mode ([int], optional): An int thats defining the search mode in the _funcs Dictinary, 
                                    more can be implimented throught the same approach.
            selection ([MSelectionList], optional): An api2.MSelectionList which doesn't need to hold anything. 
                                                    Defaults to None and searches for all Nodes.

        Returns:
            [MSelectionList]: An api2.MSelectionList containing all found nodes, 
                                empty when nothing found or given.
        """
        # -get a MItSelectionList to iterate over the nodes
        selection = cls.get_selectionIter(selection)
        newSelection = api2.MSelectionList()

        for node in selection:
            # -check if whole selection is true
            mobj = node.getDependNode()

            # -checks if the object got a Dag Path in the scene, raises Error if object doesn't live in the dag
            try:
                dag = cls.get_dagPath(mobj)
            except RuntimeError:
                # -use mobj instead for selection
                dag = mobj

            # -create a Dependency Node Function Set for the MObject to get it's name for key checking
            #   and further use if the mode requires it
            mfn = api2.MFnDependencyNode(mobj)

            if mode:
                # -if any int is given the statement is true
                # -pass the mode as key to the keywordSelection_functions
                #   dictinary which should take an instance of the class and
                #   the MObject, MFnFunctionSet
                # -if None continue to next iteration of the loop
                searchStr = _kwSel_functions[mode](mobj, mfn)
                if not searchStr:
                    continue
            else:
                # -get the Node Name
                searchStr = mfn.name()

            for k in keywords:
                if k.lower() in searchStr.lower():
                    newSelection.add(dag)

        return newSelection


#   KEYWORDSELECTION Function Switch-Case
# -private dictinary, only used within the MIO_BasicIO class
# -all methods need to be classmethods
# -all functions have to return a None if not used for selection
# -used to expand the keywordSelection modes, "future-proofing"
_kwSel_functions = {1: MIO_BasicIO.get_fileTextureName,
                    2: MIO_BasicIO.get_colorSpace}


# -------------------- Basic Maya Plug Interaction -------------------- #
# --------------------------------------------------------------------- #


class MIO_Plugs(object):
    """
    Convenient class for getting and setting Plug values.
    Most of these functions derive from pymel.dataTypes.getPlugValue.
    """

    # ----------------------------------GETTERs---------------------------------- #

    @staticmethod
    def getGroupedAttr(plug, _):
        return [MIO_BasicIO.get_plugValue(plug.child(i)) for i in range(plug.numChildren())]

    @staticmethod
    def getNumericAttr(plug, obj):
        nAttr = api2.MFnNumericAttribute(obj)
        dataType = nAttr.numericType()

        try:
            dataFunc = _numericDataTypes_functions[dataType][0]
        except KeyError:
            raise "%s: unknown numeric attribute type: %s" % (
                plug.partialName(True, True, True, False, True, True), dataType)

        return dataFunc(plug)

    @staticmethod
    def getUnitAttr(plug, obj):
        apiType = obj.apiType()

        if apiType in [api2.MFn.kDoubleLinearAttribute, api2.MFn.kFloatLinearAttribute]:
            val = plug.asMDistance()
            unit = api2.MDistance.uiUnit()

        elif apiType in [api2.MFn.kDoubleAngleAttribute, api2.MFn.kFloatAngleAttribute]:
            val = plug.asMAngle()
            unit = api2.MAngle.uiUnit()

        elif apiType == api2.MFn.kTimeAttribute:
            val = plug.asMTime()
            unit = api2.MTime.uiUnit()

        # as becomes a keyword in python 2.6
        return (val.asUnits(unit), unit)

    @staticmethod
    def getEnumAttr(plug, _):
        return MIO_Plugs.get_kInt(plug)

    @staticmethod
    def getTypedAttr(plug, obj):
        tAttr = api2.MFnTypedAttribute(obj)
        dataType = tAttr.attrType()

        try:
            dataFunc = _typedDataTypes_functions[dataType][0]
        except KeyError:
            raise TypeError("%s: Unsupported typed attribute: %s" %
                            (plug.partialName(True, True, True, False, True, True),
                             dataType))

        return dataFunc(plug)

    @staticmethod
    def get_kNumeric(plug):
        # all of the dynamic mental ray attributes fail here, but i have no idea why they are numeric attrs and not message attrs.
        # cmds.getAttr returns None, so we will too.
        try:
            dataObj = plug.asMObject()
            numFn = api2.MFnNumericData(dataObj)
        except RuntimeError:
            if plug.isArray():
                raise TypeError("%s: numeric arrays are not supported" %
                                plug.partialName(True, True, True, False,
                                                 True, True))
            else:
                raise TypeError("%s: attribute type is numeric, but its "
                                "data cannot be interpreted numerically" %
                                plug.partialName(True, True, True, False,
                                                 True, True))
        except:
            return None

        dataType = numFn.numericType()
        try:
            dataFunc = _numericDataTypes_functions[dataType][0]
        except KeyError:
            raise TypeError("%s: Unsupported typed attribute: %s" %
                            (plug.partialName(True, True, True, False, True, True),
                             dataType))

        return dataFunc(plug)

    @staticmethod
    def get_kNumericData(plug):
        dataObj = plug.asMObject()
        numFn = api2.MFnNumericData(dataObj)

        return numFn.getData()

    @staticmethod
    def get_kBool(plug):
        return plug.asBool()

    @staticmethod
    def get_kChar(plug):
        return plug.asChar()

    @staticmethod
    def get_kInt(plug):
        return plug.asInt()

    @staticmethod
    def get_kDouble(plug):
        return plug.asDouble()

    @staticmethod
    def get_kString(plug):
        return plug.asString()

    @staticmethod
    def get_kMatrix(plug):
        mobj = plug.asMObject()
        if mobj.apiType() != 0:
            return api2.MFnMatrixData(plug.asMObject()).matrix()

        return [api2.MFnMatrixData(plug.elementByLogicalIndex(i).asMObject()).matrix()
                for i in range(plug.evaluateNumElements())]

    @staticmethod
    def get_kArray(plug, MFnArray):
        try:
            dataObj = plug.asMObject()
        except RuntimeError:
            return []
        array = MFnArray(dataObj).array()
        return [array[i] for i in range(array.length())]

    # ----------------------------------SETTERs---------------------------------- #

    @staticmethod
    def setGroupedAttr(plug, value, _):
        return [MIO_BasicIO.set_plugValue(plug.child(i), value[i]) for i in range(plug.numChildren())]

    @staticmethod
    def setNumericAttr(plug, value, obj):
        nAttr = api2.MFnNumericAttribute(obj)
        dataType = nAttr.numericType()

        try:
            dataFunc = _numericDataTypes_functions[dataType][1]
        except KeyError:
            raise "%s: unknown numeric attribute type: %s" % (
                plug.partialName(True, True, True, False, True, True), dataType)

        return dataFunc(plug, value)

    @staticmethod
    def setUnitAttr(plug, value, obj):
        apiType = obj.apiType()

        if apiType in [api2.MFn.kDoubleLinearAttribute, api2.MFn.kFloatLinearAttribute]:
            unit = api2.MDistance.uiUnit()
            val = api2.MDistance(value, unit=unit)
            return plug.setMDistance(val)

        elif apiType in [api2.MFn.kDoubleAngleAttribute, api2.MFn.kFloatAngleAttribute]:
            unit = api2.MAngle.uiUnit()
            val = api2.MAngle(value, unit=unit)
            return plug.setMAngle(val)

        elif apiType == api2.MFn.kTimeAttribute:
            unit = api2.MTime.uiUnit()
            val = api2.MTime(value, unit=unit)
            return plug.setMTime(val)

        return None

    @staticmethod
    def setEnumAttr(plug, value, _):
        return MIO_Plugs.set_kInt(plug, value)

    @staticmethod
    def setTypedAttr(plug, value, obj):
        tAttr = api2.MFnTypedAttribute(obj)
        dataType = tAttr.attrType()

        try:
            dataFunc = _typedDataTypes_functions[dataType][1]
        except KeyError:
            raise TypeError("%s: Unsupported typed attribute: %s" %
                            (plug.partialName(True, True, True, False, True, True),
                             dataType))

        return dataFunc(plug, value)

    @staticmethod
    def set_kNumeric(plug, value):
        # all of kthe dynamic mental ray attributes fail here, but i have no idea why they are numeric attrs and not message attrs.
        # cmds.getAttr returns None, so we will too.
        try:
            dataObj = plug.asMObject()
            numFn = api2.MFnNumericData(dataObj)
        except RuntimeError:
            if plug.isArray():
                raise TypeError("%s: numeric arrays are not supported" %
                                plug.partialName(True, True, True, False,
                                                 True, True))
            else:
                raise TypeError("%s: attribute type is numeric, but its "
                                "data cannot be interpreted numerically" %
                                plug.partialName(True, True, True, False,
                                                 True, True))
        except:
            return None

        dataType = numFn.numericType()
        try:
            dataFunc = _numericDataTypes_functions[dataType][1]
        except KeyError:
            raise TypeError("%s: Unsupported typed attribute: %s" %
                            (plug.partialName(True, True, True, False, True, True),
                             dataType))

        return dataFunc(plug, value)

    @staticmethod
    def set_kNumericData(plug, value):
        dataObj = plug.asMObject()
        numFn = api2.MFnNumericData(dataObj)

        return numFn.setData(value)

    @staticmethod
    def set_kBool(plug, value):
        return plug.setBool(value)

    @staticmethod
    def set_kChar(plug, value):
        return plug.setChar(value)

    @staticmethod
    def set_kInt(plug, value):
        return plug.setInt(value)

    @staticmethod
    def set_kDouble(plug, value):
        return plug.setDouble(float(value))

    @staticmethod
    def set_kString(plug, value):
        return plug.setString(value)

    @staticmethod
    def set_kMatrix(plug, value):
        mfnMatrix = api2.MFnMatrixData(plug.asMObject())

        newMatrix = api2.MMatrix(value)
        mfnMatrix.set(newMatrix)

        return plug.setMObject(mfnMatrix.object())

    @staticmethod
    def set_kArray(plug, value, MFnArray, MArray):
        try:
            dataObj = plug.asMObject()
        except RuntimeError:
            return None

        mfnArray = MFnArray(dataObj)
        newArray = MArray(value)

        mfnArray.set(newArray)

        return plug.setMObject(mfnArray.object())


#   APIType Function Switch-Case
# -private dictinaries, only used within the MIO_Plugs class
# -get the given getter or setter function for the given apiType
_plugType_functions = {
    api2.MFn.kAttribute2Double: (MIO_Plugs.getGroupedAttr, MIO_Plugs.setGroupedAttr),
    api2.MFn.kAttribute2Float: (MIO_Plugs.getGroupedAttr, MIO_Plugs.setGroupedAttr),
    api2.MFn.kAttribute2Short: (MIO_Plugs.getGroupedAttr, MIO_Plugs.setGroupedAttr),
    api2.MFn.kAttribute2Int: (MIO_Plugs.getGroupedAttr, MIO_Plugs.setGroupedAttr),
    api2.MFn.kAttribute3Short: (MIO_Plugs.getGroupedAttr, MIO_Plugs.setGroupedAttr),
    api2.MFn.kAttribute3Int: (MIO_Plugs.getGroupedAttr, MIO_Plugs.setGroupedAttr),
    api2.MFn.kAttribute3Double: (MIO_Plugs.getGroupedAttr, MIO_Plugs.setGroupedAttr),
    api2.MFn.kAttribute3Float: (MIO_Plugs.getGroupedAttr, MIO_Plugs.setGroupedAttr),
    api2.MFn.kAttribute4Double: (MIO_Plugs.getGroupedAttr, MIO_Plugs.setGroupedAttr),
    api2.MFn.kCompoundAttribute: (MIO_Plugs.getGroupedAttr, MIO_Plugs.setGroupedAttr),
    api2.MFn.kDoubleLinearAttribute: (MIO_Plugs.getUnitAttr, MIO_Plugs.setUnitAttr),
    api2.MFn.kFloatLinearAttribute: (MIO_Plugs.getUnitAttr, MIO_Plugs.setUnitAttr),
    api2.MFn.kDoubleAngleAttribute: (MIO_Plugs.getUnitAttr, MIO_Plugs.setUnitAttr),
    api2.MFn.kFloatAngleAttribute: (MIO_Plugs.getUnitAttr, MIO_Plugs.setUnitAttr),
    api2.MFn.kTimeAttribute: (MIO_Plugs.getUnitAttr, MIO_Plugs.setUnitAttr),
    api2.MFn.kNumericAttribute: (MIO_Plugs.getNumericAttr, MIO_Plugs.setNumericAttr),
    api2.MFn.kEnumAttribute: (MIO_Plugs.getEnumAttr, MIO_Plugs.setEnumAttr),
    api2.MFn.kTypedAttribute: (MIO_Plugs.getTypedAttr, MIO_Plugs.setTypedAttr)
}

#   Typed Attribute Function Switch-Case
_typedDataTypes_functions = {
    api2.MFnData.kInvalid: (None, None),
    api2.MFnData.kNumeric: (MIO_Plugs.get_kNumeric, MIO_Plugs.set_kNumeric),
    api2.MFnData.kString: (MIO_Plugs.get_kString, MIO_Plugs.set_kString),
    api2.MFnData.kMatrix: (MIO_Plugs.get_kMatrix, MIO_Plugs.set_kMatrix),

    api2.MFnData.kStringArray: (partial(MIO_Plugs.get_kArray, MFnArray=api2.MFnStringArrayData),
                                partial(MIO_Plugs.set_kArray, MFnArray=api2.MFnStringArrayData, MArray=list)),

    api2.MFnData.kDoubleArray: (partial(MIO_Plugs.get_kArray, MFnArray=api2.MFnDoubleArrayData),
                                partial(MIO_Plugs.set_kArray, MFnArray=api2.MFnDoubleArrayData, MArray=api2.MDoubleArray)),

    api2.MFnData.kIntArray: (partial(MIO_Plugs.get_kArray, MFnArray=api2.MFnIntArrayData),
                             partial(MIO_Plugs.set_kArray, MFnArray=api2.MFnIntArrayData, MArray=api2.MIntArray)),

    api2.MFnData.kPointArray: (partial(MIO_Plugs.get_kArray, MFnArray=api2.MFnPointArrayData),
                               partial(MIO_Plugs.set_kArray, MFnArray=api2.MFnPointArrayData, MArray=api2.MPointArray)),

    api2.MFnData.kVectorArray: (partial(MIO_Plugs.get_kArray, MFnArray=api2.MFnVectorArrayData),
                                partial(MIO_Plugs.set_kArray, MFnArray=api2.MFnVectorArrayData, MArray=api2.MVectorArray))
}

#   Numeric Attribute Function Switch-Case
_numericDataTypes_functions = {
    api2.MFnNumericData.kBoolean: (MIO_Plugs.get_kBool, MIO_Plugs.set_kBool),
    api2.MFnNumericData.kChar: (MIO_Plugs.get_kChar, MIO_Plugs.set_kChar),
    api2.MFnNumericData.kShort: (MIO_Plugs.get_kInt, MIO_Plugs.set_kInt),
    api2.MFnNumericData.kInt: (MIO_Plugs.get_kInt, MIO_Plugs.set_kInt),
    api2.MFnNumericData.kLong: (MIO_Plugs.get_kInt, MIO_Plugs.set_kInt),
    api2.MFnNumericData.kByte: (MIO_Plugs.get_kInt, MIO_Plugs.set_kInt),
    api2.MFnNumericData.kFloat: (MIO_Plugs.get_kDouble, MIO_Plugs.set_kDouble),
    api2.MFnNumericData.kDouble: (MIO_Plugs.get_kDouble, MIO_Plugs.set_kDouble),
    api2.MFnNumericData.kAddr: (MIO_Plugs.get_kDouble, MIO_Plugs.set_kDouble),
    api2.MFnNumericData.k2Short: (MIO_Plugs.get_kNumericData, MIO_Plugs.set_kNumericData),
    api2.MFnNumericData.k2Int: (MIO_Plugs.get_kNumericData, MIO_Plugs.set_kNumericData),
    api2.MFnNumericData.k2Long: (MIO_Plugs.get_kNumericData, MIO_Plugs.set_kNumericData),
    api2.MFnNumericData.k2Float: (MIO_Plugs.get_kNumericData, MIO_Plugs.set_kNumericData),
    api2.MFnNumericData.k2Double: (MIO_Plugs.get_kNumericData, MIO_Plugs.set_kNumericData),
    api2.MFnNumericData.k3Float: (MIO_Plugs.get_kNumericData, MIO_Plugs.set_kNumericData),
    api2.MFnNumericData.k3Double: (MIO_Plugs.get_kNumericData, MIO_Plugs.set_kNumericData)
}


# ---------------------- Overridden API Classes ----------------------- #
# --------------------------------------------------------------------- #


class MIO_MIterDependNodes(api2.MItDependencyNodes):
    """
    Convenient Class that impliments the getDependNode function missing from MItDependencyNodes.
    It returns the result of thisNode(), the mobject of the node.
    Used to hold consistency between MItSelectionList and MItDependencyNodes
    in which way they retrieve mobjects. 
    """

    def getDependNode(self):
        return self.thisNode()
