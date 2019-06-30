import scrapy

from scrapy.loader import ItemLoader
from scrapy.exceptions import CloseSpider
from fbcrawl.spiders.fbcrawl import FacebookSpider
from fbcrawl.items import EventsItem, parse_date, parse_date2

from datetime import datetime

class EventsSpider(FacebookSpider):
    """
    Parse FB events, given a page (needs credentials)
    """
    name = "events"
    custom_settings = {
        'FEED_EXPORT_FIELDS': ['name','where','location','photo','start_date', \
                               'end_date','description'],
        'DUPEFILTER_CLASS' : 'scrapy.dupefilters.BaseDupeFilter',
        'CONCURRENT_REQUESTS' : 1
    }

    def __init__(self, *args, **kwargs):
        self.page = kwargs['page']
        super().__init__(*args,**kwargs)

    def parse_page(self, response):
        yield scrapy.Request(url=response.urljoin('%s/events' % self.page),
                             callback=self.parse_events,
                             priority=10,
                             meta={'index':1})

    def parse_events(self, response):
        TABLE_XPATH='/html/body/div/div/div[2]/div/table/tbody/tr/td/div[2]/div/div/div[2]/div/table/tbody/tr'
        for event in response.xpath(TABLE_XPATH):
            url = event.xpath('//td/div/div/span[3]/div/a[1]/@href').extract_first()
            yield response.follow(url, callback=self.parse_event)

    def parse_event(self, response):
        EVENT_NAME='/html/body/div/div/div[2]/div/table/tbody/tr/td/div[2]/div[2]/div[1]/h3/text()'
        EVENT_WHERE='/html/body/div/div/div[2]/div/table/tbody/tr/td/div[3]/div/div[2]/table/tbody/tr/td[2]/dt/div/text()'
        EVENT_LOCATION='/html/body/div/div/div[2]/div/table/tbody/tr/td/div[3]/div/div[2]/table/tbody/tr/td[2]/dd/div/text()'
        DATE='/html/body/div/div/div[2]/div/table/tbody/tr/td/div[3]/div/div[1]/table/tbody/tr/td[2]/dt/div/text()'
        EVENT_DESCRIPTION='/html/body/div/div/div[2]/div/table/tbody/tr/td/table/tbody/tr/td/div[2]/div[2]/div[2]/div[2]/text()'
        EVENT_COVER='/html/body/div/div/div[2]/div/table/tbody/tr/td/div[2]/div[1]/a/img/@src'
        date = response.xpath(DATE).extract_first()
        start_date = date.split('–')[0] or None
        end_date = date.split('–')[1] or None
        name = response.xpath(EVENT_NAME).extract_first()
        self.logger.info('Parsing event %s' % name)
        yield EventsItem(
            name=name,
            where=response.xpath(EVENT_WHERE).extract_first(),
            location=response.xpath(EVENT_LOCATION).extract_first(),
            photo=response.xpath(EVENT_COVER).extract_first(),
            start_date=start_date,
            end_date=end_date,
            description=response.xpath(EVENT_DESCRIPTION).extract_first()
        )
