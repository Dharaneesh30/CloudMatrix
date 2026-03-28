class Task:
    def __init__(self, task_id, cpu_required, memory_required, priority, deadline, status="pending"):
        self.task_id = task_id
        self.cpu_required = cpu_required
        self.memory_required = memory_required
        self.priority = priority
        self.deadline = deadline
        self.status = status


class Server:
    def __init__(self, server_id, cpu_capacity, memory_capacity, tasks=None):
        self.server_id = server_id
        self.cpu_capacity = cpu_capacity
        self.memory_capacity = memory_capacity
        self.tasks = tasks or []

    def current_cpu_usage(self):
        return sum(task.cpu_required for task in self.tasks)

    def current_memory_usage(self):
        return sum(task.memory_required for task in self.tasks)

    def available_cpu(self):
        return self.cpu_capacity - self.current_cpu_usage()

    def available_memory(self):
        return self.memory_capacity - self.current_memory_usage()

    def can_allocate(self, task):
        return (
            self.available_cpu() >= task.cpu_required
            and self.available_memory() >= task.memory_required
        )

    def assign_task(self, task):
        if self.can_allocate(task):
            self.tasks.append(task)
            task.status = "assigned"
            return True
        return False
