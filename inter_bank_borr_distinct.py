# -*- coding:utf8 -*-
# 本部分包含去重部分
import jieba
import pymysql
import re
import json
import datetime
import time
# 添加自定义字典
jieba.load_userdict(r'c:\users\zhengyu\desktop\userdict.txt')
stop_words_lists = ['出隔', '借隔', '出农信', '出线', '或出']
for stop_word in stop_words_lists:
    jieba.del_word(stop_word)
# 期限、数额统计字典
# re_com1 = re.compile(r'([\d.]+天|[\d.]+D|隔夜|[\d.]+M|[\d.]+月|[\d.]+个月)')  # 天/D
re_com2 = re.compile(r'([\d.]+W|[\d.]+KW|[\d.]+E|[\d.]+万|[\d.]+千万|[\d.]+亿|\d{3,4})')  # 万、千万、亿  切割金额
re_com3 = re.compile(r'([\d.]+天|[\d.]+D|隔夜|[\d.]+M|[\d.]+月|[\d.]+个月|\d{1,2})$')  # 切割天数
re_com4 = re.compile(r'(\d\.\d{1,4}%*)')  # 利率
days_dict = {}

# 按照关键字切割文本函数
def func_str_cut(ss_list):
    cutting_lists, cutting_list = list(), list()
    for ss in ss_list:
        if ss in ['借', '诚借', '出']:
            cutting_lists.append(tuple(cutting_list))
            cutting_list = list()
            cutting_list.append(ss)
        else:
            cutting_list.append(ss)
    cutting_lists.append(tuple(cutting_list))
    return list(set(cutting_lists[1:]))

# 摘出断句后最小tuple的方向、期限、量、价格、备注 main_1
def func_finl_cut(cut_tup):
    ans_list = []
    ans_dict = dict(Tr_dir=cut_tup[0], 期限=[], 金额=[], 利率=[])
    last_one = 's'  # 当前一条上一条为期限、金额、或价格的标记 s 初始状态， d 期限， m金额, p为价格
    loc = 1  # 起始位置为1，0为方向坐标
    # unknown_list = []   # 未知数的坐标
    days_list = []  # 期限的坐标
    money_list = []  # 金额的坐标
    price_list = []  # 价格的坐标
    oth_list = []  # 其他标签坐标
    for key_word in cut_tup[1:]:

        # 判定当前词的类型
        if re_com3.match(key_word):  # 期限
            this_one = 'd'
            if this_one != last_one:  # 词性变化
                if last_one == 's':  # 且上一条是其他类型标签或者第一个词
                    days_list.append(loc)
                else:                  # 上一条不是其他类型标签或第一个词
                    if last_one == 'm':
                        if not ans_dict['金额']:
                            ans_dict['金额'] = money_list
                            money_list = []
                            days_list.append(loc)
                        else:
                            ans_list.append(ans_dict)
                            ans_dict = dict(Tr_dir=cut_tup[0], 期限=[], 金额=[], 利率=[])
                            ans_dict['金额'] = money_list
                            # money_list = []
                            days_list = []
                            price_list = []
                            days_list.append(loc)
                    elif last_one == 'p':
                        if not ans_dict['利率']:
                            ans_dict['利率'] = price_list
                            price_list = []
                            days_list.append(loc)
                        else:
                            ans_list.append(ans_dict)
                            ans_dict = dict(Tr_dir=cut_tup[0], 期限=[], 金额=[], 利率=[])
                            ans_dict['利率'] = price_list
                            money_list = []
                            days_list = []
                            # price_list = []
                            days_list.append(loc)
            else:
                days_list.append(loc)

        elif re_com2.match(key_word):  # 金额
            this_one = 'm'
            if this_one != last_one:
                if last_one == 's':
                    money_list.append(loc)
                else:
                    if last_one == 'd':
                        if not ans_dict['期限']:
                            ans_dict['期限'] = days_list
                            days_list = []
                            money_list.append(loc)
                        else:
                            ans_list.append(ans_dict)
                            ans_dict = dict(Tr_dir=cut_tup[0], 期限=[], 金额=[], 利率=[])
                            ans_dict['期限'] = days_list
                            money_list = []
                            # days_list = []
                            price_list = []
                            money_list.append(loc)
                    elif last_one == 'p':
                        if not ans_dict['利率']:
                            ans_dict['利率'] = price_list
                            price_list = []
                            money_list.append(loc)
                        else:
                            ans_list.append(ans_dict)
                            ans_dict = dict(Tr_dir=cut_tup[0], 期限=[], 金额=[], 利率=[])
                            ans_dict['利率'] = price_list
                            money_list = []
                            days_list = []
                            # price_list = []
                            money_list.append(loc)
            else:
                money_list.append(loc)

        elif re_com4.match(key_word):  # 利率
            this_one = 'p'
            if this_one != last_one:
                if last_one == 's':
                    price_list.append(loc)
                else:
                    if last_one == 'd':
                        if not ans_dict['期限']:
                            ans_dict['期限'] = days_list
                            days_list = []
                            price_list.append(loc)
                        else:
                            ans_list.append(ans_dict)
                            ans_dict = dict(Tr_dir=cut_tup[0], 期限=[], 金额=[], 利率=[])
                            ans_dict['期限'] = days_list
                            money_list = []
                            # days_list = []
                            price_list = []
                            price_list.append(loc)
                    elif last_one == 'm':
                        if not ans_dict['金额']:
                            ans_dict['金额'] = money_list
                            money_list = []
                            price_list.append(loc)
                        else:
                            ans_list.append(ans_dict)
                            ans_dict = dict(Tr_dir=cut_tup[0], 期限=[], 金额=[], 利率=[])
                            ans_dict['金额'] = money_list
                            # money_list = []
                            days_list = []
                            price_list = []
                            price_list.append(loc)
            else:
                price_list.append(loc)

        else:                           # 其他标签
            this_one = 'o'
            oth_list.append(loc)  # 保证当前词类型只会有d\m\p\o四种

        last_one = this_one if this_one != 'o' else last_one  # 传递分类
        loc += 1
    # print(ans_dict)
    #  最后一组
    ans_dict['期限'] = days_list if len(days_list) > len(ans_dict['期限']) else ans_dict['期限']
    ans_dict['金额'] = money_list if len(money_list) > len(ans_dict['金额']) else ans_dict['金额']
    ans_dict['利率'] = price_list if len(price_list) > len(ans_dict['利率']) else ans_dict['利率']

    ans_list.append(ans_dict)
    for d in ans_list:
        for k, v in d.items():
            if not v:
                continue
            else:
                if k == 'Tr_dir':
                    continue
                elif k in ('期限', '金额'):
                    if len(v) == 1:
                        d[k] = [cut_tup[v[0]]]
                    else:
                        d[k] = cut_tup[v[0]: v[-1]+1]
                elif k == '利率':
                    d[k] = [cut_tup[v[0]]]
        d['备注'] = [cut_tup[a] for a in oth_list]
    return ans_list

