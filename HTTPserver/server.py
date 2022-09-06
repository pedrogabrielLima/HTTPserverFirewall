import re
import socket
import os
from request import Request

h = open('raiz/notFound.html', 'r')
notfound = h.read()

#lista de estados possiveis para enviar e receber
states_list=['already_added','add_user_ip','remove_ip','ip_prefix','port', 'regex_failure']
ip_list=['127.0.0.1', '192.168.1.10']
fileDic = {}
request_data = ''
ip_fixo='192.168.1.10'


#le os arquivos no server
def readFile(file_name):
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


#envia para a pagina
def send_message(web_socket, content_type, response):
    resp = f'HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nContent-Length: {len(response)}\r\n\r\n'
    web_socket.sendall(str.encode(resp) + response)


#trata o body da request, que no caso, geralmente é o IP
def tratarStringBody(requestBody):
    if requestBody != None and type(requestBody) == str:
        a = requestBody.strip()
        return a.strip('\r\n')
    else:
        print('NAO VEIO FORMATO STRING NO REQUEST BODY')


#checa se o IP está no formato IPV4 correto usando regex
def checkIP(ip):
    pattern = r'(\b25[0-5]|\b2[0-4][0-9]|\b[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}'
    if re.match(pattern, ip):
        return True
    else:
        return False


try:
    abs_path = os.getcwd()
    getAllFiles(abs_path)
    welcome_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    welcome_socket.bind(('', 8080))
    welcome_socket.listen(10)
    print('Pode entrar')
    while True:
        print('LISTA de IPs Cadastrados: ', ip_list)
        web_socket, _ = welcome_socket.accept()
        ip_do_usuario = web_socket.getpeername()[0]
        socket_p=web_socket.recv(2000)
        websocket_decoder = socket_p.decode()
        #na linha abaixo é chamado o método de construção de request
        #ele gerencia o que chega
        if Request.builder(websocket_decoder) == None:
            print('AAAAAAAAAAAAAA')
            print('VEIO NULO')
        else:
            request_data=Request.builder(websocket_decoder)

        #este if testa se o metodo recebido eh um GET    
        if request_data.method == 'GET':
            print('IP de quem chega: ', web_socket.getpeername()[0])
            correlation_paths = list(filter(lambda filename: filename==request_data.path.replace('/',''), fileDic.keys()))
            #print('FileDic: ', fileDic)
            #print('CORRELATION', correlation_paths)
            #print('Request Path', request_data.path)
            #este if checa se o que foi digitado apos a barra "/" é um estado ou um arquivo
            print('Printando Path', request_data.path.replace('/', ''))
            if request_data.path.replace('/', '') in states_list:
                #se estiver dentro da lista de estados possiveis, é pq n é um arquivo
                if request_data.path.replace('/', '') == 'add_user_ip':
                    send_message(web_socket, 'text/plain', str.encode('user_added'))
                    print('ADICIONOU NO GET')
                elif request_data.path.replace('/', '') == 'remove_ip':
                    send_message(web_socket, 'text/plain', str.encode('user_remove'+','+ip_do_usuario))
                elif request_data.path.replace('/', '') == 'ip_prefix':
                    send_message(web_socket, 'text/plain', str.encode('user_remove'+','+ip_do_usuario))
                else:
                    send_message(web_socket, 'text/plain', str.encode('dont_care'))
            #Checa se o que foi passado nao está no dicionário de arquivos e se é maior que 0
            if correlation_paths not in states_list and len(correlation_paths) > 0:
                #se for maior que zero, carrega o arquivo presente no dicionario
                loadHtml(web_socket, correlation_paths[0], ip_do_usuario)
            else:
                #se n for maior que zero, ou seja, se veio vazio, carrega o notFound
                #exemplo é se apenas digitar ip:8080, sem especificar diretorio
                loadHtml(web_socket, 'notFound', ip_do_usuario)
        #else que checa se veio um POST
        elif request_data.method== 'POST':
            if request_data.path.replace('/', '') in states_list:
                #se o que foi passado pelo JS no fetch foi o "add_user_ip"
                if request_data.path.replace('/', '') == 'add_user_ip':
                    #se foi, checa se o valor passado é um IP mesmo, na regex
                    #Isso evita xss e outros ataques
                    if checkIP(tratarStringBody(request_data.body)) == True:
                        #Se o ip passado estiver na lista, aí nao adiciona ele e retorna um
                        #estado chamado "already_added"
                        if tratarStringBody(request_data.body) in ip_list:
                            print('IP:{} JA EXISTENTE NA LISTA'.format(request_data.body))
                            send_message(web_socket, 'text/plain', str.encode('already_added'))
                        else:
                            send_message(web_socket, 'text/plain', str.encode('user_added'))
                            ip_list.append(tratarStringBody(request_data.body))
                            indiceUltimoIP=len(ip_list)
                            print('Ultimo IP cadastrado: ', ip_list[indiceUltimoIP-1])
                    #se o valor passado for incompátivel com a regex de IPV4, volta um
                    # estado de falha "regex_failure"        
                    else:
                        print('ERRO: IP ADICIONADO CAIU NA VERIFICACAO DE REGEX')
                        send_message(web_socket, 'text/plain', str.encode('regex_failure'))
                elif request_data.path.replace('/', '') == 'remove_ip':
                    if checkIP(tratarStringBody(request_data.body)) == True:
                        #Se o ip passado estiver na lista, ele e retorna um
                        #estado chamado "ip_removed" para o front
                        if tratarStringBody(request_data.body) in ip_list:
                            if tratarStringBody(request_data.body) != ip_fixo:
                                print('IP:{} REMOVIDO DA LISTA'.format(request_data.body))
                                send_message(web_socket, 'text/plain', str.encode('ip_removed'))
                                ip_list.remove(tratarStringBody(request_data.body))
                            else:
                                print('IP 192.168.1.10 nao pode ser removido')
                                send_message(web_socket, 'text/plain', str.encode('ip_master_plus'))
                    else:
                        print('ERRO: IP REMOVIDO CAIU NA VERIFICACAO DE REGEX')
                        send_message(web_socket, 'text/plain', str.encode('regex_failure'))
                elif request_data.path.replace('/', '') == 'ip_prefix':
                    send_message(web_socket, 'text/plain', str.encode('banned_prefix'))
                else:
                    send_message(web_socket, 'text/plain', str.encode('dont_care'))
        web_socket.close()
                

except KeyboardInterrupt:
    print("Server desligado")
    web_socket.close()
    welcome_socket.close()