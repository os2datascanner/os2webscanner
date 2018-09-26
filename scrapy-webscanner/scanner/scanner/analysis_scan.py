import os


def get_dir_files_and_bytes_count(path):
    """Return total count of files, directories and bytes for all subfolders included."""
    # In python 3.5 walk uses scandir
    if os.path.isdir(path):
        result = {
            "total_bytes": 0,
            "total_dirs": 0,
            "total_files": 0,
        }

        for root, dirs, files in os.walk("/usr/share"):
            result["total_files"] += len(files)
            result["total_dirs"] += len(dirs)
            total_bytes = [os.lstat(os.path.join(root, f)).st_size for f in files]
            result["total_bytes"] += sum(total_bytes)
    else:
        print('Path is not a directory')
        return None

    return result["total_files"], result["total_dirs"], result["total_bytes"]
