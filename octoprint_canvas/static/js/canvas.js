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
    CanvasUI.removePopup();
    CanvasUI.addNotificationList();
  };

  self.onEventFileAdded = payload => {
    if ($("body").find(`.canvas-progress-bar .file-download-name:contains("${payload.name}")`)) {
      CanvasUI.updateFileReady(payload.name);
    }
  };

  self.onDataUpdaterReconnect = () => {
    CanvasUI.removePopup();
    CanvasUI.addNotificationList();
  };

  self.onEventConnected = () => {
    self.toggleTheme();
  };

  self.addUser = () => {
    CanvasUI.loadingOverlay(true, 'addUser');
    const propertyName = self.userInput().includes("@") ? "email" : "username"
    const payload = {
      command: "addUser",
      data: {
        [propertyName]: self.userInput(),
        password: self.password(),
      },
    };
    self.ajaxRequest(payload).always(value => {
      $(".add-user input").val("");
      CanvasUI.loadingOverlay(false);
    })
  };

  self.handleAWSConnection = data => {
    let textToDisplay = ["", "", ""];
    if (data.data === true) {
      textToDisplay = ["Connected", "Connected to CANVAS", "Your Hub is properly connected to CANVAS"];
    } else {
      textToDisplay[0] = "Not Connected";
      textToDisplay[1] = "Not connected to CANVAS";
      if (data.reason === "account") {
        textToDisplay[2] = "No CANVAS accounts linked to this Hub. Please make sure you have at least 1 CANVAS account linked to enable the connection.";
      } else if (data.reason === "server") {
        textToDisplay[2] = `There seems to be an issue connecting to CANVAS.
        The plugin will automatically try to re-connect until the connection is re-established.
        In the meanwhile, please download your CANVAS files manually and upload them to the Hub.`;
      }
    }
    self.connectionStatus(textToDisplay[0]);
    self.connectionInfoHeading(textToDisplay[1]);
    self.connectionInfoBody(textToDisplay[2]);
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
      CanvasUI.toggleLogo(applyTheme);
    } else {
      self.applyTheme(false);
      $("html").removeClass("canvas-theme");
      CanvasUI.toggleLogo(applyTheme);
    }

    // Event listener for when user changes the theme settings
    $(".theme-input").on("change", event => {
      applyTheme = self.settings.settings.plugins.canvas.applyTheme();

      if (applyTheme) {
        self.applyTheme(true);
        $("html").addClass("canvas-theme");
        CanvasUI.toggleLogo(applyTheme);
      } else {
        self.applyTheme(false);
        $("html").removeClass("canvas-theme");
        CanvasUI.toggleLogo(applyTheme);
      }
    });
  };

  self.changeImportantUpdateSettings = condition => {
    displayImportantUpdateAlert = !condition;

    const payload = {
      command: "changeImportantUpdateSettings",
      condition: displayImportantUpdateAlert
    };

    self.ajaxRequest(payload).then(res => {
      self.settings.saveData();
    });
  };

  self.ajaxRequest = payload => {
    return $.ajax({
      url: API_BASEURL + "plugin/canvas",
      type: "POST",
      dataType: "json",
      data: JSON.stringify(payload),
      contentType: "application/json; charset=UTF-8"
    });
  };

  // Receive messages from the OctoPrint server
  self.onDataUpdaterPluginMessage = (pluginIdent, message) => {
    if (pluginIdent === "canvas") {
      switch (message.command) {
        case "DisplayRegisteredUsers":
          self.users(message.data);
          break;
        case "AWS":
          self.handleAWSConnection(message);
          break;
        case "UserConnectedToHUB":
          CanvasAlerts.userAddedSuccess(message.data.username);
          break;
        case "UserAlreadyExists":
          CanvasAlerts.userExistsAlready(message.data.username);
          break;
        case "invalidUserCredentials":
          CanvasAlerts.userInvalidCredentials();
          break;
        case "UserDeleted":
          CanvasAlerts.userDeletedSuccess(message.data);
          break;
        case "hubNotRegistered":
          CanvasAlerts.hubNotRegistered();
          break;
        case "CANVASDownload":
          if (message.status === "starting") {
            CanvasUI.displayNotification(message.data);
          } else if (message.status === "downloading") {
            CanvasUI.updateDownloadProgress(message.data);
          } else if (message.status === "received") {
            CanvasUI.updateFileReceived(message.data);
          }
          break;
        case "importantUpdate":
          $("body").on("click", ".update-checkbox input", event => {
            self.changeImportantUpdateSettings(event.target.checked);
          });
          CanvasAlerts.importantUpdate(message.data);
          break;
        default:
        // do nothing
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
