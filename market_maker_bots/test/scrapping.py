'''
from urllib.request import urlopen
import gzip
import re
import time
from bs4 import BeautifulSoup 

url = "https://www.binance.com/en/trade/HOT_USDT?type=spot"

page = urlopen(url)

html_bytes = gzip.decompress(page.read())

print(html_bytes)

html = html_bytes.decode("utf-8")



print(html)

pattern = "<title.*?>.*?</title.*?>"
match_results = re.search(pattern, html, re.IGNORECASE)
title = match_results.group()
title = re.sub("<.*?>", "", title) # Remove HTML tags


#start_index = html.find("<title>") + len("<title>")
#end_index = html.find("</title>")
#title = html[start_index:end_index]

print(title)

soup = BeautifulSoup(html, 'html.parser') 

app = soup.find_all('div', class_='__APP')
  
print(app)

scripts = soup.find_all("script")

print(len(scripts))

divs = soup.find_all("div")

print(len(divs))

for div in divs:
    #if 'Book' in div:
    print(div.name)
    #    break
    #time.sleep(2)

#<div class="ask-light" style="font-size: 12px; flex: 1 1 0%; text-align: left;">0.001612</div>

#pattern_1 = '<div class="tradew-ob-container css-vurnku" id="spotOrderbook">.*?</div></div></div></div></div>'
#match_results_1 = re.search(pattern_1, html, re.IGNORECASE)
#order_book = match_results_1.group()
#order_book = re.sub("<.*?>", "", order_book) # Remove HTML tags

  
#<div class="tradew-ob-container css-vurnku" id="spotOrderbook"><div class="orderbook-header "><div class="orderbook-header-tips"><div class="bn-tooltips-wrap bn-tooltips-web"><div class="bn-tooltips-ele"><div class="ob-type-button" data-testid="defaultModeButton" style="opacity: 1;"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2.66663 2.66699L7.33329 2.66699L7.33329 7.33366L2.66663 7.33366L2.66663 2.66699Z" fill="var(--color-Sell)"></path><path d="M2.66663 8.66699L7.33329 8.66699L7.33329 13.3337L2.66663 13.3337L2.66663 8.66699Z" fill="var(--color-Buy)"></path><path fill-rule="evenodd" clip-rule="evenodd" d="M8.66663 2.66699L13.3333 2.66699L13.3333 5.33366L8.66663 5.33366L8.66663 2.66699ZM8.66663 6.66699L13.3333 6.66699L13.3333 9.33366L8.66663 9.33366L8.66663 6.66699ZM13.3333 10.667L8.66663 10.667L8.66663 13.3337L13.3333 13.3337L13.3333 10.667Z" fill="var(--color-IconNormal)"></path></svg></div></div></div><div class="bn-tooltips-wrap bn-tooltips-web"><div class="bn-tooltips-ele"><div class="ob-type-button" data-testid="buyModeButton" style="opacity: 0.5;"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none"><g><path d="M2.66663 2.66699L7.33329 2.66699L7.33329 13.3337L2.66663 13.3337L2.66663 2.66699Z" fill="var(--color-Buy)"></path><path fill-rule="evenodd" clip-rule="evenodd" d="M8.66663 2.66699L13.3333 2.66699L13.3333 5.33366L8.66663 5.33366L8.66663 2.66699ZM8.66663 6.66699L13.3333 6.66699L13.3333 9.33366L8.66663 9.33366L8.66663 6.66699ZM13.3333 10.667L8.66663 10.667L8.66663 13.3337L13.3333 13.3337L13.3333 10.667Z" fill="var(--color-IconNormal)"></path></g></svg></div></div></div><div class="bn-tooltips-wrap bn-tooltips-web"><div class="bn-tooltips-ele"><div class="ob-type-button" data-testid="sellModeButton" style="opacity: 0.5;"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none"><g><path d="M2.66663 2.66699L7.33329 2.66699L7.33329 13.3337L2.66663 13.3337L2.66663 2.66699Z" fill="var(--color-Sell)"></path><path fill-rule="evenodd" clip-rule="evenodd" d="M8.66663 2.66699L13.3333 2.66699L13.3333 5.33366L8.66663 5.33366L8.66663 2.66699ZM8.66663 6.66699L13.3333 6.66699L13.3333 9.33366L8.66663 9.33366L8.66663 6.66699ZM13.3333 10.667L8.66663 10.667L8.66663 13.3337L13.3333 13.3337L13.3333 10.667Z" fill="var(--color-IconNormal)"></path></g></svg></div></div></div></div><div class="orderbook-tickSize"><div class="bn-tooltips-wrap"><div class="bn-tooltips-ele"><div class="tick-content"><span>0.000001</span><svg class="bn-svg ob-icon-caretdown" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M16.5 8.49v2.25L12 15.51l-4.5-4.77V8.49h9z" fill="currentColor"></path></svg></div></div><div class="bn-bubble bn-bubble__unset shadow data-font-14 bn-tooltips" style="transform: translate(0px, 0px); top: 100%; right: 0px;"><div class="bn-bubble-content" style="margin-top: 4px;"></div></div></div></div></div><div class="orderbook-tbheader"><div class="content"><div class="item" style="flex: 1 1 0%; justify-content: flex-start;">Price(USDT)</div><div class="item" style="flex: 1 1 0%; justify-content: flex-end;">Amount(HOT)</div><div class="item" style="flex: 1 1 0%; justify-content: flex-end;">Total</div></div></div><div class="orderlist-container"><div class="orderbook-list orderbook-ask has-overlay"><div style="overflow: visible; height: 0px; width: 0px;"><div class="orderbook-list-container" style="position: relative; height: 62px; width: 290px; overflow: auto; will-change: transform; direction: ltr;"><div style="height: 60px; width: 100%;"><div class="orderbook-progress " style="position: absolute; left: 0px; top: 0px; height: 20px; width: 100%; box-sizing: border-box;"><div class="progress-container" style="flex-direction: row;"><div class="row-content "><div class="ask-light" style="font-size: 12px; flex: 1 1 0%; text-align: left;">0.001599</div><div class="text" style="text-align: right;">5.64M</div><div class="text" style="text-align: right;">9.01K</div></div><div class="progress-bar ask-bar" style="transform: translateX(-100%); left: 100%;"></div></div></div><div class="orderbook-progress " style="position: absolute; left: 0px; top: 20px; height: 20px; width: 100%; box-sizing: border-box;"><div class="progress-container" style="flex-direction: row;"><div class="row-content "><div class="ask-light" style="font-size: 12px; flex: 1 1 0%; text-align: left;">0.001598</div><div class="text" style="text-align: right;">2.38M</div><div class="text" style="text-align: right;">3.80K</div></div><div class="progress-bar ask-bar" style="transform: translateX(-76.8722%); left: 100%;"></div></div></div><div class="orderbook-progress " style="position: absolute; left: 0px; top: 40px; height: 20px; width: 100%; box-sizing: border-box;"><div class="progress-container" style="flex-direction: row;"><div class="row-content "><div class="ask-light" style="font-size: 12px; flex: 1 1 0%; text-align: left;">0.001597</div><div class="text" style="text-align: right;">721.63K</div><div class="text" style="text-align: right;">1.15K</div></div><div class="progress-bar ask-bar" style="transform: translateX(-23.3005%); left: 100%;"></div></div></div></div></div><div class="overlay left"><div class="content" style="transform: translate(-220px, calc(-50% - 60px));"><div class="overlayItem"><div class="titleItem">Avg.Price:</div><div class="css-vurnku">≈ 0.002</div></div><div class="overlayItem"><div class="titleItem">Sum HOT:</div><div>8,739,934</div></div><div class="overlayItem"><div class="titleItem">Sum USDT:</div><div>13,971.330</div></div></div><div class="triangle" style="transform: translate(0px, calc(-50% - 60px));"></div></div></div><div class="resize-triggers"><div class="expand-trigger"><div style="width: 291px; height: 63px;"></div></div><div class="contract-trigger"></div></div></div><div class="orderbook-ticker"><div class="contractPrice status-sell">0.001596<svg class="bn-svg arrow-icon status-sell" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" clip-rule="evenodd" d="M12 20.999l7.071-7.071-1.768-1.768-4.054 4.055V2.998h-2.5v13.216L6.696 12.16l-1.768 1.768 7.07 7.071H12z" fill="currentColor"></path></svg></div><div class="markPrice">$0.001596</div><div><a target="_blank" title="orderbook info" rel="nofollow" class="ob-more-link" href="/orderbook/HOT_USDT"><svg class="bn-svg ob-more" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" clip-rule="evenodd" d="M12.288 12l-3.89 3.89 1.768 1.767L15.823 12l-1.768-1.768-3.889-3.889-1.768 1.768 3.89 3.89z" fill="currentColor"></path></svg></a></div></div><div class="orderbook-list orderbook-bid has-overlay"><div style="overflow: visible; height: 0px; width: 0px;"><div class="orderbook-list-container" style="position: relative; height: 62px; width: 290px; overflow: auto; will-change: transform; direction: ltr;"><div style="height: 60px; width: 100%;"><div class="orderbook-progress " style="position: absolute; left: 0px; top: 0px; height: 20px; width: 100%; box-sizing: border-box;"><div class="progress-container" style="flex-direction: row;"><div class="row-content "><div class="bid-light" style="font-size: 12px; flex: 1 1 0%; text-align: left;">0.001595</div><div class="text" style="text-align: right;">227.61K</div><div class="text" style="text-align: right;">363.044</div></div><div class="progress-bar bid-bar" style="transform: translateX(-7.34942%); left: 100%;"></div></div></div><div class="orderbook-progress " style="position: absolute; left: 0px; top: 20px; height: 20px; width: 100%; box-sizing: border-box;"><div class="progress-container" style="flex-direction: row;"><div class="row-content "><div class="bid-light" style="font-size: 12px; flex: 1 1 0%; text-align: left;">0.001594</div><div class="text" style="text-align: right;">1.69M</div><div class="text" style="text-align: right;">2.69K</div></div><div class="progress-bar bid-bar" style="transform: translateX(-54.584%); left: 100%;"></div></div></div><div class="orderbook-progress " style="position: absolute; left: 0px; top: 40px; height: 20px; width: 100%; box-sizing: border-box;"><div class="progress-container" style="flex-direction: row;"><div class="row-content "><div class="bid-light" style="font-size: 12px; flex: 1 1 0%; text-align: left;">0.001593</div><div class="text" style="text-align: right;">4.97M</div><div class="text" style="text-align: right;">7.91K</div></div><div class="progress-bar bid-bar" style="transform: translateX(-100%); left: 100%;"></div></div></div></div></div><div class="overlay left"><div class="content" style="transform: translate(-220px, calc(-50% - 22px));"><div class="overlayItem"><div class="titleItem">Avg.Price:</div><div class="css-vurnku">≈ 0.002</div></div><div class="overlayItem"><div class="titleItem">Sum HOT:</div><div>1,918,098</div></div><div class="overlayItem"><div class="titleItem">Sum USDT:</div><div>3,057.676</div></div></div><div class="triangle" style="transform: translate(0px, calc(-50% - 22px));"></div></div></div><div class="resize-triggers"><div class="expand-trigger"><div style="width: 291px; height: 63px;"></div></div><div class="contract-trigger"></div></div></div></div><div class="css-1y0151x"><div class="orderbook-compare"><div class="compare-direction"><div>B</div><div class="compare-percent-buy">55.61%</div></div><div class="compare-bar"><div class="compare-bids-bar" style="width: 55.61%;"></div><div class="compare-asks-bar" style="width: 44.39%;"></div></div><div class="compare-direction"><div class="compare-percent-sell">44.39%</div><div>S</div></div></div></div></div>
#print(order_book)
'''

