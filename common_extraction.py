# coding: utf-8

"""
A module containing generalized methods for environmental evaluation information extraction

通用的环评数据提取方法模块
"""

from hpspider.utils import clean_blank, get_files, format_table, query_string, replace_th, split_span
from hpspider.common_extraction_info import PROJECT_NAME, SITE, JS_DW, HP_DW, XM_GK, YX_CS, PF_NUM, PF_TIME
from scrapy.selector import Selector
import re


class Extraction:

    def __init__(self, body, response, files=None):
        self.body = body
        self.response = response
        self.files = files

    def estimate_content_format(self):
        """This helps us judge which format it is before we start extracting"""
        content_format = None
        if self.body.xpath('//th'):
            self.body = replace_th(self.body)
        table = self.body.xpath("descendant-or-self::table//tr[2]/td[2]/ancestor::table[1]")
        has_span = table.xpath('.//td/@rowspan') or table.xpath('.//td/@colspan')
        if has_span:
            table = split_span(table)
        if table:
            trs = table.xpath(".//tr")
            for tr in trs:
                tds = tr.xpath("./td")
                if len(tds) == 2:
                    content_format = 'two_col_table'
                    break
                if len(tds) > 2:
                    content_format = 'multiple_col_table'
                    break
        if not content_format:
            content_format = 'none_table'
        return content_format

    def extract(self):
        format_mapping = {
            'two_col_table': self.extract_format1,
            'multiple_col_table': self.extract_format2,
            'none_table': self.extract_format3
        }
        content_format = self.estimate_content_format()
        return format_mapping[content_format]()

    def extract_format1(self):
        pass

    def extract_format2(self):
        pass

    def extract_format3(self):
        pass


