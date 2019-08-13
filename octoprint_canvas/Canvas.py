import os
import zipfile
import StringIO
import json
import requests
import ssl
import time
import math
import socket
import threading

try:
    from ruamel.yaml import YAML
except ImportError:
    from ruamel.yaml.main import YAML
yaml = YAML(typ="safe")
yaml.default_flow_style = False

from dotenv import load_dotenv
env_path = os.path.abspath(".") + "/.env"
if os.path.abspath(".") is "/":
    env_path = "/home/pi/.env"
load_dotenv(env_path)
BASE_URL_API = os.getenv("DEV_BASE_URL_API", "api.canvas3d.io/")
from subprocess import call

from . import Shadow
from . import constants


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
        self.registerThread = None

    ##############
    # 1. SERVER STARTUP FUNCTIONS
    ##############

    def checkForRuamelVersion(self):
        paths = [
            "/home/pi/oprint/lib/python2.7/site-packages/_ruamel_yaml.so",
            "/home/pi/oprint/lib/python2.7/site-packages/ruamel.yaml.clib-0.1.0-py2.7-nspkg.pth",
            "/home/pi/oprint/lib/python2.7/site-packages/ruamel.yaml.clib-0.1.0-py2.7.egg-info",
        ]
        for path in paths:
            if os.path.exists(path):
                self._logger.info("Deleting file/directory")
                call(["rm -rf %s" % path], shell=True)

    def checkFor0cf0(self):
        if os.path.isdir("/home/pi/.mosaicdata/turquoise/") and "hub" in self.hub_yaml["canvas-hub"] and self.hub_yaml["canvas-hub"]["hub"]["name"] == "0cf0-ch" and self.hub_yaml["canvas-hub"]["hub"]["id"] == "46f352c67dd7bc1e5a28b66cf960290d" and self.hub_yaml["canvas-hub"]["token"] == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1NDIzODIxMTQsImlzcyI6IkNhbnZhc0h1YiIsInN1YiI6IjQ2ZjM1MmM2N2RkN2JjMWU1YTI4YjY2Y2Y5NjAyOTBkIn0.CMDTVKAuI2USNwvx1gjKVBMgTRCnOX8WBhp2XTjjhLM":
            self._logger.info("0cf0 found.")
            del self.hub_yaml["canvas-hub"]["hub"]
            del self.hub_yaml["canvas-hub"]["token"]
            self.updateYAMLInfo()

    def loadHubData(self):
        self._logger.info("Loading HUB data")
        hub_dir_path = os.path.expanduser('~') + "/.mosaicdata"
        hub_file_path = hub_dir_path + "/canvas-hub-data.yml"

        # if /.mosaicdata doesn't exist yet, make the directory
        if not os.path.exists(hub_dir_path):
            os.mkdir(hub_dir_path)

        # if the YML file doesn't exist, make the file
        if not os.path.isfile(hub_file_path):
            f = open(hub_file_path, "w")
            hub_template = ({'versions': {'turquoise': '1.0.0', 'global': '0.1.0', 'canvas-plugin': '0.1.0',
                                          'palette-plugin': '0.2.0', 'data-version': '0.0.1'},
                             'canvas-hub': {},
                             'canvas-users': {}})
            yaml.dump(hub_template, f)
            f.close()

        # access yaml file with all the info
        hub_data = open(hub_file_path, "r")
        hub_yaml = yaml.load(hub_data)
        hub_data.close()

        # if the yaml file exists already but doesn't have a "canvas-users" key and value yet
        if not hub_yaml or not "canvas-users" in hub_yaml:
            hub_yaml["canvas-users"] = {}
            hub_data = open(hub_file_path, "w")
            yaml.dump(hub_yaml, hub_data)
            hub_data.close()

        return hub_yaml

    def checkIfRootCertExists(self):
        root_ca_path = os.path.expanduser('~') + "/.mosaicdata/root-ca.crt"
        if not os.path.isfile(root_ca_path):
            self._logger.info("DOWNLOADING ROOT-CA CERT")
            url = "https://www.amazontrust.com/repository/AmazonRootCA1.pem"
            try:
                response = requests.get(url)
                root_ca = open(root_ca_path, "w")
                root_ca.write(response.content)
                root_ca.close()
                self._logger.info("ROOT-CA DOWNLOADED")
            except requests.exceptions.RequestException as e:
                self._logger.info(e)
        else:
            self._logger.info("ROOT-CA ALREADY THERE")

    def registerHub(self):
        while not self.hub_registered:
            self._logger.info("REGISTERING HUB (V2)")
            if not "serial-number" in self.hub_yaml["canvas-hub"]:
                name = yaml.load(self._settings.config_yaml)["server"]["secretKey"]
                payload = {
                    "name": name
                }
            else:
                name = self.hub_yaml["canvas-hub"]["serial-number"]
                serialNumber = self.hub_yaml["canvas-hub"]["serial-number"]
                payload = {
                    "hostname": serialNumber + "-canvas-hub.local/",
                    "name": name,
                    "serialNumber": serialNumber
                }

            hostname = self.getHostname()
            if hostname:
                payload["hostname"] = hostname

            url = "https://" + BASE_URL_API + "hubs"
            try:
                response = requests.put(url, json=payload).json()
                if response.get("status") >= 400:
                    self._logger.info(response)
                    time.sleep(30)
                else:
                    self.saveUpgradeResponse(response)
                    self.hub_registered = True
            except requests.exceptions.RequestException as e:
                self._logger.info(e)
                time.sleep(30)
        return

    def checkForRegistrationAndVersion(self):
        if "token" in self.hub_yaml["canvas-hub"]:
            self._logger.info("HUB already registered")
            self.hub_registered = True
            if not "version" in self.hub_yaml["canvas-hub"]:
                self._logger.info("HUB version is 1 --- NOW UPGRADING TO V2")
                self.upgradeToV2()
            else:
                self._logger.info("HUB version is 2 --- NO UPGRADE NEEDED")
                new_hostname = self.getHostname()
                if not "hostname" in self.hub_yaml["canvas-hub"] and new_hostname:
                    self.updateHostname(new_hostname)
                elif "hostname" in self.hub_yaml["canvas-hub"] and self.hub_yaml["canvas-hub"]["hostname"] != new_hostname:
                    if self.hub_yaml["canvas-hub"]["hostname"] == "" and new_hostname == None:
                        pass
                    else:
                        self.updateHostname(new_hostname)
                self.getRegisteredUsers()
                if self.hub_yaml["canvas-users"]:
                    self.makeShadowDeviceClient()
                else:
                    self._logger.info("There are no linked Canvas accounts yet. Connection not established.")
        if self.hub_registered is False:
            self._logger.info("HUB not registered yet. Registering...")
            self.startRegisterThread()

    def updatePluginVersions(self):
        updated = False
        # canvas
        if self.hub_yaml["versions"]["canvas-plugin"] != self._plugin_version:
            self.hub_yaml["versions"]["canvas-plugin"] = self._plugin_version
            updated = True
        # palette 2
        if self._plugin_manager.get_plugin_info("palette2") and self.hub_yaml["versions"]["palette-plugin"] != self._plugin_manager.get_plugin_info("palette2").version:
            self.hub_yaml["versions"]["palette-plugin"] = self._plugin_manager.get_plugin_info("palette2").version
            updated = True
        if updated:
            self.updateYAMLInfo()

    def startRegisterThread(self):
        if self.registerThread is None:
            self.registerThread = threading.Thread(target=self.registerHub)
            self.registerThread.daemon = True
            self.registerThread.start()

    ##############
    # 2. CLIENT UI STARTUP FUNCTIONS
    ##############

    def getRegisteredUsers(self):
        hub_id = self.hub_yaml["canvas-hub"]["id"]
        hub_token = self.hub_yaml["canvas-hub"]["token"]
        url = "https://" + BASE_URL_API + "hubs/" + hub_id + "/users"
        authorization = "Bearer " + hub_token
        headers = {"Authorization": authorization}
        try:
            response = requests.get(url, headers=headers).json()
            if "users" in response:
                self._logger.info("Got list of registered users.")
                users = response["users"]
                updated_users = {}
                for user in users:
                    updated_users[user["id"]] = user
                self.hub_yaml["canvas-users"] = updated_users
                self.updateYAMLInfo()
            else:
                self._logger.info("Could not get updated list of registered users.")
            self.updateRegisteredUsers()
        except requests.exceptions.RequestException as e:
            self._logger.info(e)

    def checkAWSConnection(self):
        if self.aws_connection is True:
            self.updateUI({"command": "AWS", "data": True})
        else:
            if not self.hub_yaml["canvas-users"]:
                self.updateUI({"command": "AWS", "data": False, "reason": "account"})
            else:
                self.updateUI({"command": "AWS", "data": False, "reason": "server"})

    ##############
    # 3. USER FUNCTIONS
    ##############

    def addUser(self, loginInfo):
        if self.hub_registered:
            if "username" in loginInfo["data"]:
                data = {"username": loginInfo["data"]["username"],
                        "password": loginInfo["data"]["password"]}
            elif "email" in loginInfo["data"]:
                data = {"email": loginInfo["data"]["email"],
                        "password": loginInfo["data"]["password"]}
            url = "https://" + BASE_URL_API + "users/login"
            try:
                response = requests.post(url, json=data).json()
                if response.get("status") >= 400:
                    self.updateUI({"command": "invalidUserCredentials"})
                    raise Exception(constants.INVALID_USER_CREDENTIALS)
                else:
                    self.verifyUserInYAML(response)
            except requests.exceptions.RequestException as e:
                raise Exception(e)
        else:
            self.updateUI({"command": "hubNotRegistered"})
            raise Exception(constants.HUB_NOT_REGISTERED)

    def downloadPrintFiles(self, data):
        token = self.hub_yaml["canvas-hub"]["token"]
        authorization = "Bearer " + token
        headers = {"Authorization": authorization}
        project_id = data["projectId"]
        url = "https://slice." + BASE_URL_API + "projects/" + project_id + "/download"
        filename = data["filename"]
        try:
            response = requests.get(url, headers=headers, stream=True)
            downloaded_file = self.streamFileProgress(response, filename, project_id)
            self.extractZipfile(downloaded_file, project_id)
        except requests.exceptions.RequestException as e:
            self._logger.info(e)

    def changeImportantUpdateSettings(self, condition):
        self._logger.info("Changing Important Update Settings")
        self._settings.set(["importantUpdate"], condition, force=True)
        self._logger.info(self._settings.get(["importantUpdate"]))

    ##############
    # 4. HELPER FUNCTIONS
    ##############

    def removeUserFromYAML(self, user_id):
        username = self.hub_yaml["canvas-users"][user_id]["username"]
        del self.hub_yaml["canvas-users"][user_id]
        self.updateYAMLInfo()
        self.updateRegisteredUsers()
        self.updateUI({"command": "UserDeleted", "data": username})

    def verifyUserInYAML(self, data):
        # get list of all registered users on the HUB YML file
        registeredUsers = self.hub_yaml["canvas-users"]

        # if user is not registered in HUB YML file yet
        if data.get("id") not in registeredUsers:
            self._logger.info("User is not registered to HUB yet.")
            self.registerUserAndHub(data)
        else:
            self.updateUI({"command": "UserAlreadyExists", "data": data})
            raise Exception(constants.USER_ALREADY_LINKED)

    def updateRegisteredUsers(self):
        # make a list of usernames
        if "canvas-users" in self.hub_yaml:
            list_of_users = map(lambda user: {key: user[key] for key in ["username"]}, self.hub_yaml["canvas-users"].values())
            self.updateUI({"command": "DisplayRegisteredUsers", "data": list_of_users})
            # if there are no linked users, disconnect shadow client
            if not self.hub_yaml["canvas-users"] and self.aws_connection is True:
                self.myShadow.disconnect()

    def updateYAMLInfo(self):
        hub_data_path = os.path.expanduser('~') + "/.mosaicdata/canvas-hub-data.yml"
        hub_data = open(hub_data_path, "w")
        yaml.dump(self.hub_yaml, hub_data)
        hub_data.close()

    def registerUserAndHub(self, data):
        hub_id = self.hub_yaml["canvas-hub"]["id"]
        hub_token = self.hub_yaml["canvas-hub"]["token"]
        payload = {
            "userToken": data["token"]
        }
        url = "https://" + BASE_URL_API + "hubs/" + hub_id + "/register"
        authorization = "Bearer " + hub_token
        headers = {"Authorization": authorization}
        try:
            response = requests.post(url, json=payload, headers=headers).json()
            if response.get("status") >= 400:
                self._logger.info(response)
            else:
                if "token" in data:
                    del data["token"]
                self.hub_yaml["canvas-users"][data.get("id")] = data
                self.updateYAMLInfo()
                self.updateRegisteredUsers()
                self.updateUI({"command": "UserConnectedToHUB", "data": data})
                if not self.aws_connection:
                    self.makeShadowDeviceClient()
        except requests.exceptions.RequestException as e:
            raise Exception(e)

    def updateUI(self, data):
        self._logger.info("Sending UIUpdate from Canvas")
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def streamFileProgress(self, response, filename, project_id):
        total_length = response.headers.get('content-length')
        self.updateUI({"command": "CANVASDownload", "data": {"filename": filename, "projectId": project_id}, "status": "starting"})

        actual_file = ""
        current_downloaded = 0.00
        total_length = int(total_length)
        stream_size = total_length/100

        for data in response.iter_content(chunk_size=stream_size):
            actual_file += data
            current_downloaded += len(data)
            percentage_completion = int(math.floor((current_downloaded/total_length)*100))
            self.updateUI({"command": "CANVASDownload", "data": {"current": percentage_completion, "projectId": project_id}, "status": "downloading"})
        return actual_file

    def extractZipfile(self, file, project_id):
        z = zipfile.ZipFile(StringIO.StringIO(file))
        filename = z.namelist()[0]
        watched_path = self._settings.global_get_basefolder("watched")
        self.updateUI({"command": "CANVASDownload", "data": {"filename": filename, "projectId": project_id}, "status": "received"})
        z.extractall(watched_path)

    ##############
    # 5. AWS IOT / UPGRADE RELATED FUNCTIONS
    ##############

    def upgradeToV2(self):
        self._logger.info("UPGRADING TO AMARANTH V2")
        payload = {}

        if "serial-number" in self.hub_yaml["canvas-hub"]:
            self._logger.info("Serial Number Found")
            serialNumber = self.hub_yaml["canvas-hub"]["serial-number"]
            payload = {
                "hostname": serialNumber + "-canvas-hub.local/",
                "serialNumber": serialNumber
            }
            self._logger.info("Serial Number: %s" % serialNumber)

        hostname = self.getHostname()
        if hostname:
            payload["hostname"] = hostname

        self._logger.info(json.dumps(payload))

        hub_id = self.hub_yaml["canvas-hub"]["hub"]["id"]
        hub_token = self.hub_yaml["canvas-hub"]["token"]
        url = "https://" + BASE_URL_API + "hubs/" + hub_id + "/upgrade"
        authorization = "Bearer " + hub_token
        headers = {"Authorization": authorization}
        try:
            response = requests.post(url, json=payload, headers=headers).json()
            if response.get("status") >= 400:
                self._logger.info(response)
            else:
                self.saveUpgradeResponse(response)
                if not self.aws_connection and self.hub_yaml["canvas-users"]:
                    self.makeShadowDeviceClient()
        except requests.exceptions.RequestException as e:
            self._logger.info(e)

    def saveUpgradeResponse(self, response):
        if "token" in response:
            self.hub_yaml["canvas-hub"].update(response["hub"], token=response["token"])
        else:
            self.hub_yaml["canvas-hub"].update(response["hub"])
        self.updateYAMLInfo()

        path = os.path.expanduser('~') + "/.mosaicdata/"
        cert_path = path + "certificate.pem.crt"
        private_path = path + "private.pem.key"

        cert_file = open(cert_path, "w")
        cert_file.write(response["certificatePem"])
        cert_file.close()

        private_file = open(private_path, "w")
        private_file.write(response["privateKey"])
        private_file.close()

    def getHostname(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('10.255.255.255', 1))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            self._logger.info("Unable to get hostname")
            return None

    def updateHostname(self, new_hostname):
        self._logger.info("Updating Hostname")
        hub_id = self.hub_yaml["canvas-hub"]["id"]
        hub_token = self.hub_yaml["canvas-hub"]["token"]
        url = "https://" + BASE_URL_API + "hubs/" + hub_id
        payload = {
            "hostname": new_hostname
        }
        authorization = "Bearer " + hub_token
        headers = {"Authorization": authorization}
        try:
            response = requests.post(url, json=payload, headers=headers).json()
            if response.get("status") >= 400:
                self._logger.info(response)
            else:
                if new_hostname:
                    self._logger.info("Hostname updated: %s" % new_hostname)
                    self.hub_yaml["canvas-hub"]["hostname"] = new_hostname
                    self.updateYAMLInfo()
                else:
                    self._logger.info("Deleting hostname")
                    del self.hub_yaml["canvas-hub"]["hostname"]
        except requests.exceptions.RequestException as e:
            self._logger.info(e)

    def makeShadowDeviceClient(self):
        self._logger.info("Making Shadow Client & Device")
        self.myShadow = Shadow.Shadow(self)
