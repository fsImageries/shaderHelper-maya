from basicMayaIO import MIO_BasicIO as MIO
from maya.api import OpenMaya as api2
from PySide2 import QtCore, QtWidgets

import static_lib


class BaseNode(object):
    """
    Helper Object-representation of a Dependency Node.
    Used for easy access of node information.

    Args:
        node ([MObject, String]): Maya object representing the Dependency Node or Name of it.
    """

    def __init__(self, node):
        self.mobject = node if isinstance(
            node, api2.MObject) else MIO.get_mobj(node)

        self.nodeMfn = api2.MFnDependencyNode(self.mobject)
        self.name = self.nodeMfn.name()
        self.type = self.nodeMfn.typeName
        self.typeID = self.nodeMfn.typeId
        self.connections = self.nodeMfn.getConnections()
        self.incomingConnections = MIO.get_connectedTo_plugs(
            self.connections, incoming=True)
        self.outgoingConnections = MIO.get_connectedTo_plugs(
            self.connections, incoming=False)

    def __str__(self):
        return self.name

    def get_plugFrStr(self, attrName):
        """
        Get plug from attribute string.
        Pass needed informaton from the BaseNode class.

        Args:
            attrName ([String]): The attribute which should be retrieved.

        Returns:
            [MPlug]: Returns the wanted plug.
        """
        return MIO.get_plug(self.mobject, self.nodeMfn, attrName)

    # ----------------------------------Converting Methods---------------------------------- #

    def get_map(self):
        """
        Gets the corrosponding conversion map to convert the attributes on this node.

        Returns:
            [Dict]: A Src-Attribute to Dest-Attribute Dictionary.
        """
        return static_lib.LEGALTYPES_MAPS[str(self.type).lower()]

    def get_corrospondingAttr(self, srcNode, attrPlug):
        """
        Gets the corrosponding Plug of a given Attribute on this Shader instance and returns it.
        If None can be found an empty MPlug is returned.

        Args:
            srcNode ([shader.BaseNode]): BaseNode of the Node from which the Attribute is taken.
            attrPlug ([MPlug]): Source Attribute from which the new Attribute should be retrieved.

        Returns:
            [MPlug]: The newly found MPlug or an empty one if None can be found.
        """
        if self.type != "aiStandardSurface":
            raise NotImplementedError(
                "Mapping is only for aiStandardSurface as Destination implemented.")

        attrName = attrPlug.partialName(useLongNames=True)
        nodeType = str(srcNode.type).lower()

        if nodeType in static_lib.LEGALTYPES:
            mapping = srcNode.get_map()
            newAttr = mapping.get(attrName)

            if newAttr:
                return MIO.get_plug(self.mobject, self.nodeMfn, newAttr)

        try:
            return MIO.get_plug(self.mobject, self.nodeMfn, attrName)
        except RuntimeError:
            print "(%s.%s) : Attribute not implemented yet." % (
                srcNode.name, attrName)

            return api2.MPlug()

    def print_conns(self, incoming=True, conns=None):
        if not conns:
            conns = self.incomingConnections if incoming else self.outgoingConnections
        print "Incoming:" if incoming else "Outgoing:"
        for src, dest in conns:
            print "%s --> %s" % (
                [str(plug) for plug in src] if hasattr(
                    src, "__getitem__") else [str(src)],
                [str(plug) for plug in dest] if hasattr(dest, "__getitem__") else [str(dest)])


class CustomLineEdit(QtWidgets.QLineEdit):
    focusChange = QtCore.Signal()

    def focusInEvent(self, event):
        self.focusChange.emit()
        super(CustomLineEdit, self).focusInEvent(event)
