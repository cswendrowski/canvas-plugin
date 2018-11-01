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

canvasApp.toggleTheme = () => {
  // $("html").eq(0).addClass("Cyborg")
  // if ($("#touch body").length == 1) {
  //   $("html").removeClass("Cyborg");
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

    // OBSERVABLE VALUES
    self.userEmail = ko.observable();
    self.password = ko.observable();

    self.downloadPrint = function() {
      console.log("ATTEMPTING DOWNLOAD");
      var payload = {
        Authorization:
          "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1NDEwMTI4MTAsImV4cCI6MTU0MTYxNzYxMCwiaXNzIjoiQ2FudmFzIiwic3ViIjoiODM3OGViOTViYmU0OTk1NjBkOGE2NmI4ZDUwYjg4N2EifQ.nIeuSLWN_g3khHcL4zxigMp5Ke5LPOHM5zOhBur4oPY"
      };

      $.ajax({
        url: "https://slice.api.canvas3d.io/projects/ab6225f37b511d671bd27756af3cb299/download",
        type: "GET",
        dataType: "json",
        data: JSON.stringify(payload),
        contentType: "application/json; charset=UTF-8",
        success: self.fromResponse
      }).then(res => {
        console.log("Successful download");
      });
    };

    self.connectCanvas = function() {
      var payload = {
        command: "connectCanvas",
        email: self.userEmail(),
        password: self.password()
      };

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
    };

    // you just need this, to check if we are responding to the plugin identifier that was sent by us.
    self.onDataUpdaterPluginMessage = function(pluginIdent, message) {
      if (pluginIdent === "canvas") {
        console.log("succesfully got into onDataUpdaterPluginMessage");
        console.log(message);
        if (message.command === "DisplayRegisteredUsers") {
          $(".accounts").html("");
          message.data.forEach(user => {
            $(".accounts").append(`<li>${user}</li>`);
          });
        }
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
