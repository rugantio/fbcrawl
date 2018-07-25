import scrapy

from datetime import datetime


from scrapy.loader import ItemLoader
from scrapy.http import FormRequest
from fbcrawl.items import FbcrawlItem


class FacebookSpider(scrapy.Spider):
    """
    Parse FB pages (needs credentials)
    """    
    name = "fb"

    def __init__(self, email='', password='', til='2004-1-1', **kwargs):
        super(FacebookSpider, self).__init__(**kwargs)

        til = til.split(sep='-')
        self.til = datetime(int(til[0]),int(til[1]),int(til[2]))
        
        self.email = email
        self.password = password
        self.start_urls = ['https://mbasic.facebook.com']    

    def parse(self, response):
        return FormRequest.from_response(
                response,
                formxpath='//form[contains(@action, "login")]',
                formdata={'email': self.email,'pass': self.password},
                callback=self.parse_home
        )
  
    def parse_home(self, response):
        '''Parse user news feed page'''
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
            # Handle `Someone tried to log into your account` warning.
            return FormRequest.from_response(
                response, callback=self.parse_home, dont_filter=True,)
        # Else go to the user profile.
        href = 'https://mbasic.facebook.com/ivacciniealtricomplottileggendari'
        self.logger.info('Parse function called on %s', href)
        return scrapy.Request(
            url=href,
            callback=self.parse_page,
        )



    def parse_page(self, response):
#        from scrapy.utils.response import open_in_browser
#        open_in_browser(response)
        
        for post in response.xpath("//div[contains(@id,'u_0_')]"):
#            self.logger.info('Parse function called on %s', response.url)
#            self.logger.info('Parsing page number %d', i)
#            from scrapy.utils.response import open_in_browser
#            open_in_browser(response)
            post = post.xpath("//a[contains(text(),'Notizia completa')]/@href").extract()
#   
            for i in range(len(post)):
                temp_post = response.urljoin(post[i])        
                yield scrapy.Request(temp_post, self.parse_post,dont_filter = True)            

#        next_page = response.xpath("//div/a[contains(text(),'Altri')]/@href")
#        if len(next_page) > 0:
#            next_page = response.urljoin(next_page[0].extract())
#            yield scrapy.Request(next_page, callback=self.parse_page)
#    
#        else:
#            next_page = response.xpath("//div/a[contains(text(),'2017')]/@href")
#            if len(next_page) > 0:
#                next_page = response.urljoin(next_page[0].extract())
#                yield scrapy.Request(next_page, callback=self.parse_page)
#                
    def parse_post(self,response):
        new = ItemLoader(item=FbcrawlItem(),response=response)
#        from scrapy.utils.response import open_in_browser
#        open_in_browser(response)
#         #        ("//div[string-length(@id)=15 or string-length(@id)=16]")
       # new.add_xpath('comments',"//div[string-length(@id)=15 or string-length(@id)=16]//div/text()")               
# {}' .format(next_comment_page))
        new.add_xpath('source', '//span/strong/a/text()')
        new.add_xpath('date', '//div/div/abbr/text()')
        new.add_xpath('text','//div[@data-ft]//p//text()')
        
        next_comment_page = response.xpath("//div/div[contains(@id,'see_next')]/a/@href")
        while len(next_comment_page) > 0:
            next_comment_page = response.urljoin(next_comment_page[0].extract())        
            yield scrapy.Request(next_comment_page, callback=self.parse_comments, dont_filter = True, \
                             meta={'new':new})
#            self.logger.info('Parsing page number %d', i)

#            from scrapy.utils.response import open_in_browser
#            open_in_browser(response)0
#            new.load_item()


# 
#        yield new.load_item()

    def parse_comments(self,response):
        self.logger.info('\n\n PAGINA COMMENTI  \n\n')
        new = response.meta['new']    
        new.add_xpath('commentators',"//div[number(@id)>1]/div/h3/a[@href]/text()")
        yield new.load_item()