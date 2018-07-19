import logging


def init_logger(name, scanner, logginglevel):
    logger = logging.Logger(name)
    fh = logging.FileHandler(scanner.scan_object.scan_log_file)
    fh.setLevel(logginglevel)
    logger.addHandler(fh)
    return logger
