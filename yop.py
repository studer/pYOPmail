# -*- coding: utf-8 -*-

import requests
from os.path import join
from dateutil import parser
from collections import OrderedDict
from bs4 import BeautifulSoup as bs4


class Yop(object):
    def __init__(self, username=None, url='http://www.yopmail.com/', lang='en', id_fix=u'm'):
        self._url = url
        self._lang = lang
        self._username = username
        self._id_fix = id_fix
        self._session = requests.Session()
        self._session.stream = False

    def list_mails(self):
        payload = {'login': self._username}
        r = self._session.get(join(self._url, self._lang, 'rss.php'), params=payload)

        return self._compress(self._parse_list_mails(r.text))

    def _parse_list_mails(self, source):
        html = bs4(source, 'lxml')
        messages = html.find_all('item')

        return [[m.find('pubdate').get_text(), m.find('dc:creator').get_text(), m.find('title').get_text(), self._id_fix + m.find('guid').get_text()] for m in messages]

    def _parse_elem(self, elem):
        if 'jour' in elem.attrs.get('class'):
            return elem.get_text().capitalize()
        else:
            return [i.get_text() for i in elem.find_all('span')[1:]] + [elem.a.get('href').split('id=')[-1]]

    def get_mail(self, mail_id):
        payload = {'id': mail_id}
        r = self._session.get(join(self._url, self._lang, 'mail.php'), params=payload)

        return self._parse_get_mail(r.content)

    def _parse_get_mail(self, source):
        html = bs4(source)
        message = html.find('div', id='mailmillieu')

        for i in message.find_all('script'):
            i.decompose()

        message.find_all('span')[-1].decompose()

        return message

    def read_mail(self, mail_id):
        return self.get_mail(mail_id).get_text()

    def click_mail(self, mail_id, limit=None):
        message = self.get_mail(mail_id)
        results = []

        for link in message.find_all('a')[:limit]:
            title, url = link.get_text(), link.get('href')
            print title
            print url
            try:
                r = self._session.get(url)
                print r.status_code
                results += [r]
            except:
                print 'Error'

        return results

    def click_last_mail(self, limit=1):
        last_mail_id = self.list_mails().itervalues().next()[0][-1]

        return self.click_mail(last_mail_id, limit)

    def _parse_timestamp(self, stamp):
        p = parser.parse(stamp)

        return (p.date(), p.time())

    def _compress(self, ms):
        mails = OrderedDict()
        for m in ms:
            d, t = self._parse_timestamp(m[0])
            m[0] = t
            if d in mails:
                mails[d].append(m)
            else:
                mails.setdefault(d, [m])

        return mails
