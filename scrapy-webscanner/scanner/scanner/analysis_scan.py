import os
import sys


def get_dir_and_files_count(path):
    """Return total number of files and directories for all subfolders included."""
    # In python 3.5 walk uses scandir
    if os.path.isdir(path):
        all_files = []
        all_dirs = []
        for dirpath, dirs, files in os.walk(path):
            all_files += files
            all_dirs += dirs
    else:
        print('Path is not a directory')
        return 0, 0

    return len(all_dirs), len(all_files)


def get_tree_size(path):
    """Return total size of files in path and subdirs. If
    is_dir() or stat() fails, print an error message to stderr
    and assume zero size (for example, file has been deleted).
    """
    total = 0
    for entry in os.scandir(path):
        try:
            is_dir = entry.is_dir(follow_symlinks=False)
        except OSError as error:
            print('Error calling is_dir():', error, file=sys.stderr)
            continue
        if is_dir:
            total += get_tree_size(entry.path)
        else:
            try:
                total += entry.stat(follow_symlinks=False).st_size
            except OSError as error:
                print('Error calling stat():', error, file=sys.stderr)
    return total
