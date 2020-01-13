# API HTTP STATUS CODES
API_SUCCESS = 200
API_FAILURE = 500

# GET USER ERROR MESSAGEs
HUB_NOT_REGISTERED = "HUB is not registered yet. Cannot add user."
USER_ALREADY_LINKED = "User already registered to HUB."
INVALID_USER_CREDENTIALS = "Invalid user credentials. Cannot add user"

# SHADOW DEVICE CREDENTIALS
ROOT_CA_CERTIFICATE = "https://www.amazontrust.com/repository/AmazonRootCA1.pem"
SHADOW_CLIENT_HOST = "a6xr6l0abc72a-ats.iot.us-east-1.amazonaws.com"

# SOFTWARE UPDATE
GITLAB_PROJECT_ID = 8332728
LATEST_VERSION_URL = "https://gitlab.com/api/v4/projects/%s/releases" % GITLAB_PROJECT_ID
PLUGIN_UPDATE_URL = "https://gitlab.com/mosaic-mfg/canvas-plugin/-/archive/master/canvas-plugin-master.zip"

# DEFAULT YAML FILE HUB TEMPLATE
DEFAULT_YAML = (
    {
        'versions': {
            'turquoise': '1.0.0',
            'global': '0.1.0',
            'canvas-plugin': '0.1.0',
            'palette-plugin': '0.2.0',
            'data-version': '0.0.1'
        },
        'canvas-hub': {},
        'canvas-users': {}
    }
)

# PROBLEMATIC YAML FILES/DIRECTORIES THAT CAUSE PLUGIN TO CRASH
# TODO: potentially remove in future when most recent ruamel.yaml version no longer crashes plugin
PROBLEMATIC_YAML_FILES_PATHS = [
    "/home/pi/oprint/lib/python2.7/site-packages/_ruamel_yaml.so",
    "/home/pi/oprint/lib/python2.7/site-packages/ruamel.yaml.clib-0.1.0-py2.7-nspkg.pth",
    "/home/pi/oprint/lib/python2.7/site-packages/ruamel.yaml.clib-0.1.0-py2.7.egg-info",
]

# SOME HUBS MAY HAVE THESE PROBLEMATIC VALUES
PROBLEMATIC_HUB_VALUES = {
    "name": "0cf0-ch",
    "id": "46f352c67dd7bc1e5a28b66cf960290d",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1NDIzODIxMTQsImlzcyI6IkNhbnZhc0h1YiIsInN1YiI6IjQ2ZjM1MmM2N2RkN2JjMWU1YTI4YjY2Y2Y5NjAyOTBkIn0.CMDTVKAuI2USNwvx1gjKVBMgTRCnOX8WBhp2XTjjhLM"
}
