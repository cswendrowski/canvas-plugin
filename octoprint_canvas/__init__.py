# coding=utf-8
from __future__ import absolute_import

import requests
from distutils.version import LooseVersion
import octoprint.plugin


class CanvasPlugin(octoprint.plugin.TemplatePlugin,
                   octoprint.plugin.AssetPlugin,
                   octoprint.plugin.StartupPlugin,
                   octoprint.plugin.SimpleApiPlugin,
                   octoprint.plugin.EventHandlerPlugin):

    def on_after_startup(self):
        self._logger.info("Canvas Plugin Started")

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

    # POST, runs first before on_api_commands, responds to commands from palette,js, any strings inside array = mandatory
    def get_api_commands(self):
        return dict(
            connectCanvas=["test"]
        )

    # POST, to handle commands from get_api_commands
    def on_api_command(self, command, data):
        if command == "connectCanvas":
            self._logger.info(data["test"])

    # GET, not really needed
    def on_api_get(self, request):
        self._plugin_manager.send_plugin_message(
            self._identifier, "Omega Message")
        return flask.jsonify(foo="bar")

    # EVENTHANDLERPLUGIN: To be able to go from BE to FE
    def on_event(self, event, payload):
        if "ClientOpened" in event:
            self.updateUI()

    # example for EVENTHANDLERPLUGIN
    def updateUI(self):
        self._logger.info("Sending UIUpdate")
        self._plugin_manager.send_plugin_message(
            self._identifier, "Got here from init.py")


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
