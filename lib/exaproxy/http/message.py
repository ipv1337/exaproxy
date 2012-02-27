#!/usr/bin/env python
# encoding: utf-8
"""
parser.py

Created by Thomas Mangin on 2012-02-27.
Copyright (c) 2012 Exa Networks. All rights reserved.
"""

import traceback

from exaproxy.util.logger import logger
from exaproxy.network.functions import isip

from .request import Request
from .headers import Headers

class HostMismatch(Exception):
	pass

class HTTP (object):
	def __init__(self,configuration,headers,remote_ip):
		self.raw = headers
		self.ip = remote_ip
		self.proxy_name = "X-Proxy-Version: %s version %s" % (configuration.proxy.name, configuration.proxy.version)
		self.x_forwarded_for = configuration.http.x_forwarded_for

	def parse (self):
		logger.info('header','parsing %s' % str(self.raw))

		try:
			first, remaining = self.raw.split('\n',1)
			if '\r' in self.raw:
				self.separator = '\r\n'
				self.request = Request(first.rstrip('\r')).parse()
				self.headers = Headers('\r\n').parse(remaining)
			else:
				self.separator = '\n'
				self.request = Request(first).parse()
				self.headers = Headers('\n').parse(remaining)

			headerhost = self.headers.get('host',[':'])[0].split(':',1)[1].strip()
			self.headerhost = self.extractHost(headerhost)

			if self.request.host and self.request.host != '*':
				self.host = self.request.host
			else:
				# can raise KeyError, but host is a required header
				self.host = self.headerhost

			if self.host != self.headerhost and self.request.method != 'OPTIONS' and self.host != '*':
				raise HostMismatch, 'Make up your mind: %s - %s' % (self.host, self.headerhost)

			# David, why are you trying to force that header - broken clients ?
			# If we relay the version we should not have to add any headers.

			#if request.method == 'CONNECT':
			#	self.headers.default('host','Host: ' + request.host)

			# Is this the best place to add headers?
			self.headers.replace('x-proxy-version',self.proxy_name)

			if self.x_forwarded_for:
				client = self.headers.get('x-forwarded-for', ':%s' % self.ip)[0].split(':', 1)[1].split(',')[-1].strip()
				if not isip(client):
					logger.info('header', 'Invalid address in X-Forwarded-For: %s' % client)
					client = self.ip
				self.client = client
			else:
				self.client = remote_ip

			self.content_length = int(self.headers.get('content-length', [':0'])[0].split(':',1)[1].strip())
			self.url = self.host + ((':%s' % self.request.port) if self.request.port is not None else '') + self.request.path
			self.url_noport = self.host + self.request.path

		except KeyboardInterrupt:
			raise
		except Exception, e:
			logger.error('header','could not parse header %s %s' % (type(e),str(e)))
			logger.error('header', traceback.format_exc())
			return None
		return self

	def redirect (self, host, path):
		self.host = host if host is not None else self.host
		self.path = path if path is not None else self.path

		if path is not None:
			Request(self.method + ' ' + path + ' HTTP/' + self.version).parse()

		if host is not None:
			if host.count(':') > 1:
				host = '['+host+']'

			if self.port != 80:
				host = host + ':' + str(port)

			self.header.replace('host','Host: ' + host)


        def extractHost(self, hoststring):
                if ':' in hoststring:
                        # check to see if we have an IPv6 address
                        if hoststring.startswith('[') and ']' in hoststring:
                                host = hoststring[1:].split(']', 1)[0]
                        else:
                                host = hoststring.split(':', 1)[0]
		else:
			host = hoststring

                return host


	def __str__ (self):
		return str(self.request) + self.separator + str(self.headers) + self.separator + self.separator


#if __name__ == '__main__':
#	class Conf (object):
#		class Proxy (object):
#			name = 'proxy'
#			version = '1'
#		proxy = Proxy()
#		class Http (object):
#			x_forwarded_for = True
#		http = Http()
#	conf = Conf()
#		
#	r = """\
#GET http://thomas.mangin.com/ HTTP/1.1
#Host: thomas.mangin.com
#User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:9.0.1) Gecko/20100101 Firefox/9.0.1
#Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
#Accept-Language: en-us,en;q=0.5
#Accept-Encoding: gzip, deflate
#Accept-Charset: ISO-8859-1,utf-8;q=0.7,*;q=0.7
#Proxy-Connection: keep-alive
#Cookie: txtMainTab=Timeline
#
#"""
#	h = Header(conf,r,'127.0.0.1')
#	if h.parse():
#		print "[%s]" % h
#	else:
#		print 'parsing failed'