const canvasApp = {};

/* ======================
  FUNCTIONALITIES
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

/* 2. Display Color for Connection Status */
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
  // console.log("hello");
  // let x = $("#files .gcode_files .scroll-wrapper .entry").addClass("palette-tag");
  // console.log(x);
  // for (let i = 0; i < x.length; i++) {
  //   console.log(x[i].innerHTML);
  // }
};

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
      canvasApp.tagPaletteFiles();
      canvasApp.toggleBrandName("OctoPrint");
    }
  });
};

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

canvasApp.handleWebsocketConnection = data => {
  if (data.data === true) {
    $("#connection-state-msg-canvas")
      .html("Connected")
      .css("color", "green");
  }
};

function CanvasViewModel(parameters) {
  // var self = this;

  // OBSERVABLE VALUES
  this.userEmail = ko.observable();
  this.password = ko.observable();

  this.connectCanvas = function() {
    // let payload = {
    //   email: this.userEmail(),
    //   password: this.password()
    // };
    // $.ajax({
    //   url: "https://api.canvas3d.io/users/login",
    //   type: "POST",
    //   dataType: "json",
    //   data: JSON.stringify(payload),
    //   // "Cache-control": "no-cache",
    //   // "Access-Control-Allow-Headers": "Content-Type",
    //   // "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE",
    //   // "Access-Control-Allow-Origin": "*",
    //   contentType: "application/json; charset=UTF-8",
    //   success: "Succes!"
    // }).then(res => {
    //   console.log(res);
    // });
    var payload = { command: "connectCanvas", email: this.userEmail(), password: this.password() };

    $.ajax({
      url: API_BASEURL + "plugin/canvas",
      type: "POST",
      dataType: "json",
      data: JSON.stringify(payload),
      contentType: "application/json; charset=UTF-8",
      success: this.fromResponse
    });
  };

  this.fromResponse = function() {
    console.log("SUCCESS");
  };

  this.onAfterBinding = function() {
    console.log("From Canvas2.js: HELLO");
  };

  // you just need this, to check if we are responding to the plugin identifier that was sent by us.
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
  INIT + RUN
  ======================= */
canvasApp.init = () => {
  canvasApp.toggleTheme();
  canvasApp.displayConnectionColor();
};

$(function() {
  canvasApp.init();
  CanvasViewModel();
  OCTOPRINT_VIEWMODELS.push([
    // This is the constructor to call for instantiating the plugin
    CanvasViewModel, // here is the order in which the dependencies will be injected into your view model upon // This is a list of dependencies to inject into the plugin, the order which you request
    // instantiation via the parameters argument
    ["settingsViewModel"],
    ["#tab_plugin_canvas"]
  ]); // Finally, this is the list of selectors for all elements we want this view model to be bound to.
});
