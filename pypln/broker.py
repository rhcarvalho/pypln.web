#!/usr/bin/env python
# coding: utf-8

from time import sleep
from multiprocessing import Process, Queue, cpu_count
import zmq
from client import ManagerClient


def sleep_worker(queue):
    import time
    print '[SleepWorker] Received from queue:', queue.get()
    time.sleep(2)
    print '[SleepWorker] Finished running'
    queue.put(True)
    queue.put(True)

class ManagerBroker(ManagerClient):
    def __init__(self, logger=None, logger_name='ManagerBroker',
                 time_to_sleep=0.1):
        ManagerClient.__init__(self, logger=logger, logger_name=logger_name)
        self.jobs = []
        self.max_jobs = cpu_count()
        self.time_to_sleep = 0.1

    def connect(self, api_host_port, broadcast_host_port):
        super(ManagerBroker, self).connect(api_host_port, broadcast_host_port)
        self.manager_broadcast.setsockopt(zmq.SUBSCRIBE, 'new job')

    def start_job(self, job_spec):
        queue = Queue()
        process = Process(target=sleep_worker, args=(queue, ))
        job_spec['queue'] = queue
        job_spec['process'] = process
        queue.put(job_spec['job'])
        process.start()
        self.logger.info('Process started')

    def get_a_job(self):
        for i in range(self.max_jobs - len(self.jobs)):
            self.manager_api.send_json({'command': 'get job'})
            message = self.manager_api.recv_json()
            self.logger.info('Received from Manager API: {}'.format(message))
            if message['job'] is not None:
                self.jobs.append(message)
                self.start_job(message)
            else:
                break

    def manager_has_job(self):
        try:
            message = self.manager_broadcast.recv(zmq.NOBLOCK)
        except zmq.ZMQError:
            return False
        else:
            self.logger.info('Received from Manager Broadcast: {}'.format(message))
            return True

    def finished_jobs(self):
        return [job for job in self.jobs if job['queue'].qsize() > 1]

    def full_of_jobs(self):
        return len(self.jobs) >= self.max_jobs

    def run(self):
        try:
            self.get_a_job()
            while True:
                if not self.full_of_jobs() and self.manager_has_job():
                    self.logger.info('Trying to get a new job...')
                    self.get_a_job()
                for job in self.finished_jobs():
                    job['process'].join()
                    self.logger.info('Job finished: {}'.format(job))
                    result = job['queue'].get()
                    self.manager_api.send_json({'command': 'finished job',
                                                'job id': job['job']['job id'],
                                                'result': result})
                    result = self.manager_api.recv_json()
                    self.logger.info('Result: {}'.format(result))
                    self.jobs.remove(job)
                    self.logger.info('Job removed')
                    if not self.full_of_jobs():
                        self.get_a_job()
                sleep(self.time_to_sleep)
        except KeyboardInterrupt:
            self.close_sockets()


if __name__ == '__main__':
    from logging import Logger, StreamHandler, Formatter
    from sys import stdout


    logger = Logger('ManagerBroker')
    handler = StreamHandler(stdout)
    formatter = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    broker = ManagerBroker(logger=logger)
    broker.connect(('localhost', 5555), ('localhost', 5556))
    broker.run()
