# coding: utf8

import sys
import inspect

from ..utils import logger


def log_request():

    caller_stack = inspect.stack()[1]
    caller_fct = caller_stack.function

    caller_frame = sys._getframe(1)
    caller_mod = inspect.getmodule(caller_frame)

    caller_fn = getattr(caller_mod, caller_fct)
    req_type = caller_fn.__qualname__.split(".")[0].upper()

    source = inspect.getsource(caller_fn)
    req_type = source.splitlines()[0].split(".")[1].split("(")[0].upper()
    payload = None
    if request.is_json:
        payload = request.get_json()
    elif request.form:
        payload = request.form.to_dict()
    elif request.data:
        payload = request.data.decode("utf-8")

    logger().debug(f"[{req_type}] {caller_mod.__name__}.{caller_fct} - Payload: {payload}")