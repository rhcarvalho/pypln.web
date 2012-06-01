#!/usr/bin/env python
# coding: utf-8

import uuid
from Queue import Queue
from time import sleep
from logging import Logger, NullHandler
import zmq


class Manager(object):
    #TODO: add another queue for processing jobs
    #TODO: add a timeout for processing jobs (default or get it from client)
    #TODO: if processing job have timeout, remove from processing queue, add
    #      again in job_queue and announce pending job
    #TODO: get status from brokers
    def __init__(self, logger=None, logger_name='Manager', time_to_sleep=0.1):
        self.job_queue = Queue()
        self.context = zmq.Context()
        self.time_to_sleep = time_to_sleep
        if logger is None:
            self.logger = Logger(logger_name)
            self.logger.addHandler(NullHandler())
        else:
            self.logger = logger

    def bind(self, api_host_port, broadcast_host_port):
        self.api_host_port = api_host_port
        self.broadcast_host_port = broadcast_host_port

        self.api = self.context.socket(zmq.REP)
        self.broadcast = self.context.socket(zmq.PUB)

        self.api.bind('tcp://{}:{}'.format(*self.api_host_port))
        self.broadcast.bind('tcp://{}:{}'.format(*self.broadcast_host_port))

    def close_sockets(self):
        self.api.close()
        self.broadcast.close()

    def run(self):
        try:
            while True:
                try:
                    message = self.api.recv_json(zmq.NOBLOCK)
                except zmq.ZMQError:
                    sleep(self.time_to_sleep)
                    pass
                else:
                    self.logger.info('Manager API received: {}'.format(message))
                    command = message['command']
                    if command == 'add job':
                        message['job id'] = uuid.uuid4().hex
                        self.job_queue.put(message)
                        self.api.send_json({'answer': 'job accepted',
                                            'job id': message['job id']})
                        self.broadcast.send('new job')
                    elif command == 'get job':
                        if self.job_queue.empty():
                            self.api.send_json({'job': None})
                        else:
                            job = self.job_queue.get()
                            self.api.send_json({'job': job})
                    elif command == 'finished job':
                        self.api.send_json({'answer': 'good job!'})
                        new_message = 'job finished: {}'.format(message['job id'])
                        self.broadcast.send(new_message)
                    else:
                        self.api.send_json({'answer': 'unknown command'})
        except KeyboardInterrupt:
            self.close_sockets()


if __name__ == '__main__':
    from logging import Logger, StreamHandler, Formatter
    from sys import stdout


    logger = Logger('Manager')
    handler = StreamHandler(stdout)
    formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    api_host_port = ('*', 5555)
    broadcast_host_port = ('*', 5556)
    manager = Manager(logger)
    manager.bind(api_host_port, broadcast_host_port)
    manager.run()
