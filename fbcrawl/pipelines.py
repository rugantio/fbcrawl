# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.exceptions import DropItem
from datetime import datetime

class FbcrawlPipeline(object):
    pass
#    def process_item(self, item, spider):
#        if item['date'] < datetime(2017,1,1).date():
#            raise DropItem("Dropping element because it's older than 01/01/2017")
#        elif item['date'] > datetime(2018,3,4).date():
#            raise DropItem("Dropping element because it's newer than 04/03/2018")
#        else:
#            return item
