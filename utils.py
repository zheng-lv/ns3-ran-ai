#! /usr/bin/env python3

# These methods are used by test.py and waf to look for and read the .ns3rc configuration file, which is used to specify the modules that should be enabled
# Py 和 waf 使用这些方法查找和读取.Ns3rc 配置文件，用于指定应该启用的模块
# 

import os
import sys

def get_list_from_file(file_path, list_name):
    '''Looks for a Python list called list_name in the file specified by file_path and returns it.
    在 file _ path 指定的文件中查找名为 list _ name 的 Python 列表并返回它。

    If the file or list name aren't found, this function will return an empty list.
    如果找不到文件或列表名称，此函数将返回空列表。

    '''

    list = []

    # Read in the file if it exists.如果文件存在，则读入该文件。
    if os.path.exists(file_path):
        file_in = open(file_path, "r")

        # Look for the list.去找名单。
        list_string = ""
        parsing_multiline_list = False
        for line in file_in:

            # Remove any comments.删除任何评论。
            if '#' in line:
                (line, comment) = line.split('#', 1)

            # Parse the line.解析这句话。
            if list_name in line or parsing_multiline_list:
                list_string += line

                # Handle multiline lists.处理多行列表。
                if ']' not in list_string:
                    parsing_multiline_list = True
                else:
                    # Evaluate the list once its end is reached.一旦到达列表的末尾，就对其进行评估。
                    # Make the split function only split it once.使分割函数只分割它一次。
                    list = eval(list_string.split('=', 1)[1].strip())
                    break

        # Close the file
        file_in.close()

    return list


def get_bool_from_file(file_path, bool_name, value_if_missing):
    '''Looks for a Python boolean variable called bool_name in the file specified by file_path and returns its value.
    在 file _ path 指定的文件中查找名为 bool _ name 的 Python 布尔变量并返回其值。

    If the file or boolean variable aren't found, this function will return value_if_missing.
    如果找不到文件或布尔变量，此函数将返回 value _ If _ miss。

    '''

    # Read in the file if it exists.
    if os.path.exists(file_path):
        file_in = open(file_path, "r")

        # Look for the boolean variable.
        bool_found = False
        for line in file_in:

            # Remove any comments.
            if '#' in line:
                (line, comment) = line.split('#', 1)

            # Parse the line.
            if bool_name in line:
                # Evaluate the variable's line once it is found.  Make
                # the split function only split it once.
                bool = eval(line.split('=', 1)[1].strip())
                bool_found = True
                break

        # Close the file
        file_in.close()

    if bool_found:
        return bool
    else:
        return value_if_missing


# Reads the NS-3 configuration file and returns a list of enabled modules.
# 读取 NS-3配置文件并返回已启用模块的列表。
# This function first looks for the ns3 configuration file (.ns3rc) in the current working directory and then looks in the ~ directory.
# 该函数首先查找 ns3配置文件(。Ns3rc)的工作目录，然后查看 ~ 目录。
def read_config_file():
    # By default, all modules will be enabled, examples will be disabled,and tests will be disabled.
    # 默认情况下，将启用所有模块，禁用示例，并禁用测试。
    modules_enabled  = ['all_modules']
    examples_enabled = False
    tests_enabled    = False

    # See if the ns3 configuration file exists in the current working directory and then look for it in the ~ directory.
    # 查看当前工作目录中是否存在 ns3配置文件，然后在 ~ 目录中查找。
    config_file_exists = False
    dot_ns3rc_name = '.ns3rc'
    dot_ns3rc_path = dot_ns3rc_name
    if not os.path.exists(dot_ns3rc_path):
        dot_ns3rc_path = os.path.expanduser('~/') + dot_ns3rc_name
        if not os.path.exists(dot_ns3rc_path):
            # Return all of the default values if the .ns3rc file can't be found.如果找不到. ns3rc 文件，则返回所有默认值。
            return (config_file_exists, modules_enabled, examples_enabled, tests_enabled)

    config_file_exists = True

    # Read in the enabled modules.
    modules_enabled = get_list_from_file(dot_ns3rc_path, 'modules_enabled')
    if not modules_enabled:
        # Enable all modules if the modules_enabled line can't be found.
        modules_enabled = ['all_modules']

    # Read in whether examples should be enabled or not.阅读是否应该启用示例。
    value_if_missing = False
    examples_enabled = get_bool_from_file(dot_ns3rc_path, 'examples_enabled', value_if_missing)

    # Read in whether tests should be enabled or not.阅读是否应该启用测试。
    value_if_missing = False
    tests_enabled = get_bool_from_file(dot_ns3rc_path, 'tests_enabled', value_if_missing)

    return (config_file_exists, modules_enabled, examples_enabled, tests_enabled)

