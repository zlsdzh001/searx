# -*- coding: utf-8 -*-

"""
 Baidu (Images)
 @website     https://image.baidu.com/
 @provide-api no
 @using-api   no (because of query limit)
 @results     HTML (using search portal)
 @stable      no (HTML can change)
 @parse       url, title, img_src
"""

from json import loads
from urllib.parse import urlencode
from searx import logger
import re

# engine dependent config
categories = ['images']
paging = True
language_support = False

# search-url
base_url = 'https://image.baidu.com/'
search_string = 'search/acjson?tn=resultjson_com&ipn=rj&istype=2&ie=utf-8&{query}&pn={offset}'
image_length = 20

logger = logger.getChild('baidu image engine')

# do search-request
def request(query, params):
    offset = (params['pageno'] - 1) * image_length

    search_path = search_string.format(
        query=urlencode({'word': query}),
        offset=offset)

    params['url'] = base_url + search_path

    return params


# get response from search-request
def response(resp):
    use_resp = resp.content
    try:
        resultdic = loads(use_resp)
    except Exception:
        resultdic = loads(re.sub(r'(?<!\\)\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', r'', resp.text).encode(encoding="utf-8"))
    resultlist = resultdic["data"]
    results = []

    for image in resultlist:
        try:
            if image.__contains__('replaceUrl'):
                url = image["replaceUrl"][0]["FromURL"]
            elif image.__contains__('hoverURL'):
                url = image["hoverURL"]
            elif image.__contains__('thumbURL'):
                url = image["thumbURL"]

            if image.__contains__('fromPageTitle'):
                title = image["fromPageTitle"].replace("<strong>", "").replace("</strong>", "")
            elif image.__contains__('fromPageTitleEnc'):
                title = image["fromPageTitleEnc"]
            else:
                continue

            if image.__contains__('thumbURL'):
                thumbnail = image["thumbURL"]
                img_src = image["thumbURL"]
            else:
                continue

            width = image["width"]
            height = image["height"]

            # append result
            results.append({'template': 'images.html',
                            'url': url,
                            'title': title,
                            'content': '',
                            'thumbnail_src': thumbnail,
                            'width': width,
                            'height': height,
                            'img_src': img_src})
        except Exception as e:
            logger.debug('result error :\n%s', e)

    # return results
    return results