class ShouliExtraction(Extraction):
    """This method is used for the reception section web pages."""

    def __init__(self, body, response, files=None, project_name=None, site=None, js_dw=None, hp_dw=None):
        super(ShouliExtraction, self).__init__(body, response, files)
        self.project_name = PROJECT_NAME
        self.site = SITE
        self.js_dw = JS_DW
        self.hp_dw = HP_DW
        if project_name:
            self.project_name.append(project_name)
        if site:
            self.site.append(site)
        if js_dw:
            self.js_dw.append(js_dw)
        if hp_dw:
            self.hp_dw.append(hp_dw)

    def extract_format1(self):
        """
        Format No.1: Every page has only a piece of information, being displayed in a two-column table.
        Example site: http://sthjj.hengyang.gov.cn/gsgg/201904/t20190418_2832372.html
        :return: str（error warnings） or [data]
        """
        if self.body.xpath('//th'):
            self.body = replace_th(self.body)
        table = self.body.xpath("descendant-or-self::table//tr[2]/td[2]/ancestor::table[1]")
        if len(table) > 1:
            return '拟审批提取失败(1)--多个表格'
        has_span = table.xpath('.//td/@rowspan') or table.xpath('.//td/@colspan')
        if has_span:
            table = split_span(table)

        project_name, site, js_dw, hp_dw, msg, attachments = '', '', '', '', None, None
        trs = table.xpath(".//td[2]/..")
        for tr in trs:
            tds = tr.xpath(".//td")
            if len(tds) < 2:
                continue
            td_text_list = tds.xpath("string(.)").extract()
            td1_text = td_text_list[0]
            text = clean_blank(td1_text)
            td2_text = td_text_list[1].strip()

            if query_string(self.project_name, text):
                project_name = td2_text
                continue
            if query_string(self.site, text):
                site = td2_text
                continue
            if query_string(self.js_dw, text):
                js_dw = td2_text
                continue
            if query_string(self.hp_dw, text):
                hp_dw = td2_text
                continue

        if not project_name:
            return '受理提取失败(1)--未匹配到项目名称'
        # extract the attachments
        if self.files:
            files = self.files
        else:
            files = table.xpath('.//a[contains(@href, "/") or contains(@href, "?")]')
            if not files:
                files = self.body.xpath('.//a[contains(@href, "/") or contains(@href, "?")]')
        if files:
            msg, attachments = get_files(self.response, files, 1)
        data = {
            "project_name": project_name,
            "site": site,
            "js_dw": js_dw,
            "hp_dw": hp_dw,
            "msg": msg,
            "attachments": attachments
        }
        return [data]

    def extract_format2(self):
        """
        Format No.2: One a piece of information in every page, being displyed in a table with more two columns.
        Example site: http://www.hyx.gov.cn/zwgk/bmxxgkml/xhbj/tzgg_82867/201903/t20190327_2819615.html
        :return: str（error warnings） or [data]
        """
        if self.body.xpath('//th'):
            self.body = replace_th(self.body)
        table = self.body.xpath("descendant-or-self::table//tr[2]/td[2]/ancestor::table[1]")
        if len(table) > 1:
            return '受理提取失败(1)--多个表格'
        has_span = table.xpath('.//td/@rowspan') or table.xpath('.//td/@colspan')
        if has_span:
            table = split_span(table)

        trs = table.xpath(".//td[2]/..")
        all_td1_text = ''
        for i, tr in enumerate(trs):
            td1_text = tr.xpath('string(./td[1])').extract_first()
            all_td1_text += td1_text
        if query_string(self.project_name, all_td1_text) and query_string(self.js_dw, all_td1_text):
            self.extract_format1()

        header_index = None  # indexes of headline keywords
        for i, tr in enumerate(trs):
            tr_text = tr.xpath('string(.)').extract_first()
            text = clean_blank(tr_text)
            if query_string(self.project_name, text):
                header_index = i
                break
        if header_index is None:
            return '受理提取失败(2)--未匹配到表头'

        project_name_index, site_index, js_dw_index, hp_dw_index = None, None, None, None
        header_text = trs[header_index].xpath(".//td").xpath("string(.)").extract()
        for i, text in enumerate(header_text):
            text = clean_blank(text)
            if query_string(self.project_name, text):
                project_name_index = i
                continue
            if query_string(self.site, text):
                site_index = i
                continue
            if query_string(self.js_dw, text):
                js_dw_index = i
                continue
            if query_string(self.hp_dw, text):
                hp_dw_index = i
                continue

        if project_name_index is None:
            return '受理提取失败(2)--未匹配到项目名称'

        data = []
        project_name, site, js_dw, hp_dw, msg, attachments = '', '', '', '', None, None
        for i, tr in enumerate(trs[header_index + 1:]):
            tds = tr.xpath(".//td")
            project_name = tds[project_name_index].xpath("string(.)").extract_first()
            if site_index is not None:
                site = tds[site_index].xpath("string(.)").extract_first()
            if js_dw_index is not None:
                js_dw = tds[js_dw_index].xpath("string(.)").extract_first()
            if hp_dw_index is not None:
                hp_dw = tds[hp_dw_index].xpath("string(.)").extract_first()
            if self.files:
                files = self.files
            else:
                files = tr.xpath('.//a[contains(@href, "/") or contains(@href, "?")]')
                if not files:
                    files = self.body.xpath('.//a[contains(@href, "/") or contains(@href, "?")]')
            if files:
                msg, attachments = get_files(self.response, files, len(trs[header_index + 1:]))
            d = {
                "project_name": project_name,
                "site": site,
                "js_dw": js_dw,
                "hp_dw": hp_dw,
                "msg": msg,
                "attachments": attachments
            }
            data.append(d)

        return data

    def extract_format3(self):
        '''
        Format No.3: All information is shown in an article. Probably there may be a table but anyway we need to deal with the article.
        Example site: http://www.hyx.gov.cn/zwgk/bmxxgkml/xhbj/tzgg_82867/201903/t20190327_2819615.html
        :return: str（error warnings） or [data]
        '''
        body_text = self.body.xpath('.').extract_first()
        body_text = body_text.replace('<br>', '</p><p>').replace('<b>', '<p>').replace('</b>', '</p>')
        paragraphs = Selector(text=body_text).xpath('.//p')
        if not paragraphs:
            return '受理提取失败(3)--无段落p标签'
        extract_paragraphs = [], [], [], []
        for p in paragraphs:
            p_text = p.xpath('string(.)').extract_first()
            text = clean_blank(p_text)
            if len(text) > 80:
                continue
            project_name = query_string(self.project_name, text)
            site = query_string(self.site, text)
            js_dw = query_string(self.js_dw, text)
            hp_dw = query_string(self.hp_dw, text)
            if project_name and text.index(project_name) < 5:
                extract_paragraphs[0].append((text, project_name))
                continue
            if site and text.index(site) < 5:
                extract_paragraphs[1].append((text, site))
                continue
            if js_dw and text.index(js_dw) < 5:
                extract_paragraphs[2].append((text, js_dw))
                continue
            if hp_dw and text.index(hp_dw) < 5:
                extract_paragraphs[3].append((text, hp_dw))
                continue

        data = []
        project_name, site, js_dw, hp_dw, msg, attachments = '', '', '', '', None, None
        project_names = extract_paragraphs[0]
        sites = extract_paragraphs[1]
        js_dws = extract_paragraphs[2]
        hp_dws = extract_paragraphs[3]

        if len(project_names) == 0:
            return '受理提取失败(3)--未匹配到项目名称'
        if len(project_names) == 1 and len(sites) > 0 and len(js_dws) > 0 :
            info = zip(project_names, sites, js_dws)
            if hp_dws:
                info = zip(project_names, sites, js_dws, hp_dws)
            for p in list(info):
                project_name = re.search('{string}[:：]*([\s\S]*)'.format(string=p[0][1]), p[0][0]).group(1)
                site = re.search('{string}[:：]*([\s\S]*)'.format(string=p[1][1]), p[1][0]).group(1)
                js_dw = re.search('{string}[:：]*([\s\S]*)'.format(string=p[2][1]), p[2][0]).group(1)
                if len(p) > 3:
                    hp_dw = re.search('{string}[:：]*([\s\S]*)'.format(string=p[3][1]), p[3][0]).group(1)
                if self.files:
                    files = self.files
                else:
                    files = self.body.xpath('.//a[contains(@href, "/") or contains(@href, "?")]')
                if files:
                    msg, attachments = get_files(self.response, files, len(list(info)))
                d = {
                    "project_name": project_name,
                    "site": site,
                    "js_dw": js_dw,
                    "hp_dw": hp_dw,
                    "msg": msg,
                    "attachments": attachments
                }
                data.append(d)
            return data

        elif len(project_names) > 1 and len(project_names) == len(sites) == len(js_dws):
            info = zip(project_names, sites, js_dws)
            if len(project_names) == len(hp_dws):
                info = zip(project_names, sites, js_dws, hp_dws)
            for p in list(info):
                project_name = re.search('{string}[:：]*([\s\S]*)'.format(string=p[0][1]), p[0][0]).group(1)
                site = re.search('{string}[:：]*([\s\S]*)'.format(string=p[1][1]), p[1][0]).group(1)
                js_dw = re.search('{string}[:：]*([\s\S]*)'.format(string=p[2][1]), p[2][0]).group(1)
                if len(p) > 3:
                    hp_dw = re.search('{string}[:：]*([\s\S]*)'.format(string=p[3][1]), p[3][0]).group(1)
                if self.files:
                    files = self.files
                else:
                    files = self.body.xpath('.//a[contains(@href, "/") or contains(@href, "?")]')
                if files:
                    msg, attachments = get_files(self.response, files, len(list(info)))
                d = {
                    "project_name": project_name,
                    "site": site,
                    "js_dw": js_dw,
                    "hp_dw": hp_dw,
                    "msg": msg,
                    "attachments": attachments
                }
                data.append(d)
            return data

        else:
            return '受理提取失败(3)--提取信息无法对应'


