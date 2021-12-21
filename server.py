import asyncio
import uuid
import logging


HOST = '127.0.0.1'
PORT_1 = 8000
PORT_2 = 8001
BUFFER_SIZE = 64

CLIENTS = {}
logging.basicConfig(filename='server.log',
                    format='%(asctime)s | %(message)s',
                    datefmt='%d-%m-%y %H:%M:%S',
                    level=logging.INFO)


async def generate_code():
    return str(uuid.uuid4())


async def extract_params(data):
    try:
        message, temp = data[1:].split('\" ')
        uid, code = temp.split()
        result = [message, uid, code]
    except:
        result = []
    return result


async def open_port(host, port, handler):
    s = None
    try:
        print(f"Открываем порт {port}...")
        s = await asyncio.start_server(client_connected_cb=handler, host=host, port=port)
        print(f"Порт {port} готов к приёму подключений")
    except:
        print(f"Не удалось открыть порт {port}")
    return s


async def receive_data(reader):
    d = bytearray()
    while True:
        chunk = await reader.read(BUFFER_SIZE)
        d += chunk
        reader.feed_eof()
        if reader.at_eof():
            break
    return d.decode()


async def send_data(writer, data):
    try:
        writer.write(data.encode())
        await writer.drain()
        print(f"Ответ для {writer.get_extra_info('peername')} отправлен")
    except ConnectionError:
        print("Соединение с клиентом потеряно")


async def handle_code(reader, writer):
    client = writer.get_extra_info('peername')
    print(f"Клиент {client} присоединился к порту {PORT_1}")

    while True:
        flag_ok = False

        data = await receive_data(reader)
        print(f"Получены данные от  {client}")

        if data:
            if data not in CLIENTS:
                CLIENTS[data] = await generate_code()

                await send_data(writer, CLIENTS[data])
                flag_ok = True
            else:
                await send_data(writer, "")
        else:
            await send_data(writer, "Отправлены некорректные данные")

        if flag_ok:
            break

    writer.close()
    await writer.wait_closed()
    print(f"{client} отсоединён от порта {PORT_1}")


async def handle_message(reader, writer):
    client = writer.get_extra_info('peername')
    print(f"Клиент {client} присоединился к порту {PORT_2}")

    data = await receive_data(reader)
    print(f"Получены данные от  {client}")

    params = await extract_params(data)
    if params:
        message, uid, code = params

        if uid in CLIENTS:
            if code == CLIENTS[uid]:
                logging.info("%s", message)
                print(f"Сообщение от {client} добавлено в лог")
                await send_data(writer, "Сообщение добавлено в лог")
            else:
                await send_data(writer, "Неверный код (CODE)")
        else:
            await send_data(writer, "Пользователя с данным UID не существует. Если UID введён верно, то перезапустите клиент")
    else:
        await send_data(writer, 'Введённые данные не соответствуют требуемому формату: "Текст сообщения" UID CODE')

    writer.close()
    await writer.wait_closed()
    print(f"{client} отсоединён от порта {PORT_2}")


async def start():
    code_serv = await open_port(HOST, PORT_1, handle_code)
    message_serv = await open_port(HOST, PORT_2, handle_message)

    try:
        if code_serv and message_serv:
            async with code_serv, message_serv:
                await code_serv.serve_forever()
                await message_serv.serve_forever()
        else:
            print("Не удалось открыть один или более портов. Работа сервера будет прекращена")
            input("***Нажмите Enter***")
    finally:
        if code_serv:
            code_serv.close()
            await code_serv.wait_closed()
        if message_serv:
            message_serv.close()
            await message_serv.wait_closed()


def main():
    print("Для завершения работы нажмите Ctrl+C\n")
    try:
        asyncio.run(start())
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
