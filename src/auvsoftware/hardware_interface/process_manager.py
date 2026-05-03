from multiprocessing import Pipe, Pool, Process, Queue


class ProcessManager:
    def __init__(self):
        self.processes = {}

    def add_process(self, name, process):
        self.processes[name] = process

    def remove_process(self, name):
        if name in self.processes:
            del self.processes[name]

    def get_process(self, name):
        return self.processes.get(name)

    def start_all(self):
        for process in self.processes.values():
            process.start()

    def stop_all(self):
        for process in self.processes.values():
            process.stop()