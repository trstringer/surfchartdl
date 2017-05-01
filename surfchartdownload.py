"""Change desktop background to surf chart"""

import argparse
from collections import namedtuple
from datetime import datetime
import os
import sys
import time
import urllib.request
from bs4 import BeautifulSoup # pylint: disable=import-error
from pyvirtualdisplay import Display  # pylint: disable=import-error
import requests
from selenium import webdriver # pylint: disable=import-error

def list_charts():
    """List chart regions, names, and relative urls"""

    req = requests.get(
        'http://magicseaweed.com/California-South-MSW-Surf-Charts/17/'
    )

    if req.status_code != 200:
        print('Status {}'.format(req.status_code))
        sys.exit(1)

    soup = BeautifulSoup(req.text, 'lxml')

    for nav_list in soup.find_all('ul', class_='nav-list'):
        current_region = nav_list.find_parent().find(
            'div',
            class_='nav-list-header'
        ).find('a').text.strip()
        for nav_list_item in nav_list.find_all('li'):
            temp_list_item = nav_list_item.find('a')
            print('[{}] {} ({})'.format(
                current_region,
                temp_list_item.text.strip(),
                temp_list_item['href']
            ))

def get_chart_url_and_time(url_postfix):
    """Get the image url of the current swell chart"""

    display = Display(visible=False)
    display.start()
    driver = webdriver.Chrome()
    driver.get('http://magicseaweed.com/{}'.format(url_postfix))
    soup = BeautifulSoup(driver.page_source, 'lxml')

    img_ul = soup.find('ul', class_='msw-charts-c-list')
    # pylint: disable=invalid-name
    Chart = namedtuple('Chart', ['datetimestamp', 'img_url'])
    charts = [Chart(
        datetimestamp=img_il['data-timestamp'],
        img_url=img_il['data-src']
    ) for img_il in img_ul.children if not (
        img_il.attrs.get('class') and 'msw-c-nochart' in img_il.attrs.get('class')
    )]

    driver.quit()
    display.stop()

    return charts

def get_current_chart(charts):
    """Get the current relevant chart"""

    current_unix_time = time.mktime(datetime.now().timetuple())
    current_chart = charts[-1]

    for chart in charts:
        if float(chart.datetimestamp) <= current_unix_time:
            current_chart = chart

    return current_chart

def main():
    """Main application execution"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-l', '--list', help='list available charts', action='store_true')
    arg_chart_group = parser.add_argument_group('chart arguments')
    arg_chart_group.add_argument('-c', '--chart-url', help='tail input chart url')
    arg_chart_group.add_argument('-o', '--output', help='output filename to save chart image as')
    args = parser.parse_args()

    if args.list:
        list_charts()
    elif args.chart_url and args.output:
        current_chart = get_current_chart(get_chart_url_and_time(args.chart_url))
        urllib.request.urlretrieve(
            current_chart.img_url,
            os.path.abspath(os.path.expanduser(args.output))
        )
        print(datetime.fromtimestamp(int(current_chart.datetimestamp)))

    sys.exit(0)

if __name__ == '__main__':
    main()