class NishenpiExtraction(Extraction):
    """For those cases which will be issued"""

    def __init__(self, body, response, files=None, project_name=None, site=None, js_dw=None, hp_dw=None, xm_gk=None,
                 yx_cs=None):
        super(NishenpiExtraction, self).__init__(body, response, files)
        self.project_name = PROJECT_NAME
        self.site = SITE
        self.js_dw = JS_DW
        self.hp_dw = HP_DW
        self.xm_gk = XM_GK
        self.yx_cs = YX_CS
        if project_name:
            self.project_name.append(project_name)
        if site:
            self.site.append(site)
        if js_dw:
            self.js_dw.append(js_dw)
        if hp_dw:
            self.hp_dw.append(hp_dw)
        if xm_gk:
            self.xm_gk.append(xm_gk)
        if yx_cs:
            self.yx_cs.append(yx_cs)

    def extract_format1(self):
        """
        Format No.1: A two-column table, one piece of information
        Example site: http://sthjj.hengyang.gov.cn/gsgg/201904/t20190425_2834279.html
        :return: str（error warnings） or [data]
        """
        if self.body.xpath('//th'):
            self.body = replace_th(self.body)
        table = self.body.xpath("descendant-or-self::table//tr[2]/td[2]/ancestor::table[1]")
        if len(table) > 1:
            return '拟审批提取失败(1)--多个表格'
        has_span = table.xpath('.//td/@rowspan') or table.xpath('.//td/@colspan')
        if has_span:
            table = split_span(table)

        project_name, site, js_dw, hp_dw, xm_gk, yx_cs, msg, attachments = '', '', '', '', '', '', None, None
        trs = table.xpath(".//td[2]/..")
        for tr in trs:
            tds = tr.xpath(".//td")
            if len(tds) < 2:
                continue
            td_text_list = tds.xpath("string(.)").extract()
            td1_text = td_text_list[0]
            text = clean_blank(td1_text)
            td2_text = td_text_list[1].strip()
            if query_string(self.project_name, text):
                project_name = td2_text
                continue
            if query_string(self.site, text):
                site = td2_text
                continue
            if query_string(self.js_dw, text, strict=True):
                js_dw = td2_text
                continue
            if query_string(self.hp_dw, text):
                hp_dw = td2_text
                continue
            if query_string(self.xm_gk, text):
                xm_gk = td2_text
                continue
            if query_string(self.yx_cs, text):
                yx_cs = td2_text
                continue

        if not project_name:
            return '拟审批提取失败(1)--未匹配到项目名称'

        # extract the attachments
        if self.files:
            files = self.files
        else:
            files = table.xpath('.//a[contains(@href, "/") or contains(@href, "?")]')
            if not files:
                files = self.body.xpath('.//a[contains(@href, "/") or contains(@href, "?")]')
        if files:
            msg, attachments = get_files(self.response, files, 1)
        data = {
            "project_name": project_name,
            "site": site,
            "js_dw": js_dw,
            "hp_dw": hp_dw,
            "xm_gk": xm_gk,
            "yx_cs": yx_cs,
            "msg": msg,
            "attachments": attachments
        }
        return [data]

    def extract_format2(self):
        """
        Format No.2: A table with more than 2 columns,probably more than 2 row as well. So it could cantain more than one piece of information.
        Example site: http://www.hyx.gov.cn/zwgk/bmxxgkml/xhbj/tzgg_82867/201903/t20190327_2819615.html
        :return: str（error warnings） or [data]
        """
        if self.body.xpath('//th'):
            self.body = replace_th(self.body)
        table = self.body.xpath("descendant-or-self::table//tr[2]/td[2]/ancestor::table[1]")
        if len(table) > 1:
            return '拟审批提取失败(1)--多个表格'
        has_span = table.xpath('.//td/@rowspan') or table.xpath('.//td/@colspan')
        if has_span:
            table = split_span(table)

        trs = table.xpath(".//td[2]/..")
        all_td1_text = ''
        for i, tr in enumerate(trs):
            td1_text = tr.xpath('string(./td[1])').extract_first()
            all_td1_text += td1_text
        if query_string(self.project_name, all_td1_text) and query_string(self.js_dw, all_td1_text):
            self.extract_format1()
            
        header_index = None  
        for i, tr in enumerate(trs):
            tr_text = tr.xpath('string(.)').extract_first()
            text = clean_blank(tr_text)
            if query_string(self.project_name, text):
                header_index = i
                break
        if header_index is None:
            return '拟审批提取失败(2)--未匹配到表头'

        project_name_index, site_index, js_dw_index, hp_dw_index, xm_gk_index, yx_cs_index = None, None, None, None, None, None
        header_text = trs[header_index].xpath(".//td").xpath("string(.)").extract()
        for i, text in enumerate(header_text):
            text = clean_blank(text)
            if query_string(self.project_name, text):
                project_name_index = i
                continue
            if query_string(self.site, text):
                site_index = i
                continue
            if query_string(self.js_dw, text, strict=True):
                js_dw_index = i
                continue
            if query_string(self.hp_dw, text):
                hp_dw_index = i
                continue
            if query_string(self.xm_gk, text):
                xm_gk_index = i
                continue
            if query_string(self.yx_cs, text):
                yx_cs_index = i
                continue

        if project_name_index is None:
            return '拟审批提取失败(2)--未匹配到项目名称'
        
        data = []
        project_name, site, js_dw, hp_dw, xm_gk, yx_cs, msg, attachments = '', '', '', '', '', '', None, None
        for i, tr in enumerate(trs[header_index + 1:]):
            tds = tr.xpath(".//td")
            project_name = tds[project_name_index].xpath("string(.)").extract_first()
            if site_index is not None:
                site = tds[site_index].xpath("string(.)").extract_first()
            if js_dw_index is not None:
                js_dw = tds[js_dw_index].xpath("string(.)").extract_first()
            if hp_dw_index is not None:
                hp_dw = tds[hp_dw_index].xpath("string(.)").extract_first()
            if xm_gk_index is not None:
                xm_gk = tds[xm_gk_index].xpath("string(.)").extract_first()
            if yx_cs_index is not None:
                yx_cs = tds[yx_cs_index].xpath("string(.)").extract_first()

            if self.files:
                files = self.files
            else:
                files = tr.xpath('.//a[contains(@href, "/") or contains(@href, "?")]')
                if not files:
                    files = self.body.xpath('.//a[contains(@href, "/") or contains(@href, "?")]')
            if files:
                msg, attachments = get_files(self.response, files, len(trs[header_index + 1:]))
            d = {
                "project_name": project_name,
                "site": site,
                "js_dw": js_dw,
                "hp_dw": hp_dw,
                "xm_gk": xm_gk,
                "yx_cs": yx_cs,
                "msg": msg,
                "attachments": attachments
            }
            data.append(d)

        return data

    def extract_format3(self):
        '''
        Format No.3: article
        example site: http://www.hyx.gov.cn/zwgk/bmxxgkml/xhbj/tzgg_82867/201903/t20190327_2819615.html
        :return: str（error warnings） or [data]
        '''
        body_text = self.body.xpath('.').extract_first()
        body_text = body_text.replace('<br>', '</p><p>').replace('<b>', '<p>').replace('</b>', '</p>')
        paragraphs = Selector(text=body_text).xpath('.//p')
        if not paragraphs:
            return '拟审批提取失败(3)--无段落p标签'

        extract_paragraphs = [], [], [], [], [], []
        for p in paragraphs:
            p_text = p.xpath('string(.)').extract_first()
            text = clean_blank(p_text)
            if len(text) > 80:
                continue
            project_name = query_string(self.project_name, text)
            site = query_string(self.site, text)
            js_dw = query_string(self.js_dw, text)
            hp_dw = query_string(self.hp_dw, text)
            if project_name and text.index(project_name) < 5:
                extract_paragraphs[0].append((text, project_name))
                continue
            if site and text.index(site) < 5:
                extract_paragraphs[1].append((text, site))
                continue
            if js_dw and text.index(js_dw) < 5:
                extract_paragraphs[2].append((text, js_dw))
                continue
            if hp_dw and text.index(hp_dw) < 5:
                extract_paragraphs[3].append((text, hp_dw))
                continue

        data = []
        project_name, site, js_dw, hp_dw, xm_gk, yx_cs, msg, attachments = '', '', '', '', '', '', None, None
        project_names = extract_paragraphs[0]
        sites = extract_paragraphs[1]
        js_dws = extract_paragraphs[2]
        hp_dws = extract_paragraphs[3]
        if len(project_names) == 0:
            return '拟审批提取失败(3)--未匹配到项目名称'
        if len(project_names) == 1 and len(sites) > 0 and len(js_dws) > 0:
            info = zip(project_names, sites, js_dws)
            if hp_dws:
                info = zip(project_names, sites, js_dws, hp_dws)
            for p in list(info):
                project_name = re.search('{string}[:：]*([\s\S]*)'.format(string=p[0][1]), p[0][0]).group(1)
                site = re.search('{string}[:：]*([\s\S]*)'.format(string=p[1][1]), p[1][0]).group(1)
                js_dw = re.search('{string}[:：]*([\s\S]*)'.format(string=p[2][1]), p[2][0]).group(1)
                if len(p) > 3:
                    hp_dw = re.search('{string}[:：]*([\s\S]*)'.format(string=p[3][1]), p[3][0]).group(1)
                if self.files:
                    files = self.files
                else:
                    files = self.body.xpath('.//a[contains(@href, "/") or contains(@href, "?")]')
                if files:
                    msg, attachments = get_files(self.response, files, 1)
                d = {
                    "project_name": project_name,
                    "site": site,
                    "js_dw": js_dw,
                    "hp_dw": hp_dw,
                    "xm_gk": xm_gk,
                    "yx_cs": yx_cs,
                    "msg": msg,
                    "attachments": attachments
                }
                data.append(d)
            return data

        elif len(project_names) > 1 and len(project_names) == len(sites) == len(js_dws):
            info = zip(project_names, sites, js_dws)
            if len(project_names) == len(hp_dws):
                info = zip(project_names, sites, js_dws, hp_dws)
            for p in list(info):
                project_name = re.search('{string}[:：]*([\s\S]*)'.format(string=p[0][1]), p[0][0]).group(1)
                site = re.search('{string}[:：]*([\s\S]*)'.format(string=p[1][1]), p[1][0]).group(1)
                js_dw = re.search('{string}[:：]*([\s\S]*)'.format(string=p[2][1]), p[2][0]).group(1)
                if len(p) > 3:
                    hp_dw = re.search('{string}[:：]*([\s\S]*)'.format(string=p[3][1]), p[3][0]).group(1)
                if self.files:
                    files = self.files
                else:
                    files = self.body.xpath('.//a[contains(@href, "/") or contains(@href, "?")]')
                if files:
                    msg, attachments = get_files(self.response, files, len(list(info)))
                d = {
                    "project_name": project_name,
                    "site": site,
                    "js_dw": js_dw,
                    "hp_dw": hp_dw,
                    "xm_gk": xm_gk,
                    "yx_cs": yx_cs,
                    "msg": msg,
                    "attachments": attachments
                }
                data.append(d)
            return data

        else:
            return '拟审批提取失败(3)--提取信息无法对应'


