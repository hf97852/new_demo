
# from vnpy_tts.api.vnttsmd import MdApi
from vnpy.event import EventEngine, Event
from vnpy.trader.event import (EVENT_LOG, EVENT_TICK, EVENT_CONTRACT, EVENT_POSITION, EVENT_TIMER)
from vnpy.trader.constant import (Exchange, Direction, OrderType, Offset)
from vnpy.trader.object import (TickData, LogData, SubscribeRequest, ContractData, PositionData, OrderRequest)
from vnpy.trader.gateway import BaseGateway
# from vnpy_ctp import CtpGateway
from vnpy_tts import TtsGateway as CtpGateway

from PySide6 import QtWidgets


class SimpleWidget(QtWidgets.QWidget):
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

class MonitorEngine:
    """监控引擎"""

    def __init__(self, event_engine: EventEngine, gateway: BaseGateway) -> None:
        """"""
        self.event_engine: EventEngine = event_engine
        self.gateway: BaseGateway = gateway

        self.ticks: dict[str, TickData] = {}
        self.contracts: dict[str, ContractData] = {}
        self.positions: dict[str, PositionData] = {}
        self.subscribed: set[str] = set()

        self.event_engine.register(EVENT_TICK, self.process_tick_event)        # on_tick在行情推送回报中,压入事件引擎的队列中, 订阅市场数据,触发订阅行情回报、与行情推送回报. 在subscribe函数中，启动订阅行情数据，并在订阅集合中追加订阅symbol.
        self.event_engine.register(EVENT_CONTRACT, self.process_contract_event)
        # 在合约查询回报函数中（一个回报函数压入一个合约，难道请求合约查询后，分多次回调这个回报函数，逐个将所有合约压入队列中？答：估计一次请求查询合约，回调一次函数压入队列，即使合约查询完成，又while()重复循环查），压入事件引擎的队列中，供事件分发与处理

        self.event_engine.register(EVENT_POSITION, self.process_position_event)
        # self.event_engine.register(EVENT_TIMER, self.process_timer_event)  # 定时事件触发，再定时事件中触发：查询资金账户、持仓信息。
        self.event_engine.register(EVENT_LOG, self.process_log_event)

        self.tick_history: list[TickData] = []
        self.trading_symbol: str = "IF2405.CFFEX"
        self.trading_target: int = 0

    def process_tick_event(self, event: Event) -> None:      # 而subscribe函数在持仓事件中订阅行情！
        """行情事件"""
        tick: TickData = event.data
        self.ticks[tick.vt_symbol] = tick      # 分别保存持仓合约的行情数据。

        # 缓存交易合约的Tick历史
        if tick.vt_symbol == self.trading_symbol:
            self.tick_history.append(tick)

            self.run_trading()

    def process_contract_event(self, event: Event) -> None:   # 交易服务器连接、登陆、结算信息确认成功——》请求查询合约——》查询合约回调，合约压入事件队列。
        # 说明：查询合约信息有多条，每条保存symbol_contract_map全局缓存字典中。
        """合约事件"""
        contract: ContractData = event.data
        self.contracts[contract.vt_symbol] = contract   # 通过事件引擎，把合约信息全部保存在 新的contracts字典中。这个由于后面查询合约，不再压入事件队列，不在更新？
        # 【（答：估计while()循环查询合约，才能不停的订阅.trading_symbol的行情数据，才能解释tick数据大于3个，才能执行后面的买卖策略。）】

        # 订阅策略合约行情
        if contract.vt_symbol == self.trading_symbol:  # 请求一个合约、压入队列（此处一个循环），马上取出执行process_contract_event（一个线程中执行），接着压订阅行情、行情回报、压入队列，这个线程再从事件队列（含有EVENT_CONTRACT、EVENT_TICK）中，分发与处理事件。
            req = SubscribeRequest(contract.symbol, contract.exchange)
            self.gateway.subscribe(req)   # 查询合约、与交易合约的行情事件同时存在队列中，即队列含有EVENT_CONTRACT、EVENT_TICK。 （最终都会将合约放入contracts中，其中trading_symbol订阅行情数据同时保存在ticks、 tick_history中）

    def process_position_event(self, event: Event) -> None: # 说明：查询持仓信息有多条，每条保存positions（CtpTdApi类定义的，非这个MonitorEngine中定义的position)中,在压入持仓事件中，最后清空CtpTdApi类定义的positions字典。
        """持仓事件"""
        position: PositionData = event.data
        self.positions[position.vt_positionid] = position     # 通过事件引擎，把持仓信息全部（注：是分多次调用事件处理函数保存下来的）保存在 新的positions字典中。但这个由于2秒查询一次持仓信息、压入事件队列，触发事件引擎、更新此数据。

        # 如果已经订阅，则跳过
        if position.vt_symbol in self.subscribed:   # 初始订阅集合为空。
            return

        # 如果没收到合约，则跳过.  订阅行情、下单、撤单等操作，最好等合约信息到了之后才做。
        # 因为接口已连接上就会初始化查询合约信息，如果合约信息还没收到说明初始化未完成，这时操作可能触发流控、堵了、一些数据没有
        contract = self.contracts.get(position.vt_symbol, None)
        if not contract:
            return

        # 订阅行情
        req: SubscribeRequest = SubscribeRequest(contract.symbol, contract.exchange)
        self.gateway.subscribe(req)

        # 记录信息
        self.subscribed.add(position.vt_symbol)

    def process_timer_event(self, event: Event) -> None:
        """定时事件"""
        self.calculate_value()

    def process_log_event(self, event: Event) -> None:
        """日志事件"""
        print(event.data.msg)

    def calculate_value(self) -> None:
        """"计算市值"""
        for position in self.positions.values():
            tick: TickData = self.ticks.get(position.vt_symbol, None)
            contract: ContractData = self.contracts.get(position.vt_symbol, None)

            # 如果缺失行情或者合约，则跳过计算
            if not tick or not contract:
                continue

            value = position.volume * tick.last_price * contract.size
            print(f"{position.vt_symbol} {position.direction}当前持仓市值{value}")

    def run_trading(self) -> None:
        """执行策略交易"""
        # 检查至少要3个Tick
        if len(self.tick_history) < 3:   # 从此处知道一个tick是一个切面行情数据。
            return
        # 提取行情和合约
        tick1 = self.tick_history[-1]
        tick2 = self.tick_history[-2]
        tick3 = self.tick_history[-3]

        contract = self.contracts[self.trading_symbol]

        # print(tick1.datetime, tick1.last_price, self.trading_target)

        # 多头检查
        if tick1.last_price > tick2.last_price > tick3.last_price:
            if not self.trading_target:
                req = OrderRequest(
                    symbol=contract.symbol,
                    exchange=contract.exchange,
                    direction=Direction.LONG,
                    type=OrderType.LIMIT,
                    price=tick1.last_price + 10,
                    volume=1,
                    offset=Offset.OPEN
                )
                self.gateway.send_order(req)

                self.trading_target = 1
                print(f"{self.trading_symbol}买入开仓1手", tick1.datetime)

        # 空头检查
        if tick1.last_price < tick2.last_price < tick3.last_price:
            if self.trading_target > 0:
                req = OrderRequest(
                    symbol=contract.symbol,
                    exchange=contract.exchange,
                    direction=Direction.SHORT,
                    type=OrderType.LIMIT,
                    price=tick1.last_price - 10,
                    volume=1,
                    offset=Offset.CLOSE
                )
                self.gateway.send_order(req)

                self.trading_target = 0
                print(f"{self.trading_symbol}卖出平仓1手", tick1.datetime)
                
