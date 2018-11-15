if (!document.getElementById("material-icons")) {
  let link = document.createElement("link");
  link.id = "material-icons";
  link.href = "https://fonts.googleapis.com/icon?family=Material+Icons";
  link.rel = "stylesheet";
  document.head.appendChild(link);
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

    $("head title").text(name);
    $("head")
      .find('link[rel="shortcut icon"]')
      .attr("href", "/plugin/canvas/static/img/Mosaic_Icon_Square.png");
  } else {
    $(".brand")
      .find("span")
      .text(name);

    $("head title").text(name);
    $("head")
      .find('link[rel="shortcut icon"]')
      .attr("href", "/static/img/tentacle-20x20@2x.png");
  }
};

/* 2. Add Palette Tag to .mcf.gcode files */
canvasApp.tagPaletteFiles = () => {
  let allPrintFiles = $("#files .gcode_files .scroll-wrapper").find(".entry .title");
  allPrintFiles.each((index, printFile) => {
    if (printFile.innerHTML.includes(".mcf.gcode")) {
      $(printFile).addClass("palette-tag");
    }
  });
};

/* 2.1 Event listener for clicking back and forth between GCODE folders.
Use this function to keep Palette files tagged */
canvasApp.handleGCODEFolders = () => {
  canvasApp.removeFolderBinding();
  $("#files .gcode_files .entry.back.clickable").on("click", () => {
    canvasApp.filesLoaded();
  });
};

/* 2.2 Specific Fevent listener for clicking and seeing folder dynamic elements */
canvasApp.removeFolderBinding = () => {
  $("#files .gcode_files .scroll-wrapper")
    .find(".folder .title")
    .removeAttr("data-bind")
    .on("click", event => {
      canvasApp.tagPaletteFiles();
    });
};

/* 3. Toggle on/off the Canvas Theme */
canvasApp.toggleTheme = () => {
  $("html").addClass("canvas-theme");
  canvasApp.toggleBrandName("CANVAS Hub");

  $(".theme-input").on("change", event => {
    let checked = event.target.checked;

    if (checked) {
      $("html").addClass("canvas-theme");
      canvasApp.toggleBrandName("CANVAS Hub");
      $(".theme-input-label")
        .find("span")
        .text("Turn Off");
    } else {
      $("html").removeClass("canvas-theme");
      canvasApp.toggleBrandName("OctoPrint");
      $(".theme-input-label")
        .find("span")
        .text("Turn On");
    }
  });
};

