
import os
import subprocess
import shutil

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
        self.test_config = self.TestConfig(test_config)
        self.source_config = self.SourceConfig(source_config)

        # full pathname to the directory containing all tests
        # e.g. /tests
        self.tests_dir = tests_dir

        # full pathname to the directory containing the solution
        # e.g. /solution
        self.solution_dir = solution_dir

        # e.g. /students/:eid/results/:test
        self.results_dir = os.path.join(self.source_config.student_dir, "results", self.test_config.dir)

        
        
        
    def run(self):
        # make the results dir
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

        # /tests/:test_dir/:input_file
        input_file = os.path.join(self.tests_dir, self.test_config.dir, self.test_config.input_file)
        input_str = ""
        with open(input_file, "r") as f:
            input_str = f.read()

        completed = subprocess.run(["java", "-cp", self.source_config.classpath, self.source_config.main], input=str.encode(input_str), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # handle results

        # copy the input file to the results directory
        input_file_copy = os.path.join(self.results_dir, self.test_config.input_file)
        shutil.copyfile(input_file, input_file_copy)
        
        # /students/:eid/submission/results/:test_dir/:output_file
        output_file = os.path.join(self.results_dir, self.test_config.output_file)
        with open(output_file, "w") as f:
            f.write(completed.stdout.decode())
        
        # /students/:eid/submission/results/:test_dir/err.txt
        err_file = os.path.join(self.results_dir, "err.txt")
        with open(err_file, "w") as f:
            f.write(completed.stderr.decode())

        # now write the solution result
    
    """
    Compare the results of the test run with the solution/expected result.
    """
    def compare(self):

        
        