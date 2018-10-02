import time
import magic
import mimetypes
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from pathlib import Path
from anytree import Node, PreOrderIter

stats = {}
magic_parser = magic.Magic(mime=False, uncompress=False)

def file_type_group(filetype):
    types = {}
    types['Git'] = ['Git']
    types['Text'] = ['ASCII', 'ISO-8859', 'XML', 'HTML', 'UTF-',
                     'Microsoft Word', 'Composite', 'Excel', 'OpenDocument',
                     'vCalendar']
    types['Sound & Video'] = ['SysEx', 'Audio', 'WebM', 'Matroska', 'MPEG']
    types['Compressed file'] = ['Microsoft Cabinet', 'current ar archive',
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
    types['Virtual Machine'] = ['VirtualBox']
    types['Cache data'] = ['data', 'empty']
    types['Image'] = ['YUV', 'Icon', 'icon', 'SVG', 'RIFF', 'PNG',
                      'GIF', 'JPEG']
    types['Source Code'] = ['C source' 'byte-compiled', 'C#', 'C++',
                            'Java', 'Dyalog APL']
    
    for group in types.keys():
        for current_type in types[group]:
            if filetype.find(current_type) > -1:
                return group
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

def read_dirtree(dir, nodes):
    all = dir.glob('**')
    i = 0
    #nodes[dir] = Node(dir, parent=None)
    next(all)
    for item in all:
        item_inode = item.stat().st_ino
        parent_inode = item.parent.stat().st_ino
        nodes[item_inode] = Node(item, parent=nodes[parent_inode], size=0)
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
    type = {}
    total_size = 0
    for node in PreOrderIter(nodes[root]):
        item = node.name
        if item.is_file():
            size = item.stat().st_size
            node.size=size
            total_size += size
            filetype = magic_parser.from_file(str(item))
            filetype = file_type_group(filetype)


            node.filetype = filetype
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

if __name__ == '__main__':
    t = time.time()

    pp = PdfPages('multipage.pdf')

    p = Path('/home/robertj')
    nodes = {}   

    root_inode = p.stat().st_ino
    nodes[root_inode] = Node(p)
    nodes = read_dirtree(p, nodes)
    stats['number_of_dirs'] = len(nodes)

    print('Dir-count time: {:.2f}s'.format(time.time() -t))
    
    stats['number_of_files'] = read_files(nodes, root_inode)
    print('file-count time: {:.2f}s'.format(time.time() -t))

    total_size = determine_file_information(nodes, root_inode)
    stats['total-size'] = total_size
    print('file-size time: {:.2f}s'.format(time.time() -t))

    filetypes = summarize_file_types(nodes, root_inode)
    print('file-summary time: {:.2f}s'.format(time.time() -t))

    print('--- Stats ---')
    print('Total directories: {}'.format(stats['number_of_dirs']))
    print('Total Files: {}'.format(stats['number_of_files']))
    print('Total Size: {}'.format(_to_filesize(stats['total-size'])))

    labels = []
    sizes = []
    counts = []
    for filetype, stat in filetypes.items():
        size = _to_filesize(sum(stat['sizedist']))
        status_string = 'Mime-type: {}, number of files: {}, total_size: {}'
        print(status_string.format(filetype, stat['count'], size))

        size_list = np.array(stat['sizedist'])
        size_list = size_list / 1024

        fig = plt.figure()
        plt.hist(size_list, bins=50, log=True)
        plt.title(filetype)
        plt.xlabel('Size / KB')
        plt.savefig(pp, format='pdf')
        plt.close()

        labels.append(filetype)
        sizes.append(sum(stat['sizedist']))
        counts.append(stat['count'])
        

        
    fig1, ax1 = plt.subplots()
    ax1.pie(sizes, labels=labels, autopct='%1.1f%%',
            shadow=False, startangle=90)
    ax1.axis('equal')

    plt.savefig(pp, format='pdf')
    plt.close()

    pp.close()
