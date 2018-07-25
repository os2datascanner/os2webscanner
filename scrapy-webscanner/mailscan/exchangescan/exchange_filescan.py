"""
Demands:
* starter når den første _done folder er markeret
* hvis filscan indhenter exchange download skal filscan vente indtil en ny folder er markeret med _done.
* Når alt exchange indhold er downloadet skal filscan vide at der ikke er mere indhold at scanne.
"""
import time
import queue
import multiprocessing


class Test(multiprocessing.Process):
    def __init__(self, q):
        multiprocessing.Process.__init__(self)
        self.q = q

    def run(self):
        for j in range(0, 10):
            self.q.put('something {}'.format(j))
            print('Putting something in queue.')
            time.sleep(2)


def main():
    print('Program started')
    q = multiprocessing.Queue()

    scanners = {}
    for i in range(0, 2):
        scanners[i] = Test(q)
        scanners[i].start()
        print('Started scanner {}'.format(i))
        time.sleep(1)

    print('Scanners started...')

    for key, value in scanners.items():
        get_queue_item(q)

        while value.is_alive():
            print('Process with pid {} is still alive'.format(value.pid))
            get_queue_item(q)
            time.sleep(1)

# TODO: læg user elementer i en python list og tjek tilsidst eller løbende at alle users er scannet.


def get_queue_item(q):
    item = q.get()
    while item is not None:
        print('Getting item from q: {}'.format(item))
        try:
            item = q.get(True, 1)
        except queue.Empty:
            print('Queue is empty')
            item = None


main()
