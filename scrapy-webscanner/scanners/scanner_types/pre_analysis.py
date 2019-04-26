import time
import magic
from xattr import xattr
from struct import unpack
import mimetypes
import logging
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from pathlib import Path
from matplotlib.backends.backend_pdf import PdfPages

matplotlib.use('Agg')

def _type_dict(group, sub, mime=None, relevant=False, supported=None):
    type_dict = {'super-group': group,
                 'sub-group': sub,
                 'mime': mime,
                 'relevant': relevant,
                 'supported': supported}
    return type_dict

# stat(2) calls over the network seem to be very expensive, so this cache
# class stores and reuses their results as much as possible
from stat import S_ISREG, S_ISDIR, S_ISLNK
class _statcache(dict):
    def __missing__(self, path):
        try:
            s = path.stat()
            self[path] = s
            return s
        except FileNotFoundError:
            pass

    def _test_if(self, path, func, default):
        s = self[path]
        return func(s) if s else default

    def is_file(self, path):
        return self._test_if(path, lambda s: S_ISREG(s.st_mode), False)
    def is_dir(self, path):
        return self._test_if(path, lambda s: S_ISDIR(s.st_mode), False)
    def is_symlink(self, path):
        return self._test_if(path, lambda s: S_ISLNK(s.st_mode), False)
statcache = _statcache()

types = {}

# Seveal of the ascii-types should be sorted by the mime-type
types['ASCII'] = _type_dict(
    'Text', 'Text',
    ['javascript', 'x-sql', 'json', 'x-diff', 'text/plain', 'x-trash', 'csv',
     'rdp', 'markdown', 'x-ica', 'text/css', 'x-info', 'x-ctx', 'x-cache',
     'rfc822', 'x-csrc', 'x-mif', 'x-chdr', 'x-troff-man', 'x-ruby'],
    True, 'text.py')
types['Rich Text'] = _type_dict('Text', 'Text', ['application/rtf'],
                                True, 'text.py')
types['ISO-8859'] = _type_dict('Text', 'Text', None, True, 'text.py')
types['UTF-'] = _type_dict('Text', 'Text', None, True, 'text.py')
types['vCalendar'] = _type_dict('Text', 'Text', ['calendar'], True, None)
types['Event Log'] = _type_dict('Text', 'Text', None, True, None)
types['vCard'] = _type_dict('Text', 'Text', ['vcard'], True, None)
types['sendmail m4'] = _type_dict('Text', 'Text', None, True, None)
types['Microsoft Word'] = _type_dict('Text', 'Office', ['msword'], True,
                                     'libreoffice.py')
types['Excel'] = _type_dict('Text', 'Office', ['vnd.ms-excel'],
                            True, 'libreoffice.py')
types['PowerPoint'] = _type_dict('Text', 'Office',
                                 ['vnd.ms-powerpoint'], True, 'libreoffice.py')
types['OpenDocument'] = _type_dict('Text', 'Office',
                                   ['vnd.oasis.opendocument.text',
                                    'vnd.oasis.opendocument.database',
                                    'vnd.oasis.opendocument.presentation',
                                    'vnd.oasis.opendocument.spreadsheet'],
                                   True, 'libreoffice.py')

# For some of these, magic is plain wrong
types['Composite'] = _type_dict('Text', 'Office', ['vnd.visio', 'x-msi'],
                                True, 'libreoffice.py')

# Several fils wrongly ends up here
types['XML'] = _type_dict('Text', 'Structured Text',
                          ['xml', 'x-ms-manifest', 'x-ganttproject'],
                          True, 'xml.py')

# hta should not be send here by libmagic?
types['HTML'] = _type_dict('Text', 'Structured Text',
                           ['html', 'application/hta'], True, 'html.py')

