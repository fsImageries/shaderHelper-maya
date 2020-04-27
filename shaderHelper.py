import maya.api.OpenMaya as api2
from maya import cmds, mel
from shaderHelper.customCmds import NodeConvertCmd


SHELF_NAME = "Custom"
SHELF_TOOL = {
    "label": "ShaderHelper",
    "command": "from shaderHelper_main import ShaderHelper_app\nShaderHelper_app.display()",
    "annotation": "Convert legacy shaders to aiStandardSurfaces.",
    "image1": "pythonFamily.png",
    "sourceType": "python",
    "imageOverlayLabel": "ShHelper"
}


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
        _set_shelfBTN()
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
        _remove_shelfBTN()
    except Exception as e:
        print e


def _set_shelfBTN():
    # get top shelf
    gShelfTopLevel = mel.eval("$tmpVar=$gShelfTopLevel")
    # get top shelf names
    shelves = cmds.tabLayout(gShelfTopLevel, query=1, ca=1)
    # create shelf
    if SHELF_NAME not in shelves:
        cmds.shelfLayout(SHELF_NAME, parent=gShelfTopLevel)
    # delete existing button
    _remove_shelfBTN()
    # add button
    cmds.shelfButton(style="iconOnly", parent=SHELF_NAME, **SHELF_TOOL)


def _remove_shelfBTN():
    # get existing members
    names = cmds.shelfLayout(SHELF_NAME, query=True, childArray=True) or []
    labels = [cmds.shelfButton(n, query=True, label=True) for n in names]

    # delete existing button
    if SHELF_TOOL.get("label") in labels:
        index = labels.index(SHELF_TOOL.get("label"))
        cmds.deleteUI(names[index])
