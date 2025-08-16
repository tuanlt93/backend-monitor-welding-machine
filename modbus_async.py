import asyncio
from pymodbus.client import AsyncModbusSerialClient
import time

async def poll_all_slaves(client: AsyncModbusSerialClient, units: list, addr=0, count=5):
    i : int = 0
    while True:
        for uid in units:
            try:
                rsp = await client.read_holding_registers(
                    address=addr, count=count, slave=uid
                )
                if not rsp.isError():
                    print(f"[{uid}] ✅ {rsp.registers}")
                    i = i+1
                else:
                    print(f"[{uid}] ⚠️  {rsp}")
                    
            except Exception as e:
                print(f"[{uid}] ❌ Exception: {e}")
        
        time.sleep(1)
        # không cần sleep cố định – đọc xong một vòng lại tiếp tục

async def main():
    client = AsyncModbusSerialClient(
        port="COM20", baudrate=9600, bytesize=8, parity="N",
        stopbits=1, timeout=1.0   # sẽ KHÔNG làm delay cố định nếu PLC phản hồi nhanh
    )
    await client.connect()
    if client.connected:
        await poll_all_slaves(client, [1, 2])
    else:
        print("Không thể kết nối COM")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("EXIT")

