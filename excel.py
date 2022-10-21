# -*- coding:utf-8 -*-
import pandas as pd
import re
import os
import time

filter_configration = {
    'read_file_path': r"",
    'read_file_name': "BDT-4SAR.xlsx",
    'date_column_name': '日期',
    'out_file_path': r"",
    'out_file_name': "out.xlsx",
    # 在这里写过滤列表,type需要按照年月日时分秒排列，年月日之间可以有\分割，时分秒之间可以有:分割，日和小时之间可以有空格
    'filter_date_list': [
        # 匹配列表内的年月日组合
        # {
        #     'filter_type': 'yMd',
        #     'filter_value': ['20200113']
        # },
        # 选择2000年或者2020-2021年的 1月1日或者1月8日-3月25日的数据
        # [
        #     {
        #         'filter_type': 'y',
        #         'filter_value': ['2000', '2010-2021']
        #     },
        #     {
        #         'filter_type': 'Md',
        #         'filter_value': ['0101', '0108-0325']
        #     }
        # ]
    ]
}
time_order = "yMdhms"
date_format_dict = {
    'y': '(19|20)[0-9]{2}',
    'M': '[0-2]?[0-9]',
    'd': '[0-3]?[0-9]',
    'h': '[0-2]?[0-9]',
    'm': '[0-6]?[0-9]',
    's': '[0-6]?[0-9]'
}


def transNum(num):
    if (len(num) == 1):
        return '0' + num
    return num


def check_filter_value(value, type):
    if isinstance(type, str) and isinstance(value, str):
        last_index = -1
        last_char = ''
        format_str = '^'
        for i in type:
            index = time_order.find(i)
            if index != -1:
                if index - last_index != 1 and last_index != -1:
                    print("ERROS: 不能确定时间范围的type，需要按年月日时分秒排列：", type)
                    return False
                else:
                    last_index = index
                    last_char = i
                    format_str = format_str + date_format_dict[i]
            elif i == ' ' and last_char == 'd':
                last_char = i
                format_str = format_str + i
                continue
            elif i == ':' and (last_char == 'h' or last_char == 'm'):
                last_char = i
                format_str = format_str + i
                continue
            elif i == '/' and (last_char == 'y' or last_char == 'M'):
                last_char = i
                format_str = format_str + i
                continue
            elif i == '-':
                continue
            else:
                print("ERROR: type含有不能识别的字符：", type)
                return False
        format_str = format_str + '$'
        if last_char == ' ' or last_char == ':' or last_char == '/':
            print("ERROR: type格式错误, 错误项：type: ", type, " value: ", value)
            return False
        else:
            for single_date in value.split('-'):
                if re.search(format_str, single_date) == None:
                    print("ERROR: type格式错误, 错误项：type: ", type, " value: ", value)
                    return False
        return True

    else:
        print("ERROR: 应该为string类型, 错误项：type: ", type, " value: ", value)
        return False


def check_filter_item(filter_item):
    if isinstance(filter_item, dict):
        if filter_item['filter_type']:
            if filter_item['filter_value']:
                if isinstance(filter_item['filter_value'], str):
                    return check_filter_value(filter_item['filter_value'], filter_item['filter_type'])
                elif isinstance(filter_item['filter_value'], list):
                    for filter_value_item in filter_item['filter_value']:
                        if check_filter_value(filter_value_item, filter_item['filter_type']):
                            continue
                        else:
                            return False
                else:
                    print("ERROR: 错误的filter_value类型, 错误项：", filter_item)
                    return False
            else:
                print("ERROR: 单个过滤时间项应该包含filter_value值, 错误项：", filter_item)
                return False
        else:
            print("ERROR: 单个过滤时间项应该包含filter_type值, 错误项：", filter_item)
            return False
    else:
        print("ERROR: 单个过滤时间项应该为dict格式， 错误项：", filter_item)
        return False
    return True


def check_filter_list(filter_list):
    if isinstance(filter_list, list):
        for filter_line in filter_list:
            if isinstance(filter_line, list):
                for filter_item in filter_line:
                    if check_filter_item(filter_item):
                        continue
                    else:
                        return False
            else:
                if check_filter_item(filter_line):
                    continue
                else:
                    return False
    else:
        print("ERROR: 过滤时间列表应该为list格式！")
        return False
    return True


