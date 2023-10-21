import SocketTCP
import sys

# socket TCP
client_socket_TCP = SocketTCP.SocketTCP()

# se consigue ip 
ip = sys.argv[1]
# se consigue puerto
port = int(sys.argv[2])
# dirección 
address = (ip, port)

# se consigue el nombre del archivo que se quiere enviar
dir = sys.argv[3]
# se abre el archivo
f = open(dir, "r")
# se guarda el mensaje
mssg = f.read()
# se pasa a bytes
mssg = mssg.encode()

# se le hace request de conexión 
client_socket_TCP.connect(address)

# se envía el mensaje
client_socket_TCP.send(mssg)

# se hace request de cierre
client_socket_TCP.close()

print("Conexión cerrada")