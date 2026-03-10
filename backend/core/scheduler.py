class TaskScheduler:
    def sort_by_priority(self, tasks):
        if len(tasks) <= 1:
            return tasks
        mid = len(tasks) // 2
        left = self.sort_by_priority(tasks[:mid])
        right = self.sort_by_priority(tasks[mid:])
        return self._merge_priority(left, right)
    def _merge_priority(self, left, right):
        sorted_list = []
        i = j = 0
        while i < len(left) and j < len(right):
            if left[i].priority > right[j].priority:
                sorted_list.append(left[i])
                i += 1
            else:
                sorted_list.append(right[j])
                j += 1
        sorted_list.extend(left[i:])
        sorted_list.extend(right[j:])

        return sorted_list
    def sort_by_deadline(self, tasks):
        if len(tasks) <= 1:
            return tasks

        mid = len(tasks) // 2
        left = self.sort_by_deadline(tasks[:mid])
        right = self.sort_by_deadline(tasks[mid:])
        return self._merge_deadline(left, right)
    def _merge_deadline(self, left, right):
        sorted_list = []
        i = j = 0
        while i < len(left) and j < len(right):
            if left[i].deadline < right[j].deadline:
                sorted_list.append(left[i])
                i += 1
            else:
                sorted_list.append(right[j])
                j += 1
        sorted_list.extend(left[i:])
        sorted_list.extend(right[j:])
        return sorted_list
class Scheduler:
    def __init__(self, servers):
        self.servers = servers   
    def schedule_tasks(self, tasks):
        allocation = {}
        for task in tasks:
            best_server = None
            best_score = None
            for server in self.servers:
                if server.can_allocate(task):
                    remaining_cpu = server.available_cpu() - task.cpu_required
                    if best_score is None or remaining_cpu < best_score:
                        best_score = remaining_cpu
                        best_server = server
            if best_server:
                best_server.assign_task(task)
                allocation[task.task_id] = best_server.server_id
                print(f"Task {task.task_id} -> Server {best_server.server_id}")
            else:
                allocation[task.task_id] = None
                print(f"Task {task.task_id} -> No server available")
        return allocation
def find_available_servers(task, servers):
    available_servers = []
    for server in servers:
        if server.can_allocate(task):
            available_servers.append(server)
    return available_servers
def select_least_loaded_server(servers):
    if len(servers) == 0:
        return None
    best_server = servers[0]
    for server in servers:
        if server.current_cpu_usage() < best_server.current_cpu_usage():
            best_server = server
    return best_server
def schedule_task(task, servers):
    available_servers = find_available_servers(task, servers)
    if len(available_servers) == 0:
        return None
    selected_server = select_least_loaded_server(available_servers)
    selected_server.assign_task(task)
    return selected_server
def schedule_multiple_tasks(tasks, servers):
    results = []
    for task in tasks:
        server = schedule_task(task, servers)
        if server:
            results.append((task.task_id, server.server_id))
        else:
            results.append((task.task_id, "No Server Available"))
    return results

