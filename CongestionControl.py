class CongestionControl:
    def __init__(self, MSS:int):
        # estado actual de control de congestión (slow star o congestion avoidance)
        self.current_state = "slow start"
        # entero que indica el tamaño máximo en bytes del área de datos en un segmento congestión
        self.MSS = MSS
        # entero que indica el tamaño de la ventana de congestión en bytes (se incia con un MSS)
        self.cwnd = self.MSS
        # slow start Threshold, cuando current state es slow start si cwnd >= ssthresh entonces
        # se cambia el current state a congestion avoidance, se define luego del primer tiemout
        self.ssthresh = None

    # retorna el valor current_state
    def get_current_state(self):
        return self.current_state

    # retorna el valor MSS
    def get_MSS(self):
        return self.MSS

    # retorna el valor cwnd
    def get_cwnd(self):
        return self.cwnd
    
    # retorna valor de sssthresh
    def get_ssthresh(self):
        return self.ssthresh
    
    # retorna el tamaño de la ventana expersado como la cantidad de MSSs completos que caben cwnd
    def get_MSS_in_cwnd(self):
        # division entera
        return self.get_cwnd()//self.get_MSS()
    
    # se encarga de cambios al recibir un ACK
    def event_ack_received(self):
        # para el caso slow start
        if(self.is_state_slow_start()):
            # se aumenta la cwnd en un MSS
            self.cwnd += self.MSS
            # si hay un ssthresh
            if(self.get_ssthresh() != None):
                # si el cwnd es mayor a ssthresh
                if(self.get_cwnd() >= self.get_ssthresh()):
                    # se pasa a conggestion avoidance 
                    self.current_state = "congestion avoidance"
        # para el caso congesion avoidance 
        elif(self.is_state_congestion_avoidance()):
            # se aunmenta la cwnd en MSS/cwnd
            self.cwnd += (1/self.get_MSS_in_cwnd())

        # chequear cambios de estado
        
    # función que se encarga de los cambios asociados a recepción de un timeout
    def event_timeout(self):
        # si ocurre durante slow start
        if(self.is_state_slow_start()):
            #si ocurre por primera vez (osea, ssthresh es None)
            if((self.get_ssthresh() == None)):
                # se setea como la mitad del tamaño de la ventana que provocó timeout
                self.ssthresh = self.get_cwnd()/2
            # se baja el tamaño de la ventana a un MSS
            self.cwnd = self.get_MSS()
        # si ocurre un timeout durante congestion avoidance
        if(self.is_state_congestion_avoidance()):
            # se cambia el thresh
            self.ssthresh = self.get_cwnd()/2
            # se cambia el cwnd
            self.cwnd = self.get_MSS()
            # se vuelve a slow start
            self.current_state = "slow start"
    
    # dice si está en estado slow start o no
    def is_state_slow_start(self):
        if(self.get_current_state() == "slow start"):
            return True
        else:
            return False
        
    # dice si está en estado congestion avoidance o no
    def is_state_congestion_avoidance(self):
        if(self.get_current_state() == "congestion avoidance"):
            return True
        else:
            return False
    

