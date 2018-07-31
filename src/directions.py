def assert_direction(direction):
    """
    Assert that direction is a direction.
    :param direction
    """
    assert direction in ('left', 'right', 'up', 'down'), ("Assertion failed: %s in not a direction", direction)


def opposite_direction(direction):
    return {
        'left': 'right',
        'right': 'left',
        'up': 'down',
        'down': 'up'
    }[direction]


def left_direction(direction):
    return {
        'left': 'down',
        'down': 'right',
        'right': 'up',
        'up': 'left'
    }[direction]


def right_direction(direction):
    return {
        'left': 'up',
        'up': 'right',
        'right': 'down',
        'down': 'left'
    }[direction]


def position_after_moving(x, y, direction):
    """
    Modify (x, y) position based on direction.
    :param x, y: Coordinates.
    :param direction
    :return: (x', y') - new coordinates.
    """
    return {
        'left': (x - 1, y),
        'right': (x + 1, y),
        'up': (x, y - 1),
        'down': (x, y + 1)
    }[direction]
