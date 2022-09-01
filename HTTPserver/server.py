import socket
import json
import os

from request import Request
#import base64

h = open('raiz/notFound.html', 'r')
notfound = h.read()


states_list=['add_user_ip','remove_ip','ip_prefix','port']
website_dict = {}
lista_ips=['127.0.0.1','192.169.1.10']
# Lista bruta com todos os arquivos que serão adicionados
# Ao servidor, daqui eles serão transformados para dict
allFiles = {}


def readFile(file_name):
    if file_name in allFiles.keys():
        path= allFiles[file_name]
        i= open(path, 'r')
        content= i.read()
        i.close()
        return content

def getAllFiles(dir):
    for r, d, f in os.walk(dir):
        for file in f:
            if '.html' in file:
                allFiles[file.replace('.html','')]=os.path.join(r, file)


def encontrarArquivos():
    for file in allFiles:
        file = str(file[len(abs_path)+1:])
        format = file[file.rfind('.')+1:]
        if format in ['css']:
            data = open(file, 'r').read()
            resp = f'HTTP/1.1 200 OK\r\nContent-Type: text/css\r\nContent-Length: {len(data)}\r\n\r\n'
            website_dict[file] = str.encode(resp + data)


def loadHtml(web_socket,path, ip_do_cara):
    if ip_do_cara in lista_ips:
        response = bytes(readFile(path), 'utf-8')
    else:
        response = bytes(readFile('blocked'), 'utf-8')
    send_message(web_socket,'text/html', response)


def send_message(web_socket, content_type, response):
    resp = f'HTTP/1.1 200 OK\r\nContent-Type: {content_type}\r\nContent-Length: {len(response)}\r\n\r\n'
    web_socket.sendall(str.encode(resp) + response)

    
try:
    abs_path = os.getcwd()
    getAllFiles(abs_path)
    print('--------------------')
    print('All files: ',allFiles)
    print('--------------------')
    welcome_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    nreceive = True#nreceive = Not Received
    #ticks = 0
    #f = None
    #while nreceive and ticks < 101:#try to get the info 100 times or until it's received
    #    ticks+=1
    #    try:
    #        f = welcome_socket.makefile('rb')
    #        if not f == None:
    #            nreceive = False
    #    except:
    #        pass
    #data = f.read(1024)
    welcome_socket.bind(('', 8080))
    welcome_socket.listen(5)
    print('Server online')
    while True:
        print('ITEROU 000000')
        web_socket, _ = welcome_socket.accept()
        print('KKKKKKKKKKKKKKKKKKKKK')
        print('ACCEPTED: ', web_socket)
        print('KKKKKKKKKKKKKKKKKKKKK')
        #data = web_socket.recv(2000).split(b'\r\n')
        webscoket_decoder=web_socket.recv(2000).decode()
        print('WEBSCOKET_DECODER: ', webscoket_decoder)
        request_data=Request.builder(webscoket_decoder)
        print('==============================')
        print('Imprimindo data: ', request_data)
        print('==============================')
        if request_data.method == 'GET':
            print('----------------------------------')
            client_IP = web_socket.getpeername()[0]
            print('IP: ', client_IP)
            print('----------------------------------')
            

            # Requests padrões já armazenadas no website_dict
            #################################################
            # Alternativas caso os arquivos de mesmo caminho não sejam encontrados
            path_matches = list(filter(lambda filename : filename==request_data.path.replace('/',''), allFiles.keys()))
            #################################################  
            print('--------------------')
            print('Path_matches: ',path_matches)
            print('--------------------')
            if len(path_matches) > 0:
                loadHtml(web_socket, path_matches[0], client_IP)
            elif states_list in path_matches:
                #validar se eh GET. Faz sentido se for GET.
                print('A FAZER')
            else:
                loadHtml(web_socket, 'notFound', client_IP)
        elif request_data.method== 'POST':
            if request_data.path.replace('/', '') in states_list:
                #criar filtro, como if, para mandar coisas diferentes de 'ip_changed'
                send_message(web_socket, 'text/plain', str.encode('ip_changed'))

except KeyboardInterrupt:
    print(" terminado pelo usuario")
    web_socket.close()
    welcome_socket.close()
# sudo fuser -i -k 80/tcp