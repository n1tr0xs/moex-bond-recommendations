from enum import Enum
import datetime


class Log:
    class CATEGORY(Enum):
        INFO = 0, "[INFO]"
        WARNING = 1, "[WARNING]"
        ERROR = 2, "[ERROR]"

    def __init__(self):
        self.file_name: str = datetime.datetime.now().strftime("%Y-%m-%d") + ".txt"
        self._logs: list[str] = []

    def info(self, message: str) -> None:
        """
        Logs info message.
        """
        self._log(self.CATEGORY.INFO, message)

    def error(self, message: str) -> None:
        """
        Logs error message.
        """
        self._log(self.CATEGORY.ERROR, message)

    def warning(self, message: str) -> None:
        """
        Logs warning message.
        """
        self._log(self.CATEGORY.WARNING, message)

    def save_to_file(self) -> None:
        """
        Saves all logged messages to file.
        """
        with open(self.file_name, "w", encoding="utf-8") as fout:
            for line in self._logs:
                fout.write(line)

    def _log(self, category: "Log.CATEGORY", message: str) -> None:
        # output = " ".join((category.value[1], message))
        # counting newlines
        newlines_count: int = 0
        for i in range(len(message)):
            if message[i] == "\n":
                newlines_count += 1
            else:
                break

        # constructing output message
        output: str = (
            newlines_count * "\n" + category.value[1] + " " + message[newlines_count:]
        )

        print(output)
        self._logs.append(output)