from websocket import create_connection
from threading import Lock, Thread

lock = Lock()
message_list = [] #global list

def collect_server1_data():
    global message_list
    bln_running = True
    ws_a = create_connection("wss://www.server1.com")
    ws_a.send("<subscription>")
    while bln_running:   
        response_a =  ws_a.recv()
        lock.acquire()
        message_list.append(response_a)
        lock.release()
        response_a = ""

def collect_server2_data(): 
    global message_list
    bln_running = True
    ws_b = create_connection("wss://www.server2.com")
    ws_b.send("<subscription>")
    while bln_running:   
        response_b =  ws_b.recv()
        lock.acquire()
        message_list.append(response_b)
        lock.release()
        response_b = ""


### --------Main--------
threads = []
for func in [collect_server1_data, collect_server2_data]:
    threads.append(Thread(target=func))
    threads[-1].start()

for thread in threads:
    thread.join() 