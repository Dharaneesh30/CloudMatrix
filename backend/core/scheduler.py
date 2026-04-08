class Scheduler:
    def __init__(self, servers):
        self.servers = servers
    def find_best_server(self, servers):

        # Base case
        if len(servers) == 1:
            return servers[0]

        mid = len(servers) // 2

        # Divide
        left_best = self.find_best_server(servers[:mid])
        right_best = self.find_best_server(servers[mid:])

        # Conquer (choose better server)
        if left_best.current_cpu_usage() < right_best.current_cpu_usage():
            return left_best
        else:
            return right_best


    # Schedule tasks using the divide and conquer method
    def schedule_tasks(self, tasks):

        allocation = {}

        for task in tasks:

            # find best server
            best_server = self.find_best_server(self.servers)

            if best_server.can_allocate(task):
                best_server.assign_task(task)
                allocation[task.task_id] = best_server.server_id
                print(f"Task {task.task_id} allocated to Server {best_server.server_id}")
            else:
                allocation[task.task_id] = None
                print(f"Task {task.task_id} could not be allocated")

        return allocation