def calculate_need(maximum, allocation):
    """Return Need = Max - Allocation for each process and resource."""
    if len(maximum) != len(allocation):
        raise ValueError("Max and Allocation must have the same number of processes")
    if not maximum:
        raise ValueError("Provide at least one process")
    if not isinstance(maximum[0], (list, tuple)) or not maximum[0]:
        raise ValueError("Provide at least one resource for each process")
    resource_count = len(maximum[0])
    need = []
    for max_row, allocated_row in zip(maximum, allocation):
        if not isinstance(max_row, (list, tuple)) or not isinstance(allocated_row, (list, tuple)):
            raise ValueError("Max and Allocation must contain rows of resource values")
        if len(max_row) != resource_count or len(allocated_row) != resource_count:
            raise ValueError("Every process row must contain the same number of resources")
        if len(max_row) != len(allocated_row):
            raise ValueError("Each Max and Allocation row must have the same length")
        if any(not isinstance(value, int) or isinstance(value, bool) for value in (*max_row, *allocated_row)):
            raise ValueError("Resource values must be whole numbers")
        if any(value < 0 for value in (*max_row, *allocated_row)):
            raise ValueError("Resource values cannot be negative")
        if any(a > m for m, a in zip(max_row, allocated_row)):
            raise ValueError("Allocation cannot be greater than Max")
        need.append([m - a for m, a in zip(max_row, allocated_row)])
    return need


def safe_sequence(available, maximum, allocation):
    """Return a safe process order, or None if the state is unsafe."""
    need = calculate_need(maximum, allocation)
    if not isinstance(available, (list, tuple)) or len(available) != len(need[0]):
        raise ValueError("Available must contain one value for each resource type")
    if any(not isinstance(value, int) or isinstance(value, bool) for value in available):
        raise ValueError("Available resource values must be whole numbers")
    if any(value < 0 for value in available):
        raise ValueError("Available resource values cannot be negative")
    work = list(available)
    finished = [False] * len(need)
    order = []
    while len(order) < len(need):
        found = False
        for i, row in enumerate(need):
            if not finished[i] and all(n <= w for n, w in zip(row, work)):
                work = [w + a for w, a in zip(work, allocation[i])]
                finished[i] = True
                order.append("P" + str(i))
                found = True
        if not found:
            return None
    return order
