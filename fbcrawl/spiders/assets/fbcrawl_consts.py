# fbcrawl xpath query constants
#
# For simplicity, this file contains all the xpath(s) used in the fbcrawl spider
# The purpose of this document is to enhance readability and limit the are of changes
# All Constants in this File needs to be constructed as follows: x[MEANINGFUL_TARGET_NAME]_TAGNAME
# All Container Elements ( Elements with nested attributes ) in this File needs to be constructed as follows: x[MEANINGFUL_TARGET_NAME]_

xLOGIN_FORM: str = '//form[contains(@action, "login")]'

xSAVE_DEVICE_HYPERLINK: str = "//div/a[contains(@href,'save-device')]"

xUI_LANGUAGES_: dict = {
    'en': "//input[@placeholder='Search Facebook']",
    'es': "//input[@placeholder='Buscar en Facebook']",
    'fr': "//input[@placeholder='Rechercher sur Facebook']",
    'it': "//input[@placeholder='Cerca su Facebook']",
    'pt': "//input[@placeholder='Pesquisa no Facebook']"
}

xPOST_: dict = {
    'root': "//div[contains(@data-ft,'top_level_post_id')]",
    'attributes': {
        'source': "//td/div/h3/strong/a/text() | //span/strong/a/text() | //div/div/div/a[contains(@href,'post_id')]/strong/text()",
        'shared_from': '//div[contains(@data-ft,"top_level_post_id") and contains(@data-ft,\'"isShare":1\')]/div/div[3]//strong/a/text()',
        'text': '//div[@data-ft]//p//text() | //div[@data-ft]/div[@class]/div[@class]/text()',
        'reactions': "//a[contains(@href,'reaction/profile')]/div/div/text()",
        'many_features': './@data-ft',
        'comments': './div[2]/div[2]/a[1]/text()',
        'date': './@data-ft',
        'post_id': './@data-ft',
        'url': ".//a[contains(@href,'footer')]/@href",
        'post-link': ".//a[contains(@href,'footer')]/@href",
    }
}

xMORE_POSTS_HYPERLINK: str = "//div[2]/a[contains(@href,'timestart=') and not(contains(text(),'ent')) and not(contains(text(),number()))]/@href"

xYEAR_HYPERLINK: str = "//div/a[contains(@href,'time') and contains(text(),'%s')]/@href"

xREACTIONS_: dict = {
    'root': "//div[contains(@id,'sentence')]/a[contains(@href,'reaction/profile')]/@href",
    'attributes': {
        'likes': "//td/div/h3/strong/a/text() | //span/strong/a/text() | //div/div/div/a[contains(@href,'post_id')]/strong/text()",
        'ahah': '//div[contains(@data-ft,"top_level_post_id") and contains(@data-ft,\'"isShare":1\')]/div/div[3]//strong/a/text()',
        'love': '//div[@data-ft]//p//text() | //div[@data-ft]/div[@class]/div[@class]/text()',
        'wow': "//a[contains(@href,'reaction/profile')]/div/div/text()",
        'sigh': './@data-ft',
        'grrr': './div[2]/div[2]/a[1]/text()',
    }
}
