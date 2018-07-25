# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader.processors import TakeFirst, Join

class FbcrawlItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    source = scrapy.Field()                     # page that published the post

    date = scrapy.Field(
            output_processor=TakeFirst()
    )       
                                    # when was the post published
    text = scrapy.Field(
            output_processor=Join(separator=u'')
    )                       # full text of the post

    comments = scrapy.Field(
            output_processor=Join(separator=u'\n')
    )                       # full text of the post
    commentators = scrapy.Field(
            output_processor=Join(separator=u'\n')
    )                       # full text of the post

    like = scrapy.Field()                       # num of likes
    share = scrapy.Field()                      # num of shares
    num_id = scrapy.Field()                     # progressive int associated to the entry in the final table, not present in the webpage
    
