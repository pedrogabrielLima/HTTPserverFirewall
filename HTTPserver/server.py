import re
import socket
import os
from request import Request

server_PORT = 8000  # Porta de acesso
max_CONECTIONS = 10  # Número máximo de conexões
data_BUFFER = 2000  # Tamanho do buffer

s_IPv4 = socket.AF_INET  # Address Family IPv4
s_TCP = socket.SOCK_STREAM  # TCP

# Padrão de Header HTTP
header_ = ('HTTP/1.1 {num_plus_resp}\r\n'
           'Content-Type: {content_type}\r\n'
           'Content-Length: {content_length}\r\n\r\n')

h = open('raiz/notFound.html', 'r')
notfound = h.read()

states_list = ['add_user_ip', 'remove_ip', 'ip_prefix', 'port', 'get_ip_list']
ip_list = ['127.0.0.1', '192.168.1.10', '192.168.15.1']
# Cria um set de arquivos
fileDic = {}
request_data = ''
ip_fixo = ['192.168.1.10', '127.0.0.1']


#le os arquivos no server
def readFile(file_name):
    print('FILE NAME', file_name)
    print('FILE NAME TYPE', type(file_name))
    if file_name in fileDic.keys():
        path = fileDic[file_name]
        i = open(path, 'r', encoding="utf-8")
        content = i.read()
        i.close()
        return content


#pega os arquivos no server
def getAllFiles(dir):
    for r, d, f in os.walk(dir):
        for file in f:
            if '.html' in file:
                fileDic[file.replace('.html', '')] = os.path.join(r, file)


#devolve html pro front
def loadHtml(web_socket, path, ip_do_cara):
    if ip_do_cara in ip_list:
        if path == 'blocked' or path == '/blocked':
            response = bytes(readFile('notFound'), 'utf-8')
        else:
            response = bytes(readFile(path), 'utf-8')

    elif ip_do_cara not in ip_list:
        response = bytes(readFile('blocked'), 'utf-8')

    send_message(web_socket, 'text/html', response)


def send_message(web_socket, content_type, response):
    resp = header_.format(num_plus_resp='200 OK',
                          content_type=content_type,
                          content_length=len(response))
    web_socket.sendall(str.encode(resp) + response)


def tratarStringBody(requestBody):
    if requestBody != None and type(requestBody) == str:
        a = requestBody.strip()
        return a.strip('\r\n')
    else:
        print('NAO VEIO FORMATO STRING NO REQUEST BODY')


def checkIP(ip):
    pattern = r'(\b25[0-5]|\b2[0-4][0-9]|\b[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}'
    return re.match(pattern, ip)


