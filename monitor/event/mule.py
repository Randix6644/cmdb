from monitor.event.rpc import RPCServer

# 以主程序启动时，检查是否运行在 uwsgi 中，启动调度器并阻塞线程
if __name__ == '__main__':
    try:
        import uwsgi
    except ImportError:
        print('mule must be running in uwsgi')
    else:
        print('rpc server starting...')
        rpc = RPCServer()
        rpc.run()
        print('rpc server closing...')
