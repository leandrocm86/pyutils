from collections.abc import Callable, Iterable


def groupby[T, S](iterable: Iterable[T], key: Callable[[T], S], ignore_nones=True) -> dict[S, list[T]]:
    """ Similar to more_itertools.map_reduce, grouping items from a list into a dict of lists.\n
        The key parameter is the function to be applied on each item to define its key on the dict.\n
        By default, keys resulting in None are ignored (that can be changed with the ignore_nones parameter).\n
        This implementation is different from itertools.groupby because the list doesn't need to be sorted beforehand,
        and also because it returns a whole dict instead of iterators. """
    output: dict[S, list[T]] = {}
    for e in iterable:
        elem_key = key(e)
        if elem_key is not None or not ignore_nones:
            output.setdefault(elem_key, []).append(e)
    return output


def printlist[T](list: Iterable[T], header='', elem_to_string: Callable[[T], str] = lambda e: str(e), separator=', '):
    print(header + separator.join([elem_to_string(e) for e in list]))


def flat[T](list_of_lists: Iterable[T | Iterable[T] | Iterable[Iterable[T]]]) -> list[T]:
    '''
        Flattens n-depth collections, outputing a single regular list with all inner elements.\n
        note: type hints get confused after depth = 3 (list of lists of lists).
    '''
    flatlist = []

    def add(iterable):
        for item in iterable:
            # str is also an Iterable, but we must treat it as an element in this context.
            if isinstance(item, Iterable) and not isinstance(item, str):
                add(item)
            else:
                flatlist.append(item)

    add(list_of_lists)
    return flatlist


def compare[T](list1: Iterable[T], list2: Iterable[T]) -> tuple[list[T], list[T], list[T]]:
    '''
        Compares two collections and returns a tuple with the following values:\n
        [0] - items present in both collections; # similar to set(list1).intersection(list2)\n
        [1] - items present exclusively in the first collection; # similar to set(list1).difference(list2)\n
        [2] - items present exclusively in the second collection # similar to set(list2).difference(list1)
    '''
    commons, list1_exclusives, list2_exclusives = [], [], []

    for item in list1:
        if item in list2:
            commons.append(item)
        else:
            list1_exclusives.append(item)

    for item in list2:
        if item not in commons:
            list2_exclusives.append(item)

    return commons, list1_exclusives, list2_exclusives
