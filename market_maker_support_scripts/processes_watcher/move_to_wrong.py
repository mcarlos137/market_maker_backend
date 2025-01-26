import os
import shutil
from damexCommons.tools.utils import BASE_PATH

emulated_balance_folder_target = BASE_PATH + '/base/emulated_balances/arbitrage_1/trades_wrong'
emulated_balance_folder = BASE_PATH + '/base/emulated_balances/arbitrage_1/trades'

emulated_balance_files_to_move = []
for emulated_balance_file in os.listdir(emulated_balance_folder):
    if emulated_balance_file == 'old':
        continue
    if int(emulated_balance_file.replace('.json', '')) >= 1724937900000:
        emulated_balance_files_to_move.append(emulated_balance_file)
        emulated_balance_file_base = emulated_balance_folder + '/' + emulated_balance_file
        emulated_balance_file_target = emulated_balance_folder_target + '/' + emulated_balance_file
        print('move', emulated_balance_file_base, 'to', emulated_balance_file_target)
        try:
            shutil.move(emulated_balance_file_base, emulated_balance_file_target)
            print('move_file')
        except (Exception) as error:
            print("Error while moving file", error)

emulated_balance_files_to_move = sorted(emulated_balance_files_to_move)

print('--------------', emulated_balance_files_to_move, len(emulated_balance_files_to_move))