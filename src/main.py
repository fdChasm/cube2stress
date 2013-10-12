from cube2stress.game_client import GameClient
from cube2stress.protocol.client_write_helper import cwh
import heapq
import sys
import itertools
import time
    
spot_in_line = 1
if len(sys.argv) > 1:
    spot_in_line = int(sys.argv[1])
    
scheduling_counter = itertools.count()
def get_task_entry(wait_seconds, func, args, kwargs):
    task = (time.time()+wait_seconds, next(scheduling_counter), func, args, kwargs)
    return task

def run_task(task):
    func = task[2]
    args = task[3]
    kwargs = task[4]
    return func(*args, **kwargs)

class TaskQueue(object):
    def __init__(self):
        self._queue = []
        
    def schedule(self, wait_seconds, func, args, kwargs):
        task_entry = get_task_entry(wait_seconds, func, args, kwargs)
        heapq.heappush(self._queue, task_entry)
        
    def get_tasks_due(self):
        tasks_due = []
        now = time.time()
        while len(self._queue) and self._queue[0][0] < now:
            tasks_due.append(heapq.heappop(self._queue))
        return tasks_due

class RunInCirclesController(object):
    def __init__(self):
        self.cn = None
        self.position_queue = [None]*spot_in_line
        self.followed_clientnums = set()
        self.clientnums = set()
        self.dead = False
        self.following = None
        self.following_dead = False
        self.lifesequence = -1
        
        self.task_queue = TaskQueue()
        
    def on_update(self, enet_client):
        tasks_due = self.task_queue.get_tasks_due()
        for task in tasks_due:
            run_task(task)
    
    def on_connected(self, enet_client):
        pass
        
    def on_disconnected(self, enet_client):
        sys.exit(0)

    def on_servinfo(self, enet_client, clientnum, **kwargs):
        self.cn = clientnum
        with enet_client.sendbuffer(channel=1, reliable=True) as cds:
            cwh.put_connect(cds, name="TestBot", playermodel=0, pwdhash="", authdomain="", authname="")
            
    def on_spawnstate(self, enet_client, lifesequence, **kwargs):
        self.lifesequence = lifesequence
        self.dead = False
        with enet_client.sendbuffer(channel=1, reliable=True) as cds:
            cwh.put_spawn(cds, lifesequence=lifesequence, gunselect=4)
            
    def on_text(self, enet_client, text, clientnum, **kwargs):
        if text == "@shoo":
            enet_client.disconnect()
        elif text == "@followme":
            self.following = clientnum
            
    def on_spawn(self, enet_client, clientnum, **kwargs):
        if clientnum == self.following:
            self.following_dead = False

    def on_pos(self, enet_client, clientnum, physics_state, **kwargs):
        if self.dead: return
        if self.following_dead: return
        if clientnum != self.following: return
        self.position_queue.append(physics_state)
        physics_state = self.position_queue.pop(0)
        if physics_state is not None:
            physics_state.lifesequence = self.lifesequence
            #physics_state.move = 1
            with enet_client.sendbuffer(channel=0, reliable=False) as cds:
                cwh.put_pos(cds, cn=self.cn, physics_state=physics_state)
                
    def on_died(self, enet_client, clientnum, **kwargs):
        if clientnum == self.cn:
            self.dead = True
            self.task_queue.schedule(5, self.send_tryspawn, (enet_client,), {})
        elif clientnum == self.following:
            self.following_dead = True
            physics_state = self.position_queue[-1]
            self.task_queue.schedule(0.033, self.send_lastpos, (enet_client, physics_state), {})

    def on_clientping(self, enet_client, **kwargs):
        pass
    
    def send_tryspawn(self, enet_client):
        with enet_client.sendbuffer(channel=1, reliable=True) as cds:
            cwh.put_tryspawn(cds)
            
    def send_lastpos(self, enet_client, last_physics_state):
        if not self.following_dead: return
        if self.dead: return
        if last_physics_state is None: return
        self.position_queue.append(last_physics_state)
        physics_state = self.position_queue.pop(0)
        physics_state.lifesequence = self.lifesequence
        with enet_client.sendbuffer(channel=0, reliable=False) as cds:
            cwh.put_pos(cds, cn=self.cn, physics_state=physics_state)
        self.task_queue.schedule(0.033, self.send_lastpos, (enet_client, last_physics_state), {})

test_controller = RunInCirclesController()


gc = GameClient("127.0.0.1", 28785, test_controller)
gc.run()
