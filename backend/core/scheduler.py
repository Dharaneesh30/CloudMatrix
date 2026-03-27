def merge_sort(tasks):

    if len(tasks) <= 1:
        return tasks

    mid = len(tasks) // 2

    left = merge_sort(tasks[:mid])
    right = merge_sort(tasks[mid:])

    return merge(left, right)


def merge(left, right):

    result = []
    i = j = 0

    while i < len(left) and j < len(right):

        if left[i]["priority"] <= right[j]["priority"]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    result.extend(left[i:])
    result.extend(right[j:])

    return result