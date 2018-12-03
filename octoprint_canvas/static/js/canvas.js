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

/* 1. Replaces Octoprint Name with Canvas Hub */
canvasApp.toggleBrandName = name => {
  if (name === "CANVAS Hub") {
    $(".brand")
      .find("span")
      .removeAttr("data-bind");
    $(".brand")
      .find("span")
      .text(name);

    $("head title")
      .removeAttr("data-bind")
      .text(name);
    $("head")
      .find('link[rel="shortcut icon"]')
      .attr("href", "/plugin/canvas/static/img/Mosaic_Icon_Square.png");
  } else {
    $(".brand")
      .find("span")
      .text(name);

    $("head title")
      .removeAttr("data-bind")
      .text(name);
    $("head")
      .find('link[rel="shortcut icon"]')
      .attr("href", "/static/img/tentacle-20x20@2x.png");
  }
};

/* 2. Add Palette Tag to .mcf.gcode files */
canvasApp.tagPaletteFiles = () => {
  canvasApp.removeFolderBinding();
  canvasApp.handleGCODEFolders();
  canvasApp.applyExtraTagging();
};

/* 2.1 Event listener for clicking back and forth between GCODE folders.
Use this function to keep Palette files tagged */
canvasApp.handleGCODEFolders = () => {
  canvasApp.removeFolderBinding();
  $("#files .gcode_files .entry.back.clickable").on("click", () => {
    canvasApp.applyExtraTagging();
  });
};

/* 2.2 Specific Fevent listener for clicking and seeing folder dynamic elements */
canvasApp.removeFolderBinding = () => {
  $("#files .gcode_files .scroll-wrapper")
    .find(".folder .title")
    .removeAttr("data-bind")
    .on("click", event => {
      canvasApp.applyExtraTagging();
    });
};

/* 3. Toggle on/off the Canvas Theme */
canvasApp.toggleTheme = condition => {
  // FE event listener
  $(".theme-input").on("change", event => {
    let checked = event.target.checked;

    if (checked) {
      $("html").addClass("canvas-theme");
      canvasApp.toggleBrandName("CANVAS Hub");
    } else {
      $("html").removeClass("canvas-theme");
      canvasApp.toggleBrandName("OctoPrint");
    }
  });

  // When receiving initial settings from BE
  if (condition) {
    $("html").addClass("canvas-theme");
    canvasApp.toggleBrandName("CANVAS Hub");
  }
};

/* 4. Display all connected Canvas Accounts */
canvasApp.handleUserDisplay = data => {
  $(".registered-accounts").html("");
  if (data.data.length > 0) {
    data.data.forEach(user => {
      $(".registered-accounts").append(`<li class="registered-canvas-user">
        <i class="material-icons md-18">person</i>
        <span class="username">${user.username}</span>
        <i class="hide material-icons remove-user">remove</i>
        </li>`);
    });
    $(".toggle-remove-users").css("display", "flex");
    if ($(".toggle-remove-users span").text() === "Stop Editing") {
      $(".remove-user").toggleClass("hide");
    }
  } else {
    $(".toggle-remove-users").css("display", "none");
    $(".toggle-remove-users span").text("Edit");
    $(".toggle-remove-users i").text("edit");
  }
};

/* 5. Display that Websockets are enabled between Hub and Canvas */
canvasApp.handleWebsocketConnection = data => {
  if (data.data === true) {
    $("#connection-state-msg-canvas")
      .html("Connected")
      .css("color", "green");
  } else {
    $("#connection-state-msg-canvas")
      .html("Not Connected")
      .css("color", "red");
  }
};

/* 6. Display popup notifications for files incoming and received from Canvas */
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
  let currentId = `#${data.projectId}`;
  setTimeout(function() {
    $(currentId).fadeOut(500, function() {
      this.remove();
    });
  }, 300000);
};

/* 6.1 Update the download progress (%) on UI */
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

