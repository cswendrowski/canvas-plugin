import os
import zipfile
import StringIO
import json
import websocket
import requests


try:
    import thread
except ImportError:
    import _thread as thread
from ruamel.yaml import YAML
# from __init__ import on_event
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

        self.chub_yaml = self.loadChubData()

    def connectToCanvas(self, email, password):
        # Make POST request to canvas API to log in user
        url = "https://api.canvas3d.io/users/login"
        data = {"email": email, "password": password}

        try:
            response = requests.post(url, json=data).json()
            if response.get("status") >= 400:
                self._logger.info("Error: Try Logging In Again")
                # send message back to front-end that login was unsuccessful
            else:
                self._logger.info("API response valid!")
                self.verifyUserInYAML(response)
        except requests.exceptions.RequestException as e:
            print e

    def ws_on_message(self, ws, message):
        print("Just received a message from Canvas Server!")
        print("Received: " + message)

        if is_json(message) is True:
            response = json.loads(message)
            print(response["type"])
            if response["type"] is "TOKEN_VERIFICATION":
                self.token_validation_list = response["tokens"]
            elif response['type'] is "DOWNLOAD":
                self.downloadPrintFiles(response)

    def ws_on_error(self, ws, error):
        print(error)

    def ws_on_close(self, ws):
        print("### Closing Websocket ###")

    def ws_on_open(self, ws):
        print("### Opening Websocket ###")
        list_of_tokens = json.dumps(self.getListOfTokens())
        print("Sending tokens: " + list_of_tokens)
        self.ws.send(list_of_tokens)
        print("Sent")

    def enableWebsocketConnection(self):
        # if C.HUB already has registered Canvas Users, enable websocket client
        if self.chub_yaml["canvas-users"]:
            self._logger.info("There are registered users!")
            self.ws = websocket.WebSocketApp("ws://hub-dev.canvas3d.co",
                                             on_message=self.ws_on_message,
                                             on_error=self.ws_on_error,
                                             on_close=self.ws_on_close,
                                             on_open=self.ws_on_open)
            # self.ws.on_open = self.on_open
            thread.start_new_thread(self.ws.run_forever, ())
        else:
            self._logger.info(
                "There are no registered users. Please register a Canvas account.")

    def getListOfTokens(self):
        list_of_tokens = map(
            lambda user: user['token'], self.chub_yaml["canvas-users"].values())
        return {"type": "TOKENS", "tokens": list_of_tokens}

    def loadChubData(self):
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

        return chub_yaml

    def verifyUserInYAML(self, data):
        # get list of all registered users on the C.HUB YML file
        registeredUsers = self.chub_yaml["canvas-users"]

        # if user is not registered in C.HUB YML file yet
        if data.get("id") not in registeredUsers:
            self._logger.info("Saving New User in C.HUB YML")
            # save new user to YML file
            registeredUsers[data.get("id")] = data
            chub_data_path = os.path.expanduser(
                '~') + "/.mosaicdata/canvas-hub-data.yml"
            chub_data = open(chub_data_path, "w")
            yaml.dump(self.chub_yaml, chub_data)
            chub_data.close()

        # update UI with new list of users
        list_of_users = map(
            lambda user: user['username'], self.chub_yaml["canvas-users"].values())
        self.updateUI(
            {"command": "DisplayRegisteredUsers", "data": list_of_users})

    def downloadPrintFiles(self, data):
        token = self.chub_yaml["canvas-users"][data["userId"]]["token"]
        authorization = "Bearer " + token
        headers = {"Authorization": authorization}
        url = "https://slice.api.canvas3d.io/projects/" + \
            data["projectId"] + "/download"

        r = requests.get(url, headers=headers)
        if r.ok:
            z = zipfile.ZipFile(StringIO.StringIO(r.content))
            z.extractall()
            # self._logger.info(FileDestinations.LOCAL)

        # save to uploads folder

    # example for EVENTHANDLERPLUGIN
    def updateUI(self, data):
        self._logger.info("Sending UIUpdate")
        # dummy = ["cat", "dog", "turtle"]
        # dummyObj = {"name": "John", "age": "25"}
        self._plugin_manager.send_plugin_message(
            self._identifier, data)
