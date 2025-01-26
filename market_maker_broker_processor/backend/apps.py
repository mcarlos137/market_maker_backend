from django.apps import AppConfig
from .sub import SubMessage
from .watcher import Watcher


class BackendConfig(AppConfig):
    name = 'backend'

    def ready(self):
        watcher = Watcher()
        watcher.run()
        pass


def execute_sub(args):
    print(f'SUB: {args}')
    SubMessage.main(args)
