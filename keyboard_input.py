import threading

class KeyboardThread(threading.Thread):

    def __init__(self, input_cbk = None, name='keyboard-input-thread'):
        self.input_cbk = input_cbk
        super(KeyboardThread, self).__init__(name=name, daemon=True)
        self.start()

    def run(self):
        while True:
            self.input_cbk(input()) #waits to get input + Return



def my_callback(inp):
    #evaluate the keyboard input
    print('You Entered:', inp, ' Counter is at:', showcounter)

if __name__ == '__main__':
  showcounter = 0 #something to demonstrate the change
  # start the Keyboard thread
  kthread = KeyboardThread(my_callback)

  while True:
    #the normal program executes without blocking. here just counting up
    showcounter += 1
