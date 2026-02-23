import multiprocessing
import queue
import time

def worker_wrapper(func, args, kwargs, result_queue):
    """
    Wrapper function to run the task and put the result in a queue.
    Catches all exceptions and puts them in the queue.
    """
    try:
        result = func(*args, **kwargs)
        result_queue.put({'success': True, 'result': result})
    except Exception as e:
        # Put the exception in the queue
        # Note: Exception must be picklable. Custom exceptions in generation_utils are picklable.
        result_queue.put({'success': False, 'error': e})

def run_task_with_timeout(func, args=(), kwargs=None, timeout=60):
    """
    Run a function in a separate process with a timeout.

    :param func: The function to run. Must be picklable (top-level function).
    :param args: Tuple of positional arguments.
    :param kwargs: Dictionary of keyword arguments.
    :param timeout: Timeout in seconds.
    :return: The result of the function.
    :raises TimeoutError: If the task exceeds the timeout.
    :raises Exception: Any exception raised by the task.
    """
    if kwargs is None:
        kwargs = {}

    # Create a Queue to communicate with the worker process
    result_queue = multiprocessing.Queue()

    # Create and start the process
    process = multiprocessing.Process(target=worker_wrapper, args=(func, args, kwargs, result_queue))
    process.start()

    try:
        # Wait for the result with a timeout
        try:
            result_data = result_queue.get(timeout=timeout)
        except queue.Empty:
            # Timeout occurred
            if process.is_alive():
                process.terminate()
                # Give it a moment to terminate gracefully
                process.join(timeout=1)
                # Force kill if still alive
                if process.is_alive():
                    process.kill()
                    process.join()

            raise TimeoutError(f"Generation timed out after {timeout} seconds")

        # Wait for the process to finish
        process.join()

        # Check result
        if result_data['success']:
            return result_data['result']
        else:
            # Re-raise the exception from the worker
            raise result_data['error']

    except Exception as e:
        # Ensure cleanup if an exception occurs (e.g. KeyboardInterrupt)
        if process.is_alive():
            process.terminate()
            process.join()
        raise e
