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