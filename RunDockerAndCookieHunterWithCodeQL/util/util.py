import subprocess

from config import SUDO


def killService(service_name):
    print(f"Killing service {service_name}...")
    cmd = f'echo {SUDO} | sudo -S systemctl stop {service_name}'
    result = subprocess.run(cmd, shell=True)
    print(f"Prune result: {result}")


def cookieDictToString(cookieDict):
    """Convert a dictionary of cookiename=cookievalue dictionary to string"""
    cookieString = ";".join([f"{key}={value}" for key, value in cookieDict.items()])
    return cookieString


def cookieListToCookieDict(cookieList):
    """Convert a list of cookie objects to a dictionary of cookies as cookiename=cookievalue"""
    cookieDict = {}
    for cookie in cookieList:
        # print(f"Name: {cookie.get('name', '')} Value: {cookie.get('value', '')}")
        name = cookie.get('name', '')
        value = cookie.get('value', '')
        if name != '' and value != '':
            cookieDict[name] = value
    return cookieDict


def hasLoginCookies(loginCookiesList):
    """
    Checks if a list of cookies contains any login cookies.
    Args: loginCookiesList (list): List of login cookies.
    Returns: bool: True if there are login cookies, False otherwise.
    """
    return loginCookiesList is not None and len(loginCookiesList) > 0


def anyEntryHasLoginCookies(allCookiesData):
    """
    Checks if any entry in allCookiesData has login cookies.
    Args: allCookiesData (list): A list of dictionaries, where each dictionary may contain 'login_cookies'.
    Returns: bool: True if at least one entry has login cookies, False otherwise.
    """
    if allCookiesData is None:
        return False
    for entry in allCookiesData:
        if hasLoginCookies(entry.get('loginCookies')):
            return True
    return False