try:
    abs_path = os.getcwd()
    getAllFiles(abs_path)
    welcome_socket = socket.socket(s_IPv4, s_TCP)
    welcome_socket.bind(('', server_PORT))
    welcome_socket.listen(max_CONECTIONS)
    print('Pode entrar')
    while True:
        print('LISTA de IPs Cadastrados: ', ip_list)
        web_socket, _ = welcome_socket.accept()
        ip_do_usuario = web_socket.getpeername()[0]
        socket_p = web_socket.recv(data_BUFFER)
        websocket_decoder = socket_p.decode()
        '''na linha abaixo é chamado o método de construção de request
        ele gerencia o que chega'''
        if Request.builder(websocket_decoder) == '':
            print('AAAAAAAAAAAAAA')
            print('VEIO NULO')
        else:
            request_data = Request.builder(websocket_decoder)

        #este if testa se o metodo recebido eh um GET
        if request_data.method == 'GET':
            correlation_paths = list(
                filter(
                    lambda filename: filename == request_data.path.replace(
                        '/', ''), fileDic.keys()))
            print('Printando Path', request_data.path.replace('/', ''))

            if request_data.path.replace('/', '') in states_list:
                #se estiver dentro da lista de estados possiveis, é pq n é um arquivo
                resp = 'dont_care'
                if request_data.path.replace('/', '') == 'add_user_ip':
                    resp = 'user_added'
                elif request_data.path.replace('/', '') == ('remove_ip'
                                                            or 'ip_prefix'):
                    resp = ('user_remove' + ',' + ip_do_usuario)
                elif request_data.path.replace('/', '') == ('get_ip_list'):
                    resp = ('ip_list' + ',' + ",".join(ip_list))

                # elif request_data.path.replace('/','') == ('get_ip_authority'):
                #     if (tratarStringBody(request_data.body)) in ip_list:
                #         if (tratarStringBody(request_data.body)) in ip_fixo:
                #             resp = 'is_Master'
                #         else:
                #             resp = 'is_Authorized'
                #     else:
                #         resp = 'is_Removed'
                send_message(web_socket, 'text/plain', resp.encode())

            #Checa se o que foi passado nao está no dicionário de arquivos e se é maior que 0
            if correlation_paths not in states_list and len(
                    correlation_paths) > 0:
                #se for maior que zero, carrega o arquivo presente no dicionario
                loadHtml(web_socket, correlation_paths[0], ip_do_usuario)
            else:
                #se n for maior que zero, ou seja, se veio vazio, carrega o notFound
                #exemplo é se apenas digitar ip:8080, sem especificar diretorio
                loadHtml(web_socket, 'notFound', ip_do_usuario)

        #elif que checa se veio um POST
        elif request_data.method == 'POST':
            if request_data.path.replace('/', '') in states_list:
                #se o que foi passado pelo JS no fetch foi o "add_user_ip"
                if request_data.path.replace('/', '') == 'add_user_ip':
                    #se foi, checa se o valor passado é um IP mesmo, na regex
                    #Isso evita xss e outros ataques
                    if checkIP(tratarStringBody(request_data.body)):
                        #Se o ip passado estiver na lista, aí nao adiciona ele e retorna um
                        #estado chamado "already_added"
                        if tratarStringBody(request_data.body) in ip_list:
                            print('IP:{} JA EXISTENTE NA LISTA'.format(
                                request_data.body))
                            send_message(web_socket, 'text/plain',
                                         str.encode('already_added'))
                        else:
                            send_message(web_socket, 'text/plain',
                                         str.encode('user_added'))
                            ip_list.append(tratarStringBody(request_data.body))
                            indiceUltimoIP = len(ip_list)
                            print('Ultimo IP cadastrado: ',
                                  ip_list[indiceUltimoIP - 1])
                    #se o valor passado for incompátivel com a regex de IPV4, volta um
                    # estado de falha "regex_failure"
                    else:
                        print(
                            'ERRO: IP ADICIONADO CAIU NA VERIFICACAO DE REGEX')
                        send_message(web_socket, 'text/plain',
                                     str.encode('regex_failure'))
                elif request_data.path.replace('/', '') == 'remove_ip':
                    if checkIP(tratarStringBody(request_data.body)):
                        #Se o ip passado estiver na lista, ele e retorna um
                        #estado chamado "ip_removed" para o front
                        if tratarStringBody(request_data.body) in ip_list:
                            if tratarStringBody(request_data.body) != ip_fixo:
                                print('IP:{} REMOVIDO DA LISTA'.format(
                                    request_data.body))
                                send_message(web_socket, 'text/plain',
                                             str.encode('ip_removed'))
                                ip_list.remove(
                                    tratarStringBody(request_data.body))
                            else:
                                print('IP 192.168.1.10 nao pode ser removido')
                                send_message(web_socket, 'text/plain',
                                             str.encode('ip_master_plus'))
                    else:
                        print('ERRO: IP REMOVIDO CAIU NA VERIFICACAO DE REGEX')
                        send_message(web_socket, 'text/plain',
                                     str.encode('regex_failure'))
                elif request_data.path.replace('/', '') == 'ip_prefix':
                    send_message(web_socket, 'text/plain',
                                 str.encode('banned_prefix'))

                # elif request_data.path.replace('/',
                #                                '') == ('get_ip_authority'):
                #     if (checkIP(tratarStringBody(request_data.body))):
                #         if (tratarStringBody(request_data.body)) in ip_list:
                #             if (tratarStringBody(
                #                     request_data.body)) in ip_fixo:
                #                 send_message(web_socket, 'text/plain',
                #                              str.encode('is_Master'))
                #             else:
                #                 send_message(web_socket, 'text/plain',
                #                              str.encode('is_Authorized'))
                #         else:
                #             send_message(web_socket, 'text/plain',
                #                          str.encode('is_Removed'))

                else:
                    send_message(web_socket, 'text/plain',
                                 str.encode('dont_care'))
        web_socket.close()

except KeyboardInterrupt:
    print("Server desligado")
    web_socket.close()
    welcome_socket.close()
