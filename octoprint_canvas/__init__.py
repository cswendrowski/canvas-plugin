# coding=utf-8
from __future__ import absolute_import
from distutils.version import LooseVersion

import requests
import octoprint.plugin
from . import Canvas


class CanvasPlugin(octoprint.plugin.TemplatePlugin,
                   octoprint.plugin.AssetPlugin,
                   octoprint.plugin.StartupPlugin,
                   octoprint.plugin.SimpleApiPlugin,
                   octoprint.plugin.EventHandlerPlugin,
                   octoprint.plugin.SettingsPlugin
                   ):

    # STARTUPPLUGIN
    def on_after_startup(self):
        self._logger.info("%s Plugin STARTED" % self._plugin_info)
        self.canvas = Canvas.Canvas(self)
        self.canvas.checkFor0cf0()
        self.canvas.checkIfRootCertExists()
        self.canvas.updatePluginVersions()
        self.canvas.checkForRegistrationAndVersion()

    # TEMPLATEPLUGIN
    def get_template_configs(self):
        return [
            dict(type="navbar", custom_bindings=False),
            dict(type="settings", custom_bindings=False)
        ]

    # ASSETPLUGIN
    def get_assets(self):
        return dict(
            css=["css/canvas.css"],
            js=["js/canvas.js", "js/utils/alerts.js", "js/utils/ui.js"],
            less=["less/canvas.less"]
        )

    def get_settings_defaults(self):
        return dict(applyTheme=True, importantUpdate=True)

    def get_latest(self, target, check, full_data=False, online=True):
        resp = requests.get("http://emerald.mosaicmanufacturing.com/canvas-hub-canvas/latest")
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

        # check if feature-breaking update is upcoming
        if current_version == "2.0.0" and version == "x.x.x" and needs_update:
            self._logger.info("Important Update Detected")
            self.displayImportantUpdateAlert = True

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
            addUser=["data"],
            changeImportantUpdateSettings=["condition"]
        )

    # SIMPLEAPIPLUGIN POST, to handle commands listed in get_api_commands
    def on_api_command(self, command, data):
        if command == "addUser":
            self.canvas.addUser(data)
        elif command == "changeImportantUpdateSettings":
            self.canvas.changeImportantUpdateSettings(data["condition"])

    # EVENTHANDLERPLUGIN
    def on_event(self, event, payload):
        try:
            if "Startup" in event:
                self.displayImportantUpdateAlert = False
            elif "ClientOpened" in event:
                if self.displayImportantUpdateAlert and self._settings.get(["importantUpdate"]):
                    self.canvas.updateUI({"command": "importantUpdate", "data": "x.x.x"})
                self.canvas.checkAWSConnection()
                if self.canvas.hub_registered is True:
                    self.canvas.getRegisteredUsers()
                if self.canvas.hub_yaml["canvas-users"] and self.canvas.aws_connection is True:
                    try:
                        self.canvas.myShadow.shadowGet()
                    except:
                        self._logger.info("Shadow Device not created yet")
            elif "Shutdown" in event:
                if self.canvas.aws_connection is True:
                    self.canvas.myShadow.disconnect()
        except Exception as e:
            self._logger.info(e)


# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "CANVAS"
__plugin_description__ = "A plugin to handle communication with CANVAS"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = CanvasPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