types['C#'] = _type_dict('Text', 'Source Code', ['x-pdb'], True, None)
types['Perl'] = _type_dict('Text', 'Source Code', ['x-perl'], True, None)
types['Python'] = _type_dict('Text', 'Source Code', ['x-python'], False, None)
types['shell script'] = _type_dict('Text', 'Source Code', ['x-sh'], False, None)
types['Java'] = _type_dict('Text', 'Source Code', ['x-java'], True, None)
types['Dyalog APL'] = _type_dict('Text', 'Source Code', None, True, None)
types['byte-compiled'] = _type_dict('Binary', 'Source Code', None, False, None)
types['SysEx'] = _type_dict('Media', 'Sound', None, False, None)
types['Audio'] = _type_dict('Media', 'Sound', ['audio/mpeg'], False, None)
types['MP4'] = _type_dict('Media', 'Video', ['mp4'], False, None)
types['MED_Song'] = _type_dict('Media', 'Sound', None, False, None)
types['WebM'] = _type_dict('Media', 'Video', ['webm'], False, None)
types['Matroska'] = _type_dict('Media', 'Video', ['matroska'], False, None)
types['MPEG'] = _type_dict('Media', 'Video', ['video/mpeg'], False, None)
types['QuickTime'] = _type_dict('Media', 'Video', ['quicktime'], False, None)
types['Git'] = _type_dict('Data', 'Text', None, False, None)
types['Media descriptor 0xf4'] = _type_dict('Data', 'Data', None, False, None)
types['TDB database'] = _type_dict('Data', 'Data', None, False, None)
types['SQLite'] = _type_dict('Data', 'Data', None, False, None)
types['very short file'] = _type_dict('Data', 'Data', None, False, None)
types['Qt Traslation'] = _type_dict('Data', 'Data', None, False, None)
types['FoxPro'] = _type_dict('Data', 'Data', None, False, None)
types['GVariant'] = _type_dict('Data', 'Data', None, False, None)
types['Debian'] = _type_dict('Data', 'Data', ['x-debian-package'], False, None)
types['dBase III'] = _type_dict('Data', 'Data', None, False, None)
types['PEM certificate'] = _type_dict('Data', 'Data',
                                      ['x-x509-ca-cert'], False, None)
types['OpenType'] = _type_dict('Data', 'Data', ['vnd.ms-fontobject'],
                               False, None)
types['RSA'] = _type_dict('Data', 'Data', None, False, None)
types['OpenSSH'] = _type_dict('Data', 'Data', None, False, None)
types['Applesoft'] = _type_dict('Data', 'Data', None, False, None)
types['GStreamer'] = _type_dict('Data', 'Data', None, False, None)
types['Snappy'] = _type_dict('Data', 'Data', None, False, None)
types['snappy'] = _type_dict('Data', 'Data', None, False, None)
types['GStreamer'] = _type_dict('Data', 'Data', None, False, None)
types['Minix filesystem'] = _type_dict('Data', 'Data', None, False, None)
types['SE Linux policy'] = _type_dict('Data', 'Data', None, False, None)
types['binary'] = _type_dict('Data', 'Data', None, False, None)
types['Compiled terminfo'] = _type_dict('Data', 'Data', None, False, None)
types['GPG'] = _type_dict('Data', 'Data', None, False, None)
types['PGP'] = _type_dict('Data', 'Data', ['pgp'], False, None)
types['Mini Dump'] = _type_dict('Data', 'Data', None, False, None)
types['Font'] = _type_dict('Data', 'Data', ['font-woff', 'x-font'], False, None)
types['GUS patch'] = _type_dict('Data', 'Data', None, False, None)
types['TrueType'] = _type_dict('Data', 'Data', ['font-sfnt'], False, None)
types['SoftQuad'] = _type_dict('Data', 'Data', None, False, None)
types['PPD'] = _type_dict('Data', 'Data', None, False, None)
types['GNU mes'] = _type_dict('Data', 'Data', None, False, None)
types['GNOME'] = _type_dict('Data', 'Data', None, False, None)
types['ColorSync'] = _type_dict('Data', 'Data', None, False, None)
types['Berkeley'] = _type_dict('Data', 'Data', None, False, None)
types['ESRI Shapefile'] = _type_dict('Data', 'Data', ['x-qgis'], False, None)
types['Flash'] = _type_dict('Data', 'Data', ['x-flv'], False, None)
types['Microsoft ASF'] = _type_dict('Data', 'Data', ['x-ms-wmv'], False, None)
types['DWG AutoDesk'] = _type_dict('Data', 'Data', None, False, None)
types['CLIPPER'] = _type_dict('Data', 'Data', None, False, None)
types['Transport Neutral'] = _type_dict('Data', 'Data', None, False, None)
types['shortcut'] = _type_dict('Data', 'Data', None, False, None)
types['Windows Registry'] = _type_dict('Data', 'Data', None, False, None)
types['init='] = _type_dict('Data', 'Data', None, False, None)
types['tcpdump'] = _type_dict('Data', 'Data', ['vnd.tcpdump.pcap'],
                              False, None)