class ShenpiExtraction(Extraction):
    """For issue decision section"""

    def __init__(self, body, response, files=None, project_name=None, js_dw=None, pf_num=None, pf_time=None):
        super(ShenpiExtraction, self).__init__(body, response, files)
        self.project_name = PROJECT_NAME
        self.js_dw = JS_DW
        self.pf_num = PF_NUM
        self.pf_time = PF_TIME
        if project_name:
            self.project_name.append(project_name)
        if js_dw:
            self.js_dw.append(js_dw)
        if pf_num:
            self.pf_num.append(pf_num)
        if pf_time:
            self.pf_time.append(pf_time)

    def extract_format1(self):
        """
        Format No.1: two-column table
        Example:http://www.hengshan.gov.cn/xxgk/glgk/hjbh/xmhp/201904/t20190426_2835050.html
        :return: str（error warnings） or [data]
        """
        if self.body.xpath('//th'):
            self.body = replace_th(self.body)
        table = self.body.xpath("descendant-or-self::table//tr[2]/td[2]/ancestor::table[1]")
        if len(table) > 1:
            return '审批提取失败(1)--多个表格'
        has_span = table.xpath('.//td/@rowspan') or table.xpath('.//td/@colspan')
        if has_span:
            table = split_span(table)

        project_name, pf_num, js_dw, pf_time, msg, attachments = '', '', '', '', None, None
        trs = table.xpath(".//td[2]/..")
        for tr in trs:
            tds = tr.xpath(".//td")
            if len(tds) < 2:
                continue
            td_text_list = tds.xpath("string(.)").extract()
            td1_text = td_text_list[0]
            text = clean_blank(td1_text)
            td2_text = td_text_list[1].strip()
            if query_string(self.project_name, text):
                project_name = td2_text
                continue
            if query_string(self.pf_num, text):
                pf_num = td2_text
                continue
            if query_string(self.pf_time, text):
                pf_time = td2_text
                continue
            if query_string(self.js_dw, text):
                js_dw = td2_text
                continue
        if not project_name:
            return '审批提取失败(1)--未匹配到项目名称'
        # attachment extraction
        if self.files:
            files = self.files
        else:
            files = table.xpath('.//a[contains(@href, "/") or contains(@href, "?")]')
            if not files:
                files = self.body.xpath('.//a[contains(@href, "/") or contains(@href, "?")]')
        if files:
            msg, attachments = get_files(self.response, files, 1)
        data = {
            "project_name": project_name,
            "js_dw": js_dw,
            "pf_num": pf_num,
            "pf_time": pf_time,
            "msg": msg,
            "attachments": attachments
        }
        return [data]

    def extract_format2(self):
        """
        Format No.2: Multi-column table
        example site:http://sthjj.hengyang.gov.cn/gsgg/201812/t20181204_2728278.html
        :return: str（error warnings） or [data]
        """
        if self.body.xpath('//th'):
            self.body = replace_th(self.body)
        table = self.body.xpath("descendant-or-self::table//tr[2]/td[2]/ancestor::table[1]")
        if len(table) > 1:
            return '审批提取失败(1)--多个表格'
        has_span = table.xpath('.//td/@rowspan') or table.xpath('.//td/@colspan')
        if has_span:
            table = split_span(table)

        trs = table.xpath(".//td[2]/..")
        all_td1_text = ''
        for i, tr in enumerate(trs):
            td1_text = tr.xpath('string(./td[1])').extract_first()
            all_td1_text += td1_text
        if query_string(self.project_name, all_td1_text) and query_string(self.pf_num, all_td1_text):
            self.extract_format1()

        # acquire the indexes of headline keywords
        header_index = None
        for i, tr in enumerate(trs):
            tr_text = tr.xpath('string(.)').extract_first()
            text = clean_blank(tr_text)
            if query_string(self.project_name, text):
                header_index = i
                break
        if header_index is None:
            return '审批提取失败(2)--未匹配到表头'

        # respective column indexes
        project_name_index, js_dw_index, pf_num_index, pf_time_index, = None, None, None, None
        header_text = trs[header_index].xpath(".//td").xpath("string(.)").extract()
        for i, text in enumerate(header_text):
            text = clean_blank(text)
            if query_string(self.project_name, text):
                project_name_index = i
                continue
            if query_string(self.pf_num, text):
                pf_num_index = i
                continue
            if query_string(self.pf_time, text):
                pf_time_index = i
                continue
            if query_string(self.js_dw, text):
                js_dw_index = i
                continue

        if project_name_index is None:
            return '审批提取失败(2)--未匹配到项目名称'

        data = []
        project_name, js_dw, pf_num, pf_time, msg, attachments = '', '', '', '', None, None
        for tr in trs[header_index + 1:]:
            tds = tr.xpath(".//td")
            if project_name_index is not None:
                project_name = tds[project_name_index].xpath("string(.)").extract_first()
            if pf_num_index is not None:
                pf_num = tds[pf_num_index].xpath("string(.)").extract_first()
            if pf_time_index is not None:
                pf_time = tds[pf_time_index].xpath("string(.)").extract_first()
            if js_dw_index is not None:
                js_dw = tds[js_dw_index].xpath("string(.)").extract_first()

            # extract attachments
            if self.files:
                files = self.files
            else:
                files = tr.xpath('.//a[contains(@href, "/") or contains(@href, "?")]')
                if not files:
                    files = self.body.xpath('.//a[contains(@href, "/") or contains(@href, "?")]')
            if files:
                msg, attachments = get_files(self.response, files, len(trs[header_index + 1:]))
            d = {
                "project_name": project_name,
                "js_dw": js_dw,
                "pf_num": pf_num,
                "pf_time": pf_time,
                "msg": msg,
                "attachments": attachments
            }
            data.append(d)

        return data

    def extract_format3(self):
        '''
        Format No.3: article
        Example site: http://www.hyx.gov.cn/zwgk/bmxxgkml/xhbj/tzgg_82867/201903/t20190327_2819615.html
        :return: str（error warnings） or [data]
        '''
        body_text = self.body.xpath('.').extract_first()
        body_text = body_text.replace('<br>', '</p><p>').replace('<b>', '<p>').replace('</b>', '</p>')
        paragraphs = Selector(text=body_text).xpath('.//p')
        if not paragraphs:
            return '审批提取失败(3)--无段落p标签'

        extract_paragraphs = [], [], [], []
        for p in paragraphs:
            p_text = p.xpath('string(.)').extract_first()
            text = clean_blank(p_text)
            if len(text) > 80:
                continue
            project_name = query_string(self.project_name, text)
            js_dw = query_string(self.js_dw, text)
            pf_time = query_string(self.pf_time, text)
            pf_num = query_string(self.pf_num, text)
            if project_name and text.index(project_name) < 5:
                extract_paragraphs[0].append((text, project_name))
                continue
            if js_dw and text.index(js_dw) < 5:
                extract_paragraphs[1].append((text, js_dw))
                continue
            if pf_time and text.index(pf_time) < 5:
                extract_paragraphs[2].append((text, pf_time))
                continue
            if pf_num and text.index(pf_num) < 5:
                extract_paragraphs[3].append((text, pf_num))
                continue

        data = []
        project_name, js_dw, pf_num, pf_time, msg, attachments = '', '', '', '', None, None
        project_names = extract_paragraphs[0]
        js_dws = extract_paragraphs[1]
        pf_times = extract_paragraphs[2]
        pf_nums = extract_paragraphs[3]

        if len(project_names) == 0:
            return '审批提取失败(3)--未匹配到项目名称'
        if len(project_names) == 1 and len(pf_nums) > 0:
            info = zip(project_names, pf_nums)
            if pf_times and js_dws:
                info = zip(project_names, pf_nums, pf_times, js_dws)
            elif pf_times:
                info = zip(project_names, pf_nums, pf_times)

            for p in list(info):
                project_name = re.search('{string}[:：]*([\s\S]*)'.format(string=p[0][1]), p[0][0]).group(1)
                pf_num = re.search('{string}[:：]*([\s\S]*)'.format(string=p[1][1]), p[1][0]).group(1)
                if len(p) > 2:
                    pf_time = re.search('{string}[:：]*([\s\S]*)'.format(string=p[2][1]), p[2][0]).group(1)
                if len(p) > 3:
                    js_dw = re.search('{string}[:：]*([\s\S]*)'.format(string=p[3][1]), p[3][0]).group(1)

                if self.files:
                    files = self.files
                else:
                    files = self.body.xpath('.//a[contains(@href, "/") or contains(@href, "?")]')
                if files:
                    msg, attachments = get_files(self.response, files, 1)
                d = {
                    "project_name": project_name,
                    "js_dw": js_dw,
                    "pf_num": pf_num,
                    "pf_time": pf_time,
                    "msg": msg,
                    "attachments": attachments
                }
                data.append(d)
            return data

        elif len(project_names) > 1 and len(project_names) == len(pf_nums):
            info = zip(project_names, pf_nums)
            if len(project_names) == len(pf_times) and len(project_names) == len(js_dws):
                info = zip(project_names, pf_nums, pf_times, js_dws)
            elif len(project_names) == len(pf_times):
                info = zip(project_names, pf_nums, pf_times)

            for p in list(info):
                project_name = re.search('{string}[:：]*([\s\S]*)'.format(string=p[0][1]), p[0][0]).group(1)
                pf_num = re.search('{string}[:：]*([\s\S]*)'.format(string=p[1][1]), p[1][0]).group(1)
                if len(p) > 2:
                    pf_time = re.search('{string}[:：]*([\s\S]*)'.format(string=p[2][1]), p[2][0]).group(1)
                if len(p) > 3:
                    js_dw = re.search('{string}[:：]*([\s\S]*)'.format(string=p[3][1]), p[3][0]).group(1)

                if self.files:
                    files = self.files
                else:
                    files = self.body.xpath('.//a[contains(@href, "/") or contains(@href, "?")]')
                if files:
                    msg, attachments = get_files(self.response, files, 1)
                d = {
                    "project_name": project_name,
                    "js_dw": js_dw,
                    "pf_num": pf_num,
                    "pf_time": pf_time,
                    "msg": msg,
                    "attachments": attachments
                }
                data.append(d)
            return data

        else:
            return '审批提取失败(3)--提取信息无法对应'


