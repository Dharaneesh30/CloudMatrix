def greedy_allocate(tasks, servers=None):
    """Allocate tasks to servers using greedy first-fit by descending priority."""

    if servers is None:
        servers = [
            {"server_id": "S1", "cpu": 1.0, "memory": 1.0},
            {"server_id": "S2", "cpu": 1.0, "memory": 1.0},
            {"server_id": "S3", "cpu": 1.0, "memory": 1.0}
        ]

    ordered_tasks = sorted(tasks, key=lambda t: float(t.get("priority", 0)), reverse=True)

    allocations = []
    unassigned = []

    for task in ordered_tasks:
        cpu_req = float(task.get("cpu_request", 1))
        mem_req = float(task.get("memory_request", 1))

        placed = False
        for server in servers:
            if server["cpu"] >= cpu_req and server["memory"] >= mem_req:
                allocations.append({
                    "task_id": task.get("id"),
                    "server": server["server_id"],
                    "priority": float(task.get("priority", 0)),
                    "cpu_request": cpu_req,
                    "memory_request": mem_req
                })
                server["cpu"] -= cpu_req
                server["memory"] -= mem_req
                placed = True
                break

        if not placed:
            unassigned.append({
                "task_id": task.get("id"),
                "priority": float(task.get("priority", 0)),
                "cpu_request": cpu_req,
                "memory_request": mem_req
            })

    return {
        "allocations": allocations,
        "unassigned": unassigned,
        "servers": servers
    }