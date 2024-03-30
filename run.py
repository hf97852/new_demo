
# from vnpy_tts.api.vnttsmd import MdApi
from vnpy.event import EventEngine, Event
from vnpy.trader.event import EVENT_LOG, EVENT_TICK
from vnpy.trader.constant import Exchange
from vnpy.trader.object import TickData, LogData, SubscribeRequest
from vnpy_ctp import CtpGateway

from PySide6 import QtWidgets, QtCore


class SimpleWidget(QtWidgets.QWidget):

    # signal = QtCore.Signal(str)    # 定义一个QT事件机制中的信号

    """简单图形控件"""
    def __init__(self, event_engine: EventEngine) -> None:
        """构造函数"""
        super().__init__()   #  这里要首先调用Qt对象C++中的构造函数

        self.event_engine: EventEngine = event_engine
        # self.event_engine.register("log", self.update_log)
        self.event_engine.register(EVENT_LOG, self.process_log_event)
        self.event_engine.register(EVENT_TICK, self.process_tick_event)

        # 用于绑定API对象
        self.gateway: CtpGateway = None

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

        # self.signal.connect(self.log_monitor.append)    # 子线程不能修改主线程中的图形界面，只能通过信号槽的方式，来传递信息。 3：55分讲解。插槽：log_monitor  ,一个信号对多个插槽，多个信号对一个插槽


        # 设置布局命令
        vbox: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.log_monitor)
        vbox.addWidget(self.symbol_line)
        vbox.addWidget(self.subscribe_button)

        self.setLayout(vbox)
        #self.setWindowTitle("simple")

    def subscribe_symbol(self) -> None:
        """订阅行情"""
        vt_symbol: str = self.symbol_line.text()
        symbol, exchange_str = vt_symbol.split(".")

        req = SubscribeRequest(
            symbol = symbol,
            exchange = Exchange(exchange_str)
        )
        self.gateway.subscribe(req)

        # self.api.subscribeMarketData(symbol)    # 订阅多个合约时，c++封装类内部是怎么个间隔回调法？

    def process_log_event(self, event: Event) -> None:
        """更新日志"""
        log: LogData = event.data
        self.log_monitor.append(log.msg)

    def process_tick_event(self, event: Event) -> None:
        """更新行情"""
        tick: TickData = event.data
        self.log_monitor.append(str(tick))


#   def update_log(self, event: Event) -> None:
 #       """更新日志"""
  #      msg: str = event.data
   #     self.signal.emit(msg)


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

    # CTP交易接口
    ctp_setting = {
        "用户名": "000300",
        "密码": "vnpy1234",
        "经纪商代码": "9999",
        "交易服务器": "180.168.146.187:10130",
        "行情服务器": "180.168.146.187:10131",
        "产品名称": "simnow_client_test",
        "授权编码": "0000000000000000"
    }
    ctp_gateway = CtpGateway(event_engine, 'CTP')   # 实例ctp_gateway时，绑定CtpMdApi的实例，CtpMdApi实例又反过来绑定ctp_gateway实例。
    ctp_gateway.connect(ctp_setting)   # 也包括api实例（成员变量）、初始化底层、注册服务器地址、发起连接api.init()。然后回调函数服务器连接成功，再发起登陆
    widget.gateway = gateway = ctp_gateway

    # 启动主线程UI循环
    app.exec()

    # 关闭事件引擎
    event_engine.stop()

    gateway.close()


if __name__ == '__main__':  # IF2405.CFFEX查询成功！
    main()
