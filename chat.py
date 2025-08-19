import socket, threading, argparse

parser = argparse.ArgumentParser()
parser.add_argument('-ip',"--ip", type=str, help='The IP address of the server', metavar="")
parser.add_argument("-m","--max",type=int,help="The maximum numbers of account", metavar="")
parser.add_argument("-p","--port",type=int,help="The connecting port (must be spare)", metavar="")
args=parser.parse_args()
if args.ip:
    ip = args.ip
    print(f"According to your argument, the IP address is set to {ip}")
else:
    ip = input("Connect to IP:")
if args.max:
    account_numbers = args.max
    print(f"According to your argument, the maximum numbers of account is set to {account_numbers}")
else:
    account_numbers = eval(input("The maximum numbers of account:"))
if args.port:
    portin = args.port
    print(f"According to your argument, the connecting port is set to {portin}")
else:
    portin = eval(input("The connecting port (must be spare):"))

s = socket.socket()
s.bind((ip, portin))
s.listen(account_numbers)
s.setblocking(0)

conn = []
address = []

def add_accounts():
    while 1:
        if len(conn) > account_numbers:
            break
        conntmp = None
        addresstmp = None
        try:
            conntmp, addresstmp = s.accept()
        except:
            continue
        conntmp.setblocking(0)
        conn.append(conntmp)
        address.append(addresstmp)
        print(f"Connected, ip address: {addresstmp}")


def receive_msg():
    while 1:
        for i in range(len(conn)):
            data = None
            try:
                data = conn[i].recv(1024).decode('UTF-8')
            except:
                continue
            if (not data):
                continue
            print(f"Message from client {address[i]}, msg: {data}")
            for j in range(len(conn)):
                try:
                    conn[j].send(bytes(data, encoding='utf-8'))
                except:
                    pass

t1 = threading.Thread(target=add_accounts)
t2 = threading.Thread(target=receive_msg)
t1.start()
t2.start()
