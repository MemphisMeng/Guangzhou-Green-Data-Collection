# -*- coding: utf-8 -*-

import scrapy


class HpspiderItem(scrapy.Item):
    project_name = scrapy.Field()   # 项目名称
    gs_type = scrapy.Field()        # 公示类型
    date_time = scrapy.Field()      # 发布时间
    province = scrapy.Field()       # 省
    city = scrapy.Field()           # 市
    ##
    remark = scrapy.Field()         # 备注 如果没有为空
    status = scrapy.Field()         # 默认填0

    source_url = scrapy.Field()      # 来源链接
    sp_bm = scrapy.Field()           # 审批部门
    sp_dh = scrapy.Field()           # 审批部门联系方式
    hp_type = scrapy.Field()         # 环评文件类型
    js_dw = scrapy.Field()           # 建设单位
    hp_dw = scrapy.Field()           # 环评单位
    site = scrapy.Field()            # 建设地点
    xm_gk = scrapy.Field()           # 项目概况
    yx_cs = scrapy.Field()           # 主要环境影响及环保措施
    gc_qk = scrapy.Field()           # 公众参与情况
    bg_url = scrapy.Field()          # 环评报告链接
    gc_url = scrapy.Field()          # 公参说明链接
    pf_url = scrapy.Field()          # 环评批复链接
    pf_content = scrapy.Field()      # 环评批复内容
    pf_num = scrapy.Field()          # 环评批复文号
    pf_time = scrapy.Field()         # 环评批复时间
    non_sp = scrapy.Field()          # 不批准

    source_webname = scrapy.Field()  # 来源网站名称
    problem_url = scrapy.Field()     # 有问题的链接
    error_info = scrapy.Field()      # 错误信息
    p_status = scrapy.Field()        # 是否处理过
    p_type = scrapy.Field()          # 公示类型
    p_content = scrapy.Field()       # 网页内容
    p_province = scrapy.Field()      # 省
    p_city = scrapy.Field()          # 市
    p_approval = scrapy.Field()      # 审批部门



