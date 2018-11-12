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
  // canvasApp.arrowToggle();

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
  data.data.forEach(user => {
    // if (user.token_valid) {
    $(".registered-accounts").append(`<li class="valid-token">${user.username}</li>`);
    // }
    // else {
    //   $(".registred-accounts").append(`<li class="invalid-token">${user.username}</li>`);
    // }
  });
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

/* 7. FIle LOADING */
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

// canvasApp.arrowToggle = () => {
//   $(".accordion-heading").append(`<div><i data-toggle="collapse" class="fa fa-angle-down"></i></div>`);
// };

/* ======================
  CANVAS VIEW MODEL FOR OCTOPRINT
  ======================= */

function CanvasViewModel(parameters) {
  // OBSERVABLE VALUES
  this.userEmail = ko.observable();
  this.password = ko.observable();

  this.onStartupComplete = () => {
    console.log("CanvasViewModel STARTUP COMPLETED");
    canvasApp.toggleTheme();
    canvasApp.filesLoaded();
  };

  this.onEventUpdatedFiles = () => {
    console.log("File Updated EVENT!");
    canvasApp.filesLoaded();
  };

  this.onDataUpdaterReconnect = () => {
    console.log("Server Reconnected");
    canvasApp.filesLoaded();
  };

  this.addUser = () => {
    let payload = { command: "addUser", email: this.userEmail(), password: this.password() };
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
          title: "Canvas user successfully connected",
          text: `${message.data.username} is now registered to this Canvas Hub.`,
          timer: 10000
        });
      } else if (message.command === "UserAlreadyExists") {
        swal({
          type: "info",
          // animation: false,
          title: "Canvas user already registered",
          text: `${message.data.username} is already registered to this Canvas Hub.`,
          timer: 10000
        });
      } else if (message.command === "invalidUserCredentials") {
        swal({
          type: "error",
          // animation: false,
          title: "Incorrect Login Information",
          text: "User credentials are incorrect. Please try again.",
          timer: 10000
        });
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
