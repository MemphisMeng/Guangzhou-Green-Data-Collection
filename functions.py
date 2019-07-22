# -*- coding: utf-8 -*-

import re
import hashlib
import time
import datetime
import json


def md5(name):
    name = name.strip()  # 计算企业名称md5值之前去掉企业名称的空格
    return hashlib.md5(name).hexdigest()


def clean(i):
    if i:
        # return i.replace(' ', '').replace('\n', '').replace('\r', '').replace('\t', '')
        return re.sub('\s', '', i)
    else:
        return i


def timestamp(date_str):
    if not date_str:
        return date_str
    date_str = date_str.strip()
    if date_str.isdigit():
        if len(date_str) == 8:
            tl = [date_str[0:4], date_str[4:6], date_str[6:8]]
        else:
            tl = []
    else:
        tl = re.findall(r'\d+', date_str)
    if len(tl) < 3:
        return None
    else:
        tl = tl[:3]
    ts = '-'.join(tl)
    try:
        date_time = int(time.mktime(time.strptime(ts, "%Y-%m-%d")))
    except:
        date_time = None
    return date_time


def hp_type_f(hp_type):
    # 报告书 报告表 登记表 未知
    if not hp_type:
        return hp_type
    if '报告书' in hp_type:
        return '报告书'
    elif '报告表' in hp_type:
        return '报告表'
    elif '登记表' in hp_type:
        return '登记表'
    else:
        return None


def js_dw_hp_dw(s):
    ss = clean(s)
    if not ss:
        return ss
    if len(ss) < 4:
        return None
    else:
        return ss


def re_project_name(pname):
    if not pname:
        return pname
    # 第一把书名号去掉，在针对'项目'、‘工程’、‘环境影响’、‘环评’、‘批复’
    pn0 = clean(pname)
    pn1 = pn0.replace('《', '').replace('》', '')
    pn2 = re.sub('(.*关于对)', '', pn1)
    pn2 = re.sub('(.*关于)', '', pn2)
    if '项目' in pn2:
        tpn = re.search('(.*?项目)', pn2).group(1)
    elif '工程' in pn2:
        tpn = re.search('(.*?工程)', pn2).group(1)
    elif '环评' in pn2:
        tpn = re.search('(.*?)环评', pn2).group(1)
    elif '批复' in pn2:
        tpn = re.search('(.*?)批复', pn2).group(1)
    else:
        tpn = pn2

    pn3 = re.sub('(环境影响.*)', '', tpn)
    pn = re.sub('(\..[a-zA-Z]+)', '', pn3)    # 替换后缀

    return pn


def trip_item(item):
    keys = ['project_name', 'gs_type', 'date_time', 'province', 'city', 'remark', 'status',
            'source_url', 'sp_bm', 'sp_dh', 'hp_type', 'js_dw', 'hp_dw', 'site', 'xm_gk',
            'yx_cs', 'gc_qk', 'bg_url', 'gc_url', 'pf_url', 'pf_content', 'pf_num', 'pf_time',
            'non_sp', 'source_webname', 'problem_url', 'error_info'
            ]

    p_item = {}.fromkeys(keys, None)
    p_item.update(item)
    project_name = re_project_name(p_item['project_name'])  # 关于  环境影响 书名号去掉
    date_time = timestamp(p_item['date_time'])
    sp_bm = clean(p_item['sp_bm'])  # 审批部门
    hp_type = hp_type_f(p_item['hp_type'])  # 环评文件类型 报告书 报告表 登记表 未知
    js_dw = js_dw_hp_dw(p_item['js_dw'])  # 建设单位
    hp_dw = js_dw_hp_dw(p_item['hp_dw'])  # 环评单位
    site = clean(p_item['site'])  # 建设地点
    pf_num = clean(p_item['pf_num'])  # 环评批复文号
    pf_time = timestamp(p_item['pf_time'])  # 环评批复时间
    p_item['project_name'] = project_name
    p_item['date_time'] = date_time
    p_item['sp_bm'] = sp_bm
    p_item['hp_type'] = hp_type
    p_item['js_dw'] = js_dw
    p_item['hp_dw'] = hp_dw
    p_item['site'] = site
    p_item['pf_num'] = pf_num
    p_item['pf_time'] = pf_time

    return p_item


def get_urls(item):
    data = item['data']
    data = json.loads(data)
    urls = []
    if data['bg_url']:
        urls.append(data['bg_url'])
    if data['gc_url']:
        urls.append(data['gc_url'])
    if data['pf_url']:
        urls.append(data['pf_url'])
    return urls

if __name__ == "__main__":
    t = {
            'project_name': '　　关于对广东万和电气有限公司新能源集成热水产品生2.5产基地扩产建设项目环境影响评价.pdf',
            'date_time': '2018年07月20日',
            'sp_bm': ' 绿 网 ', 'hp_type': 'xxx报告书',
            'js_dw': ' jian she 单位', 'hp_dw': 'h品单位',
            'pf_time': '20180720',
    }
    tt = trip_item(t)
    for k, v in tt.items():
        if v:
            print('%s: %s' % (k, str(v)))

