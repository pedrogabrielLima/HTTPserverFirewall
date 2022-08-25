import socket
#import base64

h = open('raiz/index.htm', 'r')
homepage = h.read()
i= open('paginateste.html', 'r')
paginaIpForadaLista = i.read()
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print("-------------------------------------")
print("Printando servidor",server)
print("-------------------------------------")
porta=80
dicionario = []
a =server.bind(('', porta))
print("Binding: ", a)
print("-------------------------------------")
b = server.listen(5)
print("server listen: ", b)
print("-------------------------------------")
try:
    while True:
        ws, addr = server.accept()
        data = ws.recv(2000)
        
        P = data.split(b' ') #GET / HTTP/1.0 -> [GET, /, HTTP/1.0]
        print("Printando data: ",P)
        if(addr[0] == "192.168.1.4"):
            if P[0] == b'GET':
                print("P1[0]: -",P[0])
                if P[1] == b'/':
                    print("P1[1]: -",P[1])
                    resp = ('HTTP/1.1 200 OK\r\n' + 'Content-Type: text/html\r\n' + 'Content-Length: ' + str(len(homepage)) + '\r\n\r\n' + (homepage))
                    #resp = ('HTTP/1.0 200 OK\r\n' + 'Content-Type: text/html\r\n' + 'Content-Length: ' + str(len(homepage)) + '\r\n\r\n' + (homepage))
                    resp = str.encode(resp)
                    ws.sendall(resp)
                    print("IP DE QUEM CHEGA:", addr[0])
                # else:
                    # ext = str(P[1].rpartition(b'.')[-1])
                    # f = open(P[1][1:], 'rb')
                    # figure = f.read()
                    
                    # ws.sendall('HTTP/1.0 200 OK\r\n' +
                                # 'Content-Type: image' + ext + '\r\n' +
                                # 'Content-Length: ' + str(len(figure)) + '\r\n\r\n' +
                                # figure)
        else:
            if P[0] == b'GET':
                print("********************************")
                print("PEGANDO O P1[0]: -",P[0])
                print("********************************")
                if P[1] == b'/':
                    print("====================================")
                    print("PEGANDO O P1[1]: -",P[1])
                    print("====================================")
                    resp = ('HTTP/1.1 200 OK\r\n' + 'Content-Type: text/html\r\n' + 'Content-Length: ' + str(len(paginaIpForadaLista)) + '\r\n\r\n' + (paginaIpForadaLista))
                    #resp = ('HTTP/1.0 200 OK\r\n' + 'Content-Type: text/html\r\n' + 'Content-Length: ' + str(len(homepage)) + '\r\n\r\n' + (homepage))
                    resp = str.encode(resp)
                    ws.sendall(resp)
except KeyboardInterrupt:
    print(" terminado pelo usuario")
    ws.close()
    server.close()

# sudo fuser -i -k 80/tcp