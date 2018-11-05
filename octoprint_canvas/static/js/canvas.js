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
  } else {
    $(".brand")
      .find("span")
      .text(name);
  }
};

/* 2. Display color for Palette 2 Connection Status */
canvasApp.displayConnectionColor = () => {
  let palette2ConnectionId = "#connection-state-msg";
  let palette2ConnectionText = $(palette2ConnectionId).text();

  if (palette2ConnectionText === "Connected") {
    $(palette2ConnectionId).css("color", "green");
  } else {
    $(palette2ConnectionId).css("color", "red");
  }
};

/* 3. Add Palette Tag to .mcf.gcode files */
canvasApp.tagPaletteFiles = () => {
  let allPrintFiles = $("#files .gcode_files .scroll-wrapper .entry").find(".title");
  allPrintFiles.each((index, printFile) => {
    if (printFile.innerHTML.includes(".mcf.gcode")) {
      $(printFile).addClass("palette-tag");
    }
  });
};

/* 3.1 Event listener for clicking back and forth between GCODE folders.
Use this function to keep Palette files tagged */
canvasApp.handleGCODEFolders = () => {
  canvasApp.removeFolderBinding();

  $("#files .gcode_files .entry.back.clickable").on("click", () => {
    canvasApp.tagPaletteFiles();
    canvasApp.removeFolderBinding();
  });
};

/* 3.2 Specific Fevent listener for clicking and seeing folder dynamic elements */
canvasApp.removeFolderBinding = () => {
  $("#files .gcode_files .scroll-wrapper")
    .find(".folder .title")
    .removeAttr("data-bind")
    .on("click", event => {
      canvasApp.tagPaletteFiles();
    });
};

/* 4. Toggle on/off the Canvas Theme */
canvasApp.toggleTheme = () => {
  $("html").addClass("canvas-theme");
  canvasApp.toggleBrandName("CANVAS Hub");

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
};

/* 5. Display all connected Canvas Accounts */
canvasApp.handleUserDisplay = data => {
  $(".registered-accounts").html("");
  data.data.forEach(user => {
    if (user.token_valid) {
      $(".registered-accounts").append(`<li class="valid-token">${user.username}</li>`);
    } else {
      $(".registred-accounts").append(`<li class="invalid-token">${user.username}</li>`);
    }
  });
};

/* 6. Display that Websockets are enabled between C.Hub and Canvas */
canvasApp.handleWebsocketConnection = data => {
  if (data.data === true) {
    $("#connection-state-msg-canvas")
      .html("Connected")
      .css("color", "green");
  }
};

/* CanvasViewModel for OctoPrint */
function CanvasViewModel(parameters) {
  // OBSERVABLE VALUES
  this.userEmail = ko.observable();
  this.password = ko.observable();

  this.onAllBound = function() {
    console.log("All ViewModels bounded");
    this.FilesViewModel = parameters[0];

    // When client finishes starting (i.e hard refresh or first time going to OctoPrint UI)
    this.FilesViewModel.onStartupComplete = () => {
      canvasApp.tagPaletteFiles();
    };

    // If files are changed (i.e added or deleted)
    this.FilesViewModel.onEventUpdatedFiles = () => {
      console.log("File Updated EVENT!");
      setTimeout(function() {
        canvasApp.removeFolderBinding();
        canvasApp.tagPaletteFiles();
      }, 600);
    };

    // If client is still open, and server reconnects
    this.FilesViewModel.onDataUpdaterReconnect = () => {
      console.log("server Reconnected");
      setTimeout(function() {
        canvasApp.tagPaletteFiles();
      }, 600);
    };
  };

  this.onStartupComplete = () => {
    console.log("CanvasViewModel STARTUP COMPLETED");
    canvasApp.displayConnectionColor();
    canvasApp.toggleTheme();
    canvasApp.handleGCODEFolders();
  };

  this.connectCanvas = function() {
    let payload = { email: this.userEmail(), password: this.password() };
    $.ajax({
      url: "https://api.canvas3d.io/users/login",
      type: "POST",
      dataType: "json",
      data: JSON.stringify(payload),
      // "Cache-control": "no-cache",
      // "Access-Control-Allow-Headers": "Content-Type",
      // "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE",
      // "Access-Control-Allow-Origin": "*",
      contentType: "application/json; charset=UTF-8",
      success: "Succes!"
    }).then(res => {
      console.log(res);
      $(".connect-canvas input").val("");

      // let payloadToBE = { command: "connectCanvas", data: res };
      // $.ajax({
      //   url: API_BASEURL + "plugin/canvas",
      //   type: "POST",
      //   dataType: "json",
      //   data: JSON.stringify(payload),
      //   contentType: "application/json; charset=UTF-8",
      //   success: this.fromResponse
      // }).then(res => {});
    });

    // PREVIOUS BE METHOD. USE FE METHOD INSTEAD

    // var payload = { command: "connectCanvas", email: this.userEmail(), password: this.password() };
    // $.ajax({
    //   url: API_BASEURL + "plugin/canvas",
    //   type: "POST",
    //   dataType: "json",
    //   data: JSON.stringify(payload),
    //   contentType: "application/json; charset=UTF-8",
    //   success: this.fromResponse
    // });
  };

  this.fromResponse = function() {
    console.log("SUCCESS");
  };

  // Receive messages from the OctoPrint server
  this.onDataUpdaterPluginMessage = function(pluginIdent, message) {
    if (pluginIdent === "canvas") {
      console.log("succesfully got into onDataUpdaterPluginMessage");
      console.log(message);
      if (message.command === "DisplayRegisteredUsers") {
        canvasApp.handleUserDisplay(message);
      } else if (message.command === "Websocket") {
        canvasApp.handleWebsocketConnection(message);
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
    // This is a list of dependencies to inject into the plugin. The order will correspond to the "parameters" arguments
    dependencies: ["filesViewModel"],
    // Finally, this is the list of selectors for all elements we want this view model to be bound to.
    elements: ["#tab_plugin_canvas"]
  });
});