# 截取期限之间的分割位
def gap_str(s, l):  # 第一个参数为str, 第二个参数为list
    # start_loc = 0
    len_end_str = len(l[-1])
    end_loc = s.find(l[-1])
    return s[0: end_loc+len_end_str].replace(l[0], '').replace(l[-1], '')

# 处理日期label
def format_str(sw):
    m = 0
    new_sw = ''
    for w in sw:
        new_sw += w
        if m > 0:
            try:
                next_w = sw[m+1]
            except:
                next_w = ''
            if w in ['D', 'M'] and next_w in map(str, range(1, 10)):
                new_sw += '、'
            else:
                pass
        m += 1
    return new_sw

# 处理标签
def func_i(i):
    l = []
    if '利率' in i or '押券宽松' in i or '随意押' in i:
        l.append('押利率')
    if '信用' in i or '押券宽松' in i or '随意押' in i:
        l.append('押信用')
    if 'AAA' in i or '3A' in i:
        l.append('押AAA')
    if 'AA+' in i or '2A+' in i:
        l.append('押AA+')
    if ('AA' in i or '2A' in i) and 'AAA' not in i and '2A+' not in i and 'AA+' not in i:
        l.append('押AA')
    if '中债' in i:
        l.append('中债')
    if '上清' in i:
        l.append('上清')
    if '存单' in i or 'CD' in i or 'cd' in i:
        l.append('押存单')
    if '银行' in i or '银信' in i:
        l.append('限银行')
    if '农信' in i or '银信' in i:
        l.append('限农信')
    if '早还款' in i or '还款早' in i or'上午还款' in i or'开门还款' in i or '早回款' in i or '早还' in i:
        l.append('早还款')
    if '大量' in i or '量大' in i:
        l.append('大量')
    return ','.join(l)

