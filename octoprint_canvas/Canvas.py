import os
import zipfile
import StringIO
import json
import websocket
import requests
import ssl
import time
import math


try:
    import thread
except ImportError:
    import _thread as thread

from ruamel.yaml import YAML
yaml = YAML(typ="safe")

from dotenv import load_dotenv
env_path = os.path.abspath(".") + "/.env"
if os.path.abspath(".") is "/":
    env_path = "/home/pi/.env"
load_dotenv(env_path)
BASE_URL_API = os.getenv("DEV_BASE_URL_API", "api.canvas3d.io/")
BASE_URL_WS = os.getenv("DEV_BASE_URL_WS", "hub.canvas3d.io:")


def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except ValueError as e:
        return False
    return True


class Canvas():
    def __init__(self, plugin):
        self._logger = plugin._logger
        self._plugin_manager = plugin._plugin_manager
        self._identifier = plugin._identifier
        self._settings = plugin._settings

        self.ws_connection = False
        self.ws_disconnect = False
        self.hub_registered = False

        self.hub_yaml = self.loadHubData()
        self.registerHub()
        if self.ws_connection is False:
            self.enableWebsocketConnection()

    ##############
    # 1. SERVER STARTUP FUNCTIONS
    ##############

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
        if not "canvas-users" in hub_yaml:
            hub_yaml["canvas-users"] = {}
            hub_data = open(hub_file_path, "w")
            yaml.dump(hub_yaml, hub_data)
            hub_data.close()

        if "token" in hub_yaml["canvas-hub"]:
            self.hub_registered = True

        return hub_yaml

    def registerHub(self):
        if self.hub_registered is False:
            # if DIY Hub
            if not "serial-number" in self.hub_yaml["canvas-hub"]:
                secret_key = yaml.load(self._settings.config_yaml)[
                    "server"]["secretKey"]
                self.registerHubAPICall(secret_key)
            # if regular Hub
            else:
                hub_serial_number = self.hub_yaml["canvas-hub"]["serial-number"]
                self.registerHubAPICall(hub_serial_number)
        else:
            self._logger.info("HUB already registered")

    def registerHubAPICall(self, hub_identifier):
        self._logger.info("Registering HUB to AMARANTH")

        url = "https://" + BASE_URL_API + "hubs"
        data = {"name": hub_identifier}

        try:
            response = requests.put(url, json=data).json()
            if response.get("status") >= 400:
                self._logger.info(response)
            else:
                self.hub_yaml["canvas-hub"].update(response)
                self.updateYAMLInfo()
                self.hub_registered = True
                self.updateUI({"command": "HubRegistered"})
        except requests.exceptions.RequestException as e:
            self._logger.info(e)

    ##############
    # 2. CLIENT UI STARTUP FUNCTIONS
    ##############

    def getRegisteredUsers(self):
        hub_id = self.hub_yaml["canvas-hub"]["hub"]["id"]
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
                self._logger.info(
                    "Could not get updated list of registered users.")
            self.updateRegisteredUsers()
            self.enableWebsocketConnection()

        except requests.exceptions.RequestException as e:
            self._logger.info(e)

    def checkUserThemeSetting(self):
        if self._settings.get(["applyTheme"]):
            self.updateUI({"command": "toggleTheme", "data": True})
        elif not self._settings.get(["applyTheme"]):
            self.updateUI({"command": "toggleTheme", "data": False})

    ##############
    # 3. WEBSOCKET FUNCTIONS
    ##############

    def ws_on_message(self, ws, message):
        self._logger.info("Just received a message from Canvas Server!")
        self._logger.info("Received: " + message)

        if is_json(message) is True:
            response = json.loads(message)
            if "CONN/OPEN" in response["type"]:
                self.sendInitialHubToken()
            elif "CONN/CLOSED" in response["type"]:
                self.ws.close()
            elif "OP/DOWNLOAD" in response["type"]:
                self._logger.info("HANDLING DL")
                self.downloadPrintFiles(response, response["filename"])
            elif "ERROR/INVALID_TOKEN" in response["type"]:
                self._logger.info("HANDLING ERROR/INVALID_TOKEN")
                self.ws.close()
            elif "AUTH/UNREGISTER_USER" in response["type"]:
                self._logger.info("REMOVING USER")
                self.removeUserFromYAML(response["userId"])
            elif "AUTH/CONFIRM_TOKEN" in response["type"]:
                self.ws_connection = True
                self.checkWebsocketConnection()

    def ws_on_error(self, ws, error):
        self._logger.info("WS ERROR: " + str(error))
        if str(error) == "Connection is already closed.":
            self._logger.info("CANVAS server is down.")

    def ws_on_close(self, ws):
        self._logger.info("### Closing Websocket ###")
        self.ws_connection = False
        self.checkWebsocketConnection()

    def ws_on_open(self, ws):
        self._logger.info("### Opening Websocket ###")

    def ws_on_pong(self, ws, pong):
        self._logger.info("Received WS Pong")

    def runWebSocket(self):
        self.ws.run_forever(ping_interval=30, ping_timeout=5,
                            sslopt={"cert_reqs": ssl.CERT_NONE})
        # if websocket connection was disconnected, try to reconnect again
        if self.hub_yaml["canvas-users"]:
            time.sleep(10)
            self._logger.info("Trying to reconnect...")
            self.enableWebsocketConnection()

    def enableWebsocketConnection(self):
        # if HUB already has registered Canvas Users, enable websocket client
        if "canvas-users" in self.hub_yaml and self.hub_yaml["canvas-users"] and self.ws_connection is False:
            url = "ws://" + BASE_URL_WS + "8443"
            self.ws = websocket.WebSocketApp(url,
                                             on_message=self.ws_on_message,
                                             on_error=self.ws_on_error,
                                             on_close=self.ws_on_close,
                                             on_open=self.ws_on_open,
                                             on_pong=self.ws_on_pong
                                             )
            thread.start_new_thread(self.runWebSocket, ())
        else:
            if self.ws_connection is True:
                self._logger.info("Websocket already enabled.")
            else:
                self._logger.info(
                    "There are no registered Canvas accounts yet. Connection not established.")
                self.checkWebsocketConnection()

    def checkWebsocketConnection(self):
        if self.ws_connection is True:
            self.updateUI({"command": "Websocket", "data": True})
        else:
            if not self.hub_yaml["canvas-users"]:
                self.updateUI({"command": "Websocket", "data": False,
                               "reason": "account"})
            else:
                self.updateUI({"command": "Websocket", "data": False,
                               "reason": "server"})

    def sendInitialHubToken(self):
        data = {
            "type": "AUTH/TOKEN",
            "token": self.hub_yaml["canvas-hub"]["token"]
        }
        self.ws.send(json.dumps(data))

    ##############
    # 4. USER FUNCTIONS
    ##############

    def addUser(self, loginInfo):
        url = "https://" + BASE_URL_API + "users/login"

        if "username" in loginInfo["data"]:
            data = {"username": loginInfo["data"]["username"],
                    "password": loginInfo["data"]["password"]}
        elif "email" in loginInfo["data"]:
            data = {"email": loginInfo["data"]["email"],
                    "password": loginInfo["data"]["password"]}

        try:
            response = requests.post(url, json=data).json()
            if response.get("status") >= 400:
                self._logger.info(response)
                self.updateUI({"command": "invalidUserCredentials"})
            else:
                self.verifyUserInYAML(response)
        except requests.exceptions.RequestException as e:
            self._logger.info(e)

    def downloadPrintFiles(self, data, filename):
        token = self.hub_yaml["canvas-hub"]["token"]
        authorization = "Bearer " + token
        headers = {"Authorization": authorization}
        project_id = data["projectId"]
        url = "https://slice." + BASE_URL_API + "projects/" + \
            project_id + "/download"

        try:
            response = requests.get(url, headers=headers, stream=True)
            downloaded_file = self.streamFileProgress(
                response, filename, project_id)
            self.extractZipfile(downloaded_file, project_id)
        except requests.exceptions.RequestException as e:
            self._logger.info(e)

    ##############
    # 5. HELPER FUNCTIONS
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

           # if websocket is not already enabled, enable it
            if not self.ws_connection:
                self.enableWebsocketConnection()

            self.registerUserAndHub(data)
        else:
            self._logger.info("User already registered to HUB.")
            self.updateUI({"command": "UserAlreadyExists", "data": data})

    def updateRegisteredUsers(self):
        # make a list of usernames
        if "canvas-users" in self.hub_yaml:
            list_of_users = map(
                lambda user: {key: user[key] for key in ["username"]}, self.hub_yaml["canvas-users"].values())
            self.updateUI(
                {"command": "DisplayRegisteredUsers", "data": list_of_users})
            if not self.hub_yaml["canvas-users"] and self.ws_connection is True:
                self.ws.close()

    def updateYAMLInfo(self):
        hub_data_path = os.path.expanduser(
            '~') + "/.mosaicdata/canvas-hub-data.yml"
        hub_data = open(hub_data_path, "w")
        yaml.dump(self.hub_yaml, hub_data)
        hub_data.close()

    def registerUserAndHub(self, data):
        hub_id = self.hub_yaml["canvas-hub"]["hub"]["id"]
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
                self.enableWebsocketConnection()
                self.updateUI({"command": "UserConnectedToHUB", "data": data})

        except requests.exceptions.RequestException as e:
            self._logger.info(e)

    def updateUI(self, data):
        self._logger.info("Sending UIUpdate from Canvas")
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def streamFileProgress(self, response, filename, project_id):
        total_length = response.headers.get('content-length')
        self.updateUI({"command": "CANVASDownload",
                       "data": {"filename": filename, "projectId": project_id}, "status": "starting"})

        actual_file = ""
        current_downloaded = 0.00
        total_length = int(total_length)
        stream_size = total_length/100

        for data in response.iter_content(chunk_size=stream_size):
            actual_file += data
            current_downloaded += len(data)
            percentage_completion = int(math.floor(
                (current_downloaded/total_length)*100))
            self.updateUI({"command": "CANVASDownload",
                           "data": {"current": percentage_completion, "projectId": project_id}, "status": "downloading"})
        return actual_file

    def extractZipfile(self, file, project_id):
        z = zipfile.ZipFile(StringIO.StringIO(file))
        filename = z.namelist()[0]
        watched_path = self._settings.global_get_basefolder("watched")
        z.extractall(watched_path)
        self.updateUI({"command": "CANVASDownload",
                       "data": {"filename": filename, "projectId": project_id}, "status": "received"})
