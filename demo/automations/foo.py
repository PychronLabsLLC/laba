def main():
    start_recording()
    info('fffasdfcd')
    sleep(10)
    open_switch("A", slow=True, block=True)
    open_switch("A")
    sleep(10)
    close_switch("B")
    info('asdfafvvv')