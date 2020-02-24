from multiprocessing import Process,Pipe
import time

def f(child_conn):
    for i in range(1, 10):
        child_conn.send(i)
        # time.sleep(1)
    child_conn.close()