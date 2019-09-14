import urllib.request
import urllib.parse
import json
import os
import time
import math
from urllib.error import HTTPError

def handle_err(cause,src,id_num):
	raw_data = cause.read()
	lines = raw_data.split('\n')
	with open("err/{0}/{1}.error".format(src,id_num),'w',encoding='utf-8') as ofile:
		for line in lines: 
			ofile.write(line+'\n')

def get_raw(url):
	print("get data from "+url)
	contents = urllib.request.urlopen(url).read()
	return json.loads(contents)

def get_page(search, page, per_page, src):
	params = {'q':search,'lan':'23','p':page,'per_page':per_page,'src':src["id"]}
	url = "https://searchcode.com/api/codesearch_I/?"+urllib.parse.urlencode(params)
	print("getting "+str(per_page)+" items from page "+str(page))
	raw_data = get_raw(url)
	results = raw_data["results"]
	id_list = []
	for result in results:
		id_list.append(result["id"])
	for id_num in id_list:
		try:
			url = "https://searchcode.com/api/result/"+str(id_num)+"/"
			code = get_raw(url)["code"]
			lines = code.split('\n')
			with open("out/{0}/{1}.java".format(src["source"],id_num),'w',encoding='utf-8') as ofile:
				for line in lines: 
					ofile.write(line+'\n')
		except HTTPError as e:
			print("HTTPError!")
			handle_err(e,src["source"],id_num)
		except json.decoder.JSONDecodeError as e:
			print("JSONDecodeError!")
			handle_err(e,src["source"],id_num)

def get_java_code(search):
	params = {'q':search,'lan':'23'}
	url = "https://searchcode.com/api/codesearch_I/?"+urllib.parse.urlencode(params)
	raw_data = get_raw(url)
	src_filters = raw_data["source_filters"]
	print("There are " + str(len(src_filters)) + " repo-sources!")
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
		pages = int(math.ceil(total/20))
		for page in range(0,pages):
			get_page(search,page,20,src)
			time.sleep(1)
		time.sleep(5)
	print("DONE!")

#get_java_code("stackoverflow.com")