def main():
    """主函数"""
    # 创建并启动事件引擎
    event_engine: EventEngine = EventEngine()
    event_engine.start()
    # 事件引擎启动，即开始2个线程，不停循环的；_run_time线程间隔1秒放入eTimer的event事件；_run线程不停get队列中的event事件，并分发给监听此事件类别的handler,与监听所有事件类别的通用handler。
    # 开始通用handler为空，监听的handler也为空。  说明：这个程序知道在widget中注册一个update_log函数。

    # quere.get(block, timeout) 队列为空时，get方法一直阻塞。block=False,timeout无意义，不会阻塞，block=True,根据timeout是阻塞一段时间还是一直阻塞。
    # quere为空时，抛出Empty异常，

    # # 创建Qt应用
    # app: QtWidgets.QApplication = QtWidgets.QApplication()
    #
    # # 创建图形控件
    # widget: SimpleWidget = SimpleWidget(event_engine)
    # widget.show()

    # CTP交易接口
    # ctp_setting = {
    #     "用户名": "000300",
    #     "密码": "vnpy1234",
    #     "经纪商代码": "9999",
    #     "交易服务器": "180.168.146.187:10130",
    #     "行情服务器": "180.168.146.187:10131",
    #     "产品名称": "simnow_client_test",
    #     "授权编码": "0000000000000000"
    # }

    ctp_setting = {
        "用户名": "3271",
        "密码": "123456",
        "经纪商代码": "",
        "交易服务器": "tcp://121.37.80.177:20002",
        "行情服务器": "tcp://121.37.80.177:20004",
        "产品名称": "",
        "授权编码": ""
    }
    # "交易服务器": "tcp://122.51.136.165:20002",
    # "行情服务器": "tcp://122.51.136.165:20004",


    ctp_gateway = CtpGateway(event_engine, 'CTP')   # 实例ctp_gateway时，绑定CtpMdApi的实例，CtpMdApi实例又反过来绑定ctp_gateway实例。
    ctp_gateway.connect(ctp_setting)   # 也包括api实例（成员变量）、初始化底层、注册服务器地址、发起连接api.init()。然后回调函数服务器连接成功，再发起登陆
    # tdapi仅仅是用来接受当日合约的详情。 合约信息查询成功。

    #widget.gateway = gateway = ctp_gateway
    gateway = ctp_gateway

    engine: MonitorEngine = MonitorEngine(event_engine, gateway)

    # # 启动主线程UI循环
    # app.exec()

    input()

    # 关闭事件引擎
    event_engine.stop()

    gateway.close()


if __name__ == '__main__':  # IF2405.CFFEX查询成功！
    main()
