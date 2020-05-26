# shaderHelper-maya
Shader Helper - Maya Python Plug-In (API2)


Simple GUI for converting legacy maya shaders to, for the time being, aiStandardSurface shaders.
Comes with convenient functionality for selecting and editing nodes and shaders.
<br/>
<br/>
ABOUT:<br/>
  This app was designed as answer to the mShadersToArnold.py script, which I found uncomfortable working with in big scenes.
  It implements a custom command to convert shaders with a predefined mAttribute-->aiAttribute map and
  reconnects every connection from the mShader to the aiShader.

  It also implements several convenient functions to select and edit nodes like changing the colorspace or rename file nodes.

  The app can also easily be extended by adding functions to the switch-case dictionaries like:

```
from shaderHelper_main import _selection_funcs

_selection_funcs[n'th_index] = desired_function
```
<br/>
INSTALLATION:

(only tested in OSX 10.14.6, Maya2020, python2.7.16)
  
  - open the terminal, CMD on win
  
  - enter python and the path to install.py
  
    -default: `python install.py`
  
  
    -optional, `python install.py path/to/the/desired/mayaPref`   eg:`/Users/user/Library/Preferences/Autodesk/maya/2020`
    
    
    -optional, `python install.py -s shelf_name`   
    enter the name of the shelf where the GUI button should be placed
  
  or
  - copy shaderHelper (folder) and shaderHelper.py to your maya preferences/plug-ins folder
  
    e.g.: /user/'username'/Library/Preferences/Autodesk/maya/2020/plug-ins
  
  - add the shaderHelper path to PYTHONPATH
  
    e.g.: PYTHONPATH = /Users/'username'/Library/Preferences/Autodesk/maya/2020/plug-ins/shaderHelper
    
       or PYTHONPATH = /already/existing/paths;/your/path/to/shaderHelper\n

   
<br/>
USAGE:

  - simply load the plugin after installation
  
  - open the gui from the Custom or user supplied shelf
  
  - select legal legacy shaders
  
  - execute convert-selection or convert-all to get the desired shaders
  
  
 <br/>
KNOWN-ISSUES:

  - if the Ui is open when maya is closed and the plug-in isn't set to auto-load it won't start correctly
  
  - there aren't any help menus integrated yet
  
 
