import time

TIMEOUT_MINUTES_CONTAINER_OPS = 1.5
TIMEOUT_MINUTES_PORTS = 1
TIME_SECONDS_BETWEEN_PORT_ATTEMPTS = 10

# List of Docker Hub Account: [username, password, email], if you have more, just append more with same format
DOCKER_ACCOUNT_LIST = [
    ['your-username', 'your-password', 'your.email@domain.com'],
]

# other constants
TOKEN_SEPARATOR = "/"  # linux
# TOKEN_SEPARATOR = "\\"  # windows

RUN_TIME_STR = time.strftime('%Y-%m-%d_%H-%M-%S')

DEFAULT_DIR_FOR_REPOS = f"repos"
DEFAULT_DIR_FOR_LOGS = "logs"
DEFAULT_DIR_FOR_OUTPUTS = "outputs"
DEFAULT_FILENAME_FOR_OUTPUT = "OUTPUT"
DEFAULT_FILENAME_FOR_ERROR = "ERROR"
DEFAULT_FILENAME_FOR_STATS = "STATS"

BUILD_IMAGE_NAME_PREFIX = "builded-image"

IS_PARALLEL_PULL = False # default value, overwritten by arg params from cmd


# mongodb
MONGO_HOST = '127.0.0.1'
MONGO_PORT = 27123
MONGO_DB_NAME = "framework_db"
MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}"


# wapiti default settings
WAPITI_DEFAULT_DIR_FOR_OUTPUTS = "outputsWapiti"
WAPITI_TYPE_REPORT = "json"
WAPITI_FILENAME_REPORT = "report.json"
WAPITI_FILENAME_LOG = "log"
WAPITI_NAMEDIR_SCANFILES = "scan"

WAPITI_COMMAND = [
    "wapiti",  # command to run Wapiti
    "--module", "csp,csrf,exec,http_headers,permanentxss,sql,ssrf,upload,xss,xxe", # modules for vuln scan
    "--headless", "visible",
    "--flush-session",
    "--tasks", "15",  # number of concurrent tasks used to crawl the target (affect how fast the scan proceeds)
    "--format", WAPITI_TYPE_REPORT,  # Report filetype
    "-v", "2",
    "--mitm-port", "16969"
]

# code coverage
CODECOVERAGE_DEFAULT_DIR_FOR_OUTPUTS = "outputsCodeCoverage"

SUDO = "your sudo password"