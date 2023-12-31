import datetime
import logging

# This function will generate a timestamped and function-scoped print output.
def pprint(message, function_name):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"[{timestamp}] [Function: {function_name}] {message}")