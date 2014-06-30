from queued import QueuedProcessor
import time
import os
import os.path
import subprocess

base_dir = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '..', '..', '..'
)
var_dir = os.path.join(base_dir, "var")
lo_dir = os.path.join(var_dir, "libreoffice")
home_root_dir = os.path.join(lo_dir, "homedirs")

class LibreOfficeProcessor(QueuedProcessor):
    item_type = "libreoffice"

    def __init__(self, instance_name):
        super(LibreOfficeProcessor, self).__init__("libreoffice")

        if not instance_name:
            raise "You must specify an instance name"

        self.home_dir = os.path.join(home_root_dir, instance_name);

        if not os.path.exists(self.home_dir):
            os.makedirs(self.home_dir)

        self.env = os.environ.copy()
        self.env['HOME'] = self.home_dir

        self.lock_file = os.path.join(self.home_dir, "running.lock")

    def run(self):
        keep_running = True

        # TODO: Need a locking mechanism to ensure we're not running multiple
        # instances:
        #
        #if(os.path.exists(self.lock_file)):
        #    raise "Lockfile '" + self.lock_file + "' exists, will not run"
        #
        #f = open(self.lock_file, 'a').close();
        #f.write(os.getpid())
        #f.close()

        while keep_running:
            item = self.get_next_item()
            if item is None:
                print "Sleeping..."
                time.sleep(1)
            else:
                scan_id = item.url.scan.pk
                tmp_dir = os.path.join(
                    var_dir,
                    'scan_%d' % (scan_id),
                    'queue_item_%d' % (item.pk)
                )
                if not os.path.exists(tmp_dir):
                    os.makedirs(tmp_dir)

                # TODO: Input type to filter mapping?
                subprocess.call([
                    "libreoffice", "--convert-to", "htm:HTML",
                    item.file, "--outdir", tmp_dir
                ], env=self.env)

                self.add_processed_files(tmp_dir)
