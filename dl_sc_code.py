import urllib.request
import urllib.parse
import json
import os
import time
import math
from urllib.error import HTTPError
import argparse

def handle_err(url,cause,src,id_num):
	print("ERROR while downloading "+str(id_num))
	with open("err/{0}/{1}.error".format(src,id_num),'w',encoding='utf-8') as ofile:
		ofile.write(url+'\n'+repr(cause))

def get_raw(url):
	#print("get data from "+url)
	contents = urllib.request.urlopen(url).read()
	return json.loads(contents)

def get_page(search, page, per_page, src):
	params = {'q':search,'lan':'23','p':page,'per_page':per_page,'src':src["id"]}
	url = "https://searchcode.com/api/codesearch_I/?"+urllib.parse.urlencode(params)
	raw_data = get_raw(url)
	results = raw_data["results"]
	id_list = []
	for result in results:
		id_list.append(result["id"])
	print("getting "+str(len(results))+" items from page "+str(page))
	for id_num in id_list:
		url = "https://searchcode.com/api/result/"+str(id_num)+"/"
		try:
			code = get_raw(url)["code"]
			lines = code.split('\n')
			with open("out/{0}/{1}.java".format(src["source"],id_num),'w',encoding='utf-8') as ofile:
				for line in lines: 
					ofile.write(line+'\n')
		except HTTPError as e:
			handle_err(url,e,src["source"],id_num)
		except json.decoder.JSONDecodeError as e:
			handle_err(url,e,src["source"],id_num)

def get_java_code(search,info,per_page):
	params = {'q':search,'lan':'23'}
	url = "https://searchcode.com/api/codesearch_I/?"+urllib.parse.urlencode(params)
	raw_data = get_raw(url)
	src_filters = raw_data["source_filters"]
	print("Found " + str(len(src_filters)) + " repo-source(s) with java files, that contain \""
		+search+"\"."+'\n')
	if not info:
		try:
			os.makedirs("out")
			os.makedirs("err")
		except FileExistsError as e:
			pass
		with open("out/src_filters.out",'w',encoding='utf-8') as ofile:
			for src in src_filters:
				ofile.write(str(src)+'\n')
				try:
					os.makedirs("out/{0}".format(src["source"]))
					os.makedirs("err/{0}".format(src["source"]))
				except FileExistsError as e:
					pass
		for src in src_filters:
			print(src["source"])
			params = {'q':search,'lan':'23','src':src["id"]}
			url = "https://searchcode.com/api/codesearch_I/?"+urllib.parse.urlencode(params)
			raw_data = get_raw(url)
			total = raw_data["total"]
			print("total: "+str(total))
			pages = int(math.ceil(total/per_page))
			print("pages: "+str(pages))
			for page in range(0,pages):
				get_page(search,page,per_page,src)
				time.sleep(1)
			time.sleep(5)
		print("DONE!")
	else:
		for src in src_filters:
			print(src["source"]+" with a total of "+str(src["count"])+" result(s).")



parser = argparse.ArgumentParser(
	description='Download Java Code from searchcode, that contains the given searchquery.')
parser.add_argument('query',metavar='Q', nargs=1, help="the searchquery.")
parser.add_argument('-i','--info',action='store_true',help="only get the number of results.")
args = parser.parse_args()
query = args.query[0]
info = args.info
get_java_code(query,info,20)