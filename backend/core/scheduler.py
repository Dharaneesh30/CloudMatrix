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