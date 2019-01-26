# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader.processors import TakeFirst, Join, MapCompose
from datetime import datetime, timedelta

def parse_date(date):
    mesi = {
    'gennaio':1,
    'febbraio':2,
    'marzo':3,
    'aprile':4,
    'maggio':5,
    'giugno':6,
    'luglio':7,
    'agosto':8,
    'settembre':9,
    'ottobre':10,
    'novembre':11,
    'dicembre':12
    }

    mesi_abbr = {
    'gen':1,
    'feb':2,
    'mar':3,
    'apr':4,
    'mag':5,
    'giu':6,
    'lug':7,
    'ago':8,
    'set':9,
    'ott':10,
    'nov':11,
    'dic':12
    }    
    
    giorni = {
    'domenica':0,
    'lunedì':1,
    'martedì':2,
    'mercoledì':3,
    'giovedì':4,
    'venerdì':5,
    'sabato':6
    }    
    
    date = date[0].split()
    year, month, day = [int(i) for i in str(datetime.now().date()).split(sep='-')] #default is today
    
    # things to match:
    #
    #Ieri alle 2:10
    #Adesso
    #5 h
    #21 giu
    #29 mag alle 13:21
    #12 luglio 2018
    #17 dicembre alle ore 17:31 
    #21 dicembre 2011 alle ore 17:31 
    #lunedì alle 10:01
    
    #try:
        #day = int(date[0])
    #except ValueError:
        #string = str(date[0])
        
    #sanity check
    if len(date) == 0:
        return 'Error: no data'
    
    #no check for today
    #elif len(date) == 1 or date[1] == 'h':
        #pass
    
    #yesterday
    elif date[0] == 'Ieri' or (date[1] == 'h' and int(str(datetime.now().time()).split(sep=':')[0]) - int(date[0]) < 0):
        day = int(str(datetime.now().date()-timedelta(1)).split(sep='-')[2])
        
    #day with 3 month length of this year
    elif (len(date) == 2 or len(date) == 3 or len(date) == 4) and len(date[1]) == 3:
        day = int(date[0])
        month = mesi_abbr[date[1]]
        
    #day of this year
    elif date[0].isdigit() and date[2] == 'alle':
        day = int(date[0])
        month = mesi[date[1]]
    
    #usual dates, with regular length month 
    elif date[0].isdigit() and date[2].isdigit():
        day = int(date[0])
        month = mesi[date[1]]
        year = int(date[2])

    #dates with weekdays (this function assumes that the month is the same)
    elif date[0].isdigit() == False and date[1].isdigit() == False:
        today = datetime.now().weekday() #today as a weekday
        weekday = giorni[date[0]]   #day to be match as number weekday
        #weekday is chronologically always lower than day
        if weekday < today:
            day -= today - weekday 
        elif weekday > today:
            weekday += 7 
            day -= today - weekday
    else:
    #date item parser fail. datetime format unknown, check xpath selector or change the language of the interface'
        return 'Error date:{}'.format(date)
    date = datetime(year,month,day)
    return date.date()

def comments_strip(string):
    return string[0].rstrip(' commenti')

def reactions_strip(string):
    friends = 1 + string[0].count(',')
    e = 1 + string[0].count(' e ')
    string = string[0].split()[::-1]
    if len(string) == 1:
        string = string[0]
        while string.rfind('.') != -1:
            string = string[0:string.rfind('.')] + string[string.rfind('.')+1:]
        return string

    string = string[0]
    while string.rfind('.') != -1:
        string = string[0:string.rfind('.')] + string[string.rfind('.')+1:]
    
    if not string.isdigit():
        return e
    else:
        return int(string) + friends

class FbcrawlItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    source = scrapy.Field(
            output_processor=TakeFirst()
    )                     # page that published the post

    date = scrapy.Field(      # when was the post published
            input_processor=TakeFirst(),
            output_processor=parse_date
    )       
                                    
    text = scrapy.Field(
            output_processor=Join(separator=u'')
    )                       # full text of the post

    comments = scrapy.Field(
            output_processor=comments_strip
    )                       
    commentators = scrapy.Field(
            output_processor=Join(separator=u'\n')
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
    url = scrapy.Field()
