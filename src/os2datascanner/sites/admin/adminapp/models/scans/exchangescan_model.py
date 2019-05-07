from .scan_model import Scan


class ExchangeScan(Scan):
    """An actual instance of the exchange scanning process done by a exchange scanner."""
    def __init__(self, *args, **kwargs):
        """Initialize a new scan.

        Stores the old status of the scan for later use.
        """
        super().__init__(*args, **kwargs)
        self._old_status = self.status

