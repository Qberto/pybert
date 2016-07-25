__author__ = 'Alberto Nieto'
__version__ = "0.0.1"

import datetime
import arcpy
import os
import sys

# # overwrites and resets timestamp an exiting log
# def ResetLog(task):
#     # None suppresses logging
#     #TODO: refactor with LogLevels
#     if self._log_path is None:
#         return
#     log = open(self._log_path, 'w')
#     dt = datetime.datetime.now().strftime("%m-%d-%y > %I:%M:%S %p")
#     msg = "{0} >>> BEGIN: {1}{2}{3}{4}".format(dt, task, os.linesep, os.linesep, os.linesep)
#     log.write(msg)
#     log.close()
#     #logs a message of the appropriate type to the class process log
#
#
# def LogMessage(message, type):
#     # None suppresses logging
#     #TODO: refactor with LogLevels e.g. ERROR, WARNING, INFO, DEBUG
#     if self._log_path is None:
#         return
#     dt = datetime.datetime.now().strftime("%m-%d-%y  %I:%M:%S %p")
#     log = open(self._log_path, 'a')
#     msg = "{0:<8} {1:>18}:  {2}{3}".format(dt, type, message, os.linesep)
#     pymsg = "{0:<10} {1}".format(dt, message)
#     log.write(msg)
#     log.close()
#     if type == "INFO":
#         arcpy.AddMessage(pymsg)
#     elif type == "WARNING":
#         arcpy.AddWarning(pymsg)
#     elif type == "ERROR":
#         arcpy.AddError(pymsg)


def get_user():
    """Returns as a string the Login ID of the User on the Host System"""
    from getpass import getuser
    # Get the login ID of the current user and convert the characters to lowercase
    user = getuser().lower()
    # Return the value held in the 'User' variable
    return user


def check_for_arcgis_python():
    allowable_python_executables = [r"C:\Python27\ArcGISx6410.3\python.exe",
                                    r"C:\Python27\ArcGIS10.3\python.exe",
                                    r"C:\Python27\ArcGISx6410.4\python.exe",
                                    r"C:\Python27\ArcGIS10.4\python.exe",]
    anaconda_python = r"C:\Users\{0}\AppData\Local\Continuum\Anaconda\python.exe".format(get_user())
    if sys.executable.upper() in [x.upper() for x in allowable_python_executables]:
        print("Python being executed from ArcGIS' 64-bit python.")
        return True
    elif sys.executable.upper() == anaconda_python.upper():
        print("Python being executed from Anacondas' python.")
        return False
    else:
        print("Python being executed from an unknown executable.")
        return False


def get_valid_response(prompt, valid_response_options):
    """
    Asks the user to type in a response to a prompt question, accepting only specified response options
    :param prompt:
    :param valid_response_options:
    :return:
    """
    while True:
        try:
            input_value = raw_input(prompt)

            if input_value not in valid_response_options:
                print("Sorry, I didn't understand that.")
                print("Please enter a valid option: {0}".format(valid_response_options))
                continue

            else:
                return input_value

        except ValueError as e:
            print e
            print e.message
            print("Sorry, I didn't understand that.")
            print("Please enter a valid option: {0}".format(valid_response_options))


def concat_two_csvs(csv_one,
                    csv_two,
                    output_dir,
                    output_name,
                    check_for_unnamed_fields=False):
    """
    Concatenates two csvs
    :param csv_one:
    :param csv_two:
    :param output_dir:
    :param output_name:
    :param check_for_unnamed_fields:
    :return: Output concatenated csv
    """
    import pandas as pd
    import os.path

    method_message = "\t\t\tconcat_two_csvs: "

    print("{0}Concatenating csvs...".format(method_message),
          "INFO")
    a = pd.read_csv(csv_one, index_col=None, header=0)
    b = pd.read_csv(csv_two, index_col=None, header=0)
    list_ = [a, b]
    df = pd.concat(list_)
    print("{0}Checking for unnamed fields...".format(method_message),
          "INFO")
    if check_for_unnamed_fields:
        if "Unnamed: 0" in df.columns:
            print('{0}"Unnamed: 0" field found. Removing...'.format(method_message),
                  "INFO")
            df.drop("Unnamed: 0", axis=1, inplace=True)
        else:
            print('{0}"No unnamed fields found.'.format(method_message),
                  "INFO")
    output_csv = "{0}\\{1}".format(output_dir, output_name)
    if os.path.isfile(output_csv):
        print("{0}Pre-existing output csv found. Removing...".format(method_message),
              "INFO")
        os.remove(output_csv)
    df.to_csv(output_csv)
    return output_csv


