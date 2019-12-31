import os
import json
import time
import threading
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTShadowClient
from . import constants


class Shadow():
    def __init__(self, canvas):
        self.canvas = canvas
        self._logger = canvas._logger
        self._hub_id = canvas.hub_yaml["canvas-hub"]["id"]
        self._myShadowClient = None
        self._myDeviceShadow = None
        self._connectThread = None

        self._initialize()

    ##############
    # PRIVATE
    ##############

    def _initialize(self):
        mosaic_path = os.path.expanduser('~') + "/.mosaicdata/"
        root_ca_path = mosaic_path + "root-ca.crt"
        private_key_path = mosaic_path + "private.pem.key"
        certificate_path = mosaic_path + "certificate.pem.crt"

        # Initialization
        self._myShadowClient = AWSIoTMQTTShadowClient(self._hub_id)
        self._myShadowClient.configureEndpoint(constants.SHADOW_CLIENT_HOST, 8883)
        self._myShadowClient.configureCredentials(root_ca_path, private_key_path, certificate_path)

        # Configuration
        self._myShadowClient.configureAutoReconnectBackoffTime(1, 32, 20)
        self._myShadowClient.configureConnectDisconnectTimeout(15)  # 15 sec
        self._myShadowClient.configureMQTTOperationTimeout(5)  # 5 sec
        self._myShadowClient.onOnline = self._onOnline
        self._myShadowClient.onOffline = self._onOffline
        self._logger.info("Shadow client initialized")

    def _connectShadowClient(self):
        # Connect to AWS IoT
        try:
            self._logger.info("Connecting shadow client...")
            self._myShadowClient.connect(30)
            self._subscribeShadowDeviceToTopic()
        except:
            self._logger.info("Could not connect shadow client")

    def _subscribeShadowDeviceToTopic(self):
        # Create device shadow with persistent subscription to the topic (i.e current hub)
        try:
            self._logger.info("Device shadow subscribing to current hub topic...")
            shadow_topic = "canvas-hub-" + self._hub_id
            self._myDeviceShadow = self._myShadowClient.createShadowHandlerWithName(shadow_topic, True)
            self._myDeviceShadow.shadowRegisterDeltaCallback(self._onDelta)  # initialize listener for device shadow deltas
            self._logger.info("Device shadow successfully subscribed to topic")
            self.getData()
        except:
            self._logger.info("Could not subscribe device shadow to the current hub topic")

    def _startConnectThread(self):
        if self._connectThread is not None:
            self._stopConnectThread()

        self._connectThreadStop = False
        self._connectThread = threading.Thread(target=self._connectToAWS)
        self._connectThread.daemon = True
        self._connectThread.start()

    def _connectToAWS(self):
        while not self._connectThreadStop:
            self._connectShadowClient()
            time.sleep(30)

    def _stopConnectThread(self):
        self._connectThreadStop = True
        if self._connectThread and threading.current_thread() != self._connectThread:
            self._connectThread.join()
        self._connectThread = None

    def _handlePrint(self, payload):
        self._logger.info("Handling print download")
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
        self._myDeviceShadow.shadowUpdate(json.dumps(state_to_send_back), self._onUpdate, 10)

    def _handleUserListChanges(self, payload):
        self._logger.info("Handling user list delta")
        current_yaml_users = list(self.canvas.hub_yaml["canvas-users"])  # for Python 2 & 3
        delta_users = payload["userIds"]

        # if contents are not the same, get new list of registered users
        if not set(current_yaml_users) == set(delta_users):
            self._logger.info("Content not the same. Updating yaml user list first.")
            if len(delta_users) < len(current_yaml_users):
                removed_user = str(set(current_yaml_users).difference(set(delta_users)).pop())
                self.canvas.removeUserFromYAML(removed_user)

        users_to_report = delta_users
        reportedState = {
            "state": {
                "reported": {
                    "userIds": users_to_report
                }
            }
        }
        self._myDeviceShadow.shadowUpdate(json.dumps(reportedState), self._onUpdate, 10)
        # if there are no linked users, disconnect shadow client
        if not self.canvas.hub_yaml["canvas-users"] and self.canvas.aws_connection:
            self._myShadowClient.disconnect()

    def _handleChanges(self, payload):
        if "userIds" in payload:
            self._handleUserListChanges(payload)
        if "queuedPrint" in payload:
            self._handlePrint(payload)

    # CALLBACKS

    def _onGetShadowObj(self, payload, responseStatus, token):
        self._logger.info("GOT SHADOW OBJECT")
        payload = json.loads(payload)
        if responseStatus == "accepted" and "delta" in payload["state"]:
            delta = payload["state"]["delta"]
            self._handleChanges(delta)
        else:
            self._logger.info("No delta found in object. No action needed.")

    def _onDelta(self, payload, responseStatus, token):
        self._logger.info("RECEIVED DELTA")
        payload = json.loads(payload)
        self._handleChanges(payload["state"])

    def _onUpdate(self, payload, responseStatus, token):
        self._logger.info("SHADOW UPDATE RESPONSE")

    def _onOnline(self):
        self._logger.info("Shadow client is online")
        self.canvas.aws_connection = True
        self.canvas.checkAWSConnection()
        self._connectThreadStop = True

    def _onOffline(self):
        self._logger.info("Shadow client is offline")
        self.canvas.aws_connection = False
        self.canvas.checkAWSConnection()

    ##############
    # PUBLIC
    ##############

    def connect(self):
        self._startConnectThread()

    def getData(self):
        self._myDeviceShadow.shadowGet(self._onGetShadowObj, 10)

    def disconnect(self):
        self._myShadowClient.disconnect()
