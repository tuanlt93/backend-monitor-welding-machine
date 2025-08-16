# app

import PLC
import time
from apis import FlaskApp


def main():
    app = FlaskApp()
    app.start()

if __name__ == "__main__":
    main()
    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        print("Exit")


