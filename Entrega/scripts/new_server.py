import SocketTCP
import sys

# dirección
address = ("localhost", 8000)
# se crea el socket
server_socketTCP = SocketTCP.SocketTCP()
# se hace bind
server_socketTCP.bind(address)
# se consigue el socket de conexión
connection_socketTCP, new_address = server_socketTCP.accept()

# se consigue el tamaño del buffer
buff_size = int(sys.argv[1])
# se consigue la cantidad de veces que se quiere hacer recieve
nRecieve = int(sys.argv[2])

# mensaje final
full_message = ""

# mensaje parciales leídos
partials_read = 0

# se hace recv las veces dichas
while partials_read < nRecieve:
    # se lee parte del mensaje
    partial_mssg = connection_socketTCP.recv(buff_size)
    # se agrega al mensaje final
    full_message += partial_mssg.decode()
    # se aumenta el número de mensajes parciales leídos
    partials_read += 1

# se imprime el mensaje
print(full_message)

# se cierra la conexión
connection_socketTCP.recv_close()

print("Conexión cerrada")


 