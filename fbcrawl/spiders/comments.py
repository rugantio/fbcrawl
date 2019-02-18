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
        'FEED_EXPORT_FIELDS': ['source','reply_to','date','text', \
                               'reactions','likes','ahah','love','wow', \
                               'sigh','grrr','url'],
        'DUPEFILTER_CLASS' : 'scrapy.dupefilters.BaseDupeFilter',
        'CONCURRENT_REQUESTS':1, 
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args,**kwargs)

    def parse_page(self, response):
        '''
        parse page does multiple things:
            1) loads replied-to-comments page one-by-one (for DFS)
            2) gets common not-replied-to comments
        '''
        #loads replied-to comments pages
        path = './/div[string-length(@class) = 2 and count(@id)=1 and contains("0123456789", substring(@id,1,1)) and .//div[contains(@id,"comment_replies")]]'  + '['+ str(response.meta['index']) + ']'
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
                                       'flag':'init'})
        #loads regular comments     
        if not response.xpath(path):
            path2 = './/div[string-length(@class) = 2 and count(@id)=1 and contains("0123456789", substring(@id,1,1)) and not(.//div[contains(@id,"comment_replies")])]'
            
            for i,reply in enumerate(response.xpath(path2)):
                self.logger.info('{} regular comment @ page {}'.format(i,response.url))
                new = ItemLoader(item=CommentsItem(),selector=reply)
                new.context['lang'] = self.lang           
                new.add_xpath('source','.//h3/a/text()')  
                new.add_xpath('text','.//div[h3]/div[1]//text()')
                new.add_xpath('date','.//abbr/text()')
                new.add_value('url',response.url)
                yield new.load_item()
            
        #previous comments
        if not response.xpath(path):
            for next_page in response.xpath('.//div[contains(@id,"see_next")]'):
                new_page = next_page.xpath('.//@href').extract()
                new_page = response.urljoin(new_page[0])
                self.logger.info('New page to be crawled {}'.format(new_page))
                yield scrapy.Request(new_page,
                                     callback=self.parse_page,
                                     meta={'index':1})        
        
    def parse_reply(self,response):
        '''
        parse reply to comments, root comment is added if flag
        '''
        if response.meta['flag'] == 'init':
            #parse root comment
            for root in response.xpath('//div[contains(@id,"root")]/div/div/div[count(@id)!=1 and contains("0123456789", substring(@id,1,1))]'): 
                new = ItemLoader(item=CommentsItem(),selector=root)
                new.context['lang'] = self.lang           
                new.add_xpath('source', './/h3/a/text()')
                new.add_value('reply_to','ROOT')
                new.add_xpath('text','.//div[1]//text()')
                new.add_xpath('date','.//abbr/text()')
                new.add_value('url',response.url)
                yield new.load_item()
            #parse all replies in the page
            for reply in response.xpath('//div[contains(@id,"root")]/div/div/div[count(@id)=1 and contains("0123456789", substring(@id,1,1))]'): 
                new = ItemLoader(item=CommentsItem(),selector=reply)
                new.context['lang'] = self.lang           
                new.add_xpath('source', './/h3/a/text()')
                new.add_value('reply_to',response.meta['reply_to'])
                new.add_xpath('text','.//div[h3]/div[1]//text()')
                new.add_xpath('date','.//abbr/text()')
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
                                           'index':response.meta['index']})
            else:
                next_reply = response.meta['url']
                self.logger.info('Nested comments crawl finished, heading to proper page: {}'.format(response.meta['url']))
                yield scrapy.Request(next_reply,
                                     callback=self.parse_page,
                                     meta={'index':response.meta['index']+1})
                
        elif response.meta['flag'] == 'back':
            #parse all comments
            for reply in response.xpath('//div[contains(@id,"root")]/div/div/div[count(@id)=1 and contains("0123456789", substring(@id,1,1))]'): 
                new = ItemLoader(item=CommentsItem(),selector=reply)
                new.context['lang'] = self.lang           
                new.add_xpath('source', './/h3/a/text()')
                new.add_value('reply_to',response.meta['reply_to'])
                new.add_xpath('text','.//div[h3]/div[1]//text()')
                new.add_xpath('date','.//abbr/text()')
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
                                           'index':response.meta['index']})
            else:
                next_reply = response.meta['url']
                self.logger.info('Nested comments crawl finished, heading to home page: {}'.format(response.meta['url']))
                yield scrapy.Request(next_reply,
                                     callback=self.parse_page,
                                     meta={'index':response.meta['index']+1})
