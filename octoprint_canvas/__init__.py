# coding=utf-8
from __future__ import absolute_import

import requests
from distutils.version import LooseVersion
import octoprint.plugin

class CanvasPlugin(octoprint.plugin.StartupPlugin):
    def on_after_startup(self):
        self._logger.info("Canvas Plugin Started")

    def get_latest(self, target, check, full_data=False, online=True):
        resp = requests.get("http://emerald.mosaicmanufacturing.com/canvas-hub-canvas-test/latest")
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

# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Canvas Plugin"
__plugin_description__ = "A plugin to handle connecting and communicating with CANVAS (Beta)"
def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = CanvasPlugin()
    
    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
