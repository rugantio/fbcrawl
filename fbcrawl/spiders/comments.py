import scrapy

from scrapy.loader import ItemLoader
from scrapy.http import FormRequest
from fbcrawl.items import FbcrawlItem


class FacebookSpider(scrapy.Spider):
    """
    Parse FB comments, given a page (needs credentials)
    """    
    name = "comments"

    def __init__(self, email='', password='', page='', **kwargs):
        super(FacebookSpider, self).__init__(**kwargs)
    
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
            # Handle 'Someone tried to log into your account' warning.
            return FormRequest.from_response(
                response, callback=self.parse_home, dont_filter=True,)
        # Else go to the user profile.
        href = response.urljoin(self.page)
        self.logger.info('Parse function called on %s', href)
        return scrapy.Request(
            url=href,
            callback=self.parse_page,
        )

    def parse_page(self, response):
        for post in response.xpath('//div[count(@class)=1 and count(@id)=1 and contains("0123456789", substring(@id,1,1))]'): #select all posts            
            new = ItemLoader(item=FbcrawlItem(),selector=post)
            new.add_xpath('source', "./div/h3/a/text()")
            new.add_xpath('text',"//div/div/span[not(contains(text(),' · '))]/text() | ./div/div/text()")
            yield new.load_item()
        
        rispostina = response.xpath('//div/a[contains(text(),"rispost")]/@href')

        for i in range(len(rispostina)):
            risp = response.urljoin(rispostina[i].extract())
            yield scrapy.Request(risp, callback=self.parse_rispostina)
        
        next_page = response.xpath("//div[contains(@id,'see_next')]/a/@href")
        if len(next_page) > 0:
            next_page = response.urljoin(next_page[0].extract())
            yield scrapy.Request(next_page, callback=self.parse_page)

    def parse_rispostina(self,response):
        for daje in response.xpath("//div[contains(@id,'root')]/div/div/div"): #select all posts                                
            new = ItemLoader(item=FbcrawlItem(),selector=daje)
            new.add_xpath('source', ".//h3/a/text()")#| ./div/div/h3/a/text()")             
            new.add_xpath('text',".//span[not(contains(text(),' · ')) and not(contains(text(),'Visualizza'))]/text() | .//div/text()")
            yield new.load_item()
