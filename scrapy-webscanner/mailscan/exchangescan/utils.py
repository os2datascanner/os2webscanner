import logging


def init_logger(name, scan_object, logginglevel):
    logger = logging.Logger(name)
    fh = logging.FileHandler(scan_object.scan_log_file)
    fh.setLevel(logginglevel)
    logger.addHandler(fh)
    return logger
