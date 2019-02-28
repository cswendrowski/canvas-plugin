if (!document.getElementById("material-icons")) {
  let link = document.createElement("link");
  link.id = "material-icons";
  link.href = "https://fonts.googleapis.com/icon?family=Material+Icons";
  link.rel = "stylesheet";
  document.head.appendChild(link);
}
if (!document.getElementById("sweetalert2-styling")) {
  let link = document.createElement("link");
  link.id = "sweetalert2-styling";
  link.href = "https://cdnjs.cloudflare.com/ajax/libs/limonte-sweetalert2/7.29.0/sweetalert2.min.css";
  link.rel = "stylesheet";
  document.head.appendChild(link);
}
if (!document.getElementById("sweetalert2-script")) {
  let script = document.createElement("script");
  script.id = "sweetalert2-script";
  script.src = "https://cdnjs.cloudflare.com/ajax/libs/limonte-sweetalert2/7.29.0/sweetalert2.min.js";
  document.head.appendChild(script);
}

const canvasApp = {};

/* ======================
  CANVAS THEME FUNCTIONALITIES
  ======================= */

/* 1. Replaces Octoprint Logo with Mosaic */
canvasApp.toggleLogo = condition => {
  if (condition) {
    $("head")
      .find('link[rel="shortcut icon"]')
      .attr("href", "/plugin/canvas/static/img/Mosaic_Icon_Square.png");
  } else {
    $("head")
      .find('link[rel="shortcut icon"]')
      .attr("href", "/static/img/tentacle-20x20@2x.png");
  }
};

/* 2. Display popup notifications for files incoming and received from Canvas */
canvasApp.displayNotification = data => {
  // if a prior popup with the same file is currently on the page, remove it
  if ($("body").find(`#${data.projectId}`).length > 0) {
    $("body")
      .find(`#${data.projectId}`)
      .fadeOut(1000, function() {
        this.remove();
      });
  }
  let notification = $(`<li id="${data.projectId}" class="progress-bar popup-notification">
            <i class="material-icons remove-popup">clear</i>
            <div class="popup-heading">
              <h6 class="popup-title">CANVAS File Incoming...</h6>
              <div class="small-loader"></div>
            </div>
            <p class="file-download-name">${data.filename}</p>
            <div class="total-bar">
              <div class="current-bar">
                <div class="progression-tool-tip"></div>
                <span>&nbsp;</span>
              </div>
            </div>
            </li>`).hide();
  $(".side-notifications-list").append(notification);
  notification.fadeIn(200);
};

/* 2.1 Update the download progress (%) on UI */
canvasApp.updateDownloadProgress = data => {
  if (data.current === 0) {
    $("body")
      .find(`#${data.projectId} .total-bar`)
      .css("position", "static");
    $("body")
      .find(`#${data.projectId} .current-bar`)
      .css("position", "relative");
    $("body")
      .find(`#${data.projectId} .progression-tool-tip`)
      .css({ left: "0%", right: "auto", visibility: "visible" })
      .removeClass("tool-tip-arrow");
  } else if (data.current === 10) {
    $("body")
      .find(`#${data.projectId} .progression-tool-tip`)
      .css({ left: "auto", right: "-13.5px" })
      .addClass("tool-tip-arrow");
  } else if (data.current === 96) {
    $("body")
      .find(`#${data.projectId} .total-bar`)
      .css("position", "relative");
    $("body")
      .find(`#${data.projectId} .current-bar`)
      .css("position", "static");
    $("body")
      .find(`#${data.projectId} .progression-tool-tip`)
      .css({ left: "auto", right: "0%" })
      .removeClass("tool-tip-arrow");
  }
  $("body")
    .find(`#${data.projectId} .current-bar`)
    .css("width", data.current + "%");
  $("body")
    .find(`#${data.projectId} .progression-tool-tip`)
    .text(data.current + "%");
};

/* 2.2 Update download progress when file is received and extracted */
canvasApp.updateFileReceived = data => {
  $("body")
    .find(`#${data.projectId} .popup-title`)
    .text("File Received. Please Wait...")
    .hide()
    .fadeIn(200);
  $("body")
    .find(`#${data.projectId} .small-loader`)
    .fadeIn(200);
  $("body")
    .find(`#${data.projectId} .total-bar`)
    .fadeOut(200);
  $("body")
    .find(`#${data.projectId} .file-download-name`)
    .text(data.filename)
    .hide()
    .fadeIn(200);
};

/* 2.3 Update download progress when file analysis is done */
canvasApp.updateFileReady = filename => {
  $("body")
    .find(`.progress-bar .file-download-name:contains("${filename}")`)
    .siblings(".popup-heading")
    .children(".popup-title")
    .text("CANVAS File Added")
    .hide()
    .fadeIn(200);
  $("body")
    .find(`.progress-bar .file-download-name:contains("${filename}")`)
    .siblings(".popup-heading")
    .children(".small-loader")
    .remove();
  setTimeout(function() {
    $("body")
      .find(`.progress-bar .file-download-name:contains("${filename}")`)
      .closest("li")
      .addClass("highlight-glow-received");
  }, 400);
};

/* 3. Remove popup notifications */
canvasApp.removePopup = () => {
  $("body").on("click", ".side-notifications-list .remove-popup", function() {
    $(this)
      .closest("li")
      .fadeOut(200, function() {
        $(this).remove();
      });
  });
};

/* 4. Loader */
canvasApp.loadingOverlay = condition => {
  if (condition) {
    $("body").append(`<div class="loading-overlay-container"><div class="loader"></div></div>`);
  } else {
    $("body")
      .find(".loading-overlay-container")
      .remove();
  }
};