def estimate_gs_type(title, body):
    """
    When we couldn't distinguish what kind of notice the article is according to the title, we identify based on the article content.
    Like what we did before we still judged them according to the appearance of certain groups of keywords
    :param body: class Selector, containing all the text
    :param title: class Selector, containing the text of the title
    :return: None or '受理','拟审批','审批'
    """

    body_text = body.xpath("string(.)").extract_first()
    body_text = clean_blank(body_text)
    if '受理' in title and ('环评' in title or '环境影响' in title):
        gs_type = '受理'
    elif ('拟' in title or '审批前' in title or '审查前' in title or
          '批复前' in title) and ('环评' in title or '环境影响' in title):
        gs_type = '拟审批'
    elif ('审批' in title or '批复' in title) and ('环评' in title or '环境影响' in title):
        gs_type = '审批'
    else:
        # 无法通过标题判断公示类型, 则通过内容来判断
        if ('受理' in body_text) and ('环评' in body_text or '环境影响' in body_text) and ('文号' not in body_text):
            gs_type = '受理'
        elif ('拟' in body_text or '审批前' in body_text or '审查前' in body_text or '批复前' in body_text) and (
                '环评' in body_text or '环境影响' in body_text):
            gs_type = '拟审批'
        elif ('文号' in body_text or '批复' in body_text) and ('环评' in body_text or '环境影响' in body_text):
            gs_type = '审批'
        else:
            gs_type = None

    return gs_type
