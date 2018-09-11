# coding=utf-8
from __future__ import absolute_import

### (Don't forget to remove me)
# This is a basic skeleton for your plugin's __init__.py. You probably want to adjust the class name of your plugin
# as well as the plugin mixins it's subclassing from. This is really just a basic skeleton to get you started.

import octoprint.plugin

class CanvasPlugin(octoprint.plugin.StartupPlugin):
    def on_after_startup(self):
        self._logger.info("Canvas Plugin Started")

    def get_latest(self, target, check, online=True):
        information =dict(
		local=dict(
			name="0.1.0",
		    value="0.1.0",
		),
		remote=dict(
			name="0.5.0",
			value="0.5.0"
		)
	)
        is_current = False
        return information, is_current

    def get_update_information(self):
        # Define the configuration for your plugin to use with the Software Update
        # Plugin here. See https://github.com/foosel/OctoPrint/wiki/Plugin:-Software-Update
        # for details.
        return dict(
	    canvas=dict(
	        displayName="Canvas Plugin",
                displayVersion=self._plugin_version,
                current=self._plugin_version,
                python_checker=self.get_latest,
	        #type="commandline",
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
