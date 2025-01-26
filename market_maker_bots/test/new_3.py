stop_check_threads = {}
stop_check_threads['strategy'] = False   

print('stop_check_threads1', stop_check_threads)

for thread in stop_check_threads:
    stop_check_threads[thread] = True
    
print('stop_check_threads2', stop_check_threads)