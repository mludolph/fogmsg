# fogmsg - Simulated cloud messages

## Requirements

- Linux based system
- Python 3 (Tested on version 3.8.2)
- Python Packages from `requirements.txt` (i.e. run `pip install -r requirements.txt`)

## Master

### Usage

```bash
$ python fogmsg/executables/master.py --help
usage: master.py [-h] [-i IP] [-p PORT]

fogmsg Master

optional arguments:
  -h, --help            show this help message and exit
  -i IP, --ip IP        address that the node will bind to (default: 0.0.0.0)
  -p PORT, --port PORT  port that the node will bind to (default: 4000)
```

### Deploying a master node

```bash
$ scripts/start_master.sh
# or
$ python fogmsg/exectuables/master.py
```

### Edge node

```bash
$ python fogmsg/executables/node.py --help
usage: node.py [-h] [--master MASTER] [-i IP] [-p PORT] [--advertised_listener ADVERTISED_LISTENER]

fogmsg Node

optional arguments:
  -h, --help            show this help message and exit
  --master MASTER       hostname of the master (default: tcp://localhost:4000)
  -i IP, --ip IP        address that the node will bind to (default: 0.0.0.0)
  -p PORT, --port PORT  port that the node will bind to (default: 4001)
  --advertised_listener ADVERTISED_LISTENER
                        the advertisement listener of this node (default: tcp://localhost:4001)
```

## Deploying an edge node

```bash
$ scripts/start_node.sh
# or
$ python fogmsg/exectuables/node.py
```