def return_valid_windows_characters(data_string):
    """
    Given an input data string, returns valid windows characters
    :param data_string: string to be converted
    :return: valid data string
    """
    import string

    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    ''.join(c for c in data_string if c in valid_chars)
    return str(data_string)


def int_with_commas(x):
    """
    Reads an integer value and reformats the characters to include commas in the thousand character space
    :param x: Integer value to be formatted into integer with commas
    """
    if type(x) not in [type(0), type(0L)]:
        raise TypeError("Parameter must be an integer.")
    if x < 0:
        return '-' + int_with_commas(-x)
    result = ''
    while x >= 1000:
        x, r = divmod(x, 1000)
        result = ",%03d%s" % (r, result)
    return "%d%s" % (x, result)


def get_median(value_list):
    """
    Given a list of numeric values, returns the median
    :param value_list:
    :return: Median value from the input value list
    """
    sorted_list = sorted(value_list)
    median = int(round(len(sorted_list) / 2))
    if len(sorted_list) % 2 == 0:
        med_val = float(sorted_list[median - 1]
                        + sorted_list[median]) / 2
    else:
        med_val = sorted_list[median]
    return med_val


def formatTime(x):
    minutes, seconds_rem = divmod(x, 60)
    if minutes >= 60:
        hours, minutes_rem = divmod(minutes, 60)
        return "%02d:%02d:%02d" % (hours, minutes_rem, seconds_rem)
    else:
        minutes, seconds_rem = divmod(x, 60)
        return "00:%02d:%02d" % (minutes, seconds_rem)


# Logging utility - reset log
def ResetLog(log_path, task):
    import datetime
    import os
    # log_path = None suppresses logging
    if log_path is None:
        return
    log = open(log_path, 'w')
    dt = datetime.datetime.now().strftime("%m-%d-%y > %I:%M:%S %p")
    msg = "{0} >>> BEGIN: {1}{2}{3}{4}".format(dt, task, os.linesep, os.linesep, os.linesep)
    log.write(msg)
    log.close()
    #logs a message of the appropriate type to the class process log


# Logging utility - log message
def LogMessage(log_path, message, type, timestamp=True):
    import datetime
    import os
    import arcpy
    # log_path = None suppresses logging
    if log_path is None:
        return
    dt = datetime.datetime.now().strftime("%m-%d-%y  %I:%M:%S %p")
    log = open(log_path, 'a')
    if timestamp:
        msg = "{0:<8} {1:>18}:  {2}{3}".format(dt, type, message, os.linesep)
    else:
        msg = "{2}{3}".format(dt, type, message, os.linesep)
    pymsg = "{0:<10} {1}".format(dt, message)
    log.write(msg)
    log.close()
    if type == "INFO":
        arcpy.AddMessage(pymsg)
    elif type == "WARNING":
        arcpy.AddWarning(pymsg)
    elif type == "ERROR":
        arcpy.AddError(pymsg)


# Class allowing dictionary diff operations
class DictDiffer(object):
    """
    Calculate the difference between two dictionaries as:
    (1) items added
    (2) items removed
    (3) keys same in both but changed values
    (4) keys same in both and unchanged values
    """

    def __init__(self, current_dict, past_dict):
        self.current_dict, self.past_dict = current_dict, past_dict
        self.set_current, self.set_past = set(current_dict.keys()), set(past_dict.keys())
        self.intersect = self.set_current.intersection(self.set_past)

    def added(self):
        return self.set_current - self.intersect

    def removed(self):
        return self.set_past - self.intersect

    def changed(self):
        return set(o for o in self.intersect if self.past_dict[o] != self.current_dict[o])

    def unchanged(self):
        return set(o for o in self.intersect if self.past_dict[o] == self.current_dict[o])