import os
import shutil
import subprocess

from config import SUDO


def getAbsolutePath(path):
    return os.path.abspath(path)


def createDirectoryIfNotExists(dirName):
    if not os.path.exists(dirName):
        os.makedirs(dirName)


def getListOfFilnameOfADir(dirName):
    absolute_path = os.path.abspath(dirName)
    print(absolute_path)
    # get all entries in the directory
    entries = os.listdir(absolute_path)

    # filter out directories and return only filenames
    return [entry for entry in entries if os.path.isfile(os.path.join(absolute_path, entry))]


def checkIfDirExists(dirName):
    return os.path.exists(dirName)


def deleteDirAndAllContents(pathOfDirToDelete):
    cmd = f'echo {SUDO} | sudo -S rm -r {pathOfDirToDelete}'
    result = subprocess.run(cmd, shell=True)
    print(f"Prune result: {result}")


def copyAndRenameFile(srcPath, destDir, newFilename):
    # construct the full destination path including the new filename
    destPath = os.path.join(destDir, newFilename)

    # check if the file already exists at the destination
    if os.path.exists(destPath):
        print(f"File {destPath} already exists. Overwriting...")
    else:
        print(f"Copying and renaming file to {destPath}")

    # copy the file to the new location and rename it
    shutil.copy2(srcPath, destPath)


def copyDir(pathSource, pathDest):
    cmd = f'echo {SUDO} | cp -S -a -r {pathSource} {pathDest}'
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0


def changeBasePath(pathToBeChanged, oldBasePath, newBasePath):
    return pathToBeChanged.replace(oldBasePath, newBasePath)
