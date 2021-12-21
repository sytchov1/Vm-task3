import asyncio
import uuid


HOST = '127.0.0.1'
PORT_1 = 8000
PORT_2 = 8001
BUFFER_SIZE = 64


async def generate_uid():
    return str(uuid.uuid1())


async def connect(host, port):
    print('Подключаемся к серверу... (Убедитесь, что сервер включен)')
    while True:
        try:
            r, w = await asyncio.open_connection(host, port)
            break
        except ConnectionError:
            pass
    return r, w


async def send_data(writer, data):
    print('Отправляем запрос на сервер...')
    try:
        writer.write(data.encode())
    except ConnectionError:
        print("Соединение с сервером потеряно")


async def receive_data(reader):
    print("Ждём ответ...")
    d = bytearray()
    while True:
        chunk = await reader.read(BUFFER_SIZE)
        d += chunk
        reader.feed_eof()
        if reader.at_eof():
            break
    return d.decode()


async def get_code():
    reader, writer = await connect(HOST, PORT_1)
    try:
        while True:
            print("Генерируем уникальный идентификатор...")
            uid = await generate_uid()

            await send_data(writer, uid)

            response = await receive_data(reader)

            if response:
                print(f"Ваш уникальный идентификатор (UID): {uid}")
                print(f'Ваш код (CODE): {response}')
                break
    finally:
        writer.close()
        await writer.wait_closed()
        print("Соединение закрыто\n")


async def send_message(params):
    reader, writer = await connect(HOST, PORT_2)
    try:
        await send_data(writer, params)

        response = await receive_data(reader)
        print(f'<-- {response}')
    finally:
        writer.close()
        await writer.wait_closed()
        print("Соединение закрыто\n")


def main():
    try:
        asyncio.run(get_code())

        print('Для отправки сообщения введите его текст, ваш уникальный идентификатор и код, полученный от сервера, '
              'в формате: "Текст сообщения" UID CODE')
        print('Для завершения работы введите "exit" или нажмите Ctrl+C\n')
        while True:
            temp = input("--> ").strip()
            if temp == "":
                pass
            elif temp == "exit":
                break
            else:
                asyncio.run(send_message(temp))
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
