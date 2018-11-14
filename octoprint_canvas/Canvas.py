import os
import zipfile
import StringIO
import json
import websocket
import requests
import ssl
import time


try:
    import thread
except ImportError:
    import _thread as thread
from ruamel.yaml import YAML
yaml = YAML(typ="safe")


def is_json(myjson):
    try:
        json_object = json.loads(myjson)
    except ValueError as e:
        return False
    return True


class Canvas():
    def __init__(self, plugin):
        plugin._logger.info("Hello from Canvas.py!")
        self._logger = plugin._logger
        self._plugin_manager = plugin._plugin_manager
        self._identifier = plugin._identifier
        # SETTINGS PLUGIN
        self._settings = plugin._settings

        self.ws_connection = False
        self.ws_disconnect = False
        self.chub_registered = False

        self.chub_yaml = self.loadChubData()

    ##############
    # 1. INITIAL FUNCTIONS
    ##############

    def loadChubData(self):
        self._logger.info("Loading HUB data")
        chub_dir_path = os.path.expanduser('~') + "/.mosaicdata"
        chub_file_path = chub_dir_path + "/canvas-hub-data.yml"

        # if /.mosaicdata doesn't exist yet, make the directory
        if not os.path.exists(chub_dir_path):
            os.mkdir(chub_path)

        # if the YML file doesn't exist, make the file
        if not os.path.isfile(chub_file_path):
            f = open(chub_file_path, "w")
            chub_template = ({'versions': {'turquoise': '1.0.0', 'global': '0.1.0', 'canvas-plugin': '0.1.0',
                                           'palette-plugin': '0.2.0', 'data-version': '0.0.1'},
                              'canvas-hub': {},
                              'canvas-users': {}})
            yaml.dump(chub_template, f)
            f.close()

        # access yaml file with all the info
        chub_data = open(chub_file_path, "r")
        chub_yaml = yaml.load(chub_data)
        chub_data.close()

        # if the yaml file exists already but doesn't have a "canvas-users" key and value yet
        if not "canvas-users" in chub_yaml:
            chub_yaml["canvas-users"] = {}
            chub_data = open(chub_file_path, "w")
            yaml.dump(chub_yaml, chub_data)
            chub_data.close()

        if "token" in chub_yaml["canvas-hub"]:
            self.chub_registered = True

        return chub_yaml

    def registerCHUB(self):
        if self.chub_registered is False:
            # if DIY CHUB
            if not "serial-number" in self.chub_yaml["canvas-hub"]:
                secret_key = yaml.load(self._settings.config_yaml)[
                    "server"]["secretKey"]
                self.registerCHUBAPICall(secret_key)
            # if regular CHUB
            else:
                chub_serial_number = self.chub_yaml["canvas-hub"]["serial-number"]
                self.registerCHUBAPICall(chub_serial_number)
        else:
            self._logger.info("C.HUB already registered")
            self.updateUI({"command": "HubRegistered"})

    def registerCHUBAPICall(self, chub_identifier):
        self._logger.info("Registering HUB to AMARANTH")

        url = "https://api-dev.canvas3d.co/hubs"
        data = {"name": chub_identifier}

        try:
            response = requests.put(url, json=data).json()
            if response.get("status") >= 400:
                self._logger.info(response)
            else:
                self.chub_yaml["canvas-hub"].update(response)
                self.updateYAMLInfo()
                self.chub_registered = True
                self.updateUI({"command": "HubRegistered"})
        except requests.exceptions.RequestException as e:
            print e

    ##############
    # 2. WEBSOCKET FUNCTIONS
    ##############

    def ws_on_message(self, ws, message):
        print("Just received a message from Canvas Server!")
        print("Received: " + message)

        if is_json(message) is True:
            response = json.loads(message)
            print(response["type"])
            if "CONN/OPEN" in response["type"]:
                print("Sending Hub Token")
                self.sendInitialHubToken()
            elif "CONN/CLOSED" in response["type"]:
                self.ws.close()
            elif "OP/DOWNLOAD" in response["type"]:
                print("HANDLING DL")
                self.downloadPrintFiles(response)
            elif "ERROR/INVALID_TOKEN" in response["type"]:
                print("HANDLING ERROR/INVALID_TOKEN")
                self.ws.close()

    def ws_on_error(self, ws, error):
        print("ERROR")
        print(error)
        if "ping/pong timed out" in error:
            self.ws_disconnect = True

    def ws_on_close(self, ws):
        print("### Closing Websocket ###")
        self.ws_connection = False
        self.checkWebsocketConnection()
        if self.ws_disconnect is True:
            while self.ws_connection is False:
                time.sleep(10)
                print("Trying to reconnect...")
                self.enableWebsocketConnection()

    def ws_on_open(self, ws):
        print("### Opening Websocket ###")
        if self.ws_disconnect is True:
            self.ws_disconnect = False
        self.ws_connection = True
        self.checkWebsocketConnection()

    def ws_on_pong(self, ws, pong):
        print("Received Pong")

    def runWebSocket(self):
        self.ws.run_forever(ping_interval=30, ping_timeout=15,
                            sslopt={"cert_reqs": ssl.CERT_NONE})

    def enableWebsocketConnection(self):
        # if C.HUB already has registered Canvas Users, enable websocket client
        if "canvas-users" in self.chub_yaml and self.chub_yaml["canvas-users"] and self.ws_connection is False:
            # prod: wss://hub-dev.canvas3d.co:8443
            # dev: ws://hub-dev.canvas3d.co:8443
            self.ws = websocket.WebSocketApp("ws://hub-dev.canvas3d.co:8443",
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
                    "There are no registered users. Please register a Canvas account.")

    def checkWebsocketConnection(self):
        if self.ws_connection is True:
            self.updateUI({"command": "Websocket", "data": True})
        else:
            self.updateUI({"command": "Websocket", "data": False})

    def sendInitialHubToken(self):
        data = {
            "type": "AUTH/TOKEN",
            "token": self.chub_yaml["canvas-hub"]["token"]
        }
        self.ws.send(json.dumps(data))

    ##############
    # 3. USER FUNCTIONS
    ##############

    def addUser(self, loginInfo):
        # Make POST request to canvas API to log in user
        url = "https://api-dev.canvas3d.co/users/login"
        # PRODUCTION: url = "https://api.canvas3d.io/users/login"

        if "username" in loginInfo["data"]:
            data = {"username": loginInfo["data"]["username"],
                    "password": loginInfo["data"]["password"]}
        elif "email" in loginInfo["data"]:
            data = {"email": loginInfo["data"]["email"],
                    "password": loginInfo["data"]["password"]}

        try:
            response = requests.post(url, json=data).json()
            if response.get("status") >= 400:
                self._logger.info("Error: Try Logging In Again")
                self._logger.info(response)
                self.updateUI({"command": "invalidUserCredentials"})
            else:
                self._logger.info("API response valid!")
                self.verifyUserInYAML(response)
        except requests.exceptions.RequestException as e:
            print e

    def downloadPrintFiles(self, data):
        user = self.chub_yaml["canvas-users"][data["userId"]]

        # user must have a valid token to enable the download
        token = user["token"]
        authorization = "Bearer " + token
        headers = {"Authorization": authorization}
        # DEV:
        url = "https://slice.api-dev.canvas3d.co/projects/" + \
            data["projectId"] + "/download"
        # url = "https://slice.api.canvas3d.io/projects/" + \
        #     data["projectId"] + "/download"

        response = requests.get(url, headers=headers)
        if response.ok:
            # unzip content and save it in the "watched" folder for Octoprint to automatically analyze and add to uploads folder
            z = zipfile.ZipFile(StringIO.StringIO(response.content))
            watched_path = self._settings.global_get_basefolder("watched")
            z.extractall(watched_path)

            self.updateUI({"command": "FileReceivedFromCanvas",
                           "data": data["filename"]})

    ##############
    # 4. HELPER FUNCTIONS
    ##############

    def verifyUserInYAML(self, data):
        # get list of all registered users on the C.HUB YML file
        registeredUsers = self.chub_yaml["canvas-users"]

        # if user is not registered in C.HUB YML file yet
        if data.get("id") not in registeredUsers:
            self._logger.info("USER IS NOT IN YAML FILE YET.")

           # if websocket is not already enabled, enable it
            if not self.ws_connection:
                self.enableWebsocketConnection()

            self.registerUserAndCHUB(data)
        else:
            self._logger.info("User already registered! You are good.")
            self.updateUI({"command": "UserAlreadyExists", "data": data})

    def updateRegisteredUsers(self):
        # make a list of usernames and their token_valid status
        if "canvas-users" in self.chub_yaml:
            list_of_users = map(
                lambda user: {key: user[key] for key in ["username"]}, self.chub_yaml["canvas-users"].values())
            self.updateUI(
                {"command": "DisplayRegisteredUsers", "data": list_of_users})

    def updateYAMLInfo(self):
        chub_data_path = os.path.expanduser(
            '~') + "/.mosaicdata/canvas-hub-data.yml"
        chub_data = open(chub_data_path, "w")
        yaml.dump(self.chub_yaml, chub_data)
        chub_data.close()

    def registerUserAndCHUB(self, data):

        self._logger.info("Sending chub_token and user_token to Canvas Server")
        chub_id = self.chub_yaml["canvas-hub"]["hub"]["id"]
        chub_token = self.chub_yaml["canvas-hub"]["token"]
        payload = {
            "userToken": data["token"]
        }

        url = "https://api-dev.canvas3d.co/hubs/" + chub_id + "/register"
        # PRODUCTION url = "https://api.canvas3d.io/hubs/" + chub_id +"/register"

        authorization = "Bearer " + chub_token
        headers = {"Authorization": authorization}

        try:
            response = requests.post(url, json=payload, headers=headers).json()
            if response.get("status") >= 400:
                self._logger.info(response)
            else:
                self.chub_yaml["canvas-users"][data.get("id")] = data
                self.updateYAMLInfo()
                self.updateRegisteredUsers()
                self.enableWebsocketConnection()
                self.updateUI({"command": "UserConnectedToHUB", "data": data})

        except requests.exceptions.RequestException as e:
            print e

    def updateUI(self, data):
        self._logger.info("Sending UIUpdate from Canvas")
        self._plugin_manager.send_plugin_message(self._identifier, data)
