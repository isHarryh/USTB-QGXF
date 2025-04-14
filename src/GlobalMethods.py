# -*- coding: utf-8 -*-
# Copyright (c) 2024, Harry Huang
# @ MIT License
import builtins
import threading

_PRINT_LOCK = threading.Lock()


def print(obj: object = "", c: int = 7):
    """Prints with colored output.

    :param obj: The object to print;
    :param c: The text color [0=black,1=red,2=green,3=yellow,4=blue,5=purple,6=cyan,7=white];
    :rtype: None;
    """
    with _PRINT_LOCK:
        return builtins.print(f"\033[03{c}m{obj}")


def input(obj: object = "", c: int = 7):
    """Inputs with colored output.

    :param obj: The object to print;
    :param c: The text color [0=black,1=red,2=green,3=yellow,4=blue,5=purple,6=cyan,7=white];
    :rtype: None;
    """
    with _PRINT_LOCK:
        return builtins.input(f"\033[03{c}m{obj}")
