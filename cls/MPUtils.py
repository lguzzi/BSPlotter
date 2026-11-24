from threading import Event, Lock, Thread
from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil, sys

class Progress:
    def __init__(self, total):
        self.total = total
        self.value = 0
        self.lock = Lock()

    def increment(self, amount=1):
        with self.lock:
            self.value += amount
    
    def snapshot(self):
        terminal_width = lambda: min(50, max(10, shutil.get_terminal_size(fallback=(80, 20)).columns - 10))
        with self.lock:
            value = self.value / self.total * 100 if self.total > 0 else 100
            bar = lambda value: '[{}{}%{}]'.format(
                '#'*int(value*terminal_width()//100),
                int(value),
                '-'*int(terminal_width()-value*terminal_width()//100+int(value<100)+int(value<10))
            )
            sys.stdout.write('\r' + bar(value))
            sys.stdout.flush()

    def run(self, stop_event):
        while not stop_event.is_set():
            self.snapshot()
            stop_event.wait(0.1)
        self.snapshot()
        print()

def parallelize(func, nthreads=None):
    def wrapper(args):
        stop_event = Event()
        progress = Progress(len(args))
        results, errors = [None] * len(args), []

        def run(arg):
            try:
                return func(arg)
            finally:
                progress.increment()
        
        progress_thread = Thread(target=progress.run, args=(stop_event,))
        progress_thread.start()
        try:
            with ThreadPoolExecutor(max_workers=nthreads) as executor:
                futures = {
                    executor.submit(run, arg): (index, arg)
                    for index, arg in enumerate(args) 
                }
                for future in as_completed(futures):
                    index, arg = futures[future]
                    try:
                        results[index] = future.result()
                    except Exception as e:
                        task_error = RuntimeError(
                            f"Error processing argument {arg!r}"
                        )
                        task_error.__cause__ = e
                        errors.append(task_error)
        finally:
            stop_event.set()
            progress_thread.join()

        if errors:
            raise ExceptionGroup("parallel operations failed", errors)
        return results
    
    return wrapper