# In principle, this could be relevat, but hard...
types['Access Database'] = _type_dict('Data', 'Data', ['msaccess'], False, None)

types['Solitaire Image'] = _type_dict('Data', 'Data', None, False, None)
types['GeoSwath RDF'] = _type_dict('Data', 'Data', None, False, None)
types['CDFV2 Encrypted'] = _type_dict('Data', 'Data', None, False, None)
types['Translation'] = _type_dict('Data', 'Data', None, False, None)
types['X11 cursor'] = _type_dict('Data', 'Data', None, False, None)
types['MSX ROM'] = _type_dict('Data', 'Data', None, False, None)
types['Quake'] = _type_dict('Data', 'Data', None, False, None)
types['empty'] = _type_dict('Data', 'Data', None, False, None)

# Several types ends here, include some certificates
# x-maker is identifed wrong by magic
# midi is wrong by mime...
types['data'] = _type_dict('Data', 'Cache Data',
                           ['vnd.ms-pki.seccat', 'x-cerius', 'x-pkcs12',
                            'onenote', 'x-koan', 'audio/ogg', 'x-maker',
                            'x-internet-signup', 'midi', 'x-director',
                            'x-cdx'], False, None)
types['PDF'] = _type_dict('Media', 'PDF', ['pdf'], True, 'pdf.py')
types['PostScript'] = _type_dict('Media', 'PDF', ['postscript'], True, None)
types['PNG'] = _type_dict('Media', 'Image', ['png'], True, 'ocr.py')
types['GIF'] = _type_dict('Media', 'Image', ['gif'], True, 'ocr.py')

# Why is bmp in jpeg?
types['JPEG'] = _type_dict('Media', 'Image',
                           ['jpeg', 'x-ms-bmp'], True, 'ocr.py')
types['tiff'] = _type_dict('Media', 'Image',
                           ['tiff', 'x-nikon-nef'], True, 'ocr.py')
types['YUV'] = _type_dict('Media', 'Image', None, True, None)
types['Icon'] = _type_dict('Media', 'Image', ['vnd.microsoft.icon'], False, None)
types['SVG'] = _type_dict('Media', 'Image', None, False, None)
types['Photoshop'] = _type_dict('Media', 'Image', ['x-photoshop'], True, None)
types['RIFF'] = _type_dict('Media', 'Video', ['x-wav', 'x-msvideo'], False, None)
types['bitmap'] = _type_dict('Media', 'Image', None, False, None)
types['ISO Media'] = _type_dict('Container', 'ISO Image', None, True, None)
types['ISO Image'] = _type_dict('Container', 'ISO Image', None, True, None)
types['ISO 9660'] = _type_dict('Container', 'ISO Image', ['x-iso9660-image'],
                               True, None)

# Some of these are not a real zip-files. Combined type-check would help.
types['Zip'] = _type_dict('Container', 'Archive',
                          ['application/zip', 'x-xpinstall', 'java-archive',
                           'vnd.android.package-archive',
                           'vnd.ms-word.document.macroEnabled.12',
                           'vnd.ms-word.template.macroEnabled.12',
                           'vnd.google-earth.kmz',
                           'vnd.ms-officetheme'],
                          True, 'zip.py')
types['xz'] = _type_dict('Container', 'Archive', ['xz'], True, None)
types['gzip'] = _type_dict('Container', 'Archive', ['gzip'], True, None)
types['7-zip'] = _type_dict('Container', 'Archive',
                            ['x-7z-compressed'], True, None)
types['bzip'] = _type_dict('Container', 'Archive', ['bzip2'], True, None)
types['Microsoft Cabinet'] = _type_dict('Container', 'Archive',
                                        ['x-cab'], True, None)
types['Tar'] = _type_dict('Container', 'Archive', ['x-tar'], True, None)
types['Par archive'] = _type_dict('Container', 'Archive', None, True, None)
types['current ar archive'] = _type_dict('Container', 'Archive', None, True,
                                         None)
types['RAR archive'] = _type_dict('Container', 'Archive',
                                  ['application/rar'], True, None)
types['XZ'] = _type_dict('Container', 'Archive', None, True, None)
types['zlib'] = _type_dict('Container', 'Archive', None, True, None)
types['VirtualBox'] = _type_dict('Container', 'Virtual Machine', None, False,
                                 None)
types['ELF'] = _type_dict('Data', 'Executable', ['octet-stream'], False, None)
types['PE32'] = _type_dict('Data', 'Executable', None, False, None)
types['Executable'] = _type_dict('Data', 'Executable', ['x-msdos-program'],
                                 False, None)
types['amd 29K'] = _type_dict('Data', 'Executable', None, False, None)

types['ERROR'] = _type_dict('Error', 'Error', None, True, None)

def file_type_group(filetype, mime=False):
    # Todo: A combined magic + mime-search will be even more accurate

    if mime is False:
        for current_type in types.keys():
            if filetype.lower().find(current_type.lower()) > -1:
                filetype = types[current_type]
                return filetype
    else:
        for current_type in types.values():
            mimetypes = current_type['mime']
            if mimetypes is None:
                continue
            assert(isinstance(mimetypes, list))
            for mimetype in mimetypes:
                if filetype.find(mimetype) > -1:
                    filetype = current_type
                    return filetype
    filetype = _type_dict('Unknown', filetype, None, True, None)
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


_HIDDEN = 0x02
def _is_hidden(path):
    try:
        if path.name.startswith("."):
            return True
        else:
            attr_bitmap = \
                unpack("<I", xattr(str(path)).get("user.cifs.dosattrib"))[0]
            return bool(attr_bitmap & _HIDDEN)
    except IOError:
        return False


