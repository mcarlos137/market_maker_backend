import time
from datetime import datetime

#current_time = int(time.time() * 1e3)
current_time = int(1721579007000)
week_day = datetime.fromtimestamp(current_time / 1e3).strftime('%A')
print('week_day', week_day)