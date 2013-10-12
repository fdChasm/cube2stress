import math

from cube2common.constants import message_types, RAD
from cube2common.read_cube_data_stream import ReadCubeDataStream
from cube2common.utils.clamp import clamp
from cube2common.vec import vec

from cube2stress.physics_state import PhysicsState
from cube2stress.protocol.client_read_stream_protocol import sauerbraten_stream_spec


def vecfromyawpitch(yaw, pitch, move, strafe):
    m = vec(0, 0, 0)
    if move:
        m.x = move * -math.sin(RAD * yaw)
        m.y = move * math.cos(RAD * yaw)
    else:
        m.x = m.y = 0

    if pitch:
        m.x *= math.cos(RAD * pitch)
        m.y *= math.cos(RAD * pitch)
        m.z = move * math.sin(RAD * pitch)
    else:
        m.z = 0

    if strafe:
        m.x += strafe * math.cos(RAD * yaw)
        m.y += strafe * math.sin(RAD * yaw)

    return m


def read_physics_state(cds):
    d = PhysicsState()

    physstate = cds.getbyte()
    flags = cds.getuint()

    for k in range(3):
        n = cds.getbyte()
        n |= cds.getbyte() << 8
        if flags & (1 << k):
            n |= cds.getbyte() << 16
            if n & 0x800000:
                n |= -1 << 24
        d.o[k] = n

    dir = cds.getbyte()
    dir |= cds.getbyte() << 8
    yaw = dir % 360
    pitch = clamp(dir / 360, 0, 180) - 90
    roll = clamp(int(cds.getbyte()), 0, 180) - 90
    mag = cds.getbyte()
    if flags & (1 << 3):
        mag |= cds.getbyte() << 8
    dir = cds.getbyte()
    dir |= cds.getbyte() << 8

    d.vel = vecfromyawpitch(dir % 360, clamp(dir / 360, 0, 180) - 90, 1, 0);

    if flags&(1<<4):
        mag = cds.getbyte()
        if flags&(1<<5):
            mag |= cds.getbyte()<<8

        if flags&(1<<6):
            dir = cds.getbyte()
            dir |= cds.getbyte()<<8
            falling = vecfromyawpitch(dir%360, clamp(dir/360, 0, 180)-90, 1, 0)
        else:
            falling = vec(0, 0, -1)
    else:
        falling = vec(0, 0, 0)
        
    d.falling = falling

    seqcolor = (physstate>>3)&1

    d.yaw = yaw
    d.pitch = pitch
    d.roll = roll

    if (physstate>>4)&2:
        d.move = -1
    else:
        d.move = (physstate>>4)&1

    if (physstate>>6)&2:
        d.strafe = -1
    else:
        d.strafe = (physstate>>6)&1
        
    d.physstate = physstate&7
    
    return d


class MessageProcessor(object):
    def process(self, channel, data):
        if len(data) == 0: return []

        if channel == 0:
            messages = self._parse_channel_0_data(data)
        elif channel == 1:
            messages = sauerbraten_stream_spec.read(data, {'aiclientnum':-1})

        return messages

    def _parse_channel_0_data(self, data):
        cds = ReadCubeDataStream(data)
        message_type = cds.getint()

        if message_type == message_types.N_POS:
            cn = cds.getuint()

            physics_state = read_physics_state(cds)

            message = ('N_POS', {'clientnum': cn, 'physics_state': physics_state, 'raw_position': data})

        elif message_type == message_types.N_JUMPPAD:
            cn = cds.getint()
            jumppad = cds.getint()

            message = ('N_JUMPPAD', {'aiclientnum': cn, 'jumppad': jumppad})

        elif message_type == message_types.N_TELEPORT:
            cn = cds.getint()
            teleport = cds.getint()
            teledest = cds.getint()

            message = ('N_TELEPORT', {'aiclientnum': cn, 'teleport': teleport, 'teledest': teledest})

        return [message]
