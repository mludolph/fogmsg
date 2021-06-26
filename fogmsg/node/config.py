class NodeConfig:
    def __init__(self, args):
        self.MASTER_HOSTNAME = args.master_hostname
        self.IP = args.ip
        self.PORT = args.port
        self.ADVERTISED_HOSTNAME = args.advertised_hostname
        self.PERSISTENCE_DIR = args.persistence_dir
        self.SENDER_QUEUE_LENGTH = args.sender_queue_length
        self.SENDER_TIMEOUT = args.sender_timeout
        print(args.sender_timeout)
