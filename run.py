
#from  vnpy_ctp.api.vnctp.vnctpmd import MdApi

from .vnctpmd import MdApi
#from .vnctptd import TdApi
#from .ctp_constant import *

class CtpMdApi(MdApi):

    def __init__(self) -> None:
        super().__init__()

    def onFrontConnect(self):
        print("onFrontConnect")


if __name__ == '__main__':
    api = CtpMdApi()
    api.createFtdcMdApi()
    api.registerFront("tcp://180.168.146.187:10131")
 #   api.registerFront("tcp://122.51.136.165 20004")  //tts

    api.init()
    input()

