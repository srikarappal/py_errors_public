import threading, time

lock_a = threading.Lock()
lock_b = threading.Lock()

def t1():
    with lock_a:
        time.sleep(0.01)
        with lock_b:  # waits for b
            pass

def t2():
    with lock_b:
        time.sleep(0.01)
        with lock_a:  # waits for a → circular wait → deadlock
            pass

A = threading.Thread(target=t1)
B = threading.Thread(target=t2)
A.start(); B.start()
A.join(); B.join()  # hangs

