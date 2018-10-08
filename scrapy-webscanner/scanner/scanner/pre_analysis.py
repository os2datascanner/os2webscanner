import time
import magic
import pickle
import numpy as np
from pathlib import Path
from anytree import Node, PreOrderIter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


def file_type_group(filetype):
    types = {}

    types['ASCII'] = {'super-group': 'Text', 'sub-group': 'Text',
                      'relevant': True, 'supported': True}
    types['ISO-8859'] = {'super-group': 'Text', 'sub-group': 'Text',
                         'relevant': True, 'supported': True}
    types['UTF-'] = {'super-group': 'Text', 'sub-group': 'Text',
                     'relevant': True, 'supported': True}
    types['vCalendar'] = {'super-group': 'Text', 'sub-group': 'Text',
                          'relevant': True, 'supported': False}
    types['Event Log'] = {'super-group': 'Text', 'sub-group': 'Text',
                          'relevant': True, 'supported': False}
    types['vCard'] = {'super-group': 'Text', 'sub-group': 'Text',
                      'relevant': True, 'supported': False}

    types['Microsoft Word'] = {'super-group': 'Text', 'sub-group': 'Office',
                               'relevant': True, 'supported': True}
    types['Excel'] = {'super-group': 'Text', 'sub-group': 'Office',
                      'relevant': True, 'supported': True}
    types['PowerPoint'] = {'super-group': 'Text', 'sub-group': 'Office',
                           'relevant': True, 'supported': True}
    types['OpenDocument'] = {'super-group': 'Text', 'sub-group': 'Office',
                             'relevant': True, 'supported': True}
    types['Composite'] = {'super-group': 'Text', 'sub-group': 'Office',
                          'relevant': True, 'supported': True}

    types['XML'] = {'super-group': 'Text', 'sub-group': 'Structure Text',
                    'relevant': True, 'supported': True}
    types['HTML'] = {'super-group': 'Text', 'sub-group': 'Structure Text',
                     'relevant': True, 'supported': True}

    types['C#'] = {'super-group': 'Text', 'sub-group': 'Source Code',
                   'relevant': True, 'supported': False}
    types['Java'] = {'super-group': 'Text', 'sub-group': 'Source Code',
                     'relevant': True, 'supported': False}
    types['Dyalog APL'] = {'super-group': 'Text', 'sub-group': 'Source Code',
                           'relevant': True, 'supported': False}

    types['byte-compiled'] = {'super-group': 'Binary',
                              'sub-group': 'Source Code',
                              'relevant': False, 'supported': False}
    types['Git'] = {'super-group': 'Text', 'sub-group': 'Data',
                    'relevant': False, 'supported': False}

    types['SysEx'] = {'super-group': 'Media', 'sub-group': 'MIDI',
                      'relevant': False, 'supported': False}
    types['Audio'] = {'super-group': 'Media', 'sub-group': 'Sound',
                      'relevant': False, 'supported': False}
    types['WebM'] = {'super-group': 'Media', 'sub-group': 'Video',
                     'relevant': False, 'supported': False}
    types['Matroska'] = {'super-group': 'Media', 'sub-group': 'Video',
                         'relevant': False, 'supported': False}
    types['MPEG'] = {'super-group': 'Media', 'sub-group': 'Video',
                     'relevant': False, 'supported': False}
    types['MED_Song'] = {'super-group': 'Media', 'sub-group': 'Video',
                         'relevant': False, 'supported': False}

    data_dict = {'super-group': 'Data', 'sub-group': 'Data', 'relevant': False,
                 'supported': False}
    types['Media descriptor 0xf4'] = data_dict
    types['TDB database'] = data_dict
    types['SQLite'] = data_dict
    types['very short file'] = data_dict
    types['FoxPro'] = data_dict
    types['GVariant'] = data_dict
    types['Debian'] = data_dict
    types['dBaseIII'] = data_dict
    types['PEM certificate'] = data_dict
    types['OpenType'] = data_dict
    types['RSA'] = data_dict
    types['OpenSSH'] = data_dict
    types['Applesoft'] = data_dict
    types['GStreamer'] = data_dict
    types['Snappy'] = data_dict
    types['snappy'] = data_dict
    types['GStreamer'] = data_dict
    types['GPG'] = data_dict
    types['PGP'] = data_dict
    types['MiniDump'] = data_dict
    types['Font'] = data_dict
    types['TrueType'] = data_dict
    types['PPD'] = data_dict
    types['GNU mes'] = data_dict
    types['GNOME'] = data_dict
    types['ColorSync'] = data_dict
    types['Berkeley'] = data_dict
    types['ESRI Shapefile'] = data_dict
    types['Flash'] = data_dict
    types['Microsoft ASF'] = data_dict
    types['DWG AutoDesk'] = data_dict
    types['CLIPPER'] = data_dict
    types['Transport Neutral'] = data_dict
    types['shortcut'] = data_dict
    types['Windows Registry'] = data_dict
    types['init='] = data_dict
    types['tcpdump'] = data_dict
    types['Solitaire Image'] = data_dict
    types['GeoSwath RDF'] = data_dict
    types['CDFV2 Encrypted'] = data_dict
    types['MSX ROM'] = data_dict
    types['empty'] = data_dict

    types['data'] = {'super-group': 'Data', 'sub-group': 'Cache Data',
                     'relevant': False, 'supported': False}
    types['PDF'] = {'super-group': 'Media', 'sub-group': 'Image',
                    'relevant': True, 'supported': True}
    types['PostScript'] = {'super-group': 'Media', 'sub-group': 'Image',
                           'relevant': True, 'supported': True}
    types['PNG'] = {'super-group': 'Media', 'sub-group': 'Image',
                    'relevant': True, 'supported': True}
    types['GIF'] = {'super-group': 'Media', 'sub-group': 'Image',
                    'relevant': True, 'supported': True}
    types['JPEG'] = {'super-group': 'Media', 'sub-group': 'Image',
                     'relevant': True, 'supported': True}
    types['YUV'] = {'super-group': 'Media', 'sub-group': 'Image',
                    'relevant': True, 'supported': False}
    types['Icon'] = {'super-group': 'Media', 'sub-group': 'Image',
                     'relevant': True, 'supported': False}
    types['SVG'] = {'super-group': 'Media', 'sub-group': 'Image',
                    'relevant': True, 'supported': False}
    types['RIFF'] = {'super-group': 'Media', 'sub-group': 'Image',
                     'relevant': True, 'supported': False}
    types['bitmap'] = {'super-group': 'Media', 'sub-group': 'Image',
                       'relevant': True, 'supported': False}

    types['ISO Image'] = {'super-group': 'Container', 'sub-group': 'ISO',
                          'relevant': True, 'supported': False}
    types['ISO 9660'] = {'super-group': 'Container', 'sub-group': 'ISO',
                         'relevant': True, 'supported': False}
    types['Microsoft Cabinet'] = {'super-group': 'Container',
                                  'sub-group': 'Archive', 'relevant': True,
                                  'supported': False}
    types['Zip'] = {'super-group': 'Container', 'sub-group': 'Archive',
                    'relevant': True, 'supported': True}
    types['Tar'] = {'super-group': 'Container', 'sub-group': 'Archive',
                    'relevant': True, 'supported': False}
    types['Par archive'] = {'super-group': 'Container',
                            'sub-group': 'Archive',
                            'relevant': True, 'supported': False}
    types['current ar archive'] = {'super-group': 'Container',
                                   'sub-group': 'Archive',
                                   'relevant': True, 'supported': False}
    types['XZ'] = {'super-group': 'Container', 'sub-group': 'Archive',
                   'relevant': True, 'supported': False}
    types['zlib'] = {'super-group': 'Container', 'sub-group': 'Archive',
                     'relevant': True, 'supported': False}
    types['VirtualBox'] = {'super-group': 'Container',
                           'sub-group': 'Virtual Machines',
                           'relevant': True, 'supported': False}

    exe_dict = {'super-group': 'Executable', 'sub-group': 'Executable',
                'relevant': False, 'supported': False}
    types['ELF'] = exe_dict
    types['PE32'] = exe_dict
    types['Executable'] = exe_dict
    types['amd 29K'] = exe_dict

    for current_type in types.keys():
        if filetype.lower().find(current_type.lower()) > -1:
            filetype = types[current_type]
            break
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
        print('Read dirs')
        self.stats['number_of_files'] = self.read_files()
        print('Read files')
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
        processed = 0
        for node in PreOrderIter(self.nodes[self.root]):
            processed += 1
            item = node.name
            print(item)
            print('Progress: {}/{}'.format(processed, len(self.nodes)))
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
        types = {'super': {},
                 'sub': {},
                 'supported': 0,
                 'relevant': 0}

        for node in PreOrderIter(self.nodes[self.root]):
            if not node.name.is_file():
                continue
            supergroup = node.filetype['super-group']
            subgroup = node.filetype['sub-group']

            if node.filetype['supported'] is True:
                types['supported'] += 1
            if node.filetype['relevant'] is True:
                types['relevant'] += 1

            if supergroup in types['super']:
                types['super'][supergroup]['count'] += 1
                types['super'][supergroup]['sizedist'].append(node.size)
            else:
                types['super'][supergroup] = {'count': 1,
                                              'sizedist': [node.size]}
            if subgroup in types['sub']:
                types['sub'][subgroup]['count'] += 1
                types['sub'][subgroup]['sizedist'].append(node.size)
            else:
                types['sub'][subgroup] = {'count': 1,
                                          'sizedist': [node.size]}

        return types


