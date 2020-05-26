from string import digits
from os.path import split, splitext
from time import time
from contextlib import contextmanager

import ctypes

try:
    from os import scandir
except ImportError:
    try:
        from scandir import scandir
    except ImportError:
        scandir = None


# -------------------------- Custom Classes --------------------------- #
# --------------------------------------------------------------------- #

class Array(object):
    """
    Simple Array class, implimenting the ctypes.py_object.
    Used for lists where the given number of items aren't changing.

    Args:
        size ([int, iterable]): Can either be a number from which the size of the array will be determined
                                or a iterable from which the array will be build.
    """

    def __init__(self, size):
        # TODO implement Generator
        iterObj = None
        try:
            iter(size)
        except TypeError:
            if size < 1 or not isinstance(size, int):
                raise ValueError("Size must be an int and bigger than 0.")
        else:
            iterObj = size
            size = len(iterObj)

        self._size = size
        # -create the array structure using the ctypes module
        objArray = ctypes.py_object * size
        self._elements = objArray()

        # -initialize each element
        if iterObj:
            self._fromIter(iterObj)
        else:
            self.clear()

    def __len__(self):
        """
        Return the size of the array.

        Returns:
            [Int]: Size of the array.
        """
        return self._size

    def __getitem__(self, index):
        """
        Return the item at a given index in the array.

        Args:
            index ([Int]): Index.

        Raises:
            ValueError: If index is smaller/equals 0 or bigger than the array size.

        Returns:
            [type]: Object held at the given index.
        """

        res = self._index_check(index)
        if res:
            raise IndexError(res)

        return self._elements[index]

    def __setitem__(self, index, value):
        """
        Set the item at a given index in the array.

        Args:
            index ([Int]): Index.
            value ([type]): Object that should be assigned.

        Raises:
            ValueError: If index is smaller/equals 0 or bigger than the array size.
        """
        res = self._index_check(index)
        if res:
            raise IndexError(res)

        self._elements[index] = value

    def __iter__(self):
        """
        Returns a generator object which can be iterated over.

        Returns:
            [Generator]: Holds the objects of the array.
        """
        return self._arrayGenerator()

    def __str__(self):
        msg = "[{0}]".format(
            ", ".join([str(self._elements[i]) for i in range(len(self))]))
        return msg

    def clear(self, value=None):
        for i in range(len(self)):
            self._elements[i] = value

    # ----------------------------------Helpers---------------------------------- #

    def _arrayGenerator(self):
        """
        Replaces the need for a Iterator-Class.
        Returns a generator Object which hold the currently indexed item.

        Yields:
            [type]: The Object at a given index.
        """
        curIdx = 0
        while curIdx < len(self._elements):
            yield self._elements[curIdx]
            curIdx += 1

    def _index_check(self, index):
        """
        Check if the given index or slice is valid.

        Args:
            index ([int, slice]): Given indecies.

        Returns:
            [string, None]: Returns a error message if index is invalid else None.
        """
        if isinstance(index, slice):
            if (abs(index.start) or abs(index.stop)) > len(self)-1:
                msg = "Slice indices out of range.\n{0} : {1}".format(
                    index.start, index.stop)
            else:
                return None
        elif abs(index) > len(self)-1:
            msg = "Index out of range."
        else:
            return None

        return msg

    def _fromIter(self, iterable):
        """
        Initialize array with elements from a given iterable.

        Args:
            iterable ([type]): An object that can be traversed.
        """
        for i, obj in enumerate(iterable):
            self._elements[i] = obj


# --------------------- Python Helper Functions ----------------------- #
# --------------------------------------------------------------------- #


def basenamePlus(filepath):
    """ Get every property of a filename as item """

    # Split of standard properties.
    basedir, filename = split(filepath)
    name_noext, ext = splitext(filename)

    # Split of Digits at the end of string. Useful for a name of a sequence i.e. Image Sequence.
    digitsChars = digits.encode()
    name_nodigits = name_noext.rstrip(digitsChars) if name_noext.rstrip(
        digitsChars) != name_noext else None

    return name_noext, name_nodigits, basedir, ext


def getImgSeq(filepath):
    """ Get list with all images of a chosen picture """

    # Get Filename with and without padding, Directory of the file and extension.
    _, filename_nodigits, basedir, ext = basenamePlus(filepath)

    # Check if Input is part of a
    if filename_nodigits is None:
        return []

    # Scan the directory for every file that has the same Name and Extension and check if it has padding.
    # If so add to frames.
    frames = [
        f.path for f in scandir(basedir) if
        f.is_file() and
        f.name.startswith(filename_nodigits) and
        f.name.endswith(ext) and
        f.name[len(filename_nodigits):-len(ext) if ext else -1].isdigit()]

    # Check if frames has more than one Image, if so return sorted frames.
    if len(frames) > 1:
        return sorted(frames)

    return []


def getPadedNames(name, padding, sequenceLen):

    if padding == 0:
        padVal = len(str(sequenceLen))
    else:
        padVal = padding

    padding = ["%s%s" % ("0" * (padVal - len(str(num))), num)
               for num in range(0, sequenceLen)]

    final = ["%s_%s" % (name, pad) for pad in padding]

    return final


def flatten(src_list):
    """
    Basic List flattening, supports Lists, Tuples and Dictionaries.

    It checks for iter attribute and goes recursively over every item. It stores matches into a new List.
    When Dictionary it gets the items and calls itself to flatten them like a normal List.
    When no type is valid return the Item in a new List.

    Args:
        src_list ([Iterable]): The Source List which should be flattened.

    Returns:
        [List]: Returns the flattened List.
    """
    if hasattr(src_list, "__iter__"):

        if isinstance(src_list, dict):
            return flatten(src_list.items())

        flat_sum = flatten(
            src_list[0]) + (flatten(src_list[1:]) if len(src_list) > 1 else[])
        return flat_sum

    return [src_list]


# ------------------------ Context Managers --------------------------- #
# --------------------------------------------------------------------- #

class FunctionTimer(object):
    def __enter__(self):
        self.start_time = time()

    def __exit__(self, *_):
        print "My program took", time() - self.start_time, "to run"


@contextmanager
def block_signals(QObj):
    """
    Convenient Context manager for blocking Qt Signals.
    Every widget change within the try-statement doens't emit it's change-Signal.

    Args:
        QObj ([QtCore.QObject]): The Object/Widget which signals should be blocked.
    """
    try:
        QObj.blockSignals(True)
        yield
    finally:
        QObj.blockSignals(False)
