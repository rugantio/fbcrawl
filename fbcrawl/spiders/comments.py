import scrapy

from scrapy.loader import ItemLoader
from fbcrawl.spiders.fbcrawl import FacebookSpider
from fbcrawl.items import CommentsItem


class CommentsSpider(FacebookSpider):
    """
    Parse FB comments, given a post (needs credentials)
    """    
    name = "comments"
    custom_settings = {
        'FEED_EXPORT_FIELDS': ['source','reply_to','date','reactions','text', \
                               'source_url','url'],
        'DUPEFILTER_CLASS' : 'scrapy.dupefilters.BaseDupeFilter',
        'CONCURRENT_REQUESTS':1, 
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)

    def parse_page(self, response):
        '''
        parse page does multiple things:
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
            self.logger.info('{} nested comment @ page {}'.format(str(response.meta['index']),ans))
            yield scrapy.Request(ans,
                                 callback=self.parse_reply,
                                 meta={'reply_to':source,
                                       'url':response.url,
                                       'index':response.meta['index'],
                                       'flag':'init',
                                       'group':group_flag})
        #load regular comments     
        if not response.xpath(path): #prevents from exec
            path2 = './/div[string-length(@class) = 2 and count(@id)=1 and contains("0123456789", substring(@id,1,1)) and not(.//div[contains(@id,"comment_replies")])]'
            for i,reply in enumerate(response.xpath(path2)):
                self.logger.info('{} regular comment @ page {}'.format(i,response.url))
                new = ItemLoader(item=CommentsItem(),selector=reply)
                new.context['lang'] = self.lang           
                new.add_xpath('source','.//h3/a/text()')  
                new.add_xpath('source_url','.//h3/a/@href')   
                new.add_xpath('text','.//div[h3]/div[1]//text()')
                new.add_xpath('date','.//abbr/text()')
                new.add_xpath('reactions','.//a[contains(@href,"reaction/profile")]//text()')
                new.add_value('url',response.url)
                yield new.load_item()
            
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
                                         callback=self.parse_page,
                                         meta={'index':1,
                                               'group':1})        
            else:
                for next_page in response.xpath(next_xpath):
                    new_page = next_page.xpath('.//@href').extract()
                    new_page = response.urljoin(new_page[0])
                    self.logger.info('New page to be crawled {}'.format(new_page))
                    yield scrapy.Request(new_page,
                                         callback=self.parse_page,
                                         meta={'index':1,
                                               'group':group_flag})        
        
    def parse_reply(self,response):
        '''
        parse reply to comments, root comment is added if flag
        '''
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
                yield new.load_item()
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
                yield new.load_item()
                
            back = response.xpath('//div[contains(@id,"comment_replies_more_1")]/a/@href').extract()
            if back:
                self.logger.info('Back found, more nested comments')
                back_page = response.urljoin(back[0])
                yield scrapy.Request(back_page, 
                                     callback=self.parse_reply,
                                     priority=100,
                                     meta={'reply_to':response.meta['reply_to'],
                                           'flag':'back',
                                           'url':response.meta['url'],
                                           'index':response.meta['index'],
                                           'group':response.meta['group']})

            else:
                next_reply = response.meta['url']
                self.logger.info('Nested comments crawl finished, heading to proper page: {}'.format(response.meta['url']))
                yield scrapy.Request(next_reply,
                                     callback=self.parse_page,
                                     meta={'index':response.meta['index']+1,
                                           'group':response.meta['group']})
                
        elif response.meta['flag'] == 'back':
            #parse all comments
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
                yield new.load_item()
            #keep going backwards
            back = response.xpath('//div[contains(@id,"comment_replies_more_1")]/a/@href').extract()
            self.logger.info('Back found, more nested comments')
            if back:
                back_page = response.urljoin(back[0])
                yield scrapy.Request(back_page, 
                                     callback=self.parse_reply,
                                     priority=100,
                                     meta={'reply_to':response.meta['reply_to'],
                                           'flag':'back',
                                           'url':response.meta['url'],
                                           'index':response.meta['index'],
                                           'group':response.meta['group']})

            else:
                next_reply = response.meta['url']
                self.logger.info('Nested comments crawl finished, heading to home page: {}'.format(response.meta['url']))
                yield scrapy.Request(next_reply,
                                     callback=self.parse_page,
                                     meta={'index':response.meta['index']+1,
                                           'group':response.meta['group']})
                
# =============================================================================
# CRAWL REACTIONS
# =============================================================================
#    def parse_reactions(self,response):
#        new = ItemLoader(item=CommentsItem(),response=response, parent=response.meta['item'])
#        new.context['lang'] = self.lang           
#        new.add_xpath('likes',"//a[contains(@href,'reaction_type=1')]/span/text()")
#        new.add_xpath('ahah',"//a[contains(@href,'reaction_type=4')]/span/text()")
#        new.add_xpath('love',"//a[contains(@href,'reaction_type=2')]/span/text()")
#        new.add_xpath('wow',"//a[contains(@href,'reaction_type=3')]/span/text()")
#        new.add_xpath('sigh',"//a[contains(@href,'reaction_type=7')]/span/text()")
#        new.add_xpath('grrr',"//a[contains(@href,'reaction_type=8')]/span/text()")        
#        yield new.load_item()     
#
#    #substitute
#    yield new.load_item()
#    ‾‾‾‾‾‾‾‾‾|‾‾‾‾‾‾‾‾‾‾‾
#    _________v___
#    #response --> reply/root
#    reactions = response.xpath(".//a[contains(@href,'reaction/profile')]/@href")
#    reactions = response.urljoin(reactions[0].extract())
#    if reactions:
#        yield scrapy.Request(reactions, callback=self.parse_reactions, meta={'item':new})
#    else:
#        yield new.load_item() 