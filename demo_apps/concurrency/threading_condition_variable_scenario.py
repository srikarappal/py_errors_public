import threading, time
cv = threading.Condition()
data_ready = False

def producer():
    global data_ready
    # compute ...
    data_ready = True
    cv.notify()  # RuntimeError: must hold the lock!

def consumer():
    with cv:
        while not data_ready:
            cv.wait()
        # use data

threading.Thread(target=consumer).start()
time.sleep(0.05)
threading.Thread(target=producer).start()
