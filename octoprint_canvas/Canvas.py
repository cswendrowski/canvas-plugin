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
        self._settings = plugin._settings

        self.ws_connection = False
        self.chub_registered = False

        self.chub_yaml = self.loadChubData()

    ##############
    # 1. INITIAL FUNCTIONS
    ##############

    def loadChubData(self):
        self._logger.info("Loading CHUB data")
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

        if "hubToken" in chub_yaml["canvas-hub"]:
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
            self._logger.info("CHUB already registered")
            self.updateUI({"command": "ChubRegistered"})

    def registerCHUBAPICall(self, chub_identifier):
        self._logger.info(chub_identifier)
        self._logger.info(
            "Making the call to the Canvas API Endpoint to register CHUB devices")

        temp = {
            "hubId": "asdad39239",
            "hubName": "Tomato",
            "hubToken": "7328283239nans"
        }

        self.chub_yaml["canvas-hub"].update(temp)
        self.chub_registered = True
        self.updateUI({"command": "ChubRegistered"})

        # url = "https://api.canvas3d.io/users/login"
        # data = {"email": email, "password": password}

        # try:
        #     response = requests.post(url, json=data).json()
        #     if response.get("status") >= 400:
        #         self._logger.info("Error: Try making the request again")
        #     else:
        #         self._logger.info("API response valid!")
        #         self.chub_registered = True
        #         self.chub_yaml["canvas-hub"].update(response)

        #         return response
        # except requests.exceptions.RequestException as e:
        #     print e

    ##############
    # 2. WEBSOCKET FUNCTIONS
    ##############

    def ws_on_message(self, ws, message):
        print("Just received a message from Canvas Server!")
        print("Received: " + message)

        if is_json(message) is True:
            response = json.loads(message)
            print(response["type"])
            # if "TOKEN_VERIFICATION" in response["type"]:
            #     # token_validation_list = response["tokens"]
            #     # self.updateTokenValidationInYAML(token_validation_list)
            #     # self.updateRegisteredUsers()
            if "DOWNLOAD" in response["type"]:
                self.downloadPrintFiles(response)

    def ws_on_error(self, ws, error):
        print(error)

    def ws_on_close(self, ws):
        print("### Closing Websocket ###")
        self.updateUI({"command": "Websocket", "data": False})
        self.ws_connection = False

    def ws_on_open(self, ws):
        print("### Opening Websocket ###")
        self.updateUI({"command": "Websocket", "data": True})
        # list_of_tokens = json.dumps(self.getListOfTokens())
        self.updateRegisteredUsers()
        # print("Sending tokens: " + list_of_tokens)
        # self.verifyTokens(list_of_tokens)
        print("Sent")

    def ws_on_pong(self, ws, pong):
        print("Received Pong")

    def enableWebsocketConnection(self):
        # if C.HUB already has registered Canvas Users, enable websocket client
        if "canvas-users" in self.chub_yaml and self.chub_yaml["canvas-users"]:
            self.ws = websocket.WebSocketApp("ws://hub-dev.canvas3d.co",
                                             on_message=self.ws_on_message,
                                             on_error=self.ws_on_error,
                                             on_close=self.ws_on_close,
                                             on_open=self.ws_on_open,
                                             on_pong=self.ws_on_pong)
            # self.ws.on_open = self.on_open
            thread.start_new_thread(lambda: self.ws.run_forever(
                ping_interval=30, ping_timeout=10), ())
            self.ws_connection = True
        else:
            self._logger.info(
                "There are no registered users. Please register a Canvas account.")

    # def verifyTokens(self, data):
    #     self.ws.send(data)

    # def updateTokenValidationInYAML(self, data):
    #     registeredUsers = self.chub_yaml["canvas-users"]

    #     # assign token status to each user account
    #     for user, userInfo in registeredUsers.iteritems():
    #         user_data = filter(
    #             lambda token_info: token_info["token"] == userInfo["token"], data)
    #         token_status = user_data[0]["valid"]
    #         registeredUsers[user]["token_valid"] = token_status

        # write this information to the YAML file
        # self.updateYAMLInfo()

    ##############
    # 3. USER FUNCTIONS
    ##############

    def addUser(self, email, password):
        # Make POST request to canvas API to log in user
        url = "https://api.canvas3d.io/users/login"
        data = {"email": email, "password": password}

        try:
            response = requests.post(url, json=data).json()
            if response.get("status") >= 400:
                self._logger.info("Error: Try Logging In Again")
                self.updateUI({"command": "invalidUserCredentials"})
                # send message back to front-end that login was unsuccessful
            else:
                self._logger.info("API response valid!")
                self.verifyUserInYAML(response)
                # MAKE ANOTHER API REQUEST TO CONNECT USER TOKEN AND CANVAS HUB
        except requests.exceptions.RequestException as e:
            print e

    def downloadPrintFiles(self, data):
        user = self.chub_yaml["canvas-users"][data["userId"]]

        # user must have a valid token to enable the download
        if user["token_valid"]:
            token = user["token"]
            authorization = "Bearer " + token
            headers = {"Authorization": authorization}
            url = "https://slice.api.canvas3d.io/projects/" + \
                data["projectId"] + "/download"

            response = requests.get(url, headers=headers)
            if response.ok:
                # unzip content and save it in the "watched" folder for Octoprint to automatically analyze and add to uploads folder
                z = zipfile.ZipFile(StringIO.StringIO(response.content))
                watched_path = self._settings.global_get_basefolder("watched")
                z.extractall(watched_path)
        else:
            self._logger.info("Token is invalid. Download will not initiate")

    ##############
    # 4. HELPER FUNCTIONS
    ##############

    def verifyUserInYAML(self, data):
        # get list of all registered users on the C.HUB YML file
        registeredUsers = self.chub_yaml["canvas-users"]

        # if user is not registered in C.HUB YML file yet
        if data.get("id") not in registeredUsers:
            self._logger.info("Saving New User in C.HUB YML")
            # save new user to YML file
            registeredUsers[data.get("id")] = data
            self.updateYAMLInfo()

           # if websocket is not already enabled, enable it
            if not self.ws_connection:
                self.enableWebsocketConnection()

            self.registerUserAndCHUB(data)
            self.updateUI({"command": "UserConnectedToCHUB", "data": data})
            # list_of_tokens = json.dumps(self.getListOfTokens())
            # self.verifyTokens(list_of_tokens)
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

    # def getListOfTokens(self):
    #     list_of_tokens = map(
    #         lambda user: user['token'], self.chub_yaml["canvas-users"].values())
    #     return {"type": "TOKENS", "tokens": list_of_tokens}

    def registerUserAndCHUB(self, userToken):
        chub_token = self.chub_yaml["canvas-hub"]["hubToken"]
        user_token = userToken
        self._logger.info("Sending chub_token and user_token to Canvas Server")
        # url = blablala
        # response = requests.post(url, json=data).json()
        # once response is good, update registered users + add dictionary key to confirm validation?
        self.updateRegisteredUsers()

    def updateUI(self, data):
        self._logger.info("Sending UIUpdate from Canvas")
        self._logger.info(data)
        self._plugin_manager.send_plugin_message(self._identifier, data)
