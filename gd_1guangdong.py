# -*- coding: utf-8 -*-
"""
author: luoxin
date:

网站：http://www.gdep.gov.cn/hpsp/
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
    page_sl = 2#57
    page_nsp = 2#17
    page_sp = 2#37

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

    def parse_url_sl(self, response):
        urls = response.xpath('//a[@class="lie"]/@href').extract()
        for url in urls:
            full_url = response.urljoin(url)
            yield scrapy.Request(url=full_url, callback=self.parse_sl)

    def parse_url_nsp(self, response):
        urls = response.xpath('//a[@class="lie"]/@href').extract()
        for url in urls:
            full_url = response.urljoin(url)
            yield scrapy.Request(url=full_url, callback=self.parse_nsp)

    def parse_url_sp(self, response):
        urls = response.xpath('//a[@class="lie"]/@href').extract()
        for url in urls:
            full_url = response.urljoin(url)
            yield scrapy.Request(url=full_url, callback=self.parse_sp)

    def parse_sl(self, response):
        test = response.xpath('//div[@align="center"]//table[1]//tr[1]/td[6]').xpath('string(.)').extract_first()
        tr_num = len(response.xpath('//div[@align="center"]//table[1]//tr'))

        if tr_num == 2 and test and '环评文件' in test:
            item = HpspiderItem()
            item['source_url'] = response.url  # 来源链接
            item['source_webname'] = '广东省环境保护公众网站'  # 来源网站名称
            item['province'] = 6  # 省
            item['sp_bm'] = '广东省环保厅'  # 审批部门
            item['gs_type'] = '受理'  # 公示类型
            item['hp_type'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[6]').xpath(
                'string(.)').extract_first()  # 环评文件类型
            item['date_time'] = response.xpath('//table[@width="60%"]').xpath('string(.)').re_first(
                '[\s\S]*(\d{4}.\d{1,2}.\d{1,2})')  # 发布时间
            item['project_name'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[2]').xpath(
                'string(.)').extract_first()  # 项目名称
            item['js_dw'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[3]').xpath(
                'string(.)').extract_first()  # 建设单位
            item['hp_dw'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[5]').xpath(
                'string(.)').extract_first()  # 环评单位
            item['site'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[4]').xpath(
                'string(.)').extract_first()  # 建设地点
            bg_url = response.xpath('//div[@id="appendix"]//a/@href').extract()
            if len(bg_url) == 1:
                item['bg_url'] = response.urljoin(bg_url[0])
            if len(bg_url) > 1:
                item['bg_url'] = response.urljoin(bg_url[0])
                item['gc_url'] = response.urljoin(bg_url[1])
            yield item
        elif tr_num == 2 and test and '类型' in test:
            item = HpspiderItem()
            item['source_url'] = response.url  # 来源链接
            item['source_webname'] = '广东省环境保护公众网站'  # 来源网站名称
            item['province'] = 6  # 省
            item['sp_bm'] = '广东省环保厅'  # 审批部门
            item['gs_type'] = '受理'  # 公示类型
            item['hp_type'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[6]').xpath(
                'string(.)').extract_first()  # 环评文件类型
            item['date_time'] = response.xpath('//table[@width="60%"]').xpath('string(.)').re_first(
                '[\s\S]*(\d{4}.\d{1,2}.\d{1,2})')  # 发布时间
            item['project_name'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[2]').xpath(
                'string(.)').extract_first()  # 项目名称
            item['js_dw'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[3]').xpath(
                'string(.)').extract_first()  # 建设单位
            item['hp_dw'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[5]').xpath(
                'string(.)').extract_first()  # 环评单位
            item['site'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[4]').xpath(
                'string(.)').extract_first()  # 建设地点
            bg_url = response.xpath('//div[@id="appendix"]//a/@href').extract()
            if len(bg_url) == 1:
                item['bg_url'] = response.urljoin(bg_url[0])
            if len(bg_url) > 1:
                item['bg_url'] = response.urljoin(bg_url[0])
                item['gc_url'] = response.urljoin(bg_url[1])
            yield item
        elif tr_num == 2 and test and '环评单位' in test:
            item = HpspiderItem()
            item['source_url'] = response.url  # 来源链接
            item['source_webname'] = '广东省环境保护公众网站'  # 来源网站名称
            item['province'] = 6  # 省
            item['sp_bm'] = '广东省环保厅'  # 审批部门
            item['gs_type'] = '受理'  # 公示类型
            item['hp_type'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[7]').xpath(
                'string(.)').extract_first()  # 环评文件类型
            item['date_time'] = response.xpath('//table[@width="60%"]').xpath('string(.)').re_first(
                '[\s\S]*(\d{4}.\d{1,2}.\d{1,2})')  # 发布时间
            item['project_name'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[3]').xpath(
                'string(.)').extract_first()  # 项目名称
            item['js_dw'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[5]').xpath(
                'string(.)').extract_first()  # 建设单位
            item['hp_dw'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[6]').xpath(
                'string(.)').extract_first()  # 环评单位
            item['site'] = response.xpath('//div[@align="center"]//table[1]//tr[2]/td[4]').xpath(
                'string(.)').extract_first()  # 建设地点
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
            item['problem_url'] = response.url  # 来源链接
            item['source_webname'] = '广东省环境保护公众网站'  # 来源网站名称
            item['error_info'] = '网页格式不正确，无法提取'
            yield item

    def parse_nsp(self, response):
        test = response.xpath('//div[@align="center"]//table[2]//tr[5]/td[1]').xpath('string(.)').extract_first()
        td_num = len(response.xpath('//div[@align="center"]//table[2]//tr[5]/td'))

        if td_num == 2 and test and '项目概况' in test:
            item = HpspiderItem()
            item['source_url'] = response.url  # 来源链接
            item['source_webname'] = '广东省环境保护公众网站'  # 来源网站名称
            item['province'] = 6  # 省
            item['sp_bm'] = '广东省环保厅'  # 审批部门
            item['gs_type'] = '拟审批'  # 公示类型
            item['date_time'] = response.xpath('//table[@width="60%"]').xpath('string(.)').re_first(
                '[\s\S]*(\d{4}.\d{1,2}.\d{1,2})')  # 发布时间
            item['project_name'] = response.xpath('//div[@align="center"]//table[2]//tr[1]/td[2]').xpath(
                'string(.)').extract_first()  # 项目名称
            item['js_dw'] = response.xpath('//div[@align="center"]//table[2]//tr[2]/td[2]').xpath(
                'string(.)').extract_first()  # 建设单位
            item['hp_dw'] = response.xpath('//div[@align="center"]//table[2]//tr[4]/td[2]').xpath(
                'string(.)').extract_first()  # 环评单位
            item['site'] = response.xpath('//div[@align="center"]//table[2]//tr[3]/td[2]').xpath(
                'string(.)').extract_first()  # 建设地点
            item['xm_gk'] = response.xpath('//div[@align="center"]//table[2]//tr[5]/td[2]').xpath(
                'string(.)').extract_first()  # 项目概况
            item['yx_cs'] = response.xpath('//div[@align="center"]//table[2]//tr[6]/td[2]').xpath(
                'string(.)').extract_first()  # 主要环境影响及环保措施
            item['gc_qk'] = response.xpath('//div[@align="center"]//table[2]//tr[7]/td[2]').xpath(
                'string(.)').extract_first()  # 公众参与情况
            yield item
        else:
            item = HpspiderItem()
            content = response.xpath('//body').extract_first()
            item['p_type'] = '拟审批'
            item['p_content'] = content
            item['p_status'] = 0
            item['problem_url'] = response.url  # 来源链接
            item['source_webname'] = '广东省环境保护公众网站'  # 来源网站名称
            item['error_info'] = '网页格式不正确，无法提取'
            yield item

    def parse_sp(self, response):
        test = response.xpath('//div[@align="center"]//table[1]//tr[1]/td[6]').xpath('string(.)').extract_first()
        test1 = response.xpath('//div[@align="center"]//table[1]//tr[1]/td[8]').xpath('string(.)').extract_first()
        test2 = response.xpath('//div[@align="center"]//table[1]//tr[1]/td[5]').xpath('string(.)').extract_first()
        tr_num = len(response.xpath('//div[@align="center"]//table[1]//tr'))
        td_num = len(response.xpath('//div[@align="center"]//table[1]//tr[1]/td'))

        if test and '建设地点' in test:
            for i in range(1, tr_num):
                item = HpspiderItem()
                item['source_url'] = response.url  # 来源链接
                item['source_webname'] = '广东省环境保护公众网站'  # 来源网站名称
                item['province'] = 6  # 省
                item['sp_bm'] = '广东省环保厅'  # 审批部门
                item['gs_type'] = '审批'  # 公示类型
                item['hp_type'] = response.xpath(
                    '//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[2]').xpath(
                    'string(.)').extract_first()  # 环评文件类型
                item['date_time'] = response.xpath('//table[@width="60%"]').xpath('string(.)').re_first(
                    '[\s\S]*(\d{4}.\d{1,2}.\d{1,2})')  # 发布时间
                item['project_name'] = response.xpath(
                    '//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[2]').xpath(
                    'string(.)').extract_first()  # 项目名称
                item['js_dw'] = response.xpath('//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[5]').xpath(
                    'string(.)').extract_first()  # 建设单位
                item['site'] = response.xpath('//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[6]').xpath(
                    'string(.)').extract_first()  # 建设地点
                item['pf_num'] = response.xpath('//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[3]').xpath(
                    'string(.)').extract_first()  # 环评批复文号
                item['pf_time'] = response.xpath(
                    '//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[4]').xpath(
                    'string(.)').extract_first()  # 环评批复时间
                pf_url = response.xpath('//div[@id="appendix"]//a/@href').extract_first()
                if pf_url:
                    item['pf_url'] = response.urljoin(pf_url)  # 环评批复链接
                yield item
        elif td_num == 8 and test1 and '审批文号' in test1:
            for i in range(1, tr_num):
                item = HpspiderItem()
                item['source_url'] = response.url  # 来源链接
                item['source_webname'] = '广东省环境保护公众网站'  # 来源网站名称
                item['province'] = 6  # 省
                item['sp_bm'] = '广东省环境保护厅'  # 审批部门
                item['gs_type'] = '审批'  # 公示类型
                item['date_time'] = response.xpath('//table[@width="60%"]').xpath('string(.)').re_first(
                    '[\s\S]*(\d{4}.\d{1,2}.\d{1,2})')  # 发布时间
                item['project_name'] = response.xpath(
                    '//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[2]').xpath(
                    'string(.)').extract_first()  # 项目名称
                item['js_dw'] = response.xpath('//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[3]').xpath(
                    'string(.)').extract_first()  # 建设单位
                item['site'] = response.xpath('//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[4]').xpath(
                    'string(.)').extract_first()  # 建设地点
                item['pf_num'] = response.xpath('//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[8]').xpath(
                    'string(.)').extract_first()  # 环评批复文号
                item['pf_time'] = response.xpath(
                    '//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[6]').xpath(
                    'string(.)').extract_first()  # 环评批复时间
                item['xm_gk'] = response.xpath('//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[5]').xpath(
                    'string(.)').extract_first()  # 项目概况
                yield item
        elif test1 and '审批结果' in test1:
            for i in range(1, tr_num):
                item = HpspiderItem()
                item['source_url'] = response.url  # 来源链接
                item['source_webname'] = '广东省环境保护公众网站'  # 来源网站名称
                item['province'] = 6  # 省
                item['sp_bm'] = '广东省环境保护厅'  # 审批部门
                item['gs_type'] = '审批'  # 公示类型
                item['date_time'] = response.xpath('//table[@width="60%"]').xpath('string(.)').re_first(
                    '[\s\S]*(\d{4}.\d{1,2}.\d{1,2})')  # 发布时间
                item['project_name'] = response.xpath(
                    '//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[2]').xpath(
                    'string(.)').extract_first()  # 项目名称
                item['js_dw'] = response.xpath('//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[3]').xpath(
                    'string(.)').extract_first()  # 建设单位
                item['site'] = response.xpath('//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[4]').xpath(
                    'string(.)').extract_first()  # 建设地点
                item['pf_num'] = response.xpath('//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[7]').xpath(
                    'string(.)').extract_first()  # 环评批复文号
                item['pf_time'] = response.xpath(
                    '//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[6]').xpath(
                    'string(.)').extract_first()  # 环评批复时间
                item['xm_gk'] = response.xpath('//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[5]').xpath(
                    'string(.)').extract_first()  # 项目概况
                yield item
        elif test2 and '审批文号' in test2:
            for i in range(1, tr_num):
                item = HpspiderItem()
                item['source_url'] = response.url  # 来源链接
                item['source_webname'] = '广东省环境保护公众网站'  # 来源网站名称
                item['province'] = 6  # 省
                item['sp_bm'] = '广东省环境保护厅'  # 审批部门
                item['gs_type'] = '审批'  # 公示类型
                item['date_time'] = response.xpath('//table[@width="60%"]').xpath('string(.)').re_first(
                    '[\s\S]*(\d{4}.\d{1,2}.\d{1,2})')  # 发布时间
                item['project_name'] = response.xpath(
                    '//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[1]').xpath(
                    'string(.)').extract_first()  # 项目名称
                item['js_dw'] = response.xpath('//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[2]').xpath(
                    'string(.)').extract_first()  # 建设单位
                item['site'] = response.xpath('//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[3]').xpath(
                    'string(.)').extract_first()  # 建设地点
                item['pf_num'] = response.xpath('//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[5]').xpath(
                    'string(.)').extract_first()  # 环评批复文号
                item['pf_time'] = response.xpath(
                    '//div[@align="center"]//table[1]//tr[' + str(i + 1) + ']/td[4]').xpath(
                    'string(.)').extract_first()  # 环评批复时间
                yield item
        else:
            item = HpspiderItem()
            content = response.xpath('//body').extract_first()
            item['p_type'] = '审批'
            item['p_content'] = content
            item['p_status'] = 0
            item['problem_url'] = response.url  # 来源链接
            item['source_webname'] = '广东省环境保护公众网站'  # 来源网站名称
            item['error_info'] = '网页格式不正确，无法提取'
            yield item
