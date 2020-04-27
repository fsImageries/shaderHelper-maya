import maya.api.OpenMaya as api2
from customCmds import NodeConvertCmd


def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass


def initializePlugin(plugin):
    """
    Entry point for a plugin. It is called once -- immediately after the plugin is loaded.
    This function registers all of the commands, nodes, contexts, etc... associated with the plugin.

    Args:
        plugin ([MObject]): MObject representing the Plugin, given by Maya.
    """
    vendor = "FzudemAA"
    version = "1.0.0"

    pluginMfn = api2.MFnPlugin(plugin, vendor, version)

    try:
        pluginMfn.registerCommand(*NodeConvertCmd.create_register())
    except Exception as e:
        print e


def uninitializePlugin(plugin):
    """
    Exit point for a plugin. It is called once -- when the plugin is unloaded.
    This function de-registers everything that was registered in the initializePlugin function.

    It is required by all plugins.

    Args:
        plugin ([MObject]): MObject representing the Plugin, given by Maya.
    """
    pluginMfn = api2.MFnPlugin(plugin)

    try:
        pluginMfn.deregisterCommand(NodeConvertCmd.COMMAND_NAME)
    except Exception as e:
        print e
