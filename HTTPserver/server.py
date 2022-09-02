import socket
import os
from request import Request

h = open('raiz/notFound.html', 'r')
notfound = h.read()

states_list=['add_user_ip','remove_ip','ip_prefix','port']
ip_list=['127.0.0.1']
fileDic = {}



#le os arquivos no server
def readFile(file_name):
    print('FILE NAME', file_name)
    print('FILE NAME TYPE', type(file_name))
    if file_name in fileDic.keys():
        path= fileDic[file_name]
        i= open(path, 'r', encoding="utf-8")
        content= i.read()
        i.close()
        return content

#pega os arquivos no server
def getAllFiles(dir):
    for r, d, f in os.walk(dir):
        for file in f:
            if '.html' in file:
                fileDic[file.replace('.html','')]=os.path.join(r, file)


#devolve html pro front
def loadHtml(web_socket, path, ip_do_cara):
        if path == 'blocked' or path == '/blocked' and ip_do_cara in ip_list:
            response = bytes(readFile('notFound'), 'utf-8')
        elif ip_do_cara in ip_list:
            response = bytes(readFile(path), 'utf-8')
        elif ip_do_cara not in ip_list:
            response = bytes(readFile('blocked'), 'utf-8')
        send_message(web_socket,'text/html', response)


def send_message(web_socket, content_type, response):
    resp = f'HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nContent-Length: {len(response)}\r\n\r\n'
    web_socket.sendall(str.encode(resp) + response)



try:
    abs_path = os.getcwd()
    getAllFiles(abs_path)
    welcome_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    welcome_socket.bind(('', 8080))
    welcome_socket.listen(1)
    print('Pode entrar')
    while True:
        print('LISTA de IPs Cadastrados: ', ip_list)
        web_socket, _ = welcome_socket.accept()
        print('++++++++++++++++++++++')
        print('ACCEPTED: ', web_socket)
        print('++++++++++++++++++++++')
        socket_p=web_socket.recv(2000)
        websocket_decoder = socket_p.decode()
        print('########################')
        print('WEBSCOKET_DECODER: ', websocket_decoder)
        print('TIPO WEBSCOKET_DECODER: ', type(websocket_decoder))
        print('########################')
        #na linha abaixo é chamado o método de construção de request
        #ele gerencia o que chega
        request_data=Request.builder(websocket_decoder)
        print('==============================')
        print('Imprimindo data: ', request_data)
        print('==============================')
        if request_data.method == 'GET':
            ip_do_usuario = web_socket.getpeername()[0]
            correlation_paths = list(filter(lambda filename : filename==request_data.path.replace('/',''), fileDic.keys()))
            if request_data.path.replace('/', '') in states_list:
                if request_data.path.replace('/', '') == 'add_user_ip':
                    send_message(web_socket, 'text/plain', str.encode('user_added'))
                elif request_data.path.replace('/', '') == 'remove_ip':
                    send_message(web_socket, 'text/plain', str.encode('user_remove'+','+ip_do_usuario))
                elif request_data.path.replace('/', '') == 'ip_prefix':
                    send_message(web_socket, 'text/plain', str.encode('user_remove'+','+ip_do_usuario))
                else:
                    send_message(web_socket, 'text/plain', str.encode('dont_care'))
            
            if correlation_paths not in states_list and len(correlation_paths) > 0:
                loadHtml(web_socket, correlation_paths[0], ip_do_usuario)
            else:
                loadHtml(web_socket, 'notFound', ip_do_usuario)
        elif request_data.method== 'POST':
            if request_data.path.replace('/', '') in states_list:
                if request_data.path.replace('/', '') == 'add_user_ip':
                    if request_data.body in ip_list:
                        send_message(web_socket, 'text/plain', str.encode('already_added'))
                    else:
                        send_message(web_socket, 'text/plain', str.encode('user_added'))
                        ip_list.append(request_data.body)
                elif request_data.path.replace('/', '') == 'remove_ip':
                    send_message(web_socket, 'text/plain', str.encode('user_removed'))
                elif request_data.path.replace('/', '') == 'ip_prefix':
                    send_message(web_socket, 'text/plain', str.encode('banned_prefix'))
                else:
                    send_message(web_socket, 'text/plain', str.encode('dont_care'))
                

except KeyboardInterrupt:
    print("Server desligado")
    web_socket.close()
    welcome_socket.close()