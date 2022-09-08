import re
import socket
import os
from request import Request

#h = open('arquivos/notFound.html', 'r')
#notfound = h.read()

#lista de estados possiveis para enviar e receber
states_list=['already_added','add_user_ip','remove_ip','ip_prefix','port','regex_failure','blocked_state','get_ip_list','get_master_ip']

#lista de ips que o server vai usar, ela sera populada
#com os ips vindos do arquivo.
ip_fixo='192.168.43.160'
#arquivoIPs='ips.txt'
#unica=[ip_fixo]
ip_list=[ip_fixo,'127.0.0.1','192.168.1.28']
fileDic = {}
request_data = ''
server_PORT = 8080  # Porta de acesso
max_CONECTIONS = 10  # Número máximo de conexões
data_BUFFER = 2000  # Tamanho do buffer
#listaDoArquivo=[]

#lê a lista de IPs guardadas no arquivo e
#retorna eles em uma variavel
#def readFromIPfile():
#    with open('teste.txt') as f:
#        lines = f.readlines()
#    for line in lines:
#        a=line.split(',')
#    #uniqueReturn = list(set(unica+ a))
#    set_1 = set(ip_list)
#    set_2 = set(a)
#    listaDiferenca = list(set_2 - set_1)
#    for item in listaDiferenca:
#        if item not in ip_list:
#            ip_list.append(item)
#    print('UNIQUE: ', listaDiferenca)
#    for itemOriginal in a:
#        if itemOriginal not in listaDoArquivo:
#            listaDoArquivo.append(itemOriginal)


#def writeToIPfile(listaAtual):
#    set_1 = set(listaAtual)
#    set_2 = set(listaDoArquivo)
#    listaDiferenca = list(set_1 - set_2)
#    for item in listaDiferenca:
#        if item not in listaDoArquivo:
#            with open('teste.txt', 'a') as f:
#                f.write(','+item)
#    print('LISTA DO ARQUIVO: ',listaDoArquivo)
#    print('IP A ESCREVER: ',listaDiferenca)


#le os arquivos no server e adiciona ao dicionario de arquivos com sua chave
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
    #\/ volta o notFound
    if ip_do_cara in ip_list and path == 'blocked':
        response = bytes(readFile('notFound'), 'utf-8')
    #\/ volta o notFound
    elif ip_do_cara in ip_list and path == 'varrendoDiretorio':
        response = bytes(readFile('notFound'), 'utf-8')
    #\/ volta o notFound
    elif ip_do_cara in ip_list and path in states_list:
        response = bytes(readFile('notFound'), 'utf-8')
    #\/ volta a pagina html que possui o nome do path passado
    elif ip_do_cara in ip_list:
        response = bytes(readFile(path), 'utf-8')
    #\/ volta a caveirona em caso de comportamento malicioso externo
    elif ip_do_cara not in ip_list and path in states_list:
        response = bytes(readFile('varrendoDiretorio'), 'utf-8')
    #\/ volta a pagina de blocked
    elif ip_do_cara not in ip_list:
        response = bytes(readFile('blocked'), 'utf-8')
    send_message(web_socket,'text/html', response)


#envia para o front
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
    #PEGA O CAMINHO RAIZ DO SERVER
    abs_path = os.getcwd()
    #PEGA TODOS OS ARQUIVOS EXISTENTES NO SERVER
    #DO TIPO HTML
    getAllFiles(abs_path)
    #STARTA O SOCKET
    welcome_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    welcome_socket.bind(('', server_PORT))
    welcome_socket.listen(max_CONECTIONS)
    print('Pode entrar')
    while True:
        print('LISTA de IPs Cadastrados: ', ip_list)
        web_socket, _ = welcome_socket.accept()
        socket_p=web_socket.recv(data_BUFFER)
        websocket_decoded = socket_p.decode()
        ip_do_usuario = web_socket.getpeername()[0]
        #na linha abaixo é chamado o método de construção de request
        #ele gerencia o que chega
        if Request.builder(websocket_decoded) == None:
            print('AAAAAAAAAAAAAA')
            print('VEIO NULO')
        else:
            request_data=Request.builder(websocket_decoded)

        #este if testa se o metodo recebido eh um GET    
        if request_data.method == 'GET':
            print('IP de quem chega: ', ip_do_usuario)
            correlation_paths = list(filter(lambda filename: filename==request_data.path.replace('/',''), fileDic.keys()))
            #este if checa se o que foi digitado apos a barra "/" é um estado ou um arquivo
            #Nesse caso, dentro do GET, ele so vai entrar apos a pagina HTML carregada e
            #Fizer um fetch que contenha alguma dos estados setados na states_list, que nesse caso
            #é o estado 'blocked_state'
            print('Printando PATH: ', request_data.path.replace('/', ''))
            if request_data.path.replace('/', '') in states_list:
                #TODO: MELHORAR O FETCH VINDO DO FRONT PARA UM ESTADO BLOQUEADO
                if request_data.path.replace('/', '') == 'blocked_state':
                    send_message(web_socket, 'text/plain', str.encode('blocked_user'+','+ip_do_usuario))
                elif request_data.path.replace('/', '') == ('get_ip_list'):
                    send_message(web_socket, 'text/plain', str.encode('ip_list' + ',' + ",".join(ip_list)))
                elif request_data.path.replace('/', '') == ('get_master_ip'):
                    send_message(web_socket, 'text/plain', str.encode(ip_fixo))
                else:
                    loadHtml(web_socket, request_data.path.replace('/', ''), ip_do_usuario)
            #se o caminho passado corresponde a algum item do dicionario, o valor
            # vai ser maior que 1, logo, carrega o arquivo presente no dicionario
            if correlation_paths not in states_list and len(correlation_paths) > 0:
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
                            #writeToIPfile(tratarStringBody(request_data.body))
                            #print('IP ADICIONADO NO ARQUIVO')
                            #writeToFile(tratarStringBody(request_data.body))
                            print('Ultimo IP cadastrado: ', ip_list[indiceUltimoIP-1])
                            #print('PRINTANDO CONTEUDO DO ARQUIVO: ')
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
                                print('Master IP pode ser removido')
                                send_message(web_socket, 'text/plain', str.encode('ip_master_plus'))
                        else:
                            print('O IP PASSADO NAO ESTA LISTA, LOGO, NAO PODE SER REMOVIDO')
                            send_message(web_socket, 'text/plain', str.encode('ip_not_provided'))
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