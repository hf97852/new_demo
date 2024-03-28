import sys

# from vnpy_ctp.api.vnctpmd import MdApi
from vnpy_tts.api.vnttsmd import MdApi
from PySide6 import QtWidgets


class SimpleWidget(QtWidgets.QWidget):
    """简单图形控件"""
    def __init__(self):
        """构造函数"""
        super().__init__()   #  这里要首先调用Qt对象C++中的构造函数

        # 用来绑定api对象
        self.api = None

        # 基础图形控件
        self.log_monitor = QtWidgets.QTextEdit()
        self.log_monitor.setReadOnly(True)    # 设置只读，防止误删

        self.subscribe_button = QtWidgets.QPushButton("订阅")
        self.symbol_line = QtWidgets.QLineEdit()

        # 连接按钮函数
        self.subscribe_button.clicked.connect(self.subscribe_symbol)


        # 设置布局命令
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.log_monitor)
        vbox.addWidget(self.symbol_line)
        vbox.addWidget(self.subscribe_button)

        self.setLayout(vbox)
        #self.setWindowTitle("simple")

    def subscribe_symbol(self):
        symbol = self.symbol_line.text()
        self.api.subscribeMarketData(symbol)

class CtpMdApi(MdApi):

    def __init__(self, monitor) -> None:
        super().__init__()

        self.monitor = monitor

    def onFrontConnected(self):
        self.monitor.append("服务器连接成功")

        ctp_req: dict = {
            # "UserId": "000300",
            "UserId": "9076",
            "Password": "123456",
            # "Password": "vnpy1234",
            "BrokerID": "9999"
        }

        self.reqUserLogin(ctp_req,1)

    def onFrontDisconnected(self, reason) -> None:
        self.monitor.append("服务器连接断开", reason)

    def onRspUserLogin(self, data, error, reqid, last):
        if not error["ErrorID"]:
            self.monitor.append("行情服务器登陆成功")

            # 订阅行情推送
            # self.subscribeMarketData("rb2301")
            # self.subscribeMarketData("rb2406")
        else:
            self.monitor.append("行情服务器登陆失败",error)


    def onRtnDepthMarketData(self, data):
        """行情数据推送回调"""
        self.monitor.append(str(data))




def main():
    """主函数"""
    app = QtWidgets.QApplication()

    widget = SimpleWidget()
    widget.show()


    # 创建实例
    api = CtpMdApi(widget.log_monitor)
    widget.api = api
    # 初始化底层
    api.createFtdcMdApi(".")

    # 注册服务器地址
    #api.registerFront("tcp://180.168.146.187:10130")
 # api.registerFront("tcp://122.51.136.165 20004")  //tts
 #    api.registerFront("tcp://121.37.90.193:20002")   仿真环境 交易前置登陆失败
    api.registerFront("tcp://121.37.80.177:20004")

    # 发起连接
    api.init()

    app.exec()


if __name__ == '__main__':
    main()
