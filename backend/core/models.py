class Task:
    def __init__(self,task_id,cpu_required,memory_required,priorty,deadline,status):
        self.task_id=task_id
        self.cpu_required=cpu_required
        self.memory_required=memory_required
        self.priority=priorty
        self.deadline=deadline
        self.status="pending"
class Server:
    def __init__(self,server_id,cpu_capacity,memory_capacity):
        self.server_id =server_id
        self.cpu_capacity=cpu_capacity
        self.memory_capacity=memory_capacity
        