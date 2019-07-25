# -*- coding: utf-8 -*-
"""
coder: 蒙安哲
date: 2019/3/22

网址:  受理  http://www.xuwen.gov.cn/Default.aspx?key=list/list&Id=1a8b4c2b-909b-426c-87bf-14240e564044&CurrentId=cb3cd21e-06ff-4380-81b4-2d7ff10e6b36&title=%E5%BB%BA%E8%AE%BE%E9%A1%B9%E7%9B%AE%E7%8E%AF%E5%A2%83%E5%BD%B1%E5%93%8D%E8%AF%84%E4%BB%B7%E4%BF%A1%E6%81%AF
备注:  徐闻县人民政府

"""

import scrapy
import json
import re
# from datetime import date
# from scrapy.utils.log import configure_logging
from hpspider.utils import right_item, problem_item, get_files, merge_table, format_table
from scrapy.selector import Selector


class HpSpider(scrapy.Spider):
    name = 'gd_zhanjiang_xuwenxian'  # 地名
    page = 28  # 由于页数随时可能出现变动，最好做全局变量以方便记忆
    url = 'http://www.xuwen.gov.cn/Ashx/PostHandler.ashx?action=News-GetPublishNewsList'  # 爬虫起始地址，翻页网站
    basic_info = {'province': 6,
                  'city': 93,
                  'source_webname': '徐闻县人民政府',
                  'sp_bm': '湛江市徐闻县环保局'}

    # file = "logs/%s%s.log" % (name, date.today().strftime("%Y_%m_%d"))
    # exceptions = set()

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     configure_logging(settings={'LOG_FILE': self.file, 'LOG_LEVEL': 'INFO'})

    def start_requests(self):
        for page in range(1, self.page + 1):
            formdata = {
                'args': json.dumps(
                    {"PageNo": str(page), "PageSize": '15', "ClassifyID": "cb3cd21e-06ff-4380-81b4-2d7ff10e6b36"}),
            }
            yield scrapy.FormRequest(url=self.url, formdata=formdata, callback=self.parse_url)

    def parse_url(self, response):
        json_dict = json.loads(response.text)
        json_data = json_dict['data']
        for data in json_data:
            formdata = {'args': json.dumps({"NewsID": data['NewsID']}), }
            if '受理' in data['Title']:
                yield scrapy.FormRequest(url='http://www.xuwen.gov.cn/Ashx/PostHandler.ashx?action='
                                             'News-GetPublishNewById&NewsID=' + data['NewsID'], formdata=formdata,
                                         callback=self.parse_url_sl)

    def parse_url_sl(self, response):
        json_dict = json.loads(response.text)
        json_data = json_dict.get('data')
        if json_data:
            web_page = json_data.get('NewsContent')
            if web_page:
                trs = Selector(text=web_page).xpath('//table//td[5]/..')
                if trs:
                    table = format_table(merge_table(trs))
                    is_same_td = len(table.xpath('//body/table/tr/td')) % len(table.xpath('//body/table/tr[1]/td')) == 0
                    if is_same_td:
                        test2 = ''.join(table.xpath('string(//tr[1]/td[2])').extract_first(default='').split())
                        test3 = ''.join(table.xpath('string(//tr[1]/td[3])').extract_first(default='').split())
                        test4 = ''.join(table.xpath('string(//tr[1]/td[4])').extract_first(default='').split())
                        test5 = ''.join(table.xpath('string(//tr[1]/td[5])').extract_first(default='').split())
                        is_test = ('项目' in test2 or '规划' in test2) and '建设单位' in test3 \
                                  and '建设地点' in test4 and ('环评' in test5 or '环境影响' in test5)
                        if is_test:
                            data_rows = table.xpath('//body/table/tr')
                            for i, data_row in enumerate(data_rows):
                                if i > 0:
                                    item = right_item(self.basic_info, response, gs_type='受理')
                                    item['date_time'] = ''.join(re.findall('\d{4}\D\d{1,2}\D\d{1,2}',
                                                                           json_data.get('LastUpdatedDate')))  # 发布时间
                                    item['project_name'] = data_row.xpath('string(./td[2])').extract_first(
                                        default='')  # 项目名称
                                    item['js_dw'] = data_row.xpath('string(./td[3])').extract_first(default='')  # 建设单位
                                    item['hp_dw'] = data_row.xpath('string(./td[5])').extract_first(default='')  # 环评单位
                                    item['site'] = data_row.xpath('string(./td[4])').extract_first(default='')  # 建设地点
                                    item['source_url'] = 'http://www.xuwen.gov.cn/Info.aspx?Id=' + \
                                                         ''.join(re.findall(r"&NewsID=(.*)", response.url)) + \
                                                         '&c=cb3cd21e-06ff-4380-81b4-2d7ff10e6b36'
                                    file_texts = data_row.xpath('.//a[contains(@href, "/")'
                                                                ' and not(contains(@href, "@"))]')
                                    if file_texts:
                                        msg, attachments = get_files(response, file_texts, 1)
                                    else:
                                        file_texts = Selector(text=web_page).xpath('//a[contains(@href, "/")'
                                                                                   ' and not(contains(@href, "@"))]')
                                        num = len(data_rows) - 1
                                        msg, attachments = get_files(response, file_texts, num)
                                    item['remark'] = json.dumps({"remark": None, "attachments": {"data": attachments,
                                                                                                 "msg": msg}},
                                                                ensure_ascii=False)
                                    yield item
                        else:
                            item = problem_item(self.basic_info, response, gs_type='受理',
                                                error_info='表格格式变化，无法提取')
                            item['problem_url'] = 'http://www.xuwen.gov.cn/Info.aspx?Id=' +\
                                                 ''.join(re.findall(r"&NewsID=(.*)", response.url)) +\
                                                 '&c=cb3cd21e-06ff-4380-81b4-2d7ff10e6b36'
                    else:
                        item = problem_item(self.basic_info, response, gs_type='受理',
                                            error_info='表格结构问题，无法提取')
                        item['problem_url'] = 'http://www.xuwen.gov.cn/Info.aspx?Id=' +\
                                             ''.join(re.findall(r"&NewsID=(.*)", response.url)) +\
                                             '&c=cb3cd21e-06ff-4380-81b4-2d7ff10e6b36'
                else:
                    item = problem_item(self.basic_info, response, gs_type='受理', error_info='网页格式不正确，无法提取')
                    item['problem_url'] = 'http://www.xuwen.gov.cn/Info.aspx?Id=' +\
                                         ''.join(re.findall(r"&NewsID=(.*?)", response.url)) +\
                                         '&c=cb3cd21e-06ff-4380-81b4-2d7ff10e6b36'
