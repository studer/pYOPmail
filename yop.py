# -*- coding: utf-8 -*-

import requests
from os.path import join
from bs4 import BeautifulSoup as bs4


class Yop(object):
    def __init__(self, username=None, url='http://www.yopmail.com', lang='en', version='2.2'):
        self.url = url
        self.lang = lang
        self.version = version
        self.username = username
        self.session = requests.session(prefetch=True)

    def list_mails(self):
        payload = {'login': self.username, 'v': self.version}
        r = self.session.get(join(self.url, self.lang, 'inbox.php'), params=payload)

        return self._compress(self._parse_list_mails(r.content))

    def _parse_list_mails(self, source):
        html = bs4(source)
        messages = html.find_all('div', lambda c: c == 'jour' or c == 'm')

        return [self._parse_elem(i) for i in messages]

    def _parse_elem(self, elem):
        if 'jour' in elem.attrs.get('class'):
            return elem.get_text().capitalize()
        else:
            return [i.get_text() for i in elem.find_all('span')[1:]] + [elem.a.get('href').split('id=')[-1]]

    def get_mail(self, mail_id):
        payload = {'id': mail_id}
        r = self.session.get(join(self.url, self.lang, 'mail.php'), params=payload)

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
            url = link.get('href')
            try:
                results += [self.session.get(url)]
            except:
                pass

        return results
        #return [self.session.get(link.get('href')) for link in message.find_all('a')[:None]]

    def click_last_mail(self, limit=1):
        last_mail_id = self.list_mails()[0][2][0][-1]

        return self.click_mail(last_mail_id, limit)

    def _compress(self, l):
        mails = []
        day = []
        for i in l:
            if isinstance(i, basestring):
                mails.append(day)
                day = [i, 0]
            else:
                day.append(i)
                day[1] += 1
        mails.append(day)

        return [(i[0], i[1], i[2:]) for i in mails[1:]]
