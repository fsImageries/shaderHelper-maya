############# MAYA IMPORTS #############
from maya.api import OpenMaya as api2
from maya import cmds
from PySide2 import QtCore, QtWidgets

############ CUSTOM IMPORTS ############
from scripts.basicMayaIO import MIO_BasicIO as MIO
from scripts import baseClasses
from scripts import static_lib

############# Ui IMPORTS ###############
from ui.shaderHelper_ui import Ui_ShaderHelper
import scripts.mahelper as mahelper
import scripts.pyhelper as pyhelper

####### Standard Library IMPORTS #######
from functools import partial


class ShaderHelper(object):

    def __init__(self):
        self.convTo = None
        self.verbose = False

    # ----------------------------------Selection---------------------------------- #

    def get_nonACESTextureNodes(self):
        """
        Go over entire scene and look for fileTexture nodes.
        Get the colorspace and check if it doesn't contain the check-word.
        If yes, return it.

        Checks for "ACES" if OCIO-Config isn't enabled and "Utility" if it is.

        Returns:
            [MSelectionList]: All found nodes or empty if none can be found.
        """
        config = cmds.colorManagementPrefs(q=True, cmConfigFileEnabled=True)
        check = "Utility" if config else "ACES"
        nodes = MIO.get_selectionIter()

        sel = api2.MSelectionList()

        for n in nodes:
            node = baseClasses.BaseNode(n.getDependNode())

            if self._fileTexture_check(mobj=node.mobject):
                space = MIO.get_colorSpace(node.mobject, node.nodeMfn)

                if check not in space:
                    sel.add(node.mobject)

        return sel

    # ----------------------------------Conversion---------------------------------- #

    def convert_all(self, force=False):
        """
        Convert all legal shaders by creating new shaders for every convertable.

        Args:
            force (bool, optional): [description]. Defaults to False.
        """
        partialCheck = partial(self._legalType_check, isDefault=True)
        names = MIO.get_names(check=partialCheck)

        if not names:
            api2.MGlobal.displayError("No supported shaders selected.")
            return

        src_dest = self._create_new(names)
        self.convert_shaders(src_dest, force=force)

    def convert_selection(self, force=False, new=True):
        """
        Convert the current selection, 
        either by creating new shaders for every convertable shader or 
        by suppling shaders in the selection to which they should be converted.

        Args:
            force (bool, optional): Determine if source nodes should be deleted. Defaults to False.
            new (bool, optional): Determine if new shaders should be created. Defaults to True.

        """
        names = MIO.get_names(
            api2.MGlobal.getActiveSelectionList(), self._legalType_check)

        if not names:
            api2.MGlobal.displayError("No supported shaders selected.")
            return

        if new:
            src_dest = self._create_new(names)
        else:
            # -check that there are at least n*2 items in the list
            if len(names) % 2 != 0:
                api2.MGlobal.displayError(
                    "Not enough Nodes given to convert properly.")
                return

            # -retrieve source, dest items by looping over the names and
            #   grouping n'th item plus the next item. Skip the next iteration.
            src_dest = tuple(((n, names[i+1])
                              for i, n in enumerate(names) if not i % 2))

        self.convert_shaders(src_dest, force=force)

    def convert_shaders(self, src_dest, force=False):
        """
        Convert the given shaders with the custom nodeConvert command.

        #INFO#
        Only impliments conversion to arnold surface shader for the time being.
        #INFO#

        Args:
            src_dest ([iterable]): List containing the source and destination shaders as strings.
                                   Sources are shaders which should be converted, 
                                   destinations are shaders to which it should be converted.
            force (bool, optional): Determines if source shaders should be deleted. Defaults to False.
        """
        try:
            for src, dest in src_dest:
                cmds.nodeConvert(src, dest)
        except Exception as e:
            # -split on first message and display
            if "\n" in e.message:
                e.message = e.args[0].split("\n")[0]

            api2.MGlobal.displayError(e.message)
        else:
            if force:
                # - if True get all source nodes and delete them
                force = [src for src,
                         _ in src_dest if src not in static_lib.NON_DELETEABLES]
                if force:  # -only execute when force has items
                    cmds.delete(*force)

            if self.verbose:
                # -get the length of the longest name
                width = len(max([s for s, _ in src_dest], key=len))

                # -format every source name to the given width
                statements = ["Successfully converted: {0:<{width}} --> {1:<10}\n".format(s, d, width=width)
                              for s, d in src_dest]
                statement = "".join(statements)

                print "\n{0}".format(statement)

            sel = (dest for _, dest in src_dest)
            MIO.multiSelect(sel)

    # ----------------------------------Editing---------------------------------- #

    def renameFileNodesToFileNames(self, selection=None):
        """
        Rename FileTextureNodes to there corresponding FileTextureNames.
        eg. Node-file1: ImageName-someTexture_NRM --> 
            Node-someTexture_NRM: ImageName-someTexture_NRM

        Args:
            selection ([MSelectionList], optional): An api2.MSelectionList which doesn't need to hold anything. 
                                                    Defaults to None and searches for all Nodes.
        """
        # -get a MItSelectionList to iterate over the nodes
        selection = MIO.get_selectionIter(selection)

        for s in selection:
            mobj = s.getDependNode()

            # -if the selected node isn't a fileTexture
            #   continue to the next iteration of the loop
            if mobj.apiType() != 497:
                continue

            # TODO make BaseNode use String; get_names and do the rest with BaseNode
            node = baseClasses.BaseNode(mobj)
            oldname = node.name
            newname = MIO.get_fileTextureName(mobj, node.nodeMfn)

            cmds.rename(oldname, newname)

            if self.verbose:
                print "Renamed {} --> {}.".format(oldname, newname)

    def changeColorspace(self, colorspace, selection=None):
        """
        Change the colorspace of multiple nodes to the given colorspace.

        Args:
            colorspace ([String]): The colorspace to which it should be changed.
            selection ([MSelectionList], optional): An api2.MSelectionList which doesn't need to hold anything. 
                                                    Defaults to None and searches for all Nodes.
        """
        # -get a MItSelectionList to iterate over the nodes
        selection = MIO.get_selectionIter(selection)

        for s in selection:
            mobj = s.getDependNode()

            # -if the selected node isn't a fileTexture
            #   continue to the next iteration of the loop
            if mobj.apiType() != 497:
                continue

            node = baseClasses.BaseNode(mobj)
            csPlug = node.get_plugFrStr("colorSpace")
            oldColorspace = MIO.get_plugValue(csPlug)

            MIO.set_plugValue(csPlug, colorspace)

            if self.verbose:
                print "Changed {0}: {1} --> {2}".format(
                    csPlug, oldColorspace, colorspace)

    # ----------------------------------Helpers---------------------------------- #

    def _create_new(self, names):
        """
        Create a new shader for every given node and name them appropriately.

        Args:
            names ([iterable]): List containing shader names.

        Returns:
            [tuple]: List containing a list of source and destination names.
        """
        prefix = static_lib.CONVERT_TO[self.convTo]
        src_dest = tuple(((n, MIO.create_node(mahelper.prefix_name(n, prefix), shading=True, string=True))
                          for n in names))
        return src_dest

    @staticmethod
    def _legalType_check(**kwargs):
        """
        Check if node can be converted and if isDefault Node.
        Default nodes shouldn't be converted most of the time, 
        if you want to use the selection mode.

        Args:
            [MFnDependencyNode]: mfn=MFnDependencyNode, node which should be checked.

        Returns:
            [Bool]: Status if it can be converted.
        """
        mfn = kwargs["mfn"]
        if mfn.typeName in static_lib.LEGALTYPES:
            if kwargs.get("isDefault", None):
                return bool(mfn.name() not in static_lib.NON_DELETEABLES)
            return True
        return False

    @staticmethod
    def _fileTexture_check(**kwargs):
        """
        Check if node is a file texture node.

        Args:
            [MObject]: mobj=MObject, node which should be checked.

        Returns:
            [Bool]: Status if postive or not.
        """
        mobj = kwargs["mobj"]
        if mobj.apiType() == 497:
            return True

        return False


