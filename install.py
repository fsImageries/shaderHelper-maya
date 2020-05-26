import sys
import os
import platform
import shutil


# ------------------------- STATIC VARIABLES -------------------------- #
# --------------------------------------------------------------------- #

OS_NAME = platform.system()
VARIABLES = ["PYTHONPATH"]
INPUT = raw_input if sys.version[0] == "2" else input

EMPTY_SHELF = """global proc shelf_{0} () {{
    global string $gBuffStr;
    global string $gBuffStr0;
    global string $gBuffStr1;\n\n\n}}"""

SHELF_NAME = "Custom"


# ------------------------- Getter functions -------------------------- #
# --------------------------------------------------------------------- #


def get_mayaPref_path():
    """
    Get Mayas preference folder either by supplying it through the command line
    or by trying to build it depending on the OS.

    Raises:
        OSError: If Path given by the command line isn't valid.
        OSError: If no maya Version dir can be found in the Preferences dir.
    """
    if len(sys.argv) == 2:
        if os.path.isdir(sys.argv[1]):
            mayaPref_path = sys.argv[1]
        else:
            raise OSError(
                "The given path is not valid:\n====>{0}".format(sys.argv[1]))

    elif OS_NAME == "Darwin":   # -check if macOSX is running
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


def get_mayaEnv(mayaPref_path):
    """
    Get the path to Maya.env file if it exits, else create it.

    Args:
        mayaPref_path ([String]): Path to current maya preference folder.

    Returns:
        [String]: Path to Maya.env.
    """
    mayaEnv = os.path.join(mayaPref_path, "Maya.env")

    if not os.path.isfile(mayaEnv):
        with open(mayaEnv, "w+"):
            pass

    return mayaEnv


def get_shelf(mayaPref, shelfname):
    """
    Get the path to the shelf.mel file, create it if it doesn't exist, and return it.
    Shelf search is case-sensitive.
    """

    shelves = os.path.join(mayaPref, "prefs/shelves")

    shelfpath = os.path.join(shelves, "shelf_{0}.mel".format(shelfname))

    if not os.path.isfile(shelfpath):
        if _write_to_file(shelfpath, EMPTY_SHELF.format(shelfname)):
            print("Successfully created: 'shelf_{}.mel'".format(shelfname))

    return shelfpath


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


# ------------------------- Setter functions -------------------------- #
# --------------------------------------------------------------------- #


def set_mayaEnv(mayaEnv, package_path, variables):
    """
    Go over the Maya.env file and add or edit every supplied Enviroment Variable.

    Args:
        mayaEnv ([String]): Path to Maya.env
        package_path ([String]): Path that should be added to Maya.env.
        variables ([Iterable]): List which contains the Variable Names that should be edited.

    Returns:
        [Bool]: Success state.
    """
    # -use ':' if MacOSX or Linux, ';' if windows
    sep = ":" if OS_NAME in ["Darwin", "Linux"] else ";"

    # -get the content of maya.env
    env_file = _open_from_file(mayaEnv)

    # -get the lines in env_file which contain the Enviroment Variables and aren't comments
    path_lines = tuple((
        l for l in env_file for v in variables if v in l and not l.startswith("//")))

    # -if there are any of the searched Variables go over them and add the package path to the Variable
    # -replace the new edited line in the env_file with the old one
    # -if the path already exists skip the steps
    if path_lines:
        for line in path_lines:
            index = env_file.index(line)

            front, back = line.split("=")

            if package_path in back:
                continue

            line = "{0} = {1}{2}{3}\n".format(
                front.strip(), back.strip(), sep, package_path)

            env_file[index] = line

    # -get every Variable that isn't in path_lines (in maya.env) and create it
    create = set((v for v in variables if v not in "".join(path_lines)))

    # -add the pcakage path to the newly created Variables
    for c in create:
        line = "\n{0} = {1}\n".format(c, package_path)
        env_file.append(line)

    return _write_to_file(mayaEnv, env_file)


