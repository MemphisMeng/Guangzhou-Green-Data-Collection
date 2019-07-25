# -*- coding: utf-8 -*-
"""
http://www.gdep.gov.cn/hpsp/
"""

from datetime import date
import scrapy
from scrapy.utils.log import configure_logging
from hpspider.items import HpspiderItem


class GuangdongSpider(scrapy.Spider):
    name = 'gd_1guangdong'

    file = "logs/%s%s.log" % (name, date.today().strftime("%Y_%m_%d"))
    exceptions = set()

    url_sl = 'http://www.gdep.gov.cn/hpsp/jsxmsp/slgg/index_{page}.html'
    url_nsp = 'http://www.gdep.gov.cn/hpsp/jsxmsp/spqgs/index_{page}.html'
    url_sp = 'http://www.gdep.gov.cn/hpsp/jsxmsp/sphgg/index_{page}.html'
    page_sl = 57
    page_nsp = 17
    page_sp = 37
    '''
    The three variables above respectively stand for the total pages that the website of reception, to-do issues and response have.
    So in the following part of this file, I split the function into three branches, each of which is focused on different topics.
    '''

    def __init__(self, *args, **kwargs):
        super(GuangdongSpider, self).__init__(*args, **kwargs)
        configure_logging(settings={'LOG_FILE': self.file, 'LOG_LEVEL': 'INFO'})

    def start_requests(self):
        yield scrapy.Request('http://www.gdep.gov.cn/hpsp/jsxmsp/slgg/index.html', callback=self.parse_url_sl)
        for page in range(1, self.page_sl):
            yield scrapy.Request(url=self.url_sl.format(page=page), callback=self.parse_url_sl)

        yield scrapy.Request('http://www.gdep.gov.cn/hpsp/jsxmsp/spqgs/index.html', callback=self.parse_url_nsp)
        for page in range(1, self.page_nsp):
            yield scrapy.Request(url=self.url_nsp.format(page=page), callback=self.parse_url_nsp)

        yield scrapy.Request('http://www.gdep.gov.cn/hpsp/jsxmsp/sphgg/index.html', callback=self.parse_url_sp)
        for page in range(1, self.page_sp):
            yield scrapy.Request(url=self.url_sp.format(page=page), callback=self.parse_url_sp)

    def parse_url_sl(self, response): # With 'sl' in the title, the function is expected to deal with the reception issues
        # It is also appliable in the following functions.
        urls = response.xpath('//a[@class="lie"]/@href').extract()
        for url in urls:
            full_url = response.urljoin(url)
            yield scrapy.Request(url=full_url, callback=self.parse_sl)

    def parse_url_nsp(self, response): # 'nsp' represents to-be-processed cases
        urls = response.xpath('//a[@class="lie"]/@href').extract()
        for url in urls:
            full_url = response.urljoin(url)
            yield scrapy.Request(url=full_url, callback=self.parse_nsp)

    def parse_url_sp(self, response):  # 'sp' represents processed cases
        urls = response.xpath('//a[@class="lie"]/@href').extract()
        for url in urls:
            full_url = response.urljoin(url)
            yield scrapy.Request(url=full_url, callback=self.parse_sp)

    def parse_sl(self, response):
        test = response.xpath('//div[@align="center"]//table[1]//tr[1]/td[6]').xpath('string(.)').extract_first()
        tr_num = len(response.xpath('//div[@align="center"]//table[1]//tr'))

        if tr_num == 2 and test and '环评文件' in test:  # First we needed to check whether any files are attached in the page
            item = HpspiderItem()
            item['source_url'] = response.url  
            item['source_webname'] = '广东省环境保护公众网站'  # the title of the source website
            item['province'] = 6  # provincial code
            item['sp_bm'] = '广东省环保厅'  # administration which really deals with this kind of issues
            item['gs_type'] = '受理'  # the type of the operation towards this issue
            item['hp_type'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[6]').xpath(
                'string(.)').extract_first()  # the type of the file attached
            # We wanted to know what kind of files the governments uploaded.
            # But we soon no longer needed this, because most metropolitan websites don't show it.
            item['date_time'] = response.xpath('//table[@width="60%"]').xpath('string(.)').re_first(
                '[\s\S]*(\d{4}.\d{1,2}.\d{1,2})')  # releasing date
            item['project_name'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[2]').xpath(
                'string(.)').extract_first()  # title of construction project
            item['js_dw'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[3]').xpath(
                'string(.)').extract_first()  # constructor
            item['hp_dw'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[5]').xpath(
                'string(.)').extract_first()  # evaluator of environmental effects
            item['site'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[4]').xpath(
                'string(.)').extract_first()  # construction sites
            bg_url = response.xpath('//div[@id="appendix"]//a/@href').extract()
            if len(bg_url) == 1:
                item['bg_url'] = response.urljoin(bg_url[0])
            if len(bg_url) > 1:
                item['bg_url'] = response.urljoin(bg_url[0])
                item['gc_url'] = response.urljoin(bg_url[1])
            yield item
            # Our methodology is to find a general used but simple keyword in the page.
            # Based on what the keyword is, we defined a certain ( which is as well as fixed) way to extract what we wanted.
            # We chose '类型(type)', '环评单位(evaluator)', 'file(环评文件)' as the keywords. (Obviously it's not a smart way.)
        elif tr_num == 2 and test and '类型' in test:  
            item = HpspiderItem()
            item['source_url'] = response.url  # source
            item['source_webname'] = '广东省环境保护公众网站' 
            item['province'] = 6  
            item['sp_bm'] = '广东省环保厅'  
            item['gs_type'] = '受理'  
            item['hp_type'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[6]').xpath(
                'string(.)').extract_first()  
            item['date_time'] = response.xpath('//table[@width="60%"]').xpath('string(.)').re_first(
                '[\s\S]*(\d{4}.\d{1,2}.\d{1,2})')  
            item['project_name'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[2]').xpath(
                'string(.)').extract_first()  
            item['js_dw'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[3]').xpath(
                'string(.)').extract_first()  
            item['hp_dw'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[5]').xpath(
                'string(.)').extract_first()  
            item['site'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[4]').xpath(
                'string(.)').extract_first()  
            bg_url = response.xpath('//div[@id="appendix"]//a/@href').extract()
            if len(bg_url) == 1:
                item['bg_url'] = response.urljoin(bg_url[0])
            if len(bg_url) > 1:
                item['bg_url'] = response.urljoin(bg_url[0])
                item['gc_url'] = response.urljoin(bg_url[1])
            yield item
        elif tr_num == 2 a-nd test and '环评单位' in test:
            item = HpspiderItem()
            item['source_url'] = response.url  
            item['source_webname'] = '广东省环境保护公众网站'  
            item['province'] = 6  
            item['sp_bm'] = '广东省环保厅'  
            item['gs_type'] = '受理'  
            item['hp_type'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[7]').xpath(
                'string(.)').extract_first()  
            item['date_time'] = response.xpath('//table[@width="60%"]').xpath('string(.)').re_first(
                '[\s\S]*(\d{4}.\d{1,2}.\d{1,2})')  
            item['project_name'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[3]').xpath(
                'string(.)').extract_first()  
            item['js_dw'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[5]').xpath(
                'string(.)').extract_first()  
            item['hp_dw'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[6]').xpath(
                'string(.)').extract_first()  
            item['site'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[4]').xpath(
                'string(.)').extract_first()  
            bg_url = response.xpath('//div[@id="appendix"]//a/@href').extract()
            if len(bg_url) == 1:
                item['bg_url'] = response.urljoin(bg_url[0])
            if len(bg_url) > 1:
                item['bg_url'] = response.urljoin(bg_url[0])
                item['gc_url'] = response.urljoin(bg_url[1])
            yield item
        else:
            item = HpspiderItem()
            content = response.xpath('//body').extract_first()
            item['p_type'] = '受理'
            item['p_content'] = content
            item['p_status'] = 0
            item['problem_url'] = response.url  
            item['source_webname'] = '广东省环境保护公众网站'  
            item['error_info'] = '网页格式不正确，无法提取'
            # We had not been aware of that it is constant that the format of a site is not totally the same as another.
            # We thought it must be the developer's duty to maintain every site in a constant format.
            # So something troublesome occurred, we just assumed it to be an error, never thinking we could make a difference.
            yield item

    def parse_nsp(self, response):
        test = response.xpath('//div[@align="center"]//table[2]//tr[5]/td[1]').xpath('string(.)').extract_first()
        td_num = len(response.xpath('//div[@align="center"]//table[2]//tr[5]/td'))
        
        # Here we needed to checked whether the brief introduction to the constrcution project is contained.
        # Otherwise we categorized the page into "erroric" types.
        if td_num == 2 and test and '项目概况' in test:
            item = HpspiderItem()
            item['source_url'] = response.url  
            item['source_webname'] = '广东省环境保护公众网站'  
            item['province'] = 6  
            item['sp_bm'] = '广东省环保厅'  # Bureau of Environmental Protection of Guangdong Province
            item['gs_type'] = '拟审批'  
            item['date_time'] = response.xpath('//table[@width="60%"]').xpath('string(.)').re_first(
                '[\s\S]*(\d{4}.\d{1,2}.\d{1,2})')  
            item['project_name'] = response.xpath('//div[@align="center"]//table[2]//tr[1]/td[2]').xpath(
                'string(.)').extract_first()  
            item['js_dw'] = response.xpath('//div[@align="center"]//table[2]//tr[2]/td[2]').xpath(
                'string(.)').extract_first()  
            item['hp_dw'] = response.xpath('//div[@align="center"]//table[2]//tr[4]/td[2]').xpath(
                'string(.)').extract_first()  
            item['site'] = response.xpath('//div[@align="center"]//table[2]//tr[3]/td[2]').xpath(
                'string(.)').extract_first()  
            item['xm_gk'] = response.xpath('//div[@align="center"]//table[2]//tr[5]/td[2]').xpath(
                'string(.)').extract_first()  
            item['yx_cs'] = response.xpath('//div[@align="center"]//table[2]//tr[6]/td[2]').xpath(
                'string(.)').extract_first()  
            item['gc_qk'] = response.xpath('//div[@align="center"]//table[2]//tr[7]/td[2]').xpath(
                'string(.)').extract_first()  
            yield item
        else:
            item = HpspiderItem()
            content = response.xpath('//body').extract_first()
            item['p_type'] = '拟审批'
            item['p_content'] = content
            item['p_status'] = 0
            item['problem_url'] = response.url  
            item['source_webname'] = '广东省环境保护公众网站'  
            item['error_info'] = '网页格式不正确，无法提取'
            yield item

    def parse_sp(self, response):
        test = response.xpath('//div[@align="center"]//table[1]//tr[1]/td[6]').xpath('string(.)').extract_first()
        test1 = response.xpath('//div[@align="center"]//table[1]//tr[1]/td[8]').xpath('string(.)').extract_first()
        test2 = response.xpath('//div[@align="center"]//table[1]//tr[1]/td[5]').xpath('string(.)').extract_first()
        tr_num = len(response.xpath('//div[@align="center"]//table[1]//tr'))
        td_num = len(response.xpath('//div[@align="center"]//table[1]//tr[1]/td'))

        # We chose '建设地点(construction sites)', '审批文号(code of case)' as the keywords.
        # The information is either laid in a row or a column.
        # To confirm the structure of the table, or in other words, to check if the information is laid in a row, 
        # I needed to make sure the last column existed.
        # Usually there are five, six or eight columns in one page.
        if test and '建设地点' in test: # when a page includes 6 columns
            for i in range(1, tr_num):
                item = HpspiderItem()
                item['source_url'] = response.url  
                item['source_webname'] = '广东省环境保护公众网站'  
                item['province'] = 6  
                item['sp_bm'] = '广东省环保厅'  
                item['gs_type'] = '审批'  
                item['hp_type'] = response.xpath(
                    '//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[2]').xpath(
                    'string(.)').extract_first()  
                item['date_time'] = response.xpath('//table[@width="60%"]').xpath('string(.)').re_first(
                    '[\s\S]*(\d{4}.\d{1,2}.\d{1,2})')  
                item['project_name'] = response.xpath(
                    '//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[2]').xpath(
                    'string(.)').extract_first()  
                item['js_dw'] = response.xpath('//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[5]').xpath(
                    'string(.)').extract_first()  
                item['site'] = response.xpath('//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[6]').xpath(
                    'string(.)').extract_first()
                item['pf_num'] = response.xpath('//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[3]').xpath(
                    'string(.)').extract_first()
                item['pf_time'] = response.xpath(
                    '//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[4]').xpath(
                    'string(.)').extract_first()
                pf_url = response.xpath('//div[@id="appendix"]//a/@href').extract_first()
                if pf_url:
                    item['pf_url'] = response.urljoin(pf_url)  
                yield item
        elif td_num == 8 and test1 and '审批文号' in test1:  # 8 columns included with '审批文号' on the line of the table
            for i in range(1, tr_num):
                item = HpspiderItem()
                item['source_url'] = response.url  
                item['source_webname'] = '广东省环境保护公众网站'  
                item['province'] = 6  
                item['sp_bm'] = '广东省环境保护厅'  
                item['gs_type'] = '审批'  
                item['date_time'] = response.xpath('//table[@width="60%"]').xpath('string(.)').re_first(
                    '[\s\S]*(\d{4}.\d{1,2}.\d{1,2})')  
                item['project_name'] = response.xpath(
                    '//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[2]').xpath(
                    'string(.)').extract_first()  
                item['js_dw'] = response.xpath('//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[3]').xpath(
                    'string(.)').extract_first()  
                item['site'] = response.xpath('//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[4]').xpath(
                    'string(.)').extract_first()  
                item['pf_num'] = response.xpath('//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[8]').xpath(
                    'string(.)').extract_first()  # In China, there will be a code for whichever case once if it is issued or processed.
                # This variable is the collection for the codes.
                item['pf_time'] = response.xpath(
                    '//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[6]').xpath(
                    'string(.)').extract_first()  # the releasing date of the code
                item['xm_gk'] = response.xpath('//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[5]').xpath(
                    'string(.)').extract_first()  # a brief introcduction to the construction project, which is 
                yield item
        elif test1 and '审批结果' in test1:  # 8 columns included with '审批结果' on the first line
            for i in range(1, tr_num):
                item = HpspiderItem()
                item['source_url'] = response.url  
                item['source_webname'] = '广东省环境保护公众网站'  
                item['province'] = 6  
                item['sp_bm'] = '广东省环境保护厅'  
                item['gs_type'] = '审批'  
                item['date_time'] = response.xpath('//table[@width="60%"]').xpath('string(.)').re_first(
                    '[\s\S]*(\d{4}.\d{1,2}.\d{1,2})')  
                item['project_name'] = response.xpath(
                    '//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[2]').xpath(
                    'string(.)').extract_first()  
                item['js_dw'] = response.xpath('//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[3]').xpath(
                    'string(.)').extract_first()  
                item['site'] = response.xpath('//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[4]').xpath(
                    'string(.)').extract_first()  
                item['pf_num'] = response.xpath('//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[7]').xpath(
                    'string(.)').extract_first()  
                item['pf_time'] = response.xpath(
                    '//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[6]').xpath(
                    'string(.)').extract_first()  
                item['xm_gk'] = response.xpath('//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[5]').xpath(
                    'string(.)').extract_first()  
                yield item
        elif test2 and '审批文号' in test2:  # 5 columns included with '审批文号' on the first line
            for i in range(1, tr_num):
                item = HpspiderItem()
                item['source_url'] = response.url  
                item['source_webname'] = '广东省环境保护公众网站'  
                item['province'] = 6  
                item['sp_bm'] = '广东省环境保护厅'  
                item['gs_type'] = '审批'  
                item['date_time'] = response.xpath('//table[@width="60%"]').xpath('string(.)').re_first(
                    '[\s\S]*(\d{4}.\d{1,2}.\d{1,2})')  
                item['project_name'] = response.xpath(
                    '//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[1]').xpath(
                    'string(.)').extract_first()  
                item['js_dw'] = response.xpath('//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[2]').xpath(
                    'string(.)').extract_first()  
                item['site'] = response.xpath('//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[3]').xpath(
                    'string(.)').extract_first()  
                item['pf_num'] = response.xpath('//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[5]').xpath(
                    'string(.)').extract_first()  
                item['pf_time'] = response.xpath(
                    '//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[4]').xpath(
                    'string(.)').extract_first()  
                yield item
        else:  # finally, errors
            item = HpspiderItem()
            content = response.xpath('//body').extract_first()
            item['p_type'] = '审批'
            item['p_content'] = content
            item['p_status'] = 0
            item['problem_url'] = response.url  
            item['source_webname'] = '广东省环境保护公众网站'  
            item['error_info'] = '网页格式不正确，无法提取'
            yield item
