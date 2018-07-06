import time
import logging
import subprocess
import multiprocessing
import psutil
import settings

logger = logging.getLogger('Mailscan_exchange')


class Stats(multiprocessing.Process):
    def __init__(self, user_queue):
        multiprocessing.Process.__init__(self)
        self.user_queue = user_queue
        self.scanners = []
        # Measure initial values while we have the chance
        self.start_time = time.time()
        self.total_users = self.user_queue.qsize()
        self.init_du = self.disk_usage()

    def number_of_threads(self):
        """ Number of threads
        :return: Tuple with Number of threads, and nuber of active threads
        """
        return (len(self.scanners), len(multiprocessing.active_children()))

    def add_scanner(self, scanner):
        """ Add a scanner to the internal list of scanners
        :param scanner: The scanner object to be added
        :return: The new number of threads
        """
        self.scanners.append(scanner)
        return self.number_of_threads()

    def disk_usage(self):
        """ Return the current disk usage
        :return: Disk usage in MB
        """
        error = True
        while error:
            try:
                du_output = subprocess.check_output(['du', '-s',
                                                     settings.export_path])
                error = False
            except subprocess.CalledProcessError:
                # Happens if du is called while folder is being marked done
                logger.warn('du-error')
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
        mem_list = []
        for scanner in self.scanners:
            pid = scanner.pid
            process = psutil.Process(pid)
            mem_info = process.memory_full_info()
            used_memory = mem_info.uss/1024**2
            mem_list.append(used_memory)
        return mem_list

    def status(self):
        template = ('Threads: {}. ' +
                    'Queue: {}. ' +
                    'Export: {:.3f}GB. ' +
                    'Time: {:.2f}min. ' +
                    'Speed: {:.2f}MB/s. ' +
                    'Memory consumption: {:.3f}GB. ' +
                    'Scanned users: {} / {}')
        memory = sum(self.memory_info()) / 1024
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

    def run(self):
        processes = self.number_of_threads()[1]
        while processes > 0:
            time.sleep(30)
            status = self.status()
            print(status)
            logger.info(status)