# 处理日期文本返回json   main_2
def tags_qx(term_str):
    re_com = re.compile(r'([\d.]+天|[\d.]+D|隔夜|[\d.]+M|[\d.]+月|[\d.]+个月|\d{1,2})')
    term_str = term_str.replace('日', 'D').replace('天', 'D').replace('个月', 'M').replace('月', 'M').replace('隔夜', '1D')
    term_list = re_com.findall(term_str)  # 将周期切割成list
    if len(term_list) == 0:
        return None
    if len(term_str) == len(''.join(term_list)):   # 无分割位 默认表或的关系
        label_show = '、'.join(term_list)
        try:
            detail_data = [{'desc': 'P', 'data': term[0:len(term)-1] if term[-1] != 'M'
            else str(int(term[0:len(term)-1]) * 31), 'unit': 'D'} for term in term_list]
        except:
            return None
        return json.dumps({'label': label_show, 'detail_data': detail_data}, ensure_ascii=False)
    else:  # 有分割位
        term_loc = 0
        cut_term_lists = []
        while term_loc < len(term_list)-1:
            cut_term_lists.append([term_list[term_loc], term_list[term_loc+1]])
            term_loc += 1
        # return cut_term_lists

        loc = 0
        detail_data_r = []
        for cut_term_list in cut_term_lists:
            unit_1 = cut_term_list[0][-1]  # 第1个日期的单位
            unit_2 = cut_term_list[1][-1]  # 第2个日期的单位
            sub_str = term_str[loc:]
            loc = term_str.find(cut_term_list[-1])
            r = gap_str(sub_str, cut_term_list)  # 分割位字符
            try:
                if unit_1 in map(str, list(range(0, 10))) and unit_2 in map(str, list(range(0, 10))):  # 无单位
                    continue

                elif unit_1 in map(str, list(range(0, 10))) and unit_2 == 'D':                          # 无，D
                    if re.compile(r'([-|~|至|—|到|―|－|～])').search(r):  # 属于区间
                        detail_data_r.append({'desc': 'R',
                                              'begin': cut_term_list[0],
                                              'end': cut_term_list[1][0:len(cut_term_list[1])-1],
                                              'unit': 'D'})
                    else:  # 属于 点
                        detail_data_r.append({'desc': 'P',
                                              'data': cut_term_list[0],
                                              'unit': 'D'})
                        detail_data_r.append({'desc': 'P',
                                              'data': cut_term_list[1][0:len(cut_term_list[1])-1],
                                              'unit': 'D'})

                elif unit_1 in map(str, list(range(0, 10))) and unit_2 == 'M':                          # 无，M

                    if re.compile(r'([-|~|至|—|到|―|－|～])').search(r):                                     # 属于区间
                        detail_data_r.append({'desc': 'R',
                                              'begin': str(int(cut_term_list[0]) * 31),
                                              'end': str(int(cut_term_list[1][0:len(cut_term_list[1]) - 1]) * 31),
                                              'unit': 'D'})

                    else:                                                                                   # 属于 点
                        detail_data_r.append({'desc': 'P',
                                              'data': str(int(cut_term_list[0]) * 31),
                                              'unit': 'D'})
                        detail_data_r.append({'desc': 'P',
                                              'data': str(int(cut_term_list[1][0:len(cut_term_list[1])-1]) * 31),
                                              'unit': 'D'})

                elif unit_1 == 'D' and unit_2 in map(str, list(range(0, 10))):                         # D，无
                    detail_data_r.append({'desc': 'P',
                                          'data': cut_term_list[0][0:len(cut_term_list[0])-1],
                                          'unit': 'D'})

                elif unit_1 == 'D' and unit_2 == 'D':                                                    # D，D
                    if re.compile(r'([-|~|至|—|到|―|－|～])').search(r):                                    # 属于区间
                        detail_data_r.append({'desc': 'R',
                                              'begin': cut_term_list[0][0:len(cut_term_list[0])-1],
                                              'end': cut_term_list[1][0:len(cut_term_list[1])-1],
                                              'unit': 'D'})
                    else:
                        detail_data_r.append({'desc': 'P',
                                              'data': cut_term_list[0][0:len(cut_term_list[0]) - 1],
                                              'unit': 'D'})

                        detail_data_r.append({'desc': 'P',
                                              'data': cut_term_list[1][0:len(cut_term_list[1]) - 1],
                                              'unit': 'D'})

                elif unit_1 == 'D' and unit_2 == 'M':                                                   # D，M
                    if re.compile(r'([-|~|至|—|到|―|－|～])').search(r):                                    # 属于区间
                        detail_data_r.append({'desc': 'R',
                                              'begin': cut_term_list[0][0:len(cut_term_list[0])-1],
                                              'end': str(int(cut_term_list[1][0:len(cut_term_list[1])-1]) * 31),
                                              'unit': 'D'})
                    else:
                        detail_data_r.append({'desc': 'P',
                                              'data': cut_term_list[0][0:len(cut_term_list[0]) - 1],
                                              'unit': 'D'})

                        detail_data_r.append({'desc': 'P',
                                              'data': str(int(cut_term_list[1][0:len(cut_term_list[1]) - 1]) * 31),
                                              'unit': 'D'})

                elif unit_1 == 'M' and unit_2 in map(str, list(range(0, 10))):                   # M、无
                    detail_data_r.append({'desc': 'P',
                                          'data': str(int(cut_term_list[0][0:len(cut_term_list[0]) - 1]) * 31),
                                          'unit': 'D'})

                elif unit_1 == 'M' and unit_2 == 'D':                                            # M、D
                    detail_data_r.append({'desc': 'P',
                                          'data': str(int(cut_term_list[0][0:len(cut_term_list[0]) - 1]) * 31),
                                          'unit': 'D'})
                    detail_data_r.append({'desc': 'P',
                                          'data': cut_term_list[1][0:len(cut_term_list[1]) - 1],
                                          'unit': 'D'})

                elif unit_1 == 'M' and unit_2 == 'M':                                                   # M、M
                    if re.compile(r'([-|~|至|—|到|―|－|～])').search(r):                                    # 属于区间
                        detail_data_r.append({'desc': 'R',
                                              'begin': str(int(cut_term_list[0][0:len(cut_term_list[0])-1]) * 31),
                                              'end': str(int(cut_term_list[1][0:len(cut_term_list[1])-1]) * 31),
                                              'unit': 'D'})
                    else:
                        detail_data_r.append({'desc': 'P',
                                              'data': str(int(cut_term_list[0][0:len(cut_term_list[0]) - 1]) * 31),
                                              'unit': 'D'})

                        detail_data_r.append({'desc': 'P',
                                              'data': str(int(cut_term_list[1][0:len(cut_term_list[1]) - 1]) * 31),
                                              'unit': 'D'})

                for dic in detail_data_r:
                    if dic['desc'] == 'R' and (int(dic['begin']) >= int(dic['end'])   # 如果开始起始大于等于截止或者仅有0则pass
                                               or re.compile(r'^0+$').match(dic['begin'])
                                               or re.compile(r'^0+$').match(dic['end'])
                                               or int(dic['begin']) > 365
                                               or int(dic['end']) > 365
                                               ):
                        return None
                    if dic['desc'] == 'P' and (re.compile(r'^0+$').match(dic['data']) or int(dic['data']) >= 365):  # 只有0则pass
                        return None
            except:
                return None
        return json.dumps({'label': format_str(term_str), 'detail_data': [eval(v) for v in set([str(k) for k in detail_data_r])]}, ensure_ascii=False)  # 去重

