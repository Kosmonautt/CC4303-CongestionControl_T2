import SocketTCP

address = ("localhost", 8000)

client_socketTCP = SocketTCP.SocketTCP()
client_socketTCP.connect(address)

# debug
#client_socketTCP.debug = True

# test 1
message = "Mensje de len=16".encode()
client_socketTCP.send(message)
# test 2
message = "Mensaje de largo 19".encode()
client_socketTCP.send(message)
# test 3
message = "Mensaje de largo 19".encode()
client_socketTCP.send(message)

# test 3
message = "Un super test bastante largo de más que 19 bytes".encode()
client_socketTCP.send(message)

client_socketTCP.close()

print("fin")