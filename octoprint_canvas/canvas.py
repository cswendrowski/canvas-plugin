class Canvas():
  def __init__(self, plugin):
    plugin._logger.info("Hello from Canvas!")
        self._logger = plugin._logger
        self._printer = plugin._printer
        self._plugin_manager = plugin._plugin_manager
        self._identifier = plugin._identifier
        self._settings = plugin._settings