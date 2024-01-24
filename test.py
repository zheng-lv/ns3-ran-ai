#! /usr/bin/env python3
## -*- Mode: python; py-indent-offset: 4; indent-tabs-mode: nil; coding: utf-8; -*-
#
# Copyright (c) 2009 University of Washington
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation;
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
import os
import sys
import time
import optparse
import subprocess
import threading
import signal
import xml.dom.minidom
import shutil
import fnmatch

from utils import get_list_from_file

# imported from waflib Logs colors_lst 字典包含了一些颜色常量和对应的控制字符串，用于在输出中设置文本的颜色和样式。
colors_lst={'USE':True,'BOLD':'\x1b[01;1m','RED':'\x1b[01;31m','GREEN':'\x1b[32m','YELLOW':'\x1b[33m','PINK':'\x1b[35m','BLUE':'\x1b[01;34m','CYAN':'\x1b[36m','GREY':'\x1b[37m','NORMAL':'\x1b[0m','cursor_on':'\x1b[?25h','cursor_off':'\x1b[?25l',}
'''get_color(cl) 函数接受一个颜色常量作为参数，并根据 colors_lst 字典返回对应的颜色控制字符串。如果 USE 键的值为 True，则会根据给定的颜色常量返回相应的控制字符串；否则，返回空字符串。'''
def get_color(cl):
    if colors_lst['USE']:
        return colors_lst.get(cl,'')
    return''
'''color_dict 类通过 __getattr__ 和 __call__ 方法实现了动态获取和调用 get_color 函数的功能。可以通过访问 color_dict 对象的属性或调用它来获取颜色控制字符串。'''
class color_dict(object):
    def __getattr__(self,a):
        return get_color(a)
    def __call__(self,a):
        return get_color(a)
colors=color_dict()
'''最后，代码尝试导入 queue 模块，但如果导入失败，会尝试导入 Queue 模块作为替代。'''
try:
    import queue
except ImportError:
    import Queue as queue
#
# XXX This should really be part of a waf command to list the configuration
# items relative to optional ns-3 pieces.
#
# A list of interesting configuration items in the waf configuration
# cache which we may be interested in when deciding on which examples
# to run and how to run them.  These are set by waf during the
# configuration phase and the corresponding assignments are usually
# found in the associated subdirectory wscript files.
#
# XXX 这应该是列出配置的 waf 命令的一部分项目相对于可选的 ns-3件。
# waf 配置中有趣的配置项列表缓存，我们可能会感兴趣的时候决定哪些例子
# 以及如何运行它们配置阶段和相应的分配通常是
# 在相关的子目录 wscript 文件中找到。
interesting_config_items = [
    "NS3_ENABLED_MODULES",
    "NS3_ENABLED_CONTRIBUTED_MODULES",
    "NS3_MODULE_PATH",
    "NSC_ENABLED",
    "ENABLE_REAL_TIME",
    "ENABLE_THREADING",
    "ENABLE_EXAMPLES",
    "ENABLE_TESTS",
    "EXAMPLE_DIRECTORIES",
    "ENABLE_PYTHON_BINDINGS",
    "NSCLICK",
    "ENABLE_BRITE",
    "ENABLE_OPENFLOW",
    "APPNAME",
    "BUILD_PROFILE",
    "VERSION",
    "PYTHON",
    "VALGRIND_FOUND",
]

NSC_ENABLED = False
ENABLE_REAL_TIME = False
ENABLE_THREADING = False
ENABLE_EXAMPLES = True
ENABLE_TESTS = True
NSCLICK = False
ENABLE_BRITE = False
ENABLE_OPENFLOW = False
EXAMPLE_DIRECTORIES = []
APPNAME = ""
BUILD_PROFILE = ""
BUILD_PROFILE_SUFFIX = ""
VERSION = ""
PYTHON = ""
VALGRIND_FOUND = True

#
# This will be given a prefix and a suffix when the waf config file is read.
#当读取 waf 配置文件时，将给它一个前缀和一个后缀。
test_runner_name = "test-runner"

#如果用户强制我们运行某些类型的测试，我们可以告诉 waf 只构建
# If the user has constrained us to run certain kinds of tests, we can tell waf to only build
#
core_kinds = ["core", "performance", "system", "unit"]

#对于测试套件来说，有一些特殊的情况会杀死工具集
# There are some special cases for test suites that kill valgrind.  
# This is because NSC causes illegal instruction crashes when run under valgrind.
#这是因为 NSC 导致非法指令崩溃时，运行在工具集。

core_valgrind_skip_tests = [
    "ns3-tcp-cwnd",
    "nsc-tcp-loss",
    "ns3-tcp-interoperability",
    "routing-click",
    "lte-rr-ff-mac-scheduler",
    "lte-tdmt-ff-mac-scheduler",
    "lte-fdmt-ff-mac-scheduler",
    "lte-pf-ff-mac-scheduler",
    "lte-tta-ff-mac-scheduler",
    "lte-fdbet-ff-mac-scheduler",
    "lte-ttbet-ff-mac-scheduler",
    "lte-fdtbfq-ff-mac-scheduler",
    "lte-tdtbfq-ff-mac-scheduler",
    "lte-pss-ff-mac-scheduler",
]

#
# There are some special cases for test suites that fail when NSC is missing.
# 当 NSC 丢失时，对于失败的测试套件有一些特殊情况。
#
core_nsc_missing_skip_tests = [
    "ns3-tcp-cwnd",
    "nsc-tcp-loss",
    "ns3-tcp-interoperability",
]

#
# Parse the examples-to-run file if it exists.
#
# This function adds any C++ examples or Python examples that are to be run to the lists in example_tests and python_tests, respectively.
# 这个函数将任何 C + + 示例或 Python 示例分别添加到 example _ test 和 Python _ test 中的列表中。
#
def parse_examples_to_run_file(
    examples_to_run_path,
    cpp_executable_dir,
    python_script_dir,
    example_tests,
    example_names_original,
    python_tests):

    # Look for the examples-to-run file exists.查找要运行的示例文件是否存在。
    if os.path.exists(examples_to_run_path):

        # Each tuple in the C++ list of examples to run contains  要运行的 C++ 示例列表中的每个元组都包含
        #
        #     (example_name, do_run, do_valgrind_run)
        # 
        # where example_name is the executable to be run, do_run is a    其中 example_name 是要运行的可执行文件，do_run 是
        # condition under which to run the example, and do_valgrind_run is    运行示例的条件，do_valgrind_run 是
        # a condition under which to run the example under valgrind.  This     在 valgrind 下运行示例的条件。 这
        # is needed because NSC causes illegal instruction crashes with      需要，因为 NSC 会导致非法指令崩溃
        # some tests when they are run under valgrind.                在 valgrind 下运行时的一些测试。
        #
        # Note that the two conditions are Python statements that   请注意，这两个条件是 Python 语句
        # can depend on waf configuration variables.  For example,   可以取决于 waf 配置变量。 例如，
        #
        #     ("tcp-nsc-lfn", "NSC_ENABLED == True", "NSC_ENABLED == False"),
        #
        cpp_examples = get_list_from_file(examples_to_run_path, "cpp_examples")
        for example_name, do_run, do_valgrind_run in cpp_examples:

            # Separate the example name from its arguments.
            example_name_original = example_name
            example_name_parts = example_name.split(' ', 1)
            if len(example_name_parts) == 1:
                example_name      = example_name_parts[0]
                example_arguments = ""
            else:
                example_name      = example_name_parts[0]
                example_arguments = example_name_parts[1]

            # Add the proper prefix and suffix to the example name to
            # match what is done in the wscript file.
            example_path = "%s%s-%s%s" % (APPNAME, VERSION, example_name, BUILD_PROFILE_SUFFIX)

            # Set the full path for the example.
            example_path = os.path.join(cpp_executable_dir, example_path)
            example_name = os.path.join(
                os.path.relpath(cpp_executable_dir, NS3_BUILDDIR),
                example_name)
            # Add all of the C++ examples that were built, i.e. found
            # in the directory, to the list of C++ examples to run.
            if os.path.exists(example_path):
                # Add any arguments to the path.
                if len(example_name_parts) != 1:
                    example_path = "%s %s" % (example_path, example_arguments)
                    example_name = "%s %s" % (example_name, example_arguments)

                # Add this example.
                example_tests.append((example_name, example_path, do_run, do_valgrind_run))
                example_names_original.append(example_name_original)

        # Each tuple in the Python list of examples to run contains
        #
        #     (example_name, do_run)
        #
        # where example_name is the Python script to be run and
        # do_run is a condition under which to run the example.
        #
        # Note that the condition is a Python statement that can
        # depend on waf configuration variables.  For example,
        #
        #     ("realtime-udp-echo.py", "ENABLE_REAL_TIME == True"),
        #
        python_examples = get_list_from_file(examples_to_run_path, "python_examples")
        for example_name, do_run in python_examples:
            # Separate the example name from its arguments.
            example_name_parts = example_name.split(' ', 1)
            if len(example_name_parts) == 1:
                example_name      = example_name_parts[0]
                example_arguments = ""
            else:
                example_name      = example_name_parts[0]
                example_arguments = example_name_parts[1]

            # Set the full path for the example.
            example_path = os.path.join(python_script_dir, example_name)

            # Add all of the Python examples that were found to the
            # list of Python examples to run.
            if os.path.exists(example_path):
                # Add any arguments to the path.
                if len(example_name_parts) != 1:
                    example_path = "%s %s" % (example_path, example_arguments)

                # Add this example.
                python_tests.append((example_path, do_run))

#
# The test suites are going to want to output status.  They are running
# concurrently.  This means that unless we are careful, the output of
# the test suites will be interleaved.  Rather than introducing a lock
# file that could unintentionally start serializing execution, we ask
# the tests to write their output to a temporary directory and then
# put together the final output file when we "join" the test tasks back
# to the main thread.  In addition to this issue, the example programs
# often write lots and lots of trace files which we will just ignore.
# We put all of them into the temp directory as well, so they can be
# easily deleted.
#
TMP_OUTPUT_DIR = "testpy-output"

def read_test(test):
    result = test.find('Result').text
    name = test.find('Name').text
    if not test.find('Reason') is None:
        reason = test.find('Reason').text
    else:
        reason = ''
    if not test.find('Time') is None:
        time_real = test.find('Time').get('real')
    else:
        time_real = ''
    return (result, name, reason, time_real)

