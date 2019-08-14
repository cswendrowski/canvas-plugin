if (!document.getElementById("material-icons")) {
  let link = document.createElement("link");
  link.id = "material-icons";
  link.href = "https://fonts.googleapis.com/icon?family=Material+Icons";
  link.rel = "stylesheet";
  document.head.appendChild(link);
}

const CanvasUI = {
  /* 1. Replaces Octoprint Logo with Mosaic */
  toggleLogo: condition => {
    if (condition) {
      $("head")
        .find('link[rel="shortcut icon"]')
        .attr("href", "/plugin/canvas/static/img/Mosaic_Icon_Square.png");
    } else {
      $("head")
        .find('link[rel="shortcut icon"]')
        .attr("href", "/static/img/tentacle-20x20@2x.png");
    }
  },
  /* 2. Display popup notifications for files incoming and received from Canvas */
  displayNotification: data => {
    // if a prior popup with the same file is currently on the page, remove it
    if ($("body").find(`#${data.projectId}`).length > 0) {
      $("body")
        .find(`#${data.projectId}`)
        .fadeOut(1000, function () {
          this.remove();
        });
    }
    let notification = $(`<li id="${data.projectId}" class="canvas-progress-bar popup-notification">
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
  },
  /* 2.1 Update the download progress (%) on UI */
  updateDownloadProgress: data => {
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
  },
  /* 2.2 Update download progress when file is received and extracted */
  updateFileReceived: data => {
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
  },
  /* 2.3 Update download progress when file analysis is done */
  updateFileReady: filename => {
    $("body")
      .find(`.canvas-progress-bar .file-download-name:contains("${filename}")`)
      .siblings(".popup-heading")
      .children(".popup-title")
      .text("CANVAS File Added")
      .hide()
      .fadeIn(200);
    $("body")
      .find(`.canvas-progress-bar .file-download-name:contains("${filename}")`)
      .siblings(".popup-heading")
      .children(".small-loader")
      .remove();
    setTimeout(function () {
      $("body")
        .find(`.canvas-progress-bar .file-download-name:contains("${filename}")`)
        .closest("li")
        .addClass("highlight-glow-received");
    }, 400);
  },
  /* 3. Remove popup notifications */
  removePopup: () => {
    $("body").on("click", ".side-notifications-list .remove-popup", function () {
      $(this)
        .closest("li")
        .fadeOut(200, function () {
          $(this).remove();
        });
    });
  },
  /* 4. Loader */
  loadingOverlay: condition => {
    if (condition) {
      $("body").append(`<div class="loading-overlay-container"><div class="loader"></div></div>`);
    } else {
      $("body")
        .find(".loading-overlay-container")
        .remove();
    }
  },
  /* 5. Add Notification List To DOM */
  addNotificationList: () => {
    if ($("body").find(".side-notifications-list").length === 0) {
      $("body")
        .css("position", "relative")
        .append(`<ul class="side-notifications-list"></ul>`);
    }
  },
};