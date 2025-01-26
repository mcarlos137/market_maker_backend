import logging
import json
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class Watcher:

    def __init__(self, folders_to_watch: [], callback: callable):
        self.observer = Observer()
        self.folders_to_watch = folders_to_watch
        self.callback = callback
        
    def run(self):
        logging.info('ADDING WATCHERS')
        event_handler = Handler(callback=self.callback)
        for folder_to_watch in self.folders_to_watch:
            self.observer.schedule(event_handler, folder_to_watch, recursive=False)
        self.observer.start()
        while True:
            time.sleep(30)
            

class Handler(FileSystemEventHandler):
    
    def __init__(self, callback: callable):
        self.callback = callback

    def on_any_event(self, event):
        if event.is_directory:
            return
        elif event.event_type == 'created':
            try:
                data = json.loads(open(event.src_path, 'r', encoding='UTF-8').read())
                self.callback(event.src_path, data)
            except (Exception) as error:
                logging.error("Error while parsing data %s", error)
                return
            