import scrapy
#added time and random to prevent getting blocked by Facebook
import time
from random import randrange

from scrapy.loader import ItemLoader
from scrapy.exceptions import CloseSpider
from fbcrawl.spiders.fbcrawl import FacebookSpider
from fbcrawl.items import CommentsItem, parse_date, parse_date2

from datetime import datetime

class CommentsSpider(FacebookSpider):
    """
    Parse FB comments, given a post (needs credentials)
    """
    name = "comments"
    #added the additional fields for specific reactions and profile info
    custom_settings = {
        'FEED_EXPORT_FIELDS': ['source','reply_to','date','text', \
                               'reactions','likes','url', 'ahah','love','wow', \
                               'sigh','grrr','name', \
                               'gender', 'birthday', 'current_city',\
                               'hometown', 'work', 'education', 'interested_in'],
        'DUPEFILTER_CLASS' : 'scrapy.dupefilters.BaseDupeFilter',
        'CONCURRENT_REQUESTS' : 1
    }

    def __init__(self, *args, **kwargs):
        if 'post' in kwargs and 'page' in kwargs:
            raise AttributeError('You need to specifiy only one between post and page')
        elif 'post' in kwargs:
            self.page = kwargs['post']
            self.type = 'post'
        elif 'page' in kwargs:
            self.type = 'page'

        super().__init__(*args,**kwargs)

    def parse_page(self, response):
        '''
        '''
        if self.type == 'post':
            yield scrapy.Request(url=response.url,
                                 callback=self.parse_post,
                                 priority=10,
                                 meta={'index':1})
        elif self.type == 'page':
            #select all posts
            for post in response.xpath("//div[contains(@data-ft,'top_level_post_id')]"):
                many_features = post.xpath('./@data-ft').get()
                date = []
                date.append(many_features)
                date = parse_date(date,{'lang':self.lang})
                current_date = datetime.strptime(date,'%Y-%m-%d %H:%M:%S') if date is not None else date

                if current_date is None:
                    date_string = post.xpath('.//abbr/text()').get()
                    date = parse_date2([date_string],{'lang':self.lang})
                    current_date = datetime(date.year,date.month,date.day) if date is not None else date
                    date = str(date)

                if abs(self.count) + 1 > self.max:
                    raise CloseSpider('Reached max num of post: {}. Crawling finished'.format(abs(self.count)))
                self.logger.info('Parsing post n = {}, post_date = {}'.format(abs(self.count)+1,date))

                #returns full post-link in a list
                post = post.xpath(".//a[contains(@href,'footer')]/@href").extract()
                temp_post = response.urljoin(post[0])
                self.count -= 1
                yield scrapy.Request(temp_post,
                                     self.parse_post,
                                     priority = self.count,
                                     meta={'index':1})

            #load following page, try to click on "more"
            #after few pages have been scraped, the "more" link might disappears
            #if not present look for the highest year not parsed yet
            #click once on the year and go back to clicking "more"

            #new_page is different for groups
            if self.group == 1:
                new_page = response.xpath("//div[contains(@id,'stories_container')]/div[2]/a/@href").extract()
            else:
                new_page = response.xpath("//div[2]/a[contains(@href,'timestart=') and not(contains(text(),'ent')) and not(contains(text(),number()))]/@href").extract()
                #this is why lang is needed

            if not new_page:
                self.logger.info('[!] "more" link not found, will look for a "year" link')
                #self.k is the year link that we look for
                if response.meta['flag'] == self.k and self.k >= self.year:
                    xpath = "//div/a[contains(@href,'time') and contains(text(),'" + str(self.k) + "')]/@href"
                    new_page = response.xpath(xpath).extract()
                    if new_page:
                        new_page = response.urljoin(new_page[0])
                        self.k -= 1
                        self.logger.info('Found a link for year "{}", new_page = {}'.format(self.k,new_page))
                        yield scrapy.Request(new_page,
                                             callback=self.parse_page,
                                             priority = -1000,
                                             meta={'flag':self.k})
                    else:
                        while not new_page: #sometimes the years are skipped this handles small year gaps
                            self.logger.info('Link not found for year {}, trying with previous year {}'.format(self.k,self.k-1))
                            self.k -= 1
                            if self.k < self.year:
                                raise CloseSpider('Reached date: {}. Crawling finished'.format(self.date))
                            xpath = "//div/a[contains(@href,'time') and contains(text(),'" + str(self.k) + "')]/@href"
                            new_page = response.xpath(xpath).extract()
                        self.logger.info('Found a link for year "{}", new_page = {}'.format(self.k,new_page))
                        new_page = response.urljoin(new_page[0])
                        self.k -= 1
                        yield scrapy.Request(new_page,
                                             callback=self.parse_page,
                                             priority = -1000,
                                             meta={'flag':self.k})
                else:
                    self.logger.info('Crawling has finished with no errors!')
            else:
                new_page = response.urljoin(new_page[0])
                if 'flag' in response.meta:
                    self.logger.info('Page scraped, clicking on "more"! new_page = {}'.format(new_page))
                    yield scrapy.Request(new_page,
                                         callback=self.parse_page,
                                         priority = -1000,
                                         meta={'flag':response.meta['flag']})
                else:
                    self.logger.info('First page scraped, clicking on "more"! new_page = {}'.format(new_page))
                    yield scrapy.Request(new_page,
                                         callback=self.parse_page,
                                         priority = -1000,
                                         meta={'flag':self.k})

    def parse_post(self, response):
        '''
        parse post does multiple things:
            1) loads replied-to-comments page one-by-one (for DFS)
            2) call parse_reply on the nested comments
            3) adds simple (not-replied-to) comments
            4) follows to new comment page
        '''

        #load replied-to comments pages
        #select nested comment one-by-one matching with the index: response.meta['index']
        path = './/div[string-length(@class) = 2 and count(@id)=1 and contains("0123456789", substring(@id,1,1)) and .//div[contains(@id,"comment_replies")]]'  + '['+ str(response.meta['index']) + ']'
        group_flag = response.meta['group'] if 'group' in response.meta else None

        for reply in response.xpath(path):
            source = reply.xpath('.//h3/a/text()').extract()
            answer = reply.xpath('.//a[contains(@href,"repl")]/@href').extract()
            ans = response.urljoin(answer[::-1][0])
            self.logger.info('{} nested comment'.format(str(response.meta['index'])))
            yield scrapy.Request(ans,
                                 callback=self.parse_reply,
                                 priority=1000,
                                 meta={'reply_to':source,
                                       'url':response.url,
                                       'index':response.meta['index'],
                                       'flag':'init',
                                       'group':group_flag})


        #load regular comments
        if not response.xpath(path): #prevents from exec
            path2 = './/div[string-length(@class) = 2 and count(@id)=1 and contains("0123456789", substring(@id,1,1)) and not(.//div[contains(@id,"comment_replies")])]'
            for i,reply in enumerate(response.xpath(path2)):
                self.logger.info('{} regular comment'.format(i+1))
                new = ItemLoader(item=CommentsItem(),selector=reply)
                new.context['lang'] = self.lang
                new.add_xpath('source','.//h3/a/text()')
                new.add_xpath('source_url','.//h3/a/@href')
                new.add_xpath('text','.//div[h3]/div[1]//text()')
                new.add_xpath('date','.//abbr/text()')
                new.add_xpath('reactions','.//a[contains(@href,"reaction/profile")]//text()')
                new.add_value('url',response.url)

                """ 
                PROFILE REACTIONS SECTION
                adds functionality for adding profile and specific reaction data
                gets the profile url, creates a new item
                if the profile exists, add info to new item and increment 'check'
                to signal that new information has been added to the item
                and it's already been yielded
                repeat this process for reactions
                """
          
                #profile = response.xpath(".//h3/a/@href")
                #profile = response.urljoin(profile[0].extract())

                profile = "https://mbasic.facebook.com" + new.get_collected_values('source_url')[0]
                #print('profile', profile)
                #print('new item', new.get_collected_values('name'))

                item = new.load_item()
                check = 0
                if profile:
                    check += 1
                    yield scrapy.Request(profile, callback=self.parse_profile, meta={'item':item})

                temp = ItemLoader(item=CommentsItem(),selector=reply)
                temp.context['lang'] = self.lang

                temp.add_xpath('reactions', './/a[contains(@href,"reaction/profile")]/@href')
                reactions = temp.get_collected_values('reactions')
                if reactions:
                    check +=1
                    reactions = "https://mbasic.facebook.com" + temp.get_collected_values('reactions')[0]
                    temp = 0
                    yield scrapy.Request(reactions, callback=self.parse_reactions, meta={'item':item})

                if check == 0:
                    yield item



        #new comment page
        if not response.xpath(path):
            #for groups
            next_xpath = './/div[contains(@id,"see_next")]'
            prev_xpath = './/div[contains(@id,"see_prev")]'
            if not response.xpath(next_xpath) or group_flag == 1:
                for next_page in response.xpath(prev_xpath):
                    new_page = next_page.xpath('.//@href').extract()
                    new_page = response.urljoin(new_page[0])
                    self.logger.info('New page to be crawled {}'.format(new_page))
                    yield scrapy.Request(new_page,
                                         callback=self.parse_post,
                                         meta={'index':1,
                                               'group':1})
            else:
                for next_page in response.xpath(next_xpath):
                    new_page = next_page.xpath('.//@href').extract()
                    new_page = response.urljoin(new_page[0])
                    self.logger.info('New page to be crawled {}'.format(new_page))
                    yield scrapy.Request(new_page,
                                         callback=self.parse_post,
                                         meta={'index':1,
                                               'group':group_flag})

    def parse_reply(self,response):
        '''
        parse reply to comments, root comment is added if flag
        '''
