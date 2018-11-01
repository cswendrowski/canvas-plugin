# coding=utf-8
from __future__ import absolute_import
from distutils.version import LooseVersion
# from flask import make_response, render_template
from octoprint.filemanager.destinations import FileDestinations

import requests
import octoprint.plugin
from . import Canvas


class CanvasPlugin(octoprint.plugin.TemplatePlugin,
                   octoprint.plugin.AssetPlugin,
                   octoprint.plugin.StartupPlugin,
                   octoprint.plugin.SimpleApiPlugin,
                   octoprint.plugin.EventHandlerPlugin,
                   octoprint.plugin.UiPlugin,
                   octoprint.plugin.ShutdownPlugin):

    # STARTUPPLUGIN
    def on_after_startup(self):
        self._logger.info("Canvas Plugin STARTED")
        self.canvas = Canvas.Canvas(self)
        self.canvas.enableWebsocketConnection()

        # temp = {
        #     "type": "DOWNLOAD",
        #     "userId": "8378eb95bbe499560d8a66b8d50b887a",
        #     "projectId": "ab6225f37b511d671bd27756af3cb299",
        #     "filename": "hello"
        # }
        # self.downloadPrintFiles(temp)

    def on_shutdown(self):
        self._logger.info("Canvas Plugin CLOSED")
        self.canvas.ws.close()

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
            self.canvas.connectToCanvas(data["email"], data["password"])

    # SIMPLEAPIPLUGIN GET, not really needed
    # def on_api_get(self, request):
    #     self._plugin_manager.send_plugin_message(
    #         self._identifier, "Omega Message")
    #     return flask.jsonify(foo="bar")

    # EVENTHANDLERPLUGIN: To be able to go from BE to FE
    def on_event(self, event, payload):
        if "ClientOpened" in event:
            self._logger.info("YOOOOOOOOOOOOOOOOOOOOOOO")
            list_of_users = map(
                lambda user: user['username'], self.canvas.chub_yaml["canvas-users"].values())
            data = {"command": "DisplayRegisteredUsers",
                    "data": list_of_users}
            self.canvas.updateUI(data)

    def get_template_configs(self):
        return [
            dict(type="tab", custom_bindings=True)
        ]

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
