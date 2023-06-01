"""Utilities for manipulating path."""

from os import path
import sys


def from_root(relative: str):
    """
    Return the path to the file from the root of the project

    :param relative: The relative path from the root of the project
    """
    this_folder = path.dirname(sys.argv[0])
    return path.normpath(path.join(this_folder, relative))
