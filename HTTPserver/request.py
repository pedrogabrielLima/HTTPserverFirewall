import re
from xml.etree.ElementTree import tostring

class Request():
    def __init__(self,method,path,headers,body):
        self.method=method
        self.path=path
        self.headers=headers
        self.body=body


    def __str__(self):
        return "method: %s\npath:%s\nheaders: %s\nbody: %s"%(self.method,self.path,self.headers,self.body)


    def builder(http_post):
        print('PRINTANDO HTTP POST:', http_post)
        print('PRINTANDO TIPO HTTP POST:', type(http_post))
        req_line = re.compile(r'(?P<method>GET|POST)\s+(?P<resource>.+?)\s+(?P<version>HTTP/1.1)')
        field_line = re.compile(r'\s*(?P<key>.+\S)\s*:\s+(?P<value>.+\S)\s*')
        first_line_end = http_post.find('\n')
        headers_end = http_post.find('\r\n\r\n')
        request = req_line.match(
            http_post[:first_line_end]
        )
        headers = dict(
            field_line.findall(
                http_post[first_line_end:headers_end]
            )
        )
        body = http_post[headers_end + 2:]
        print('------------------------------')
        print('Printando as quatro variaveis:')
        print(request["method"], request["resource"], headers, type(body))
        print('------------------------------')
        return Request(request["method"], request["resource"], headers, body)