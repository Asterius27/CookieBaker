from config import MONGO_URI, MONGO_DB_NAME
from pymongo import *

connector = None


def createConnection():
	# create connection to DB if it does not already exist
	global connector

	if connector is None:
		try:
			connector = MongoClient(MONGO_URI)[MONGO_DB_NAME]
		except Exception as e:
			print(f"Error connecting to MongoDB: {e}")
			connector = None
	return connector


def isConnectionCreated():
	global connector
	if connector is None:
		return False

	try:
		connector.client.server_info()  # raise an exception if connection is not ok
		return True  # if no exception raised, then connection is ok
	except Exception:
		print("Server not available")
		return False


def extractCookies():
	"""function to extract cookies detail from misc_cookies collection created by CH that are stored in MongoDB"""
	global connector

	# Connect if not already connected
	if connector is None:
		createConnection()

	try:
		# Access the "misc_cookies" collection within the "framework_db" database
		collection = connector["misc_cookies"]

		cookieData = collection.find_one()  # single url:port analyzed, so single document in misc_cookies (or nothing)

		if cookieData:
			# Extract 'login_cookies' and 'nonlogin_cookies' from the document
			loginCookies = cookieData.get('login_cookies', [])
			nonLoginCookies = cookieData.get('nonlogin_cookies', [])

			# Return the lists of cookies
			return loginCookies, nonLoginCookies
		else:
			print("No cookies found in 'misc_cookies' collection.")
			return [], []

	except Exception as e:
		print(f"Error extracting cookies: {e}")
		return [], []


def extractCookiesDetailed():
	"""extract cookies data from credentials_and_cookies collection in MongoDB"""
	global connector

	# Connect if not already connected
	if connector is None:
		createConnection()

	try:
		collection = connector["credentials_and_cookies"]
		allDocuments = collection.find()

		allCookiesData = []
		for document in allDocuments:
			loginCookies = document.get('login_cookies', [])
			nonLoginCookies = document.get('nonlogin_cookies', [])
			username = document.get('username', None)
			url = document.get('url', None)
			repoUrl = document.get('repoURL', None)
			password = document.get('password', None)
			redirectedToUrl = document.get('redirected_to_url', None)
			isExternalCredential = document.get('is_external_credential', None)

			allCookiesData.append({
				'username': username,
				'url': url,
				'repoUrl': repoUrl,
				'loginCookies': loginCookies,
				'nonLoginCookies': nonLoginCookies,
				'password': password,
				'redirectedToUrl': redirectedToUrl,
				'isExternalCredential': isExternalCredential
			})

		if len(allCookiesData) > 0:
			return allCookiesData
		else:
			print("No cookies found in 'credentials_and_cookies' collection.")
			return []

	except Exception as e:
		print(f"Error extracting detailed cookies: {e}")
		return []

