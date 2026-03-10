class Task:
    def __init__(self,task_id,cpu_required,memory_required,priorty,deadline,status):
        self.task_id=task_id
        self.cpu_required=cpu_required
        self.memory_required=memory_required
        self.priority=priorty
        self.deadline=deadline
        self.status="pending"
class Server:
    def __init__(self,task,server_id,cpu_capacity,memory_capacity):
        self.server_id =server_id
        self.cpu_capacity=cpu_capacity
        self.memory_capacity=memory_capacity
        self.task=task
    def cpu_usage(self):
        total=0
        for task in self.task:
            total+=self.cpu_capacity 
        return total 
    def current_memory_usage(self):
        return sum(task.memory_required for task in self.tasks)

    def available_cpu(self):
        return self.cpu_capacity - self.current_cpu_usage()

    def available_memory(self):
        return self.memory_capacity - self.current_memory_usage()

    def can_allocate(self, task):
        return (
            self.available_cpu() >= task.cpu_required and
            self.available_memory() >= task.memory_required
        )

    def assign_task(self, task):
        self.tasks.append(task)
