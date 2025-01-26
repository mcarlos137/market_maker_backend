import time
import json
import os
import shutil
import os
from datetime import datetime
from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler

DIRECTORIES_TO_WATCH = ["../action_files", "../strategy_files"]

class Watcher:
    
    def __init__(self):
        self.observer = PollingObserver()

    def run(self):
        print('ADDING WATCHERS')
        threads = []
        for i in range(len(DIRECTORIES_TO_WATCH)):
            event_handler = Handler()
            self.observer.schedule(event_handler, DIRECTORIES_TO_WATCH[i], recursive=True)
            threads.append(self.observer)
        self.observer.start()
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()


class Handler(FileSystemEventHandler):

    @staticmethod
    def on_any_event(event):
        if event.is_directory:
            return None

        elif event.event_type == 'created':
            # Take any action here when a file is first created.
            print("Received created event - %s." % event.src_path)
            if '.swp' in event.src_path:
                return
            if "action_files" in event.src_path: 
                print('action_files')
                try:
                    actions = json.loads(open(event.src_path, 'r', encoding='UTF-8').read())
                except UnicodeDecodeError as error:
                    print('error', error)
                    return
                for obj in actions:
                    if not obj.get('instance_id') is None:
                        instance_id = obj['instance_id']
                        with open("../instances.json") as f:
                            instances = json.load(f)
                            if instance_id not in str(instances):
                                break
                        action = obj['action']
                        request = obj['request']
                        print(f'instance_id: {instance_id}')
                        print(f'action: {action}')
                        print(f'request: {request}')
                        command = "commlib-cli --username mqtt-test --password mqtt-test --host localhost --port 1883 --btype mqtt rpcc "
                        command = command + \
                            "'hbot/%s/%s' '%s' " % (instance_id, action, request)
                        print(f'command: {command}')
                        response = os.system(command=command)
                        print(f'response: {response}')
                    else:
                         with open("../region.json") as f:
                            r = json.load(f)
                            region = obj['params']['region']
                            if region == r['name']:
                                print('execute:', actions)
                                match obj['action']:
                                    case 'create_bot':
                                        bot_id = obj['params']['bot_id']
                                        bot_group = obj['params']['bot_group']
                                        bot_type = obj['params']['bot_type']
                                        exchange = obj['params']['exchange']
                                        api = obj['params']['api']
                                        connector = obj['params']['connector']
                                        wallet = obj['params']['wallet']
                                        strategy = obj['params']['strategy']
                                        base_asset = obj['params']['base_asset']
                                        quote_asset = obj['params']['quote_asset']
                                        creation_timestamp = obj['params']['creation_timestamp']
                                        tick_time = obj['params']['tick_time']
                                        use = obj['params']['use']
                                        command = None
                                        if exchange is not None and api is not None:
                                            command = "../scripts/create_bot_script.sh %s %s %s %s %s %s %s %s %s %s %s %s" % (bot_id, bot_group, bot_type, exchange, api, strategy, base_asset, quote_asset, tick_time, creation_timestamp, region, use)
                                        elif connector is not None and wallet is not None:
                                             command = "../scripts/create_bot_dex_script.sh %s %s %s %s %s %s %s %s %s %s %s %s" % (bot_id, bot_group, bot_type, connector, wallet, strategy, base_asset, quote_asset, tick_time, creation_timestamp, region, use)
                                        if command is None:
                                            print(f'no command available for params {obj["params"]}')
                                            return
                                        print(f'command: {command}')
                                        response = os.system(command=command)
                                        print(f'response: {response}')
                                    case 'restart_bot':
                                        bot_id = obj['params']['bot_id']   
                                        bot_group = obj['params']['bot_group']
                                        command = "../scripts/restart_bot_script.sh %s %s" % (bot_id, bot_group)
                                        print(f'command: {command}')
                                        response = os.system(command=command)
                                        print(f'response: {response}')  
                                    case 'activate_bot':
                                        bot_id = obj['params']['bot_id']     
                                        bot_group = obj['params']['bot_group']
                                        command = "../scripts/activate_bot_script.sh %s %s" % (bot_id, bot_group)
                                        print(f'command: {command}')
                                        response = os.system(command=command)
                                        print(f'response: {response}')   
                                    case 'inactivate_bot':
                                        bot_id = obj['params']['bot_id']   
                                        bot_group = obj['params']['bot_group']  
                                        command = "../scripts/inactivate_bot_script.sh %s %s" % (bot_id, bot_group)
                                        print(f'command: {command}')
                                        response = os.system(command=command)
                                        print(f'response: {response}')    
                                    case 'edit_bot':
                                        bot_id = obj['params']['bot_id']   
                                        bot_group = obj['params']['bot_group']  
                                        del obj['params']['bot_group']
                                        params = '\'' + json.dumps(obj['params']) + '\''
                                        command = "../scripts/edit_bot_script.sh %s %s %s" % (bot_id, bot_group, params)
                                        print(f'command: {command}')
                                        response = os.system(command=command)
                                        print(f'response: {response}')    
                                        
                                    case 'create_strategy':
                                        strategy_id = obj['params']['strategy_id']   
                                        strategy_type = obj['params']['strategy_type']  
                                        version = obj['params']['version']  
                                        use = obj['params']['use']  
                                        del obj['params']['region']
                                        params = '\'' + json.dumps(obj['params']) + '\''
                                        command = "../scripts/create_strategy_script.sh %s %s %s %s %s" % (strategy_id, strategy_type, params, version, use)
                                        print(f'command: {command}')
                                        response = os.system(command=command)
                                        print(f'response: {response}')    
                                        
                                    case 'create_target':
                                        target_id = obj['params']['target_id']   
                                        del obj['params']['region']
                                        params = '\'' + json.dumps(obj['params']) + '\''
                                        command = "../scripts/create_target_script.sh %s %s" % (target_id, params)
                                        print(f'command: {command}')
                                        response = os.system(command=command)
                                        print(f'response: {response}')    
                                    case 'edit_target':
                                        target_id = obj['params']['target_id']   
                                        del obj['params']['region']
                                        params = '\'' + json.dumps(obj['params']) + '\''
                                        command = "../scripts/edit_target_script.sh %s %s" % (target_id, params)
                                        print(f'command: {command}')
                                        response = os.system(command=command)
                                        print(f'response: {response}')    
                                        
                                    case 'create_orchestration_rule':
                                        orchestration_rule_id = obj['params']['orchestration_rule_id']  
                                        strategy = obj['params']['strategy']
                                        start_time = obj['params']['start_time']
                                        exchanges_apis = obj['params']['exchanges_apis']
                                        members = obj['params']['members']  
                                        creation_timestamp = obj['params']['creation_timestamp']
                                        tick_time = obj['params']['tick_time']
                                        excluded_days = obj['params']['excluded_days'] 
                                        use = obj['params']['use'] 
                                        del obj['params']['region']
                                        command = "../scripts/create_orchestration_rule_script.sh %s %s %s %s %s %s %s %s %s" % (orchestration_rule_id, strategy, '\"' + members + '\"', tick_time, creation_timestamp, start_time, '\'' + exchanges_apis + '\'', '\"' + excluded_days + '\"', use)
                                        print(f'command: {command}')
                                        response = os.system(command=command)
                                        print(f'response: {response}')
                                    case 'edit_orchestration_rule':
                                        orchestration_rule_id = obj['params']['orchestration_rule_id']  
                                        del obj['params']['region'] 
                                        params = '\'' + json.dumps(obj['params']) + '\''
                                        command = "../scripts/edit_orchestration_rule_script.sh %s %s" % (orchestration_rule_id, params)
                                        print(f'command: {command}')
                                        response = os.system(command=command)
                                        print(f'response: {response}')       
                                    case 'restart_orchestration_rule':
                                        orchestration_rule_id = obj['params']['orchestration_rule_id']  
                                        command = "../scripts/restart_orchestration_rule_script.sh %s" % (orchestration_rule_id)
                                        print(f'command: {command}')
                                        response = os.system(command=command)
                                        print(f'response: {response}')   
                                    case 'activate_orchestration_rule':
                                        orchestration_rule_id = obj['params']['orchestration_rule_id']  
                                        command = "../scripts/activate_orchestration_rule_script.sh %s" % (orchestration_rule_id)
                                        print(f'command: {command}')
                                        response = os.system(command=command)
                                        print(f'response: {response}')   
                                    case 'inactivate_orchestration_rule':
                                        orchestration_rule_id = obj['params']['orchestration_rule_id']  
                                        command = "../scripts/inactivate_orchestration_rule_script.sh %s" % (orchestration_rule_id)
                                        print(f'command: {command}')
                                        response = os.system(command=command)
                                        print(f'response: {response}')    
                                    case 'edit_orchestration_rule_target':
                                        orchestration_rule_id = obj['params']['orchestration_rule_id']  
                                        del obj['params']['orchestration_rule_id']
                                        del obj['params']['region']
                                        params = '\'' + json.dumps(obj['params']) + '\''
                                        command = "../scripts/edit_orchestration_rule_target_script.sh %s %s" % (orchestration_rule_id, params)
                                        print(f'command: {command}')
                                        response = os.system(command=command)
                                        print(f'response: {response}')   
                                    case 'edit_orchestration_rule_rules':
                                        orchestration_rule_id = obj['params']['orchestration_rule_id']  
                                        del obj['params']['orchestration_rule_id']
                                        del obj['params']['region']
                                        params = '\'' + json.dumps(obj['params']['rules']) + '\''
                                        command = "../scripts/edit_orchestration_rule_rules_script.sh %s %s" % (orchestration_rule_id, params)
                                        print(f'command: {command}')
                                        response = os.system(command=command)
                                        print(f'response: {response}')
                                        
                                    case 'create_bot_multi_source':                                        
                                        bot_id = obj['params']['bot_id']
                                        bot_group = obj['params']['bot_group']
                                        bot_type = obj['params']['bot_type']
                                        exchanges_apis = obj['params']['exchanges_apis']
                                        connectors_wallets = obj['params']['connectors_wallets']
                                        strategy = obj['params']['strategy']
                                        base_assets = obj['params']['base_assets']
                                        quote_asset = obj['params']['quote_asset']
                                        creation_timestamp = obj['params']['creation_timestamp']
                                        tick_time = obj['params']['tick_time']
                                        use = obj['params']['use']
                                        testing = 'true' if bool(obj['params']['testing']) else 'false'
                                        emulated_balance = obj['params']['emulated_balance']
                                        command = None
                                        if exchanges_apis is not None:
                                            command = "../scripts/create_bot_multi_source_script.sh %s %s %s %r %s %r %s %s %s %s %s %s %s" % (bot_id, bot_group, bot_type, exchanges_apis, strategy, base_assets, quote_asset, tick_time, creation_timestamp, region, use, testing, emulated_balance)
                                        elif connectors_wallets is not None:
                                             command = "../scripts/create_bot_multi_source_dex_script.sh %s %s %s %r %s %r %s %s %s %s %s %s %s" % (bot_id, bot_group, bot_type, connectors_wallets, strategy, base_assets, quote_asset, tick_time, creation_timestamp, region, use, testing, emulated_balance)
                                        if command is None:
                                            print(f'no command available for params {obj["params"]}')
                                            return
                                        print(f'command: {command}')
                                        response = os.system(command=command)
                                        print(f'response: {response}')
                                    
                                        
                    time.sleep(5)

        elif event.event_type == 'modified':
            # Taken any action here when a file is modified.
            print("Received modified event - %s." % event.src_path)