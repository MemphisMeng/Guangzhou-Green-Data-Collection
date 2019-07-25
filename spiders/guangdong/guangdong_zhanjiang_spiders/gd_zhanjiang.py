"""
coder: 蒙安哲
date: 2019/3/21

网址:  受理  http://www.gdzjepb.gov.cn/list/49/tid/27.html
备注:  湛江市生态环境局公众网

"""

# -*- coding: utf-8 -*-
import scrapy
import json
# from datetime import date
# from scrapy.utils.log import configure_logging
from hpspider.utils import right_item, problem_item, get_files, merge_table, format_table


class Hpspider(scrapy.Spider):
    name = 'gd_zhanjiang'
    page = 4

    url = 'http://www.gdzjepb.gov.cn/list/49/tid/27.html'

    basic_info = {'province': 6,
                  'city': 93,
                  'source_webname': '湛江市生态环境局公众网',
                  'sp_bm': '湛江市环境保护局'}

    # file = "logs/%s%s.log" % (name, date.today().strftime("%Y_%m_%d"))
    # exceptions = set()

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     configure_logging(settings={'LOG_FILE': self.file, 'LOG_LEVEL': 'INFO'})

    def start_requests(self):
        # post请求参数
        for i in range(1, self.page + 1):
            formdata = {
                'page': str(i),
            }
            yield scrapy.FormRequest(url=self.url, formdata=formdata, callback=self.parse_url)

    def parse_url(self, response):
        links = response.xpath('//span[@class="contd_la1m1"]/../a')

        for link in links:
            url = link.xpath('./@href').extract_first(default='')
            full_url = response.urljoin(url)
            yield scrapy.Request(url=full_url, callback=self.parse_url_sl)

    def parse_url_sl(self, response):
        trs = response.xpath('//div[@id="news_content"]//td[4]/..')
        if trs:
            table = format_table(merge_table(trs))
            test2 = ''.join(table.xpath('string(//tr[1]/td[2])').extract_first(default='').split())
            test3 = ''.join(table.xpath('string(//tr[1]/td[3])').extract_first(default='').split())
            test4 = ''.join(table.xpath('string(//tr[1]/td[4])').extract_first(default='').split())
            test5 = ''.join(table.xpath('string(//tr[1]/td[5])').extract_first(default='').split())
            is_test = ('项目' in test2 or '规划' in test2) and '建设单位' in test3 \
                      and '地点' in test4 and ('环评' in test5 or '环境影响' in test5)
            if is_test:
                data_rows = table.xpath('//body/table/tr')
                for i, data_row in enumerate(data_rows):
                    if i > 0:
                        item = right_item(self.basic_info, response, gs_type='受理')
                        item['date_time'] = response.xpath('string(//div[@class="lm_nr1"])'). \
                            re_first('\d{4}\D\d{1,2}\D\d{1,2}')  # 发布时间
                        item['project_name'] = data_row.xpath('string(./td[2])').extract_first(default='')  # 项目名称
                        item['js_dw'] = data_row.xpath('string(./td[3])').extract_first(default='')  # 建设单位
                        item['hp_dw'] = data_row.xpath('string(./td[5])').extract_first(default='')  # 环评单位
                        item['site'] = data_row.xpath('string(./td[4])').extract_first(default='')  # 建设地点
                        file_texts = data_row.xpath('.//a[contains(@href, "/") and not(contains(@href, "@"))]')  # 附件链接
                        if file_texts:
                            msg, attachments = get_files(response, file_texts, 1)
                        else:
                            file_texts = response.xpath('//div[@id="news_content"]//a[contains(href,"/") '
                                                        'and not (contains(@href,"@"))]')
                            num = len(data_rows) - 1
                            msg, attachments = get_files(response, file_texts, num)
                        item['remark'] = json.dumps({"remark": None, "attachments": {"data": attachments,
                                                                                     "msg": msg}},
                                                    ensure_ascii=False)
                        yield item
            else:
                yield problem_item(self.basic_info, response, gs_type='受理', error_info='表格格式变化，无法提取')

        else:
            trs = response.xpath('//div[@id="news_content"]//td[2]/..')
            table = format_table(merge_table(trs))
            if trs:
                test2 = ''.join(table.xpath('string(//tr[2]/td[1])').extract_first(default='').split())
                test3 = ''.join(table.xpath('string(//tr[3]/td[1])').extract_first(default='').split())
                test4 = ''.join(table.xpath('string(//tr[4]/td[1])').extract_first(default='').split())
                test5 = ''.join(table.xpath('string(//tr[5]/td[1])').extract_first(default='').split())
                is_test = ('项目' in test2 or '规划' in test2) and '建设单位' in test3 \
                            and '地点' in test4 and ('环评' in test5 or '环境影响' in test5)
                if is_test:
                    data_rows = table.xpath('//body/table/tr')
                    item = right_item(self.basic_info, response, gs_type='受理')
                    item['date_time'] = response.xpath('string(//div[@class="lm_nr1"])'). \
                        re_first('\d{4}\D\d{1,2}\D\d{1,2}')
                    item['project_name'] = data_rows[1].xpath('string(./td[2])').extract_first(default='')
                    item['js_dw'] = data_rows[2].xpath('string(./td[2])').extract_first(default='')
                    item['hp_dw'] = data_rows[4].xpath('string(./td[2])').extract_first(default='')
                    item['site'] = data_rows[3].xpath('string(./td[2])').extract_first(default='')
                    file_texts = data_rows[6].xpath('.//a[contains(@href, "/") and not(contains(@href, "@"))]')
                    if file_texts:
                        msg, attachments = get_files(response, file_texts, 1)
                    else:
                        file_texts = response.xpath('//div[@cid="news_content"]//a[contains(href,"/") '
                                                    'and not (contains(@href,"@"))]')
                        msg, attachments = get_files(response, file_texts, 1)
                    item['remark'] = json.dumps({"remark": None, "attachments": {"data": attachments, "msg": msg}},
                                                ensure_ascii=False)
                    yield item
                else:
                    yield problem_item(self.basic_info, response, gs_type='受理', error_info='表格格式变化，无法提取')
            else:
                yield problem_item(self.basic_info, response, gs_type='受理', error_info='网页格式不正确，无法提取')
