# fbcrawl
Fbcrawl is an advanced crawler for Facebook, written in python, based on the [Scrapy](https://scrapy.org/) framework. 

## DISCLAIMER
This software is NOT to be used, for any reason. It is not authorized by Facebook and neither compliant with Facebook's [robots.txt](https://www.facebook.com/robots.txt). It violates Facebook's [terms and conditions on scraping](http://www.facebook.com/apps/site_scraping_tos_terms.php).

It is released for educational purposes only, to show how a crawler can be made to recursively parse a facebook page.

# Introduction

<div style="text-align:center">
<img src="./trump.png" alt="Donald Trump" width="1080">
</div>

EDIT: fbcrawl can now crawl comments! check out the "how to crawl comments" section!

What features can fbcrawl obtain? Everything that you see in the table is crawled by default. I decided to simplify the timestamp feature, leaving out the hour and to ignore comments and commentators, which are going to be parsed post-by-post by another crawler.

You can see that fbcrawl makes asynchronous requests and thus the tuples are not in chronological order, populates a csv or a json file.

Fbcrawl makes use of the mobile version of facebook: [https://mbasic.facebook.com](https://mbasic.facebook.com) because it's all plain HTML and we can navigate easily through the pages without cumbersome javascript injections. 

Unfortunately one thing I was not able to retrieve is the post sharing number because it's not displayed in this basic version, if someone knows how to collect this feature, please let me know.

## Installation
Requirements are: **python3** (python2 is also supported), **scrapy** and other dependencies libraries (twisted, libxml2 etc.).

Scrapy can be installed through the package manager of the distribution (in my arch box is simply called "scrapy") or through internal python package system that also should take care of required dependencies (just don't mix the two methods, it would produces conflicts), typing:

 ```pip install scrapy```

## Architecture
The way scrapy works is through an engine that manages granularly every step of the crawling process.

<img src="https://docs.scrapy.org/en/latest/_images/scrapy_architecture_02.png" width="800">

The project is thus divided in several files that serve different purposes:

\fbcrawl
<br />&nbsp;&nbsp;&nbsp;&nbsp;
    README.md -- this file
<br />&nbsp;&nbsp;&nbsp;&nbsp;
    scrapy.cfg -- ini-style file that defines the project
<br />&nbsp;&nbsp;&nbsp;&nbsp;
    \fbcrawl
<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        \__init.py__
<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        **items.py** -- defines the fields that we want to export
<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        middlewares.py
<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        **pipelines.py** -- defines how we handle each item (the set of fields)
<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        **settings.py** -- all the parameter settings of the project
<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        \spiders
<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        \__init.py__
<br />&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        **fbcrawl.py** -- defines the crawling functions and the selectors

## The Spider (fbcrawl.py)
The core of the crawler is this spider class, that defines the spider name, `fbcrawl`. On init it navigates to `mbasic.facebook.com` and calls the parse method which logs into facebook according to the provided `credentials`, that are passed as parameters at execution time (see "How to use"). Several checkpoints and exceptions are nicely handled to provide a clean log in, after which the parse_page method is called with the page name given at runtime and the crawling process begins recursively retrieving all the posts in every page and for each post it retrieves all the features, calling parse_post, and all the reactions (you guessed it) using parse_reactions.

The webpage are parsed and the fields are extracted with **XPath** scrapy selectors. These selectors are based on python lib `lxml` so they are very fast (supposedly better than `beautifulsoup`). Another way to extract relevant data is to use **CSS** selector.

I decided to use XPath to navigate the webpage as one would navigate a filesystem, taking into consideration only the `/article` elements. If you know nothing about XPath [this guide](https://blog.scrapinghub.com/2016/10/27/an-introduction-to-xpath-with-examples/) and [this cheatsheet](http://www.zvon.org/comp/r/tut-XPath_1.html#Pages~List_of_XPaths) can be helpful, along with the original [W3C docs](https://www.w3.org/TR/2017/REC-xpath-31-20170321/).

The XPath are easy to obtain using Firefox's or Chromium's dev tools, but sometimes the field relative to a property changes location, which is something to keep in mind. For example, notice how I had to handle the `source` field: `new.add_xpath('source', '//span/strong/a/text() | //div/a/strong/text() | //td/div/h3/strong/a/text()')`. It has a selector that connects three different XPath connected with an OR operator. This kind of juggling is helpful to maintain consistency of the data in our table. The control on the data and the policy to use is often implemented in the Item Pipeline (in our simple project we are using ).

So the parse methods populates Item fields (to be explained in the next section) and pass control over to the Item Loader.

Refer to Scrapy's [Spider documentation](https://docs.scrapy.org/en/latest/topics/spiders.html) for more info.

## Items (items.py)
This file defines an Item class, so that the fields that we have extracted can be grouped in Items and organized in a more concise manner. Item objects are simple containers used to collect the scraped data. They provide a dictionary-like API (similar to Django Models) with a convenient syntax for declaring their available fields.

I have extracted every field present in the post elements and add a few local ones. Namely for each article we have:

```
source      -    name of the post publisher, if it's shared it's the original one
date        -    timestamp in datetime.date() format
text        -    full text of the post, if empty it's a pic or a video
reactions   -    total number of reactions
likes       -    number of likes 
ahah        -    number of ahah
love        -    number of love
wow         -    number of wow
sigh        -    number if sigh
grrr        -    number of grrr
comments    -    number of comments
url         -    relative link to the post
```
Notice that this file is also used to modify the fields that we want to change before deciding what to do with the items. To accomplish this kind of tasks, scrapy provides a series of built-in "`processors`" (such as the `input_processor`) and functions (such as `TakeFirst()`) that we can use to adjust the fields we want. These are explained in the official [Item Loaders](https://docs.scrapy.org/en/latest/topics/loaders.html) section of the documentation.

Also Refer to Scrapy's [Item documentation](https://docs.scrapy.org/en/latest/topics/items.html) for more info.

## Settings (settings.py)
Scrapy is a very powerful framework and it allows complex tweaking to be put in place. In this project we changed just only a handful of settings, but keep in mind that there are a lot of them.

Pipelines are useful methods to manipulate items as you can see from the [official guide](https://doc.scrapy.org/en/latest/topics/item-pipeline.html). In our project I have prepared a pipeline to drop all the posts that were made before a certain date, you can check out the code in `pipelines.py`. Pipelines are not initialized by default, they need to be declared here. Since we can define more than one of them a number  in the 0-1000 range is used to indicate priority (lower is first). This is why we have set:
```
ITEM_PIPELINES = {
    'fbcrawl.pipelines.FbcrawlPipeline': 300,
}
```
Besides dropping our items according to timestamp we can also export it locally to a CSV or a JSON. In case we choose to create a CSV file we need to specify the order of the columns by explicitly setting:
```
FEED_EXPORT_FIELDS = ["source", "date", "text", "reactions","likes","ahah","love","wow","sigh","grrr","comments","url"] 
```

Scrapy's default behavior is to follow robots.txt guidelines, so we need to disable this by setting `ROBOTSTXT_OBEY = False`.

## How to use
Make sure that scrapy is installed and clone this repository. Navigate through the project's top level directory and launch scrapy with:
```
scrapy crawl fb -a email="EMAILTOLOGIN" -a password="PASSWORDTOLOGIN" -a page="NAMEOFTHEPAGETOCRAWL"

```
the keywords will be passed to the \__init__ method of fbcrawl.py.

If you want to (also) export the table locally you don't need to add a new pipeline because scrapy has an option to store all the items in a CSV or in a JSON file (or in XML). This is especially useful if you want to do some client-side analysis for example using pandas or if you want to replicate the table in a file system and not in the database. To export to CSV type:
```
scrapy crawl fb -a email="EMAILTOLOGIN" -a password="PASSWORDTOLOGIN" -a page="NAMEOFTHEPAGETOCRAWL" -o DUMPFILE.csv
```
To export to JSON the option is the same, just change the extension:
```
scrapy crawl fb -a email="EMAILTOLOGIN" -a password="PASSWORDTOLOGIN" -a page="NAMEOFTHEPAGETOCRAWL" -o DUMPFILE.json
```
Keep in mind that the default behavior is to append the field crawled over to the already existing file and not to overwrite it. There are many other ways of exporting, check out the [exporter reference](https://doc.scrapy.org/en/latest/topics/exporters.html) if you want to know more.

More information regarding Scrapy's [Deployment](https://doc.scrapy.org/en/latest/topics/deploy.html) and [Common Practices](https://doc.scrapy.org/en/latest/topics/practices.html) are present in the official documentation.

# How to crawl comments 

A new spider is now dedicated to crawl all the comments from a post, along with the name of the commentators. It's been written in a rush, so it's pretty ugly and no other metadata is available at the moment (PR welcome!). 
You can try it out with:
```
scrapy crawl comments -a email="EMAILTOLOGIN" -a password="PASSWORDTOLOGIN" -a page="LINKOFTHEPOSTTOCRAWL" -o DUMPFILE.csv
```
Make sure that the `page` option is a proper post link, that begins with the pagename and is accessible from mbasic.facebook.com.

# TODO

Number of comments is wrong, it only counts direct comments and not reply comments, because that's how `mbasic.facebook.com` works. Also the number of shares is not retrieved. To fix both of these issues:

* extract URL of post and use m.facebook.com to retrieve these data

At the moment crawling starts from the beginning of 2017, it needs to go back until 2004:

* write appropriate recursive functions in parse_page
* set two parameters at runtime (**from** ant **until**) in \__init__
* memorize datetime in a local variable in parsing method and check that datetime in the post respect the period, otherwise stop crawling
* this is faster than using the pipeline but might not be as accurate, so change pipelines.py and settings.py accordingly

The crawler works only in italian:

* add english interface support

Comments and commentators are naively parsed:

* write a spyder that crawls all the metadata possible
