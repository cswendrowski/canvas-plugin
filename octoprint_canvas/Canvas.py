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
    # 1. INITIAL FUNCTIONS
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

        url = "https://api-dev.canvas3d.co/hubs"
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
            print e

    ##############
    # 2. WEBSOCKET FUNCTIONS
    ##############

    def ws_on_message(self, ws, message):
        print("Just received a message from Canvas Server!")
        print("Received: " + message)

        if is_json(message) is True:
            response = json.loads(message)
            if "CONN/OPEN" in response["type"]:
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
        print("WS ERROR: " + str(error))
        if "ping/pong timed out" in error:
            self.ws_disconnect = True

    def ws_on_close(self, ws):
        print("### Closing Websocket ###")
        self.ws_connection = False
        self.checkWebsocketConnection()

    def ws_on_open(self, ws):
        print("### Opening Websocket ###")
        if self.ws_disconnect is True:
            self.ws_disconnect = False
        self.ws_connection = True
        self.checkWebsocketConnection()

    def ws_on_pong(self, ws, pong):
        print("Received WS Pong")

    def runWebSocket(self):
        self.ws.run_forever(ping_interval=30, ping_timeout=5,
                            sslopt={"cert_reqs": ssl.CERT_NONE})
        # if websocket connection was disconnected, try to reconnect again
        if self.ws_disconnect is True:
            time.sleep(10)
            print("Trying to reconnect...")
            self.enableWebsocketConnection()

    def enableWebsocketConnection(self):
        # if HUB already has registered Canvas Users, enable websocket client
        if "canvas-users" in self.hub_yaml and self.hub_yaml["canvas-users"] and self.ws_connection is False:
            # prod: wss: // hub.canvas3d.io: 8443
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
                    "There are no registered Canvas accounts yet. Connection not established.")

    def checkWebsocketConnection(self):
        if self.ws_connection is True:
            self.updateUI({"command": "Websocket", "data": True})
        else:
            self.updateUI({"command": "Websocket", "data": False})

    def sendInitialHubToken(self):
        data = {
            "type": "AUTH/TOKEN",
            "token": self.hub_yaml["canvas-hub"]["token"]
        }
        self.ws.send(json.dumps(data))

    ##############
    # 3. USER FUNCTIONS
    ##############

    def addUser(self, loginInfo):
        url = "https://api-dev.canvas3d.co/users/login"

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
            print e

    def removeUser(self, userInfo):
        username = userInfo["data"]
        hub_id = self.hub_yaml["canvas-hub"]["hub"]["id"]

        registeredUsers = self.hub_yaml["canvas-users"]
        for user in registeredUsers.values():
            if user["username"] == username:
                user_token = user["token"]
                user_id = user["id"]

        url = "https://api-dev.canvas3d.co/hubs/" + hub_id + "/unregister"

        authorization = "Bearer " + user_token
        headers = {"Authorization": authorization}

        try:
            response = requests.post(url, headers=headers).json()
            if response.get("status") >= 400:
                self._logger.info("ERROR")
            else:
                self.removeUserFromYAML(user_id, username)
        except requests.exceptions.RequestException as e:
            print e

    def downloadPrintFiles(self, data):
        user = self.hub_yaml["canvas-users"][data["userId"]]

        token = user["token"]
        authorization = "Bearer " + token
        headers = {"Authorization": authorization}
        url = "https://slice.api-dev.canvas3d.co/projects/" + \
            data["projectId"] + "/download"

        response = requests.get(url, headers=headers)
        if response.ok:
            # unzip content and save it in the "watched" folder for Octoprint to automatically analyze and add to uploads folder
            z = zipfile.ZipFile(StringIO.StringIO(response.content))
            filename = z.namelist()[0]
            self.updateUI({"command": "CanvasDownloadStart",
                           "data": {"filename": filename, "status": "incoming"}})
            watched_path = self._settings.global_get_basefolder("watched")
            z.extractall(watched_path)
            self.updateUI({"command": "FileReceivedFromCanvas",
                           "data": filename})

    ##############
    # 4. HELPER FUNCTIONS
    ##############

    def removeUserFromYAML(self, user_id, username):
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

        url = "https://api-dev.canvas3d.co/hubs/" + hub_id + "/register"
        authorization = "Bearer " + hub_token
        headers = {"Authorization": authorization}

        try:
            response = requests.post(url, json=payload, headers=headers).json()
            if response.get("status") >= 400:
                self._logger.info(response)
            else:
                self.hub_yaml["canvas-users"][data.get("id")] = data
                self.updateYAMLInfo()
                self.updateRegisteredUsers()
                self.enableWebsocketConnection()
                self.updateUI({"command": "UserConnectedToHUB", "data": data})

        except requests.exceptions.RequestException as e:
            print e

    def updateUI(self, data):
        self._logger.info("Sending UIUpdate from Canvas")
        self._plugin_manager.send_plugin_message(self._identifier, data)
