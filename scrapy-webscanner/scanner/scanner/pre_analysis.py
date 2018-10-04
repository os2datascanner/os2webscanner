import time
import magic
import pickle
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from pathlib import Path
from anytree import Node, PreOrderIter


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


class PreDataScanner(object):
    def __init__(self, path):
        self.root = path.stat().st_ino
        self.nodes = {}
        self.stats = {}
        self.read_file_system(path)

    def read_file_system(self, path):
        self.nodes[self.root] = Node(p, size=0, filetype='Directory')
        self.read_dirtree()

        # We have not yet read the files, so at this point the
        # node-dict contains only directories
        self.stats['number_of_dirs'] = len(self.nodes)
        self.stats['number_of_files'] = self.read_files()
        self.stats['total-size'] = self.determine_file_information()

    def read_dirtree(self):
        dir = self.nodes[self.root].name
        all = dir.glob('**')
        next(all)  # The root of the tree is already created
        for item in all:
            item_inode = item.stat().st_ino
            parent_inode = item.parent.stat().st_ino
            self.nodes[item_inode] = Node(item, size=0, filetype='Directory',
                                          parent=self.nodes[parent_inode])

    def read_files(self):
        new_nodes = {}
        for node in PreOrderIter(self.nodes[self.root]):
            dir = node.name
            items = dir.glob('*')
            for item in items:
                if item.is_dir():
                    continue
                if item.is_symlink():
                    continue
                item_inode = item.stat().st_ino
                new_nodes[item_inode] = Node(item, parent=node, size=0)
        self.nodes.update(new_nodes)
        return(len(new_nodes))

    def determine_file_information(self):
        """ Read through all file-nodes. Attach size and
        filetype to all of them.
        :param nodes: A dict with all nodes
        :param root: Pointer to root-node
        :return: Total file size in bytes
        """
        magic_parser = magic.Magic(mime=False, uncompress=False)
        total_size = 0
        for node in PreOrderIter(self.nodes[self.root]):
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

    def check_file_group(self, filetype, size=0):
        for node in PreOrderIter(self.nodes[self.root]):
            if (node.filetype == filetype) and (node.size > size):
                print(node)

    def summarize_file_types(self):
        filetypes = {}
        for node in PreOrderIter(self.nodes[self.root]):
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


if __name__ == '__main__':
    t = time.time()
    p = Path('/home/robertj')

    try:
        with open('pre_scanner.p', 'rb') as f:
            pre_scanner = pickle.load(f)
    except FileNotFoundError:
        pre_scanner = PreDataScanner(p)
        with open('pre_scanner.p', 'wb') as f:
            pickle.dump(pre_scanner, f, pickle.HIGHEST_PROTOCOL)
    print('Load-time: {:.1f}s'.format(time.time() - t))

    # TODO: Performance check, something is slower than before
    # the code was turned into a class
    nodes = pre_scanner.nodes
    stats = pre_scanner.stats
    root_inode = pre_scanner.root

    filetypes = pre_scanner.summarize_file_types()

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

    pre_scanner.check_file_group('Virtual Machine')