/* 6.2 Update download progress when file is received and extracted */
canvasApp.updateFileReceived = data => {
  $("body")
    .find(`#${data.projectId} .popup-title`)
    .text("File Received. Analyzing File...")
    .hide()
    .fadeIn(200);
  $("body")
    .find(`#${data.projectId} .small-loader`)
    .css("visibility", "visible")
    .hide()
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

/* 6.3 Update download progress when file analysis is done */
canvasApp.updateFileReady = filename => {
  $("body")
    .find(`.progress-bar .file-download-name:contains("${filename}")`)
    .siblings(".popup-heading")
    .children(".popup-title")
    .text("CANVAS File Ready")
    .hide()
    .fadeIn(200);
  $("body")
    .find(`.progress-bar .file-download-name:contains("${filename}")`)
    .siblings(".popup-heading")
    .children(".small-loader")
    .fadeOut(200, function() {
      $(this).css("visibility", "hidden");
    });
  setTimeout(function() {
    $("body")
      .find(`.progress-bar .file-download-name:contains("${filename}")`)
      .closest("li")
      .addClass("highlight-glow-received");
  }, 400);
};

/* 7. Remove popup notifications */
canvasApp.removePopup = () => {
  $("body").on("click", ".side-notifications-list .remove-popup", function() {
    $(this)
      .closest("li")
      .fadeOut(200, function() {
        $(this).remove();
      });
  });
};

/* 8. Apply additional tagging function for slower DOM-binding scenarios*/
canvasApp.applyExtraTagging = () => {
  let count = 0;
  let applyTagging = setInterval(function() {
    if (count > 20) {
      clearInterval(applyTagging);
    }
    let allPrintFiles = $("#files .gcode_files .scroll-wrapper").find(".entry .title");
    allPrintFiles.each((index, printFile) => {
      if (printFile.innerHTML.includes(".mcf.gcode")) {
        $(printFile).addClass("palette-tag");
      }
    });
    count++;
  }, 100);
};

/* 9. Remove Canvas user event listener */
canvasApp.removeUser = () => {
  $(".registered-accounts").on("click", ".remove-user", event => {
    user = event.target.previousElementSibling.innerText;
    this.removeUser(user);
  });
};

/* 10. Toggle edit users */
canvasApp.toggleEditUser = () => {
  $(".toggle-remove-users span").on("click", () => {
    $(".remove-user").toggleClass("hide");
    if ($(".toggle-remove-users span").text() === "Edit") {
      $(".toggle-remove-users span").text("Stop Editing");
      $(".toggle-remove-users i")
        .text("clear")
        .css("font-size", "15px");
    } else {
      $(".toggle-remove-users span").text("Edit");
      $(".toggle-remove-users i").text("edit");
    }
  });
};

/* 11. Loader */
canvasApp.loadingOverlay = condition => {
  if (condition) {
    $("body").append(`<div class="loading-overlay-container"><div class="loader"></div></div>`);
  } else {
    $("body")
      .find(".loading-overlay-container")
      .remove();
  }
};

/* 12. Add Notification List To DOM */
canvasApp.addNotificationList = () => {
  if ($("body").find(".side-notifications-list").length === 0) {
    $("body")
      .css("position", "relative")
      .append(`<ul class="side-notifications-list"></ul>`);
  }
};

/* 13. Alert Texts */

canvasApp.userAddedSuccess = username => {
  return swal({
    type: "success",
    title: "CANVAS user successfully connected",
    text: `${username} is now registered to this CANVAS Hub.`
  });
};

canvasApp.userExistsAlready = username => {
  return swal({
    type: "info",
    title: "CANVAS user already registered",
    text: `${username} is already registered to this CANVAS Hub.`
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

/* 14. Smaller loader */
canvasApp.smallLoader = () => {
  return;
};

/* ======================
  CANVAS VIEW MODEL FOR OCTOPRINT
  ======================= */

function CanvasViewModel(parameters) {
  this.userInput = ko.observable();
  this.password = ko.observable();

  this.onStartupComplete = () => {
    canvasApp.toggleTheme();
    canvasApp.tagPaletteFiles();
    canvasApp.removePopup();
    canvasApp.addNotificationList();
    canvasApp.removeUser();
    canvasApp.toggleEditUser();
  };

  this.onEventFileAdded = () => {
    canvasApp.tagPaletteFiles();
  };

  this.onEventFileRemoved = () => {
    canvasApp.tagPaletteFiles();
  };

  this.onEventMetadataAnalysisFinished = payload => {
    canvasApp.tagPaletteFiles();
    canvasApp.updateFileReady(payload.name);
  };

  this.onEventUpdatedFiles = () => {
    canvasApp.tagPaletteFiles();
  };

  this.onEventFileSelected = () => {
    canvasApp.tagPaletteFiles();
  };

  this.onEventFileDeselected = () => {
    canvasApp.tagPaletteFiles();
  };

  this.onDataUpdaterReconnect = () => {
    canvasApp.tagPaletteFiles();
    canvasApp.removePopup();
    canvasApp.addNotificationList();
    canvasApp.toggleEditUser();
  };

  this.addUser = () => {
    canvasApp.loadingOverlay(true);
    let payload = { command: "addUser", data: { username: this.userInput(), password: this.password() } };

    if (this.userInput().includes("@")) {
      payload = { command: "addUser", data: { email: this.userInput(), password: this.password() } };
    }

    $.ajax({
      url: API_BASEURL + "plugin/canvas",
      type: "POST",
      dataType: "json",
      data: JSON.stringify(payload),
      contentType: "application/json; charset=UTF-8"
    }).then(res => {
      $(".add-user input").val("");
      canvasApp.loadingOverlay(false);
    });
  };

  this.removeUser = username => {
    canvasApp.loadingOverlay(true);
    let payload = { command: "removeUser", data: username };

    $.ajax({
      url: API_BASEURL + "plugin/canvas",
      type: "POST",
      dataType: "json",
      data: JSON.stringify(payload),
      contentType: "application/json; charset=UTF-8"
    }).then(res => {
      canvasApp.loadingOverlay(false);
    });
  };

  // Receive messages from the OctoPrint server
  this.onDataUpdaterPluginMessage = (pluginIdent, message) => {
    if (pluginIdent === "canvas") {
      if (message.command === "DisplayRegisteredUsers") {
        canvasApp.handleUserDisplay(message);
      } else if (message.command === "Websocket") {
        canvasApp.handleWebsocketConnection(message);
      } else if (message.command === "UserConnectedToHUB") {
        canvasApp.userAddedSuccess(message.data.username);
      } else if (message.command === "UserAlreadyExists") {
        canvasApp.userExistsAlready(message.data.username);
      } else if (message.command === "invalidUserCredentials") {
        canvasApp.userInvalidCredentials();
      } else if (message.command === "UserDeleted") {
        canvasApp.userDeletedSuccess(message.data);
      } else if (message.command === "toggleTheme") {
        if (message.data) {
          $(".theme-input").attr("checked", true);
          canvasApp.toggleTheme(true);
        } else {
          $(".theme-input").attr("checked", false);
        }
      } else if (message.command === "CANVASDownload") {
        if (message.status === "starting") {
          canvasApp.displayNotification(message.data);
        } else if (message.status === "downloading") {
          canvasApp.updateDownloadProgress(message.data);
        } else if (message.status === "received") {
          canvasApp.updateFileReceived(message.data);
        }
      }
    }
  };
}

/* ======================
  RUN
  ======================= */

$(function() {
  CanvasViewModel();
  OCTOPRINT_VIEWMODELS.push({
    // This is the constructor to call for instantiating the plugin
    construct: CanvasViewModel,
    // This is a list of dependencies to inject into the plugin. The order will correspond to the "parameters" arguments above
    dependencies: ["settingsViewModel"],
    // Finally, this is the list of selectors for all elements we want this view model to be bound to.
    elements: ["#tab_plugin_canvas"]
  });
});
