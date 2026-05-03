from . import models


def post_init_hook(*args):
    """Manifest hook; see ``hooks.post_init_hook``."""
    from .hooks import post_init_hook as _run

    return _run(*args)
