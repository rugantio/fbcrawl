# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader.processors import TakeFirst, Join, MapCompose
from datetime import datetime, timedelta
    
def comments_strip(string,loader_context):
    lang = loader_context['lang']
    if lang == 'it':
        if string[0].rfind('Commenta') != -1:
            return
        else:
            return string[0].rstrip(' commenti')
        
    elif lang == 'en':
        if(string[0] == 'Share'):
            return '0'
        new_string = string[0].rstrip(' Comments')
        while new_string.rfind(',') != -1:
            new_string = new_string[0:new_string.rfind(',')] + new_string[new_string.rfind(',')+1:]
        return new_string
    else:
        return string

def reactions_strip(string,loader_context):
    lang = loader_context['lang']
    if lang == 'it':
        newstring = string[0]
        #19.298.873       
        if len(newstring.split()) == 1:
            while newstring.rfind('.') != -1:
                newstring = newstring[0:newstring.rfind('.')] + newstring[newstring.rfind('.')+1:]
            return newstring
        #Pamela, Luigi e altri 4
        else:   
            return string
            friends = newstring.count(' e ') + newstring.count(',')
            newstring = newstring.split()[::-1][0]
            while newstring.rfind('.') != -1:
                newstring = newstring[0:newstring.rfind('.')] + newstring[newstring.rfind('.')+1:]
            return int(newstring) + friends
    elif lang == 'en':
        newstring = string[0]
        #19,298,873       
        if len(newstring.split()) == 1:
            while newstring.rfind(',') != -1:
                newstring = newstring[0:newstring.rfind(',')] + newstring[newstring.rfind(',')+1:]
            return newstring
#        #Mark and other 254,134 
#        elif newstring.split()[::-1][1].isdigit(): 
#            friends = newstring.count(' and ') + newstring.count(',')
#            newstring = newstring.split()[::-1][1]
#            while newstring.rfind(',') != -1:
#                newstring = newstring[0:newstring.rfind(',')] + newstring[newstring.rfind(',')+1:]
#            return int(newstring) + friends
#        #Philip and 1K others
        else:
            return newstring
    else:
        return string

def url_strip(url):
    fullurl = url[0]
    #catchin '&id=' is enough to identify the post
    i = fullurl.find('&id=')
    if i != -1:
        return fullurl[:i+4] + fullurl[i+4:].split('&')[0]
    else:  #catch photos   
        i = fullurl.find('/photos/')
        if i != -1:
            return fullurl[:i+8] + fullurl[i+8:].split('/?')[0]
        else: #catch albums
            i = fullurl.find('/albums/')
            if i != -1:
                return fullurl[:i+8] + fullurl[i+8:].split('/?')[0]
            else:
                return fullurl
    
def parse_date(date):
    import json
        
    d = json.loads(date[0]) #nested dict of features
    flat_d = dict() #only retain 'leaves' of d tree
    
    def recursive_items(dictionary):
        '''
        Get most nested key:value pair of nested dict
        '''
        for key, value in dictionary.items():
            if type(value) is dict:
                yield from recursive_items(value)
            else:
                yield (key, value)

    for key, value in recursive_items(d):
        flat_d[key] = value

    #returns timestamp in localtime conversion from linux timestamp UTC
    return str(datetime.fromtimestamp(flat_d['publish_time']))  
    
def id_strip(post_id):
    import json
    d = json.loads(post_id[::-1][0]) #nested dict of features
    return str(d['top_level_post_id'])
    

class FbcrawlItem(scrapy.Item):
    source = scrapy.Field()   
    date = scrapy.Field()       
    text = scrapy.Field(
        output_processor=Join(separator=u'')
    )                       # full text of the post
    comments = scrapy.Field(
        output_processor=comments_strip
    )                                       
    reactions = scrapy.Field(
        output_processor=reactions_strip
    )                  # num of reactions
    likes = scrapy.Field(
        output_processor=reactions_strip
    )                      
    ahah = scrapy.Field()                      
    love = scrapy.Field()                      
    wow = scrapy.Field()                      
    sigh = scrapy.Field()                      
    grrr = scrapy.Field()                      
    share = scrapy.Field()                      # num of shares
    url = scrapy.Field(
        output_processor=url_strip
    )
    post_id = scrapy.Field(
        output_processor=id_strip
    )
    shared_from = scrapy.Field()

class CommentsItem(scrapy.Item):
    source = scrapy.Field()   
    reply_to=scrapy.Field()
    date = scrapy.Field(      # when was the post published
        output_processor=parse_date
    )       
    text = scrapy.Field(
        output_processor=Join(separator=u'')
    )                       # full text of the post
    reactions = scrapy.Field(
        output_processor=reactions_strip
    )                  # num of reactions
    likes = scrapy.Field(
        output_processor=reactions_strip
    )                      
    source_url = scrapy.Field()                      
    url = scrapy.Field()
    #ahah = scrapy.Field()                      
    #love = scrapy.Field()                      
    #wow = scrapy.Field()                      
    #sigh = scrapy.Field()                      
    #grrr = scrapy.Field()                      
    #share = scrapy.Field()                      # num of shares
