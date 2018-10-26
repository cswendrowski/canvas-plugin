const canvasApp = {};

/* ======================
  FUNCTIONALITIES
  ======================= */

/* 1. Replaces Octoprint Name with Canvas Hub */
canvasApp.replaceBrandName = () => {
  // MUST FIND BETTER WAY TO REPLACE
  $(".brand")
    .find("span")
    .removeAttr("data-bind");
  $(".brand")
    .find("span")
    .text("CANVAS Hub");
};

/* 2. Display Color for Connection Status */
canvasApp.displayConnectionColor = () => {
  let palette2Connection = { id: "#connection-state-msg" };
  let canvasConnection = { id: "#connection-state-msg-canvas" };
  let connections = [palette2Connection, canvasConnection];

  palette2Connection.status = $(palette2Connection.id).text();
  canvasConnection.status = $(canvasConnection.id).text();

  connections.forEach(connection => {
    if (connection.status === "Connected") {
      $(connection.id).css("color", "green");
    } else {
      $(connection.id).css("color", "red");
    }
  });
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

/* ======================
  INIT + RUN
  ======================= */
canvasApp.init = () => {
  canvasApp.replaceBrandName();
  canvasApp.displayConnectionColor();
  canvasApp.tagPaletteFiles();
};

$(function() {
  canvasApp.init();
  function CanvasViewModel(parameters) {
    var self = this;

    self.connectCanvas = function() {
      console.log("Connect Canvas");
      var payload = { command: "connectCanvas", test: "hello" };

      $.ajax({
        url: API_BASEURL + "plugin/canvas",
        type: "POST",
        dataType: "json",
        data: JSON.stringify(payload),
        contentType: "application/json; charset=UTF-8",
        success: self.fromResponse
      });
    };

    self.fromResponse = function() {
      console.log("SUCCESS");
    };

    self.onAfterBinding = function() {
      console.log("From Canvas2.js: HELLO");

      // var payload = { command: "uiUpdate" };

      // $.ajax({
      //   url: API_BASEURL + "plugin/palette2",
      //   type: "POST",
      //   dataType: "json",
      //   data: JSON.stringify(payload),
      //   contentType: "application/json; charset=UTF-8",
      //   success: self.fromResponse
      // });
    };

    // you just need this, to check if we are responding to the plugin identifier that was sent by us.
    self.onDataUpdaterPluginMessage = function(pluginIdent, message) {
      if (pluginIdent === "canvas") {
        console.log("succesfully got into onDataUpdaterPluginMessage");
      }
    };
  }
  OCTOPRINT_VIEWMODELS.push([
    // This is the constructor to call for instantiating the plugin
    CanvasViewModel, // here is the order in which the dependencies will be injected into your view model upon // This is a list of dependencies to inject into the plugin, the order which you request
    // instantiation via the parameters argument
    ["settingsViewModel"],
    ["#tab_plugin_canvas"]
  ]); // Finally, this is the list of selectors for all elements we want this view model to be bound to.
});