#
# A simple example of writing a text file with a test result summary.  It is expected that this output will be fine for developers looking for problems.
# 使用测试结果摘要编写文本文件的简单示例。预计对于寻找问题的开发人员来说，这个输出将是很好的。
#
def node_to_text(test, f, test_type='Suite'):
    (result, name, reason, time_real) = read_test(test)
    if reason:
        reason = " (%s)" % reason

    output = "%s: Test %s \"%s\" (%s)%s\n" % (result, test_type, name, time_real, reason)
    f.write(output)
    for details in test.findall('FailureDetails'):
        f.write("    Details:\n")
        f.write("      Message:   %s\n" % details.find('Message').text)
        f.write("      Condition: %s\n" % details.find('Condition').text)
        f.write("      Actual:    %s\n" % details.find('Actual').text)
        f.write("      Limit:     %s\n" % details.find('Limit').text)
        f.write("      File:      %s\n" % details.find('File').text)
        f.write("      Line:      %s\n" % details.find('Line').text)
    for child in test.findall('Test'):
        node_to_text(child, f, 'Case')

def translate_to_text(results_file, text_file):
    text_file += '.txt'
    print('Writing results to text file \"%s\"...' % text_file, end='')
    f = open(text_file, 'w')
    import xml.etree.ElementTree as ET
    et = ET.parse(results_file)
    for test in et.findall('Test'):
        node_to_text(test, f)

    for example in et.findall('Example'):
        result = example.find('Result').text
        name = example.find('Name').text
        if not example.find('Time') is None:
            time_real = example.find('Time').get('real')
        else:
            time_real = ''
        output = "%s: Example \"%s\" (%s)\n" % (result, name, time_real)
        f.write(output)

    f.close()
    print('done.')

#
# A simple example of writing an HTML file with a test result summary.  使用测试结果摘要编写 HTML 文件的简单示例。
# It is expected that this will eventually be made prettier as time progresses and we have time to tweak it.  预计随着时间的推移，这将最终变得更漂亮，我们有时间来调整它。
# This may end up being moved to a separate module since it will probably grow over time.这可能最终被移动到一个单独的模块，因为它可能会随着时间的推移而增长。
# 
#
def translate_to_html(results_file, html_file):
    html_file += '.html'
    print('Writing results to html file %s...' % html_file, end='')
    f = open(html_file, 'w')
    f.write("<html>\n")
    f.write("<body>\n")
    f.write("<center><h1>ns-3 Test Results</h1></center>\n")

    #
    # Read and parse the whole results file.
    #
    import xml.etree.ElementTree as ET
    et = ET.parse(results_file)

    #
    # Iterate through the test suites 迭代测试套件
    #
    f.write("<h2>Test Suites</h2>\n")
    for suite in et.findall('Test'):
        #
        # For each test suite, get its name, result and execution time info 对于每个测试套件，获取它的名称、结果和执行时间信息
        #
        (result, name, reason, time) = read_test(suite)

        #
        # Print a level three header with the result, name and time.   打印一个包含结果、名称和时间的第三级标题。
        # If the test suite passed, the header is printed in green. 如果测试套件通过，标题将以绿色打印。
        #  If the suite was skipped, print it in orange, otherwise assume something bad happened and print in red.
        # 如果套件被跳过，则将其打印为橙色，否则假设发生了不好的事情，并将其打印为红色。
        #
        if result == "PASS":
            f.write("<h3 style=\"color:green\">%s: %s (%s)</h3>\n" % (result, name, time))
        elif result == "SKIP":
            f.write("<h3 style=\"color:#ff6600\">%s: %s (%s) (%s)</h3>\n" % (result, name, time, reason))
        else:
            f.write("<h3 style=\"color:red\">%s: %s (%s)</h3>\n" % (result, name, time))

        #
        # The test case information goes in a table. 测试用例信息放在一个表中。
        #
        f.write("<table border=\"1\">\n")

        #
        # The first column of the table has the heading Result
        #
        f.write("<th> Result </th>\n")

        #
        # If the suite crashed or is skipped, there is no further information, so just如果套件崩溃或被跳过，没有进一步的信息，所以只需
        # declare a new table row with the result (CRASH or SKIP) in it.  Looks like:   声明一个包含结果(CRASH 或 SKIP)的新表行。
        #
        #   +--------+
        #   | Result |
        #   +--------+
        #   | CRASH  |
        #   +--------+
        #
        # Then go on to the next test suite.  Valgrind and skipped errors look the same.
        #
        if result in ["CRASH", "SKIP", "VALGR"]:
            f.write("<tr>\n")
            if result == "SKIP":
                f.write("<td style=\"color:#ff6600\">%s</td>\n" % result)
            else:
                f.write("<td style=\"color:red\">%s</td>\n" % result)
            f.write("</tr>\n")
            f.write("</table>\n")
            continue

        #
        # If the suite didn't crash, we expect more information, so fill out the table heading row.  如果套件没有崩溃，我们希望获得更多信息，所以请填写表格标题行。
        # Like,
        #
        #   +--------+----------------+------+
        #   | Result | Test Case Name | Time |
        #   +--------+----------------+------+
        #
        f.write("<th>Test Case Name</th>\n")
        f.write("<th> Time </th>\n")

        #
        # If the test case failed, we need to print out some failure details so extend the heading row again.  如果测试用例失败，我们需要打印出一些失败的详细信息，以便再次扩展标题行。
        # Like,
        #
        #   +--------+----------------+------+-----------------+
        #   | Result | Test Case Name | Time | Failure Details |
        #   +--------+----------------+------+-----------------+
        #
        if result == "FAIL":
            f.write("<th>Failure Details</th>\n")

        #
        # Now iterate through all of the test cases.
        #
        for case in suite.findall('Test'):

            #
            # Get the name, result and timing information from xml to use in printing table below.
            # 从 xml 中获取名称、结果和计时信息，以便在下面的打印表格中使用。
            #
            (result, name, reason, time) = read_test(case)

            #
            # If the test case failed, we iterate through possibly multiple
            # failure details
            #
            if result == "FAIL":
                #
                # There can be multiple failures for each test case.   每个测试用例可能有多个失败。
                # The first row always gets the result, name and timing information along with the failure details. 第一行始终获取结果、名称和计时信息以及故障详细信息。
                # Remaining failures don't duplicate this information but just get blanks for readability.  剩下的故障不会重复这些信息，只是为了可读性而得到空格。
                # Like,
                #
                #   +--------+----------------+------+-----------------+
                #   | Result | Test Case Name | Time | Failure Details |
                #   +--------+----------------+------+-----------------+
                #   |  FAIL  | The name       | time | It's busted     |
                #   +--------+----------------+------+-----------------+
                #   |        |                |      | Really broken   |
                #   +--------+----------------+------+-----------------+
                #   |        |                |      | Busted bad      |
                #   +--------+----------------+------+-----------------+
                #

                first_row = True
                for details in case.findall('FailureDetails'):

                    #
                    # Start a new row in the table for each possible Failure Detail 为每个可能的失败详细信息在表中启动一个新行
                    #
                    f.write("<tr>\n")

                    if first_row:
                        first_row = False
                        f.write("<td style=\"color:red\">%s</td>\n" % result)
                        f.write("<td>%s</td>\n" % name)
                        f.write("<td>%s</td>\n" % time)
                    else:
                        f.write("<td></td>\n")
                        f.write("<td></td>\n")
                        f.write("<td></td>\n")

                    f.write("<td>")
                    f.write("<b>Message: </b>%s, " % details.find('Message').text)
                    f.write("<b>Condition: </b>%s, " % details.find('Condition').text)
                    f.write("<b>Actual: </b>%s, " % details.find('Actual').text)
                    f.write("<b>Limit: </b>%s, " % details.find('Limit').text)
                    f.write("<b>File: </b>%s, " % details.find('File').text)
                    f.write("<b>Line: </b>%s" % details.find('Line').text)
                    f.write("</td>\n")

                    #
                    # End the table row
                    #
                    f.write("</td>\n")
            else:
                #
                # If this particular test case passed, then we just print the PASS result in green, followed by the test case name and its execution time information. 
                # 如果这个特定的测试用例通过了，那么我们只需将 PASS 结果打印成绿色，然后打印测试用例名称及其执行时间信息。
                #  These go off in <td> ... </td> table data.
                # The details table entry is left blank.
                #
                #   +--------+----------------+------+---------+
                #   | Result | Test Case Name | Time | Details |
                #   +--------+----------------+------+---------+
                #   |  PASS  | The name       | time |         |
                #   +--------+----------------+------+---------+
                #
                f.write("<tr>\n")
                f.write("<td style=\"color:green\">%s</td>\n" % result)
                f.write("<td>%s</td>\n" % name)
                f.write("<td>%s</td>\n" % time)
                f.write("<td>%s</td>\n" % reason)
                f.write("</tr>\n")
        #
        # All of the rows are written, so we need to end the table. 所有行都已写入，因此我们需要结束表。
        #
        f.write("</table>\n")

    #
    # That's it for all of the test suites.   所有的测试套件都是这样的。
    # Now we have to do something about our examples.  现在我们必须对我们的例子做些什么。
    #
    f.write("<h2>Examples</h2>\n")

    #
    # Example status is rendered in a table just like the suites. 示例状态在表中呈现，就像套件一样。
    #
    f.write("<table border=\"1\">\n")

    #
    # The table headings look like, 表格的标题看起来像,
    #
    #   +--------+--------------+--------------+---------+
    #   | Result | Example Name | Elapsed Time | Details |
    #   +--------+--------------+--------------+---------+
    #
    f.write("<th> Result </th>\n")
    f.write("<th>Example Name</th>\n")
    f.write("<th>Elapsed Time</th>\n")
    f.write("<th>Details</th>\n")

    #
    # Now iterate through all of the examples
    #
    for example in et.findall("Example"):

        #
        # Start a new row for each example
        #
        f.write("<tr>\n")

        #
        # Get the result and name of the example in question
        #
        (result, name, reason, time) = read_test(example)

        #
        # If the example either failed or crashed, print its result status
        # in red; otherwise green.  This goes in a <td> ... </td> table data
        #
        if result == "PASS":
            f.write("<td style=\"color:green\">%s</td>\n" % result)
        elif result == "SKIP":
            f.write("<td style=\"color:#ff6600\">%s</fd>\n" % result)
        else:
            f.write("<td style=\"color:red\">%s</td>\n" % result)

        #
        # Write the example name as a new tag data.
        #
        f.write("<td>%s</td>\n" % name)

        #
        # Write the elapsed time as a new tag data.
        #
        f.write("<td>%s</td>\n" % time)

        #
        # Write the reason, if it exist
        #
        f.write("<td>%s</td>\n" % reason)

        #
        # That's it for the current example, so terminate the row.
        #
        f.write("</tr>\n")

    #
    # That's it for the table of examples, so terminate the table.
    #
    f.write("</table>\n")

    #
    # And that's it for the report, so finish up.
    #
    f.write("</body>\n")
    f.write("</html>\n")
    f.close()
    print('done.')

#
# Python Control-C handling is broken in the presence of multiple threads. 当存在多个线程时，Python Control-C 处理会中断。
# Signals get delivered to the runnable/running thread by default and if it is blocked, the signal is simply ignored.  默认情况下，信号被传递到可运行/正在运行的线程，如果它被阻塞，信号就会被忽略。
# So we hook sigint and set a global variable telling the system to shut down gracefully.
# 所以我们钩住 sigint 并设置一个全局变量，告诉系统优雅地关闭。
#
thread_exit = False

