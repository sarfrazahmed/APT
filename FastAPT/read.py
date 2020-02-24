import multiprocessing
import time
manager = multiprocessing.Manager()

val = multiprocessing.Value("i", 1, lock=True)

for p in range(1, 10):
    val = val + 1
    time.sleep(1)