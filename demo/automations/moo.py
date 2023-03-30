def main():
    start_recording()
    info('fffasdfcd')
    open_switch("A", slow=True, block=True)
    open_switch("A")
    sleep(10)
    close_switch("B")
    info('asdfafvvv')