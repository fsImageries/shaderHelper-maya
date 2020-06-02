import ctypes


# ---------------------------- Sequences ------------------------------ #
# --------------------------------------------------------------------- #

class _BaseSequence(object):
    """
    Base class for holding commen sequence methods.
    Only meant for subclassing.
    """

    def _index_check(self, index):
        """
        Check if the given index or slice is valid.

        Args:
            index ([int, slice]): Given indecies.

        Returns:
            [string, None]: Returns a error message if index is invalid else None.
        """
        if isinstance(index, slice):
            if (abs(index.start) > len(self) - 1 or abs(index.stop)) > len(self)-1 or \
                    index.start > index.stop:
                msg = "Slice indices out of range.\n{0} : {1}".format(
                    index.start, index.stop)
            else:
                return None
        elif not isinstance(index, int):
            msg = "Indices must be integer."
        elif (index > 0 and index > len(self) - 1) or (index < 0 and abs(index) > len(self)):
            # -check if given index, when positive, is bigger then len(self) -1
            #   or, when negative, is bigger len(self)
            msg = "Index out of range."
        else:
            return None

        return msg

    def _negativeIndices(self, indices):
        """
        Checks for negative indices in a slice or int and returns the positive values.

        Args:
            indices ([slice, int]): Slice object containing the indices or int of a single index.

        Returns:
            [slice, int]: Slice with the new indices or positive int index.
        """
        try:
            st_idx = indices.start
            end_idx = indices.stop

            if indices.start < 0:
                st_idx = len(self) - abs(indices.start)

            if indices.stop < 0:
                end_idx = len(self) - abs(indices.stop)

            return slice(st_idx, end_idx)

        except AttributeError:
            if indices < 0:
                indices = len(self) - abs(indices)

            return indices


class Array(_BaseSequence):
    """
    Simple Array class, implimenting the ctypes.py_object.
    Used for lists where the given number of items aren't changing.

    Args:
        size ([int, iterable]): Can either be a number from which the size of the array will be determined
                                or a iterable from which the array will be build.
    """

    def __init__(self, size):
        if not isinstance(size, int):
            try:
                # -test if item is iterable else raise error
                iter(size)
                # -pass the iterable to _fromIter and initialize with from elements
                self._fromIter(size)
            except TypeError:
                raise ValueError("Must be an interger or iterable.")
        else:
            if size < 1:
                raise ValueError("Size must be bigger than 0.")

            # -set the size and build the array
            self._size = size
            self._buildArray()

            # -initialize each element
            self.clear()

    def __str__(self):
        msg = "[{0}]".format(
            ", ".join([str(self._elements[i]) for i in range(len(self))]))
        return msg

    # -----------------------------Sequence Dunders------------------------------ #

    def __len__(self):
        """
        Return the size of the array.

        Returns:
            [Int]: Size of the array.
        """
        return self._size

    def __iter__(self):
        """
        Returns a generator object which can be iterated over.

        Returns:
            [Generator]: Holds the objects of the array.
        """
        return self._arrayGenerator()

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

    # ----------------------------------Helpers---------------------------------- #

    def clear(self, value=None):
        """
        Clear each element of the array by looping over it 
        and assigning the given value.

        Args:
            value ([type], optional): Value or Object which should be assigned. Defaults to None.
        """
        for i in range(len(self)):
            self._elements[i] = value

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

    def _buildArray(self):
        """
        Build array from the given size attribute.
        Create the array structure using the ctypes module.

        """
        objArray = ctypes.py_object * self._size
        self._elements = objArray()

    def _fromIter(self, iterable):
        """
        Initialize array with elements from a given iterable.

        Args:
            iterable ([type]): An object that can be traversed.
        """
        try:
            # -check for len of the iterable
            self._size = len(iterable)
        except TypeError:
            # -if generator -> initialize LinkedList to get len
            iterable = LinkedList(iterable)
            self._size = len(iterable)

        # -build array
        self._buildArray()

        # -initialize each element
        for i, obj in enumerate(iterable):
            self._elements[i] = obj