# 处理资金额度返回json  main_3
def tags_je(money_strs):
    re_com2 = re.compile(r'([\d.]+W|[\d.]+KW|[\d.]+E|[\d.]+万|[\d.]+千万|[\d.]+亿|[1-9]{1}\d{2,3})')
    money_strs = money_strs.replace('千万', 'KW').replace('万', 'W').replace('亿', 'E').replace('元', '')
    # 统一量级单位
    money_list = re_com2.findall(money_strs)
    money_list_new = []
    try:
        for money in money_list:
            if 'KW' in money:
                money_num = money.replace('KW', '')
                money_list_new.append(round(eval(money_num), 4))
            elif 'W' in money:
                money_num = money.replace('W', '')
                money_list_new.append(round(eval(money_num) / 1000, 4))
            elif 'E' in money:
                money_num = money.replace('E', '')
                money_list_new.append(round(eval(money_num) * 10, 4))
            else:
                if eval(money) <= 50:
                    money_list_new.append(round(eval(money) * 10, 4))
                else:
                    money_list_new.append(round(eval(money) / 1000, 4))
        # 按列表构成个数分情况处理
        if len(money_list_new) == 0:
            return None
        elif len(money_list_new) == 1:
            return json.dumps(
                {'label': money_strs, 'detail_data': [{'desc': 'P', 'data': str(money_list_new[0]), 'unit': 'KW'}]},
                ensure_ascii=False)
        elif len(money_list_new) == 2:
            r_1 = money_strs.replace(money_list[0], '').replace(money_list[-1], '')  # 分隔符
            if re.compile(r'([-|~|至|—|到|―|－|～])').search(r_1):  # 表区间
                return json.dumps(
                    {"label": money_strs, "detail_data": [{"desc": "R", "begin": str(sorted(money_list_new)[0]),
                                                           "end": str(sorted(money_list_new)[-1]), "unit": "KW"}]},
                    ensure_ascii=False)
            elif re.compile(r'([+|＋|加])').search(r_1):  # 表加法
                return json.dumps(
                    {"label": money_strs, "detail_data": [{"desc": "R", "begin": str(sorted(money_list_new)[0]),
                                                           "end": str(round(sum(money_list_new), 4)), "unit": "KW"}]},
                    ensure_ascii=False)
            elif r_1 == '' or r_1 == '或' or r_1 == '、' or r_1 == '及':  # 表或关系
                return json.dumps(
                    {"label": money_strs, "detail_data": [{"desc": "P", "data": str(money_list_new[0]), "unit": "KW"},
                                                          {"desc": "P", "data": str(money_list_new[-1]),
                                                           "unit": "KW"}]},
                    ensure_ascii=False)
            else:
                return None
        else:  # 大于2多个数值 表加法
            count_plus = money_strs.replace('＋', '+').replace('加', '+').count('+')
            if count_plus + 1 == len(money_list_new):
                return json.dumps(
                    {"label": money_strs, "detail_data": [{"desc": 'R', "begin": str(sorted(money_list_new)[0]),
                                                           "end": str(round(sum(money_list_new), 4)), "unit": "KW"}]},
                    ensure_ascii=False)
            else:
                return None
    except:
        return None

