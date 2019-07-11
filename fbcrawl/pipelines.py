# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy.exceptions import DropItem
from postgres.models import Post, Group
from postgres.settings import postgres_database
from datetime import datetime
import shortuuid

class FbcrawlPipeline(object):
    pass
#    def process_item(self, item, spider):
#        if item['date'] < datetime(2017,1,1).date():
#            raise DropItem("Dropping element because it's older than 01/01/2017")
#        elif item['date'] > datetime(2018,3,4).date():
#            raise DropItem("Dropping element because it's newer than 04/03/2018")
#        else:
#            return item

class PostgresPostPipeline(object):

   def process_item(self, item, spider):
        success = True
        if len(item['source']) < 2:
            raise DropItem("Dropping element because doesnt have a source name")
        if 'date' in item and len(item['date']) == 0:
            raise DropItem("No date found")
        if 'text' not in item:
            raise DropItem("Do not have or do not contain any valid text")
        if len(item['text']) < 10:
            raise DropItem("Incomplete info")
        try:
            with postgres_database.atomic():
                if len(item['source'][1]) > 0 and len(Group.select().where(Group.name == item['source'][1]) ) == 0:
                    Group.create(
                        uuid=str(shortuuid.uuid())[:20],
                        name=item['source'][1]
                    )
                post = Post.create(
                        post_id=item['post_id'],
                        source=item['source'][0],
                        text=item['text'],
                        shared_in=item['source'][1],
                        url=item['url'],
                        date=item['date'][0],
                        reactions = item['reactions'] if 'reactions' in item and item['reactions'] else 0,
                        likes = item['likes'] if 'likes' in item and item['likes'] else 0,
                        ahah = item['ahah'] if 'ahah' in item and item['ahah'] else 0,
                        love = item['love'] if 'love' in item and item['love'] else 0,
                        wow = item['wow'] if 'wow' in item and item['wow'] else 0,
                        sigh = item['sigh'] if 'sigh' in item and item['sigh'] else 0,
                        grr = item['grrr'] if 'grrr' in item and item['grrr'] else 0,
                        comment_count = item['comments'] if 'comments' in item and item['comments'] else 0)
        except BaseException as e:
            raise DropItem("Exception : {}".format(str(e)))
        return item