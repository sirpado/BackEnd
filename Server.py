import DataLayer.sqlconnection as sqlconnection
from Scrapers import mainScraper
import multiprocessing
import socket
import json

class Server(object):
    def __init__(self, hostname, port):
        import logging
        self.logger = logging.getLogger("server")
        self.hostname = hostname
        self.port = port

    def start(self):
        self.logger.debug("listening")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.hostname, self.port))
        self.socket.listen(1)

        while True:
            conn, address = self.socket.accept()
            self.logger.debug("Got connection")
            process = multiprocessing.Process(target=handle, args=(conn, address))
            process.daemon = True
            process.start()
            self.logger.debug("Started process %r", process)
####################################End Of Class#######################################################


def handle(connection, address):
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("process-%r" % (address,))
    try:
        logger.debug("Connected %r at %r", connection, address)
        while True:
            data = connection.recv(1024)
            if data == b'':
                logger.debug("Socket closed remotely")
                break

            data = data[:-1]
            logger.debug("Received data %r", data)
            recived_json = json.loads(data.decode('utf-8'))
            command = str((recived_json["command"]))
            if command == 'scan':
                product_name = sqlconnection.scanBarcode(recived_json["barcode"])
                logger.debug("Sending Product Name %r",product_name)
                x = {"result":"name","name":product_name}
                connection.sendall(json.dumps(x,ensure_ascii=False).encode('utf-8'))
            elif command == 'search':
                searchWords = recived_json["ingredients"].split(",")
                urgentProducts = recived_json["urgent"].split(",")
                recipes = mainScraper.scrape(searchWords,urgentProducts)
                json_array = []
                for recipe in recipes:
                    json_array.append(recipe)
                    logger.debug("Sending Recipe %r",recipe)
                x = {"result":"recipes","items":json_array}
                connection.sendall(json.dumps(x,ensure_ascii= False).encode('utf-8'))
                #done = {"":"done"}
                #logger.debug(("Sending Done command"))
                #connection.sendall(json.dumps(done).encode())
            logger.debug("Sent data")

    except:
        logger.exception("Problem handling request")
    finally:
        logger.debug("Closing socket")
        connection.close()


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)
    server = Server("0.0.0.0", 9000)

    try:
        logging.info("Listening")
        server.start()
    except:
        logging.exception("Unexpected exception")
    finally:
        logging.info("Shutting down")
        for process in multiprocessing.active_children():
            logging.info("Shutting down process %r", process)
            process.terminate()
            process.join()
    logging.info("All done")



