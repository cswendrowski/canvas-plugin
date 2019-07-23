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

const Alerts = {
  userAddedSuccess: username => {
    return swal({
      type: "success",
      title: "CANVAS user successfully added",
      text: `${username} is now linked to this CANVAS Hub.`
    });
  },
  userExistsAlready: username => {
    return swal({
      type: "info",
      title: "CANVAS user already linked",
      text: `${username} is already linked to this CANVAS Hub.`
    });
  },
  userInvalidCredentials: () => {
    return swal({
      type: "error",
      title: "Incorrect Login Information",
      text: "User credentials are incorrect. Please try again."
    });
  },
  userDeletedSuccess: username => {
    return swal({
      type: "success",
      title: "CANVAS user successfully removed",
      text: `${username} is now removed from this CANVAS Hub.`
    });
  },
  hubNotRegistered: () => {
    return swal({
      type: "info",
      title: "CANVAS Hub not registered yet",
      text: `There seems to be an issue registering your CANVAS Hub. Please make sure you are connected to the Internet and try again.`
    });
  },
  importantUpdate: version => {
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
  },
};