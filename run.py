
# from vnpy_ctp.api.vnctpmd import MdApi
from vnpy_tts.api.vnttsmd import MdApi

class CtpMdApi(MdApi):

    def __init__(self) -> None:
        super().__init__()

    def onFrontConnected(self):
        print("服务器连接成功")

        ctp_req: dict = {
            # "UserId": "000300",
            "UserId": "9076",
            "Password": "123456",
            # "Password": "vnpy1234",
            "BrokerID": "9999"
        }

        self.reqUserLogin(ctp_req,1)

    def onFrontDisconnected(self, reason) -> None:
        print("服务器连接断开", reason)

    def onRspUserLogin(self, data, error, reqid, last):
        if not error["ErrorID"]:
            print("行情服务器登陆成功")

            # 订阅行情推送
            # self.subscribeMarketData("rb2301")
            self.subscribeMarketData("rb2406")
        else:
            print("行情服务器登陆失败",error)

    def onRtnDepthMarketData(self, data):
        """行情数据推送回调"""
        print(data)
        # print(data)
        # print(error)



def main():
    """主函数"""
    # 创建实例
    api = CtpMdApi()

    # 初始化底层
    api.createFtdcMdApi(".")

    # 注册服务器地址
    #api.registerFront("tcp://180.168.146.187:10130")
 # api.registerFront("tcp://122.51.136.165 20004")  //tts
 #    api.registerFront("tcp://121.37.90.193:20002")   仿真环境 交易前置登陆失败
    api.registerFront("tcp://121.37.80.177:20004")

    # 发起连接
    api.init()

    # 阻塞主进程推出
    input()


if __name__ == '__main__':
    main()
