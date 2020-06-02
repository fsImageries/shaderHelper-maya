from maya.api import OpenMaya as api2

try:
    # -try to import from namespace if you got the library already installed
    from basicMayaIO import MIO_BasicIO as MIO
    from baseClasses import BaseNode
    import customTypes as ct
except ImportError:
    # -import from package if None can be found
    from scripts.basicMayaIO import MIO_BasicIO as MIO
    from scripts.baseClasses import BaseNode
    from scripts import customTypes as ct

import sys
import traceback


class NodeConvertCmd(api2.MPxCommand):
    """
    Node convert commandline command.
    Rewire the incoming/ outgoing connections 
    from the source object to the destination object.
    After that go over the given attributes, get the needed mapping
    and set all values which aren't connected.

    Args:
        source ([String]): The source node which should be converted.
        dest ([String]): The destionation node which will get converted to.

    Raises:
        RuntimeError: When wrong arguments are given or any of the nodes don't exist.
    """
    COMMAND_NAME = "nodeConvert"

    def __init__(self):
        super(NodeConvertCmd, self).__init__()
        self.undo = True
        self.modi = api2.MDGModifier()

        self.new_src_dest_items = ct.LinkedList()
        self.old_src_dest_items = ct.LinkedList()
        self.connected_attrs = ct.LinkedList()
        self.plugs = None

    def doIt(self, arg_list):
        """
        Get the source and dest nodes and retrieve all the needed connections and attribute
        conversions.
        If any of the functions return False it will return without calling redoIt.

        Args:
            arg_list ([MArgList]): Maya Object containing all the data given to the command.
        """
        src, dst = self.parse_args(arg_list)

        self.srcNode = BaseNode(MIO.get_mobj(src))
        self.destNode = BaseNode(MIO.get_mobj(dst))

        result_conns = self.eval_connections()
        result_attrs = self.eval_attributes()

        if not result_conns or not result_attrs:
            self.undo = False
            raise RuntimeError()

        connections = self.parse_connections()
        self.parse_disconnections(connections)
        for src, dest in connections:
            self.modi.connect(src, dest)

        self.redoIt()

    def redoIt(self):
        """
        Connect all new connections and set all needed plugs.
        """
        self.modi.doIt()

        if self.plugs:
            for plug, value in self.plugs[1]:
                MIO.set_plugValue(plug, value)

    def undoIt(self):
        """
        Return every connection and changed plug to there pre-command state.
        """
        self.modi.undoIt()

        if self.plugs:
            for plug, value in self.plugs[0]:
                MIO.set_plugValue(plug, value)

    def isUndoable(self):
        return self.undo

    def eval_connections(self):
        """
        Goes over the incoming/ outgoing attributes on the srcNode and
        retrieves the corrosponding plugs on the destNode.

        Returns:
            [Bool]: True if everything succeeded, else False.
        """
        try:
            for srcPlugs, destPlug in self.srcNode.incomingConnections:
                newDestPlug = self.destNode.get_corrospondingAttr(
                    self.srcNode, destPlug)

                if not newDestPlug.isNull:
                    self.connected_attrs.append(
                        destPlug.partialName(useLongNames=True))

                    for plug in srcPlugs:
                        self.old_src_dest_items.append(
                            (plug.partialName(includeNodeName=True, useLongNames=True), destPlug.partialName(includeNodeName=True, useLongNames=True)))
                        self.new_src_dest_items.append(
                            (plug.partialName(includeNodeName=True, useLongNames=True), newDestPlug.partialName(includeNodeName=True, useLongNames=True)))

            for srcPlug, destPlugs in self.srcNode.outgoingConnections:
                newSrcPlug = self.destNode.get_corrospondingAttr(
                    self.srcNode, srcPlug)

                if not newSrcPlug.isNull:
                    self.connected_attrs.append(
                        srcPlug.partialName(useLongNames=True))

                    for plug in destPlugs:
                        self.old_src_dest_items.append(
                            (srcPlug.partialName(includeNodeName=True, useLongNames=True), plug.partialName(includeNodeName=True, useLongNames=True)))
                        self.new_src_dest_items.append(
                            (newSrcPlug.partialName(includeNodeName=True, useLongNames=True), plug.partialName(includeNodeName=True, useLongNames=True)))

        except Exception as e:
            _, _, tb = sys.exc_info()
            val = traceback.extract_tb(tb, 1)[0]

            self.runtimeErr(error=e, tb=val)
            return False
        else:
            return True

    def eval_attributes(self):
        """
        Goes over the Attributes given by the mapping and
        retrieves all newPlugs and there new Values and
        the oldPlugs and there Values (for undo).

        Returns:
            [Bool]: True if everything succeeded, else False.
        """
        newPlugs_oldVal_items = ct.LinkedList()
        newPlugs_newVal_items = ct.LinkedList()

        try:
            mapping = self.srcNode.get_map()
            for attr in mapping.keys():
                # -check if attr is connected,
                #   - if yes - skip attribute and component attributes
                #   - if component attribute is connected - skip main attribute
                #     and the connected component
                if any(attr in c for c in self.connected_attrs) or any(
                        c in attr for c in self.connected_attrs):
                    continue

                oldAttr = self.srcNode.get_plugFrStr(attr)
                newAttr = self.destNode.get_plugFrStr(mapping[attr])
                attrVal = MIO.get_plugValue(oldAttr)
                oldAttrVal = MIO.get_plugValue(newAttr)

                newPlugs_oldVal_items.append((newAttr, oldAttrVal))
                newPlugs_newVal_items.append((newAttr, attrVal))

            self.plugs = (newPlugs_oldVal_items, newPlugs_newVal_items)
        except Exception as e:
            _, _, tb = sys.exc_info()
            val = traceback.extract_tb(tb, 1)[0]

            self.runtimeErr(error=e, tb=val)
            return False
        else:
            return True

    def parse_connections(self):
        """
        Extract the actual MObjects and MPlugs from the strings given to the command.

        Args:
            arg_list ([MArgList]): Maya Object containing all the data given to the command.

        Raises:
            RuntimeError: If any given Node or attribute Name is wrong.

        Returns:
            [List]: Containing Tuples of Source, Destination MPlugs.
        """
        connections = self.new_src_dest_items

        # -loop over the connections and split every name by . character
        # -store it as a tuple comprised of 2 Lists with the node and attribute names
        #   of the sources and destinations
        srcDest_NodeConns_str = [(src.split(".", 1), dest.split(".", 1))
                                 for src, dest in connections]

        # -I append to the List with a for-loop instead of a List Comprehension
        #   because of readability
        srcDest_plugs = ct.LinkedList()

        for src, dest in srcDest_NodeConns_str:
            try:
                # -get the MObjects of the source and destination Nodes
                # -get the MPlugs of the source and destination attributes
                # -if any of the needed objects don't exist,
                #   the functions will raise a RunTime Error
                srcMobj = MIO.get_mobj(src[0])
                srcPlug = MIO.get_plug(
                    srcMobj, api2.MFnDependencyNode(srcMobj), src[1])

                destMobj = MIO.get_mobj(dest[0])
                destPlug = MIO.get_plug(
                    destMobj, api2.MFnDependencyNode(destMobj), dest[1])

            except RuntimeError as re:
                # -override the Runtime Error to display the object that is throwing the Error
                #   and raise it afterwards

                # -check if the variable names are NOT in the local namespace,
                #   if False check which one is missing and store the corrosponding names
                if bool("srcMobj" and "srcPlug" not in locals()):
                    result = src[0] if "srcMobj" not in locals() else src[1]

                elif bool("destMobj" and "destPlug" not in locals()):
                    result = dest[0] if "destMobj" not in locals() else dest[1]

                # -split the Error message and swap the kInvalidParameter with the
                #   first object that throwed an Error
                err_arg = re.message.split(":")[1]
                endResult = "(%s) :%s" % (result, err_arg)
                re.message = endResult
                raise

            else:
                # -append the source and destination MPlgs if no Error occured
                srcDest_plugs.append((srcPlug, destPlug))

        return srcDest_plugs

    def parse_disconnections(self, connections):
        """
        Check every destination Plug if its changeable,
        yes- get every plug its connected to, as source, and disconnect it
        no- do nothing, is can be connected to
        """
        for _, dest in connections:
            if dest.isFreeToChange():  # -if True no changes can be made
                for plug in dest.connectedTo(True, False):
                    self.modi.disconnect(plug, dest)

    def parse_args(self, arg_list):
        """
        Extract the argument data and pass it as 2 Strings.

        Args:
            arg_list ([MArgList]): Maya Object containing all the data given to the command.

        Returns:
            [String]: Return 2 Strings, the Source and Destination Node.
        """
        try:
            arg_parse = api2.MArgDatabase(self.syntax(), arg_list)
        except RuntimeError as re:
            re.message = "Wrong arguments given to %s.\nSignature: %s(Str(srcNode), Str(dstNode))" % (
                self.COMMAND_NAME, self.COMMAND_NAME)

            self.runtimeErr(re)
            return None  # -raises unexpected Failure when raising the error

        srcNode_str = arg_parse.commandArgumentString(0)
        dstNode_str = arg_parse.commandArgumentString(1)

        return srcNode_str, dstNode_str

    def runtimeErr(self, error, raise_err=False, tb=None):
        """
        Helper method to react to a Runtime Error.
        It sets the undo to False and undoes every action the command made.
        If raise_err is True, it raises the error else it displays the error message.

        Args:
            error ([Exception]): A RuntimeError Exception object containing the Error message.
            raise_err ([Bool], optional) : If True, raise the error else display the error message.
                                           Defaults to False.
        """
        if tb:
            print "File '%s', line %s, in %s" % (tb[0], tb[1], tb[2])

        self.undo = False
        self.undoIt()

        if raise_err:
            raise error

        api2.MGlobal.displayError(error.message)

    @classmethod
    def create_syntax(cls):
        """
        Command syntax creator Function.

        Returns:
            [MSyntax]: Syntax object containing the definition of the commands syntax.
        """
        syntax = api2.MSyntax()

        syntax.addArg(api2.MSyntax.kString)
        syntax.addArg(api2.MSyntax.kString)

        return syntax

    @classmethod
    def create_cmd(cls):
        """
        Command creator Funtion.

        Returns:
            [NodeConvertCmd]: Instance of the command.
        """
        return NodeConvertCmd()

    @classmethod
    def create_register(cls):
        """
        Helper method to get a register-ready List containing all needed data.

        Returns:
            [List]: Containing the Cmd-Name, creator- and syntax creator function.
        """
        return [cls.COMMAND_NAME, cls.create_cmd, cls.create_syntax]
