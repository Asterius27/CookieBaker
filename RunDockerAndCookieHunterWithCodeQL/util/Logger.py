# logger to intercept stdout and write everything in a log file
import os
import sys


class Logger(object):

    def __init__(self, dir_for_logs, token_separator, filename):
        self.terminal = sys.stdout

        if not os.path.exists(dir_for_logs):
            os.makedirs(dir_for_logs)

        self.log = open(f"{dir_for_logs}{token_separator}{filename}.log", "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()

    def flush(self):
        # this flush method is needed for python 3 compatibility.
        # this handles the flush command by doing nothing.
        # you might want to specify some extra behavior here.
        pass
