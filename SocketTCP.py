import random
import socket

buff_size = 48

class SocketTCP:
    def __init__(self):
        self.socketUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.dirDestination = None
        self.dirOrigin = None
        self.nSec = None
        # número de puerto al crear un socket de respuesta para el cliente
        self.new_socket_port = None
        self.timeout = 0
        self.buffSize = None
        # dice si queda por leer del mensaje con un recv
        self.bytes_left_to_read = 0
        # caché del sockt
        self.cache = None
        # dice si el caché está vacío
        self.cache_empty = True
    
    # setters de los diferentes parámetros
    def set_socketUDP(self, socketUDP):
        self.socketUDP = socketUDP

    def set_dirDestination(self, dirDestination):
        self.dirDestination = dirDestination

    def set_nSec(self, nSec):
        self.nSec = nSec

    def set_timeout(self, timeout):
        # timeout en la clase
        self.timeout = timeout
        # timeout en su socketUDP
        self.socketUDP.settimeout(timeout)

    # envía el mensaje (en bytes) dado a la dirección ya seteada con su número de secuencia
    def send_pure(self, mssg):
        self.socketUDP.sendto(mssg, self.dirDestination)

    # recibe un mensaje escuchando en la dirección dada
    def recv_pure(self, buff_size):
        return self.socketUDP.recvfrom(buff_size)
    
    # función que recibe un mensaje codificado y lo envía por completo a un destinatario, lo envía en pedazos
    # de 16 bytes
    def send(self, message):
        # se consigue el largo del mensaje total codificado
        len_mssg = len(message)

        # dice si se envió el largo con éxtio
        length_sent = False
        # se crea la estructura del mensaje con headers con el largo del mensaje total
        struct_lenght = ["0","0","0",str(self.nSec), str(len_mssg)]
        # se pasa a segmento
        message_length = self.create_segment(struct_lenght)

        # se le dice que espero 5 segundos al socket
        self.set_timeout(5)
        # tamaño del buffer del socketUDP, headers+data
        buff_size_UDP = 48

        while not length_sent:
            # se envía el largo del mensaje total
            self.send_pure(message_length.encode())

            # aquí se almacena la respuesta del receptor
            response = None
            # se espera confirmación del receptor
            try:
                # se consige la respuesta de confirmación
                response = (self.recv_pure(buff_size_UDP))[0]
                # se pasa a estructura (PUEDE QUE FALLE SI HAY MUCHO FLUJO, MENSAJE LLEGA MAL, CORREGIR)
                response = self.parse_segment(response.decode())
                # se revisa que tengo un ACK y que el nSec sea correcto
                bool_ACK = response[1] == "1"
                bool_nsec = int(response[3]) == self.nSec + len((str(len_mssg)).encode())

                # si ambos están correctos, se continua y se actualiza el nSec                
                if (bool_ACK and bool_nsec):
                    length_sent = True
                    self.set_nSec(int(response[3]))

            # si es que falla
            except TimeoutError:
                pass

        # bytes del mensaje enviados
        bytes_sent = 0
        # cuántos bytes envía el socketUDP cada vez
        buff_size = 16

        while bytes_sent < len_mssg:
            # máximo byte hasta el que se va a enviar
            max_byte = min(len_mssg, bytes_sent+buff_size)

            # se obtiene el trozo del mensaje que se enviará
            message_slice = message[bytes_sent: max_byte]

            # número de bytes que enviamos
            len_mssg_slice = len(message_slice)

            # se crea estructura del mensaje (con el mensaje en forma de string)
            mssg_slice_struct = ["0","0","0",str(self.nSec),message_slice.decode()]  
            # se pasa a segmento
            seg_slice = self.create_segment(mssg_slice_struct)
            # se envía el segmento
            self.send_pure(seg_slice.encode())

            # se espera la respuesta del receptor
            try:
                #se consigue la respuesta de confirmación
                response = self.recv_pure(buff_size_UDP)[0]
                # se pasa a estructura (PUEDE QUE FALLE SI HAY MUCHO FLUJO, MENSAJE LLEGA MAL, CORREGIR)
                response = self.parse_segment(response.decode())
                # se revisa que tengo un ACK y que el nSec sea correcto
                bool_ACK = response[1] = "1"
                bool_nsec = int(response[3]) == self.nSec + len_mssg_slice

                # si ambos son correctos, se continua con el mensaje
                if(bool_ACK and bool_nsec):
                    # se actualiza la cantidad de bytes enviados
                    bytes_sent+=len_mssg_slice
                    # se actualiza el número de secuencia
                    self.nSec+= len_mssg_slice
            
            # si es que no llega a tiempo el mensaje
            except TimeoutError:
                pass
    
    # función que recibe un mensaje con un tamaño de buffer dado
    def recv(self,buff_size):
        # aquí se guarda el mensaje que retorna
        ret_val = ""
        # tamaño del buffer del socketUDP, headers+data
        buff_size_UDP = 48

        # si es que bytes_left no es 0, entonces no se busca el largo de nuevo
        if(self.bytes_left_to_read == 0):
            # se recibe el mensaje con el largo del mensaje total
            len_initial_mssg = (self.recv_pure(buff_size_UDP))[0]
            # se pasa a estructura
            len_initial_mssg = self.parse_segment(len_initial_mssg.decode())
            # se consigue el número de secuencia y la sección de datos
            initial_mssg_sec = len_initial_mssg[3]
            # se consigue la sección de datos
            initial_mssg_data = len_initial_mssg[4]
            # se consigue el largo del mensaje (en bytes) total
            total_lenght = int(initial_mssg_data)
            # se actualiza el número de secuencia
            self.nSec = int(initial_mssg_sec) + len(initial_mssg_data.encode())
            # bytes que se deben leer
            self.bytes_left_to_read = total_lenght
            # se envía el mensaje ACK al emisor
            initial_confrm_struct = ["0","1","0",str(self.nSec)]
            # se pasa a seg
            initial_confrm_seg = self.create_segment(initial_confrm_struct)
            # se envía el mensaje al emisor
            self.send_pure(initial_confrm_seg.encode())

        # antes de hacer un recv, se revisa el caché
        if(not self.cache_empty):
            # se debe revisar si el caché es más grande que el buff size
            if(len(self.cache)>buff_size):
                # solo se consigue lo necesario
                ret_val_buff_size = (self.cache)[0:buff_size]
                # el resto se queda en el caché
                self.cache = self.cache[buff_size:len(self.cache)]
                # se agrega al valor de retorno
                ret_val += ret_val_buff_size.decode()
            else:
                # se agrega al valor de retorno
                ret_val += (self.cache).decode()
                # si es más peqeueño, se saca por completo
                self.cache = None
                self.cache_empty = True 


        # cuántos bytes hay que recibir
        bytes_to_recieve = min(self.bytes_left_to_read, buff_size)

        # bytes recibidos
        bytes_recieved = 0
        # ahora se empieza a conseguir el mensaje
        while bytes_recieved < bytes_to_recieve:
            # se espera un segmento
            partial_message = (self.recv_pure(buff_size_UDP))[0]
            # se pasa a estructura
            partial_message = self.parse_segment(partial_message.decode())
            # se consigue el número de secuencia y la sección de datos
            mssg_nSec = partial_message[3]
            # se consigue la data
            mssg_data = partial_message[4]
            
            # se revisa si es segmento duplicado
            if(int(mssg_nSec) < self.nSec):
                # se debe enviar el ACK nuevamente
                # se pasa a seg
                ACK_seg = self.create_segment(["0","1","0",str(self.nSec)])
                # se envía el mensaje al emisor
                self.send_pure(ACK_seg.encode())

            # si no es duplicado
            else:
                # se añade el segmento a el mensaje final
                ret_val+= mssg_data
                # se aumenta el número de bytes recibidos
                bytes_recieved += len(mssg_data.encode())
                # se actualiza el número de secuencia
                self.nSec += len(mssg_data.encode())
                # se debe enviar el ACK
                ACK_seg = self.create_segment(["0","1","0",str(self.nSec)])
                # se envía el mensaje al emisor
                self.send_pure(ACK_seg.encode())

        # se restan los bytes recibidos de los bytes left to read
        self.bytes_left_to_read -= bytes_recieved

        # se revisa si el mensaje es más grande que el buffer
        if (len(ret_val.encode()) > buff_size):
            # si lo es, se guarda el resto en el caché
            ret_val_buff_size = (ret_val.encode())[0:buff_size]
            to_cache = (ret_val.encode())[buff_size:len(ret_val.encode())]
            # para el caso de caché vacío 
            if(self.cache_empty):
                self.cache = to_cache
                self.cache_empty = False
                # se actualiza el resultdo que retorna 
                ret_val = ret_val_buff_size.decode()

            # caché no vacío
            else:
                # se consigue la primera parte del nuevo caché
                cache = self.cache
                # se les hace append a ambos
                new_cache = (cache.decode()) + (to_cache.decode())
                # se agrega al caché
                self.cache = new_cache.encode()

        # se retorna el mensaje final (en bytes)
        return ret_val.encode()





    # pasa segmento TCP a estructura
    @staticmethod
    def parse_segment(seg):
        # se divide el segmento por sus separadores
        seg_split = seg.split("|||")
        # se consigue sus headers
        syn = seg_split[0]
        ack = seg_split[1]
        fin = seg_split[2]
        seq = seg_split[3]
        data = None
        # si hay datos se consiguen
        if (len(seg_split) >= 5):
            data = seg_split[4]
        # se crea la estructura 
        struct = [syn, ack, fin, seq, data]

        return struct

    @staticmethod
    def create_segment(struct):
        # se concatenan los headers
        seg = struct[0]+"|||"+struct[1]+"|||"+struct[2]+"|||"+struct[3]+"|||"
        # si hay datos se concatena al mensaje
        if (len(struct) > 4):
            seg += struct[4]
        # se retorna el segmento
        return seg
    
    # asocia el socket UDP y la dirección de destino a la dirección dada
    def bind(self, address):
        # origen en el parámetro adress de la clase
        self.dirOrigin = address
        # se le hace bind al socket UDP
        self.socketUDP.bind(address)
        # se le inicia el puerto siguiente a los sockets nuevos
        self.new_socket_port = address[1]+1
    
    # función que inicia la conexión de un SocketTCP con otro que se encuentra escuchando en la diección adress
    def connect(self, address):
        # número al azar entre 0 y 100 para el número de secuencia
        self.set_nSec(random.randint(0, 100))
        # se setea la dirección de destino
        self.set_dirDestination(address)
        
        # se crea el mensaje SYN del handshake
        struct_handshake = ["1","0","0",str(self.nSec)]
        # se pasa a segmento
        seg_SYN = self.create_segment(struct_handshake)
        # se pasa a bytes
        seg_SYN = seg_SYN.encode()
        # dice si se recibió correctamente la respuesta del recpetors
        ack_corretly = False

        while not ack_corretly:
            # se envía el mensaje
            self.send_pure(seg_SYN)

            # se recibe la respuesta  SYN+ACK del server con el mensaje y la dirección de la response
            message_SYN_ACK, response_adress = self.recv_pure(buff_size)
            # se setea la nueva dirección de destino
            self.set_dirDestination(response_adress)
            # se pasa el mensaje a una estructura
            struct_handshake_response = self.parse_segment(message_SYN_ACK.decode())

            # se revisa que los headers sean correctos
            # SYN
            bool_SYN = struct_handshake_response[0] == "1"
            # ACK 
            bool_ACK = struct_handshake_response[1] == "1"
            # se revisa que el número de secuencia sea correcto
            bool_nSec = int(struct_handshake_response[3]) == (self.nSec + 1)

            # si todos son correctos
            if(bool_SYN and bool_ACK and bool_nSec):
                # se sale del while
                ack_corretly = True
        
        # se actualiza el número de secuencia
        self.nSec += 2

        # se manda el mensaje de confirmación al server
        # se crea el mensaje ACK del handshake
        struct_handshake_ACK = ["0","1","0",str(self.nSec)]
        # se pasa a segmento
        seg_ACK = self.create_segment(struct_handshake_ACK)
        # se pasa a bytes
        seg_ACK = seg_ACK.encode()

        # caso borde

        # se envía el mensaje
        self.send_pure(seg_ACK)

    # función que espera una petición syn, si el handshake
    # se realiza correctamente retorna un nuevo objeto SocketTCP
    def accept(self):
        # dice si la petición se reciió correctamente 
        syn_correctly = False

        while not syn_correctly:
            # se recibe la petición SYN
            message_SYN, address_SYN = self.recv_pure(buff_size)
            # se pasa el mensaje a estructura
            struct_handshake_SYN = self.parse_segment(message_SYN.decode())

            # se revisa que los headers sean correctos
            # SYN
            bool_SYN = struct_handshake_SYN[0] == "1"
            # ACK
            bool_ACK = struct_handshake_SYN[1] == "0"
            # se consigue el número de secuencia
            nsec_SYN = int(struct_handshake_SYN[3])

            # si es que los valores recibidos son correctos
            if (bool_SYN and bool_ACK and (type(nsec_SYN) == int)):
                syn_correctly = True
        
        # se crea el socket que se comunicará con el cliente
        response_SocketTCP = SocketTCP()
        # se le setea el número de secuencia
        response_SocketTCP.set_nSec(nsec_SYN+1)
        # se le da una nueva dirección de destino (la del cliente)
        response_SocketTCP.set_dirDestination(address_SYN)
        # se le hace binding a una dirección distinta a la del server
        response_SocketTCP.bind(('localhost',self.new_socket_port))
        # se aumenta el número del puerto para un futuro socket
        self.new_socket_port += 1

        # se crea el mensaje SYN+ACK
        struct_handshake_SYN_ACK = ["1","1","0",str(response_SocketTCP.nSec)]
        # se pasa a segmento
        seg_SYN_ACK = self.create_segment(struct_handshake_SYN_ACK)
        # se pasa a bytes
        seg_SYN_ACK = seg_SYN_ACK.encode()

        # dice si se recibió el ack corectamente
        ack_correctly = False
        
        while not ack_correctly:
            # se envía el mensaje
            response_SocketTCP.send_pure(seg_SYN_ACK)

            # se recibe la petición ACK
            message_ACK, address_ACK = response_SocketTCP.recv_pure(buff_size)
            # se pasa el mensaje a estructura
            struct_handshake_ACK = self.parse_segment(message_ACK.decode())

            # se obtienen headers, número de secuencia y address
            # SYN
            bool_ACK = struct_handshake_ACK[0] == "0"
            # ACK
            bool_SYN = struct_handshake_ACK[1] == "1"
            # se consigue el número de secuencia
            nsec_ACK = int(struct_handshake_ACK[3])

            # si es que se recib el mensaje ACK
            if(bool_ACK and bool_SYN and (response_SocketTCP.nSec + 1 == nsec_ACK)):
                # se le setea el nuevo nsec
                response_SocketTCP.set_nSec(nsec_ACK)
                # se revisa que la dirección recibida se la misma
                assert address_ACK == response_SocketTCP.dirDestination
                # se cambia la variable
                ack_correctly = True
            # si se resive el mensaje SYN de nuevo
            elif((not bool_ACK) and (not bool_SYN) and (response_SocketTCP.nSec -1 == nsec_ACK)):
                # se manda de nuevo el mensaje SYN_ACK (osea se contiúa el while)
                continue

        # finalmente se retorna el socket y adress 
        return response_SocketTCP, response_SocketTCP.dirOrigin

    def close(self):
        # se crea el mensaje de fin para el receptor
        FIN_struct = ["0","0","1",str(self.nSec)]
        # se pasa a seg
        FIN_seg = self.create_segment(FIN_struct)
        # se pasa a bytes
        FIN_seg = FIN_seg.encode()

        # número de timeouts ocurridos sim recibir respuesta
        timeouts = 0
        # dice si se recibio SYN_ACK correctamente
        SYN_ACK_correctly = False

        # se envía el mensaje que se quiere terminar la comunicacións
        self.send_pure(FIN_seg)

        while (not SYN_ACK_correctly) and timeouts < 4:
            try:
                # se recibe la respuesta 
                response = self.recv_pure(48)[0]
                # se parsea a estcutura
                response = self.parse_segment(response.decode())
                # se verifican los headers y el nSec
                # ACK
                bool_ACK = response[1] == "1"
                # FIN
                bool_FIN =  response[2] == "1"
                # nSec
                bool_nSec =  int(response[3]) == self.nSec + 1

                # si los 3 son correctos
                if(bool_ACK and bool_FIN and bool_nSec):
                    # se sale del while
                    SYN_ACK_correctly = True

            # se aumenta timeout
            except TimeoutError:
                timeouts += 1

        # si hay más de 3 se asume termino de conexión
        if(timeouts > 3):
            return

        # se actualiza el número de secuencia
        self.nSec += 2
        # se crea el mensaje de ACK para el receptor
        ACK_struct = ["0","1","0",str(self.nSec)]
        # se pasa a seg
        ACK_seg = self.create_segment(ACK_struct)
        # se pasa a bytes
        ACK_seg = ACK_seg.encode()

        timeouts = 0

        while timeouts <= 3:
            # se envía el mensaje que se quiere terminar la comunicacións
            self.send_pure(ACK_seg)

            try:
                # se espera tiemout 
                self.recv_pure(48)
            except TimeoutError:
                # se aumenta tiemouts 
                timeouts += 1

    def recv_close(self):
        # hasta que se reciba petición de cierre
        fin_recieved = False

        while not fin_recieved:
            # se recibe la petición de fin 
            request = self.recv_pure(48)[0]
            # se parsea a estcutura
            request = self.parse_segment(request.decode())
            # se verifican los headers
            # ACK
            bool_ACK = request[1] == "0"
            # FIN
            bool_FIN = request[2] == "1"
            # nSec
            nSec_request = int(request[3])
            if(bool_ACK and bool_FIN):
                fin_recieved = True

        # se crea el mensaje de fin ack para el emisor 
        FIN_ACK_struct = ["0","1","1",str(nSec_request+1)]
        # se pasa a seg
        FIN_ACK_seg = self.create_segment(FIN_ACK_struct)
        # se pasa a bytes
        FIN_ACK_seg = FIN_ACK_seg.encode()
        # se envía el mensaje que se quiere terminar la comunicacións
        self.send_pure(FIN_ACK_seg)

        # dice si se ha recibido un mensaje ACK
        ack_recieved = False
        # número de tiemouts
        timeouts = 0

        while not ack_recieved and timeouts < 4: 
            try:
                # se recibe la confirmación de confirmación de fin 
                confirm = self.recv_pure(48)[0]
                # se parsea a estcutura
                confirm = self.parse_segment(confirm.decode())
                # se verifican los headers
                # ACK
                bool_ACK = confirm[1] == "1"
                # FIN 
                bool_FIN = confirm[2] == "0"

                # si se confirma el FIN
                if(bool_ACK and bool_FIN):
                    # se termina la conexión
                    return

            # si hay tiemout
            except TimeoutError:
                timeouts += 1
        
        # se termina la conexión 
        return