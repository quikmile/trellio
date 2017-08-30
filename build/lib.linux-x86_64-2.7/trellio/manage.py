#!/usr/bin/python
import sys

from .management.core import execute_from_command_line

if __name__ == '__main__':
    execute_from_command_line(sys.argv)
