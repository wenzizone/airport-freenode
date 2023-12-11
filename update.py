#!/bin/python
# -*- coding: utf-8 -*-

__author__ = 'wenzizone'

from bs4 import BeautifulSoup
import urllib.request
import re
import datetime
import os
import yaml
from functools import reduce

basicHeader = {
    'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
}

User_Agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
clashfan_url = "https://clashfan.com/freenode/"
storePath = "node"
template = "template/airport-tpl.yaml"

now = datetime.datetime.now()
year = now.strftime("%Y")
month = now.strftime("%m")
day = now.strftime("%d")

def getFileName(*args):  
  if len(args) == 2:
    clashFileName = "{}{}.yaml"
  elif len(args) == 4:
    if isinstance(args[3], int):
      clashFileName = "{3}-{0}{1}{2}.yaml"
    elif isinstance(args[3], str) and args[3] == "clash":
      clashFileName = "{}{}{}-{}.yaml"
    else:
      v2rayFileName = "{}{}{}-{}.txt"
  else:
    clashFileName = "{}{}{}.yaml"

  return clashFileName.format(*args)

def getFileUrlPath(*args):
  return os.path.join(*args)

## yy/mm/n-yymmdd.yml
freeNodeList = [
  {
    "name": "wenode",
    "hostUrl": "https://wenode.cc/",
    "midPath": os.path.join("wp-content", "uploads", getFileUrlPath(year,month)),
    "fileName" : getFileName(year,month,day)
  },
  {
    "name": "nodeshare",
    "hostUrl": "https://nodeshare.org/",
    "midPath": os.path.join("wp-content", "uploads", getFileUrlPath(year,month)),
    "fileName" : getFileName(month, day)
  },
  {
    "name": "freeclash",
    "hostUrl": "https://freeclash.org/",
    "midPath": os.path.join("wp-content", "uploads", getFileUrlPath(year,month)),
    "fileName" : getFileName(month, day)
  },
  {
    "name": "freeclashnode",
    "hostUrl": "https://www.freeclashnode.com/",
    "midPath": os.path.join("uploads", getFileUrlPath(year,month)),
    "fileName" : getFileName(year, month, day, 1)
  },
  {
    "name": "openrunner",
    "hostUrl": "https://freenode.openrunner.net/",
    "midPath": "uploads",
    "fileName" : getFileName(year, month, day, "clash")
  },
  {
    "name": "nodebird",
    "hostUrl": "https://nodebird.net/",
    "midPath": os.path.join("wp-content", "uploads", getFileUrlPath(year,month)),
    "fileName" : getFileName(year, month, day)
  }
]

def getNodeFromLists(nodeList):
  url = os.path.join(nodeList['hostUrl'], nodeList['midPath'], nodeList['fileName'])
  print(url)
  req = urllib.request.Request(url, headers=basicHeader)
  req.add_header('Referer', nodeList['hostUrl'])
  try: 
    r = urllib.request.urlopen(req)
    fh = open(os.path.join(storePath,nodeList['name']+".yaml"), 'wb')
    while chunk := r.read(200):
      fh.write(chunk)
    fh.close()
  except urllib.error.HTTPError as e:
    print(e)

def getNodeFromClashfan():
  ## 解析网页，获取clash 免费节点订阅连接
  req = urllib.request.Request(clashfan_url)
  req.add_header('Referer', 'https://www.google.com')
  req.add_header('User-Agent', User_Agent)
  r = urllib.request.urlopen(req)

  soup = BeautifulSoup(r, 'lxml')

  targetC = soup.find("pre", class_="wp-block-preformatted")

  #print(targetC.get_text())
  m = re.search(r'\s(http[s]?://.*\w)\s', targetC.get_text())
  print(m.group().strip())
  clashfan_subscribe_url = m.group().strip()

  ## 根据获取到的订阅连接，下载对应的yaml文件
  fileName = 'node/ClashFan.yaml'
  
  req = urllib.request.Request(clashfan_subscribe_url)
  req.add_header('Referer', clashfan_url)
  req.add_header('User-Agent', User_Agent)
  try: 
    fh = open(fileName, 'w')
    with urllib.request.urlopen(req) as f:
      f.read().decode('utf-8')
    fh.close()
  except urllib.error.HTTPError as e:
    print(e)

def putClashNodeInOneFile():
  with open(template, 'r') as file:
    try:
      tplConfig = yaml.safe_load(file)
    except yaml.YAMLError as exc:
      print("Error in configuration file: %s", exc)
  for file in os.listdir(storePath):
    if os.path.splitext(file)[1] == ".yaml":
      if file == "clash.yaml":
        continue
      else:
          #print(file)
          with open(os.path.join(storePath, file), 'r') as source:
            try:
              sourceConfig = yaml.safe_load(source)
            except yaml.YAMLError as exc:
              print("Error in configuration file: %s", exc)
            if type(sourceConfig) == dict and 'proxies' in sourceConfig:
              sourceConfig['proxies'] = filterBadCipher(sourceConfig['proxies'])
              proxies = list(map(lambda x: x['name'], sourceConfig['proxies']))
              #print(proxies)
              if type(tplConfig['proxies']) == list:
                tplConfig['proxies'].extend(sourceConfig['proxies'])
              else:
                tplConfig['proxies'] = sourceConfig['proxies']
              tplConfig['proxy-groups'][0]['proxies'].extend(proxies)
              if type(tplConfig['proxy-groups'][1]['proxies']) == list:
                tplConfig['proxy-groups'][1]['proxies'].extend(proxies)
              else:
                tplConfig['proxy-groups'][1]['proxies'] = proxies
            #print(tplConfig)
    else:
      if file == "v2ray.txt":
        continue
      else:
        continue
  #print(tplConfig)
  #remove_duplicate_dicts(tplConfig['proxies'])
  tplConfig['proxies'] = delete_duplicate_str(tplConfig['proxies'])
  tplConfig['proxy-groups'][0]['proxies'] = dedupe(tplConfig['proxy-groups'][0]['proxies'])
  tplConfig['proxy-groups'][1]['proxies'] = dedupe(tplConfig['proxy-groups'][1]['proxies'])
  with open('node/clash.yaml', 'w') as file:
    yaml.dump(tplConfig, file, encoding='utf-8')



# 从列表里去重
def dedupe(l):
  newList = list(set(l))
  newList.sort(key=l.index)
  return newList

def delete_duplicate_str(data):
    immutable_dict = set([str(item) for item in data])
    #print(immutable_dict)
    data = [eval(i) for i in immutable_dict]
    return data

def filterBadCipher(l):
  for item in l:
    if 'cipher' in item and item['cipher'] == 'chacha20-poly1305':
      l.remove(item)
  return l

# Main entry
if __name__ == '__main__':
  ## 从clash 获取免费节点订阅文件
  getNodeFromClashfan()
  res = list(map(getNodeFromLists, freeNodeList))
  putClashNodeInOneFile()



