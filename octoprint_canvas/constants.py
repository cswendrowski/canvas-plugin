# API HTTP STATUS CODES
API_SUCCESS = 200
API_FAILURE = 500

# GET USER ERROR MESSAGEs
HUB_NOT_REGISTERED = "HUB is not registered yet. Cannot add user."
USER_ALREADY_LINKED = "User already registered to HUB."
INVALID_USER_CREDENTIALS = "Invalid user credentials. Cannot add user"

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