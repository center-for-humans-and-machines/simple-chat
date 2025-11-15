import logging


# ANSI escape codes for colors
class LogColors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[32;1m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


# Custom formatter
class CustomFormatter(logging.Formatter):
    format_string = "%(asctime)s - %(levelname)s - %(message)s"

    format_dict = {
        logging.DEBUG: LogColors.OKBLUE + format_string + LogColors.ENDC,
        logging.INFO: LogColors.OKGREEN + format_string + LogColors.ENDC,
        logging.WARNING: LogColors.WARNING + format_string + LogColors.ENDC,
        logging.ERROR: LogColors.FAIL + format_string + LogColors.ENDC,
        logging.CRITICAL: LogColors.BOLD
        + LogColors.FAIL
        + format_string
        + LogColors.ENDC,
    }

    def __init__(self, datefmt="%Y-%m-%d %H:%M:%S"):
        logging.Formatter.__init__(self, self.format_string, datefmt)

    def format(self, record):
        self._style._fmt = self.format_dict.get(record.levelno, self.format_string)
        return logging.Formatter.format(self, record)


# Custom logger class
class CustomLogger(logging.Logger):
    def __init__(self, name, level=logging.NOTSET):
        super().__init__(name, level)
        formatter = CustomFormatter()
        # Console handler
        import sys

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        ch.setFormatter(formatter)
        self.addHandler(ch)
        # File handler
        fh = logging.FileHandler("logs.txt")
        fh.setLevel(level)
        fh.setFormatter(formatter)
        self.addHandler(fh)

    def _log_with_title(
        self,
        level,
        msg,
        title=None,
        args=None,
        exc_info=None,
        extra=None,
        stack_info=False,
    ):
        # Construct the message with the title if provided
        if title:
            msg = f"{title}: {msg}"
        # Use str.format for safer and more flexible formatting
        if args:
            try:
                msg = msg.format(*args)
            except TypeError as e:
                # Handle formatting errors
                self._log(logging.ERROR, f"Logging formatting error: {e}", ())
                msg = f"{msg} [Formatting Error: Arguments mismatch]"
        # Call the original logging method
        super()._log(level, msg, (), exc_info, extra, stack_info)

    def debug(self, msg, title=None, *args, **kwargs):
        self._log_with_title(logging.DEBUG, msg, title, args, kwargs)

    def info(self, msg, title=None, *args, **kwargs):
        self._log_with_title(logging.INFO, msg, title, args, kwargs)

    def warning(self, msg, title=None, *args, **kwargs):
        self._log_with_title(logging.WARNING, msg, title, args, kwargs)

    def error(self, msg, title=None, *args, **kwargs):
        self._log_with_title(logging.ERROR, msg, title, args, kwargs)

    def critical(self, msg, title=None, *args, **kwargs):
        self._log_with_title(logging.CRITICAL, msg, title, args, kwargs)

    def log(self, level, msg, title=None, *args, **kwargs):
        if title:
            msg = f"{LogColors.HEADER}{title}{LogColors.ENDC}: {msg}"
        super().log(level, msg, *args, **kwargs)


# Function to setup custom logger
def setup_logger(name, level=logging.DEBUG):
    logging.setLoggerClass(CustomLogger)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger
