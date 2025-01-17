import os
import subprocess

from config import SUDO

def createDirectoryIfNotExists(dirName):
    if not os.path.exists(dirName):
        os.makedirs(dirName)


def checkIfDirExists(dirName):
    return os.path.exists(dirName)


def deleteDirAndAllContents(pathOfDirToDelete):
    cmd = f'echo {SUDO} | sudo -S rm -r {pathOfDirToDelete}'
    result = subprocess.run(cmd, shell=True)
    print(f"Prune result: {result}")


def copyDir(pathSource, pathDest):
    print(f"Copying {pathSource} into {pathDest}...")
    cmd = f'echo {SUDO} | cp -S -a -r {pathSource} {pathDest}'
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0


def removeSymlinks(directory):
    # os.walk() will walk through all directories and subdirectories at any level
    for root, dirs, files in os.walk(directory):
        # Combine the root directory with the files to get the full path
        for item in files + dirs:  # check both files and subdirectories
            path = os.path.join(root, item)
            if os.path.islink(path):  # Check if it's a symlink
                try:
                    os.remove(path)  # Remove the symlink
                    print(f"Removed symlink: {path}")
                except OSError as e:
                    print(f"Error removing symlink {path}: {e}")