/* 5. Add Notification List To DOM */
canvasApp.addNotificationList = () => {
  if ($("body").find(".side-notifications-list").length === 0) {
    $("body")
      .css("position", "relative")
      .append(`<ul class="side-notifications-list"></ul>`);
  }
};

/* 6. Alert Texts */
canvasApp.userAddedSuccess = username => {
  return swal({
    type: "success",
    title: "CANVAS user successfully added",
    text: `${username} is now linked to this CANVAS Hub.`
  });
};

canvasApp.userExistsAlready = username => {
  return swal({
    type: "info",
    title: "CANVAS user already linked",
    text: `${username} is already linked to this CANVAS Hub.`
  });
};

canvasApp.userInvalidCredentials = () => {
  return swal({
    type: "error",
    title: "Incorrect Login Information",
    text: "User credentials are incorrect. Please try again."
  });
};

canvasApp.userDeletedSuccess = username => {
  return swal({
    type: "success",
    title: "CANVAS user successfully removed",
    text: `${username} is now removed from this CANVAS Hub.`
  });
};

canvasApp.importantUpdate = version => {
  return swal({
    type: "info",
    title: `Important Update (Version ${version})`,
    html: `CANVAS Plugin - Version ${version} is available for download.
    <br /><br />This version of the plugin contains important changes that allow a more stable connection to CANVAS. Due to changes on the CANVAS servers to facilitate these improvements, this update is required for 'Send to CANVAS Hub' functionality.
    <br /><br />We apologize for the inconvenience.`,
    input: "checkbox",
    inputClass: "update-checkbox",
    inputPlaceholder: "Don't show me this again"
  });
};

/* ======================
  CANVAS VIEW MODEL FOR OCTOPRINT
  ======================= */

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
  self.brand = ko.computed(function() {
    return self.applyTheme() ? "CANVAS Hub" : "OctoPrint";
  });

  self.modifyAppearanceVM = () => {
    self.appearance.name.subscribe(function() {
      if (self.appearance.name() === "CANVAS Hub" || self.appearance.name() === "OctoPrint") {
        self.appearance.name("");
      }
    });

    self.appearance.brand = ko.pureComputed(function() {
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

    self.appearance.fullbrand = ko.pureComputed(function() {
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

    self.appearance.title = ko.pureComputed(function() {
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
    self.files.getSuccessClass = function(data) {
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
    canvasApp.removePopup();
    canvasApp.addNotificationList();
  };

  self.onEventFileAdded = payload => {
    if ($("body").find(`.progress-bar .file-download-name:contains("${payload.name}")`)) {
      canvasApp.updateFileReady(payload.name);
    }
  };

  self.onDataUpdaterReconnect = () => {
    canvasApp.removePopup();
    canvasApp.addNotificationList();
  };

  self.onEventConnected = () => {
    self.toggleTheme();
  };

  self.addUser = () => {
    canvasApp.loadingOverlay(true);
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
      canvasApp.toggleLogo(applyTheme);
    } else {
      self.applyTheme(false);
      $("html").removeClass("canvas-theme");
      canvasApp.toggleLogo(applyTheme);
    }

    // Event listener for when user changes the theme settings
    $(".theme-input").on("change", event => {
      applyTheme = self.settings.settings.plugins.canvas.applyTheme();

      if (applyTheme) {
        self.applyTheme(true);
        $("html").addClass("canvas-theme");
        canvasApp.toggleLogo(applyTheme);
      } else {
        self.applyTheme(false);
        $("html").removeClass("canvas-theme");
        canvasApp.toggleLogo(applyTheme);
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
      if (message.command === "DisplayRegisteredUsers") {
        self.users(message.data);
      } else if (message.command === "AWS") {
        self.handleAWSConnection(message);
      } else if (message.command === "UserConnectedToHUB") {
        $(".add-user input").val("");
        canvasApp.loadingOverlay(false);
        canvasApp.userAddedSuccess(message.data.username);
      } else if (message.command === "UserAlreadyExists") {
        $(".add-user input").val("");
        canvasApp.loadingOverlay(false);
        canvasApp.userExistsAlready(message.data.username);
      } else if (message.command === "invalidUserCredentials") {
        $(".add-user input").val("");
        canvasApp.loadingOverlay(false);
        canvasApp.userInvalidCredentials();
      } else if (message.command === "UserDeleted") {
        canvasApp.userDeletedSuccess(message.data);
      } else if (message.command === "CANVASDownload") {
        if (message.status === "starting") {
          canvasApp.displayNotification(message.data);
        } else if (message.status === "downloading") {
          canvasApp.updateDownloadProgress(message.data);
        } else if (message.status === "received") {
          canvasApp.updateFileReceived(message.data);
        }
      } else if (message.command === "importantUpdate") {
        $("body").on("click", ".update-checkbox input", event => {
          self.changeImportantUpdateSettings(event.target.checked);
        });
        canvasApp.importantUpdate(message.data);
      }
    }
  };
}

/* ======================
  RUN
  ======================= */

$(function() {
  OCTOPRINT_VIEWMODELS.push({
    // This is the constructor to call for instantiating the plugin
    construct: CanvasViewModel, // This is a list of dependencies to inject into the plugin. The order will correspond to the "parameters" arguments above
    dependencies: ["settingsViewModel", "appearanceViewModel", "filesViewModel"], // Finally, this is the list of selectors for all elements we want this view model to be bound to.
    elements: ["#tab_plugin_canvas"]
  });
});
