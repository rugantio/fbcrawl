import scrapy
import logging

from scrapy.loader import ItemLoader
from scrapy.http import FormRequest
from scrapy.exceptions import CloseSpider
from fbcrawl.items import FbcrawlItem, parse_date2
from datetime import datetime
from fbcrawl.spiders.assets.fbcrawl_consts import *


    
class FacebookSpider(scrapy.Spider):
    '''
    Parse FB pages (needs credentials)
    '''    
    name = 'fb'
    custom_settings = {
        'FEED_EXPORT_FIELDS': ['source','shared_from','date','text', \
                               'reactions','likes','ahah','love','wow', \
                               'sigh','grrr','comments','post_id','url']
    }
    
    def __init__(self, *args, **kwargs):
        #turn off annoying logging, set LOG_LEVEL=DEBUG in settings.py to see more logs
        logger = logging.getLogger('scrapy.middleware')
        logger.setLevel(logging.WARNING)
        super().__init__(*args,**kwargs)
        
        #email & pass need to be passed as attributes!
        if 'email' not in kwargs or 'password' not in kwargs:
            raise AttributeError('You need to provide valid email and password:\n'
                                 'scrapy fb -a email="EMAIL" -a password="PASSWORD"')
        else:
            self.logger.info('Email and password provided, using these as credentials')

        #page name parsing (added support for full urls)
        if 'page' not in kwargs:
            raise AttributeError('You need to provide a valid page name to crawl!'
                                 'scrapy fb -a page="PAGENAME"')
        elif self.page.find('https://www.facebook.com/') != -1:
            self.page = self.page[25:]
            self.logger.info('Page attribute provided, scraping "{}"'.format(self.page))
        elif self.page.find('https://mbasic.facebook.com/') != -1:
            self.page = self.page[28:]
            self.logger.info('Page attribute provided, scraping "{}"'.format(self.page))
        elif self.page.find('https://m.facebook.com/') != -1:
            self.page = self.page[23:]
            self.logger.info('Page attribute provided, scraping "{}"'.format(self.page))
        else:
            self.logger.info('Page attribute provided, scraping "{}"'.format(self.page))
       
        #parse date
        if 'date' not in kwargs:
            self.date = datetime(2014,1,1)
            self.year = 2014
        else:
            print(type(kwargs['date']))
            self.date = datetime.strptime(kwargs['date'],'%Y-%m-%d')
            self.year = datetime.now().year - 1

        #parse lang, if not provided (but is supported) it will be guessed in parse_home
        if 'lang' not in kwargs:
            self.logger.info('Language attribute not provided, I will try to guess it from the fb interface')
            self.logger.info('To specify, add the lang parameter: scrapy fb -a lang="LANGUAGE"')
            self.logger.info('Currently choices for "LANGUAGE" are: "en", "es", "fr", "it", "pt"')
            self.lang = '_'                       
        elif self.lang == 'en'  or self.lang == 'es' or self.lang == 'fr' or self.lang == 'it' or self.lang == 'pt':
            self.logger.info('Language attribute recognized, using "{}" for the facebook interface'.format(self.lang))
        else:
            self.logger.info('Lang "{}" not currently supported'.format(self.lang))                             
            self.logger.info('Currently supported languages are: "en", "es", "fr", "it", "pt"')                             
            self.logger.info('Change your interface lang from facebook settings and try again')
            raise AttributeError('Language provided not currently supported')
            
        #current year, this variable is needed for parse_page recursion
        self.k = 2019
        #count number of posts, used to prioritized parsing and correctly insert in the csv
        self.count = 0
        
        self.start_urls = ['https://mbasic.facebook.com']    

    def parse(self, response):
        '''
        Handle login with provided credentials
        '''
        return FormRequest.from_response(
                response,
                formxpath=xLOGIN_FORM,
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
        if response.xpath(xSAVE_DEVICE_HYPERLINK):
            self.logger.info('Got stuck in "save-device" checkpoint')
            self.logger.info('I will now try to redirect to the correct page')
            return FormRequest.from_response(
                response,
                formdata={'name_action_selected': 'dont_save'},
                callback=self.parse_home
                )
            
        #set language interface
        if self.lang == '_':
            found = False
            for key,val in xUI_LANGUAGES_.items():
                 if response.xpath(val):
                    self.logger.info(f'Language recognized: lang="[0]"',key)
                    self.lang = key
                    found=True
                    break 
            
            if not found:
                    raise AttributeError('Language not recognized\n'
                                     'Change your interface lang from facebook ' 
                                     'and try again')
                                                                 
        #navigate to provided page
        href = response.urljoin(self.page)
        self.logger.info('Scraping facebook page {}'.format(href))
        return scrapy.Request(url=href,callback=self.parse_page,meta={'index':1})

    def parse_page(self, response):
        '''
        Parse the given page selecting the posts.
        Then ask recursively for another page.
        '''
#        #open page in browser for debug
#        from scrapy.utils.response import open_in_browser
#        open_in_browser(response)
    
        #select all posts
        for post in response.xpath(xPOST_['root']):     
 
            many_features = post.xpath(xPOST_['attributes']['many_features']).get()
            date = []
            date.append(many_features)
            date = parse_date2(date)
            current_date = datetime.strptime(date,'%Y-%m-%d %H:%M:%S')

            if self.date > current_date:
                raise CloseSpider('Reached date: {}'.format(self.date))
            new = ItemLoader(item=FbcrawlItem(),selector=post)
            self.logger.info('Parsing post n = {}'.format(abs(self.count)))
            new.add_xpath('comments', xPOST_['attributes']['comments'])     
            new.add_xpath('date',xPOST_['attributes']['date'])
            new.add_xpath('post_id',xPOST_['attributes']['post_id'])
            new.add_xpath('url', xPOST_['attributes']['url'])

            #page_url #new.add_value('url',response.url)
            #returns full post-link in a list
            post = post.xpath(xPOST_['attributes']['post-link']).extract() 
            temp_post = response.urljoin(post[0])
            self.count -= 1
            yield scrapy.Request(temp_post, self.parse_post, priority = self.count, meta={'item':new})       

        #load following page, try to click on "more"
        #after few pages have been scraped, the "more" link might disappears 
        #if not present look for the highest year not parsed yet, click once 
        #and keep looking for "more"
        new_page = response.xpath(xMORE_POSTS_HYPERLINK).extract()      
        if not new_page: 
            if response.meta['flag'] == self.k and self.k >= self.year:                
                self.logger.info('There are no more, flag set at = {}'.format(self.k))
                xpath = xYEAR_HYPERLINK % (str(self.k))
                new_page = response.xpath(xpath).extract()
                if new_page:
                    new_page = response.urljoin(new_page[0])
                    self.k -= 1
                    self.logger.info('Everything OK, new flag: {}'.format(self.k))                                
                    yield scrapy.Request(new_page, callback=self.parse_page, meta={'flag':self.k})
                else:
                    while not new_page: #sometimes the years are skipped this handles small year gaps
                        self.logger.info('XPATH not found for year {}'.format(self.k-1))
                        self.k -= 1
                        self.logger.info('Trying with previous year, flag={}'.format(self.k))
                        if self.k < self.year:
                            self.logger.info('The previous year to crawl is less than the parameter year: {} < {}'.format(self.k,self.year))
                            self.logger.info('This is not handled well, please re-run with -a year="{}" or less'.format(self.k))
                            break                        
                        xpath = xYEAR_HYPERLINK % (str(self.k))
                        new_page = response.xpath(xpath).extract()
                    self.logger.info('New page found with flag {}'.format(self.k))
                    new_page = response.urljoin(new_page[0])
                    self.k -= 1
                    self.logger.info('Now going with flag {}'.format(self.k))
                    yield scrapy.Request(new_page, callback=self.parse_page, meta={'flag':self.k}) 
            else:
                self.logger.info('Crawling has finished with no errors!')
        else:
            new_page = response.urljoin(new_page[0])
            if 'flag' in response.meta:
                self.logger.info('Page scraped, click on more! new_page = {} flag = {}'.format(new_page,date))
                yield scrapy.Request(new_page, callback=self.parse_page, meta={'flag':response.meta['flag']})
            else:
#                self.logger.info('FLAG DOES NOT ALWAYS REPRESENT ACTUAL YEAR')
                self.logger.info('First page scraped, click on more {}! Flag not set, default flag = {}'.format(new_page,date))
                yield scrapy.Request(new_page, callback=self.parse_page, meta={'flag':self.k})
                
    def parse_post(self,response):
        new = ItemLoader(item=FbcrawlItem(),response=response,parent=response.meta['item'])
        new.add_xpath('source',xPOST_['attributes']['source'])
        new.add_xpath('shared_from',xPOST_['attributes']['shared_from'])
     #   new.add_xpath('date','//div/div/abbr/text()')
        new.add_xpath('text',xPOST_['attributes']['text'])
        new.add_xpath('reactions',xPOST_['attributes']['reactions'])  
        
        reactions = response.xpath(xREACTIONS_['root'])
        reactions = response.urljoin(reactions[0].extract())
        yield scrapy.Request(reactions, callback=self.parse_reactions, meta={'item':new})
        
    def parse_reactions(self,response):
        new = ItemLoader(item=FbcrawlItem(),response=response, parent=response.meta['item'])
        new.context['lang'] = self.lang           
        new.add_xpath('likes',xREACTIONS_['attributes']['likes'])
        new.add_xpath('ahah',xREACTIONS_['attributes']['ahah'])
        new.add_xpath('love',xREACTIONS_['attributes']['love'])
        new.add_xpath('wow',xREACTIONS_['attributes']['wow'])
        new.add_xpath('sigh',xREACTIONS_['attributes']['sigh'])
        new.add_xpath('grrr',xREACTIONS_['attributes']['grrr']) 
        yield new.load_item()       