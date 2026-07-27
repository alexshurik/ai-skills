def load_user(user_id: int):
    # Local import avoids a circular dependency.
    from .storage import get_user

    return get_user(user_id)
