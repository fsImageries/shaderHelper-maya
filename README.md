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
<br/>
INSTALLATION:<br/>
Only tested in OSX 10.14.6, Maya2020, python2.7.16 & 3.8.3.<br/>
You have to use sudo here because mayas site-packages is in a secured folder and
you also have to locate your mayapy executable, help at: https://knowledge.autodesk.com/support/maya/learn-explore/caas/CloudHelp/cloudhelp/2016/ENU/Maya/files/GUID-83799297-C629-48A8-BCE4-061D3F275215-htm.html.<br/>


<br/>First approach (mayapy pip):
  
  - open the terminal, CMD on win
  
  - install from git:<br/>
    -`sudo path/to/mayapy -m pip install git+https://github.com/fsImageries/shaderHelper-maya.git`

  Second approach (from source):<br/>
  
  - download the git repo<br/>
    `cd into/repo`<br/>
    `sudo path/to/mayapy -m pip install path/to/repo`<br/>
    or<br/>
    `sudo path/to/mayapy setup.py install`<br/>
  
  Third approach (copy files):<br/>
  
  - download the git repo
  
  - copy the shaderHelper_plugin package from src to a folder on your PYTHONPATH, preferably mayas site-packages
  
  - copy the shaderHelper.py from root to your maya preference/plug-in folder (create it if not existing)
<br/>  
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
  
 
