from util.fileUtil import copyDir


def copyRepository(destPath, repoLocalCopyPath):
    print(f"Cloning repo {repoLocalCopyPath} into {destPath}")

    isCopied = copyDir(repoLocalCopyPath, destPath)

    return isCopied
