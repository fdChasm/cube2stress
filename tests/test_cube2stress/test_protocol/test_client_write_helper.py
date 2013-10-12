import unittest

from cube2common.cube_data_stream import CubeDataStream

from cube2stress.physics_state import PhysicsState
from cube2stress.protocol.client_write_helper import cwh
from cube2stress.protocol.message_processor import MessageProcessor


class TestClientWriteHelper(unittest.TestCase):
    def test_put_pos(self):
        cds = CubeDataStream()
        
        physics_state = PhysicsState()
        
        cwh.put_pos(cds=cds, cn=5, physics_state=physics_state)
        
        message_processor = MessageProcessor()
        
        messages = message_processor.process(channel=0, data=str(cds))
        
        print messages