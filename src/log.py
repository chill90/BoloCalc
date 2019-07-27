# Built-in modules
import datetime as dt


class Log:
    """
    Log object writes logging information to a file and to stdout

    Args:
    log_file (str): logging file
    log_level (int): how much logging info to print to stdout.
    0 - 2, with 0 being the most info and 2 being the least

    Attributes:
    level (dict): possible logging levels -- 'CRUCIAL', 'MODERATE', 'NOTIFY'
    """
    def __init__(self, log_file, log_level=1):
        # Log leveling
        if log_level is None:
            self._log_level = 0
        elif log_level > 2:
            self._log_level = 2
        elif log_level < 0:
            self._log_level = 0
        else:
            self._log_level = log_level
        # Log level enums
        self.level = {"CRUCIAL": 0,
                      "MODERATE": 1,
                      "NOTIFY": 2}
        # Open log file
        self._log_file = log_file
        self._f = open(self._log_file, 'w')
        self.log(
            "Logging to file '%s,' printing with verbosity = %d"
            % (self._log_file, self._log_level),
            self.level["MODERATE"])
        # Error preamble
        self._err_preamble = "BoloCalc Error: "
        return

    def __del__(self):
        self._f.close()
        return

    # ***** Public methods *****
    def log(self, msg, log_level=None):
        """
        Log a message

        Args:
        msg (str): message to log
        log_level (int): level at which to log, 0-2
        """
        if not log_level:
            log_level = self._log_level
        self._write(msg)
        if log_level <= self._log_level:
            print(msg),

    def err(self, msg):
        """
        Report an error and raise a BoloCalc exception

        Args:
        msg (str): error message
        """
        err_msg = self._err_preamble + msg
        self._write(err_msg)
        raise Exception(err_msg)

    # ***** Private methods *****
    def _write(self, msg):
        """ Write message to log file """
        self._f.write(self._dt_msg(msg))
        return

    def _dt_msg(self, msg):
        """ Append datetime to message """
        now = dt.datetime.now()
        return ("[%04d-%02d-%02d %02d:%02d:%02d] %s\n" % (
            now.year, now.month, now.day, now.hour,
            now.minute, now.second, msg))