def judge_num_list(left_list, right_list):
    for index, item in enumerate(left_list):
        left_item = int(item)
        right_item = int(right_list[index])
        if left_item > right_item:
            return 1
        elif left_item < right_item:
            return -1
        else:
            continue
    return 0


def check_daydata_with_single_date_item(day_data_filter_result_map, value, type):
    re_express = re.sub(r"(M|d|h|m|s)", lambda m: r"([\d]{1,2})", type)
    re_express = re.sub(r"y", lambda m: r"([\d]{1,4})", re_express)
    daydata_value_list = []
    if value.find('-') == -1:
        value_re_result = re.search(re_express, value)
        value_date_list = []
        i = 1
        for type_item in type:
            if "yMdhms".find(type_item) != -1:
                value_date_list.append(value_re_result.group(i))
                i = i + 1
                daydata_value_list.append(day_data_filter_result_map[type_item])
        return judge_num_list(value_date_list, daydata_value_list) == 0
    else:
        value_date_map = {
            'start': [],
            'end': []
        }
        for splite_index, splited_value in enumerate(value.split('-')):
            if splite_index == 0:
                splite_name = 'start'
            else:
                splite_name = 'end'
            value_re_result = re.search(re_express, splited_value)
            i = 1
            for type_item in type:
                if "yMdhms".find(type_item) != -1:
                    value_date_map[splite_name].append(value_re_result.group(i))
                    i = i + 1
                    daydata_value_list.append(day_data_filter_result_map[type_item])
            if splite_index == 0:
                if judge_num_list(value_date_map[splite_name], daydata_value_list) != 1:
                    continue
                else:
                    return False
            else:
                return judge_num_list(value_date_map[splite_name], daydata_value_list) != -1


def check_daydata_in_filter_item(day_data, filter_item):
    day_data_filter_express = r'^([\d]{1,2})/([\d]{1,2})/([\d]{1,4}) ([\d]{1,2}):([\d]{1,2}):([\d]{1,2})$'
    day_data_filter_result = re.search(day_data_filter_express, day_data)
    day_data_filter_result_map = {
        'y': day_data_filter_result.group(3),
        'M': transNum(day_data_filter_result.group(1)),
        'd': transNum(day_data_filter_result.group(2)),
        'h': transNum(day_data_filter_result.group(4)),
        'm': transNum(day_data_filter_result.group(5)),
        's': transNum(day_data_filter_result.group(6))
    }
    if isinstance(filter_item['filter_value'], str):
        return check_daydata_with_single_date_item(day_data_filter_result_map, filter_item['filter_value'],
                                                   filter_item['filter_type'])
    elif isinstance(filter_item['filter_value'], list):
        for value_item in filter_item['filter_value']:
            if check_daydata_with_single_date_item(day_data_filter_result_map, value_item, filter_item['filter_type']):
                return True
            else:
                continue
        return False


def check_daydata_by_filter_list(day_data, filter_lists):
    for filter_list in filter_lists:
        if isinstance(filter_list, list):
            for filter_item in filter_list:
                if check_daydata_in_filter_item(day_data, filter_item):
                    continue
                else:
                    return False
            return True
        else:
            if check_daydata_in_filter_item(day_data, filter_list):
                return True
            else:
                continue
    return False


def filter_by_configration(configration):
    if check_filter_list(configration['filter_date_list']):
        read_file_path = os.path.join(configration['read_file_path'], configration['read_file_name'])
        filteredData = pd.read_excel(read_file_path)
        outData = pd.DataFrame(columns=filteredData.columns)
        i = 0
        for index, row in filteredData.iterrows():
            if check_daydata_by_filter_list(row[filter_configration['date_column_name']],
                                            configration['filter_date_list']):
                outData.loc[i] = filteredData.iloc[index]
                i = i + 1
        print(outData)
        out_file_path = os.path.join(configration['out_file_path'], configration['out_file_name'])
        outData.to_excel(out_file_path, index=False)


def get_filter_item_by_file_path(file_path, filter_type):
    with open(file_path, 'r') as f:
        date_list = f.read().split('\n')

    return {
        'filter_type': filter_type,
        'filter_value': date_list
    }


if __name__ == "__main__":
    # print(get_filter_item_by_file_path('./date.txt', 'yMd'))
    filter_configration['filter_date_list'].append([get_filter_item_by_file_path('./date.txt', 'yMd')])
    start_time = time.time()
    filter_by_configration(filter_configration)
    print(f"分析完成，用时时间为{time.time() - start_time}秒")
