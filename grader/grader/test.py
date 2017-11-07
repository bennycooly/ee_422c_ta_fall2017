
import os
import subprocess
import shutil
import difflib
import signal
import yaml
import re
from contextlib import contextmanager

from java import JavaUtils

class TestConfig:
    def __init__(self, tests_dir, test_dir_basename):
        self.name = ""

        # the full path to the tests directory
        # e.g. /tests
        self.tests_dir = tests_dir

        # directory name of the test inside the tests directory
        # not a full path, just the name of the directory
        # e.g. for the test /tests/provided, self.dir should be set to "provided"
        self.test_dir_basename = test_dir_basename

        # :tests_dir/:test_dir_basename
        self.test_dir = os.path.join(tests_dir, test_dir_basename)

        # :test_dir/:input_filename
        self.input_file = ""

        # :test_dir/:output_filename
        self.output_file = ""

        # :test_dir/:solution_filename
        self.solution_file = ""

        # :test_dir/:regex_filename
        self.regex_file = ""

        # e.g. [{ src: "Src.java", dst: "dir", "replace": True }, { src: "Src2.java", dst: "dir/Src2.java", "replace": False }]
        # the "src" file will be searched for in the test directory
        # the "dst" file/directory will be searched for in the source classpath
        # "replace" indicates if the file should overwrite the file in the student's directory, if it exists
        self.copy_entries = {}

class SourceConfig:
    def __init__(self, student_dir, main_class):
        # full pathname to the student's home directory
        # e.g. /students/:eid
        self.student_dir = student_dir

        # :student_dir/submission
        self.source_dir = os.path.join(student_dir, "submission")

        self.main = main_class
        self.classpath = ""
        self.args = []

class ResultConfig:
    def __init__(self, student_dir):
        # :student_dir/results
        self.results_dir = os.path.join(student_dir, "results")

        # :results_dir/:test_dir_basename/compile.txt
        self.compile_file = ""
        
        # :results_dir/:test_dir_basename/:output_file
        self.output_file = ""     

        # :results_dir/:test_dir_basename/err.txt
        self.error_file = ""

        # :results_dir/:test_dir_basename/diff.txt
        self.diff_file = ""

        # :results_dir/summary.txt
        self.summary_file = ""

class Result:
    def __init__(self):
        self.status = ""

