import scrapy

from scrapy.loader import ItemLoader
from scrapy.http import FormRequest
from fbcrawl.items import FbcrawlItem
from scrapy.exceptions import CloseSpider


class FacebookSpider(scrapy.Spider):
    """
    Parse FB pages (needs credentials)
    """    
    name = "fb"

    def __init__(self, email='', password='', page='', year=2018, lang='_', **kwargs):
        super(FacebookSpider, self).__init__(**kwargs)
        
        #email & pass need to be passed as attributes!
        if not email or not password:
            raise ValueError("You need to provide valid email and password!")
        else:
            self.email = email
            self.password = password
            
        #page name parsing (added support for full urls)
        if not page:
            raise ValueError("You need to provide a valid page name to crawl!")
        elif page.find('https://www.facebook.com/') != -1:
            self.page = page[25:]
        elif page.find('https://mbasic.facebook.com/') != -1:
            self.page = page[28:]
        elif page.find('https://m.facebook.com/') != -1:
            self.page = page[23:]
        else:
            self.page = page
        
        #parse year 
        assert int(year) <= 2019 and int(year) >= 2015, 'Year must be a number 2015 <= year <= 2019'
        self.year = int(year)    #arguments are passed as strings
    
        #parse lang, if not provided (but is supported) it will be guessed in parse_home
        if lang=='_':
            self.logger.info('Language attribute not provided, I will try to guess it')
            self.logger.info('Currently supported languages are: "en", "es", "fr", "it", "pt"')
            self.lang=lang                            
        elif lang == 'en'  or lang == 'es' or lang == 'fr' or lang == 'it' or lang == 'pt':
            self.lang = lang
        else:
            self.logger.info('Lang "{}" not currently supported'.format(lang))                             
            self.logger.info('Currently supported languages are: "en", "es", "fr", "it", "pt"')                             
            self.logger.info('Change your interface lang from facebook and try again')
            raise CloseSpider('Language provided not currently supported')

        self.start_urls = ['https://mbasic.facebook.com']    

    def parse(self, response):
        '''
        Handle login with provided credentials
        '''
        return FormRequest.from_response(
                response,
                formxpath='//form[contains(@action, "login")]',
                formdata={'email': self.email,'pass': self.password},
                callback=self.parse_home
        )
  
    def parse_home(self, response):
        '''
        This method has multiple purposes:
        1) Handle failed logins due to facebook 'save-device' redirection
        2) Set language interface, if not already provided
        3) Navigate to given page 
        '''
        #handle 'save-device' redirection
        if response.xpath("//div/a[contains(@href,'save-device')]"):
            return FormRequest.from_response(
                response,
                formdata={'name_action_selected': 'dont_save'},
                callback=self.parse_home)
            
        #set language interface
        if self.lang == '_':
            if response.xpath("//input[@placeholder='Search Facebook']"):
                self.lang = 'en'
            elif response.xpath("//input[@value='Buscar']"):
                self.lang = 'es'
            elif response.xpath("//input[@value='Rechercher']"):
                self.lang = 'fr'
            elif response.xpath("//input[@value='Cerca']"):
                self.lang = 'it'
            elif response.xpath("//input[@value='Pesquisar']"):
                self.lang = 'pt'                
            else:
                raise CloseSpider('Language not recognized')
          
        #navigate to provided page
        href = response.urljoin(self.page)
        self.logger.info('Parsing facebook page %s', href)
        return scrapy.Request(url=href,callback=self.parse_page)

    def parse_page(self, response):
        '''
        Parse the given page selecting the posts.
        Then ask recursively for another page.
        '''
        #select all posts
        for post in response.xpath("//div[contains(@data-ft,'top_level_post_id')]"):            
            new = ItemLoader(item=FbcrawlItem(),selector=post)
            new.add_xpath('comments', "./div[2]/div[2]/a[1]/text()")        
            new.add_xpath('url', ".//a[contains(@href,'footer')]/@href")
            new.add_xpath('reactions',".//a[contains(@aria-label,'reactions')]/text()")   

            #page_url #new.add_value('url',response.url)
            #returns full post-link in a list
            post = post.xpath(".//a[contains(@href,'footer')]/@href").extract() 
            temp_post = response.urljoin(post[0])        
            yield scrapy.Request(temp_post, self.parse_post, meta={'item':new})       

        #load following page
        next_page = response.xpath("//div[2]/a[contains(@href,'timestart=') and not(contains(text(),'ent')) and not(contains(text(),number()))]/@href").extract()      
        if len(next_page) == 0: 
            if response.meta['flag'] == 4 and self.year <= 2015:
                self.logger.info('2014 reached, flag = 5')
                next_page = response.xpath("//div/a[contains(@href,'time') and contains(text(),'2015')]/@href").extract()
                self.logger.info('next_page = {}'.format(next_page[0]))
                new_page = response.urljoin(next_page[0])
                yield scrapy.Request(new_page, callback=self.parse_page, meta={'flag':5}) 
            elif response.meta['flag'] == 3 and self.year <= 2015:
                self.logger.info('2015 reached, flag = 4')
                next_page = response.xpath("//div/a[contains(@href,'time') and contains(text(),'2015')]/@href").extract()
                self.logger.info('next_page = {}'.format(next_page[0]))
                new_page = response.urljoin(next_page[0])
                yield scrapy.Request(new_page, callback=self.parse_page, meta={'flag':4}) 
            elif response.meta['flag'] == 2 and self.year <= 2016:
                self.logger.info('2016 reached, flag = 3')                
                next_page = response.xpath("//div/a[contains(@href,'time') and contains(text(),'2016')]/@href").extract()
                self.logger.info('next_page = {}'.format(next_page[0]))
                new_page = response.urljoin(next_page[0])
                yield scrapy.Request(new_page, callback=self.parse_page, meta={'flag':3}) 
            elif response.meta['flag'] == 1 and self.year <= 2017:            
                self.logger.info('2017 reached, flag = 2')          
                next_page = response.xpath("//div/a[contains(@href,'time') and contains(text(),'2017')]/@href").extract()
                self.logger.info('next_page = {}'.format(next_page[0]))
                new_page = response.urljoin(next_page[0])
                yield scrapy.Request(new_page, callback=self.parse_page, meta={'flag':2})      
            elif response.meta['flag'] == 0 and self.year <= 2018:                      
                self.logger.info('2018 reached, flag = 1')
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
        
        reactions = response.xpath("//div[contains(@id,'sentence')]/a[contains(@href,'reaction/profile')]/@href")
        reactions = response.urljoin(reactions[0].extract())
        yield scrapy.Request(reactions, callback=self.parse_reactions, meta={'item':new})
        
    def parse_reactions(self,response):
        new = ItemLoader(item=FbcrawlItem(),response=response, parent=response.meta['item'])
        new.context['lang'] = self.lang           
        new.add_xpath('likes',"//a[contains(@href,'reaction_type=1')]/span/text()")
        new.add_xpath('ahah',"//a[contains(@href,'reaction_type=4')]/span/text()")
        new.add_xpath('love',"//a[contains(@href,'reaction_type=2')]/span/text()")
        new.add_xpath('wow',"//a[contains(@href,'reaction_type=3')]/span/text()")
        new.add_xpath('sigh',"//a[contains(@href,'reaction_type=7')]/span/text()")
        new.add_xpath('grrr',"//a[contains(@href,'reaction_type=8')]/span/text()")        
        yield new.load_item()
