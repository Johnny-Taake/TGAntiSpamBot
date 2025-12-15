import logging
import colorama

colorama.init()


class ColoredFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": colorama.Fore.CYAN,
        "INFO": colorama.Fore.GREEN,
        "WARNING": colorama.Fore.YELLOW,
        "ERROR": colorama.Fore.RED,
        "CRITICAL": colorama.Fore.MAGENTA,
    }

    def __init__(
        self, fmt=None, datefmt=None, style="%", validate=True, use_color=True
    ):
        super().__init__(fmt, datefmt, style, validate)
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        original_levelname = record.levelname
        try:
            if self.use_color:
                color = self.COLORS.get(original_levelname)
                if color:
                    record.levelname = (
                        f"{color}{original_levelname}{colorama.Style.RESET_ALL}"
                    )
            return super().format(record)
        finally:
            record.levelname = original_levelname