class PreDataScanner(object):
    def __init__(self, path, detection_method='fast-magic'):
        if detection_method not in ['fast-magic', 'magic', 'mime']:
            # Also add an option to use both
            exit('Unsupport type detection')
        else:
            self.detection_method = detection_method
        self.nodes = {}
        self.stats = {}
        self.t0 = time.time()
        self.read_file_system(path)

    def read_file_system(self, path):
        self.nodes[path] = {'size': 0,
                            'filetype': _type_dict('Directory', 'Directory',
                                                   False, None)}
        self.read_dirtree(path)

        # We have not yet read the files, so at this point the
        # node-dict contains only directories
        self.stats['number_of_dirs'] = len(self.nodes)
        self.stats['time_number_of_dirs'] = time.time() - self.t0
        status_string = 'Read {} directories. Total run-time: {:.2f}s'
        logging.info(status_string.format(self.stats['number_of_dirs'],
                                          self.stats['time_number_of_dirs']))

        self.stats['number_of_files'] = self.read_files()
        status_string = 'Read {} directories. Total run-time: {:.2f}s'
        self.stats['time_number_of_files'] = time.time() - self.t0
        status_string = 'Read {} files. Total run-time: {:.2f}s'
        logging.info(status_string.format(self.stats['number_of_files'],
                                          self.stats['time_number_of_files']))
        self.stats['total_size'] = self.determine_file_information()
        self.stats['time_file_types'] = time.time() - self.t0
        status_string = 'Generated metadata for {} files. Total run-time: {:.2f}s'
        logging.info(status_string.format(self.stats['number_of_files'],
                                          self.stats['time_number_of_files']))

    def read_dirtree(self, path):
        logging.info('Reading directories...')
        all_dirs = path.glob('**')
        next(all_dirs)  # The root of the tree is already created
        processed = 0
        t0 = time.time()
        t = t0
        for item in all_dirs:
            processed += 1
            if not processed % 2500:
                now = time.time()
                delta_t = now - t0
                avg_speed = processed / delta_t
                current_speed = 2500 / (now - t)
                t = now
                status = ('Progress: found {} directories in {:.0f}s. ' +
                          'Avg. Speed: {:.0f} directories/s. ' +
                          'Current Speed {:.0f} directories/s.')
                logging.info(status.format(processed, delta_t,
                                           avg_speed, current_speed))
            self.nodes[item] = {'size': 0,
                                'filetype': _type_dict('Directory', 'Directory',
                                                       False, None)}

    def read_files(self):
        logging.info('Reading files...')
        new_nodes = {}
        dirs_processed = 0
        files_processed = 0
        t0 = time.time()
        t = t0
        for node in self.nodes.keys():
            dirs_processed += 1
            if not dirs_processed % 2500:
                now = time.time()
                delta_t = now - t0
                avg_speed = dirs_processed / delta_t
                current_speed = 2500 / (now - t)
                t = now
                eta = (len(self.nodes) - dirs_processed) / current_speed
                status = ('Progress: on directory {}/{} after {:.0f}s. ' +
                          'Found {} files. ' +
                          'Avg. Speed: {:.0f} directories/s. ' +
                          'Current Speed {:.0f} directories/s. ETA: {:.0f}s.')
                logging.info(status.format(dirs_processed, len(self.nodes),
                                           delta_t, files_processed, avg_speed,
                                           current_speed, eta))
            items = node.glob('*')
            for item in items:
                files_processed += 1
                if statcache.is_dir(item):
                    continue
                if statcache.is_symlink(item):
                    continue
                if _is_hidden(item):
                    if 'hidden_file_count' not in self.stats:
                        self.stats['hidden_file_count'] = 1
                    else:
                        self.stats['hidden_file_count'] += 1
                    continue
                new_nodes[item] = {'size': 0}
        self.nodes.update(new_nodes)
        return len(new_nodes)

    def _find_file_type(self, node):
        filetype = None
        if self.detection_method == 'fast-magic':
            if node.suffix == '.txt':  # No need to check these two
                filetype = 'ASCII'
            elif node.suffix == '.html':
                filetype = 'HTML'
        if self.detection_method in ['magic', 'fast-magic'] and filetype is None:
            try:
                filetype = magic.from_buffer(open(str(node), 'rb').read(512))
            except TypeError:
                filetype = 'ERROR'
            filetype = file_type_group(filetype, mime=False)

        if self.detection_method == 'mime':
            mime_type = mimetypes.guess_type(node.name, strict=False)
            if mime_type[1] is not None:
                matchtype = mime_type[1]
            elif mime_type[0] is not None:
                matchtype = mime_type[0]
            else:
                matchtype = 'Unknown'
            filetype = file_type_group(matchtype, mime=True)
            """
            if filetype['super-group'] == 'Unknown' and matchtype is not 'Unknown':
                print()
                print(node)
                print('Mime: {}'.format(mime_type))
                magictype = magic.from_buffer(open(str(node), 'rb').read(512))
                print('Magic: {}'.format(magictype))
                import random
                if random.random() > 0.95:
                    1/0
            """
        return filetype

    def determine_file_information(self):
        """ Read through all file-nodes. Attach size and
        filetype to all of them.
        :param nodes: A dict with all nodes
        :param root: Pointer to root-node
        :return: Total file size in bytes
        """
        logging.info('Generating file metadata...')
        total_size = 0
        processed = 0
        t0 = time.time()
        t = t0
        for node in self.nodes.keys():
            processed += 1
            if not processed % 2500:
                now = time.time()
                delta_t = now - t0
                avg_speed = processed / delta_t
                current_speed = 2500 / (now - t)
                t = now
                eta = (len(self.nodes) - processed) / current_speed
                status = ('Progress: {}/{} in {:.0f}s. ' +
                          'Avg. Speed: {:.0f} files/s. ' +
                          'Current Speed {:.0f} files/s. ETA: {:.0f}s.')
                logging.info(status.format(processed, len(self.nodes), delta_t,
                                           avg_speed, current_speed, eta))
            if statcache.is_file(node):
                size = statcache[node].st_size
                self.nodes[node]['size'] = size
                total_size += size
                filetype = self._find_file_type(node)
                self.nodes[node]['filetype'] = filetype
            else:
                self.nodes[node]['filetype'] = _type_dict('Directory', 'Directory',
                                                          False, None)
        return total_size

    def check_file_group(self, filetype, size=0):
        for node in self.nodes:
            if (node['filetype'] == filetype) and (node['size'] > size):
                print(node)

    def summarize_file_types(self):
        types = {'super': {},
                 'sub': {},
                 'supported': 0,
                 'relevant': 0}

        for node in self.nodes.keys():
            node_info = self.nodes[node]
            if not statcache.is_file(node):
                continue
            supergroup = self.nodes[node]['filetype']['super-group']
            subgroup = self.nodes[node]['filetype']['sub-group']

            if node_info['filetype']['supported'] is not None:
                types['supported'] += 1
            if node_info['filetype']['relevant'] is True:
                types['relevant'] += 1

            if supergroup in types['super']:
                types['super'][supergroup]['count'] += 1
                types['super'][supergroup]['sizedist'].append(node_info['size'])
            else:
                types['super'][supergroup] = {'count': 1,
                                              'sizedist': [node_info['size']]}
            if subgroup in types['sub']:
                types['sub'][subgroup]['count'] += 1
                types['sub'][subgroup]['sizedist'].append(node_info['size'])
            else:
                types['sub'][subgroup] = {'count': 1,
                                          'sizedist': [node_info['size']],
                                          'supergroup': supergroup}
        return types

    def update_stats(self, print_output=True):
        """ Update the internal stat-collection """
        self.stats['supported_file_count'] = 0
        self.stats['supported_file_size'] = 0
        self.stats['relevant_file_count'] = 0
        self.stats['relevant_file_size'] = 0
        self.stats['relevant_unsupported_count'] = 0
        self.stats['relevant_unsupported_size'] = 0
        for file_info in self.nodes.values():
            if file_info['filetype']['relevant']:
                self.stats['relevant_file_count'] += 1
                self.stats['relevant_file_size'] += file_info['size']
            if file_info['filetype']['supported'] is not None:
                self.stats['supported_file_count'] += 1
                self.stats['supported_file_size'] += file_info['size']
            if (file_info['filetype']['supported'] is None and file_info['filetype']['relevant']):
                self.stats['relevant_unsupported_count'] += 1
                self.stats['relevant_unsupported_size'] += file_info['size']

        if print_output:
            print('--- Stats ---')
            print('Total directories: {}'.format(self.stats['number_of_dirs']))
            print('Total Files: {}'.format(self.stats['number_of_files']))
            print('Total Size: {}'.format(_to_filesize(self.stats['total_size'])))
            print()

            supported = 'Total Supported Files: {} in {}bytes'
            print(supported.format(self.stats['supported_file_count'],
                                   _to_filesize(self.stats['supported_file_size'])))

            relevant = 'Total Relevant files: {} in {}bytes'
            print(relevant.format(self.stats['relevant_file_count'],
                                  _to_filesize(self.stats['relevant_file_size'])))

            rel_unsup = 'Relevant unsupported files: {} in {}bytes'
            size = self.stats['relevant_unsupported_size']
            print(rel_unsup.format(self.stats['relevant_unsupported_count'],
                                   _to_filesize(size)))
            print('-------')
            print()

    def plot(self, pp, types):
        labels = []
        sizes = []
        counts = []
        for filetype, stat in types.items():
            size = _to_filesize(sum(stat['sizedist']))
            status_string = \
                'Mime-type: {}, number of files: {}, total_size: {}'
            print(status_string.format(filetype, stat['count'], size))

            size_list = np.array(stat['sizedist'])
            size_list = size_list / 1024**2

            plt.hist(size_list,
                    range=(0, max(size_list)), bins=50, log=True)
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
            if (sizes[i] / self.stats['total_size']) < 0.025:
                other += sizes[i]
            else:
                compact_sizes.append(sizes[i])
                compact_labels.append(labels[i])
        compact_labels.append('Other')
        compact_sizes.append(other)

        explode = [0.4 if (i / self.stats['total_size']) < 0.05 else 0
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
    p = Path('/tmp/mnt/os2webscanner/tmpxus17k2_/')

    pre_scanner = PreDataScanner(p, detection_method='mime')
    filetypes = pre_scanner.summarize_file_types()
    pre_scanner.update_stats(print_output=True)

    pp = PdfPages('multipage.pdf')
    pre_scanner.plot(pp, filetypes['super'])
    pre_scanner.plot(pp, filetypes['sub'])
    pp.close()

    # pre_scanner.check_file_group('Virtual Machine')
