import sys
import getopt

import Checksum
import BasicSender

'''
This is a skeleton sender class. Create a fantastic transport protocol here.
'''
class Sender(BasicSender.BasicSender):
    def __init__(self, dest, port, filename, debug=False):
        super(Sender, self).__init__(dest, port, filename, debug)
        self.window={}
        self.max_size=5
        self.last_ack=None
        self.last_ack_num=0
        self.end=False
        self.seq_no=0
	self.end_packet=None

    # Main sending loop.
    def start(self):
        msg_type=None
        while not len(self.window)==5:
            msg=self.infile.read(1300)
            if self.seq_no==0:
                msg_type='start'
            elif msg=="":
                msg_type='end'
            else:
                msg_type='data'
            packet=self.make_packet(msg_type,self.seq_no,msg)
            self.send(packet)
            self.window[self.seq_no]=packet
            self.seq_no+=1
        while (not self.end) or (not len(self.window)==0):
            ack=self.receive(0.5)
            if ack==None:
                self.handle_timeout()
            elif Checksum.validate_checksum(ack):
                msg_type,seq_no,data,checksum=self.split_packet(ack)
                if self.last_ack_num==0:
                    self.last_ack_num=seq_no
                    self.last_ack=ack
                    self.handle_new_ack(ack)
                elif seq_no==self.last_ack_num:
                    self.handle_dup_ack(ack)
                else:
                    self.handle_new_ack(ack)
            else:
                print "it gets corrupted"
                self.send(self.window[self.last_ack_num])
	self.send(self.end_packet)
	self.seq_no=0
	self.last_ack_num=0
	self.last_ack=None
	self.end=False
	self.end_packet=None






        

    def handle_timeout(self):
        for x in self.window.values():
            msg_type,seq_no,data,checksum=self.split_packet(x)
            self.send(x)

    def handle_new_ack(self, ack):
        msg_type,seq_no,data,checksum=self.split_packet(ack)
        if Checksum.validate_checksum(ack):
            if seq_no>self.last_ack_num:
                self.last_ack_num=int(seq_no)
                self.last_ack=ack
            for x in self.window.keys():
                if x<int(seq_no):
                    self.window.pop(x,0)

            while (not len(self.window)==5) and (not self.end): 
                msg=self.infile.read(1300)
                self.seq_no+=1
                if msg=="":
                    msg_type='end'
                    packet=self.make_packet(msg_type,self.seq_no,msg)
                    self.end=True
                    self.end_packet=packet
                else:
                    msg_type='data'
                    packet=self.make_packet(msg_type,self.seq_no,msg)
                    self.window[self.seq_no]=packet
                    self.send(packet)

    def handle_dup_ack(self, ack):
        msg_type,seq_no,data,checksum=self.split_packet(ack)
        if Checksum.validate_checksum(ack):
            self.send(self.window[int(seq_no)])

    def log(self, msg):
        if self.debug:
            print msg

'''
This will be run if you run this script from the command line. You should not
change any of this; the grader may rely on the behavior here to test your
submission.
'''
if __name__ == "__main__":
    def usage():
        print "BEARS-TP Sender"
        print "-f FILE | --file=FILE The file to transfer; if empty reads from STDIN"
        print "-p PORT | --port=PORT The destination port, defaults to 33122"
        print "-a ADDRESS | --address=ADDRESS The receiver address or hostname, defaults to localhost"
        print "-d | --debug Print debug messages"
        print "-h | --help Print this usage message"

    try:
        opts, args = getopt.getopt(sys.argv[1:],
                               "f:p:a:d", ["file=", "port=", "address=", "debug="])
    except:
        usage()
        exit()

    port = 33122
    dest = "localhost"
    filename = None
    debug = False

    for o,a in opts:
        if o in ("-f", "--file="):
            filename = a
        elif o in ("-p", "--port="):
            port = int(a)
        elif o in ("-a", "--address="):
            dest = a
        elif o in ("-d", "--debug="):
            debug = True

    s = Sender(dest,port,filename,debug)
    try:
        s.start()
    except (KeyboardInterrupt, SystemExit):
        exit()
