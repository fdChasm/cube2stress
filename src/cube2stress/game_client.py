from cube2stress.enet_client import EnetClient
from cube2stress.protocol.message_processor import MessageProcessor


class GameClient(object):
    def __init__(self, host, port, controller):
        self._enet_client = EnetClient(host, port, self)
        self._message_processor = MessageProcessor()
        self._controller = controller

    def run(self):
        while True:
            self._enet_client.service()
            if hasattr(self._controller, "on_update"):
                self._controller.on_update(self._enet_client)

    def on_connected(self):
        self._dispatch_event_to_controller("connected", {})

    def on_message_received(self, channel, data):
        for message_type, message_data in self._message_processor.process(channel, data):
            event_name = message_type[2:].lower()
            self._dispatch_event_to_controller(event_name, message_data)

    def on_disconnected(self):
        self._dispatch_event_to_controller("disconnected", {})

    def _dispatch_event_to_controller(self, event_name, event_data):
        handler_name = "on_{}".format(event_name)
        if hasattr(self._controller, handler_name):
            handler = getattr(self._controller, handler_name)
            handler(self._enet_client, **event_data)
