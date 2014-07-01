from queued import QueuedProcessor
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

    def convert(self, item, tmp_dir):
        return_code = subprocess.call([
                            "libreoffice", "--headless", "--convert-to", "htm:HTML",
                            item.file_path, "--outdir", tmp_dir
                        ], env=self.env)
        return return_code == 0