def sigint_hook(signal, frame):
    global thread_exit
    thread_exit = True
    return 0


#
# In general, the build process itself naturally takes care of figuring out which tests are built into the test runner.  一般来说，构建过程本身会很自然地确定哪些测试被构建到测试运行程序中。
# For example, if waf configure determines that ENABLE_EMU is false due to some missing dependency,
# 例如，如果 waf configure 确定 ENABLE _ EMU 由于缺少某些依赖项而为 false,Emu 网络设备的测试根本不会被构建，因此不会包括在构建的测试流道中。
# the tests for the emu net device simply will not be built and will therefore not be included in the built test runner.
# 
#
# Examples, however, are a different story.  然而，例子就不同了。
# In that case, we are just given a list of examples that could be run.  在这种情况下，我们只获得了一个可以运行的示例列表。
# Instead of just failing, for example, nsc-tcp-zoo if NSC is not present, we look into the waf saved configuration for relevant configuration items.
#例如，如果 NSC 不存在，则不仅仅是失败，我们将查看相关配置项的 waf 保存的配置。
#
# XXX This function pokes around in the waf internal state file.  XXX 此函数在 waf 内部状态文件中查找。
# To be a little less hacky, we should add a command to waf to return this info  and use that result.
# 为了不那么蹩脚，我们应该向 waf 添加一个命令来返回这个信息并使用这个结果。
#
def read_waf_config():
    f = None
    try:
        # sys.platform reports linux2 for python2 and linux for python3 Platform 报告用于 python2的 linux2和用于 python3的 linux Platform 报告用于 python2的 linux2和用于 python3的 linux
        f = open(".lock-waf_" + sys.platform + "_build", "rt")
    except FileNotFoundError:
        try:
            f = open(".lock-waf_linux2_build", "rt")
        except FileNotFoundError:
            print('The .lock-waf ... directory was not found.  You must do waf build before running test.py.', file=sys.stderr)
            sys.exit(2)

    for line in f:
        if line.startswith("top_dir ="):
            key, val = line.split('=')
            top_dir = eval(val.strip())
        if line.startswith("out_dir ="):
            key, val = line.split('=')
            out_dir = eval(val.strip())
    global NS3_BASEDIR
    NS3_BASEDIR = top_dir
    global NS3_BUILDDIR
    NS3_BUILDDIR = out_dir
    for line in open("%s/c4che/_cache.py" % out_dir).readlines():
        for item in interesting_config_items:
            if line.startswith(item):
                exec(line, globals())

    if options.verbose:
        for item in interesting_config_items:
            print("%s ==" % item, eval(item))

#
# It seems pointless to fork a process to run waf to fork a process to run the test runner, so we just run the test runner directly.  
# 让一个进程运行 waf，让另一个进程运行测试运行程序似乎毫无意义，所以我们只是直接运行测试运行程序。
# The main thing that waf would do for us would be to sort out the shared library path but we can deal with that easily and do here.
# Waf 将为我们做的主要事情是整理出共享库路径，但是我们可以很容易地处理这个问题，在这里就可以做到。
# 
#
# There can be many different ns-3 repositories on a system, and each has its own shared libraries, so ns-3 doesn't hardcode a shared library search ath -- it is cooked up dynamically, so we do that too.
# 一个系统上可以有许多不同的 ns-3存储库，每个存储库都有自己的共享库，所以 ns-3不会硬编码一个共享库搜索 ath ——它是动态编写的，所以我们也这样做。
# p
#
def make_paths():
    # 标志，用于检查特定的环境变量是否已存在
    have_DYLD_LIBRARY_PATH = False
    have_LD_LIBRARY_PATH = False
    have_PATH = False
    have_PYTHONPATH = False

    # 获取所有环境变量名称的列表
    keys = list(os.environ.keys())

    # 检查特定的环境变量是否存在
    for key in keys:
        if key == "DYLD_LIBRARY_PATH":
            have_DYLD_LIBRARY_PATH = True
        if key == "LD_LIBRARY_PATH":
            have_LD_LIBRARY_PATH = True
        if key == "PATH":
            have_PATH = True
        if key == "PYTHONPATH":
            have_PYTHONPATH = True

    # 将 PYTHONPATH 设置为基于 NS3_BUILDDIR 的特定路径
    pypath = os.environ["PYTHONPATH"] = os.path.join(NS3_BUILDDIR, "bindings", "python")

    # 更新 PYTHONPATH，如果不存在则创建
    if not have_PYTHONPATH:
        os.environ["PYTHONPATH"] = pypath
    else:
        os.environ["PYTHONPATH"] += ":" + pypath

    # 如果启用了详细输出选项，打印 PYTHONPATH
    if options.verbose:
        print("os.environ[\"PYTHONPATH\"] == %s" % os.environ["PYTHONPATH"])

    # 根据操作系统设置额外的环境变量
    if sys.platform == "darwin":
         # 初始化或追加到 DYLD_LIBRARY_PATH
        if not have_DYLD_LIBRARY_PATH:
            os.environ["DYLD_LIBRARY_PATH"] = ""
        for path in NS3_MODULE_PATH:
            os.environ["DYLD_LIBRARY_PATH"] += ":" + path
        # 如果启用了详细输出选项，打印 DYLD_LIBRARY_PATH
        if options.verbose:
            print("os.environ[\"DYLD_LIBRARY_PATH\"] == %s" % os.environ["DYLD_LIBRARY_PATH"])
    elif sys.platform == "win32": # Windows
        # 初始化或追加到 PATH
        if not have_PATH:
            os.environ["PATH"] = ""
        for path in NS3_MODULE_PATH:
            os.environ["PATH"] += ';' + path
        # 如果启用了详细输出选项，打印 PATH
        if options.verbose:
            print("os.environ[\"PATH\"] == %s" % os.environ["PATH"])
    elif sys.platform == "cygwin":# Cygwin（Windows 上的类 Unix 环境）
        # 初始化或追加到 PATH
        if not have_PATH:
            os.environ["PATH"] = ""
        for path in NS3_MODULE_PATH:
            os.environ["PATH"] += ":" + path
        # 如果启用了详细输出选项，打印 PATH
        if options.verbose:
            print("os.environ[\"PATH\"] == %s" % os.environ["PATH"])
    else:  # 其他类 Unix 平台
        # 初始化或追加到 LD_LIBRARY_PATH
        if not have_LD_LIBRARY_PATH:
            os.environ["LD_LIBRARY_PATH"] = ""
        for path in NS3_MODULE_PATH:
            os.environ["LD_LIBRARY_PATH"] += ":" + str(path)
        # 如果启用了详细输出选项，打印 LD_LIBRARY_PATH
        if options.verbose:
            print("os.environ[\"LD_LIBRARY_PATH\"] == %s" % os.environ["LD_LIBRARY_PATH"])

#
# Short note on generating suppressions:
#关于产生抑制的简短说明:
# See the valgrind documentation for a description of suppressions.  有关抑制的描述，请参阅 valgray 文档。
# The easiest way to generate a suppression expression is by using the valgrind --gen-suppressions option. 生成抑制表达式的最简单方法是使用 valgrind --gen-suppressions option.
# To do that you have to figure out how to run the test in question.要做到这一点，你必须弄清楚如何运行有问题的测试。
# 
#
# If you do "test.py -v -g -s <suitename> then test.py will output most of what you need.  如果您执行“ test.py-v-g-s < suitename >”，那么 test.py 将输出您需要的大部分内容。
# For example, if you are getting a valgrind error in the devices-mesh-dot11s-regression test suite, you can run:
# 例如，如果您在设备 Mesh-dot11s-回归测试套件中得到了 valgray 错误，您可以运行:
#
#   ./test.py -v -g -s devices-mesh-dot11s-regression
#
# You should see in the verbose output something that looks like:您应该在详细输出中看到如下内容:
#
#   Synchronously execute valgrind --suppressions=/home/craigdo/repos/ns-3-allinone-dev/ns-3-dev/testpy.supp
#   --leak-check=full --error-exitcode=2 /home/craigdo/repos/ns-3-allinone-dev/ns-3-dev/build/debug/utils/ns3-dev-test-runner-debug
#   --suite=devices-mesh-dot11s-regression --basedir=/home/craigdo/repos/ns-3-allinone-dev/ns-3-dev
#   --tempdir=testpy-output/2010-01-12-22-47-50-CUT
#   --out=testpy-output/2010-01-12-22-47-50-CUT/devices-mesh-dot11s-regression.xml
#
# You need to pull out the useful pieces, and so could run the following to reproduce your error:
# 您需要提取出有用的部分，因此可以运行以下命令来重现您的错误:
#
#   valgrind --suppressions=/home/craigdo/repos/ns-3-allinone-dev/ns-3-dev/testpy.supp
#   --leak-check=full --error-exitcode=2 /home/craigdo/repos/ns-3-allinone-dev/ns-3-dev/build/debug/utils/ns3-dev-test-runner-debug
#   --suite=devices-mesh-dot11s-regression --basedir=/home/craigdo/repos/ns-3-allinone-dev/ns-3-dev
#   --tempdir=testpy-output
#
# Hint: Use the first part of the command as is, and point the "tempdir" to somewhere real.  提示: 按原样使用命令的第一部分，并将“ temdir”指向某个真实的地方。
# You don't need to specify an "out" file.您不需要指定“ out”文件。
#
# When you run the above command you should see your valgrind error.  当您运行上面的命令时，您应该会看到 valground 错误。
# The suppression expression(s) can be generated by adding the --gen-suppressions=yes   抑制表达式可以通过添加--gen-suppressions=yes
# option to valgrind.  Use something like:
#
#   valgrind --gen-suppressions=yes --suppressions=/home/craigdo/repos/ns-3-allinone-dev/ns-3-dev/testpy.supp
#   --leak-check=full --error-exitcode=2 /home/craigdo/repos/ns-3-allinone-dev/ns-3-dev/build/debug/utils/ns3-dev-test-runner-debug
#   --suite=devices-mesh-dot11s-regression --basedir=/home/craigdo/repos/ns-3-allinone-dev/ns-3-dev
#   --tempdir=testpy-output
#
# Now when valgrind detects an error it will ask:
#
#   ==27235== ---- Print suppression ? --- [Return/N/n/Y/y/C/c] ----
#
# to which you just enter 'y'<ret>.
#
# You will be provided with a suppression expression that looks something like
# the following:
#   {
#     <insert_a_suppression_name_here>
#     Memcheck:Addr8
#     fun:_ZN3ns36dot11s15HwmpProtocolMac8SendPreqESt6vectorINS0_6IePreqESaIS3_EE
#     fun:_ZN3ns36dot11s15HwmpProtocolMac10SendMyPreqEv
#     fun:_ZN3ns36dot11s15HwmpProtocolMac18RequestDestinationENS_12Mac48AddressEjj
#     ...
#     the rest of the stack frame
#     ...
#   }
#您需要添加一个只能在详细模式下由 valGraduate 打印出来的压制名称(但是在任何情况下都需要有这个名称)。
# You need to add a supression name which will only be printed out by valgrind in verbose mode (but it needs to be there in any case).  
# The entire stack frame is shown to completely characterize the error, but in most cases you won't need all of that info.  
# 整个堆栈框架被显示为完全描述错误，但在大多数情况下，您不需要所有这些信息。
# For example, if you want to turn off all errors that happen hen the function (fun:) is called, you can just delete the rest of the stack frame.  
# 例如，如果要关闭调用函数(fun:)时发生的所有错误，只需删除堆栈帧的其余部分。
# You can also use wildcards to make the mangled signatures more readable.
#您还可以使用通配符使损坏的签名更具可读性。
# I added the following to the testpy.supp file for this particular error:
#对于这个特定的错误，我在 testpy.Supp 文件中添加了以下内容:
#   {
#     Suppress invalid read size errors in SendPreq() when using HwmpProtocolMac
#     Memcheck:Addr8
#     fun:*HwmpProtocolMac*SendPreq*
#   }
#
# Now, when you run valgrind the error will be suppressed.现在，当你运行 val弓的错误将被抑制。
#
VALGRIND_SUPPRESSIONS_FILE = "testpy.supp"