#        from scrapy.utils.response import open_in_browser
#        open_in_browser(response)

        if response.meta['flag'] == 'init':
            #parse root comment
            for root in response.xpath('//div[contains(@id,"root")]/div/div/div[count(@id)!=1 and contains("0123456789", substring(@id,1,1))]'):
                new = ItemLoader(item=CommentsItem(),selector=root)
                new.context['lang'] = self.lang
                new.add_xpath('source','.//h3/a/text()')
                new.add_xpath('source_url','.//h3/a/@href')
                new.add_value('reply_to','ROOT')
                new.add_xpath('text','.//div[1]//text()')
                new.add_xpath('date','.//abbr/text()')
                new.add_xpath('reactions','.//a[contains(@href,"reaction/profile")]//text()')
                new.add_value('url',response.url)
                #response --> reply/root
                """
                PROFILE REACTIONS SECTION (REPEAT SEE LINE 176 )
                the only difference is that, when getting the item temporarily
                the selector is the root instead of the reply, (it matches the for loop)
                """
                #profile = response.xpath(".//h3/a/@href")
                #profile = response.urljoin(profile[0].extract())
                profile = "https://mbasic.facebook.com" + new.get_collected_values('source_url')[0]
                print('profile', profile)
                #print('new item', new.get_collected_values('name'))
                item = new.load_item()
                check = 0
                if profile:
                    check += 1
                    yield scrapy.Request(profile, callback=self.parse_profile, meta={'item':item})

                #reactions = new.get_value('reactions')
                #print("reactions",reactions)

                temp = ItemLoader(item=CommentsItem(),selector=root)
                temp.context['lang'] = self.lang

                temp.add_xpath('reactions', './/a[contains(@href,"reaction/profile")]/@href')
                reactions = temp.get_collected_values('reactions')
                if reactions:
                    check += 1
                    reactions = "https://mbasic.facebook.com" + temp.get_collected_values('reactions')[0]
                    temp = 0
                    yield scrapy.Request(reactions, callback=self.parse_reactions, meta={'item':item})

                if check == 0:
                    yield item



            #parse all replies in the page
            for reply in response.xpath('//div[contains(@id,"root")]/div/div/div[count(@id)=1 and contains("0123456789", substring(@id,1,1))]'):
                new = ItemLoader(item=CommentsItem(),selector=reply)
                new.context['lang'] = self.lang
                new.add_xpath('source','.//h3/a/text()')
                new.add_xpath('source_url','.//h3/a/@href')
                new.add_value('reply_to',response.meta['reply_to'])
                new.add_xpath('text','.//div[h3]/div[1]//text()')
                new.add_xpath('date','.//abbr/text()')
                new.add_xpath('reactions','.//a[contains(@href,"reaction/profile")]//text()')
                new.add_value('url',response.url)

                """
                PROFILE REACTIONS SECTION SECTION (REPEAT SEE LINE 176)
                """
                #profile = response.xpath(".//h3/a/@href")
                #profile = response.urljoin(profile[0].extract())
                profile = "https://mbasic.facebook.com" + new.get_collected_values('source_url')[0]


                #print('new item', new.get_collected_values('name'))
                item = new.load_item()
                check = 0
                if profile:
                    check += 1
                    yield scrapy.Request(profile, callback=self.parse_profile, meta={'item':item})

                temp = ItemLoader(item=CommentsItem(),selector=reply)
                temp.context['lang'] = self.lang

                temp.add_xpath('reactions', './/a[contains(@href,"reaction/profile")]/@href')
                reactions = temp.get_collected_values('reactions')
                if reactions:
                    check += 1
                    reactions = "https://mbasic.facebook.com" + temp.get_collected_values('reactions')[0]
                    temp = 0
                    yield scrapy.Request(reactions, callback=self.parse_reactions, meta={'item':item})

                if check == 0:
                    yield item


            back = response.xpath('//div[contains(@id,"comment_replies_more_1")]/a/@href').extract()
            if back:
                self.logger.info('Back found, more nested comments')
                back_page = response.urljoin(back[0])
                yield scrapy.Request(back_page,
                                     callback=self.parse_reply,
                                     priority = 1000,
                                     meta={'reply_to':response.meta['reply_to'],
                                           'flag':'back',
                                           'url':response.meta['url'],
                                           'index':response.meta['index'],
                                           'group':response.meta['group']})

            else:
                next_reply = response.meta['url']
                self.logger.info('Nested comments crawl finished, heading to proper page: {}'.format(response.meta['url']))
                yield scrapy.Request(next_reply,
                                     callback=self.parse_post,
                                     meta={'index':response.meta['index']+1,
                                           'group':response.meta['group']})

        elif response.meta['flag'] == 'back':
            """
            adds random time pauses to prevent blocking
            DOWNSIDE: the algorithm will go slower, but still
            runs pretty quickly
            the greater the length of time, the more 
            likely you'll go undetected, but if you're using a large amount 
            of data, this may be unreasonable
            """
            #print("did we make it")
            r = randrange(0,20)
            time.sleep(r)
            #parse all comments
            for reply in response.xpath('//div[contains(@id,"root")]/div/div/div[count(@id)=1 and contains("0123456789", substring(@id,1,1))]'):
                #print("reply")
                new = ItemLoader(item=CommentsItem(),selector=reply)
                new.context['lang'] = self.lang
                new.add_xpath('source','.//h3/a/text()')
                new.add_xpath('source_url','.//h3/a/@href')
                new.add_value('reply_to',response.meta['reply_to'])
                new.add_xpath('text','.//div[h3]/div[1]//text()')
                new.add_xpath('date','.//abbr/text()')
                new.add_xpath('reactions','.//a[contains(@href,"reaction/profile")]//text()')
                new.add_value('url',response.url)

                """
                SECTION (REPEAT SEE LINE 176)
                """
                
                profile = "https://mbasic.facebook.com" + new.get_collected_values('source_url')[0]

                #profile = response.xpath(".//h3/a/@href")
                #profile = response.urljoin(profile[0].extract())
                #print('profile', profile)
                #print('new item', new.get_collected_values('name'))
                check = 0
                item = new.load_item()
                if profile:
                    check += 1
                    print(1)
                    yield scrapy.Request(profile, callback=self.parse_profile, meta={'item':item})

                #response --> reply/root
                #print("before ", item)
                temp = ItemLoader(item=CommentsItem(),selector=reply)
                temp.context['lang'] = self.lang

                temp.add_xpath('reactions', './/a[contains(@href,"reaction/profile")]/@href')
                reactions = temp.get_collected_values('reactions')
                if reactions:
                    check += 1
                    reactions = "https://mbasic.facebook.com" + temp.get_collected_values('reactions')[0]
                    temp = 0
                    print(2)
                    yield scrapy.Request(reactions, callback=self.parse_reactions, meta={'item':item})

                if check == 0:
                    print(3)
                    yield item
                #print("after ", item)




            #keep going backwards
            back = response.xpath('//div[contains(@id,"comment_replies_more_1")]/a/@href').extract()
            self.logger.info('Back found, more nested comments')
            if back:
                back_page = response.urljoin(back[0])
                yield scrapy.Request(back_page,
                                     callback=self.parse_reply,
                                     priority=1000,
                                     meta={'reply_to':response.meta['reply_to'],
                                           'flag':'back',
                                           'url':response.meta['url'],
                                           'index':response.meta['index'],
                                           'group':response.meta['group']})

            else:
                next_reply = response.meta['url']
                self.logger.info('Nested comments crawl finished, heading to home page: {}'.format(response.meta['url']))
                yield scrapy.Request(next_reply,
                                     callback=self.parse_post,
                                     meta={'index':response.meta['index']+1,
                                           'group':response.meta['group']})
    """
    PARSE_PROFILE
    This function parses the profile information from the user associated 
    with the current comment. It first does a random time pause, then adds
    profile fields to the item that is associated with a specific comment.
    This is done explicitly. I left the other way I tried, feeding in the 
    item and adding xpaths, but it wouldn't return correctly. (the other
    method mirrors the old way of getting reaction information)
    """
    def parse_profile(self,response):
        '''because visiting profiles causes blocking the quickest, 
        its especially useful to have a randomized time pause
        at the start of parsing each profile.
        the if statement ensures that infrequently there will an even 
        longer time pause, to create greater randomness and infrequently
        increase the wait time
        '''
        r = randrange(0,20)
        if(r == 0):
            r2 = randrange(0,60)
            time.sleep(60 + r2)

        time.sleep(r)
        #new = ItemLoader(item=response.meta['item'],response=response )
        self.logger.info('Crawling profile info')
        #new.context['lang'] = self.lang

        item = response.meta['item']
        item['name'] = response.xpath('//span/div/span/strong/text()').extract()
        item['gender'] = response.xpath("//div[@id='basic-info']//div[@title='Gender']//div/text()").extract()
        item['birthday'] = response.xpath("//div[@id='basic-info']//div[@title='Birthday']//div/text()").extract()
        item['current_city'] = response.xpath("//div[@id='living']//div[@title='Current City']//a/text()").extract()
        item['hometown'] = response.xpath("//div[@id='living']//div[@title='Hometown']//a/text()").extract()
        item['work'] = response.xpath("//div[@id='work']//a/text()").extract()
        item['education'] = response.xpath("//div[@id='education']//a/text()").extract()
        item['interested_in'] = response.xpath("//div[@id='interested-in']//div[not(contains(text(),'Interested In'))]/text()").extract()

        '''new.add_xpath('name','//span/div/span/strong/text()').extract()
        new.add_xpath('gender',"//div[@id='basic-info']//div[@title='Gender']//div/text()").extract()
        new.add_xpath('birthday',"//div[@id='basic-info']//div[@title='Birthday']//div/text()").extract()
        new.add_xpath('current_city',"//div[@id='living']//div[@title='Current City']//a/text()").extract()
        new.add_xpath('hometown',"//div[@id='living']//div[@title='Hometown']//a/text()").extract()
        new.add_xpath('work',"//div[@id='work']//a/text()").extract()
        new.add_xpath('education',"//div[@id='education']//a/text()").extract()
        new.add_xpath('interested_in',"//div[@id='interested-in']//div[not(contains(text(),'Interested In'))]/text()")'''
        #print(item['name'])
        #print(item)
        #self.logger.info('its making it to the end of the function')
        #item = new.load_item()
        yield item
        #yield new.load_item()


    """
    PARSE_REACTIONS
    This function parses the reaction information associated with a 
    particular comment. It is, other than the difference in field
    names, identical to the code in parse reactions. Again, there
    is a random time pause. I think it helped to have a pause when 
    visiting new pages, which is why it was included here, as the 
    reactions page is a separate URL. This intends to mimic what an 
    user might do.
    """
    def parse_reactions(self,response):
        r = randrange(0,20)
        time.sleep(r)
        #new = ItemLoader(item=CommentsItem(),response=response, parent=response.meta['item'])
        #print("reactions",new.item)
        #new.context['lang'] = self.lang
        item = response.meta['item']
        item['likes'] = response.xpath("//a[contains(@href,'reaction_type=1')]/span/text()").extract()
        item['ahah'] = response.xpath("//a[contains(@href,'reaction_type=4')]/span/text()").extract()
        item['love'] = response.xpath("//a[contains(@href,'reaction_type=2')]/span/text()").extract()
        item['wow'] = response.xpath("//a[contains(@href,'reaction_type=3')]/span/text()").extract()
        item['sigh'] = response.xpath("//a[contains(@href,'reaction_type=7')]/span/text()").extract()
        item['grrr'] = response.xpath("//a[contains(@href,'reaction_type=8')]/span/text()").extract()
        #print(item)


        yield item
        '''new.add_xpath('likes',"//a[contains(@href,'reaction_type=1')]/span/text()")
        new.add_xpath('ahah',"//a[contains(@href,'reaction_type=4')]/span/text()")
        new.add_xpath('love',"//a[contains(@href,'reaction_type=2')]/span/text()")
        new.add_xpath('wow',"//a[contains(@href,'reaction_type=3')]/span/text()")
        new.add_xpath('sigh',"//a[contains(@href,'reaction_type=7')]/span/text()")
        new.add_xpath('grrr',"//a[contains(@href,'reaction_type=8')]/span/text()")'''
        #yield new.load_item()