"""
The Test class represents a single I/O test. This class will generate all necessary files (input, output, error)
in the results directory of the specified student.
"""
class Test:
    num_matched = 0

    def __init__(self, tests_dir, test_dir_basename, student_dir, main_class):
        """Constructor
        :param str tests_dir: The full pathname to the tests directory, e.g. /tests
        :param str test_dir_basename: The directory name of the test to run, e.g. test1
        :param str student_dir: The full pathname to the student home directory, e.g. /students/:eid
        :param str main_class: The fully qualified name of the main class, e.g. "assignment2.Main". Can be "find", which means we will search for it
        """
        self.test_config = TestConfig(tests_dir, test_dir_basename)
        self.source_config = SourceConfig(student_dir, main_class)
        self.result_config = ResultConfig(student_dir)
        self.status = ""

    def load_config(self):
        print("Loading test configuration files...")

        # load common test configuration
        common_test_config_file = os.path.join(self.test_config.tests_dir, "test.yaml")
        common_test_config = {}
        with open(common_test_config_file, "r") as f:
            common_test_config = yaml.load(f)
        
        print("Common test config: " + str(common_test_config))

        test_config_file = os.path.join(self.test_config.test_dir, "test.yaml")
        test_config = {}
        with open(test_config_file, "r") as f:
            test_config = yaml.load(f)
        
        # merge the test config with the common test config
        # order matters: specific test config entries should replace common test config entries
        test_config = dict(**common_test_config, **test_config)
        
        print("Merged config: " + str(test_config))

        # Test configuration
        self.test_config.name = test_config.get("name")
        # :test_dir/:input_file
        self.test_config.input_file = os.path.join(self.test_config.test_dir, test_config.get("input"))

        # :test_dir/:solution_file
        self.test_config.solution_file = os.path.join(self.test_config.test_dir, test_config.get("solution"))

        # :test_dir/:regex_file
        self.test_config.regex_file = os.path.join(self.test_config.test_dir, test_config.get("regex"))

        self.test_config.copy_entries = test_config.get("copy")

        # Source configuration
        # attempt to fix directory structure automatically
        JavaUtils.fix_directory_structure(self.source_config.student_dir, "assignment2")
        # check if we need to find the main file
        if self.source_config.main == "find":
            self.source_config.main = JavaUtils.find_main(self.source_config.source_dir)
            print("Main class: " + self.source_config.main)
        
        self.source_config.classpath = JavaUtils.get_classpath(self.source_config.source_dir, self.source_config.main)
        print("Classpath: " + self.source_config.classpath)

        self.source_config.args = test_config.get("args")

        # Result configuration
        # :results_dir/:test_dir_basename/compile.txt
        self.result_config.compile_file = os.path.join(self.result_config.results_dir, self.test_config.test_dir_basename, "compile.txt")
        
        # :results_dir/:test_dir_basename/:output_file
        self.result_config.output_file = os.path.join(self.result_config.results_dir, self.test_config.test_dir_basename, test_config.get("output"))   

        # :results_dir/:test_dir_basename/err.txt
        self.result_config.error_file = os.path.join(self.result_config.results_dir, self.test_config.test_dir_basename, "err.txt")

        # :results_dir/:test_dir_basename/diff.txt
        self.result_config.diff_file = os.path.join(self.result_config.results_dir, self.test_config.test_dir_basename, "diff.txt")

        # :results_dir/summary.txt
        self.result_config.summary_file = os.path.join(self.result_config.results_dir, "summary.txt")


    # copy a file from the test directory to the student directory
    def copy_files(self):
        if self.test_config.copy_entries is None:
            print("No files to copy.")
            return

        print("Copying files...")
        # each copy_entry is a dictionary that contains "src" and "dst"
        for copy_entry in self.test_config.copy_entries:
            file_to_copy = os.path.join(self.test_config.test_dir, copy_entry["src"])
            dst = os.path.join(self.source_config.classpath, copy_entry["dst"])
            if not os.path.exists(dst):
                print("Incorrect directory structure.")
                with open(self.result_config.summary_file, "w") as f:
                    f.write("Incorrect directory structure.")
                return
            # check if we need to replace the file or not
            if copy_entry["replace"]:
                res_path = shutil.copy(file_to_copy, dst)
                print("Copied file: " + res_path)
            else:
                if os.path.exists(os.path.join(dst, copy_entry["src"])):
                    print("File exists, and config indicates to not replace the file: " + file_to_copy)
                else:
                    res_path = shutil.copy(file_to_copy, dst)
                    print("Copied file: " + res_path)
    
    # compile the files
    def compile(self):
        completed_process = JavaUtils.compile(self.source_config.classpath)
        with open(self.result_config.compile_file, "w") as f:
            if completed_process.returncode == 0:
                f.write(completed_process.stdout)
            else:
                f.write(completed_process.stderr)
        print(completed_process)
       
        
    def run(self):
        print("Running test " + self.test_config.test_dir_basename + "...")
        # read and load the configurations
        self.load_config()

        # make the results dir and its test subdirectory
        if not os.path.exists(self.result_config.results_dir):
            os.makedirs(self.result_config.results_dir)
        
        results_test_subdir = os.path.join(self.result_config.results_dir, self.test_config.test_dir_basename)
        if not os.path.exists(results_test_subdir):
            os.makedirs(results_test_subdir)
        
        # copy files and then compile
        self.copy_files()
        self.compile()

        input_str = ""
        with open(self.test_config.input_file, "r") as f:
            input_str = f.read()

        completed = subprocess.run(["java", "-cp", self.source_config.classpath, self.source_config.main] + self.source_config.args, input=input_str, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        # handle results

        # copy the input file to the results directory
        shutil.copy(self.test_config.input_file, os.path.join(self.result_config.results_dir, self.test_config.test_dir_basename))

        # copy the solution file to the student's directory
        shutil.copy(self.test_config.solution_file, os.path.join(self.result_config.results_dir, self.test_config.test_dir_basename))

        # copy the regex file to the student's directory
        if self.test_config.regex_file:
            shutil.copy(self.test_config.regex_file, os.path.join(self.result_config.results_dir, self.test_config.test_dir_basename))

        with open(self.result_config.output_file, "w") as f:
            f.write(completed.stdout)
        
        with open(self.result_config.error_file, "w") as f:
            f.write(completed.stderr)

        # now write the solution result
        self.compare()

        # summarize
        self.summarize()

        return self.status
    
    """
    Compare the results of the test run with the solution/expected result.
    """
    def compare(self):
        # use regex
        if self.test_config.regex_file:
            with open(self.test_config.regex_file, "r") as f_regex, \
                open(self.result_config.output_file, "r") as f_out, \
                open(self.result_config.diff_file, "w") as f_diff:

                matches = ""
                
                try:
                    with time_limit(5):
                        matches = re.search(f_regex.read(), f_out.read())
                
                except TimeoutError as e:
                    f_diff.write("Timeout when comparing regex. Check the output and soluton files.")
                    return

                if matches is None:
                    print("No match.")
                    f_diff.write("Output did not match the solution regex.")
                    return
                
                print("matched!")
                Test.num_matched += 1
                self.status = "pass"
        
        # use straight diff comparison
        else:
            with open(self.test_config.solution_file, "r") as f_sol, \
                open(self.result_config.output_file, "r") as f_out, \
                open(self.result_config.diff_file, "w") as f_diff:
                diffs = difflib.unified_diff(f_sol.read().strip(), f_out.read().strip(), fromfile=self.result_config.output_file, tofile=self.test_config.solution_file)
                diffs_list = list(diffs)
                print(str(diffs_list))
                f_diff.writelines(diffs_list)

        
    
    def summarize(self):
        with open(self.result_config.diff_file, "r") as f, open(self.result_config.summary_file, "a") as f_sum:
            f_sum.write("==============================================================\n")
            f_sum.write("Test Name:\t" + self.test_config.name + "\n")
            f_sum.write("Test Directory:\t" + self.test_config.test_dir_basename + "\n")
            diffs = f.read().strip()
            if diffs == "":
                print("no differences!")
                f_sum.writelines("Result:\tPassed\n")
            else:
                f_sum.writelines("Result:\tFailed\n")
        
        print("num matched: " + str(Test.num_matched))


@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutError("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
