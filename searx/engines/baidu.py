# -*- coding: utf-8 -*-

"""
 Baidu (Web)
 @website     https://www.baidu.com
 @provide-api no
 @using-api   no (because of query limit)
 @results     HTML (using search portal)
 @stable      no (HTML can change)
 @parse       url, title, content
"""

from lxml import html

from searx.engines.xpath import extract_text
from urllib.parse import urlencode
from searx.utils import gen_useragent
from searx.webutils import new_hmac
from searx import settings, logger
import re

logger = logger.getChild('baidu engine')

# engine dependent config
categories = ['general']
paging = True
language_support = False

# search-url
base_url = 'https://www.baidu.com/'
search_string = 's?{query}&pn={offset}'

"""
The regex patterns in this gist are intended only to match web URLs -- http,
https, and naked domains like "example.com".
"""
WEB_URL_REGEX = r"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))"""

# do search-request


def request(query, params):
    offset = (params['pageno'] - 1) * 10 + 1
    search_path = search_string.format(
        query=urlencode({'wd': query}),
        offset=offset)

    params['url'] = base_url + search_path

    params['headers']['User-Agent'] = gen_useragent('Windows NT 6.3; WOW64')

    return params


# get response from search-request
def response(resp):
    results = []

    dom = html.fromstring(resp.text)

    try:
        results.append({'number_of_results': int(dom.xpath('//span[@class="nums_text"]/text()')[0]
                                                 .split(u'\u7ea6')[1].split(u'\u4e2a')[0].replace(',', ''))})
    except Exception as e:
        logger.debug('result error :\n%s', e)

    print(dom.xpath('//div[@class="result c-container new-pmd"]'))
    # parse results
    for result in dom.xpath('//div[@class="result c-container new-pmd"]'):
        title = extract_text(result.xpath('.//h3/a')[0])

        # when search query is Chinese words
        try:
            url = result.xpath('.//h3[@class="t"]/a')[0].attrib.get('href')
            # To generate miji url with baidu url
            content = extract_text((result.xpath('.//div[@class="c-abstract"]') or 
                result.xpath('.//div[@class="c-abstract c-abstract-en"]')))

            # append result
            results.append({'url': url,'title': title,'content': content})

        # when search query is English words
        except Exception:
            try:
                url = result.xpath('.//h3[@class="t"]/a')[0].attrib.get('href')
                showurl = extract_text(result.xpath('.//div[@class="f13"]/a')).replace('百度快照', '').replace('翻译此页', '')
                content = extract_text(result.xpath('.//div[@class="c-span18 c-span-last"]')[0])
                # To generate miji url with baidu url
                url = settings['result_proxy'].get('server_name') + "/url_proxy?proxyurl=" + \
                    url + "&token=" + new_hmac(settings['result_proxy']['key'], url.encode("utf-8"))

                # append result
                results.append({'url': url,
                                'title': title,
                                'content': content})
            except Exception as e:
                logger.debug('result error :\n%s', e)

    # return results
    return results