hour_start = int(input(r'请输入抓取时间起始( 如：早上7点为7，下午1点为13 )：'))
hour_end = int(input(r'请输入抓取时间截止( 如：早上7点为7，下午1点为13 )：'))
freq = int(input(r'请输入抓取频率( 如：5秒一次为5，建议频率大于5为宜 )：'))

while True:
    local_time_hour = time.localtime(time.time())[3]
    if local_time_hour in range(hour_start, hour_end):
        conv_dict = {'１': 1, '２': 2, '３': 3, '４': 4, '５': 5, '６': 6, '７': 7, '８': 8, '９': 9,  '０': 0, 'Ｄ': 'D',
                     'Ｍ': 'M', 'Ａ': 'A', 'Ｅ': 'E', 'Ｗ': 'W', 'Ｋ': 'K', '一': 1, '二': 2, '两': 2, '俩': 2, '三': 3,
                     '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '：': ':'}

        conn = pymysql.connect(host='10.10.128.116', user='root', password='111111', database='pdb', charset='utf8')
        cursor = conn.cursor()
        sqls = r'''
select FT,F3,F2,F5,F4 from (
    SELECT Ft,F3,F2,F5,F4,
    if(@cont=stat_tmp.F5 and @qq = stat_tmp.F3,@rank:=@rank+1,@rank:=1) as rank,
    @cont:=stat_tmp.F5,
		@qq := stat_tmp.F3
    from (
				select Ft,F3,F2,F5,cast(cast(F4 as datetime) as UNSIGNED) as F4 from q_talk s
        where (F5 like '出%' or F5 like '借%' or F5 like '诚借%')
        and (F5 not like '出存单%' and F5 not like '出同业存单%' and F5 not like '出同存%' and F5 not like '出债%'
        and F5 not like '出券%' and F5 not like '出卷%')
        and F5 not like '%.IB%'
        and F5 not like '%理财%'
        and F5 NOT REGEXP '[0-9]{5,}'
        and CAST(F4 as date) = cast(SYSDATE() as date) # 增量处理
        and Ft not in (select distinct F1 from P12091 t 
where cast(t.F12 as date) = cast(SYSDATE() as date))
				order by F5,F3 asc, FT desc
    ) stat_tmp ,(select @cont:= null, @qq := null ,@rank:=0) a
    )result where result.rank = 1 
        '''
        cursor.execute(sqls)
        data = cursor.fetchall()
        dict_data = {i[0:3]: i[3:] for i in data}  # Ft为key

        for i, j in dict_data.items():
            # print(i, j)
            cnt_str = j[0].strip().replace('　', '').replace(' ', '').replace(',', '').replace('，', '').upper()
            for conv_k in conv_dict.keys():  # 全半角转换
                cnt_str = cnt_str.replace(conv_k, str(conv_dict[conv_k]))
            cnt = cnt_str.split('\n')  # 换行
            cnt_list = list(set([w.strip() for w in cnt if re.match(r'(借|诚借|出).+', w)]))  # 分行剔除杂项并去重
            for ww in cnt_list:
                func_jb_cut_list = func_str_cut(list(jieba.cut(ww)))   # 单一断句的tuple构成的list
                for sss in func_jb_cut_list:
                    # print(i, ww, '      ', sss, func_finl_cut(sss))
                    F1 = i[0]  # 原始记录ID
                    F2 = i[1]  # qq、邮箱
                    F3 = re.sub(r'【.*】', '', i[2])  # 称呼
                    F12 = str(j[-1])  # qq准确发言时间
                    F11 = ''.join(sss)  # 原文、行
                    cursor.execute(r'''select F11,cast(F12 as char) as F12 from P12091 w
                                                        where cast(F12 as date) = cast(SYSDATE() as date)
                                                        order by F11 asc, cast(F12 as datetime) asc ''')  # 获取当日已经存在的数据,注意排序方式保证下面生成字典仅保留原文相同情况下最大的时间戳
                    data_exists = cursor.fetchall()  # P12091已经存在的数据
                    data_exists_d = {k: v for k, v in data_exists}  # 处理成为字典，原文相同，时间最大
                    if F11 in data_exists_d.keys():  # 时间差在120秒以内
                        date_time_delta = sorted([datetime.datetime.strptime(data_exists_d[F11], '%Y%m%d%H%M%S'),
                                                  datetime.datetime.strptime(F12, '%Y%m%d%H%M%S')])
                        if (date_time_delta[-1] - date_time_delta[0]).seconds <= 120:
                            continue
                    for d in func_finl_cut(sss):
                        F4 = d['Tr_dir']  # 交易方向
                        F5 = re.sub(r'\d{1,2}:\d{1,2}', '', ''.join(d['期限']))  # 期限文本
                        F6 = tags_qx(F5)  # 期限json
                        F7 = ''.join(d['金额'])  # 金额文本
                        F8 = tags_je(F7)  # 金额json
                        try:
                            F9 = ''.join(d['利率']) if ''.join(d['利率'])[-1] == '%' else ''  # 利率
                        except:
                            F9 = ''
                        F10 = func_i(''.join(sss))
                        print(F1,  '---------', 'F4:', F4, 'F5:', F5, 'F6:', F6, 'F7:', F7, 'F8:', F8, 'F9:', F9,
                              'F10:', F10, 'F11:', F11)
                        if (F5 != '' and F6 is None) or (F7 != '' and F8 is None) :
                            FS = 0
                        elif (F6 is not None and ('[]' in F6 or '""' in F6)) \
                                or (F8 is not None and ('[]' in F8 or '""' in F8)):
                            FS = 0
                        else:
                            FS = 1
                        cursor.execute(r'''
        insert into pdb.P12091 values(UNIX_TIMESTAMP(CURRENT_TIMESTAMP)<<32 | RIGHT(UUID_SHORT(),8),
        UNIX_TIMESTAMP(CURRENT_TIMESTAMP)<<32 | RIGHT(UUID_SHORT(),8),%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,null,null,%s,%s)''',
                                       [F1, F2, F3, F12, F4, F5, F6, F7, F8, F9, F10, F11, FS,
                                        datetime.datetime.now().strftime('%Y%m%d%H%M%S'),
                                        datetime.datetime.now().strftime('%Y%m%d%H%M%S')])
                        conn.commit()
        cursor.close()
        conn.close()
        time.sleep(freq)
    else:
        time.sleep(300)
        continue