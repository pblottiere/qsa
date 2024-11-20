# coding: utf8

import sys
import inspect
from flask import request  # Importer request pour récupérer le payload
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

    # Récupérer le payload de la requête
    payload = None
    try:
        if request.is_json:
            payload = request.get_json()  # JSON request body
        elif request.form:
            payload = request.form.to_dict()  # Form data
        elif request.data:
            payload = request.data.decode("utf-8")  # Raw data
    except Exception as e:
        logger().error(f"Failed to extract payload: {e}")
        payload = "Unable to parse payload"

    logger().debug(f"[{req_type}] {caller_mod.__name__}.{caller_fct} - Payload: {payload}")