'''
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time

url = "http://www.yahoo.com"
browser = webdriver.Chrome()
browser.get(url)
body = browser.find_element(By.NAME, 'p')
time.sleep(10)
#page_source = browser.page_source('body')
#all_body_id_html =  browser.find_element_by_id('body') # you can also get all html

print(body)
browser.close()
'''


from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common import NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.support.wait import WebDriverWait
from bs4 import BeautifulSoup


options = webdriver.ChromeOptions()
options.add_experimental_option('excludeSwitches', ['enable-automation'])
options.add_experimental_option('useAutomationExtension', False)
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-setuid-sandbox")
options.add_argument('--disable-infobars')
options.add_argument('--disable-extensions')
#options.page_load_strategy = 'none'
print('arguments ->', options.arguments)
#options.enable_downloads = True


browser = webdriver.Remote(
   command_executor='http://192.168.0.116:4444',
   options=options
)

print('capabilities ->', browser.capabilities)

#browser = webdriver.Chrome()

browser.get('https://www.binance.com/en/trade/HOT_USDT?type=spot')
#browser.get('https://gist.github.com/ntamvl/4f93bbb7c9b4829c601104a2d2f91fe5')
#print('1')
#element = browser.find_element(by=By.ID, value='orderbook')
#print(element)
#print('1')
#element_1 = browser.find_element(by=By.ID, value='__APP')
#print(element_1)
#print('2')
#element_2 = element_1.find_element(by=By.CLASS_NAME, value='tablet')
#print(element_2)
#print('3')
#element_3 = element_2.find_element(by=By.CLASS_NAME, value='css-gdhyni')
#print(element_3)
#print('4')
#element_4 = browser.find_element(by=By.NAME, value='orderbook')
#print(element_4)
page_source = browser.page_source

#print(page_source)


soup = BeautifulSoup(page_source, 'lxml')
soup.find_all()
orderbook = soup.find_all('div', {"class": "orderbook-list-container"})
print('------------------', orderbook)
#browser.refresh()
#print('2')
#elements = browser.find_elements(by=By.TAG_NAME, value='div')
#print(len(elements))

#revealed = browser.find_element(by=By.TAG_NAME, value='div')
#errors = [NoSuchElementException, ElementNotInteractableException]
#wait = WebDriverWait(browser, timeout=500, poll_frequency=.2, ignored_exceptions=errors)
#wait.until(lambda d : revealed.send_keys("Displayed") or True)

#print('revealed ->', revealed)
#assert 'Yahoo' in browser.title
#browser.download_file('a.html', '/Users/mcarlos/Documents')



#elements = browser.find_elements(by=By.TAG_NAME, value='div')

#print(len(elements))

#for element in elements:
#    print(element.rect)

#print(elements)

#elem = browser.find_element(By.NAME, 'p')  # Find the search box
#print(elem.tag_name)
#elem.send_keys('seleniumhq' + Keys.RETURN)

browser.quit()