class ShaderHelper_app(QtWidgets.QMainWindow, Ui_ShaderHelper):

    UI_NAME = "ShaderHelper"
    WINDOW_TITLE = "Shader Helper"
    UI_INSTANCE = None

    PLUGIN = "shaderHelper"

    @classmethod
    def display(cls):
        """
        Is used when in production.
        Manages a ShaderHelper_app instance and restores it when hiden or closed.
        """
        if cls.UI_INSTANCE:
            cls.UI_INSTANCE.workspaceControl_instance.show_workspaceControl(
                cls.UI_INSTANCE)
        else:
            if not mahelper.is_plugin_loaded(cls.PLUGIN):
                mahelper.reload_plugin(cls.PLUGIN)
            cls.UI_INSTANCE = cls()

    @classmethod
    def get_uiScript(cls):
        """
        Get script with which the ShaderHelper_app is shown to restore it on start-up.

        Returns:
            [String]: Display method from ShaderHelper_app.
        """
        module_name = cls.__module__
        if module_name == "__main__":
            # -used in interactive session for testing
            module_name = cls.module_name_override

        uiScript = "from {0} import {1}\n{1}.display()".format(
            module_name, cls.__name__)
        return uiScript

    # ----------------------------------Setup---------------------------------- #

    def __init__(self):
        """
        Register a Color Managment Config Changed callback to refresh the colorspaces accordingly.

        Instantiate the ShaderHelper as logic variable.

        Setup the ShaderHelper Ui and call the WorkspaceControl after it to parent the full Ui.
        """
        super(ShaderHelper_app, self).__init__()
        self.cmConfigChanged_callback = MIO.registerCallback(
            self.cmConfigChanged, "colorMgtConfigChanged")

        self.logic = ShaderHelper()
        self.setupUi(self)
        self.setupControlls()
        self.setupConnections()

        mahelper.WorkspaceControl.create_workspaceControl(self)

    def __del__(self):
        MIO.deregisterCallback(self.cmConfigChanged_callback)

    def setupControlls(self, asSlot=False):
        # -controls which need to be updated if any function is called
        self.logic.convTo = self.convTo_comboBox.currentText()
        self.logic.verbose = self.activate_verbosity.isChecked()

        colorspace = self.changeColorSpace_radioBTN.isChecked()
        self.colorSpace_comboBox.setEnabled(colorspace)

        if asSlot:
            return

        self.selection_model = QtCore.QStringListModel([])
        self.selection_listView.setModel(self.selection_model)
        self.selection_listView.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection)

        # -initialize colorspace comboBox
        self.cmConfigChanged()

        self.edit_radioBTN_GRP = QtWidgets.QButtonGroup()
        for child in self.t3_editing.children():
            if isinstance(child, QtWidgets.QRadioButton):
                self.edit_radioBTN_GRP.addButton(child)

        # -subclass customLineEdit with new FocusChange event and
        #   replace every occurrence of the old one.
        self.search_lineEdit = baseClasses.CustomLineEdit(self.t1_selection)
        self.search_lineEdit.setObjectName("search_lineEdit")
        self.t1_gridLayout.addWidget(self.search_lineEdit, 2, 2, 1, 1)
        self.search_lineEdit.setToolTip(QtWidgets.QApplication.translate(
            "ShaderHelper", "Keywords seperated by comma.", None, -1))

    def setupConnections(self):
        # -----------TAB1 Selection------------ #
        self.searchBy_comboBox.currentIndexChanged.connect(
            lambda: self.search_slot(state=None))

        self.search_lineEdit.textChanged.connect(
            lambda: self.search_slot(state=None))
        self.search_lineEdit.returnPressed.connect(self.search_slot)
        self.search_lineEdit.focusChange.connect(self.search_slot)

        self.searchSelection_checkBox.stateChanged.connect(
            lambda: self.search_slot(state=None))

        self.searchAction_comboBox.currentIndexChanged.connect(
            lambda: self.search_slot(state=True))

        self.selection_listView.clicked.connect(self.select_slot)

        # -----------TAB2 Conversion----------- #
        self.convTo_comboBox.currentTextChanged.connect(
            lambda: self.setupControlls(asSlot=True))
        self.convertSelection_BTN.pressed.connect(
            lambda: self.convert_slot(False))
        self.convertAll_BTN.pressed.connect(lambda: self.convert_slot(True))

        # -----------TAB3 Editing-------------- #
        self.editSelection_BTN.pressed.connect(
            lambda: self.editing_slot(selection=True))
        self.editAll_BTN.pressed.connect(self.editing_slot)

        self.changeColorSpace_radioBTN.toggled.connect(
            lambda: self.setupControlls(asSlot=True))

        # -------------MENU Options------------ #
        self.activate_verbosity.triggered.connect(
            lambda: self.setupControlls(asSlot=True))

    # ----------------------------------Connection Slots---------------------------------- #

    def search_slot(self, state=None):
        """
        Manages the incoming search requests.
        Gets the names from the selected searching Method and displays them in the listView.
        SwitchSelection does the actual work and checks the ui for current inputs.

        Args:
            state ([Bool], optional): Determines if a action or keyword-search is used. Defaults to None.
        """
        selection = None

        if self.searchSelection_checkBox.isChecked():
            selection = MIO.get_selection()

        sel = self.switchSelection(selection, state)
        names = MIO.get_names(sel)

        self.selection_model.setStringList(names)

    def select_slot(self):
        """
        Manages the selected items in the listView and selects them in Maya.
        """
        selInds = self.selection_listView.selectedIndexes()

        sel = tuple((self.selection_model.data(i) for i in selInds))

        MIO.multiSelect(sel)

    def convert_slot(self, mode):
        """
        Manages the conversion of nodes.

        Args:
            mode ([Bool]): Determines which conversion mode is used. 
        """
        force = self.force_checkBox.isChecked()

        if mode:
            with mahelper.undo_chunk():
                self.logic.convert_all(force=force)
        else:
            new = self.convNew_radioBTN.isChecked()
            with mahelper.undo_chunk():
                self.logic.convert_selection(force=force, new=new)

    def editing_slot(self, selection=False):
        """
        Manages the editing of nodes.
        It gets the currently selected button and the corrosponding function from the 
        _editing_funcs dictionary and builds the kwargs for it.

        Args:
            selection (Bool, optional): Determines if the current selection should be used. Defaults to False.
        """
        button = self.edit_radioBTN_GRP.checkedButton()
        func = _editing_funcs[button.text().replace(" ", "")]

        kwargs = {}
        if selection:
            kwargs["selection"] = MIO.get_selection()
        if self.colorSpace_comboBox.isEnabled():
            kwargs["colorspace"] = self.colorSpace_comboBox.currentText()

        with mahelper.undo_chunk():
            func(self.logic, **kwargs)

    # ----------------------------------UI Logic---------------------------------- #

    def switchSelection(self, selection, state):
        """
        Swtich between keyword-search or search action.
        Where search action searches all nodes for a property and keyword-search for names and nodetypes.

        Args:
            selection ([MSelectionList, None]): Determines if the current selection is used or all nodes.
            state ([Bool]): True when searchAction is used, determines which widgets should be changed.

        Returns:
            [type]: [description]
        """
        # -when keyword-search calls set the searchAction comboBox empty
        # -if signal isn't blocked when function gets called again and comboBox
        #   isn't turned blank
        if not state and self.searchAction_comboBox.currentIndex() != -1:
            with pyhelper.block_signals(self.searchAction_comboBox):
                self.searchAction_comboBox.setCurrentIndex(-1)

        # -clear focus because focusChange is an event that calls this function to turn off the action comboBox
        if state:
            self.search_lineEdit.clearFocus()

            index = self.searchAction_comboBox.currentIndex()
            if index >= 0:
                # -get the corrosponding function if the index is valid
                sel = _selection_funcs[self.searchAction_comboBox.currentIndex()](
                    self.logic)
        else:
            mode = self.searchBy_comboBox.currentIndex()
            text = self.search_lineEdit.text()
            keywords = tuple((key.strip() for key in text.split(",")))

            sel = MIO.keywordSelection(
                keywords, mode=mode, selection=selection)

        return sel

    def cmConfigChanged(self, *_, **__):
        """
        Color Management Config Changed callback slot.
        Clear the colorspace comboBox and repopulate it.
        """
        self.colorSpace_comboBox.clear()

        for cs in static_lib.COLORSPACES():
            self.colorSpace_comboBox.addItem(cs)


# ShaderHelper_app Switch-Case dictionaries
# -private dictinaries, only used within the ShaderHelper_app class
# -used to determine which selection action should be called
_selection_funcs = {0: ShaderHelper.get_nonACESTextureNodes}

# -used to determine which editing function should be called
_editing_funcs = {"renameFileTextures": ShaderHelper.renameFileNodesToFileNames,
                  "changeColorspace": ShaderHelper.changeColorspace}
