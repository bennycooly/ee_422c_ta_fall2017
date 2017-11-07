
import os
import glob
import subprocess
import shutil

class JavaUtils:
    @staticmethod
    def compile(classpath, javac_files = "*", javac_args = {}):
        args_list = []
        for key, val in javac_args.items():
            args_list.append(key)
            args_list.append(val)
        
        files = []
        if javac_files == "*":
            files = glob.glob(classpath + "/**/*.java", recursive=True)
        elif type(javac_files) is list:
            files = javac_files

        completed = subprocess.run(["javac", "-cp", classpath] + args_list + files, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

        if completed.returncode == 0:
            print("Compiled successfully.")
        else:
            print("Failed to compile.")
        return completed

    @staticmethod
    def find_main(classpath):
        java_files = glob.glob(classpath + "/**/*.java", recursive=True)
        for java_file in java_files:
            with open(java_file, "r", errors="ignore") as f:
                # print(java_file)
                contents = f.read()
                if "main(" in contents or "main (" in contents:
                    words = contents.split()
                    for i, word in enumerate(words):
                        if word == "package":
                            package = words[i + 1].replace(';', '')
                            main_class = package + '.' + os.path.basename(java_file).replace(".java", '')
                            print(main_class)
                            return main_class
                    # no package
                    main_class = os.path.basename(java_file).replace(".java", '')
                    # print(main_class)
                    return main_class
        
        print("main class not found")
        return ""

    
    @staticmethod
    def fix_directory_structure(classpath, package):
        """Attempts to fix the directory structure of the classpath.
        If the classpath does not contain the package directory, then it will
        be made.
        """
        java_files = glob.glob(classpath + "/**/*.java", recursive=True)
        java_dir = os.path.dirname(java_files[0])
        java_dir_basename = os.path.basename(java_dir)
        if java_dir_basename != package:
            package_dir = os.path.join(java_dir, package)
            print(package_dir)
            # delete file by same name...
            if os.path.exists(package_dir) and not os.path.isdir(package_dir):
                os.remove(package_dir)
            os.mkdir(package_dir)
            for java_file in java_files:
                shutil.copy(java_file, package_dir)
                os.remove(java_file)
            


    @staticmethod
    def get_file_location(file, classpath):
        """ Parses the input java file and returns its correct full path.
        e.g. if the java file is in package assignment.pack1, then this method returns assignment1/pack1
        """
        with open(file, "r") as f:
            contents = f.read()
            words = contents.split()
            for i, word in enumerate(words):
                if word == "package":
                    package = words[i + 1].replace(';', '')
                    package_path = package.replace('.', '/')
                    path = os.path.join(classpath, package_path)
                    return path
            
            return classpath


    @staticmethod
    def get_classpath(dir, main_class):
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
            if len(classpath_matches) > 0:
                classpath = os.path.join(classpath_matches[0], "..")
            else:
                classpath = "dir"

        return classpath
        
