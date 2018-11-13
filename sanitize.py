#!/usr/bin/python3.6
import re, sys, requests

#url
web_url = "http://localhost:8888"
#where to save configs
file_path = "/configs/oxidized/"
#api path for oxidized
api_path = "/node/fetch/"
#regex for grabbing devices from home web page
expression = "(\<a href=\'\/node\/fetch\/)([\w\.-]+)(\' title=\'configuration\'>)"


def get_device_url(web_url):
    #gets the main page of oxidized with all the devices listed
    r = requests.get(web_url)
    return r.text


def parse_device_names(web_page, expression):
    #parses the main page and extracts the devices hostnames
    device_list = []
    web_page = web_page.split('\n')
    for i in web_page:
        if re.findall(expression, i):
            device_name = re.sub(expression, r'\2', i)
            device_list.append(device_name)
    return device_list


def get_device_configs(web_url, api_path, device):
    #grab device configuration from web portal and return as text
    r = requests.get(web_url+api_path+device)
    yield r.text


def sanitize_device_configs(entry):
    #remove unwanted config from device configuration
    entry = entry.rsplit('\n')
    for line in entry:
        line = re.sub(r'^\s?(radius-server\shost|server-private)\s([\d\.]+)(.*)', r'\1 <omitted radius> \3', line)
        line = re.sub(r'^\s?(ldap-server\shost)(.*)', r'\1 <omitted ldap>', line)
        line = re.sub(r'^(snmp-server\s)(.*)', r'\1 <omitted snmp>', line)
        line = re.sub(r'(aaa-server[\s\w\(\)]+host)(.*)', r'\1 <omitted aaa>', line)
        line = re.sub(r'^(logging\s)(.*)', r'\1 <omitted log host>', line)
        line = re.sub(r'(userprofile attribute-name)(.*)', r'\1 <omitted userprofile>', line)
        line = re.sub(r'(username[\s\w-]+sshkey)(.*)$', r'\1 <omitted rsa>', line)
        line = re.sub(r'^([\s\t]*server\s)([\d\.]+)', r'\1 <omitted server host>', line)
        line = re.sub(r'^([\s\t]*username\s[\w-]+(password|secret))', r'\1 <omitted username pw>', line)
        line = re.sub(r'(\s+)(secret|key|password|private|sys-unit-key|sym-unit-key|match identity|encrypted-password|enable s|enable p)(.*)', r'\1 \2 <omitted key>', line)
        line = re.sub(r'(.*passphrase)(.*)', r'\1 <omitted key2>', line)
        line = re.sub(r'(\s+)(encr|authentication|group|lifetime|transform-set|pfs|isakmp-profile|pre-shared-key)(.*)', r'\1\2 <omitted ipsec>', line)
        line = re.sub(r'(.*name-servers\s)(.*)', r'\1 <omitted ns host>', line)
        line = re.sub(r'(\s[\d\w]{8}){8}', r'<omitted rsa key>', line)
        yield line


def write_device_configs(file_path, device_name, config):
    #write device configuration into a file
    with open(file_path+device_name, 'wt') as f:
        for e in config:
            f.write(e+'\n')


def main():
	#define webpage front webpage to grab devices
	web_page = get_device_url(web_url)
	#createa array from parsed devices
	device_list = parse_device_names(web_page, expression)
	#loop over each device
	for device in device_list:
		#pull full config file of device
		print('Starting device: '+ device +' and saving new config at ' + file_path + device)
		configs = get_device_configs(web_url, api_path, device)
		#iterate over configuration lines
		for entry in configs:
			#parse configuration lines in data sanitizer function
			entry = sanitize_device_configs(entry)
			#write entry into file
			write_device_configs(file_path, device, entry)
	print('done')
		

if '__name__' == '__main__':
    main()	
