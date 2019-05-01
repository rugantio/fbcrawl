# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.exceptions import DropItem
from datetime import datetime
from fbcrawl.exporters import TCPExports
import logging

class FbcrawlPipeline(object):
    # def __init__(self, file_name):
    def __init__(self):
        # this is an empty initialization  for the exporter 
        self.exporter = lambda: None


    @classmethod
    def from_crawler(cls, crawler):
        # getting the value of FILE_NAME field from settings.py if needed 
        output_file_name = crawler.settings.get('FILE_NAME')
        return cls()

    def open_spider(spider,self):
        #Specifying target exporter 
        self.exporter = TCPExports()
        self.exporter.start_exporting()

    def close_spider(spider,self):
        # Ending the export 
        self.exporter.finish_exporting()

        # Closing the opened output file
        # self.file_handle.close()

    def process_item(self, item, spider):
        # passing the item to FanItemExporter object for expoting to file
        if item["text"]:
            spider.exporter.export_item(item["text"])
        return item
