__author__ = 'patrickbelon'
import zmq
import os

context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.setsockopt(zmq.SUBSCRIBE, '')
socket.connect("tcp://127.0.0.1:4999")
pid_alive = []
while True:
    msg = socket.recv()
    pid_list = msg.split(":")
    if len(pid_list) > 1:
        print 'created ' + pid_list[1]
    else:
        print 'killed ' + pid_list[0]