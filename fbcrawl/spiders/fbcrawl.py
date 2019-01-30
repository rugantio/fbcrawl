import scrapy

from scrapy.loader import ItemLoader
from scrapy.http import FormRequest
from fbcrawl.items import FbcrawlItem


class FacebookSpider(scrapy.Spider):
    """
    Parse FB pages (needs credentials)
    """    
    name = "fb"

    def __init__(self, email='', password='', page='', year=2018, **kwargs):
        super(FacebookSpider, self).__init__(**kwargs)
        
        self.year = int(year)        #arguments are passed as strings
    
        if not email or not password:
            raise ValueError("You need to provide valid email and password!")
        else:
            self.email = email
            self.password = password
            
        if not page:
            raise ValueError("You need to provide a valid page name to crawl!")
        else:
            self.page = page
            
        self.start_urls = ['https://mbasic.facebook.com']    


    def parse(self, response):
        return FormRequest.from_response(
                response,
                formxpath='//form[contains(@action, "login")]',
                formdata={'email': self.email,'pass': self.password},
                callback=self.parse_home
        )
  
    def parse_home(self, response):
        '''
        Parse user news feed page. This code is outdate and needs review.
        '''
        if response.css('#approvals_code'):
            # Handle 'Approvals Code' checkpoint (ask user to enter code).
            if not self.code:
                # Show facebook messages via logs
                # and request user for approval code.
                message = response.css('._50f4::text').extract()[0]
                self.log(message)
                message = response.css('._3-8y._50f4').xpath('string()').extract()[0]
                self.log(message)
                self.code = input('Enter the code: ')
            self.code = str(self.code)
            if not (self.code and self.code.isdigit()):
                self.log('Bad approvals code detected.')
                return
            return FormRequest.from_response(
                response,
                formdata={'approvals_code': self.code},
                callback=self.parse_home,
            )
        elif response.xpath("//div/input[@value='Ok' and @type='submit']"):
            # Handle 'Save Browser' checkpoint.
            return FormRequest.from_response(
                response,
                formdata={'name_action_selected': 'dont_save'},
                callback=self.parse_home,
                dont_filter=True,
            )
        elif response.css('button#checkpointSubmitButton'):
            # Handle 'Someone tried to log into your account' warning.
            return FormRequest.from_response(
                response, callback=self.parse_home, dont_filter=True,)
        # Else go to the page requested.
        if self.page.find('.facebook.com/') != -1:
            self.page = self.page[28:]
        href = response.urljoin(self.page)
        self.logger.info('Parse function called on %s', href)
        return scrapy.Request(
            url=href,
            callback=self.parse_page,
        )

    def parse_page(self, response):
        #select all posts
        for post in response.xpath("//div[contains(@data-ft,'top_level_post_id')]"):            
            new = ItemLoader(item=FbcrawlItem(),selector=post)
            new.add_xpath('comments', "./div[2]/div[2]/a[1]/text()")        
            new.add_xpath('url', ".//a[contains(@href,'footer')]/@href")
            #page_url
            #new.add_value('url',response.url)
            #returns full post-link in a list
            post = post.xpath(".//a[contains(@href,'footer')]/@href").extract() 
            temp_post = response.urljoin(post[0])        
            yield scrapy.Request(temp_post, self.parse_post, meta={'item':new})       

        #load following page
#        next_page = response.xpath('//*[@id="structured_composer_async_container"]/div[2]/a/@href')
        next_page = response.xpath("//div[2]/a[contains(@href,'timestart=') and not(contains(text(),'ece')) and not(contains(text(),number()))]/@href").extract()      
        if len(next_page) == 0:
            if response.meta['flag'] == 3 and self.year <= 2015:
                self.logger.info('2015 reached, flag = {}'.format(response.meta['flag']))
                next_page = response.xpath("//div/a[contains(@href,'time') and contains(text(),'2015')]/@href").extract()
                self.logger.info('next_page = {}'.format(next_page[0]))
                new_page = response.urljoin(next_page[0])
                yield scrapy.Request(new_page, callback=self.parse_page, meta={'flag':4}) 
            elif response.meta['flag'] == 2 and self.year <= 2016:
                self.logger.info('2016 reached, flag = {}'.format(response.meta['flag']))                
                next_page = response.xpath("//div/a[contains(@href,'time') and contains(text(),'2016')]/@href").extract()
                self.logger.info('next_page = {}'.format(next_page[0]))
                new_page = response.urljoin(next_page[0])
                yield scrapy.Request(new_page, callback=self.parse_page, meta={'flag':3}) 
            elif response.meta['flag'] == 1 and self.year <= 2017:            
                self.logger.info('2017 reached, flag = {}'.format(response.meta['flag']))                
                next_page = response.xpath("//div/a[contains(@href,'time') and contains(text(),'2017')]/@href").extract()
                self.logger.info('next_page = {}'.format(next_page[0]))
                new_page = response.urljoin(next_page[0])
                yield scrapy.Request(new_page, callback=self.parse_page, meta={'flag':2})      
            elif response.meta['flag'] == 0 and self.year <= 2018:                      
                self.logger.info('2018 reached, flag = {}'.format(response.meta['flag']))
                next_page = response.xpath("//div/a[contains(@href,'time') and contains(text(),'2018')]/@href").extract()
                self.logger.info('next_page = {}'.format(next_page[0]))
                new_page = response.urljoin(next_page[0])
                yield scrapy.Request(new_page, callback=self.parse_page, meta={'flag':1})
        else:
            new_page = response.urljoin(next_page[0])
            if 'flag' in response.meta:
                yield scrapy.Request(new_page, callback=self.parse_page, meta={'flag':response.meta['flag']})
            else:
                yield scrapy.Request(new_page, callback=self.parse_page, meta={'flag':0})
                
    def parse_post(self,response):
        new = ItemLoader(item=FbcrawlItem(),response=response,parent=response.meta['item'])            
        new.add_xpath('source', "//td/div/h3/strong/a/text() | //span/strong/a/text() | //div/div/div/a[contains(@href,'post_id')]/strong/text()")
        new.add_xpath('date', '//div/div/abbr/text()')
        new.add_xpath('text','//div[@data-ft]//p//text() | //div[@data-ft]/div[@class]/div[@class]/text()')
        new.add_xpath('reactions',"//a[contains(@href,'reaction/profile')]/div/div/text()")   
        
        reactions = response.xpath("//div[contains(@id,'sentence')]/a[contains(@href,'reaction/profile')]/@href")
        reactions = response.urljoin(reactions[0].extract())
        yield scrapy.Request(reactions, callback=self.parse_reactions, meta={'item':new})
        
    def parse_reactions(self,response):
        new = ItemLoader(item=FbcrawlItem(),response=response, parent=response.meta['item'])
        new.add_xpath('likes',"//a[contains(@href,'reaction_type=1')]/span/text()")
        new.add_xpath('ahah',"//a[contains(@href,'reaction_type=4')]/span/text()")
        new.add_xpath('love',"//a[contains(@href,'reaction_type=2')]/span/text()")
        new.add_xpath('wow',"//a[contains(@href,'reaction_type=3')]/span/text()")
        new.add_xpath('sigh',"//a[contains(@href,'reaction_type=7')]/span/text()")
        new.add_xpath('grrr',"//a[contains(@href,'reaction_type=8')]/span/text()")        
        yield new.load_item()
