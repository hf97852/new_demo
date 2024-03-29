
from vnpy_tts.api.vnttsmd import MdApi
from vnpy.event import EventEngine, Event

from PySide6 import QtWidgets, QtCore

class SimpleWidget(QtWidgets.QWidget):

    signal = QtCore.Signal(str)    # 定义一个QT事件机制中的信号

    """简单图形控件"""
    def __init__(self, event_engine: EventEngine) -> None:
        """构造函数"""
        super().__init__()   #  这里要首先调用Qt对象C++中的构造函数

        self.event_engine: EventEngine = event_engine
        self.event_engine.register("log", self.update_log)

        self.api = None

        # 定义要在事件引擎中使用的处理程序函数
        # HandlerType: callable = Callable[[Event], None] 定义一个HandlerType变量类型，此变量类型为一个可调用的对象类型（此对象为接受一个Event参数，返回值为None的函数名）。
        # Callable：表示可调用对象的类型。
        # print(HandlerType) 输出：typing.Callable[[__main__.Event], NoneType]； type(HandlerType) 输出：typing._CallableGenericAlias


        # 基础图形控件
        self.log_monitor: QtWidgets.QTextEdit = QtWidgets.QTextEdit()
        self.log_monitor.setReadOnly(True)    # 设置只读，防止误删

        self.subscribe_button: QtWidgets.QPushButton = QtWidgets.QPushButton("订阅")
        self.symbol_line: QtWidgets.QLineEdit = QtWidgets.QLineEdit()

        # 连接按钮函数
        self.subscribe_button.clicked.connect(self.subscribe_symbol)
        self.signal.connect(self.log_monitor.append)    # 子线程不能修改主线程中的图形界面，只能通过信号槽的方式，来传递信息。 3：55分讲解。插槽：log_monitor  ,一个信号对多个插槽，多个信号对一个插槽


        # 设置布局命令
        vbox: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.log_monitor)
        vbox.addWidget(self.symbol_line)
        vbox.addWidget(self.subscribe_button)

        self.setLayout(vbox)
        #self.setWindowTitle("simple")

    def subscribe_symbol(self) -> None:
        """订阅行情"""
        symbol: str = self.symbol_line.text()
        self.api.subscribeMarketData(symbol)    # 订阅多个合约时，c++封装类内部是怎么个间隔回调法？

    def update_log(self, event: Event) -> None:
        """更新日志"""
        msg: str = event.data
        self.signal.emit(msg)


class CtpMdApi(MdApi):

    def __init__(self, event_engine: EventEngine) -> None:
        super().__init__()

        self.event_engine: EventEngine = event_engine

    def onFrontConnected(self):
        """服务器连接成功回报"""
        self.write_log("行情服务器连接成功") # 将”log"，“行情服务器连接成功” 压入队列。 由于先前widget实例时，注册“log"、”update_log"进入_handlers字典，线程_run获取队列中的事件类型log，分发给update_log函数并执行。

        ctp_req: dict = {
            # "UserId": "000300",
            "UserId": "9076",
            "Password": "123456",
            # "Password": "vnpy1234",
            "BrokerID": "9999"
        }

        self.reqUserLogin(ctp_req,1)

    def onFrontDisconnected(self, reason: int) -> None:
        """服务器连接断开回报"""
        self.write_log(f"服务器连接断开{reason}")

    def onRspUserLogin(self, data: dict, error: dict, reqid: int, last: bool) -> None:
        """用户登陆请求回报"""
        if not error["ErrorID"]:
            self.write_log("行情服务器登陆成功")  #同上，写入队列，由线程分发并调用update_log函数。

            # 订阅行情推送
            # self.subscribeMarketData("rb2301")
            # self.subscribeMarketData("rb2406")
        else:
            self.write_log(f"行情服务器登陆失败{error}")


    def onRtnDepthMarketData(self, data: dict) -> None:
        """行情数据推送回调"""
        self.write_log(str(data))    # 间隔的行情数据推送回调，由线程_run分发执行update_log函数显示在log_monitor上。

    def write_log(self, msg: str) -> None:
        """"""
        event: Event = Event("log", msg)
        self.event_engine.put(event)



def main():
    """主函数"""
    # 创建并启动事件引擎
    event_engine: EventEngine = EventEngine()
    event_engine.start()
    # 事件引擎启动，即开始2个线程，不停循环的；_run_time线程间隔1秒放入eTimer的event事件；_run线程不停get队列中的event事件，并分发给监听此事件类别的handler,与监听所有事件类别的通用handler。
    # 开始通用handler为空，监听的handler也为空。  说明：这个程序知道在widget中注册一个update_log函数。

    # quere.get(block, timeout) 队列为空时，get方法一直阻塞。block=False,timeout无意义，不会阻塞，block=True,根据timeout是阻塞一段时间还是一直阻塞。
    # quere为空时，抛出Empty异常，

    # 创建Qt应用
    app: QtWidgets.QApplication = QtWidgets.QApplication()

    # 创建图形控件
    widget: SimpleWidget = SimpleWidget(event_engine)
    widget.show()

    # 创建API实例
    api: CtpMdApi = CtpMdApi(event_engine)      # event_engine 同时传给widget, api，应该为公共变量。
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

    # 启动主线程UI循环
    app.exec()

    # 关闭事件引擎
    event_engine.stop()


if __name__ == '__main__':
    main()
