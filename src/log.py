# Built-in modules
import datetime as dt
import sys as sy


class Log:
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
        if not log_level:
            log_level = self._log_level
        self._write(msg)
        if log_level <= self._log_level:
            print(wrmsg),

    def err(self, msg):
        err_msg = self._err_preamble + msg
        self._write(err_msg)
        print(err_msg, file=sy.stderr)
        raise Exception()

    # ***** Private methods *****
    def _write(self, msg):
        self._f.write(self._dt_msg(msg))
        return

    def _dt_msg(self, msg):
        now = dt.datetime.now()
        return ("[%04d-%02d-%02d %02d:%02d:%02d] %s\n" % (
            now.year, now.month, now.day, now.hour,
            now.minute, now.second, msg))
