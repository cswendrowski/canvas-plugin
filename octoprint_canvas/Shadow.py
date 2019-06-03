from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
import os
import json


class Shadow():
    def __init__(self, canvas):
        self._logger = canvas._logger
        self.canvas = canvas

        hub_id = self.canvas.hub_yaml["canvas-hub"]["id"]
        host = "a6xr6l0abc72a-ats.iot.us-east-1.amazonaws.com"
        mosaic_path = os.path.expanduser('~') + "/.mosaicdata/"
        root_ca_path = mosaic_path + "root-ca.crt"
        private_key_path = mosaic_path + "private.pem.key"
        certificate_path = mosaic_path + "certificate.pem.crt"

        # Initialization
        self.myShadowClient = AWSIoTMQTTShadowClient(hub_id)
        self.myShadowClient.configureEndpoint(host, 8883)
        self.myShadowClient.configureCredentials(root_ca_path, private_key_path, certificate_path)

        # Configuration
        self.myShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
        self.myShadowClient.configureConnectDisconnectTimeout(15)  # 10 sec
        self.myShadowClient.configureMQTTOperationTimeout(5)  # 5 sec
        self.myShadowClient.onOnline = self.onOnline
        self.myShadowClient.onOffline = self.onOffline
        self._logger.info("Shadow Client initialized")

        # Connect to AWS IoT
        self.myShadowClient.connect(30)

        # Topic to subscribe to
        hub_id = self.canvas.hub_yaml["canvas-hub"]["id"]
        shadow_topic = "canvas-hub-" + hub_id

        # Create device shadow with persistent subscription to the above topic
        self.myDeviceShadow = self.myShadowClient.createShadowHandlerWithName(shadow_topic, True)
        self._logger.info("Device Shadow created")

        # initialize listener for device shadow deltas + get object upon connection
        self.myDeviceShadow.shadowRegisterDeltaCallback(self.onDelta)
        self.myDeviceShadow.shadowGet(self.onGetShadowObj, 10)

    def shadowGet(self):
        self.myDeviceShadow.shadowGet(self.onGetShadowObj, 10)

    def disconnect(self):
        self.myShadowClient.disconnect()

    def handleDeltaFromGet(self, delta):
        self._logger.info("Handling Delta From Get")
        if "userIds" in delta:
            self.handleUserListChanges(delta)
        if "queuedPrint" in delta:
            self.handlePrint(delta)

    def handlePrint(self, payload):
        self._logger.info("Handling Prints")
        self._logger.info(payload)
        self.canvas.downloadPrintFiles(payload["queuedPrint"])
        state_to_send_back = {
            "state": {
                "reported": {
                    "queuedPrint": None
                },
                "desired": {
                    "queuedPrint": None
                }
            }
        }
        self.myDeviceShadow.shadowUpdate(json.dumps(state_to_send_back), self.onUpdate, 10)

    def handleUserListChanges(self, payload):
        self._logger.info("Handling user list delta")
        current_yaml_users = self.canvas.hub_yaml["canvas-users"].keys()
        delta_users = payload["userIds"]

        self._logger.info("YAML: %s" % current_yaml_users)
        self._logger.info("DELTA: %s" % delta_users)

        sameListContent = set(current_yaml_users) == set(delta_users)

        # if contents are not the same, get new list of registered users
        if not sameListContent:
            self._logger.info("Content not the same. Updating yaml user list first.")
            if len(delta_users) < len(current_yaml_users):
                removed_user = str(set(current_yaml_users).difference(set(delta_users)).pop())
                self.canvas.removeUserFromYAML(removed_user)
            self.canvas.getRegisteredUsers()

        users_to_report = delta_users
        reportedState = {
            "state": {
                "reported": {
                    "userIds": users_to_report
                }
            }
        }
        self.myDeviceShadow.shadowUpdate(json.dumps(reportedState), self.onUpdate, 10)

    ##############
    # CALLBACKS
    ##############

    def onGetShadowObj(self, payload, responseStatus, token):
        self._logger.info("GOT SHADOW OBJECT")
        self._logger.info("Payload: %s" % payload)
        self._logger.info("Status: %s" % responseStatus)
        self._logger.info("Token: %s" % token)

        payload = json.loads(payload)
        if responseStatus == "accepted" and "delta" in payload["state"]:
            delta = payload["state"]["delta"]

            if "userIds" in delta:
                self.handleUserListChanges(delta)
            if "queuedPrint" in delta:
                self.handlePrint(delta)
        else:
            self._logger.info("No delta found in object. No action needed.")

    def onDelta(self, payload, responseStatus, token):
        self._logger.info("RECEIVED DELTA")
        self._logger.info("Payload: %s" % payload)
        self._logger.info("Status: %s" % responseStatus)
        self._logger.info("Token: %s" % token)

        payload = json.loads(payload)
        if "userIds" in payload["state"]:
            self.handleUserListChanges(payload["state"])
        if "queuedPrint" in payload["state"]:
            self.handlePrint(payload["state"])

    def onUpdate(self, payload, responseStatus, token):
        self._logger.info("SHADOW UPDATE RESPONSE")
        self._logger.info("Payload: %s" % payload)
        self._logger.info("Status: %s" % responseStatus)
        self._logger.info("Token: %s" % token)

    def onOnline(self):
        self._logger.info("Shadow Client is online")
        self.canvas.aws_connection = True
        self.canvas.checkAWSConnection()

    def onOffline(self):
        self._logger.info("Shadow Client is offline")
        self.canvas.aws_connection = False
        self.canvas.checkAWSConnection()