/* 4. Display all connected Canvas Accounts */
canvasApp.handleUserDisplay = data => {
  $(".registered-accounts").html("");
  console.log(data.data.length);
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

/* 5. Display that Websockets are enabled between C.Hub and Canvas */
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

/* 6. Show Canvas Plugin Tab Content */
canvasApp.unhideCanvasTabContent = () => {
  $(".canvas-plugin").css("display", "block");
};

/* 7. FILE LOADING */
canvasApp.filesLoaded = () => {
  let checkExist = setInterval(function() {
    if ($("#files .gcode_files .scroll-wrapper").find(".entry .action-buttons .toggleAdditionalData").length) {
      canvasApp.tagPaletteFiles();
      let dynamicFilesFullyLoaded = true;
      let allFiles = $("#files .gcode_files .scroll-wrapper").find(".entry .action-buttons .toggleAdditionalData");
      allFiles.each((i, file) => {
        // if any of the files have a class of disabled on them,
        // it means that all the files have not finished dynamically being added to the DOM
        if (file.classList.value.includes("disabled")) {
          dynamicFilesFullyLoaded = false;
        }
      });
      if (dynamicFilesFullyLoaded) {
        canvasApp.removeFolderBinding();
        canvasApp.tagPaletteFiles();
        canvasApp.handleGCODEFolders();
        clearInterval(checkExist);
      }
    }
  }, 100);
};

/* 8. DISPLAY POPUP WHEN FILES RECEIVED FROM CANVAS */
canvasApp.displayNotification = data => {
  if (data.status === "incoming") {
    let notification = $(`<li id="file-incoming${this.incomingCounter}" class="popup-notification">
            <i class="material-icons remove-popup">clear</i>
            <h6>Canvas File Incoming...</h6>
            <p>${data.filename}</p>
            </li>`).hide();
    $(".side-notifications-list").append(notification);
    notification.fadeIn(200);
    let currentId = `#file-incoming${this.incomingCounter}`;
    this.incomingCounter++;
    setTimeout(function() {
      $(currentId).fadeOut(500, function() {
        this.remove();
      });
    }, 10000);
  } else if (data.status === "received") {
    $(`#file-incoming${this.receivedCounter}`).fadeOut(1000, function() {
      this.remove();
    });
    let notification = $(`<li id="file-added${this.receivedCounter}" class="popup-notification">
            <i class="material-icons remove-popup">clear</i>
            <h6>File Received From CANVAS</h6>
            <p>${data.filename}</p>
            </li>`).hide();
    $(".side-notifications-list").append(notification);
    notification.fadeIn(200);
    let currentId = `#file-added${this.receivedCounter}`;
    this.receivedCounter++;
    setTimeout(function() {
      $(currentId).fadeOut(500, function() {
        this.remove();
      });
    }, 5000);
  }
};

/* 9. REMOVE POPUP WHEN RECEIVING FILES FROM CANVAS */
canvasApp.removePopup = () => {
  $("body").on("click", ".side-notifications-list .remove-popup", function() {
    $(this)
      .closest("li")
      .fadeOut(200, function() {
        $(this).remove();
      });
  });
};

/* 10. APPLY ADDITIONAL TAGGING FOR UPDATED FILES BECAUSE
DYNAMIC ELEMENTS WERE NOT DONE ON EVENT LISTENING */
canvasApp.applyExtraTagging = () => {
  let count = 0;
  let applyTagging = setInterval(function() {
    if (count > 150) {
      clearInterval(applyTagging);
    }
    canvasApp.tagPaletteFiles();
    count++;
  }, 100);
};

/* 11. Remove Canvas user event listener */
canvasApp.removeUser = () => {
  $(".registered-accounts").on("click", ".remove-user", event => {
    user = event.target.previousElementSibling.innerText;
    this.removeUser(user);
  });
};

/* 12. Toggle edit users */
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

/* ======================
  CANVAS VIEW MODEL FOR OCTOPRINT
  ======================= */

function CanvasViewModel(parameters) {
  // OBSERVABLE VALUES
  this.userInput = ko.observable();
  this.password = ko.observable();
  this.users = ko.observableArray();
  this.incomingCounter = 0;
  this.receivedCounter = 0;

  this.onStartupComplete = () => {
    console.log("CanvasViewModel STARTUP COMPLETED");
    canvasApp.toggleTheme();
    canvasApp.filesLoaded();
    canvasApp.removePopup();
    $("body")
      .css("position", "relative")
      .append(`<ul class="side-notifications-list"></ul>`);
    canvasApp.removeUser();
    canvasApp.toggleEditUser();
  };

  this.onEventFileAdded = payload => {
    canvasApp.applyExtraTagging();
    if (this.canvasFileReceived) {
      this.canvasFilename = payload.name;
    }
  };

  this.onEventMetadataAnalysisFinished = () => {
    canvasApp.applyExtraTagging();
  };

  this.onEventUpdatedFiles = () => {
    canvasApp.applyExtraTagging();
    canvasApp.filesLoaded();
    if (this.canvasFileReceived) {
      canvasApp.tagPaletteFiles();
      this.onDataUpdaterPluginMessage("canvas", {
        command: "CanvasFileAnalysisDone",
        data: { filename: this.canvasFilename, status: "received" }
      });
      this.canvasFileReceived = false;
      this.canvasFilename = null;
    }
  };

  this.onDataUpdaterReconnect = () => {
    console.log("Server Reconnected");
    canvasApp.filesLoaded();
    canvasApp.removePopup();
    if (!$("body").find(".side-notifications-list")) {
      $("body")
        .css("position", "relative")
        .append(`<ul class="side-notifications-list"></ul>`);
    }
    canvasApp.toggleEditUser();
  };

  this.addUser = () => {
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
    });
  };

  this.removeUser = username => {
    let payload = { command: "removeUser", data: username };

    $.ajax({
      url: API_BASEURL + "plugin/canvas",
      type: "POST",
      dataType: "json",
      data: JSON.stringify(payload),
      contentType: "application/json; charset=UTF-8"
    }).then(res => {
      console.log("USER BEING REMOVED");
    });
  };

  // Receive messages from the OctoPrint server
  this.onDataUpdaterPluginMessage = (pluginIdent, message) => {
    if (pluginIdent === "canvas") {
      console.log(message);
      if (message.command === "DisplayRegisteredUsers") {
        canvasApp.handleUserDisplay(message);
      } else if (message.command === "Websocket") {
        canvasApp.handleWebsocketConnection(message);
      } else if (message.command === "HubRegistered") {
        canvasApp.unhideCanvasTabContent();
      } else if (message.command === "UserConnectedToHUB") {
        swal({
          type: "success",
          // animation: false,
          title: "CANVAS user successfully connected",
          text: `${message.data.username} is now registered to this Canvas Hub.`
        });
      } else if (message.command === "UserAlreadyExists") {
        swal({
          type: "info",
          // animation: false,
          title: "CANVAS user already registered",
          text: `${message.data.username} is already registered to this Canvas Hub.`
        });
      } else if (message.command === "invalidUserCredentials") {
        swal({
          type: "error",
          // animation: false,
          title: "Incorrect Login Information",
          text: "User credentials are incorrect. Please try again."
        });
      } else if (message.command === "CanvasDownloadStart") {
        canvasApp.displayNotification(message.data);
      } else if (message.command === "FileReceivedFromCanvas") {
        this.canvasFileReceived = true;
      } else if (message.command === "CanvasFileAnalysisDone") {
        canvasApp.displayNotification(message.data);
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
    // dependencies: ["filesViewModel"],
    // Finally, this is the list of selectors for all elements we want this view model to be bound to.
    elements: ["#tab_plugin_canvas"]
  });
});
