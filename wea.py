import SocketTCP

wea = "hola pirinola 16"

socket_ = SocketTCP.SocketTCP()

print(socket_.chop_message(wea.encode(), 4))