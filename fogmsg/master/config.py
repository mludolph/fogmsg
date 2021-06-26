class MasterConfig:
    def __init__(self, args):
        self.IP = args.ip
        self.PORT = args.port
        self.PERSISTENCE_DIR = args.persistence_dir
        self.SENDER_QUEUE_LENGTH = args.sender_queue_length
        self.SENDER_TIMEOUT = args.sender_timeout
        self.UI_PORT = args.ui_port
