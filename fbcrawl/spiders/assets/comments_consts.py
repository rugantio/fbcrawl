# comments xpath query constants
#
# For simplicity, this file contains all the xpath(s) used in the comments spider
# The purpose of this document is to enhance readability and limit the are of changes
# All Constants in this File needs to be constructed as follows: x[MEANINGFUL_TARGET_NAME]_TAGNAME
# All Container Elements ( Elements with nested attributes ) in this File needs to be constructed as follows: x[MEANINGFUL_TARGET_NAME]_

xNESTED_COMMENT_: dict = {
    'root':  './/div[string-length(@class) = 2 and count(@id)=1 and contains("0123456789", substring(@id,1,1)) and .//div[contains(@id,"comment_replies")]][%s]',
    'attributes': {
        'source': './/h3/a/text()',
        'answer': './/a[contains(@href,"repl")]/@href',
    }
}

xREGULAR_COMMENT_: dict = {
    'root': './/div[contains(@id,"see_next")]',
    'attributes': {
        'source': './/h3/a/text()',
        'source_url': './/h3/a/@href',
        'text': './/div[h3]/div[1]//text()',
        'date': './/abbr/text()',
        'reactions': './/a[contains(@href,"reaction/profile")]//text()'
    }
}

xNEXT_COMMENTS_: dict = {
    'root': './/div[string-length(@class) = 2 and count(@id)=1 and contains("0123456789", substring(@id,1,1)) and not(.//div[contains(@id,"comment_replies")])]',
    'attributes': {
        'new_page': './/@href',
    }
}

xPREV_COMMENTS_DIV: str = './/div[contains(@id,"see_prev")]'

xREPLY_: dict = {
    'root': './/div[contains(@id,"see_next")]',
    'attributes': {
        'source': './/h3/a/text()',
        'source_url': './/h3/a/@href',
        'text_root': './/div[1]//text()',
        'text_child': './/div[h3]/div[1]//text()',
        'date': './/abbr/text()',
        'reactions': './/a[contains(@href,"reaction/profile")]//text()',
        'back': '//div[contains(@id,"comment_replies_more_1")]/a/@href'
    }
}

xAll_ROOT_DIV: str = '//div[contains(@id,"root")]/div/div/div[count(@id)=1 and contains("0123456789", substring(@id,1,1))]'
xAll_REPLIES_DIV: str = '//div[contains(@id,"root")]/div/div/div[count(@id)=1 and contains("0123456789", substring(@id,1,1))]'
