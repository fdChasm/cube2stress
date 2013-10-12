import contextlib

from cube2common.cube_data_stream import CubeDataStream
import enet


class EnetClient(object):
    def __init__(self, host, port, game_client):
        address = enet.Address(host, port)
        self._enet_client_host = enet.Host(None, 2, 3, 0, 0)
        self._enet_client_host.connect(address, 3, 0)
        self._enet_client_host.flush()

        self._game_client = game_client
        
        self.disconnecting = False

    def disconnect(self):
        if self.peer is not None and not self.disconnecting:
            self.disconnecting = True
            self.peer.disconnect()

    def service(self):
        event = self._enet_client_host.service(5)

        if event.type == enet.EVENT_TYPE_CONNECT:
            self.is_connected = True
            self.peer = event.peer
            self.failed = False
            self._game_client.on_connected()

        elif event.type == enet.EVENT_TYPE_DISCONNECT:
            self.is_connected = False
            self.peer = None
            self.failed = False
            self._game_client.on_disconnected()

        elif event.type == enet.EVENT_TYPE_RECEIVE:
            self._game_client.on_message_received(event.channelID, event.packet.data)

    def send(self, channel, data, reliable=True):
        if self.peer is None or self.failed or self.disconnecting:
            return

        flags = enet.PACKET_FLAG_RELIABLE if reliable else 0

        packet = enet.Packet(str(data), flags)
        status = self.peer.send(channel, packet)
        if status < 0:
            print("{peer.address}: Error sending packet!".format(peer=self.peer))
            self.failed = True

    @contextlib.contextmanager
    def sendbuffer(self, channel, reliable):
        cds = CubeDataStream()
        yield cds
        self.send(channel, cds, reliable)
