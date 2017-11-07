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
import multiprocessing as mp

from java import JavaUtils
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

        # map of student id's (canvas id) to their submission objects
        self.submission_map = {}

        # map of student id's (canvas id) to their test results
        self.results_map = {}

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
        self.parser.add_argument(
            "-s", "--single-student",
            nargs=1,
            metavar="STUDENT_EID",
            help = "Student EID"
        )
        self.parser.add_argument(
            "-u", "--update",
            action="store_true",
            help = "Regrade and update grades"
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
        if os.path.exists(students_json_file) and self.is_valid_json_file(students_json_file):
            print("Using existing students.json file.")
            with open(students_json_file, "r") as f:
                students = json.loads(f.read())
        
        else:
            print("Retrieving students from LMS.")
            # get all students
            url = self.lms["course-url"] + "/users"
            params = {
                "enrollment_type": ["student"]
            }
            students = self.get_paginated_result(
                url = url, params=params, headers=self.lms["headers"]
            )
            # write to .grader/students.json file
            with open(students_json_file, "w") as f:
                f.write(json.dumps(students, indent=4))
            
            print("Saved students to " + students_json_file)
        
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
        
        ## Filter students if requested
        # check if we are grading all students or just a subset
        if "students-subset" in self.config:
            students_subset = []
            # add specified students
            if "students" in self.config["students-subset"]:
                print("Getting specified students...")
                custom_student_eids = self.config["students-subset"]["students"]
                # for eid in custom_student_eids:
                    
                #     students.append(student)
                filtered_students = list(filter(lambda s: s.get("sis_user_id") in custom_student_eids, students))
                students_subset.extend(filtered_students)
                # print(students_subset)

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
                            students_subset.extend(section["students"])
            
            students = students_subset

        # create student map
        for student in students:
            self.student_map[student["id"]] = student
            # print(student["sis_user_id"])

        print("Grading " + str(len(self.student_map.values())) + " students.")
    
    def init_submissions(self):
        submissions_json_file = os.path.join(".grader", "submissions.json")
        submissions = []

        # check for existing .grader/submissions.json file
        if os.path.exists(submissions_json_file) and self.is_valid_json_file(submissions_json_file):
            print("Using existing submissions.json file.")
            with open(submissions_json_file, "r") as f:
                submissions = json.loads(f.read())

        else:
            print("Retrieving submissions from LMS.")
            url = self.lms["assignment-url"] + "/submissions"
            all_submissions = self.get_paginated_result(
                url=url,
                headers=self.lms["headers"]
            )
            submissions.extend(all_submissions)

            # write to json file
            with open(submissions_json_file, "w") as f:
                f.write(json.dumps(submissions, indent=4))
        
        # we only look at the submissions of the students we need to grade
        submissions_subset = list(filter(lambda sub: sub.get("user_id") in self.student_map, submissions))

        submissions = submissions_subset
        
        # map each user's eid to the user's submission
        for submission in submissions:
            if submission.get("workflow_state") == "unsubmitted":
                self.student_map.pop(submission.get("user_id"))
                continue
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

    # try to fix package related directory structures
    
    def run_tests(self):
        tests_dir = self.config["tests"]["dir"]

        results_json = os.path.join(".grader", "results.json")

        if os.path.exists(results_json) and self.is_valid_json_file(results_json) and not self.args.update:
            print("Using existing results.json file.")
            with open(results_json, "r") as f:
                results = json.load(f)
                for result in results:
                    self.results_map[result.get("student-id")] = result
            
        else:
            processes = []
            q = mp.Queue()

            for i, student in enumerate(self.student_map.values()):
                self.results_map[student.get("id")] = {}
                process = mp.Process(target=self.run_tests_for_student, args=(q, student,))
                processes.append(process)
                process.start()

            for process in processes:
                process.join()
            
            results_list = []
            while not q.empty():
                result = q.get()
                self.results_map[result.get("student-id")] = result
                results_list.append(result)
            q.close()
            
            print(results_list)

            # write to the json file
            with open(results_json, "w") as f:
                json.dump(results_list, f, indent=4)
        

    def run_tests_for_student(self, q, student,):
        print("Running tests for student: " + student["sis_user_id"])

        student_dir = os.path.join(self.dirs["students"], student["sis_user_id"])
        tests_dir = self.dirs["tests"]
        source_dir = os.path.join(student_dir, "submission")
        results_dir = os.path.join(student_dir, "results")

        # first clean the student directory
        if os.path.exists(results_dir):
            shutil.rmtree(results_dir)
        os.makedirs(results_dir)
        # create summary file
        open(os.path.join(student_dir, "results", "summary.txt"), "w+")

        num_passed = 0
    
        for test_dirname in os.listdir(tests_dir):
            test_dir = os.path.join(self.dirs["tests"], test_dirname)
            if not os.path.isdir(test_dir):
                continue

            main_class = self.config["source"]["main"]
            test = Test(tests_dir, test_dirname, student_dir, main_class)

            result = test.run()

            if result == "pass":
                num_passed += 1
        
        q.put({
            "student-id": student.get("id"),
            "tests-passed": num_passed
        })

    
    def post_grades(self):
        grade_data = {
            "grade_data": {}
        }
        for result in self.results_map.values():
            num_tests = 25
            points_per_missed = self.config.get("grade").get("points-per-missed")
            grade = 100 - (points_per_missed * (num_tests - result.get("tests-passed")))
            grade_data["grade_data"][str(result.get("student-id"))] = {
                "posted_grade": str(grade)
            }

        print(json.dumps(grade_data))

        grade_url = self.lms.get("assignment-url") + "/submissions/update_grades"
        headers = self.lms.get("headers")
        headers["Content-Type"] = "application/json"
        r = requests.post(
            url = grade_url,
            headers = headers,
            data = json.dumps(grade_data)
        )
        response = r.json()
        print(grade_url)
        print(response)

        
    
    def zip_results(self):
        for student in self.student_map.values():
            results_dir = os.path.join(self.dirs["students"], student["sis_user_id"], "results")

            zip_filename = os.path.join(results_dir, "results.zip")
            if os.path.exists(zip_filename):
                os.remove(zip_filename)
        
            print("Zip file is " + zip_filename)

            with zipfile.ZipFile(zip_filename, "w") as z:
                for file in glob.glob(os.path.join(results_dir, "**/*"), recursive=True):
                    # don't write ourselves
                    if str(file) == zip_filename:
                        continue
                    # print(file)
                    # write files relative to the results directory path
                    z.write(file, arcname=os.path.relpath(file, results_dir))
                

    def attach_results(self):
        upload_data = {
            "grade_data": {}
        }
        for student in self.student_map.values():
            url = self.lms.get("assignment-url") + "/submissions/" + str(student.get("id")) + "/comments/files"
            print(url)
            results_dir = os.path.join(self.dirs.get("students"), student.get("sis_user_id"), "results")
            zip_filename = os.path.join(results_dir, "results.zip")
            print(zip_filename)

            # first issue a POST to Canvas to retrieve the upload token
            data = {
                "name": "results.zip",
                "content_type": "application/zip",
                "on_duplicate": "overwrite"
            }
            r = requests.post(
                url = url,
                headers = self.lms.get("headers"),
                data = data
            )
            token_response = r.json()
            print(token_response)

            # now upload the file
            upload_url = token_response.get("upload_url")
            files = {
                "file": open(zip_filename, "rb")
            }
            data = token_response.get("upload_params")
            r = requests.post(
                url = upload_url,
                files = files,
                data = data
            )
            upload_response = r.json()
            print(upload_response)

            upload_data["grade_data"][str(student.get("id"))] = {
                "file_ids": [
                    upload_response.get("id")
                ]
            }

        print(upload_data)
        # now issue a PUT to comment on the submission
        submissions_url = self.lms.get("assignment-url") + "/submissions/update_grades"
        headers = self.lms.get("headers")
        headers["Content-Type"] = "application/json"
        r = requests.post(
            url = submissions_url,
            headers = headers,
            data = json.dumps(upload_data)
        )

        print(r.json())

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
            if len(classpath_matches) > 0:
                classpath = os.path.join(classpath_matches[0], "..")
            else:
                classpath = dir
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
        # self.run_tests()
        
        # self.zip_results()
        # self.post_grades()
        # self.attach_results()

    
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
