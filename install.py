import sys
import os
import platform
import shutil


# TODO implement pre-check system to clean already existing files and folders
OS_NAME = platform.system()
INPUT = raw_input if sys.version[0] == "2" else input
PLUGIN = "shaderHelper.py"


def parse_args():
    """
    Get the command-line arguments if given, else assign None.

    Returns:
        [dict]: Keyword dictionary containing the values.
    """
    data = dict()

    if ("-v" or "--version") in sys.argv:
        try:
            v_flag_idx = sys.argv.index("-v")
        except ValueError:
            v_flag_idx = sys.argv.index("--version")

        data["m_ver"] = sys.argv[v_flag_idx+1]
    else:
        data["m_ver"] = None

    if ("-pr" or "--preference") in sys.argv:
        try:
            pr_flag_idx = sys.argv.index("-pr")
        except ValueError:
            pr_flag_idx = sys.argv.index("--preference")

        data["mayaPref_path"] = sys.argv[pr_flag_idx+1]
    else:
        data["mayaPref_path"] = None

    return data


def get_mayapy(m_ver):
    """
    Get the path to the mayapy executable.

    Args:
        m_ver ([int, None]): User supplied version or None.

    Raises:
        OSError: When the autodesk folder can't be located.
        OSError: When the maya version can't be located.

    Returns:
        [String]: Path to mayapy executable.
    """
    if OS_NAME == "Darwin":   # -check if macOSX is running
        base = "/Applications/Autodesk/"

        if not os.path.isdir(base):
            raise OSError("Can't locate Autodesk installation.")

        if not m_ver:
            lsDir = os.listdir(base)
            gen = (l for l in lsDir if "maya" in l)
            mayaVer = sorted(gen, reverse=True)
        else:
            mayaVer = ("maya{}".format(m_ver),)

        if not mayaVer:
            raise OSError(
                "No Valid Maya Version found.\n====>{0}".format(base))

        maya_base = os.path.join(base, mayaVer[0])

        return os.path.join(maya_base, "Maya.app/Contents/bin/mayapy")

    elif OS_NAME == "Windows":  # -check for windows
        return None

    return None


def get_mayaPref(mayaPref_path):
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
                lsDir = os.listdir(mayaPref)
                gen = (l for l in lsDir if l.isdigit())
                mayaVer = sorted(gen, reverse=True)

                if not mayaVer:
                    raise OSError(
                        "No Valid Maya Version found.\n====>{0}".format(mayaPref))

                mayaPref_path = os.path.join(mayaPref, mayaVer[0])

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


def setup_package(mayapy):
    """
    Install python packages through command-line use.

    Args:
        mayapy ([String]): Path to python interpreter.

    Returns:
        [Bool]: Success status.
    """
    try:
        os.system("sudo {} setup.py install".format(mayapy))
    except Exception as e:
        print("Something went wrong.\n{}".format(e))
    else:
        return True
    return False


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

        # -simple loop that asks for Y/N, goes on indefinite if no corret answer is given
        # -if Y, delete the folder with all its content
        while True:
            choice = str(
                INPUT("Delete {0}? Y/N: ".format(package_type))).lower().strip()

            if choice == "y":
                remove(dst_path)
                break
            elif choice == "n":
                return None

    # -copy the plugin to the plugin_path
    try:
        copy(src_path, dst_path)
    except Exception as e:
        remove(dst_path)
        print(e.message)
        return False
    else:
        return True


# ------------------------- Main -------------------------------------- #
# --------------------------------------------------------------------- #


def main():
    basepath = os.getcwd() if "/" not in __file__ else os.path.dirname(__file__)
    kwargs = parse_args()
    mayapy = get_mayapy(kwargs["m_ver"])

    if not mayapy:
        raise OSError("Can't locate mayapy.")

    package = setup_package(mayapy)

    if not package:
        raise OSError("Can't install python package.")

    mayaPref = get_mayaPref(kwargs["mayaPref_path"])

    if not mayaPref:
        raise OSError("Can't locate maya preference folder.")

    plugin_path = get_joined(mayaPref, "plug-ins")
    plugin = setup_plugin(basepath, plugin_path, PLUGIN)

    if not plugin:
        raise OSError("Can't copy {0}.\nPlease copy from {1} to {2}.".format(
            PLUGIN, basepath, plugin_path))

    print("""
Successfully installed shaderHelper.
If any problems occurred please let me know at github.""")


if __name__ == "__main__":
    main()
