/* ======================
  NAMESPACE
  ======================= */
const canvasApp = {};

/* ======================
  FUNCTIONALITIES
  ======================= */

/* 1. Replaces Octoprint Logo with Canvas Hub */
canvasApp.replaceBrandName = () => {
  $(".brand")
    .find("span")
    .removeAttr("data-bind");
  $(".brand")
    .find("span")
    .text("CANVAS Hub");
};

/* 2. Display Color for Connection Status */
canvasApp.displayConnectionColor = () => {
  let connectionStatus = $("#connection-state-msg").text();

  if (connectionStatus === "Connected") {
    $("#connection-state-msg").css("color", "green");
  } else {
    $("#connection-state-msg").css("color", "red");
  }
};

/* 3. Add Palette Tag to .mcf.gcode files */
canvasApp.tagPaletteFiles = () => {
  console.log("hello");
  // $("#files .gcode_files .scroll-wrapper .entry")
  //   .find(".title")
  //   .addClass("tag");
  // $("#files .gcode_files .scroll-wrapper .entry")
  //   .find(".clickable")
  //   .addClass("tag");
  // $("#files .gcode_files .scroll-wrapper .entry")
  //   .find(".title.clickable")
  //   .addClass("tag");

  let x = $("#files .gcode_files .scroll-wrapper .entry").addClass("palette-tag");

  console.log(x);

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
});
