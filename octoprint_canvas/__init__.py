# coding=utf-8
from __future__ import absolute_import
from distutils.version import LooseVersion
from flask import make_response, render_template
from ruamel.yaml import YAML
yaml = YAML(typ="safe")

import os
import requests
import zipfile
import StringIO
import json
import octoprint.plugin
from websocket import create_connection
from octoprint.filemanager.destinations import FileDestinations
# import websocket
# try:
#     import thread
# except ImportError:
#     import _thread as thread
# import time


class CanvasPlugin(octoprint.plugin.TemplatePlugin,
                   octoprint.plugin.AssetPlugin,
                   octoprint.plugin.StartupPlugin,
                   octoprint.plugin.SimpleApiPlugin,
                   octoprint.plugin.EventHandlerPlugin,
                   octoprint.plugin.UiPlugin):

    # STARTUPPLUGIN
    def on_after_startup(self):
        self._logger.info("Canvas Plugin Started")
        self.chub_yaml = self.loadChubData()
        # self.downloadPrintFiles("ab6225f37b511d671bd27756af3cb299")
        self.enableWebsocketConnection()

    # ASSETPLUGIN

    def get_assets(self):
        return dict(
            css=["css/canvas.css"],
            js=["js/canvas.js"]
        )

    def get_latest(self, target, check, full_data=False, online=True):
        resp = requests.get(
            "http://emerald.mosaicmanufacturing.com/canvas-hub-canvas-test/latest")
        version_data = resp.json()
        version = version_data["versions"][0]["version"]
        current_version = check.get("current")
        information = dict(
            local=dict(
                name=current_version,
                value=current_version,
            ),
            remote=dict(
                name=version,
                value=version
            )
        )
        self._logger.info("current version: %s" % current_version)
        self._logger.info("remote version: %s" % version)
        needs_update = LooseVersion(current_version) < LooseVersion(version)
        self._logger.info("needs update: %s" % needs_update)
        return information, not needs_update

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
        # for details.
        return dict(
            canvas=dict(
                displayName="Canvas Plugin",
                displayVersion=self._plugin_version,
                current=self._plugin_version,
                python_checker=self,
                type="python_checker",
                command="/home/pi/test-version.sh",

                # update method: pip
                pip="https://gitlab.com/mosaic-mfg/canvas-plugin/-/archive/master/canvas-plugin-master.zip"
            )
        )

    # SIMPLEAPIPLUGIN POST, runs first before on_api_commands, responds to commands from palette,js, any strings inside array = mandatory
    def get_api_commands(self):
        return dict(
            connectCanvas=["email", "password"]
        )

    # SIMPLEAPIPLUGIN POST, to handle commands listed in get_api_commands
    def on_api_command(self, command, data):
        if command == "connectCanvas":
            self.connectToCanvas(data["email"], data["password"])

    # SIMPLEAPIPLUGIN GET, not really needed
    def on_api_get(self, request):
        self._plugin_manager.send_plugin_message(
            self._identifier, "Omega Message")
        return flask.jsonify(foo="bar")

    # EVENTHANDLERPLUGIN: To be able to go from BE to FE
    def on_event(self, event, payload):
        if "ClientOpened" in event:
            list_of_users = map(
                lambda user: user['username'], self.chub_yaml["canvas-users"].values())
            data = {"command": "DisplayRegisteredUsers",
                    "data": list_of_users}
            self.updateUI(data)
        elif "DisplayRegisteredUsers" in event:
            data = {"command": "DisplayRegisteredUsers", "data": payload}
            self.updateUI(data)

    # example for EVENTHANDLERPLUGIN

    def updateUI(self, data):
        self._logger.info("Sending UIUpdate")
        dummy = ["cat", "dog", "turtle"]
        dummyObj = {"name": "John", "age": "25"}
        self._plugin_manager.send_plugin_message(
            self._identifier, data)

    def get_template_configs(self):
        return [
            dict(type="tab", custom_bindings=True)
        ]


############
# CANVAS FUNCTIONS
####################


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
                self.downloadPrintFiles("ab6225f37b511d671bd27756af3cb299")
                # self.enableWebsocketConnection()

                # self.verifyUserInYAML(response)

        except requests.exceptions.RequestException as e:
            print e

    def enableWebsocketConnection(self):
        if "canvas-users" in self.chub_yaml:
            self._logger.info("There are registered users!")
            ws = create_connection("ws://hub-dev.canvas3d.co")
            print("Sending 'Hello, World'...")
            # make function to send C.HUB serial number
            ws.send("Hello, World")
            print("Sent")
            print("Receiving...")
            result = ws.recv()
            # make function call for printing here
            print("Received '%s'" % result)
            ws.close()
        else:
            self._logger.info(
                "There are no registered users. Please register a Canvas account.")

    def loadChubData(self):
        chub_path = os.path.expanduser('~') + "/.mosaicdata"

        # if /.mosaicdata doesn't exist yet, make the directory and the YML file
        if not os.path.exists(chub_path):
            os.mkdir(chub_path)
            f = open(chub_path + "/canvas-hub-data.yml", "w")
            f.close()

        # access yaml file with all the info
        chub_file_path = chub_path + "/canvas-hub-data.yml"
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
        self.on_event("DisplayRegisteredUsers", list_of_users)

    def downloadPrintFiles(self, project_id):
        # need user ID to locate token
        token = "Bearer " + "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1NDEwMTI4MTAsImV4cCI6MTU0MTYxNzYxMCwiaXNzIjoiQ2FudmFzIiwic3ViIjoiODM3OGViOTViYmU0OTk1NjBkOGE2NmI4ZDUwYjg4N2EifQ.nIeuSLWN_g3khHcL4zxigMp5Ke5LPOHM5zOhBur4oPY"
        headers = {"Authorization": token}
        url = "https://slice.api.canvas3d.io/projects/" + project_id + "/download"

        r = requests.get(url, headers=headers)
        if r.ok:
            z = zipfile.ZipFile(StringIO.StringIO(r.content))
            z.extractall()
            self._logger.info(FileDestinations.LOCAL)

        # save to uploads folder


    # If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
    # ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
    # can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Canvas"
__plugin_description__ = "A plugin to handle connecting and communicating with CANVAS (Beta)"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = CanvasPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
