function CanvasViewModel(parameters) {
  var self = this;

  self.settings = parameters[0];
  self.appearance = parameters[1];
  self.files = parameters[2];

  self.userInput = ko.observable();
  self.password = ko.observable();
  self.connectionStatus = ko.observable();
  self.connectionInfoHeading = ko.observable();
  self.connectionInfoBody = ko.observable();
  self.users = ko.observable([]);
  self.applyTheme = ko.observable();
  self.brand = ko.computed(function () {
    return self.applyTheme() ? "CANVAS Hub" : "OctoPrint";
  });

  self.modifyAppearanceVM = () => {
    self.appearance.name.subscribe(function () {
      if (self.appearance.name() === "CANVAS Hub" || self.appearance.name() === "OctoPrint") {
        self.appearance.name("");
      }
    });

    self.appearance.brand = ko.pureComputed(function () {
      if (self.applyTheme()) {
        if (self.appearance.name()) {
          return self.brand() + " (" + self.appearance.name() + ")";
        } else {
          return self.brand();
        }
      } else {
        if (self.appearance.name()) {
          return self.appearance.name();
        } else {
          return self.brand();
        }
      }
    });

    self.appearance.fullbrand = ko.pureComputed(function () {
      if (self.applyTheme()) {
        if (self.appearance.name()) {
          return self.brand() + ": " + self.appearance.name();
        } else {
          return self.brand();
        }
      } else {
        if (self.appearance.name()) {
          return self.brand() + ": " + self.appearance.name();
        } else {
          return self.brand();
        }
      }
    });

    self.appearance.title = ko.pureComputed(function () {
      if (self.applyTheme()) {
        if (self.appearance.name()) {
          return self.appearance.name() + " [" + self.brand() + "]";
        } else {
          return self.brand();
        }
      } else {
        if (self.appearance.name()) {
          return self.appearance.name() + " [" + self.brand() + "]";
        } else {
          return self.brand();
        }
      }
    });
  };

  self.modifyFilesVM = () => {
    self.files.getSuccessClass = function (data) {
      if (!data["prints"] || !data["prints"]["last"]) {
        if (data.name.includes(".mcf.gcode")) {
          return "palette-tag";
        } else {
          return "";
        }
      } else {
        if (data.name.includes(".mcf.gcode")) {
          return data["prints"]["last"]["success"] ? "text-success palette-tag" : "text-error palette-tag";
        } else {
          return data["prints"]["last"]["success"] ? "text-success" : "text-error";
        }
      }
    };
  };

  self.modifyAppearanceVM();
  self.modifyFilesVM();

  self.onBeforeBinding = () => {
    self.applyTheme(self.settings.settings.plugins.canvas.applyTheme());
  };

  self.onAfterBinding = () => {
    self.toggleTheme();
    self.files.requestData();
  };

  self.onStartupComplete = () => {
    UI.removePopup();
    UI.addNotificationList();
  };

  self.onEventFileAdded = payload => {
    if ($("body").find(`.canvas-progress-bar .file-download-name:contains("${payload.name}")`)) {
      UI.updateFileReady(payload.name);
    }
  };

  self.onDataUpdaterReconnect = () => {
    UI.removePopup();
    UI.addNotificationList();
  };

  self.onEventConnected = () => {
    self.toggleTheme();
  };

  self.addUser = () => {
    UI.loadingOverlay(true);
    let payload = { command: "addUser", data: { username: self.userInput(), password: self.password() } };

    if (self.userInput().includes("@")) {
      payload = { command: "addUser", data: { email: self.userInput(), password: self.password() } };
    }

    $.ajax({
      url: API_BASEURL + "plugin/canvas",
      type: "POST",
      dataType: "json",
      data: JSON.stringify(payload),
      contentType: "application/json; charset=UTF-8"
    });
  };

  self.handleAWSConnection = data => {
    if (data.data === true) {
      self.connectionStatus("Connected");
      self.connectionInfoHeading("Connected to CANVAS");
      self.connectionInfoBody("Your Hub is properly connected to CANVAS");
    } else {
      self.connectionStatus("Not Connected");
      self.connectionInfoHeading("Not connected to CANVAS");
      if (data.reason === "account") {
        self.connectionInfoBody(
          "No CANVAS accounts linked to this Hub. Please make sure you have at least 1 CANVAS account linked to enable the connection."
        );
      } else if (data.reason === "server") {
        self.connectionInfoBody(
          "There seems to be an issue connecting to CANVAS. The plugin will automatically try to re-connect until the connection is re-established. In the meanwhile, please download your CANVAS files manually and upload them to the Hub."
        );
      }
    }
  };

  self.toggleStatusInfo = () => {
    $(".connection-info-text").toggle(50);
  };

  self.toggleTheme = condition => {
    let applyTheme = self.settings.settings.plugins.canvas.applyTheme();

    // Apply theme immediately
    if (applyTheme) {
      self.applyTheme(true);
      $("html").addClass("canvas-theme");
      UI.toggleLogo(applyTheme);
    } else {
      self.applyTheme(false);
      $("html").removeClass("canvas-theme");
      UI.toggleLogo(applyTheme);
    }

    // Event listener for when user changes the theme settings
    $(".theme-input").on("change", event => {
      applyTheme = self.settings.settings.plugins.canvas.applyTheme();

      if (applyTheme) {
        self.applyTheme(true);
        $("html").addClass("canvas-theme");
        UI.toggleLogo(applyTheme);
      } else {
        self.applyTheme(false);
        $("html").removeClass("canvas-theme");
        UI.toggleLogo(applyTheme);
      }
    });
  };

  self.changeImportantUpdateSettings = condition => {
    displayImportantUpdateAlert = !condition;

    let payload = {
      command: "changeImportantUpdateSettings",
      condition: displayImportantUpdateAlert
    };

    $.ajax({
      url: API_BASEURL + "plugin/canvas",
      type: "POST",
      dataType: "json",
      data: JSON.stringify(payload),
      contentType: "application/json; charset=UTF-8"
    }).then(res => {
      self.settings.saveData();
    });
  };

  // Receive messages from the OctoPrint server
  self.onDataUpdaterPluginMessage = (pluginIdent, message) => {
    if (pluginIdent === "canvas") {
      console.log(message);
      if (message.command === "DisplayRegisteredUsers") {
        self.users(message.data);
      } else if (message.command === "AWS") {
        self.handleAWSConnection(message);
      } else if (message.command === "UserConnectedToHUB") {
        $(".add-user input").val("");
        UI.loadingOverlay(false);
        Alerts.userAddedSuccess(message.data.username);
      } else if (message.command === "UserAlreadyExists") {
        $(".add-user input").val("");
        UI.loadingOverlay(false);
        Alerts.userExistsAlready(message.data.username);
      } else if (message.command === "invalidUserCredentials") {
        $(".add-user input").val("");
        UI.loadingOverlay(false);
        Alerts.userInvalidCredentials();
      } else if (message.command === "UserDeleted") {
        Alerts.userDeletedSuccess(message.data);
      } else if (message.command === "CANVASDownload") {
        if (message.status === "starting") {
          UI.displayNotification(message.data);
        } else if (message.status === "downloading") {
          UI.updateDownloadProgress(message.data);
        } else if (message.status === "received") {
          UI.updateFileReceived(message.data);
        }
      } else if (message.command === "importantUpdate") {
        $("body").on("click", ".update-checkbox input", event => {
          self.changeImportantUpdateSettings(event.target.checked);
        });
        Alerts.importantUpdate(message.data);
      }
    }
  };
}

/* ======================
  RUN
  ======================= */


$(function () {
  OCTOPRINT_VIEWMODELS.push({
    // This is the constructor to call for instantiating the plugin
    construct: CanvasViewModel, // This is a list of dependencies to inject into the plugin. The order will correspond to the "parameters" arguments above
    dependencies: ["settingsViewModel", "appearanceViewModel", "filesViewModel"], // Finally, this is the list of selectors for all elements we want this view model to be bound to.
    elements: ["#tab_plugin_canvas"]
  });
});
