'''
Call this file like this: 'python check-files.py YOUR_ZIP_FILE.zip'.
Make sure this script at least finds all of the project files successfully.
You can ignore compile errors related to Problem3.java as that will be graded manually.
'''
import sys
import glob
import zipfile
import subprocess

def main():
    print("Checking files...")
    zip_filename = sys.argv[1]
    
    print("Zip file is " + zip_filename)
    if not zipfile.is_zipfile(zip_filename):
        print("Not a proper zip file, or file not found.")
        exit(1)

    zip_file = zipfile.ZipFile(zip_filename, 'r')
    zip_file.extractall(path = "./zip-outdir")
    zip_file.close()


    prog_files = glob.glob("./zip-outdir/**/Problem*.java", recursive = True)
    for file in prog_files:
        print("Found file: " + file)
        completed = subprocess.run(["javac", file])
        if completed.returncode == 0:
            print("Compiled successfully: " + file)
        else:
            print("Failed to compile: " + file)

if __name__ == "__main__":
    main()