def run_job_synchronously(shell_command, directory, valgrind, is_python, build_path=""):
    suppressions_path = os.path.join(NS3_BASEDIR, VALGRIND_SUPPRESSIONS_FILE)

    if is_python:
        path_cmd = PYTHON[0] + " " + os.path.join(NS3_BASEDIR, shell_command)
    else:
        if len(build_path):
            path_cmd = os.path.join(build_path, shell_command)
        else:
            path_cmd = os.path.join(NS3_BUILDDIR, shell_command)

    if valgrind:
        cmd = "valgrind --suppressions=%s --leak-check=full --show-reachable=yes --error-exitcode=2 --errors-for-leak-kinds=all %s" % (suppressions_path,
            path_cmd)
    else:
        cmd = path_cmd

    if options.verbose:
        print("Synchronously execute %s" % cmd)

    start_time = time.time()
    proc = subprocess.Popen(cmd, shell=True, cwd=directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_results, stderr_results = proc.communicate()
    elapsed_time = time.time() - start_time

    retval = proc.returncode
    try:
        stdout_results = stdout_results.decode()
    except UnicodeDecodeError:
        print("Non-decodable character in stdout output of %s" % cmd)
        print(stdout_results)
        retval = 1
    try:
        stderr_results = stderr_results.decode()
    except UnicodeDecodeError:
        print("Non-decodable character in stderr output of %s" % cmd)
        print(stderr_results)
        retval = 1

    if options.verbose:
        print("Return code = ", retval)
        print("stderr = ", stderr_results)

    return (retval, stdout_results, stderr_results, elapsed_time)

#
# This class defines a unit of testing work.  这个类定义了一个测试工作单元。
# It will typically refer to a test suite to run using the test-runner, or an example to run directly.它通常引用要使用测试运行程序运行的测试套件，或者直接运行的示例。
#
class Job:
    def __init__(self):
        self.is_break = False
        self.is_skip = False
        self.skip_reason = ""
        self.is_example = False
        self.is_pyexample = False
        self.shell_command = ""
        self.display_name = ""
        self.basedir = ""
        self.tempdir = ""
        self.cwd = ""
        self.tmp_file_name = ""
        self.returncode = False
        self.elapsed_time = 0
        self.build_path = ""

    #
    # A job is either a standard job or a special job indicating that a worker thread should exist.  作业是一个标准作业或一个特殊作业，指示工作线程应该存在。
    # This special job is indicated by setting is_break to true.这个特殊的作业通过将 is _ break 设置为 true 来表示。
    # 
    #
    def set_is_break(self, is_break):
        self.is_break = is_break

    #
    # If a job is to be skipped, we actually run it through the worker threads to keep the PASS, FAIL, CRASH and SKIP processing all in one place.
    # 如果要跳过某个作业，我们实际上会在辅助线程中运行它，以便将 PASS、 FAIL、 CRASH 和 SKIP 处理集中在一个地方。
    #
    def set_is_skip(self, is_skip):
        self.is_skip = is_skip

    #
    # If a job is to be skipped, log the reason.如果要跳过某个作业，请记录原因。
    #
    def set_skip_reason(self, skip_reason):
        self.skip_reason = skip_reason

    #
    # Examples are treated differently than standard test suites.  示例与标准测试套件的处理方式不同。
    # This is mostly because they are completely unaware that they are being run as tests. 这主要是因为它们完全不知道它们是作为测试运行的。 
    # So we have to do some special case processing to make them look like tests.
    # 因此，我们必须做一些特殊的案例处理，使它们看起来像测试。
    #
    def set_is_example(self, is_example):
        self.is_example = is_example

    #
    # Examples are treated differently than standard test suites.  
    # This is mostly because they are completely unaware that they are being run as
    # tests.  So we have to do some special case processing to make them look
    # like tests.
    #
    def set_is_pyexample(self, is_pyexample):
        self.is_pyexample = is_pyexample

    #这是将在作业中执行的 shell 命令。
    # This is the shell command that will be executed in the job. 
    #
    #   For example, "utils/ns3-dev-test-runner-debug --test-name=some-test-suite"
    #
    def set_shell_command(self, shell_command):
        self.shell_command = shell_command

    #
    # This is the build path where ns-3 was built.  这是构建 ns-3的路径。
    #  For example,
    #  "/home/craigdo/repos/ns-3-allinone-test/ns-3-dev/build/debug"
    #
    def set_build_path(self, build_path):
        self.build_path = build_path

    #
    # This is the display name of the job, typically the test suite or example name.  这是作业的显示名称，通常是测试套件或示例名称。
    #  For example,
    #
    #  "some-test-suite" or "udp-echo"
    #
    def set_display_name(self, display_name):
        self.display_name = display_name

    #
    # This is the base directory of the repository out of which the tests are being run.  这是运行测试的存储库的基本目录。
    # It will be used deep down in the testing framework to determine where the source directory of the test was, and therefore where to find provided test vectors.  
    # 它将在测试框架的深层使用，以确定测试的源目录在哪里，因此在哪里可以找到提供的测试向量。
    # For example,
    #
    #  "/home/user/repos/ns-3-dev"
    #
    def set_basedir(self, basedir):
        self.basedir = basedir

    #
    # This is the directory to which a running test suite should write any temporary files.
    # 
    #
    def set_tempdir(self, tempdir):
        self.tempdir = tempdir

    #
    # This is the current working directory that will be given to an executing test as it is being run.  这是当前的工作目录，当一个正在执行的测试运行时，它将被赋予这个值。
    # It will be used for examples to tell them where to write all of the pcap files that we will be carefully ignoring.  它将用于示例，告诉他们在哪里写入我们将小心忽略的所有 pcap 文件。
    # For
    # example,
    #
    #  "/tmp/unchecked-traces"
    #
    def set_cwd(self, cwd):
        self.cwd = cwd

    #
    # This is the temporary results file name that will be given to an executing  test as it is being run.  这是一个临时结果文件名，将在正在执行的测试运行时给予该文件名。
    # We will be running all of our tests in parallel so there must be multiple temporary output files.  我们将并行运行所有测试，因此必须有多个临时输出文件。
    # These will be collected into a single XML file at the end and then be deleted.这些将在最后被收集到一个单独的 XML 文件中，然后被删除。
    # 
    #
    def set_tmp_file_name(self, tmp_file_name):
        self.tmp_file_name = tmp_file_name

    #
    # The return code received when the job process is executed.执行作业进程时收到的返回代码。
    #
    def set_returncode(self, returncode):
        self.returncode = returncode

    #
    # The elapsed real time for the job execution.作业执行所经过的实时时间。
    #
    def set_elapsed_time(self, elapsed_time):
        self.elapsed_time = elapsed_time

#
# The worker thread class that handles the actual running of a given test.处理给定测试的实际运行的辅助线程类。
# Once spawned, it receives requests for work through its input_queue and ships the results back through the output_queue.
# 派生之后，它通过 input _ queue 接收工作请求，并通过 output _ queue 将结果发送回来。
#
class worker_thread(threading.Thread):
    def __init__(self, input_queue, output_queue):
        threading.Thread.__init__(self)
        self.input_queue = input_queue
        self.output_queue = output_queue

    def run(self):
        while True:
            job = self.input_queue.get()
            #
            # Worker threads continue running until explicitly told to stop with a special job.
            # 辅助线程继续运行，直到被明确告知以特殊作业停止。
            #
            if job.is_break:
                return
            #
            # If the global interrupt handler sets the thread_exit variable,we stop doing real work and just report back a "break" in the  normal command processing has happened.
            # 如果全局 interrupt handler 设置 thread _ exit 变量，我们就停止实际工作，只是报告正常命令处理中发生了“中断”。
            #
            #
            if thread_exit == True:
                job.set_is_break(True)
                self.output_queue.put(job)
                continue

            #
            # If we are actually supposed to skip this job, do so.  
            # Note that if is_skip is true, returncode is undefined.
            #
            if job.is_skip:
                if options.verbose:
                    print("Skip %s" % job.shell_command)
                self.output_queue.put(job)
                continue

            #
            # Otherwise go about the business of running tests as normal.
            #
            else:
                if options.verbose:
                    print("Launch %s" % job.shell_command)

                if job.is_example or job.is_pyexample:
                    #
                    # If we have an example, the shell command is all we need to know.  如果我们有一个示例，那么我们只需要知道 shell 命令。
                    # It will be something like "examples/udp/udp-echo" or
                    # "examples/wireless/mixed-wireless.py"
                    #
                    (job.returncode, standard_out, standard_err, et) = run_job_synchronously(job.shell_command,
                        job.cwd, options.valgrind, job.is_pyexample, job.build_path)
                else:
                    #
                    # If we're a test suite, we need to provide a little more info
                    # to the test runner, specifically the base directory and temp
                    # file name 如果我们是一个测试套件，我们需要提供更多的信息到测试运行程序，特别是基本目录和临时目录
                    #
                    if options.update_data:
                        update_data = '--update-data'
                    else:
                        update_data = ''
                    (job.returncode, standard_out, standard_err, et) = run_job_synchronously(job.shell_command +
                        " --xml --tempdir=%s --out=%s %s" % (job.tempdir, job.tmp_file_name, update_data),
                        job.cwd, options.valgrind, False)

                job.set_elapsed_time(et)

                if options.verbose:
                    print("returncode = %d" % job.returncode)
                    print("---------- begin standard out ----------")
                    print(standard_out)
                    print("---------- begin standard err ----------")
                    print(standard_err)
                    print("---------- end standard err ----------")

                self.output_queue.put(job)

#
# This is the main function that does the work of interacting with the test-runner itself.
# 这是与测试运行程序本身进行交互的主要函数。
#
def run_tests():
    #
    # Pull some interesting configuration information out of waf, primarily so we can know where executables can be found, 
    # 从 waf 中提取一些有趣的配置信息，这样我们就可以知道在哪里可以找到可执行文件,
    # but also to tell us what pieces of the system have been built.  This will tell us what examples are runnable.
    # 还要告诉我们系统的哪些部分已经建成。这将告诉我们哪些示例是可运行的。
    #
    read_waf_config()

    #
    # Set the proper suffix.  设置适当的后缀。
    #
    global BUILD_PROFILE_SUFFIX
    if BUILD_PROFILE == 'release':
        BUILD_PROFILE_SUFFIX = ""
    else:
        BUILD_PROFILE_SUFFIX = "-" + BUILD_PROFILE

    #
    # Add the proper prefix and suffix to the test-runner name to match what is done in the wscript file.
    # 向测试运行程序名称添加适当的前缀和后缀，以匹配在 wscript 文件中执行的操作。
    #
    test_runner_name = "%s%s-%s%s" % (APPNAME, VERSION, "test-runner", BUILD_PROFILE_SUFFIX)

    #
    # Run waf to make sure that everything is built, configured and ready to go unless we are explicitly told not to.  运行 waf 以确保所有东西都已经构建、配置并准备好了，除非明确告诉我们不要这样做。
    # We want to be careful about causing our users pain while waiting for extraneous stuff to compile and link,
    # 我们希望在等待无关内容编译和链接时，小心不要给用户带来痛苦,因此，我们允许知道自己在做什么的用户根本不调用 waf。
    #  so we allow users that know what they''re doing to not invoke waf at all.
    #
    if not options.nowaf:

        #
        # If the user is running the "kinds" or "list" options, there is an implied dependency on the test-runner since we call that program if those options are selected.  
        # 如果用户正在运行“ kind”或“ list”选项，则存在对测试运行程序的隐含依赖，因为如果选择了这些选项，我们将调用该程序。
        # We will exit after processing those options, so if we see them, we can safely only build the test-runner.
        # 我们将在处理这些选项后退出，因此如果我们看到它们，我们只能安全地构建测试运行程序。
        #
        # If the user has constrained us to running only a particular type of file, we can only ask waf to build what we know will be necessary.
        # 如果用户限制我们只能运行特定类型的文件，我们只能要求 waf 构建我们知道必要的文件。
        # For example, if the user only wants to run BVT tests, we only have to build the test-runner and can ignore all of the examples.
        # 例如，如果用户只想运行 BVT 测试，我们只需要构建测试运行程序，并且可以忽略所有示例。
        #
        # If the user only wants to run a single example, then we can just build that example.
        # 如果用户只想运行一个示例，那么我们可以构建该示例。
        #
        # If there is no constraint, then we have to build everything since the user wants to run everything.
        # 如果没有约束，那么我们必须构建所有内容，因为用户希望运行所有内容。
        #
        if options.kinds or options.list or (len(options.constrain) and options.constrain in core_kinds):
            if sys.platform == "win32":
                waf_cmd = "./waf --target=test-runner"
            else:
                waf_cmd = "./waf --target=test-runner"
        elif len(options.example):
            if sys.platform == "win32": #Modify for windows
                waf_cmd = "./waf --target=%s" % os.path.basename(options.example)
            else:
                waf_cmd = "./waf --target=%s" % os.path.basename(options.example)
        else:
            if sys.platform == "win32": #Modify for windows
                waf_cmd = "./waf"
            else:
                waf_cmd = "./waf"

        if options.verbose:
            print("Building: %s" % waf_cmd)

        proc = subprocess.Popen(waf_cmd, shell = True)
        proc.communicate()
        if proc.returncode:
            print("Waf died. Not running tests", file=sys.stderr)
            return proc.returncode


    #
    # Dynamically set up paths.  动态设置路径。
    #
    make_paths()

    #
    # Get the information from the build status file.从构建状态文件中获取信息。
    #
    build_status_file = os.path.join(NS3_BUILDDIR, 'build-status.py')
    if os.path.exists(build_status_file):
        ns3_runnable_programs = get_list_from_file(build_status_file, "ns3_runnable_programs")
        ns3_runnable_scripts = get_list_from_file(build_status_file, "ns3_runnable_scripts")
    else:
        print('The build status file was not found.  You must do waf build before running test.py.', file=sys.stderr)
        sys.exit(2)

    #
    # Make a dictionary that maps the name of a program to its path. 创建一个将程序名映射到其路径的字典。
    #
    ns3_runnable_programs_dictionary = {}
    for program in ns3_runnable_programs:
        # Remove any directory names from path. 从路径中删除任何目录名。
        program_name = os.path.basename(program)
        ns3_runnable_programs_dictionary[program_name] = program

    # Generate the lists of examples to run as smoke tests in order to ensure that they remain buildable and runnable over time.
    # 生成要作为烟雾测试运行的示例列表，以确保它们随着时间的推移保持可构建和可运行。
    #
    example_tests = []
    example_names_original = []
    python_tests = []
    for directory in EXAMPLE_DIRECTORIES:
        # Set the directories and paths for this example.
        example_directory   = os.path.join("examples", directory)
        examples_to_run_path = os.path.join(example_directory, "examples-to-run.py")
        cpp_executable_dir   = os.path.join(NS3_BUILDDIR, example_directory)
        python_script_dir    = os.path.join(example_directory)

        # Parse this example directory's file.
        parse_examples_to_run_file(
            examples_to_run_path,
            cpp_executable_dir,
            python_script_dir,
            example_tests,
            example_names_original,
            python_tests)

    for module in NS3_ENABLED_MODULES:
        # Remove the "ns3-" from the module name.
        module = module[len("ns3-"):]

        # Set the directories and paths for this example.
        module_directory     = os.path.join("src", module)
        example_directory    = os.path.join(module_directory, "examples")
        examples_to_run_path = os.path.join(module_directory, "test", "examples-to-run.py")
        cpp_executable_dir   = os.path.join(NS3_BUILDDIR, example_directory)
        python_script_dir    = os.path.join(example_directory)

        # Parse this module's file. 解析这个模块的文件。
        parse_examples_to_run_file(
            examples_to_run_path,
            cpp_executable_dir,
            python_script_dir,
            example_tests,
            example_names_original,
            python_tests)

    for module in NS3_ENABLED_CONTRIBUTED_MODULES:
        # Remove the "ns3-" from the module name.
        module = module[len("ns3-"):]

        # Set the directories and paths for this example.
        module_directory     = os.path.join("contrib", module)
        example_directory    = os.path.join(module_directory, "examples")
        examples_to_run_path = os.path.join(module_directory, "test", "examples-to-run.py")
        cpp_executable_dir   = os.path.join(NS3_BUILDDIR, example_directory)
        python_script_dir    = os.path.join(example_directory)

        # Parse this module's file.
        parse_examples_to_run_file(
            examples_to_run_path,
            cpp_executable_dir,
            python_script_dir,
            example_tests,
            example_names_original,
            python_tests)

    #
    # If lots of logging is enabled, we can crash Python when it tries to save all of the text.  如果启用了大量的日志记录，那么当 Python 试图保存所有文本时，我们可以使它崩溃。
    # We just don't allow logging to be turned on when  test.py runs.   我们只是不允许在 test.py 运行时打开日志记录。
    #If you want to see logging output from your tests, you have to run them using the test-runner directly.如果希望看到测试的日志输出，则必须直接使用测试运行程序运行它们。
    # 
    #
    os.environ["NS_LOG"] = ""

    #
    # There are a couple of options that imply we can to exit before starting up a bunch of threads and running tests.  有几个选项暗示我们可以在启动一堆线程和运行测试之前退出。
    # Let's detect these cases and handle them without doing all of the hard work.让我们检测并处理这些案件，而不用做所有的艰苦工作。
    # 
    #
    if options.kinds:
        path_cmd = os.path.join("utils", test_runner_name + " --print-test-type-list")
        (rc, standard_out, standard_err, et) = run_job_synchronously(path_cmd, os.getcwd(), False, False)
        print(standard_out)

    if options.list:
        if len(options.constrain):
            path_cmd = os.path.join("utils", test_runner_name + " --print-test-name-list --print-test-types --test-type=%s" % options.constrain)
        else:
            path_cmd = os.path.join("utils", test_runner_name + " --print-test-name-list --print-test-types")
        (rc, standard_out, standard_err, et) = run_job_synchronously(path_cmd, os.getcwd(), False, False)
        if rc != 0:
            # This is usually a sign that ns-3 crashed or exited uncleanly
            print(('test.py error:  test-runner return code returned {}'.format(rc)))
            print(('To debug, try running {}\n'.format('\'./waf --run \"test-runner --print-test-name-list\"\'')))
            return
        if isinstance(standard_out, bytes):
            standard_out = standard_out.decode()
        list_items = standard_out.split('\n')
        list_items.sort()
        print("Test Type    Test Name")
        print("---------    ---------")
        for item in list_items:
            if len(item.strip()):
                print(item)
        example_names_original.sort()
        for item in example_names_original:
                print("example     ", item)
        print()

    if options.kinds or options.list:
        return

    #
    # We communicate results in two ways.  First, a simple message relating
    # PASS, FAIL, CRASH or SKIP is always written to the standard output.  It
    # is expected that this will be one of the main use cases.  A developer can
    # just run test.py with no options and see that all of the tests still
    # pass.
    #
    # The second main use case is when detailed status is requested (with the
    # --text or --html options).  Typically this will be text if a developer
    # finds a problem, or HTML for nightly builds.  In these cases, an
    # XML file is written containing the status messages from the test suites.
    # This file is then read and translated into text or HTML.  It is expected
    # that nobody will really be interested in the XML, so we write it somewhere
    # with a unique name (time) to avoid collisions.  In case an error happens, we
    # provide a runtime option to retain the temporary files.
    #
    # When we run examples as smoke tests, they are going to want to create
    # lots and lots of trace files.  We aren't really interested in the contents
    # of the trace files, so we also just stash them off in the temporary dir.
    # The retain option also causes these unchecked trace files to be kept.
    #
    date_and_time = time.strftime("%Y-%m-%d-%H-%M-%S-CUT", time.gmtime())

    if not os.path.exists(TMP_OUTPUT_DIR):
        os.makedirs(TMP_OUTPUT_DIR)

    testpy_output_dir = os.path.join(TMP_OUTPUT_DIR, date_and_time);

    if not os.path.exists(testpy_output_dir):
        os.makedirs(testpy_output_dir)

    #
    # Create the main output file and start filling it with XML.  We need to
    # do this since the tests will just append individual results to this file.
    #
    xml_results_file = os.path.join(testpy_output_dir, "results.xml")
    f = open(xml_results_file, 'w')
    f.write('<?xml version="1.0"?>\n')
    f.write('<Results>\n')
    f.close()

    #
    # We need to figure out what test suites to execute.  We are either given one
    # suite or example explicitly via the --suite or --example/--pyexample option,
    # or we need to call into the test runner and ask it to list all of the available
    # test suites.  Further, we need to provide the constraint information if it
    # has been given to us.
    #
    # This translates into allowing the following options with respect to the
    # suites
    #
    #  ./test,py:                                           run all of the suites and examples
    #  ./test.py --constrain=core:                          run all of the suites of all kinds
    #  ./test.py --constrain=unit:                          run all unit suites
    #  ./test.py --suite=some-test-suite:                   run a single suite
    #  ./test.py --example=examples/udp/udp-echo:           run single example
    #  ./test.py --pyexample=examples/wireless/mixed-wireless.py:  run python example
    #  ./test.py --suite=some-suite --example=some-example: run the single suite
    #
    # We can also use the --constrain option to provide an ordering of test
    # execution quite easily.
    #

    # Flag indicating a specific suite was explicitly requested
    single_suite = False

    if len(options.suite):
        # See if this is a valid test suite.
        path_cmd = os.path.join("utils", test_runner_name + " --print-test-name-list")
        (rc, suites, standard_err, et) = run_job_synchronously(path_cmd, os.getcwd(), False, False)

        if isinstance(suites, bytes):
            suites = suites.decode()

        suites_found = fnmatch.filter(suites.split('\n'), options.suite)

        if not suites_found:
            print('The test suite was not run because an unknown test suite name was requested.', file=sys.stderr)
            sys.exit(2)
        elif len(suites_found) == 1:
            single_suite = True

        suites = '\n'.join(suites_found)

    elif len(options.example) == 0 and len(options.pyexample) == 0:
        if len(options.constrain):
            path_cmd = os.path.join("utils", test_runner_name + " --print-test-name-list --test-type=%s" % options.constrain)
            (rc, suites, standard_err, et) = run_job_synchronously(path_cmd, os.getcwd(), False, False)
        else:
            path_cmd = os.path.join("utils", test_runner_name + " --print-test-name-list")
            (rc, suites, standard_err, et) = run_job_synchronously(path_cmd, os.getcwd(), False, False)
    else:
        suites = ""

    #
    # suite_list will either a single test suite name that the user has
    # indicated she wants to run or a list of test suites provided by
    # the test-runner possibly according to user provided constraints.
    # We go through the trouble of setting up the parallel execution
    # even in the case of a single suite to avoid having to process the
    # results in two different places.
    #
    if isinstance(suites, bytes):
        suites = suites.decode()
    suite_list = suites.split('\n')

    #
    # Performance tests should only be run when they are requested,
    # i.e. they are not run by default in test.py.
    # If a specific suite was requested we run it, even if
    # it is a performance test.
    if not single_suite and options.constrain != 'performance':

        # Get a list of all of the performance tests.
        path_cmd = os.path.join("utils", test_runner_name + " --print-test-name-list --test-type=%s" % "performance")
        (rc, performance_tests, standard_err, et) = run_job_synchronously(path_cmd, os.getcwd(), False, False)
        if isinstance(performance_tests, bytes):
            performance_tests = performance_tests.decode()
        performance_test_list = performance_tests.split('\n')

        # Remove any performance tests from the suites list.
        for performance_test in performance_test_list:
            if performance_test in suite_list:
                suite_list.remove(performance_test)

    # We now have a possibly large number of test suites to run, so we want to
    # run them in parallel.  We're going to spin up a number of worker threads
    # that will run our test jobs for us.
    #
    input_queue = queue.Queue(0)
    output_queue = queue.Queue(0)

    jobs = 0
    threads=[]

    #
    # In Python 2.6 you can just use multiprocessing module, but we don't want
    # to introduce that dependency yet; so we jump through a few hoops.
    #
    processors = 1

    if sys.platform != "win32":
        if 'SC_NPROCESSORS_ONLN'in os.sysconf_names:
            processors = os.sysconf('SC_NPROCESSORS_ONLN')
        else:
            proc = subprocess.Popen("sysctl -n hw.ncpu", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout_results, stderr_results = proc.communicate()
            stdout_results = stdout_results.decode()
            stderr_results = stderr_results.decode()
            if len(stderr_results) == 0:
                processors = int(stdout_results)

    if (options.process_limit):
        if (processors < options.process_limit):
            print('Using all %s processors' % processors)
        else:
            processors = options.process_limit
            print('Limiting to %s worker processes' % processors)

    #
    # Now, spin up one thread per processor which will eventually mean one test
    # per processor running concurrently.
    #
    for i in range(processors):
        thread = worker_thread(input_queue, output_queue)
        threads.append(thread)
        thread.start()

    #
    # Keep track of some summary statistics
    #
    total_tests = 0
    skipped_tests = 0
    skipped_testnames = []

    #
    # We now have worker threads spun up, and a list of work to do.  So, run
    # through the list of test suites and dispatch a job to run each one.
    #
    # Dispatching will run with unlimited speed and the worker threads will
    # execute as fast as possible from the queue.
    #
    # Note that we actually dispatch tests to be skipped, so all of the
    # PASS, FAIL, CRASH and SKIP processing is done in the same place.
    #
    for test in suite_list:
        test = test.strip()
        if len(test):
            job = Job()
            job.set_is_example(False)
            job.set_is_pyexample(False)
            job.set_display_name(test)
            job.set_tmp_file_name(os.path.join(testpy_output_dir, "%s.xml" % test))
            job.set_cwd(os.getcwd())
            job.set_basedir(os.getcwd())
            job.set_tempdir(testpy_output_dir)
            if (options.multiple):
                multiple = ""
            else:
                multiple = " --stop-on-failure"
            if (len(options.fullness)):
                fullness = options.fullness.upper()
                fullness = " --fullness=%s" % fullness
            else:
                fullness = " --fullness=QUICK"

            path_cmd = os.path.join("utils", test_runner_name + " --test-name=%s%s%s" % (test, multiple, fullness))

            job.set_shell_command(path_cmd)

            if options.valgrind and test in core_valgrind_skip_tests:
                job.set_is_skip(True)
                job.set_skip_reason("crashes valgrind")

            # Skip tests that will fail if NSC is missing.
            if not NSC_ENABLED and test in core_nsc_missing_skip_tests:
                job.set_is_skip(True)
                job.set_skip_reason("requires NSC")

            if options.verbose:
                print("Queue %s" % test)

            input_queue.put(job)
            jobs = jobs + 1
            total_tests = total_tests + 1

    #
    # We've taken care of the discovered or specified test suites.  我们已经处理了已发现或指定的测试套件。
    # Now we have to deal with examples run as smoke tests. 现在我们必须处理作为烟雾测试运行的示例。 
    # We have a list of all of the example programs it makes sense to try and run.  我们有一个所有示例程序的列表，尝试并运行它是有意义的。
    # Each example will have a condition associated with it that must evaluate to true for us to try and execute it.  每个示例都有一个与之相关联的条件，该条件的计算结果必须为 true，我们才能尝试并执行它。
    # This is used to determine if the example has a dependency that is not satisfied.  这用于确定示例是否具有不满足的依赖项。
    # For example, if an example depends on NSC being configured by waf, that example should have a condition that evaluates to true if NSC is enabled.  
    # 例如，如果一个示例依赖于通过 waf 配置的 NSC，那么该示例应该有一个条件，如果启用 NSC，则该条件的计算结果为 true。
    # For example,
    #
    #      ("tcp-nsc-zoo", "NSC_ENABLED == True"),
    #
    # In this case, the example "tcp-nsc-zoo" will only be run if we find the waf configuration variable "NSC_ENABLED" to be True.
    # 在本例中，只有当我们发现 waf 配置变量“ NSC _ ENABLED”为 True 时，示例“ tcp-NSC-zoo”才会运行。
    #
    # We don't care at all how the trace files come out, so we just write them to a single temporary directory.
    # 我们根本不关心跟踪文件是如何产生的，所以我们只是将它们写到一个临时目录中。
    #
    # XXX As it stands, all of the trace files have unique names, and so file collisions can only happen if two instances of an example are running in two versions of the test.py process concurrently.  
    # 按照现在的情况，所有跟踪文件都有唯一的名称，因此只有当一个示例的两个实例同时在 test.py 进程的两个版本中运行时，才会发生文件冲突。
    # We may want to create uniquely named temporary traces directories to avoid this problem.
    # 我们可能需要创建唯一命名的临时跟踪目录来避免这个问题。
    #
    # We need to figure out what examples to execute.  We are either given one suite or example explicitly via the --suite or --example option,
    # 我们需要弄清楚要执行哪些示例。我们可以获得一个套件，也可以通过—— kit 或—— example 选项显式地获得一个示例,或者我们需要在示例列表中查找可用的示例
    #  or we need to walk the list of examples looking for available example
    # conditions.
    #
    # This translates into allowing the following options with respect to the
    # suites
    #
    #  ./test.py:                                           run all of the examples
    #  ./test.py --constrain=unit                           run no examples
    #  ./test.py --constrain=example                        run all of the examples
    #  ./test.py --suite=some-test-suite:                   run no examples
    #  ./test.py --example=some-example:                    run the single example
    #  ./test.py --suite=some-suite --example=some-example: run the single example
    #
    #
    if len(options.suite) == 0 and len(options.example) == 0 and len(options.pyexample) == 0:
        if len(options.constrain) == 0 or options.constrain == "example":
            if ENABLE_EXAMPLES:
                for name, test, do_run, do_valgrind_run in example_tests:
                    # Remove any arguments and directory names from test.
                    test_name = test.split(' ', 1)[0]
                    test_name = os.path.basename(test_name)

                    # Don't try to run this example if it isn't runnable.
                    if test_name in ns3_runnable_programs_dictionary:
                        if eval(do_run):
                            job = Job()
                            job.set_is_example(True)
                            job.set_is_pyexample(False)
                            job.set_display_name(name)
                            job.set_tmp_file_name("")
                            job.set_cwd(testpy_output_dir)
                            job.set_basedir(os.getcwd())
                            job.set_tempdir(testpy_output_dir)
                            job.set_shell_command(test)
                            job.set_build_path(options.buildpath)

                            if options.valgrind and not eval(do_valgrind_run):
                                job.set_is_skip(True)
                                job.set_skip_reason("skip in valgrind runs")

                            if options.verbose:
                                print("Queue %s" % test)

                            input_queue.put(job)
                            jobs = jobs + 1
                            total_tests = total_tests + 1

    elif len(options.example):
        # Add the proper prefix and suffix to the example name to
        # match what is done in the wscript file.
        example_name = "%s%s-%s%s" % (APPNAME, VERSION, options.example, BUILD_PROFILE_SUFFIX)

        key_list = []
        for key in ns3_runnable_programs_dictionary:
            key_list.append (key)
        example_name_key_list = fnmatch.filter(key_list, example_name)

        if len(example_name_key_list) == 0:
            print("No example matching the name %s" % options.example)
        else:
            #
            # If you tell me to run an example, I will try and run the example
            # irrespective of any condition.
            #
            for example_name_iter in example_name_key_list:
                example_path = ns3_runnable_programs_dictionary[example_name_iter]
                example_path = os.path.abspath(example_path)
                job = Job()
                job.set_is_example(True)
                job.set_is_pyexample(False)
                job.set_display_name(example_path)
                job.set_tmp_file_name("")
                job.set_cwd(testpy_output_dir)
                job.set_basedir(os.getcwd())
                job.set_tempdir(testpy_output_dir)
                job.set_shell_command(example_path)
                job.set_build_path(options.buildpath)

                if options.verbose:
                    print("Queue %s" % example_name_iter)

                input_queue.put(job)
                jobs = jobs + 1
                total_tests = total_tests + 1

    #
    # Run some Python examples as smoke tests.  We have a list of all of
    # the example programs it makes sense to try and run.  Each example will
    # have a condition associated with it that must evaluate to true for us
    # to try and execute it.  This is used to determine if the example has
    # a dependency that is not satisfied.
    #
    # We don't care at all how the trace files come out, so we just write them
    # to a single temporary directory.
    #
    # We need to figure out what python examples to execute.  We are either
    # given one pyexample explicitly via the --pyexample option, or we
    # need to walk the list of python examples
    #
    # This translates into allowing the following options with respect to the
    # suites
    #
    #  ./test.py --constrain=pyexample           run all of the python examples
    #  ./test.py --pyexample=some-example.py:    run the single python example
    #
    if len(options.suite) == 0 and len(options.example) == 0 and len(options.pyexample) == 0:
        if len(options.constrain) == 0 or options.constrain == "pyexample":
            if ENABLE_EXAMPLES:
                for test, do_run in python_tests:
                    # Remove any arguments and directory names from test.
                    test_name = test.split(' ', 1)[0]
                    test_name = os.path.basename(test_name)

                    # Don't try to run this example if it isn't runnable.
                    if test_name in ns3_runnable_scripts:
                        if eval(do_run):
                            job = Job()
                            job.set_is_example(False)
                            job.set_is_pyexample(True)
                            job.set_display_name(test)
                            job.set_tmp_file_name("")
                            job.set_cwd(testpy_output_dir)
                            job.set_basedir(os.getcwd())
                            job.set_tempdir(testpy_output_dir)
                            job.set_shell_command(test)
                            job.set_build_path("")

                            #
                            # Python programs and valgrind do not work and play
                            # well together, so we skip them under valgrind.
                            # We go through the trouble of doing all of this
                            # work to report the skipped tests in a consistent
                            # way through the output formatter.
                            #
                            if options.valgrind:
                                job.set_is_skip(True)
                                job.set_skip_reason("skip in valgrind runs")

                            #
                            # The user can disable python bindings, so we need
                            # to pay attention to that and give some feedback
                            # that we're not testing them
                            #
                            if not ENABLE_PYTHON_BINDINGS:
                                job.set_is_skip(True)
                                job.set_skip_reason("requires Python bindings")

                            if options.verbose:
                                print("Queue %s" % test)

                            input_queue.put(job)
                            jobs = jobs + 1
                            total_tests = total_tests + 1

    elif len(options.pyexample):
        # Don't try to run this example if it isn't runnable.
        example_name = os.path.basename(options.pyexample)
        if example_name not in ns3_runnable_scripts:
            print("Example %s is not runnable." % example_name)
        else:
            #
            # If you tell me to run a python example, I will try and run the example
            # irrespective of any condition.
            #
            job = Job()
            job.set_is_pyexample(True)
            job.set_display_name(options.pyexample)
            job.set_tmp_file_name("")
            job.set_cwd(testpy_output_dir)
            job.set_basedir(os.getcwd())
            job.set_tempdir(testpy_output_dir)
            job.set_shell_command(options.pyexample)
            job.set_build_path("")

            if options.verbose:
                print("Queue %s" % options.pyexample)

            input_queue.put(job)
            jobs = jobs + 1
            total_tests = total_tests + 1

    #
    # Tell the worker threads to pack up and go home for the day.  告诉工人们收拾东西回家休息一天。
    # Each one will exit when they see their is_break task. 每一个都将在看到它们的 is _ break 任务时退出。
    #
    for i in range(processors):
        job = Job()
        job.set_is_break(True)
        input_queue.put(job)

    #
    # Now all of the tests have been dispatched, so all we have to do here in the main thread is to wait for them to complete.  现在所有的测试都已经发送完毕，所以我们在主线程中要做的就是等待它们完成。
    # Keyboard interrupt handling is broken as mentioned above.  如上所述，键盘中断处理中断。
    # We use a signal handler to catch sigint and set a global variable.  我们使用一个信号处理器来捕捉信号并设置一个全局变量
    # When the worker threads sense this they stop doing real work and will just start throwing jobs back at us with is_break set to True.  
    # 当工作线程感觉到这一点时，它们就停止做实际的工作，并开始用 is _ break 设置为 True 向我们返回作业。
    # In this case, there are no real results so we ignore them.  在这种情况下，没有真正的结果，所以我们忽略它们。
    # If there are real results, we always print PASS or FAIL to standard out as a quick indication of what happened.如果有真正的结果，我们总是打印 PASS 或 FAIL 标准出来，作为发生了什么的快速指示。
    # 
    #
    passed_tests = 0
    failed_tests = 0
    failed_testnames = []
    crashed_tests = 0
    crashed_testnames = []
    valgrind_errors = 0
    valgrind_testnames = []
    for i in range(jobs):
        job = output_queue.get()
        if job.is_break:
            continue

        if job.is_example or job.is_pyexample:
            kind = "Example"
        else:
            kind = "TestSuite"

        if job.is_skip:
            status = "SKIP"
            status_print = colors.GREY + status + colors.NORMAL
            skipped_tests = skipped_tests + 1
            skipped_testnames.append(job.display_name + (" (%s)" % job.skip_reason))
        else:
            if job.returncode == 0:
                status = "PASS"
                status_print = colors.GREEN + status + colors.NORMAL
                passed_tests = passed_tests + 1
            elif job.returncode == 1:
                failed_tests = failed_tests + 1
                failed_testnames.append(job.display_name)
                status = "FAIL"
                status_print = colors.RED + status + colors.NORMAL
            elif job.returncode == 2:
                valgrind_errors = valgrind_errors + 1
                valgrind_testnames.append(job.display_name)
                status = "VALGR"
                status_print = colors.CYAN + status + colors.NORMAL
            else:
                crashed_tests = crashed_tests + 1
                crashed_testnames.append(job.display_name)
                status = "CRASH"
                status_print = colors.PINK + status + colors.NORMAL

        print("[%d/%d]" % (passed_tests + failed_tests + skipped_tests + crashed_tests, total_tests), end=' ')
        if options.duration or options.constrain == "performance":
            print("%s (%.3f): %s %s" % (status_print, job.elapsed_time, kind, job.display_name))
        else:
            print("%s: %s %s" % (status_print, kind, job.display_name))

        if job.is_example or job.is_pyexample:
            #
            # Examples are the odd man out here.  They are written without any
            # knowledge that they are going to be run as a test, so we need to
            # cook up some kind of output for them.  We're writing an xml file,
            # so we do some simple XML that says we ran the example.
            #
            # XXX We could add some timing information to the examples, i.e. run
            # them through time and print the results here.
            #
            f = open(xml_results_file, 'a')
            f.write('<Example>\n')
            example_name = "  <Name>%s</Name>\n" % job.display_name
            f.write(example_name)

            if status == "PASS":
                f.write('  <Result>PASS</Result>\n')
            elif status == "FAIL":
                f.write('  <Result>FAIL</Result>\n')
            elif status == "VALGR":
                f.write('  <Result>VALGR</Result>\n')
            elif status == "SKIP":
                f.write('  <Result>SKIP</Result>\n')
            else:
                f.write('  <Result>CRASH</Result>\n')

            f.write('  <Time real="%.3f"/>\n' % job.elapsed_time)
            f.write('</Example>\n')
            f.close()

        else:
            #
            # If we're not running an example, we're running a test suite.如果我们不运行一个例子，我们运行一个测试套件。
            # These puppies are running concurrently and generating output that was written to a temporary file to avoid collisions.这些小程序并发运行并生成写入临时文件的输出，以避免冲突。
            # 
            #
            # Now that we are executing sequentially in the main thread, we can concatenate the contents of the associated temp file to the main results file and remove that temp file.
            # 现在我们在主线程中按顺序执行，我们可以将相关联的临时文件的内容连接到主结果文件并删除该临时文件。
            # 
            #
            # One thing to consider is that a test suite can crash just as well as any other program, so we need to deal with that possibility as well.  
            # 需要考虑的一件事是，一个测试套件可能像其他任何程序一样崩溃，因此我们也需要处理这种可能性。
            # If it ran correctly it will return 0 if it passed, or 1 if it failed.  如果运行正确，它将返回0如果它通过，或1如果它失败。
            # In this case, we can count on the results file it saved being complete.  
            # If it crashed, it  will return some other code, and the file should be considered corrupt and useless.  如果它崩溃了，它将返回一些其他的代码，并且文件应该被认为是损坏的和无用的。
            #
            # If the suite didn't create any XML, then we're going to have to do it ourselves.
            # 如果这个套件没有创建任何 XML，那么我们将不得不自己动手。
            #
            # Another issue is how to deal with a valgrind error.  另外一个问题是如何处理 valground 错误。
            # If we run a test suite under valgrind and it passes, we will get a return code of 0 and there will be a valid xml results file since the code ran to completion.  
            # 如果我们运行了一个测试套件，它通过，我们将得到一个0的返回代码，并且将有一个有效的 xml 结果文件，因为代码运行到完成。
            # If we get a return code of 1 under valgrind,the test case failed, but valgrind did not find any problems so the test case return code was passed through.  
            # 如果我们得到的返回代码是1，那么测试用例失败了，但是 val弓没有发现任何问题，所以测试用例返回代码被传递了。
            # We will have a valid xml results file here as well since the test suite ran. 自从测试套件运行以来，这里也有一个有效的 xml 结果文件。
            # If we see a
            # return code of 2, this means that valgrind found an error (we asked
            # it to return 2 if it found a problem in run_job_synchronously) but
            # the suite ran to completion so there is a valid xml results file.
            # If the suite crashes under valgrind we will see some other error
            # return code (like 139).  If valgrind finds an illegal instruction or
            # some other strange problem, it will die with its own strange return
            # code (like 132).  However, if the test crashes by itself, not under
            # valgrind we will also see some other return code.
            #
            # If the return code is 0, 1, or 2, we have a valid xml file.  If we
            # get another return code, we have no xml and we can't really say what
            # happened -- maybe the TestSuite crashed, maybe valgrind crashed due
            # to an illegal instruction.  If we get something beside 0-2, we assume
            # a crash and fake up an xml entry.  After this is all done, we still
            # need to indicate a valgrind error somehow, so we fake up an xml entry
            # with a VALGR result.  Thus, in the case of a working TestSuite that
            # fails valgrind, we'll see the PASS entry for the working TestSuite
            # followed by a VALGR failing test suite of the same name.
            #
            '''这段代码注释描述了在运行测试套件时处理Valgrind错误的策略。Valgrind是一个用于检测内存泄漏和内存错误的工具，而这段注释主要关注在测试套件运行中的Valgrind返回代码和结果文件的处理。
                
                1. **Valgrind返回代码的解释：**
                   - 如果Valgrind返回代码是0，表示测试套件通过，并且有一个有效的XML结果文件，因为代码正常运行完成。
                   - 如果返回代码是1，表示测试用例失败，但Valgrind未发现问题，所以测试用例的返回代码被传递。同样，会有一个有效的XML结果文件。
                   - 如果返回代码是2，表示Valgrind发现了错误，但测试套件仍然正常运行，因此同样存在一个有效的XML结果文件。
                
                2. **其他Valgrind返回代码的处理：**
                   - 如果Valgrind返回代码不是0、1或2，说明发生了一些异常情况，如测试套件崩溃或Valgrind由于非法指令而崩溃。在这种情况下，无法确定发生了什么，但为了表示发生了崩溃，会伪造一个XML条目。
                
                3. **VALGR结果的处理：**
                   - 无论上述情况如何，最终需要指示Valgrind错误，因此会伪造一个带有VALGR结果的XML条目。这确保在测试通过但Valgrind失败的情况下，会在结果中看到通过的测试套件后跟着同名的Valgrind失败的测试套件。
                
                这种处理策略确保在测试过程中能够有效地处理Valgrind的不同返回情况，同时生成一致的XML结果文件，以便更好地了解测试套件的执行状态。
            '''
            if job.is_skip:
                f = open(xml_results_file, 'a')
                f.write("<Test>\n")
                f.write("  <Name>%s</Name>\n" % job.display_name)
                f.write('  <Result>SKIP</Result>\n')
                f.write("  <Reason>%s</Reason>\n" % job.skip_reason)
                f.write("</Test>\n")
                f.close()
            else:
                if job.returncode == 0 or job.returncode == 1 or job.returncode == 2:
                    f_to = open(xml_results_file, 'a')
                    f_from = open(job.tmp_file_name)
                    f_to.write(f_from.read())
                    f_to.close()
                    f_from.close()
                else:
                    f = open(xml_results_file, 'a')
                    f.write("<Test>\n")
                    f.write("  <Name>%s</Name>\n" % job.display_name)
                    f.write('  <Result>CRASH</Result>\n')
                    f.write("</Test>\n")
                    f.close()

    #
    # We have all of the tests run and the results written out.  One final
    # bit of housekeeping is to wait for all of the threads to close down
    # so we can exit gracefully.
    #
    for thread in threads:
        thread.join()

    #
    # Back at the beginning of time, we started the body of an XML document
    # since the test suites and examples were going to just write their
    # individual pieces.  So, we need to finish off and close out the XML
    # document
    #
    f = open(xml_results_file, 'a')
    f.write('</Results>\n')
    f.close()

    #
    # Print a quick summary of events
    #
    print("%d of %d tests passed (%d passed, %d skipped, %d failed, %d crashed, %d valgrind errors)" % (passed_tests,
        total_tests, passed_tests, skipped_tests, failed_tests, crashed_tests, valgrind_errors))
    #
    # Repeat summary of skipped, failed, crashed, valgrind events
    #
    if skipped_testnames:
        skipped_testnames.sort()
        print('List of SKIPped tests:\n    %s' % '\n    '.join(map(str, skipped_testnames)))
    if failed_testnames:
        failed_testnames.sort()
        print('List of FAILed tests:\n    %s' % '\n    '.join(map(str, failed_testnames)))
    if crashed_testnames:
        crashed_testnames.sort()
        print('List of CRASHed tests:\n    %s' % '\n    '.join(map(str, crashed_testnames)))
    if valgrind_testnames:
        valgrind_testnames.sort()
        print('List of VALGR failures:\n    %s' % '\n    '.join(map(str, valgrind_testnames)))
    #
    # The last things to do are to translate the XML results file to "human
    # readable form" if the user asked for it (or make an XML file somewhere)
    #
    if len(options.html) + len(options.text) + len(options.xml):
        print()

    if len(options.html):
        translate_to_html(xml_results_file, options.html)

    if len(options.text):
        translate_to_text(xml_results_file, options.text)

    if len(options.xml):
        xml_file = options.xml + '.xml'
        print('Writing results to xml file %s...' % xml_file, end='')
        shutil.copyfile(xml_results_file, xml_file)
        print('done.')

    #
    # Let the user know if they need to turn on tests or examples.
    #
    if not ENABLE_TESTS or not ENABLE_EXAMPLES:
        print()
        if not ENABLE_TESTS:
            print('***  Note: ns-3 tests are currently disabled. Enable them by adding')
            print('***  "--enable-tests" to ./waf configure or modifying your .ns3rc file.')
            print()
        if not ENABLE_EXAMPLES:
            print('***  Note: ns-3 examples are currently disabled. Enable them by adding')
            print('***  "--enable-examples" to ./waf configure or modifying your .ns3rc file.')
            print()

    #
    # Let the user know if they tried to use valgrind but it was not
    # present on their machine.
    #
    if options.valgrind and not VALGRIND_FOUND:
        print()
        print('***  Note: you are trying to use valgrind, but valgrind could not be found')
        print('***  on your machine.  All tests and examples will crash or be skipped.')
        print()

    #
    # If we have been asked to retain all of the little temporary files, we
    # don't delete tm.  If we do delete the temporary files, delete only the
    # directory we just created.  We don't want to happily delete any retained
    # directories, which will probably surprise the user.
    #
    '''这段注释描述了在处理临时文件时的删除策略。根据注释内容，删除策略分为两种情况：
        1. **保留所有小临时文件：**
           - 如果程序被要求保留所有小临时文件，则不会删除 `tm` 目录。
           - 换句话说，如果存在指令要求保留所有生成的临时文件，那么不会执行删除操作。   
        2. **仅删除刚创建的目录：**
           - 如果程序不需要保留所有小临时文件，只删除刚创建的目录。
           - 这意味着在其他情况下，仅删除最近创建的临时目录，而不删除任何已经被指示保留的目录。
           - 避免意外删除用户可能希望保留的目录，确保删除操作不会影响保留的目录。        
        这种删除策略的设计是为了平衡在测试或程序运行过程中产生的临时文件的管理。如果用户明确要求保留这些文件，系统会保留它们；
        否则，系统会删除其中一些，但不会删除用户可能希望保留的文件。这有助于避免对用户的不必要干扰和意外删除可能有用的文件。
    '''
    if not options.retain:
        shutil.rmtree(testpy_output_dir)

    if passed_tests + skipped_tests == total_tests:
        return 0 # success
    else:
        return 1 # catchall for general errors

def main(argv):
    parser = optparse.OptionParser()
    parser.add_option("-b", "--buildpath", action="store", type="string", dest="buildpath", default="",
                      metavar="BUILDPATH",
                      help="specify the path where ns-3 was built (defaults to the build directory for the current variant)")

    parser.add_option("-c", "--constrain", action="store", type="string", dest="constrain", default="",
                      metavar="KIND",
                      help="constrain the test-runner by kind of test")

    parser.add_option("-d", "--duration", action="store_true", dest="duration", default=False,
                      help="print the duration of each test suite and example")

    parser.add_option("-e", "--example", action="store", type="string", dest="example", default="",
                      metavar="EXAMPLE",
                      help="specify a single example to run (no relative path is needed)")

    parser.add_option("-u", "--update-data", action="store_true", dest="update_data", default=False,
                      help="If examples use reference data files, get them to re-generate them")

    parser.add_option("-f", "--fullness", action="store", type="choice", dest="fullness", default="QUICK",
                      metavar="FULLNESS", choices=["QUICK", "EXTENSIVE", "TAKES_FOREVER"],
                      help="choose the duration of tests to run: QUICK, EXTENSIVE, or TAKES_FOREVER, where EXTENSIVE includes QUICK and TAKES_FOREVER includes QUICK and EXTENSIVE (only QUICK tests are run by default)")

    parser.add_option("-g", "--grind", action="store_true", dest="valgrind", default=False,
                      help="run the test suites and examples using valgrind")

    parser.add_option("-k", "--kinds", action="store_true", dest="kinds", default=False,
                      help="print the kinds of tests available")

    parser.add_option("-l", "--list", action="store_true", dest="list", default=False,
                      help="print the list of known tests")

    parser.add_option("-m", "--multiple", action="store_true", dest="multiple", default=False,
                      help="report multiple failures from test suites and test cases")

    parser.add_option("-n", "--nowaf", action="store_true", dest="nowaf", default=False,
                      help="do not run waf before starting testing")

    parser.add_option("-p", "--pyexample", action="store", type="string", dest="pyexample", default="",
                      metavar="PYEXAMPLE",
                      help="specify a single python example to run (with relative path)")

    parser.add_option("-r", "--retain", action="store_true", dest="retain", default=False,
                      help="retain all temporary files (which are normally deleted)")

    parser.add_option("-s", "--suite", action="store", type="string", dest="suite", default="",
                      metavar="TEST-SUITE",
                      help="specify a single test suite to run")

    parser.add_option("-t", "--text", action="store", type="string", dest="text", default="",
                      metavar="TEXT-FILE",
                      help="write detailed test results into TEXT-FILE.txt")

    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                      help="print progress and informational messages")

    parser.add_option("-w", "--web", "--html", action="store", type="string", dest="html", default="",
                      metavar="HTML-FILE",
                      help="write detailed test results into HTML-FILE.html")

    parser.add_option("-x", "--xml", action="store", type="string", dest="xml", default="",
                      metavar="XML-FILE",
                      help="write detailed test results into XML-FILE.xml")

    parser.add_option("--nocolor", action="store_true", dest="nocolor", default=False,
                      help="do not use colors in the standard output")
    parser.add_option("--jobs", action="store", type="int", dest="process_limit", default=0,
                      help="limit number of worker threads")

    global options
    options = parser.parse_args()[0]
    signal.signal(signal.SIGINT, sigint_hook)

    # From waf/waflib/Options.py
    envcolor=os.environ.get('NOCOLOR','') and 'no' or 'auto' or 'yes'

    if options.nocolor or envcolor == 'no':
        colors_lst['USE'] = False

    return run_tests()

if __name__ == '__main__':
    sys.exit(main(sys.argv))
