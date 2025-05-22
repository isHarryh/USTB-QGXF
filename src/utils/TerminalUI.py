# -*- coding: utf-8 -*-
# Copyright (c) 2024, Harry Huang
# @ MIT License
import sys
from threading import Condition, Thread
from typing import Any, Callable, Iterable, List, Optional, overload, TextIO, Union


ContentSequence = Iterable[Union[str, tuple[str, int]]]

_ANSI = "\x1b"
_ANSI_CLEAR = f"{_ANSI}[2J"
_ANSI_ERASE = f"{_ANSI}[J"
_ANSI_HOME = f"{_ANSI}[H"
_ANSI_NOCOLOR = f"{_ANSI}[0m"
_ANSI_RESET = f"{_ANSI}c"


class ObservableLine:
    def __init__(
        self,
        initial_content: Optional[ContentSequence] = None,
        on_change: Optional[Callable[[], Any]] = None,
    ):
        self._content = [] if initial_content is None else list(initial_content)
        self._on_change = (lambda: None) if on_change is None else on_change
        self._changed = True
        self._last_read = ""

    def read(self) -> str:
        """Reads the complete string of this line."""
        full = ""
        for item in self._content:
            if isinstance(item, str):
                full += item
            elif isinstance(item, Iterable):
                text, color = item
                full += f"{_ANSI}[{30 + color}m{text}{_ANSI_NOCOLOR}"
            else:
                raise TypeError("Each content must be str or tuple")

        self._changed = False
        self._last_read = full
        return full

    @overload
    def write(self, content: ContentSequence, append: bool = False): ...

    @overload
    def write(self, string: str, color: int, append: bool = False): ...

    def write(self, *args, append: bool = False):  # type: ignore
        """Writes new content to this line."""
        if len(args) == 0:
            content = []
        elif len(args) == 1:
            content = list(args[0])
        elif len(args) == 2:
            content = [(args[0], args[1])]
        else:
            raise TypeError("Unknown overloading parameters")

        if append:
            self._content.extend(content)
        else:
            self._content = content
        self._changed = True
        self._on_change()

    @property
    def changed(self) -> bool:
        """The indicator shows whether this line has changed since the last read."""
        return self._changed

    @property
    def last_read(self) -> str:
        """The result of the last `read()` call."""
        return self._last_read


class TerminalUI:
    def __init__(self, target: TextIO = sys.stdout):
        self.target = target
        self.lines: List[ObservableLine] = []

        self._condition = Condition()
        self._print_requested = False
        self._last_lines_len = 0

        self._running = True
        self._thread = Thread(target=self._loop, name="TerminalUI", daemon=True)
        self._thread.start()

        self._request_print()

    @overload
    def add_line(self) -> ObservableLine: ...

    @overload
    def add_line(self, content: ContentSequence) -> ObservableLine: ...

    @overload
    def add_line(self, string: str, color: int) -> ObservableLine: ...

    def add_line(self, *args) -> ObservableLine:  # type: ignore
        """Adds a new line to TUI, returns the line's instance for manipulation."""
        if len(args) == 0:
            content = []
        elif len(args) == 1:
            content = list(args[0])
        elif len(args) == 2:
            content = [(args[0], args[1])]
        else:
            raise TypeError("Unknown overloading parameters")
        with self._condition:
            line = ObservableLine(content, self._request_print)
            self.lines.append(line)
            self._request_print()
            return line

    def remove_line(self, line: ObservableLine):
        """Removes the given line from TUI."""
        with self._condition:
            if line in self.lines:
                index = self.lines.index(line)
                del self.lines[index]
                self._request_print()

    def remove_all_lines(self):
        """Removes all lines in TUI."""
        with self._condition:
            self.lines.clear()
            self._request_print()

    def dispose(self):
        """Disposes TUI thread."""
        self._running = False
        with self._condition:
            self._condition.notify_all()
        self._thread.join()

    def _loop(self):
        while self._running:
            with self._condition:
                while not self._print_requested and self._running:
                    self._condition.wait()
                if not self._running:
                    break

            self._print_requested = False
            self._print()

    def _print(self):
        with self._condition:
            output_lines = []
            for idx, line in enumerate(self.lines):
                line_str = line.read()
                output_lines.append(line_str)
            full = "\n".join(output_lines)
            full = f"{_ANSI_RESET}{_ANSI_CLEAR}{_ANSI_HOME}{full}{_ANSI_ERASE}"

            self.target.write(full)
            self.target.flush()

    def _request_print(self):
        with self._condition:
            self._print_requested = True
            self._condition.notify()


STDOUT = TerminalUI()

# Test
if __name__ == "__main__":
    import time

    line1 = STDOUT.add_line([("Status: ", 3), ("Processing", 6)])
    time.sleep(1)

    for _ in range(3):
        line1.write(["."], append=True)
        time.sleep(0.1)

    line2 = STDOUT.add_line(["Progress: ", ("Started", 4)])
    time.sleep(1)

    line3 = STDOUT.add_line(["Progress: ", ("Started", 4)])
    time.sleep(1)

    for i in range(20):
        line2.write(["Progress: ", ("#" * i, 4)])
        time.sleep(0.02)
        line3.write(["Progress: ", ("#" * i, 4)])
        time.sleep(0.02)

    line1.write([("Status: ", 3), ("Done", 2)])
    time.sleep(1)

    STDOUT.remove_line(line1)
    time.sleep(1)

    STDOUT.remove_all_lines()
    STDOUT.dispose()
