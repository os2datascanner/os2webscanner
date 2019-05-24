import time
import pika
import pickle
import curses
import logging
import subprocess
import multiprocessing
import psutil
try:
    from ..settings import export_path
except ImportError:
    from .settings import export_path

try:
    from PyExpLabSys.common.database_saver import DataSetSaver, CustomColumn
    from PyExpLabSys.common.supported_versions import python3_only  # noqa
    import credentials
except ImportError:
    pass

logger = logging.getLogger(__name__)
fh = logging.FileHandler('logfile.log')
fh.setLevel(logging.INFO)
logger.addHandler(fh)
logger.error('Stat start')


class Stats(multiprocessing.Process):
    def __init__(self, user_queue, log_data=False):
        psutil.cpu_percent(percpu=True)  # Initial dummy readout
        multiprocessing.Process.__init__(self)
        conn_params = pika.ConnectionParameters('localhost')
        connection = pika.BlockingConnection(conn_params)
        self.channel = connection.channel()
        self.channel.queue_declare('global')
        self.amqp_messages = {}
        self.amqp_messages['global'] = {}
        self.amqp_messages['global']['children'] = -1
        self.amqp_messages['global']['amqp_time'] = -1
        self.user_queue = user_queue
        self.scanners = []
        self.screen = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.curs_set(False)
        self.screen.keypad(1)
        self.screen.nodelay(1)
        # Measure initial values while we have the chance
        self.start_time = time.time()
        self.total_users = self.user_queue.qsize()
        self.init_du = self.disk_usage()
        self.log_data = log_data

    def _amqp_single_update(self, queue_name):
        method, header, body = self.channel.basic_get(queue_name)
        while method:  # Always empty queue, do now show old data
            body_dict = pickle.loads(body)
            self.amqp_messages[queue_name] = body_dict
            method, header, body = self.channel.basic_get(queue_name)

    def amqp_update(self):
        t = time.time()
        self._amqp_single_update('global')
        for pid in self.scanners:
            self._amqp_single_update(str(pid))
        self.amqp_messages['global']['amqp_time'] = time.time() - t

    def number_of_threads(self):
        """ Number of threads
        :return: Tuple with Number of threads, and nuber of active threads
        """
        return (len(self.scanners), self.amqp_messages['global']['children'])

    def add_scanner(self, scanner):
        """ Add a scanner to the internal list of scanners
        :param scanner: The scanner object to be added
        :return: The new number of scanners
        """
        self.scanners.append(scanner)
        return len(self.scanners)

    def disk_usage(self):
        """ Return the current disk usage
        :return: Disk usage in MB
        """
        error = True
        while error:
            try:
                du_output = subprocess.check_output(['du', '-s',
                                                     export_path],
                                                    stderr=subprocess.DEVNULL)
                error = False
            except subprocess.CalledProcessError:
                # Happens if du is called while folder is being marked done

                # logger.warn('du-error') Warning ends up in the terminal...
                # will need to investiate
                time.sleep(1)
        size = float(du_output.decode('utf-8').split('\t')[0]) / 1024
        return size

    def exported_users(self):
        """ Returns the number of exported users
        :return: Tuple with finished exports and total users
        """
        finished_users = (self.total_users - self.user_queue.qsize() -
                          self.number_of_threads()[1])
        return (finished_users, self.total_users)

    def amount_of_exported_data(self):
        """ Return the total amount of exported data (MB)
        :return: The total amount of exported data sinze start
        """
        return self.disk_usage() - self.init_du

    def memory_info(self):
        """ Returns the memory consumption (in MB) of all threads
        :return: List of memory consumptions
        """
        mem_list = {}
        for pid in self.scanners:
            try:
                process = psutil.Process(pid)
                mem_info = process.memory_full_info()
                used_memory = mem_info.uss/1024**2
                if self.log_data:
                    label = '{} memory'.format(pid)
                    dt = (time.time() - self.start_time)
                    self.data_set_saver.save_point(label, (dt, used_memory))
            except psutil._exceptions.NoSuchProcess:
                used_memory = -1
            mem_list[str(pid)] = used_memory
        return mem_list

    def status(self):
        template = ('Threads: {}. ' +
                    'Queue: {}. ' +
                    'Export: {:.3f}GB. ' +
                    'Time: {:.2f}min. ' +
                    'Speed: {:.2f}MB/s. ' +
                    'Memory consumption: {:.3f}GB. ' +
                    'Scanned users: {} / {}')
        memory = sum(self.memory_info().values()) / 1024
        processes = self.number_of_threads()[1]
        dt = (time.time() - self.start_time)
        users = self.exported_users()
        ret_str = template.format(processes,
                                  self.user_queue.qsize(),
                                  self.disk_usage() / 1024,
                                  dt / 60.0,
                                  self.amount_of_exported_data() / dt,
                                  memory,
                                  users[0], users[1])
        return ret_str

    def init_logging(self):
        if self.log_data:
            self.comment = 'Run'
            self.data_set_saver = DataSetSaver('measurements_mailscan',
                                               'xy_values_mailscan',
                                               credentials.user, credentials.passwd)
            self.data_set_saver.start()
            # PyExpLabSys does does not excell in db-normalization - add
            # metadata to all channels
            metadata = {"Time": CustomColumn(self.start_time, "FROM_UNIXTIME(%s)"),
                        "comment": self.comment, "type": 1, "label": None,
                        "processes": self.number_of_threads()[1]}

            metadata['label'] = 'Avg export speed'
            self.data_set_saver.add_measurement(metadata['label'], metadata)
            metadata['label'] = 'Total export size'
            self.data_set_saver.add_measurement(metadata['label'], metadata)
            metadata['label'] = 'Total users'
            self.data_set_saver.add_measurement(metadata['label'], metadata)
            metadata['label'] = 'Total memory'
            self.data_set_saver.add_measurement(metadata['label'], metadata)
            metadata['label'] = 'Total CPU'
            self.data_set_saver.add_measurement(metadata['label'], metadata)
            metadata['label'] = 'Total Mails'
            self.data_set_saver.add_measurement(metadata['label'], metadata)
            for scanner in self.amqp_messages.keys():
                if scanner == 'global':
                    continue
                metadata['processes'] = 1
                metadata['label'] = '{} memory'.format(scanner)
                self.data_set_saver.add_measurement(metadata['label'], metadata)
                metadata['label'] = '{} exported users'.format(scanner)
                self.data_set_saver.add_measurement(metadata['label'], metadata)

    def run(self):
        self.amqp_update()
        self.init_logging()
        processes = self.number_of_threads()[1]
        while processes:
            self.amqp_update()
            thread_info = self.number_of_threads()
            processes = thread_info[1]
            status = self.status()
            logger.info(status)
            # print(status)

            dt = int((time.time() - self.start_time))
            msg = 'Run-time: {}min {}s  '.format(int(dt / 60),
                                                 int(dt % 60))
            self.screen.addstr(2, 3, msg)

            users = self.exported_users()
            msg = 'Exported users: {}/{}  '.format(users[0], users[1])
            self.screen.addstr(3, 3, msg)

           
            total_export_size = self.amount_of_exported_data()
            msg = 'Total export: {:.3f}MB   '.format(total_export_size)
            self.screen.addstr(4, 3, msg)

            speed = total_export_size / dt
            msg = 'Avg eksport speed: {:.3f}MB/s   '.format(speed)
            self.screen.addstr(5, 3, msg)

            mem_info = self.memory_info()
            msg = 'Memory usage: {:.1f}MB'
            self.screen.addstr(6, 3, msg.format(sum(mem_info.values())))

            msg = 'amqp update time: {:.1f}ms  '
            update_time = self.amqp_messages['global']['amqp_time'] * 1000
            self.screen.addstr(7, 3, msg.format(update_time))
                                                    
            cpu_usage = psutil.cpu_percent(percpu=True)
            msg = 'CPU{} usage: {}%  '
            for i in range(0, len(cpu_usage)):
                self.screen.addstr(9 + i, 3, msg.format(i, cpu_usage[i]))

            if self.log_data:
                dt = (time.time() - self.start_time)
                label = 'Total users'
                self.data_set_saver.save_point(label, (dt, users[0]))
                label = 'Total export size'
                self.data_set_saver.save_point(label, (dt, total_export_size))
                label = 'Avg export speed'
                self.data_set_saver.save_point(label, (dt, speed))
                label = 'Total CPU'
                self.data_set_saver.save_point(label, (dt, sum(cpu_usage)))
                label = 'Total memory'
                self.data_set_saver.save_point(label,
                                               (dt, sum(mem_info.values())))


            i = i + 2
            msg = 'Total threads: {}.  '
            self.screen.addstr(9 + i, 3, msg.format(thread_info[0]))

            i = i + 1
            msg = 'Active threads: {}  '
            self.screen.addstr(9 + i, 3, msg.format(thread_info[1]))

            i = 0
            exported_grand_total = 0
            self.screen.addstr(2 + i, 50, 'Scan status:')
            i = i + 1
            for key, data in self.amqp_messages.items():
                if key == 'global':
                    continue
                msg = 'ID {}'.format(key)
                self.screen.addstr(2 + i, 50, msg)
                i = i + 1
                try:
                    if mem_info[key] > 0:
                        msg = 'Current path: {}/{}'.format(data['rel_path'],
                                                           data['folder'])
                    else:
                        msg = 'Current path: {}'.format(data['rel_path'])
                    self.screen.addstr(2 + i, 50, msg)
                    self.screen.clrtoeol()
                    i = i + 1
                    if mem_info[key] > 0:
                        run_time = (time.time() - data['start_time']) / 60.0
                    else:
                        run_time = 0
                    msg = 'Progress: {} of {} mails. Export time: {:.1f}min'
                    self.screen.addstr(2 + i, 50, msg.format(data['total_scanned'],
                                                             data['total_count'],
                                                             run_time))
                    self.screen.clrtoeol()
                    i = i + 1
                    msg = 'Exported users: {}. Exported mails: {} Total mails: {}. Memory consumption: {:.1f}MB   '
                    if self.log_data:
                        label = '{} exported users'.format(key)
                        dt = (time.time() - self.start_time)
                        eu = data['exported_users']
                        self.data_set_saver.save_point(label, (dt, eu))
                    msg = msg.format(data['exported_users'],
                                     data['exported_mails'],
                                     data['total_mails'],
                                     mem_info[key])
                    exported_grand_total += data['exported_mails']
                    exported_grand_total += data['total_mails']
                    self.screen.addstr(2 + i, 50, msg)
                    i = i + 1
                    msg = 'Last amqp update: {}'.format(data['latest_update'])
                    self.screen.addstr(2 + i, 50, msg)
                    self.screen.clrtoeol()
                except KeyError:
                    self.screen.addstr(2 + i, 50, str(data))
                    i = i + 1
                    self.screen.addstr(2 + i, 50, str(mem_info))
                i = i + 2
            self.screen.refresh()

            if self.log_data:
                dt = (time.time() - self.start_time)
                label = 'Total Mails'
                self.data_set_saver.save_point(label,
                                               (dt, exported_grand_total))

            
            key = self.screen.getch()
            if key == ord('q'):
                # Quit program
                pass
            time.sleep(1)

        curses.nocbreak()
        self.screen.keypad(0)
        curses.echo()
        curses.endwin()