class LinkedList(_BaseSequence):
    """
    Simple linked list for efficiently adding and removing items from a sequence.
    Can be constructed as an empty list or from an already existing iterable.
    Unsorted version.

    Args:
        source ([iterable, optional]): Source iterable from which the list should be constructed.
                                       Defaults to None.
        sorting([function, optional]): 
            Function by which the items are compared, 
            must return True if the item is a match and false if not.
            Defaults to None.

            E.g.: 'while sorting(curNode.data, addedData): ...
    """

    def __init__(self, source=None, sorting=None):
        self._head = None
        self._tail = None
        self._size = 0

        self.append = self._sortAppend if sorting else self._append
        self._search = self._sortedSearch if sorting else self._unsortedSearch
        self.sorting = sorting

        if source:
            self._fromIter(source)

    def __str__(self):
        res = "[{}]"
        items = None
        for item in self.__iter__():
            if not items:
                items = "{}".format(item)
            else:
                items = items + "-> {}".format(item)

        return res.format(items if items else "empty")

    # -----------------------------Sequence Dunders------------------------------ #

    def __len__(self):
        """
        Return the size of the list.

        Returns:
            [Int]: Size of the list.
        """
        return self._size

    def __iter__(self):
        """
        Returns a generator object which can be iterated over.

        Returns:
            [Generator]: Yields the objects of the list.
        """
        return self._listGenerator(self._head)

    def __contains__(self, target):
        """
        Returns True if target in list else False.

        Args:
            target ([type]): Object which should be checked.

        Returns:
            [bool]: True when item found.
        """
        return self._search(target)

    def __getitem__(self, index):
        """
        Return the item at a given index in the list.

        Args:
            index ([int, slice]): Index.

        Raises:
            ValueError: If index is smaller/equals 0 or bigger than the list size.

        Returns:
            [type]: Object held at the given index.
        """
        res = self._index_check(index)
        if res:
            raise IndexError(res)

        # -assign a counter and load the first object in the list
        i = 0
        curNode = self._head

        # -check for int or slice
        if isinstance(index, int):
            # -check for negative index, calculate the positive
            if index < 0:
                index = len(self) - abs(index)

            # -iterate over the nodes by comparing the indices
            while i != index:
                curNode = curNode.next
                i += 1
            # -save the stored data and return it
            result = curNode.data
        else:
            # -check negative indices, calculate the postive ones
            index = self._negativeSlices(index)

            # -create new list and return it
            result = LinkedList()

            # -iterate over the nodes by comparing the index to the end index
            while i <= index.stop:
                # -check if index is bigger/equals the start index
                if i >= index.start:
                    result.append(curNode.data)
                curNode = curNode.next
                i += 1

        return result

    def __setitem__(self, index, value):
        """
        Set the item at a given index in the list.

        Args:
            index ([int, slice]): Index.
            value ([type]): Object that should be assigned.

        Raises:
            ValueError: If index is smaller/equals 0 or bigger than the list size.
        """
        res = self._index_check(index)
        if res:
            raise IndexError(res)

        i = 0
        curNode = self._head

        if isinstance(index, int):
            if index < 0:
                index = (len(self)-1) - abs(index)
            while i != index:
                curNode = curNode.next
                i += 1
            curNode.data = value
        else:
            index = self._negativeSlices(index)

            if len(value) != (index.stop - index.start):
                raise ValueError("Not enough values given.")

            valIter = iter(value)
            while i <= index.stop:
                if i >= index.start:
                    curNode.data = next(valIter, None)
                curNode = curNode.next
                i += 1

    # -----------------------------------Methods--------------------------------- #

    def _append(self, item):
        """
        Unsorted append, faster version.
        Gets assigned when the list is constructed.

        Args:
            item ([type]): Object which should be added.
        """
        # -create a list node and assign the item
        newNode = _LinkedNode(item)

        # -check if head is empty, assign new node as head
        #   else assign new node as next on the current tail
        if self._head is None:
            self._head = newNode
        else:
            self._tail.next = newNode

        # -assign new node as tail
        self._tail = newNode
        self._size += 1

    def _sortAppend(self, item):
        """
        Sorted append, slower version through list traversel.
        Gets assigned when the list is constructed.

        Args:
            item ([type]): Object which should be added.
        """
        predNode = None
        curNode = self._head

        # -iterate through the nodes and stop when match is found or
        #   list has come to an end
        while curNode is not None and self.sorting(curNode.data, item):
            predNode = curNode
            curNode = curNode.next

        # -create new node with item assigned
        newNode = _LinkedNode(item)
        # -assign the current node as the next in the chain
        newNode.next = curNode
        self._size += 1

        # -if current node is head reassign with new node
        #   else assign it as the next node in the predecessor
        if curNode is self._head:
            self._head = newNode
        else:
            predNode.next = newNode

    def _unsortedSearch(self, target):
        """
        Compare items till list is exhausted or match found.
        """
        curNode = self._head

        # -iterate till curNode is None or given target is equal to curNodes data
        while curNode is not None and curNode.data != target:
            curNode = curNode.next
        return curNode is not None

    def _sortedSearch(self, target):
        """
        Compare items till list is exhausted or 
        sorting determines that no match is possible, terminate early on.
        """
        curNode = self._head

        # -iterate till curNode is None or sorting returns False
        while curNode is not None and self.sorting(curNode.data, target):
            if curNode.data == target:
                return True
            curNode = curNode.next
        return False

    def _removal(self, predNode, curNode):
        """
        Remove a current node by skipping it in the chain,
        release it from it's predecessor and replace it with current nodes next.

        Args:
            predNode ([LinkedNode]): Previous node.
            curNode ([LinkedNode]): Current node.

        Returns:
            [type]: Data of the removed node.
        """
        # -if current node is head reassign the next one as head
        #   else reassign the next from the predecessor
        #   the node after the current one
        if curNode is self._head:
            self._head = curNode.next
        else:
            predNode.next = curNode.next

        # -if current node is tail predecessor node will be tail
        if curNode is self._tail:
            self._tail = predNode
        
        return curNode.data

    def remove(self, item):
        """
        Remove given item from list.

        Args:
            item ([type]): Object which should be removed.

        Raises:
            ValueError: If item not in list.

        Returns:
            [type]: Removed object.
        """
        # -create a predecessor node and assign the head as current node
        predNode = None
        curNode = self._head

        # -search for the given item, raise error if None (last one) is found
        while curNode is not None and curNode.data != item:
            predNode = curNode
            curNode = curNode.next

        if curNode is None:
            raise ValueError(
                "LinkedList.remove({0}): {0} not in list".format(item))

        self._size -= 1
        return self._removal(predNode, curNode)

    def pop(self, index=-1):
        """
        Remove item at a given index.

        Args:
            index (int, optional): Index of the object which should be removed. Defaults to -1.

        Raises:
            IndexError: When index out of range.

        Returns:
            [type]: Removed object.
        """
        res = self._index_check(index)
        if res:
            raise IndexError(res)

        index = self._negativeIndices(index)

        # -create a predecessor node and assign the head as current node
        predNode = None
        curNode = self._head

        # -loop through the nodes till the matching index is found
        i = 0
        while index != i:
            predNode = curNode
            curNode = curNode.next
            i += 1

        self._size -= 1
        return self._removal(predNode, curNode)

    # ----------------------------------Helpers---------------------------------- #

    def _listGenerator(self, head):
        """
        Replaces the need for a Iterator-Class.
        Returns a generator Object which hold the currently indexed item.

        Yields:
            [type]: The Object at a given index.
        """
        curNode = head
        while curNode is not None:
            yield curNode.data
            curNode = curNode.next

    def _fromIter(self, iterable):
        """
        Initialize the linked list with elements from a given iterable.

        Args:
            iterable ([type]): An object that can be traversed.
        """
        for obj in iterable:
            self.append(obj)


class _LinkedNode(object):
    def __init__(self, data, nextItem=None):
        self.data = data
        self.next = nextItem

    def __str__(self):
        return str(self.data)
