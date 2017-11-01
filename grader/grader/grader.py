'''
Call this file like this: 'python check-files.py YOUR_ZIP_FILE.zip'.
Make sure this script at least finds all of the project files successfully.
You can ignore compile errors related to Problem3.java as that will be graded manually.
'''
import sys
import shutil
import os
import glob
import zipfile
import subprocess
import argparse
import yaml
import requests
import json

from test import Test

class Grader:
    def __init__(self, argv):
        # working directory is the previous directory

        self.parser = argparse.ArgumentParser(description = "Grader for simple Java applications")
        self.args = []

        self.argv = argv

        # configuration dictionary
        self.config = {}

        self.lms = {
            "base-url": "",

            # course url
            "course-url": "",

            # headers
            "headers": {
                "Authorization": ""
            }
        }

        self.assignment = {}

        # map of student id's (canvas id) to their student objects
        self.student_map = {}

        # map of student id;s (canvas id) to their submission objects
        self.submission_map = {}

        # dictionary of all directory names
        # only the dirs["grader"] directory should be absolute;
        # every other dir is relative to the grader dir
        self.dirs = {
            # base directory of the grader script
            "base": "",

            # directory that will contain submissions and results
            "students": "students",

            # students/:submission
            # student directory for submission download
            "submission": "submission",

            # students/:results
            # student directory for test results
            "results": "results",

            # directory containing the solution
            "solution": "solution",

            # tests directory
            "tests": "tests"
        }
    
    def init(self):
        # add arguments to the parser
        self.parser.add_argument(
            "-c", "--config",
            nargs=1,
            metavar="CONFIG_FILE.yaml",
            help = "YAML configuration file",
            required = True
        )

        self.args = self.parser.parse_args(self.argv[1:])
        print(self.args)
        
        config_file = self.args.config[0]
        with open(config_file) as f:
            config = yaml.load(f.read())

        self.config = config
        print(self.config)

        self.init_lms()
        self.init_dirs()
        self.init_students()
        self.init_submissions()        
    
    def init_lms(self):
        self.lms["base-url"] = self.config["canvas"]["base-url"]
        self.lms["course-url"] = self.lms["base-url"] + "/courses/" + str(self.config["canvas"]["course"])
        self.lms["headers"]["Authorization"] = "Bearer " + self.config["canvas"]["auth-token"]

        # get the assignment
        assignment_name = self.config["canvas"]["assignment"]
        url = self.lms["course-url"] + "/assignments"
        assignments = self.get_paginated_result(url, headers = self.lms["headers"])
        for assignment in assignments:
            if assignment.get("name") == assignment_name:
                self.assignment = assignment
                print("Found assignment: " + assignment_name)
                break
        
        if self.assignment == {}:
            print("Unable to find assignment with name: " + assignment_name)
            exit(1)
        
        self.lms["assignment-url"] = self.lms["course-url"] + "/assignments/" + str(self.assignment["id"])


    """
    Initializes all grader directories.
    """
    def init_dirs(self):
        # create the .grader/ configuration directory
        if not os.path.exists(".grader"):
            os.makedirs(".grader")

        self.dirs["grader"] = os.path.abspath(".")
        self.dirs["students"] = os.path.relpath(self.config["students-dir"])
        self.dirs["solution"] = os.path.relpath(self.config["solution"]["dir"])
        self.dirs["tests"] = os.path.relpath(self.config["tests"]["dir"])
        print(self.dirs)


    def init_students(self):
        students_json_file = os.path.join(".grader", "students.json")
        students = []

        # check for existing .grader/student.json file
        if (not os.path.exists(students_json_file)) or \
            (not self.is_valid_json_file(students_json_file)):

            print("Retrieving students from LMS.")

            # check if we are grading all students or just a subset
            if "students-subset" not in self.config:
                print("No subset of students specified; retrieving all students.")
                # get all students
                url = self.lms["course-url"] + "/users"
                params = {
                    "enrollment_type": ["student"]
                }
                students = self.get_paginated_result(
                    url = url, params=params, headers=self.lms["headers"])
            
            else:
                # add specified students
                if "students" in self.config["students-subset"]:
                    print("Getting specified students...")
                    custom_student_eids = self.config["students-subset"]["students"]
                    for eid in custom_student_eids:
                        url = self.lms["course-url"] + "/users"
                        params = {
                            "enrollment_type": ["student"],
                            "search_term": eid
                        }
                        r = requests.get(
                            url = url,
                            params = params,
                            headers = self.lms["headers"]
                        )

                        if r is None:
                            print("Warning: could not find student " + eid)
                            continue

                        student = r.json()[0]
                        students.append(student)

                # add students for specified sections
                if "sections" in self.config["students-subset"]:
                    print("Getting students in specified sections...")
                    section_utids = self.config["students-subset"]["sections"]
                    url = self.lms["course-url"] + "/sections"
                    params = {
                        "include": "students"
                    }
                    r = requests.get(
                        url = url,
                        headers = self.lms["headers"],
                        params = params
                    )
                    sections = r.json()
                    # find the sections based on their given section ut id's
                    for section in sections:
                        for section_utid in section_utids:
                            # append all students
                            if str(section_utid) in section["sis_section_id"]:
                                students.extend(section["students"])
                    


            # write to .grader/students.json file
            with open(students_json_file, "w") as f:
                f.write(json.dumps(students, indent=4))
        
        else:
            print("Using existing students.json file.")
            with open(students_json_file, "r") as f:
                students = json.loads(f.read())

        # create student map
        for student in students:
            self.student_map[student["id"]] = student
            # print(student["sis_user_id"])

        print("Found " + str(len(self.student_map.values())) + " students.")

        # make directories for all the students
        print("Making highest level student directory...")
        if not os.path.exists(self.dirs["students"]):
            os.makedirs(self.dirs["students"])

        print("Making directories for each student...")
        for student in students:
            student_eid = student["sis_user_id"]
            student_dir = os.path.join(self.dirs["students"], student_eid)
            if os.path.exists(student_dir):
                continue
                # shutil.rmtree(student_dir)

            # students/:eid
            os.makedirs(student_dir)

            # students/:eid/submission
            os.makedirs(os.path.join(student_dir, "submission"))

            # students/:eid/results
            os.makedirs(os.path.join(student_dir, "results"))
    
    def init_submissions(self):
        submissions_json_file = os.path.join(".grader", "submissions.json")
        submissions = []

        # check for existing .grader/submissions.json file
        if (not os.path.exists(submissions_json_file)) or \
            (not self.is_valid_json_file(submissions_json_file)):

            print("Retrieving submissions from LMS.")
            url = self.lms["assignment-url"] + "/submissions"
            all_submissions = self.get_paginated_result(
                url=url,
                headers=self.lms["headers"]
            )
            submissions = list(filter(lambda s: s["user_id"] in self.student_map, all_submissions))

            # write to json file
            with open(submissions_json_file, "w") as f:
                f.write(json.dumps(submissions, indent=4))
        
        else:
            print("Using existing submissions.json file.")
            with open(submissions_json_file, "r") as f:
                submissions = json.loads(f.read())
        
        # map each user's eid to the user's submission
        for submission in submissions:
            self.submission_map[submission["user_id"]] = submission
        
        print("Found " + str(len(submissions)) + " submissions.")
        assert(len(self.student_map) == len(self.submission_map))

    
    def download_submissions(self):
        for submission in self.submission_map.values():
            # skip if student did not submit
            if submission["workflow_state"] == "unsubmitted":
                continue

            attachment = submission["attachments"][0]
            attachment_url = attachment["url"]
            student_eid = self.student_map[submission["user_id"]]["sis_user_id"]
            # print(student_eid)

            filename = os.path.join(self.dirs["students"], student_eid, "submission.zip")

            # if the file already exists, skip it
            if os.path.exists(filename):
                continue

            r = requests.get(
                url=attachment_url,
                headers=self.lms["headers"],
                stream=True
            )

            with open(filename, "wb") as f:
                for chunk in r.iter_content(chunk_size=128):
                    f.write(chunk)


    def unzip_submissions(self):
        for student in self.student_map.values():
            zip_filename = os.path.join(self.dirs["students"], student["sis_user_id"], "submission.zip")

        
            print("Zip file is " + zip_filename)
            if not zipfile.is_zipfile(zip_filename):
                print("Not a proper zip file, or file not found.")
                continue

            zip_file = zipfile.ZipFile(zip_filename, 'r')
            zip_file.extractall(path=os.path.join(self.dirs["students"], student["sis_user_id"], "submission"))

            # delete macos files
            macos_dir = os.path.join(self.dirs["students"], student["sis_user_id"], "submission", "__MACOSX")
            if os.path.exists(macos_dir):
                shutil.rmtree(macos_dir)
                
            zip_file.close()

    """
    Compile the source files for every student as well as the solution.
    """
    def compile_sources(self):
        source = self.config["source"]
        # for source in sources:
        source_files = source["files"]
        for student in self.student_map.values():
            print("Looking at student " + student["sis_user_id"])
            compile_result_file = os.path.join(self.dirs["students"], student["sis_user_id"], "results", "compile.txt")
            student_files = []
            source_path = os.path.join(self.dirs["students"], student["sis_user_id"], "submission")

            if type(source_files) is str and source_files == "*":
                matched_files = glob.glob(os.path.join(source_path, "**", "*.java"), recursive=True)
                student_files.extend(matched_files)

            if type(source_files) is list:
                for file in source_files:
                    matched_files = glob.glob(os.path.join(source_path, "**", file), recursive=True)
                    student_files.extend(matched_files)

            # compile student files
            # for file in student_files:
            print("Found files: " + str(["javac"] + student_files))
            completed = subprocess.run(["javac"] + student_files)
            if completed.returncode == 0:
                print("Compiled successfully.")
            else:
                print("Failed to compile.")
        
        print("Compiling solution files...")
        solution_files = []
        for file in source_files:
            matched_files = glob.glob(os.path.join(self.dirs["solution"], "**", file))
            solution_files.extend(matched_files)
        

        for file in solution_files:
            completed = subprocess.run(["javac", file])
            if completed.returncode == 0:
                print("Compiled successfully.: " + file)
            else:
                print("Failed to compile: " + file)

    
    def run_tests(self):
        tests_dir = self.config["tests"]["dir"]            
        # test_configs = self.config["tests"]["tests"]

        for student in self.student_map.values():
            print("Running tests for student: " + student["sis_user_id"])

            student_dir = os.path.join(self.dirs["students"], student["sis_user_id"])
            source_dir = os.path.join(student_dir, "submission")
            results_dir = os.path.join(student_dir, "results")

            # first clean the student directory
            if os.path.exists(results_dir):
                shutil.rmtree(results_dir)
            os.makedirs(results_dir)
            # create summary file
            open(os.path.join(student_dir, "results", "summary.txt"), "w+")
        
            for test_dirname in os.listdir(self.dirs["tests"]):
                test_dir = os.path.join(self.dirs["tests"], test_dirname)
                print(test_dir)
                main_class = self.config["source"]["main"]
                classpath = self.get_classpath(student_dir, main_class)
                test = Test(
                    test_config = "",
                    source_config = {
                        "student-dir": student_dir,
                        "main": main_class,
                        "classpath": classpath
                    },
                    tests_dir = self.dirs["tests"]
                )

        return

        # first run the solution
        solution_dir = self.dirs["solution"]

        for test_config in test_configs:
            main_class = test_config["main"]
            classpath = self.get_classpath(self.dirs["solution"], main_class)
            test = Test(
                test_config = test_config,
                source_config = {
                    "student-dir": self.dirs["solution"],
                    "main": main_class,
                    "classpath": classpath
                },
                tests_dir = self.dirs["tests"],
                solution_dir = self.dirs["solution"]
            )

            test.run()

        for student in self.student_map.values():
            print("Running tests for student: " + student["sis_user_id"])

            student_dir = os.path.join(self.dirs["students"], student["sis_user_id"])
            source_dir = os.path.join(student_dir, "submission")

            # first clean the student directory
            results_dir = os.path.join(student_dir, "results")
            if os.path.exists(results_dir):
                shutil.rmtree(results_dir)
            os.makedirs(results_dir)
            # create summary file
            open(os.path.join(student_dir, "results", "summary.txt"), "w+")

            # run all tests
            for test_config in test_configs:
                main_class = test_config["main"]
                classpath = self.get_classpath(source_dir, main_class)
                # change the path to the test to be relative to the cwd
                # test_config["dir"] = os.path.join(self.dirs["tests"], test_config["dir"])
                test = Test(
                    test_config = test_config,
                    source_config = {
                        "student-dir": student_dir,
                        "main": main_class,
                        "classpath": classpath
                    },
                    tests_dir = self.dirs["tests"],
                    solution_dir = self.dirs["solution"]
                )

                test.run()
                test.compare()
                test.grade()
    
    def zip_results(self):
        for student in self.student_map.values():
            results_dir = os.path.join(self.dirs["students"], student["sis_user_id"], "results")

            zip_filename = os.path.join(results_dir, "results.zip")
            if os.path.exists(zip_filename):
                os.remove(zip_filename)
        
            print("Zip file is " + zip_filename)

            with zipfile.ZipFile(zip_filename, "w") as z:
                for file in glob.glob(os.path.join(results_dir, "**\*"), recursive=True):
                    # don't write ourselves
                    if str(file) == zip_filename:
                        continue

                    # write files relative to the results directory path
                    z.write(file, arcname=os.path.relpath(file, results_dir))
                

    def attach_results(self):
        for student in self.student_map.values():
            student["id"]


    """
    Perform multiple paginated GET requests and return the combined result.
    """
    def get_paginated_result(self, url, headers = {}, params = {}):
        params["per_page"] = 100
        # make the first request
        r = requests.get(
            url = url,
            headers = headers,
            params = params
        )

        res = r.json()

        # make the rest of the requests
        while (r.links["current"]["url"] != r.links["last"]["url"]):
            # get the next request, THEN append to the result
            # we do this since we already have the first request done
            r = requests.get(
                url = r.links["next"]["url"],
                headers = headers,
                params = params
                )
            res.extend(r.json())

        return res

    def is_valid_json_file(self, json_file):
        json_str = ""
        with open(json_file,"r") as f:
            json_str = f.read()
        
        return self.is_valid_json_str(json_str)
    
    def is_valid_json_str(self, json_str):
        try:
            json_obj = json.loads(json_str)
            return True

        except ValueError:
            return False
    

    def get_classpath(self, dir, main_class):
        classpath = ""
        if '.' in main_class:
            # search for the highest-level package directory
            classpath_matches = glob.glob(os.path.join(dir, "**", main_class.split('.')[0]), recursive=True)
            classpath = os.path.join(classpath_matches[0], "..")
        else:
            # search for the main java file
            # print(os.path.join(dir, "**", main_class))
            classpath_matches = glob.glob(os.path.join(dir, "**", main_class + ".java"), recursive=True)
            classpath = os.path.join(classpath_matches[0], "..")

        return classpath


        
    
    """
    Runs the grader.
    """
    def start(self):
        self.init()
        # self.download_submissions()
        # self.unzip_submissions()
        # self.compile_sources()
        self.run_tests()
        # self.zip_results()

    
    def clean(self):
        print("Cleaning grader directories and files...")
        # shutil.rmtree(os.path.abspath("./results"))

def main(args):
    grader = Grader(args)
    grader.start()
    grader.clean()


if __name__ == "__main__":
    print(sys.argv)
    main(sys.argv)
