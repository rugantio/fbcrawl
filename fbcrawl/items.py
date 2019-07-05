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
        #Mark and other 254,134
        elif newstring.split()[::-1][1].isdigit():
            friends = newstring.count(' and ') + newstring.count(',')
            newstring = newstring.split()[::-1][1]
            while newstring.rfind(',') != -1:
                newstring = newstring[0:newstring.rfind(',')] + newstring[newstring.rfind(',')+1:]
            return int(newstring) + friends
        #Philip and 1K others
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

def parse_date(date,loader_context):
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
    ret = str(datetime.fromtimestamp(flat_d['publish_time'])) if 'publish_time' in flat_d else None
    return ret

def parse_date2(init_date,loader_context):
    lang = loader_context['lang']
# =============================================================================
# Italian - status:final
# =============================================================================
    if lang == 'it':
        months = {
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

        months_abbr = {
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
        'lunedì':0,
        'martedì':1,
        'mercoledì':2,
        'giovedì':3,
        'venerdì':4,
        'sabato':5,
        'domenica':6
        }

        date = init_date[0].split()
        year, month, day = [int(i) for i in str(datetime.now().date()).split(sep='-')] #default is today

        l = len(date)

        #sanity check
        if l == 0:
            return 'Error: no data'

        #adesso, ieri, 4h, 50min
        elif l == 1:
            if date[0].isalpha():
                if date[0].lower() == 'ieri':
                    day = int(str(datetime.now().date()-timedelta(1)).split(sep='-')[2])
                    #check that yesterday was not in another month
                    month = int(str(datetime.now().date()-timedelta(1)).split(sep='-')[1])
                elif date[0].lower() == 'adesso':
                        return datetime(year,month,day).date()    #return today
                else:  #not recognized, (return date or init_date)
                    return date
            else:
                #4h, 50min (exploit future parsing)
                l = 2
                new_date = [x for x in date[0] if x.isdigit()]
                date[0] = ''.join(new_date)
                new_date = [x for x in date[0] if not(x.isdigit())]
                date[1] = ''.join(new_date)
# l = 2
        elif l == 2:
            #22 min (oggi)
            if date[1] == 'min':
                if int(str(datetime.now().time()).split(sep=':')[1]) - int(date[0]) >= 0:
                    return datetime(year,month,day).date()
                #22 min (ieri)
                else:
                    day = int(str(datetime.now().date()-timedelta(1)).split(sep='-')[2])
                    month = int(str(datetime.now().date()-timedelta(1)).split(sep='-')[1])
                    return datetime(year,month,day).date()
            #4 h (oggi)
            elif date[1] == 'h':
                if int(str(datetime.now().time()).split(sep=':')[0]) - int(date[0]) >= 0:
                    return datetime(year,month,day).date()
                #4 h (ieri)
                else:
                    day = int(str(datetime.now().date()-timedelta(1)).split(sep='-')[2])
                    month = int(str(datetime.now().date()-timedelta(1)).split(sep='-')[1])
                    return datetime(year,month,day).date()
            #2 gen
            elif len(date[1]) == 3 and date[1].isalpha():
                day = int(date[0])
                month = months_abbr[date[1].lower()]
                return datetime(year,month,day).date()
            #2 gennaio
            elif len(date[1]) > 3 and date[1].isalpha():
                day = int(date[0])
                month = months[date[1]]
                return datetime(year,month,day).date()
            #parsing failed
            else:
                return date
# l = 3
        elif l == 3:
            #21 giu 2017
            if len(date[1]) == 3 and date[2].isdigit():
                day = int(date[0])
                month = months_abbr[date[1]]
                year = int(date[2])
                return datetime(year,month,day).date()
            #21 giugno 2017
            elif len(date[1]) > 3 and date[2].isdigit():
                day = int(date[0])
                month = months[date[1]]
                year = int(date[2])
                return datetime(year,month,day).date()
            #9 ore fa
            elif date[0].isdigit() and date[1][:2] == 'or':
                if int(str(datetime.now().time()).split(sep=':')[0]) - int(date[0]) >= 0:
                    return datetime(year,month,day).date()
                #9 ore fa (ieri)
                else:
                    day = int(str(datetime.now().date()-timedelta(1)).split(sep='-')[2])
                    month = int(str(datetime.now().date()-timedelta(1)).split(sep='-')[1])
                    return datetime(year,month,day).date()
            #7 minuti fa
            elif date[0].isdigit() and date[1][:3] == 'min':
                return datetime(year,month,day).date()

            #ieri alle 20:45
            elif date[0].lower() == 'ieri' and date[1] == 'alle':
                day = int(str(datetime.now().date()-timedelta(1)).split(sep='-')[2])
                month = int(str(datetime.now().date()-timedelta(1)).split(sep='-')[1])
                return datetime(year,month,day).date()
            #oggi alle 11:11
            elif date[0].lower() == 'oggi' and date[1] == 'alle':
                return datetime(year,month,day).date()
            #lunedì alle 12:34
            elif date[0].isalpha() and date[1] == 'alle':
                today = datetime.now().weekday() #today as a weekday
                weekday = giorni[date[0].lower()]   #day to be match as number weekday
                #weekday is chronologically always lower than day
                delta = today - weekday
                if delta >= 0:
                    day = int(str(datetime.now().date()-timedelta(delta)).split(sep='-')[2])
                    month = int(str(datetime.now().date()-timedelta(delta)).split(sep='-')[1])
                    return datetime(year,month,day).date()
                #lunedì = 0 sabato = 6, mar 1 ven 5
                else:
                    delta += 8
                    day = int(str(datetime.now().date()-timedelta(delta)).split(sep='-')[2])
                    month = int(str(datetime.now().date()-timedelta(delta)).split(sep='-')[1])
                    return datetime(year,month,day).date()
            #parsing failed
            else:
                return date
# l = 4
        elif l == 4:
            #Ieri alle ore 23:32
            if date[0].lower() == 'ieri' and date[1] == 'alle':
                day = int(str(datetime.now().date()-timedelta(1)).split(sep='-')[2])
                month = int(str(datetime.now().date()-timedelta(1)).split(sep='-')[1])
                return datetime(year,month,day).date()
            #domenica alle ore 19:29
            elif date[0].isalpha() and date[1] == 'alle':
                today = datetime.now().weekday() #today as a weekday
                weekday = giorni[date[0].lower()]   #day to be match as number weekday
                #weekday is chronologically always lower than day
                delta = today - weekday
                if delta >= 0:
                    day = int(str(datetime.now().date()-timedelta(delta)).split(sep='-')[2])
                    month = int(str(datetime.now().date()-timedelta(delta)).split(sep='-')[1])
                    return datetime(year,month,day).date()
                #lunedì = 0 sabato = 6, mar 1 ven 5
                else:
                    delta += 8
                    day = int(str(datetime.now().date()-timedelta(delta)).split(sep='-')[2])
                    month = int(str(datetime.now().date()-timedelta(delta)).split(sep='-')[1])
                    return datetime(year,month,day).date()
            #parsing failed
            else:
                return date
# l = 5
        elif l == 5:
           if date[2] == 'alle':
               #29 feb alle ore 21:49
               if len(date[1]) == 3:
                   day = int(date[0])
                   month = months_abbr[date[1].lower()]
                   return datetime(year,month,day).date()
               #29 febbraio alle ore 21:49
               else:
                   day = int(date[0])
                   month = months[date[1].lower()]
                   return datetime(year,month,day).date()
           #parsing failed
           else:
               return date
# l = 6
        elif l == 6:
           if date[3] == 'alle':
               #29 feb 2016 alle ore 21:49
               if len(date[1]) == 3:
                   day = int(date[0])
                   month = months_abbr[date[1].lower()]
                   year = int(date[2])
                   return datetime(year,month,day).date()
               #29 febbraio 2016 alle ore 21:49
               else:
                   day = int(date[0])
                   month = months[date[1].lower()]
                   year = int(date[2])
                   return datetime(year,month,day).date()
           #parsing failed
           else:
               return date
# =============================================================================
# English - status:beta
# =============================================================================
    elif lang == 'en':
        months = {
        'january':1,
        'february':2,
        'march':3,
        'april':4,
        'may':5,
        'june':6,
        'july':7,
        'august':8,
        'september':9,
        'october':10,
        'november':11,
        'december':12
        }

        months_abbr = {
        'jan':1,
        'feb':2,
        'mar':3,
        'apr':4,
        'may':5,
        'jun':6,
        'jul':7,
        'aug':8,
        'sep':9,
        'oct':10,
        'nov':11,
        'dec':12
        }

        days = {
        'monday':0,
        'tuesday':1,
        'wednesday':2,
        'thursday':3,
        'friday':4,
        'saturday':5,
        'sunday':6
        }

        date = init_date[0].split()
        year, month, day = [int(i) for i in str(datetime.now().date()).split(sep='-')] #default is today

        l = len(date)

        #sanity check
        if l == 0:
            return 'Error: no data'

        #Yesterday, Now, 4hr, 50mins
        elif l == 1:
            if date[0].isalpha():
                if date[0].lower() == 'yesterday':
                    day = int(str(datetime.now().date()-timedelta(1)).split(sep='-')[2])
                    #check that yesterday was not in another month
                    month = int(str(datetime.now().date()-timedelta(1)).split(sep='-')[1])
                elif date[0].lower() == 'now':
                        return datetime(year,month,day).date()    #return today
                else:  #not recognized, (return date or init_date)
                    return date
            else:
                #4h, 50min (exploit future parsing)
                l = 2
                new_date = [x for x in date[0] if x.isdigit()]
                date[0] = ''.join(new_date)
                new_date = [x for x in date[0] if not(x.isdigit())]
                date[1] = ''.join(new_date)
# l = 2
        elif l == 2:
            if date[1] == 'now':
                return datetime(year,month,day).date()
            #22 min (ieri)
            if date[1] == 'min' or date[1] == 'mins':
                if int(str(datetime.now().time()).split(sep=':')[1]) - int(date[0]) < 0 and int(str(datetime.now().time()).split(sep=':')[0])==0:
                    day = int(str(datetime.now().date()-timedelta(1)).split(sep='-')[2])
                    month = int(str(datetime.now().date()-timedelta(1)).split(sep='-')[1])
                    return datetime(year,month,day).date()
                #22 min (oggi)
                else:
                    return datetime(year,month,day).date()

            #4 h (ieri)
            elif date[1] == 'hr' or date[1] == 'hrs':
                if int(str(datetime.now().time()).split(sep=':')[0]) - int(date[0]) < 0:
                    day = int(str(datetime.now().date()-timedelta(1)).split(sep='-')[2])
                    month = int(str(datetime.now().date()-timedelta(1)).split(sep='-')[1])
                    return datetime(year,month,day).date()
                #4 h (oggi)
                else:
                    return datetime(year,month,day).date()

            #2 jan
            elif len(date[1]) == 3 and date[1].isalpha():
                day = int(date[0])
                month = months_abbr[date[1].lower()]
                return datetime(year,month,day).date()
            #2 january
            elif len(date[1]) > 3 and date[1].isalpha():
                day = int(date[0])
                month = months[date[1]]
                return datetime(year,month,day).date()
            #jan 2
            elif len(date[0]) == 3 and date[0].isalpha():
                day = int(date[1])
                month = months_abbr[date[0].lower()]
                return datetime(year,month,day).date()
            #january 2
            elif len(date[0]) > 3 and date[0].isalpha():
                day = int(date[1])
                month = months[date[0]]
                return datetime(year,month,day).date()
            #parsing failed
            else:
                return date
            return date
# l = 3
        elif l == 3:
            #5 hours ago
            if date[2] == 'ago':
                if date[1] == 'hour' or date[1] == 'hours' or date[1] == 'hr' or date[1] == 'hrs':
                    # 5 hours ago (yesterday)
                    if int(str(datetime.now().time()).split(sep=':')[0]) - int(date[0]) < 0:
                        day = int(str(datetime.now().date()-timedelta(1)).split(sep='-')[2])
                        month = int(str(datetime.now().date()-timedelta(1)).split(sep='-')[1])
                        return datetime(year,month,day).date()
                    # 5 hours ago (today)
                    else:
                        return datetime(year,month,day).date()
                #10 minutes ago
                elif date[1] == 'minute' or date[1] == 'minutes' or date[1] == 'min' or date[1] == 'mins':
                    #22 minutes ago (yesterday)
                    if int(str(datetime.now().time()).split(sep=':')[1]) - int(date[0]) < 0 and int(str(datetime.now().time()).split(sep=':')[0])==0:
                        day = int(str(datetime.now().date()-timedelta(1)).split(sep='-')[2])
                        month = int(str(datetime.now().date()-timedelta(1)).split(sep='-')[1])
                        return datetime(year,month,day).date()
                    #22 minutes ago (today)
                    else:
                        return datetime(year,month,day).date()
                else:
                    return date
            else:
                #21 Jun 2017
                if len(date[1]) == 3 and date[1].isalpha() and date[2].isdigit():
                    day = int(date[0])
                    month = months_abbr[date[1].lower()]
                    year = int(date[2])
                    return datetime(year,month,day).date()
                #21 June 2017
                elif len(date[1]) > 3 and date[1].isalpha() and date[2].isdigit():
                    day = int(date[0])
                    month = months[date[1].lower()]
                    year = int(date[2])
                    return datetime(year,month,day).date()
                #Jul 11, 2016
                elif len(date[0]) == 3 and len(date[1]) == 3 and date[0].isalpha():
                    day = int(date[1][:-1])
                    month = months_abbr[date[0].lower()]
                    year = int(date[2])
                    return datetime(year,month,day).date()
                #parsing failed
                else:
                    return date
# l = 4
        elif l == 4:
            #yesterday at 23:32 PM
            if date[0].lower() == 'yesterday' and date[1] == 'at':
                day = int(str(datetime.now().date()-timedelta(1)).split(sep='-')[2])
                month = int(str(datetime.now().date()-timedelta(1)).split(sep='-')[1])
                return datetime(year,month,day).date()
            #Thursday at 4:27 PM
            elif date[1] == 'at':
                today = datetime.now().weekday() #today as a weekday
                weekday = days[date[0].lower()]   #day to be match as number weekday
                #weekday is chronologically always lower than day
                delta = today - weekday
                if delta >= 0:
                    day = int(str(datetime.now().date()-timedelta(delta)).split(sep='-')[2])
                    month = int(str(datetime.now().date()-timedelta(delta)).split(sep='-')[1])
                    return datetime(year,month,day).date()
                #monday = 0 saturday = 6
                else:
                    delta += 8
                    day = int(str(datetime.now().date()-timedelta(delta)).split(sep='-')[2])
                    month = int(str(datetime.now().date()-timedelta(delta)).split(sep='-')[1])
                    return datetime(year,month,day).date()
            #parsing failed
            else:
                return date
# l = 5
        elif l == 5:
           if date[2] == 'at':
               #Jan 29 at 10:00 PM
               if len(date[0]) == 3:
                   day = int(date[1])
                   month = months_abbr[date[0].lower()]
                   return datetime(year,month,day).date()
               #29 febbraio alle ore 21:49
               else:
                   day = int(date[1])
                   month = months[date[0].lower()]
                   return datetime(year,month,day).date()
           #parsing failed
           else:
               return date
# l = 6
        elif l == 6:
           if date[3] == 'at':
               date[1]
               #Aug 25, 2016 at 7:00 PM
               if len(date[0]) == 3:
                   day = int(date[1][:-1])
                   month = months_abbr[date[0].lower()]
                   year = int(date[2])
                   return datetime(year,month,day).date()
               #August 25, 2016 at 7:00 PM
               else:
                   day = int(date[1][:-1])
                   month = months[date[0].lower()]
                   year = int(date[2])
                   return datetime(year,month,day).date()
           #parsing failed
           else:
               return date
# l > 6
        #parsing failed - l too big
        else:
            return date
    #parsing failed - language not supported
    else:
        return init_date

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
    ahah = scrapy.Field(
        output_processor=reactions_strip
    )
    love = scrapy.Field(
        output_processor=reactions_strip
    )
    wow = scrapy.Field(
        output_processor=reactions_strip
    )
    sigh = scrapy.Field(
        output_processor=reactions_strip
    )
    grrr = scrapy.Field(
        output_processor=reactions_strip
    )
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
        output_processor=parse_date2
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
    ahah = scrapy.Field()
    love = scrapy.Field()
    wow = scrapy.Field()
    sigh = scrapy.Field()
    grrr = scrapy.Field()
    share = scrapy.Field()                      # num of shares

class ProfileItem(scrapy.Item):
    name = scrapy.Field()
    gender = scrapy.Field()
    birthday = scrapy.Field()
    current_city = scrapy.Field()
    hometown = scrapy.Field()
    work = scrapy.Field()
    education = scrapy.Field()
    interested_in = scrapy.Field()
    page = scrapy.Field()

class EventsItem(scrapy.Item):
    name = scrapy.Field()
    location = scrapy.Field()
    where = scrapy.Field()
    photo = scrapy.Field()
    start_date = scrapy.Field()
    end_date = scrapy.Field()
    description = scrapy.Field()
