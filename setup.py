import platform
import shutil
import codecs
import sys
import os
import re

from setuptools import find_packages, setup


# Most of this setup is shamelessly copied from https://github.com/robertjoosten mayapip setup.py.
# Thanks nonetheless :*
#----------------------------------------------------------------------#

def read(*parts):
    with codecs.open(os.path.join(here, *parts), 'r') as fp:
        return fp.read()


def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(
        r"^__version__ = ['\"]([^'\"]*)['\"]",
        version_file,
        re.M,
    )
    if version_match:
        return version_match.group(1)

    raise RuntimeError("Unable to find version string.")


package = "shaderHelper_plugin"
here = os.path.abspath(os.path.dirname(__file__))
long_description = read("README.md")
requires = ["mayapyUtils"]
required_links = ["enter_public_url"]

attrs = {"name": package,
         "version": find_version("src", package, "__init__.py"),
         "author": "Farooq Singh",
         "author_email": "imageries@mail.de",
         "package_dir": {"": "src"},
         "packages": find_packages(where="src"),
         "install_requires": requires,
         "dependency_links": required_links,
         "license": "MIT",
         "description": "Maya-Python helper library.",
         "long_description": long_description,
         "keywords": "maya python mayapy utilities"}

#----------------------------------------------------------------------#

OS_NAME = platform.system()
INPUT = raw_input if sys.version[0] == "2" else input
PLUGIN = "shaderHelper.py"
END_CARD = """Successfully installed shaderHelper.\nIf any problems occurred please let me know at github."""


def get_mayaVer():
    """
    Search for the appropriate maya version by consulting the interpreter.

    Returns:
        [String, None]: Maya Version when found, None if not.
    """
    pattern = re.search(r"maya\d+\.?(?:\d{1,2})?",
                        sys.executable)

    if not pattern:
        return None

    idx1, idx2 = pattern.span()
    match = pattern.string[idx1:idx2]
    return match.replace("maya", "")


def get_mayaPref(mayaPref_path=None, mayaVer=None):
    """
    Get Mayas preference folder either by supplying it through the command line
    or by trying to build it depending on the OS.

    Raises:
        OSError: If no maya Version dir can be found in the Preferences dir.
        OSError: If an unsupported system tries to load the script.
    """
    if mayaPref_path is None or not os.path.isdir(mayaPref_path):
        if mayaPref_path:
            print("The given path is not valid:\n====>{0}".format(
                mayaPref_path))

        if OS_NAME == "Darwin":   # -check if macOSX is running
            user = os.path.expanduser("~")
            maya = "Library/Preferences/Autodesk/maya"

            mayaPref = os.path.join(user, maya)

            if os.path.isdir(mayaPref):
                if not mayaVer:
                    lsDir = os.listdir(mayaPref)
                    gen = (l for l in lsDir if l.isdigit())
                    mayaVer = sorted(gen, reverse=True)

                    if not mayaVer:
                        raise OSError(
                            "No Valid Maya Version found.\n====>{0}".format(mayaPref))
                    mayaVer = mayaVer[0]

                mayaPref_path = os.path.join(mayaPref, mayaVer)

            else:
                raise OSError("Can't locate maya preference folder.")

    return mayaPref_path


def get_joined(base, end):
    """
    Get the path where the application should be installed.

    Args:
        mayaPref ([String]): Maya Preferences path.
        package_path ([String]): Path where the package should live in.

    Returns:
        [String]: Absolute path to for the package.
    """
    return os.path.join(base, end)


def setup_plugin(basepath, plugin_path, package):
    """
    Copy the needed files from the application folder to the system folder.

    Args:
        basepath ([String]): Path to the source/application files.
        plugin_path ([String]): Path to the destination, where the folder should be copied to.
        package ([String]): Folder or file which should be copied.

    Returns:
        [Bool]: Succes state or None if nothing got copied by user wish.
    """
    # -if the folder or file already exists ask the user how to deal with the problem
    src_path = get_joined(basepath, package)
    dst_path = get_joined(plugin_path, package)
    package_type = "folder" if os.path.isdir(dst_path) else "file"
    remove = shutil.rmtree if package_type == "folder" else os.remove
    copy = shutil.copytree if package_type == "folder" else shutil.copyfile

    if os.path.exists(dst_path):
        print("\n'{0}'- already exists.".format(dst_path))

        remove(dst_path)
    try:
        copy(src_path, dst_path)
    except Exception as e:
        remove(dst_path)
        print(e.message)
        return False
    else:
        return True


def main():
    try:
        setup(**attrs)
    except Exception:
        print("Couldn't install shaderHelper_plugin package.")
        raise
    else:
        # -copy shaderHelper.py to plugin_path
        basepath = os.getcwd() if "/" not in __file__ else os.path.dirname(__file__)
        mayaVer = get_mayaVer()
        mayaPref = get_mayaPref(mayaVer=mayaVer)

        if not mayaPref:
            raise OSError("Can't locate maya preference folder.")

        plugin_path = get_joined(mayaPref, "plug-ins")
        plugin = setup_plugin(basepath, plugin_path, PLUGIN)

        if not plugin:
            raise OSError("Can't copy {0}.\nPlease copy from {1} to {2}.".format(
                PLUGIN, basepath, plugin_path))

        print(END_CARD)


if __name__ == "__main__":
    main()
