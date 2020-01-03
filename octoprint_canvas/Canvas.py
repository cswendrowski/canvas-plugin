import os
import zipfile
import json
import requests
import time
import socket
import threading
from subprocess import call
from dotenv import load_dotenv
from io import BytesIO, open  # for Python 2 & 3
from future.utils import listvalues, lmap  # for Python 2 & 3
from . import constants
from . import Shadow

try:
    from ruamel.yaml import YAML
except ImportError:
    from ruamel.yaml.main import YAML
yaml = YAML(typ="safe")
yaml.default_flow_style = False

env_path = os.path.abspath(".") + "/.env"
if os.path.abspath(".") is "/":
    env_path = "/home/pi/.env"
load_dotenv(env_path)
BASE_URL_API = os.getenv("DEV_BASE_URL_API", "api.canvas3d.io/")


class Canvas():
    def __init__(self, plugin):
        self._logger = plugin._logger
        self._plugin_manager = plugin._plugin_manager
        self._identifier = plugin._identifier
        self._settings = plugin._settings
        self._plugin_version = plugin._plugin_version

        self.aws_connection = False
        self.hub_registered = False

        self.hub_yaml = {}
        self.isHubS = False
        self.registerThread = None

    ##############
    # PRIVATE
    ##############

    def _writeFile(self, path, content):
        data = open(path, "w")
        data.write(path)
        data.close()

    def _loadYAMLFile(self, yaml_file_path):
        hub_data = open(yaml_file_path, "r")
        hub_yaml = yaml.load(hub_data)
        hub_data.close()
        return hub_yaml

    def _writeYAMLFile(self, yaml_file_path, data):
        yaml_file = open(yaml_file_path, "w")
        yaml.dump(data, yaml_file)
        yaml_file.close()

    def _updateYAMLInfo(self):
        hub_data_path = os.path.expanduser('~') + "/.mosaicdata/canvas-hub-data.yml"
        self._writeYAMLFile(hub_data_path, self.hub_yaml)

    def _getAuthorizationHeader(self):
        hub_token = self.hub_yaml["canvas-hub"]["token"]
        headers = {"Authorization": "Bearer %s" % hub_token}
        return headers

    def _startRegisterThread(self):
        if self.registerThread is None:
            self.registerThread = threading.Thread(target=self._registerHub)
            self.registerThread.daemon = True
            self.registerThread.start()

    def _registerHub(self):
        while not self.hub_registered:
            self._logger.info("REGISTERING HUB (V2)")
            if not "serial-number" in self.hub_yaml["canvas-hub"]:
                name = yaml.load(self._settings.config_yaml)["server"]["secretKey"]
                payload = {"name": name}
            else:
                name = self.hub_yaml["canvas-hub"]["serial-number"]
                serialNumber = self.hub_yaml["canvas-hub"]["serial-number"]
                payload = {
                    "hostname": serialNumber + "-canvas-hub.local/",
                    "name": name,
                    "serialNumber": serialNumber
                }

            hostname = self._getHostname()
            if hostname:
                payload["hostname"] = hostname
            if self.isHubS:
                payload["isHubS"] = True

            url = "https://" + BASE_URL_API + "hubs"
            try:
                response = requests.put(url, json=payload)
                response_body = response.json()
                if response.status_code >= 400:
                    self._logger.info(response_body)
                    time.sleep(30)
                else:
                    self._saveRegistrationResponse(response_body)
                    self.hub_registered = True
            except requests.exceptions.RequestException as e:
                self._logger.info(e)
                time.sleep(30)
        return

    def _saveRegistrationResponse(self, response):
        if "token" in response:
            self.hub_yaml["canvas-hub"].update(response["hub"], token=response["token"])
        else:
            self.hub_yaml["canvas-hub"].update(response["hub"])
        self._updateYAMLInfo()

        # determine paths
        path = os.path.expanduser('~') + "/.mosaicdata/"
        cert_path = path + "certificate.pem.crt"
        private_path = path + "private.pem.key"

        # write files
        self._writeFile(cert_path, response["certificatePem"])
        self._writeFile(private_path, response["privateKey"])

    def _registerUserToHub(self, data):
        hub_id = self.hub_yaml["canvas-hub"]["id"]
        url = "https://" + BASE_URL_API + "hubs/" + hub_id + "/register"
        headers = self._getAuthorizationHeader()
        payload = {"userToken": data["token"]}
        try:
            response = requests.post(url, json=payload, headers=headers)
            response_body = response.json()
            if response.status_code >= 400:
                self._logger.info(response_body)
            else:
                if "token" in data:
                    del data["token"]
                self.hub_yaml["canvas-users"][data["id"]] = data
                self._updateYAMLInfo()
                self._updateUsersOnUI()
                if not self.aws_connection:
                    self._makeShadowDeviceClient()
                self.updateUI({"command": "UserConnectedToHUB", "data": data})
        except requests.exceptions.RequestException as e:
            raise Exception(e)

    def _verifyUserInYAML(self, data):
        registeredUsers = self.hub_yaml["canvas-users"]
        if data["id"] not in registeredUsers:
            self._logger.info("User is not registered to HUB yet.")
            self._registerUserToHub(data)
        else:
            self.updateUI({"command": "UserAlreadyExists", "data": data})
            raise Exception(constants.USER_ALREADY_LINKED)

    def _registerUserToHub(self, data):
        hub_id = self.hub_yaml["canvas-hub"]["id"]
        url = "https://" + BASE_URL_API + "hubs/" + hub_id + "/register"
        headers = self._getAuthorizationHeader()
        payload = {"userToken": data["token"]}
        try:
            response = requests.post(url, json=payload, headers=headers)
            response_body = response.json()
            if response.status_code >= 400:
                self._logger.info(response_body)
            else:
                if "token" in data:
                    del data["token"]
                self.hub_yaml["canvas-users"][data["id"]] = data
                self._updateYAMLInfo()
                self._updateUsersOnUI()
                if not self.aws_connection:
                    self._makeShadowDeviceClient()
                self.updateUI({"command": "UserConnectedToHUB", "data": data})
        except requests.exceptions.RequestException as e:
            raise Exception(e)

    def _updateUsersOnUI(self):
        # make a list of usernames
        if "canvas-users" in self.hub_yaml:
            usersValueList = listvalues(self.hub_yaml["canvas-users"])  # for Python 2 & 3
            list_of_users = lmap(lambda user: {key: user[key] for key in ["username"]}, usersValueList)  # for Python 2 & 3
            self.updateUI({"command": "DisplayRegisteredUsers", "data": list_of_users})

    def _streamFileProgress(self, response, filename, project_id):
        self._logger.info("Starting stream buffer")
        self.updateUI({
            "command": "CANVASDownload",
            "data": {
                "filename": filename,
                "projectId": project_id
            },
            "status": "starting"
        })

        buffer = BytesIO()
        total_bytes = int(response.headers.get("content-length"))
        chunk_size = total_bytes // 100  # for Python 2 & 3

        for data in response.iter_content(chunk_size=chunk_size):
            buffer.write(data)
            downloaded_bytes = float(len(buffer.getvalue()))
            percentage_completion = int((downloaded_bytes / total_bytes) * 100)
            self._logger.info("%s%% downloaded" % percentage_completion)
            self.updateUI({
                "command": "CANVASDownload",
                "data": {
                    "current": percentage_completion,
                    "projectId": project_id
                },
                "status": "downloading"
            }, False)
        return buffer

    def _extractZipfile(self, buffer_file, project_id):
        zip_file = zipfile.ZipFile(buffer_file)
        filename = zip_file.namelist()[0]
        watched_path = self._settings.global_get_basefolder("watched")
        self.updateUI({
            "command": "CANVASDownload",
            "data": {
                "filename": filename,
                "projectId": project_id
            },
            "status": "received"
        })
        self._logger.info("Extracting zip file")
        zip_file.extractall(watched_path)
        zip_file.close()

    def _upgradeToV2(self):
        self._logger.info("UPGRADING TO AMARANTH V2")
        payload = {}

        if "serial-number" in self.hub_yaml["canvas-hub"]:
            serialNumber = self.hub_yaml["canvas-hub"]["serial-number"]
            payload = {
                "hostname": serialNumber + "-canvas-hub.local/",
                "serialNumber": serialNumber
            }
            self._logger.info("Serial Number Found: %s" % serialNumber)

        hostname = self._getHostname()
        if hostname:
            payload["hostname"] = hostname

        self._logger.info(json.dumps(payload))

        hub_id = self.hub_yaml["canvas-hub"]["hub"]["id"]
        url = "https://" + BASE_URL_API + "hubs/" + hub_id + "/upgrade"
        headers = self._getAuthorizationHeader()
        try:
            response = requests.post(url, json=payload, headers=headers)
            response_body = response.json()
            if response.get("status") >= 400:
                self._logger.info(response_body)
            else:
                self._saveRegistrationResponse(response_body)
                if not self.aws_connection and self.hub_yaml["canvas-users"]:
                    self._makeShadowDeviceClient()
        except requests.exceptions.RequestException as e:
            self._logger.info(e)

    def _getHostname(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            self._logger.info("Unable to get hostname")
            return None

    def _updateHostname(self, new_hostname):
        self._logger.info("Updating Hostname")
        hub_id = self.hub_yaml["canvas-hub"]["id"]
        url = "https://" + BASE_URL_API + "hubs/" + hub_id
        headers = self._getAuthorizationHeader()
        payload = {"hostname": new_hostname}
        try:
            response = requests.post(url, json=payload, headers=headers)
            response_body = response.json()
            if response.status_code >= 400:
                self._logger.info(response_body)
            else:
                if new_hostname:
                    self._logger.info("Hostname updated: %s" % new_hostname)
                    self.hub_yaml["canvas-hub"]["hostname"] = new_hostname
                    self._updateYAMLInfo()
                else:
                    self._logger.info("Deleting hostname")
                    del self.hub_yaml["canvas-hub"]["hostname"]
        except requests.exceptions.RequestException as e:
            self._logger.info(e)

    def _makeShadowDeviceClient(self):
        self._logger.info("Connecting Hub to CANVAS...")
        self.myShadow = Shadow.Shadow(self)
        self.myShadow.connect()

    ##############
    # PUBLIC
    ##############

    # 1. SERVER STARTUP FUNCTIONS
    def checkForRuamelVersion(self):
        for path in constants.PROBLEMATIC_YAML_FILES_PATHS:
            if os.path.exists(path):
                self._logger.info("Deleting file/directory")
                call(["rm -rf %s" % path], shell=True)

    def checkFor0cf0(self):
        if (
            os.path.isdir("/home/pi/.mosaicdata/turquoise/") and
            "hub" in self.hub_yaml["canvas-hub"] and
            self.hub_yaml["canvas-hub"]["hub"]["name"] == constants.PROBLEMATIC_HUB_VALUES["name"] and
            self.hub_yaml["canvas-hub"]["hub"]["id"] == constants.PROBLEMATIC_HUB_VALUES["id"] and
            self.hub_yaml["canvas-hub"]["token"] == constants.PROBLEMATIC_HUB_VALUES["token"]
        ):
            self._logger.info("0cf0 found.")
            del self.hub_yaml["canvas-hub"]["hub"]
            del self.hub_yaml["canvas-hub"]["token"]
            self._updateYAMLInfo()

    def loadHubData(self):
        self._logger.info("Loading HUB data")
        hub_dir_path = os.path.expanduser('~') + "/.mosaicdata"
        hub_file_path = hub_dir_path + "/canvas-hub-data.yml"

        # if /.mosaicdata doesn't exist yet, make the directory
        if not os.path.exists(hub_dir_path):
            os.mkdir(hub_dir_path)

        # if the YML file doesn't exist, make the file
        if not os.path.isfile(hub_file_path):
            self._writeYAMLFile(hub_file_path, constants.DEFAULT_YAML)

        # access yaml file with all the info
        hub_yaml = self._loadYAMLFile(hub_file_path)

        # for compatibility with older hub zero, if the yaml file doesn't have a "canvas-users" key
        if not "canvas-users" in hub_yaml and all(key in hub_yaml for key in ("canvas-hub", "versions")):
            hub_yaml["canvas-users"] = {}
            self._writeYAMLFile(hub_file_path, hub_yaml)

        # if, for some reason, yaml file is empty or missing a property
        if not hub_yaml or not all(key in hub_yaml for key in ("canvas-users", "canvas-hub", "versions")):
            self._logger.info("Resetting YAML file to default")
            self._writeYAMLFile(hub_file_path, constants.DEFAULT_YAML)
            hub_yaml = self._loadYAMLFile(hub_file_path)

        return hub_yaml

    def checkIfRootCertExists(self):
        root_ca_path = os.path.expanduser('~') + "/.mosaicdata/root-ca.crt"
        if not os.path.isfile(root_ca_path):
            self._logger.info("DOWNLOADING ROOT-CA CERT")
            try:
                response = requests.get(constants.ROOT_CA_CERTIFICATE)
                self._writeFile(root_ca_path, response.content)
                self._logger.info("ROOT-CA DOWNLOADED")
            except requests.exceptions.RequestException as e:
                self._logger.info(e)
        else:
            self._logger.info("ROOT-CA ALREADY THERE")

    def checkForRegistrationAndVersion(self):
        if "token" in self.hub_yaml["canvas-hub"]:
            self._logger.info("HUB already registered")
            self.hub_registered = True
            if not "version" in self.hub_yaml["canvas-hub"]:
                self._logger.info("HUB version is 1 --- NOW UPGRADING TO V2")
                self._upgradeToV2()
            else:
                self._logger.info("HUB version is 2 --- NO UPGRADE NEEDED")
                new_hostname = self._getHostname()
                if not "hostname" in self.hub_yaml["canvas-hub"] and new_hostname:
                    self._updateHostname(new_hostname)
                elif "hostname" in self.hub_yaml["canvas-hub"] and self.hub_yaml["canvas-hub"]["hostname"] != new_hostname:
                    if self.hub_yaml["canvas-hub"]["hostname"] == "" and new_hostname == None:
                        pass
                    else:
                        self._updateHostname(new_hostname)
                self.getRegisteredUsers()
                if self.hub_yaml["canvas-users"]:
                    self._makeShadowDeviceClient()
                else:
                    self._logger.info("There are no linked Canvas accounts yet. Connection not established.")
        if not self.hub_registered:
            self._logger.info("HUB not registered yet. Registering...")
            self._startRegisterThread()

    def updatePluginVersions(self):
        updated = False
        if "versions" in self.hub_yaml:
            # canvas
            if self.hub_yaml["versions"]["canvas-plugin"] != self._plugin_version:
                self.hub_yaml["versions"]["canvas-plugin"] = self._plugin_version
                updated = True
            # palette 2
            if self._plugin_manager.get_plugin_info("palette2") and self.hub_yaml["versions"]["palette-plugin"] != self._plugin_manager.get_plugin_info("palette2").version:
                self.hub_yaml["versions"]["palette-plugin"] = self._plugin_manager.get_plugin_info("palette2").version
                updated = True
            if updated:
                self._updateYAMLInfo()

    def determineHubVersion(self):
        hub_file_path = os.path.expanduser('~') + "/.mosaicdata/canvas-hub-data.yml"
        if os.path.exists(hub_file_path):
            hub_yaml = self._loadYAMLFile(hub_file_path)
            hub_rank = hub_yaml["versions"]["global"]
            if hub_rank == "0.2.0":
                return True
        return False

    # 2. UI FUNCTIONS
    def getRegisteredUsers(self):
        hub_id = self.hub_yaml["canvas-hub"]["id"]
        url = "https://" + BASE_URL_API + "hubs/" + hub_id + "/users"
        headers = self._getAuthorizationHeader()
        try:
            response = requests.get(url, headers=headers)
            response_body = response.json()
            if "users" in response_body:
                self._logger.info("Got list of registered users.")
                users = response_body["users"]
                updated_users = {}
                for user in users:
                    updated_users[user["id"]] = user
                self.hub_yaml["canvas-users"] = updated_users
                self._updateYAMLInfo()
                # if there are no linked users, disconnect shadow client
                if not self.hub_yaml["canvas-users"] and self.aws_connection:
                    self.myShadow.disconnect()
            else:
                self._logger.info("Could not get updated list of registered users.")
            self._updateUsersOnUI()
        except requests.exceptions.RequestException as e:
            self._logger.info(e)

    def checkAWSConnection(self):
        if self.aws_connection:
            self.updateUI({"command": "AWS", "data": True})
        else:
            reason = "server" if self.hub_yaml["canvas-users"] else "account"
            self.updateUI({"command": "AWS", "data": False, "reason": reason})

    # 3. USER FUNCTIONS
    def addUser(self, loginInfo):
        if self.hub_registered:
            loginData = loginInfo["data"]
            payload = {"password": loginData["password"]}
            if "username" in loginData:
                payload["username"] = loginData["username"]
            elif "email" in loginData:
                payload["email"] = loginData["email"]
            url = "https://" + BASE_URL_API + "users/login"
            try:
                response = requests.post(url, json=payload)
                response_body = response.json()
                if response.status_code >= 400:
                    self.updateUI({"command": "invalidUserCredentials"})
                    raise Exception(constants.INVALID_USER_CREDENTIALS)
                else:
                    self._verifyUserInYAML(response_body)
            except requests.exceptions.RequestException as e:
                raise Exception(e)
        else:
            self.updateUI({"command": "hubNotRegistered"})
            raise Exception(constants.HUB_NOT_REGISTERED)

    def downloadPrintFiles(self, data):
        project_id = data["projectId"]
        url = "https://slice." + BASE_URL_API + "projects/" + project_id + "/download"
        headers = self._getAuthorizationHeader()
        filename = data["filename"]
        try:
            self._logger.info("Starting CANVAS download")
            response = requests.get(url, headers=headers, stream=True)
            downloaded_file = self._streamFileProgress(response, filename, project_id)
            self._extractZipfile(downloaded_file, project_id)
        except requests.exceptions.RequestException as e:
            self._logger.info(e)

    def changeImportantUpdateSettings(self, condition):
        self._logger.info("Changing Important Update Settings")
        self._settings.set(["importantUpdate"], condition, force=True)
        self._logger.info(self._settings.get(["importantUpdate"]))

    # 4. HELPER FUNCTIONS
    def removeUserFromYAML(self, user_id):
        username = self.hub_yaml["canvas-users"][user_id]["username"]
        del self.hub_yaml["canvas-users"][user_id]
        self._updateYAMLInfo()
        self._updateUsersOnUI()
        self.updateUI({"command": "UserDeleted", "data": username})

    def updateUI(self, data, displayLog=True):
        if displayLog:
            self._logger.info("Sending UIUpdate from Canvas Plugin")
        self._plugin_manager.send_plugin_message(self._identifier, data)
