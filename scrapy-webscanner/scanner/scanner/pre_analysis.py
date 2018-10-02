import time
import magic
import pickle
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from pathlib import Path
from anytree import Node, PreOrderIter

magic_parser = magic.Magic(mime=False, uncompress=False)


def file_type_group(filetype):
    types = {}
    types['Git'] = ['Git']
    types['Text'] = ['ASCII', 'ISO-8859', 'XML', 'HTML', 'UTF-',
                     'Microsoft Word', 'Composite', 'Excel', 'OpenDocument',
                     'vCalendar']
    types['Sound & Video'] = ['SysEx', 'Audio', 'WebM', 'Matroska', 'MPEG']
    types['Compressed files'] = ['Microsoft Cabinet', 'current ar archive',
                                 'Zip', 'zip', 'Par archive', 'tar', 'XZ',
                                 'zlib']
    types['Data'] = ['Media descriptor 0xf4', 'TDB database', 'SQLite',
                     'very short file', 'FoxPro', 'GVariant',  'Debian',
                     'dBase III', 'PEM certificate', 'OpenType', 'RSA',
                     'OpenSSH', 'Applesoft', 'GStreamer', 'Snappy', 'snappy',
                     'GPG', 'PGP', 'Mini DuMP', 'Font', 'TrueType', 'PPD',
                     'GNU mes', 'GNOME', 'ColorSync', 'Berkeley']
    types['PDF'] = ['PDF']
    types['ISO Image'] = ['ISO 9660',  'ISO Media']
    types['Executable'] = ['ELF', 'Executable', 'executable', 'PE32',
                           'amd 29K']
    types['Virtual Machines'] = ['VirtualBox']
    types['Cache data'] = ['data', 'empty']
    types['Images'] = ['YUV', 'Icon', 'icon', 'SVG', 'RIFF', 'PNG',
                       'GIF', 'JPEG']
    types['Source Code'] = ['C source', 'byte-compiled', 'C#', 'C++',
                            'Java', 'Dyalog APL']

    for group in types.keys():
        for current_type in types[group]:
            if filetype.find(current_type) > -1:
                filetype = group
    return filetype


def check_file_group(nodes, root, filetype, size=0):
    for node in PreOrderIter(nodes[root]):
        if (node.filetype == filetype) and (node.size > size):
            print(node)


def _to_filesize(filesize):
    sizes = {0: 'Bytes', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}
    filesize = float(filesize)
    for i in range(0, len(sizes)):
        if (filesize / 1024) > 1:
            filesize = filesize / 1024
        else:
            break
    formatted_size = ('{:.1f}{}'.format(filesize, sizes[i]))
    return formatted_size


def read_dirtree(dir, nodes):
    all = dir.glob('**')
    next(all)  # The root of the tree is already created
    for item in all:
        item_inode = item.stat().st_ino
        parent_inode = item.parent.stat().st_ino
        nodes[item_inode] = Node(item, parent=nodes[parent_inode], size=0,
                                 filetype='Directory')
    return nodes


def read_files(nodes, root):
    new_nodes = {}
    for node in PreOrderIter(nodes[root]):
        dir = node.name
        items = dir.glob('*')
        for item in items:
            if item.is_dir():
                continue
            if item.is_symlink():
                continue
            item_inode = item.stat().st_ino
            new_nodes[item_inode] = Node(item, parent=node, size=0)
    nodes.update(new_nodes)
    return(len(new_nodes))


def determine_file_information(nodes, root):
    """ Read through all file-nodes. Attach size and
    filetype to all of them.
    :param nodes: A dict with all nodes
    :param root: Pointer to root-node
    :return: Total file size in bytes
    """
    total_size = 0
    for node in PreOrderIter(nodes[root]):
        item = node.name
        if item.is_file():
            size = item.stat().st_size
            node.size = size
            total_size += size
            filetype = magic_parser.from_file(str(item))
            filetype = file_type_group(filetype)
            node.filetype = filetype
        else:
            node.filetype = 'Directory'
    return total_size


def summarize_file_types(nodes, root):
    filetypes = {}
    for node in PreOrderIter(nodes[root]):
        if not node.name.is_file():
            continue
        ft = node.filetype
        if node.filetype in filetypes:
            filetypes[ft]['count'] += 1
            filetypes[ft]['sizedist'].append(node.size)
        else:
            filetypes[ft] = {'count': 1,
                             'sizedist': [node.size]}
    return filetypes


def read_file_system(path):
    root = path.stat().st_ino
    nodes = {}
    stats = {}

    nodes[root] = Node(p, size=0, filetype='Directory')
    nodes = read_dirtree(path, nodes)
    stats['number_of_dirs'] = len(nodes)
    stats['number_of_files'] = read_files(nodes, root)
    stats['total-size'] = determine_file_information(nodes, root)

    file_system = {'nodes': nodes,
                   'stats': stats,
                   'root': p.stat().st_ino}
    return file_system


if __name__ == '__main__':
    t = time.time()

    try:
        with open('file_system.p', 'rb') as f:
            file_system = pickle.load(f)
    except FileNotFoundError:
        p = Path('/home/robertj')
        file_system = read_file_system(p)
        with open('file_system.p', 'wb') as f:
            pickle.dump(file_system, f, pickle.HIGHEST_PROTOCOL)

    print('Load-time: {:1f}s'.format(time.time() - t))
    nodes = file_system['nodes']
    stats = file_system['stats']
    root_inode = file_system['root']

    filetypes = summarize_file_types(nodes, root_inode)
    print('--- Stats ---')
    print('Total directories: {}'.format(stats['number_of_dirs']))
    print('Total Files: {}'.format(stats['number_of_files']))
    print('Total Size: {}'.format(_to_filesize(stats['total-size'])))

    pp = PdfPages('multipage.pdf')
    labels = []
    sizes = []
    counts = []
    for filetype, stat in filetypes.items():
        size = _to_filesize(sum(stat['sizedist']))
        status_string = 'Mime-type: {}, number of files: {}, total_size: {}'
        print(status_string.format(filetype, stat['count'], size))

        size_list = np.array(stat['sizedist'])
        size_list = size_list / 1024**2

        fig = plt.figure()
        plt.hist(size_list, range=(0, max(size_list)), bins=50, log=True)
        plt.title(filetype)
        plt.xlabel('Size / MB')
        plt.savefig(pp, format='pdf')
        plt.close()

        labels.append(filetype)
        sizes.append(sum(stat['sizedist']))
        counts.append(stat['count'])

    other = 0
    compact_sizes = []
    compact_labels = []
    for i in range(0, len(sizes)):
        if (sizes[i] / stats['total-size']) < 0.025:
            other += sizes[i]
        else:
            compact_sizes.append(sizes[i])
            compact_labels.append(labels[i])
    compact_labels.append('Other')
    compact_sizes.append(other)

    explode = [0.4 if (i / stats['total-size']) < 0.05 else 0
               for i in compact_sizes]

    fig1, ax1 = plt.subplots()
    textprops = {'fontsize': 'x-small'}
    wedges, texts, autotext = ax1.pie(compact_sizes, autopct='%1.0f%%',
                                      shadow=False, startangle=90,
                                      explode=explode,
                                      textprops=textprops)
    ax1.axis('equal')
    ax1.legend(wedges, compact_labels, fontsize='x-small')

    plt.savefig(pp, format='pdf')
    plt.close()

    pp.close()

    check_file_group(nodes, root_inode, 'Virtual Machine')
