
import os
import subprocess
from subprocess import SubprocessError
import shutil
import difflib

"""
The Test class represents a single I/O test. This class will generate all necessary files (input, output, error)
in the results directory of the specified student.
"""
class Test:
    class TestConfig:
        def __init__(self, config):
            self.name = config["name"]

            # directory name of the test inside the tests directory
            # not a full path, just the name of the directory
            # e.g. for the test /tests/provided, self.dir should be set to "provided"
            self.dir = config["dir"]

            self.input_file = config["input"]
            self.output_file = config["output"]
            self.solution_file = config["solution"]
    
    class SourceConfig:
        def __init__(self, config):
            # full pathname to the student's home directory
            # e.g. /students/:eid
            self.student_dir = config["student-dir"]

            self.main = config["main"]
            self.classpath = config["classpath"]

    def __init__(self, test_config, source_config, tests_dir, solution_dir):
        if type(test_config) is TestConfig:
            self.test_config = test_config
        elif type(test_config) is dict:
            self.test_config = self.TestConfig(test_config)
        
        if type(source_config) is SourceConfig:
            self.source_config = source_config
        elif type(source_config) is dict:
            self.source_config = self.SourceConfig(source_config)

        # full pathname to the directory containing all tests
        # e.g. /tests
        self.tests_dir = tests_dir

        # full pathname to the directory containing the solution
        # e.g. /solution
        self.solution_dir = solution_dir

        # e.g. /students/:eid/submission/results
        self.results_dir = os.path.join(self.source_config.student_dir, "results")

        # set the files
        
        # /tests/:test_dir/:input_file
        self.input_file = os.path.join(self.tests_dir, self.test_config.dir, self.test_config.input_file)
        
        # /students/:eid/submission/results/:test_dir/:output_file
        self.output_file = os.path.join(self.results_dir, self.test_config.dir, self.test_config.output_file)

        # /students/:eid/submission/results/:test_dir/err.txt
        self.error_file = os.path.join(self.results_dir, self.test_config.dir, "err.txt")

        # /students/:eid/submission/results/:test_dir/diff.txt
        self.diff_file = os.path.join(self.results_dir, self.test_config.dir, "diff.txt")

        # /students/:eid/submission/results/summary.txt
        self.summary_file = os.path.join(self.results_dir, "summary.txt")

        # /solution/results/:output_file
        self.solution_file = os.path.join(self.solution_dir, "results", self.test_config.dir, self.test_config.output_file)

       
        
    def run(self):
        # make the results dir
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
        
        if not os.path.exists(os.path.dirname(self.output_file)):
            os.makedirs(os.path.dirname(self.output_file))

        
        input_str = ""
        with open(self.input_file, "r") as f:
            input_str = f.read()

        completed = subprocess.run(["java", "-cp", self.source_config.classpath, self.source_config.main], input=input_str, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        # handle results

        # copy the input file to the results directory
        input_file_copy = os.path.join(self.results_dir, self.test_config.dir, self.test_config.input_file)
        shutil.copyfile(self.input_file, input_file_copy)

        with open(self.output_file, "w") as f:
            f.write(completed.stdout)
        
        
        with open(self.error_file, "w") as f:
            f.write(completed.stderr)

        # now write the solution result
    
    """
    Compare the results of the test run with the solution/expected result.
    """
    def compare(self):
        # copy the solution file to the student's directory
        solution_copy = os.path.join(self.results_dir, self.test_config.dir, "sol.txt")
        shutil.copyfile(self.solution_file, solution_copy)

        with open(solution_copy, "r") as f_sol, \
                open(self.output_file, "r") as f_out, \
                open(self.diff_file, "w") as f_diff:

            diffs = difflib.unified_diff(f_sol.read().strip(), f_out.read().strip(), fromfile=self.output_file, tofile=solution_copy)
            diffs_list = list(diffs)
            print(str(diffs_list))
            f_diff.writelines(diffs_list)
    
    def grade(self):
        with open(self.diff_file, "r") as f, open(self.summary_file, "a") as f_sum:
            diffs = f.read().strip()
            if diffs == "":
                print("no differences!")
                f_sum.writelines(self.test_config.name + ": Passed\n")
            else:
                f_sum.writelines(self.test_config.name + ": Failed\n")
            
    

        