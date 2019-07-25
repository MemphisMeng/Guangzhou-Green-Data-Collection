"""
coder: Anzhe Memphis Meng
date: 2019/3/16

网址:  受理/拟审批/批复  http://www.chaozhou.gov.cn/jsxmhjyxpjxx/index_1.jhtml
备注:  潮州市政府网站  根据历史爬虫数据设置抓取时间
"""

# -*- coding: utf-8 -*-
import scrapy
import json
# from datetime import date
# from scrapy.utils.log import configure_logging
from hpspider.utils import right_item, problem_item, get_files


class ChaozhouSpider(scrapy.Spider):
    name = 'gd_chaozhou'
    page = 21    # 由于页数随时可能出现变动，最好做全局变量以方便记忆

    # 作用范围
    allowed_domains = ["chaozhou.gov.cn"]

    url = 'http://www.chaozhou.gov.cn/jsxmhjyxpjxx/index_{page}.jhtml'

    basic_info = {'province': 6,
                  'city': 78,
                  'source_webname': '中国潮州政府网站',
                  'sp_bm': '潮州市生态环境局'}

    # file = "logs/%s%s.log" % (name, date.today().strftime("%Y_%m_%d"))
    # exceptions = set()

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     configure_logging(settings={'LOG_FILE': self.file, 'LOG_LEVEL': 'INFO'})

    def start_requests(self):
        for page in range(1, self.page + 1):
            yield scrapy.Request(url=self.url.format(page=page), callback=self.parse_url)

    def parse_url(self, response):
        links = response.xpath('//div[contains(@class, "guifanxing")]//ul//a')

        for link in links:
            title = link.xpath('string(.)').extract_first(default='')
            url = link.xpath('./@href').extract_first(default='')
            full_url = response.urljoin(url)
            if '受理' in title and ('环境影响' in title or '环评' in title):
                yield scrapy.Request(url=full_url, callback=self.parse_url_sl)
            elif '审批' in title and ('环境影响' or '环评') in title and '审批后' not in title:
                yield scrapy.Request(url=full_url, callback=self.parse_url_nsp)
            elif ('批复' in title or '审批后' in title) and ('环境影响' or '环评') in title:
                yield scrapy.Request(url=full_url, callback=self.parse_url_pf)

    def parse_url_sl(self, response):

        tr_num = len(response.xpath('//span[@id="zoom"]//tr/td'))
        td_num = len(response.xpath('//span[@id="zoom"]//tr[1]/td'))

        if tr_num % td_num == 0:
            title_list = response.xpath('//span[@id="zoom"]/table//tr[1]')
            test1 = title_list.xpath('./td[2]').xpath('string(.)').extract_first(default='')
            test2 = title_list.xpath('./td[3]').xpath('string(.)').extract_first(default='')
            test3 = title_list.xpath('./td[4]').xpath('string(.)').extract_first(default='')
            test4 = title_list.xpath('./td[5]').xpath('string(.)').extract_first(default='')
            test5 = title_list.xpath('./td[6]').xpath('string(.)').extract_first(default='').replace(' ', '')
            is_test = ('项目' in test1 or '规划' in test1) and '建设单位' in test2 \
                    and '建设地点' in test3 and '环评单位' in test4 and ('环评' in test5 or '环境影响' in test5)
            if is_test:
                data_rows = response.xpath('//span[@id="zoom"]/table//td[7]/..')
                for i, data_row in enumerate(data_rows):
                    if i > 0:
                        item = right_item(self.basic_info, response, gs_type='受理')
                        item['date_time'] = response.xpath('string(//*[@class="xm-content-date"])').\
                            re_first('\d{4}\D\d{1,2}\D\d{1,2}')  # 发布时间
                        item['project_name'] = data_row.xpath('string(./td[2])').extract_first(default='')  # 项目名称
                        item['js_dw'] = data_row.xpath('string(./td[3])').extract_first(default='')  # 建设单位
                        item['hp_dw'] = data_row.xpath('string(./td[5])').extract_first(default='')  # 环评单位
                        item['site'] = data_row.xpath('string(./td[4])').extract_first(default='')  # 建设地点
                        file_texts = data_row.xpath('.//a[contains(@href, "/") and not(contains(@href, "@"))]')
                        if file_texts:
                            msg, attachments = get_files(response, file_texts, 1)
                        else:
                            file_texts = response.xpath('//*[@id="zoom"]/../..//a[contains(@href, "/") and \
                            not(contains(@href, "@"))]')
                            num = len(data_rows) - 1
                            msg, attachments = get_files(response, file_texts, num)
                        item['remark'] = json.dumps({"remark": None, "attachments": {"data": attachments,
                                                    "msg": msg}}, ensure_ascii=False)
                        yield item
            else:
                yield problem_item(self.basic_info, response, gs_type='受理', error_info='表格格式变化，无法提取')
        else:
            yield problem_item(self.basic_info, response, gs_type='受理', error_info='网页格式不正确，无法提取')

    def parse_url_nsp(self, response):
        tr_num = len(response.xpath('//span[@id="zoom"]/table//tr'))
        td_num = len(response.xpath('//span[@id="zoom"]/table//tr/td'))
        test1 = response.xpath('//span[@id="zoom"]/table//tr[@class="firstRow"]/td[1]').xpath('string(.)').\
            extract_first(default='')
        test2 = response.xpath('//span[@id="zoom"]/table//tr[2]/td[1]').xpath('string(.)').\
            extract_first(default='')
        test3 = response.xpath('//span[@id="zoom"]/table//tr[3]/td[1]').xpath('string(.)').\
            extract_first(default='')
        test4 = response.xpath('//span[@id="zoom"]/table//tr[4]/td[1]').xpath('string(.)'). \
            extract_first(default='')
        test5 = response.xpath('//span[@id="zoom"]/table//tr[5]/td[1]').xpath('string(.)'). \
            extract_first(default='')
        test6 = response.xpath('//span[@id="zoom"]/table//tr[6]/td[1]').xpath('string(.)'). \
            extract_first(default='')

        if td_num % tr_num == 0:
            is_test = '项目名称' in test1 and '建设单位' in test2 and '建设地点' in test3 and '环评机构' in test4 \
                    and '概况' in test5 and ('环境影响' in test6 or '环评' in test6)
            if is_test:
                data_rows = response.xpath('//span[@id="zoom"]/table//tr')
                item = right_item(self.basic_info, response, gs_type='拟审批')
                item['date_time'] = response.xpath('//div[@id="main-xm-content"]//td[@class="xm-content-date"]\
                                    //td[1]').xpath('string(.)').re_first('[\s\S]*(\d{4}.\d{1,2}.\d{1,2})')  # 发布时间
                item['project_name'] = data_rows[0].xpath('./td[2]').xpath('string(.)').extract_first(default='')  # 项目名称
                item['js_dw'] = data_rows[1].xpath('./td[2]').xpath('string(.)').extract_first(default='')   # 建设单位
                item['site'] = data_rows[2].xpath('./td[2]').xpath('string(.)').extract_first(default='')   # 建设地点
                item['hp_dw'] = data_rows[3].xpath('./td[2]').xpath('string(.)').extract_first(default='')   # 环评单位
                item['xm_gk'] = data_rows[4].xpath('./td[2]').xpath('string(.)').extract_first(default='')   # 项目概况
                item['yx_cs'] = data_rows[5].xpath('./td[2]').xpath('string(.)').extract_first(default='')   # 主要环境影响及环保措施
                gc_qk = data_rows[6].xpath('./td[2]').xpath('string(.)').extract_first(default='')   # 公众参与情况
                if gc_qk:
                    item['gc_qk'] = gc_qk
                yield item
            else:
                yield problem_item(self.basic_info, response, gs_type='拟审批', error_info='表格格式变化，无法提取')
        else:
            yield problem_item(self.basic_info, response, gs_type='拟审批', error_info='表格格式变化，无法提取')

    def parse_url_pf(self, response):
        tr_num = len(response.xpath('//span[@id="zoom"]//tr/td'))
        td_num = len(response.xpath('//span[@id="zoom"]//tr[@class="firstRow"]/td'))
        test1 = response.xpath('//span[@id="zoom"]//tr[@class="firstRow"]/td[2]').xpath('string(.)').\
            extract_first(default='')
        test2 = response.xpath('//span[@id="zoom"]//tr[@class="firstRow"]/td[3]').xpath('string(.)').\
            extract_first(default='')
        test3 = response.xpath('//span[@id="zoom"]//tr[@class="firstRow"]/td[4]').xpath('string(.)').\
            extract_first(default='')
        test4 = response.xpath('//span[@id="zoom"]//tr[@class="firstRow"]/td[5]').xpath('string(.)').\
            extract_first(default='')
        test5 = response.xpath('//span[@id="zoom"]//tr[@class="firstRow"]/td[6]').xpath('string(.)').\
            extract_first(default='')

        if tr_num % td_num == 0:
            if '批复名称' in test1 and '审批文号' in test2 and ('审批时间' in test3 or '审批日期' in test3) and \
                    '建设单位' in test4 and '建设地点' in test5:
                data_rows = response.xpath('//span[@id="zoom"]/table//tr')
                for i, data_row in enumerate(data_rows):
                    if i > 0:
                        item = right_item(self.basic_info, response, gs_type='审批')
                        item['project_name'] = data_row.xpath('./td[2]').xpath('string(.)').re_first('关于(.*)环境影响')  # 项目名称
                        item['js_dw'] = data_row.xpath('./td[5]/p').xpath('string(.)').extract_first(default='')  # 建设单位
                        item['site'] = data_row.xpath('./td[6]/p').xpath('string(.)').extract_first(default='')  # 建设地点
                        item['pf_num'] = data_row.xpath('./td[3]/p').xpath('string(.)').extract_first(default='')  # 环评批复文号
                        item['pf_time'] = data_row.xpath('./td[4]/p').xpath('string(.)').extract_first(default='')  # 环评批复时间
                        pf_url = response.xpath('//*[@id="zoom"]/../..//a[contains(@href, "/") and\
                         not(contains(@href, "@"))]')
                        msg, attachments = get_files(response, pf_url, tr_num - 1)
                        item['remark'] = json.dumps({"remark": None, "attachments": {"data": attachments,
                                                                                     "msg": msg}}, ensure_ascii=False)
                        yield item
            else:
                yield problem_item(self.basic_info, response, gs_type='审批', error_info='表格格式变化，无法提取')
        else:
            yield problem_item(self.basic_info, response, gs_type='审批', error_info='表格格式变化，无法提取')