def plot(pp, types):
    labels = []
    sizes = []
    counts = []
    for filetype, stat in types.items():
        size = _to_filesize(sum(stat['sizedist']))
        status_string = 'Mime-type: {}, number of files: {}, total_size: {}'
        print(status_string.format(filetype, stat['count'], size))

        size_list = np.array(stat['sizedist'])
        size_list = size_list / 1024**2

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

if __name__ == '__main__':
    t = time.time()
    p = Path('/mnt/new_var/mailscan/users/')


    try:
        with open('pre_scanner.p', 'rb') as f:
            pre_scanner = pickle.load(f)
    except FileNotFoundError:
        pre_scanner = PreDataScanner(p)
        with open('pre_scanner.p', 'wb') as f:
            pickle.dump(pre_scanner, f, pickle.HIGHEST_PROTOCOL)
    print('Load-time: {:.1f}s'.format(time.time() - t))

    nodes = pre_scanner.nodes
    stats = pre_scanner.stats
    root_inode = pre_scanner.root

    filetypes = pre_scanner.summarize_file_types()

    print('--- Stats ---')
    print('Total directories: {}'.format(stats['number_of_dirs']))
    print('Total Files: {}'.format(stats['number_of_files']))
    print('Total Size: {}'.format(_to_filesize(stats['total-size'])))
    print()
    print('Total Supported Files: {}'.format(filetypes['supported']))
    print('Total Relevant Files: {}'.format(filetypes['relevant']))
    print('-------')
    print()

    pp = PdfPages('multipage.pdf')
    plot(pp, filetypes['super'])
    plot(pp, filetypes['sub'])
    pp.close()

    # pre_scanner.check_file_group('Virtual Machine')