def set_files(basepath, plugin_path, package):
    """
    Copy the needed files from the application folder to the system folder.

    Args:
        basepath ([String]): Path to the source/application files.
        package_path ([String]): Path to the destination, where the folder should be copied to.

    Returns:
        [Bool]: Succes state or None if nothing got copied by user wish.
    """
    # -if a folder with the same name exists ask the user if he wants to leave it there or delete it
    package_path = get_joined(plugin_path, package)
    plugin_file = get_joined(basepath, "{0}.py".format(package))

    if os.path.exists(package_path):
        print("\n'{0}'- already exists.".format(package_path))

        # -simple loop that asks for Y/N, goes on indefinite if no corret answer is given
        # -if Y, delete the folder with all its contents
        while True:
            choice = str(INPUT("Delete folder: {0}? Y/N: ")).lower().strip()

            if choice == "y":
                shutil.rmtree(package_path)
                break
            elif choice == "n":
                return None

    # -copy the package and the plugin to the package path and plugin_path
    try:
        shutil.copytree(src=get_joined(basepath, package), dst=package_path)

        shutil.copyfile(src=plugin_file, dst=get_joined(
            plugin_path, "{0}.py".format(package)))
    except Exception as e:
        shutil.rmtree(package_path)
        print(e.message)
        return False
    else:
        return True


def set_shelf():
    """
    Add shelf name to shaderHelper.py plugin_name variable.
    """
    shelf = sys.argv[sys.argv.index("-s")+1]
    pluginPath = os.path.join(os.getcwd(), os.path.basename(
        "shaderHelper.py"))

    plugin = _open_from_file(pluginPath)

    plugin[3] = 'SHELF_NAME = "{0}"\r\n'.format(shelf)

    return _write_to_file(pluginPath, plugin)


# ------------------------- Helper functions -------------------------- #
# --------------------------------------------------------------------- #


def _open_from_file(path):
    """
    Open the whole file and return it.
    """
    with open(path) as path_file:
        out_file = path_file.readlines()

    return out_file


def _write_to_file(path, content):
    """
    Try to write the whole text to the source-file.
    """
    try:
        with open(path, "w+") as f:
            f.writelines(content)
    except Exception as e:
        print(e.message)
        return False
    else:
        return True


# ------------------------- Main -------------------------------------- #
# --------------------------------------------------------------------- #


def main(mayaEnv, plugin_path, basepath, package):
    try:
        env_res = set_mayaEnv(mayaEnv, get_joined(
            plugin_path, package), VARIABLES)

        files_res = set_files(basepath, plugin_path, package)

        if "-s" in sys.argv:
            set_shelf()

    except Exception as e:
        print("Something went wrong:")
        print(e.message)

        if "env_res" not in locals():
            env_res = False
        if "files_res" not in locals():
            files_res = False
    finally:
        print("\n")

        if env_res:
            width = len(max(VARIABLES))

            print("Successfully edited Maya.env.")
            for v in VARIABLES:
                print("\t==>{0:<<{width}}- was edited".format(v, width=width))
        else:
            print("Couldn't edit Maya.env.")

        print("\n")

        if files_res:
            print("Successfully copied ShaderHelper folder and plugin.")
            print("\t==>{0}\n\tcopied to -->\n\t==>{1}\n".format(
                basepath, get_joined(plugin_path, package)))
            print("\t==>{0}\n\tcopied to -->\n\t==>{1}\n".format(
                get_joined(basepath, "{0}.py".format(package)), get_joined(plugin_path, "{0}.py".format(package))))

        elif files_res is None:
            print("ShaderHelper already in place at:\n{0}".format(
                get_joined(plugin_path, package)))
        else:
            print("Couldn't install shaderHelper.")


# --------------------------__main__ block ---------------------------- #
# --------------------------------------------------------------------- #

if __name__ == "__main__":
    mayaPref = get_mayaPref_path()
    mayaEnv = get_mayaEnv(mayaPref)
    package = "shaderHelper"
    plugin_path = get_joined(mayaPref, "plug-ins")
    basepath = os.getcwd() if "/" not in __file__ else os.path.dirname(__file__)

    main(mayaEnv, plugin_path, basepath, package)
