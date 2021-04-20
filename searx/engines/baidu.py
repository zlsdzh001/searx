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
import requests

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

    # parse results
    for result in dom.xpath('//div[@class="result c-container new-pmd"]'):
        title = extract_text(result.xpath('.//h3/a')[0])

        # when search query is Chinese words
        try:
            url = result.xpath('.//h3[@class="t"]/a')[0].attrib.get('href')
            url = get_baidu_link_location(url)
            
            # To generate miji url with baidu url
            content = extract_text((result.xpath('.//div[@class="c-abstract"]') or 
                result.xpath('.//div[@class="c-abstract c-abstract-en"]')))

            # append result
            results.append({'url': url,'title': title,'content': content})

        # when search query is English words
        except Exception:
            try:
                url = result.xpath('.//h3[@class="t"]/a')[0].attrib.get('href')
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

def get_baidu_link_location(url:str):
    if len(url.strip()) == 0:
        return url
    if url.find('www.baidu.com/link?url=') == 0:
        return url
    resp = requests.get(url, allow_redirects=False)
    if resp.is_redirect == False:
        return url
    return resp.headers['location']