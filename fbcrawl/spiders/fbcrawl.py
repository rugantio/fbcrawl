import scrapy
import logging

from scrapy.loader import ItemLoader
from scrapy.http import FormRequest
from fbcrawl.items import FbcrawlItem

class FacebookSpider(scrapy.Spider):
    """
    Parse FB pages (needs credentials)
    """    
    name = "fb"
    custom_settings = {
        'FEED_EXPORT_FIELDS': ['source','shared_from','date','text', \
                               'reactions','likes','ahah','love','wow', \
                               'sigh','grrr','comments','url']
    }

    def __init__(self,email='',password='',page='',year=2018,lang='_',*args,**kwargs):
        #turn off annoying logging, set LOG_LEVEL=DEBUG in settings.py to see more logs
        logger = logging.getLogger('scrapy.middleware')
        logger.setLevel(logging.WARNING)
        super().__init__(**kwargs)
        
        #email & pass need to be passed as attributes!
        if not email or not password:
            raise AttributeError('You need to provide valid email and password:\n'
                                 'scrapy fb -a email="EMAIL" -a password="PASSWORD"')
        else:
            self.email = email
            self.password = password
            
        #page name parsing (added support for full urls)
        if not page:
            raise AttributeError('You need to provide a valid page name to crawl!'
                                 'scrapy fb -a page="PAGENAME"')
        elif page.find('https://www.facebook.com/') != -1:
            self.page = page[25:]
        elif page.find('https://mbasic.facebook.com/') != -1:
            self.page = page[28:]
        elif page.find('https://m.facebook.com/') != -1:
            self.page = page[23:]
        else:
            self.page = page
        
        #parse year 
        assert int(year) <= 2019 and int(year) >= 2006, 'Year must be a number 2006 <= year <= 2019'
        self.year = int(year)    #arguments are passed as strings

        #parse lang, if not provided (but is supported) it will be guessed in parse_home
        if lang=='_':
            self.logger.info('Language attribute not provided, I will try to guess it from the fb interface')
            self.logger.info('To specify, add the lang parameter: scrapy fb -a lang="LANGUAGE"')
            self.logger.info('Currently choices for "LANGUAGE" are: "en", "es", "fr", "it", "pt"')
            self.lang=lang                            
        elif lang == 'en'  or lang == 'es' or lang == 'fr' or lang == 'it' or lang == 'pt':
            self.lang = lang.lower()
        else:
            self.logger.info('Lang "{}" not currently supported'.format(lang))                             
            self.logger.info('Currently supported languages are: "en", "es", "fr", "it", "pt"')                             
            self.logger.info('Change your interface lang from facebook and try again')
            raise AttributeError('Language provided not currently supported')

        #current year, this variable is needed for parse_page recursion
        self.k = 2019
        self.count = 0
        
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
            self.logger.info('Got stuck in "save-device" checkpoint')
            self.logger.info('I will now try to redirect to the correct page')
            return FormRequest.from_response(
                response,
                formdata={'name_action_selected': 'dont_save'},
                callback=self.parse_home
                )
            
        #set language interface
        if self.lang == '_':
            if response.xpath("//input[@placeholder='Search Facebook']"):
                self.logger.info('Language recognized: lang="en"')
                self.lang = 'en'
            elif response.xpath("//input[@placeholder='Buscar en Facebook']"):
                self.logger.info('Language recognized: lang="es"')
                self.lang = 'es'
            elif response.xpath("//input[@placeholder='Rechercher sur Facebook']"):
                self.logger.info('Language recognized: lang="fr"')
                self.lang = 'fr'
            elif response.xpath("//input[@placeholder='Cerca su Facebook']"):
                self.logger.info('Language recognized: lang="it"')
                self.lang = 'it'
            elif response.xpath("//input[@placeholder='Pesquisa no Facebook']"):
                self.logger.info('Language recognized: lang="pt"')
                self.lang = 'pt'                
            else:
                raise AttributeError('Language not recognized\n'
                                     'Change your interface lang from facebook ' 
                                     'and try again')
                                                                 
        #navigate to provided page
        href = response.urljoin(self.page)
        self.logger.info('Scraping facebook page {}'.format(href))
        return scrapy.Request(url=href,callback=self.parse_page)

    def parse_page(self, response):
        '''
        Parse the given page selecting the posts.
        Then ask recursively for another page.
        '''
        #select all posts
        for post in response.xpath("//div[contains(@data-ft,'top_level_post_id')]"):            
            new = ItemLoader(item=FbcrawlItem(),selector=post)
            self.logger.info('Parsing post n = {}'.format(abs(self.count)))
            new.add_xpath('comments', "./div[2]/div[2]/a[1]/text()")        
            new.add_xpath('url', ".//a[contains(@href,'footer')]/@href")
            new.add_xpath('reactions',".//a[contains(@aria-label,'reactions')]/text()")   

            #page_url #new.add_value('url',response.url)
            #returns full post-link in a list
            post = post.xpath(".//a[contains(@href,'footer')]/@href").extract() 
            temp_post = response.urljoin(post[0])
            self.count -= 1
            yield scrapy.Request(temp_post, self.parse_post, priority = self.count, meta={'item':new})       

        #load following page
        #tries to click on "more", otherwise it looks for the appropriate
        #year for 1-click only and proceeds to click on others
        new_page = response.xpath("//div[2]/a[contains(@href,'timestart=') and not(contains(text(),'ent')) and not(contains(text(),number()))]/@href").extract()      
        if not new_page: 
            if response.meta['flag'] == self.k and self.year <= self.k:                
                self.logger.info('There are no more, clicking on year = {}'.format(self.k))
                xpath = "//div/a[contains(@href,'time') and contains(text(),'" + str(self.k) + "')]/@href"
                new_page = response.xpath(xpath).extract()
                if new_page:
                    new_page = response.urljoin(new_page[0])
                    self.k -= 1
                    self.logger.info('Everything OK, new flag: {}'.format(self.k))                                
                    yield scrapy.Request(new_page, callback=self.parse_page, meta={'flag':self.k})
                else:
                    while not new_page: #sometimes the years are skipped 
                        self.logger.info('XPATH not found for year {}'.format(self.k-1))
                        self.k -= 1
                        self.logger.info('Trying with previous year, flag={}'.format(self.k))
                        xpath = "//div/a[contains(@href,'time') and contains(text(),'" + str(self.k) + "')]/@href"
                        new_page = response.xpath(xpath).extract()
                    self.logger.info('New page found with flag {}'.format(self.k))
                    new_page = response.urljoin(new_page[0])
                    self.k -= 1
                    self.logger.info('Now going with flag {}'.format(self.k))
                    yield scrapy.Request(new_page, callback=self.parse_page, meta={'flag':self.k})                            
        else:
            new_page = response.urljoin(new_page[0])
            if 'flag' in response.meta:
                self.logger.info('Page scraped, click on more! flag = {}'.format(response.meta['flag']))
                yield scrapy.Request(new_page, callback=self.parse_page, meta={'flag':response.meta['flag']})
            else:
                self.logger.info('FLAG DOES NOT REPRESENT ACTUAL YEAR')
                self.logger.info('First page scraped, click on more! Flag not set, default flag = {}'.format(self.k))
                yield scrapy.Request(new_page, callback=self.parse_page, meta={'flag':self.k})
                
    def parse_post(self,response):
        new = ItemLoader(item=FbcrawlItem(),response=response,parent=response.meta['item'])
        new.add_xpath('source', "//td/div/h3/strong/a/text() | //span/strong/a/text() | //div/div/div/a[contains(@href,'post_id')]/strong/text()")
        new.add_xpath('shared_from','//div[contains(@data-ft,"top_level_post_id") and contains(@data-ft,\'"isShare":1\')]/div/div[3]//strong/a/text()')
        new.add_xpath('date','//div/div/abbr/text()')
        new.add_xpath('text','//div[@data-ft]//p//text() | //div[@data-ft]/div[@class]/div[@class]/text()')
        new.add_xpath('reactions',"//a[contains(@href,'reaction/profile')]/div/div/text()")  
        
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