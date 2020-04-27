import maya.OpenMayaUI as apiUI
import maya.cmds as cmds

from contextlib import contextmanager
from shiboken2 import wrapInstance, getCppPointer
from PySide2 import QtWidgets, QtCore


# --------------------- Workspace Control Setups ---------------------- #
# --------------------------------------------------------------------- #


class WorkspaceControl(object):

    def __init__(self, name):
        # -construct with a given workspace_control name
        self.name = name
        self.widget = None

    def create(self, label, widget, uiScript=None, plugin=None):
        """
        Create a workspace_control with the given name and label.

        Args:
            label ([String]): Displayed Text label on the workspace_control.
            widget ([QWidget]): The Ui or widget which should be parent to mayas layout.
            uiScript ([String], optional): Python-string which should generate the Ui. 
                                           Defaults to None.
        """
        print plugin, type(plugin)
        if not plugin:
            cmds.workspaceControl(self.name, label=label)
        else:
            cmds.workspaceControl(self.name, label=label,
                                  checksPlugins=True, requiredPlugin="shaderHelper.py")

        # -supply the control with a ui-creation script
        if uiScript:
            cmds.workspaceControl(self.name, e=True, uiScript=uiScript)

        self.add_widgetToLayout(widget)
        self.set_visible(True)

    def add_widgetToLayout(self, widget):
        """
        Retrieve the workspace_control and widget as pointers and add them
        to the main maya layout.

        Args:
            widget ([QWidget]): The Ui or widget which should be parent to mayas layout. 
        """
        if widget:
            self.widget = widget

            # maya.app.general.mayaMixin
            # If the input parent happens to be a Native window (such as the main Maya
            # window) then when we are parented to it, we also become a Native window.
            # Being a Native window is okay, but we don't want our ancestors to be
            # switched to Native, such as when we are docked inside a tabWidget.
            self.widget.setAttribute(QtCore.Qt.WA_DontCreateNativeAncestors)

            workspaceControl_ptr = long(apiUI.MQtUtil.findControl(self.name))
            widget_ptr = long(getCppPointer(self.widget)[0])

            apiUI.MQtUtil.addWidgetToMayaLayout(
                widget_ptr, workspaceControl_ptr)

    def restore(self, widget):
        """
        Restore the widget.

        Args:
            widget ([QWidget]): The Ui or Widget which should be restored.
        """
        self.add_widgetToLayout(widget)

    def exists(self):
        """
        Check if the given workspace_control exits.

        Returns:
            [Bool]: True if existing.
        """
        return cmds.workspaceControl(self.name, q=True, exists=True)

    def is_visible(self):
        """
        Check if the given workspace_control is visible.

        Returns:
            [Bool]: True if visible.
        """
        return cmds.workspaceControl(self.name, q=True, visible=True)

    def is_floating(self):
        """
        Check if the given workspace_control is floating.

        Returns:
            [Bool]: True if floating.
        """
        return cmds.workspaceControl(self.name, q=True, floating=True)

    def is_collapsed(self):
        """
        Check if the given workspace_control is collapsed.

        Returns:
            [Bool]: True if collapsed.
        """
        return cmds.workspaceControl(self.name, q=True, collapse=True)

    def set_visible(self, visible):
        """
        Sets the visibility of the workspace_control.

        Args:
            visible ([Bool]): Determines if the workspace_control should be invisible or restored.
        """
        if visible:
            cmds.workspaceControl(self.name, e=True, restore=True)
        else:
            cmds.workspaceControl(self.name, e=True, visible=False)

    def set_label(self, label):
        """
        Sets the label of the workspace_control.

        Args:
            label ([String]): The String which should be displayed on the workspace_control.
        """
        cmds.workspaceControl(self.name, e=True, label=label)

    # ----------------------------------UI Helper Methods---------------------------------- #
    # -only used with QT Ui classes
    # -assumes your Ui comes with some Class level name variables:
    #       - UI_NAME: ObjectName of the Ui.
    #       - WINDOW_TITLE: Title that should be displayed in the Ui window.

    @staticmethod
    def get_workspaceControl_name(uiCls):
        return "{0}_workspaceControl".format(uiCls.UI_NAME)

    @staticmethod
    def create_workspaceControl(UiSelf):
        UiSelf.workspaceControl_instance = WorkspaceControl(
            WorkspaceControl.get_workspaceControl_name(UiSelf))

        if UiSelf.workspaceControl_instance.exists():
            UiSelf.workspaceControl_instance.restore(UiSelf)
        else:
            UiSelf.workspaceControl_instance.create(
                UiSelf.WINDOW_TITLE, UiSelf, UiSelf.get_uiScript(), getattr(UiSelf, "PLUGIN", None))

    @staticmethod
    def show_workspaceControl(UiSelf):
        UiSelf.workspaceControl_instance.set_visible(True)


# ---------------------- Maya Helper Functions ------------------------ #
# --------------------------------------------------------------------- #


def getMayaWin():
    """
    Return the QMainWindow for the main Maya Window as QWidget.

    Raises:
        RuntimeError: When no maya window can be found.

    Returns:
        [QWidget]: Maya window as QWidget-object.
    """
    winptr = apiUI.MQtUtil.mainWindow()
    if winptr is None:
        raise RuntimeError("No Maya Window found.")

    window = wrapInstance(long(winptr), QtWidgets.QWidget)
    return window


@contextmanager
def undo_chunk():
    """
    Convenient Context Manager for handling Undo Chunks.
    It automatically opens and closes an UndoChunk when the code in the
    try-block is successfully run.
    """
    try:
        cmds.undoInfo(ock=True)
        yield
    finally:
        cmds.undoInfo(cck=True)


def prefix_name(name, prefix):
    """
    Prefix a name of a given node, checks if a namespace is contained and preserves it.

    Args:
        name ([String]): Name of the node.
        prefix ([String]): Prefix which should be added to the front.

    Returns:
        [String]: The new name with namespace if present.
    """
    if ":" in name:
        namespace, name = name.split(":")
        prefixName = "{0}{1}".format(prefix, name.title())
        newName = "{0}:{1}".format(namespace, prefixName)
    else:
        newName = "{0}{1}".format(prefix, name.title())

    return newName

# ------------------------------- PLUGIN SETUP ------------------------ #
# --------------------------------------------------------------------- #


def is_plugin_loaded(plugin_name):
    return cmds.pluginInfo(plugin_name, q=True, l=True)


def reload_plugin(plugin_name, unload=False):
    if not unload:
        cmds.evalDeferred("cmds.loadPlugin('{0}')".format(plugin_name))
    else:
        cmds.evalDeferred("cmds.unloadPlugin('{0}')".format(plugin_name))
