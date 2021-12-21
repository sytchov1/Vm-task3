# Импорт модулей
import asyncio      # Для создания асинхронного сервера
import uuid         # Для генерации уникального кода
import logging      # Для ведения лога сообщений

# Константы
HOST = '127.0.0.1'  # Localhost
PORT_1 = 8000       # Порт для уникальных кодов
PORT_2 = 8001       # Порт для сообщений
BUFFER_SIZE = 64    # Объём данных, считываемых с порта за раз

logging.basicConfig(filename='server.log',
                    format='%(asctime)s | %(message)s',
                    datefmt='%d-%m-%y %H:%M:%S',
                    level=logging.INFO)     # Настройки лог-файла

clients = {}        # Информация о клиентах за текущую сессию


# Функция для генерации уникального кода на основе случайных значений
async def generate_code():
    return str(uuid.uuid4())


# Функция для распаковки параметров из принятой строки
async def extract_params(data):
    try:
        message, temp = data[1:].split('\" ')
        uid, code = temp.split()
        result = [message, uid, code]
    except:
        result = []
    return result


# Функция для установки порта в режим прослушивания
async def open_port(host, port, handler):
    s = None
    try:
        print(f"Открываем порт {port}...")
        s = await asyncio.start_server(client_connected_cb=handler, host=host, port=port)
        print(f"Порт {port} готов к приёму подключений")
    except:
        print(f"Не удалось открыть порт {port}")
    return s


# Функция для считывания данных от клиента
async def receive_data(reader):
    d = bytearray()
    while True:
        chunk = await reader.read(BUFFER_SIZE)  # Считываем часть данных
        d += chunk
        reader.feed_eof()
        if reader.at_eof():                     # Если данные еще остались, то считываем повторно
            break
    return d.decode()


# Функция для отправки данных клиенту
async def send_data(writer, data):
    try:
        writer.write(data.encode())
        await writer.drain()    # Очищаем буффер
        print(f"Ответ для {writer.get_extra_info('peername')} отправлен")
    except ConnectionError:
        print("Соединение с клиентом потеряно")


# Функция-обработчик, принимающая уникальный идентификатор и возвращающая уникальный код
async def handle_code(reader, writer):
    client = writer.get_extra_info('peername')
    print(f"Клиент {client} присоединился к порту {PORT_1}")

    while True:
        flag_ok = False     # Флаг для проверки уникальности идентификатора

        data = await receive_data(reader)       # Считываем идентификатор клиента
        print(f"Получены данные от  {client}")

        if data:
            if data not in clients:                     # Если клиента с таким uid еще не было в текущей сессии,
                clients[data] = await generate_code()   # то генерируем код и сохраняем для текущей сессии

                await send_data(writer, clients[data])  # Отправляем код клиенту
                flag_ok = True
            else:
                await send_data(writer, "")   # Если полученный id не уникальный, то просим клиента прислать новый
        else:
            await send_data(writer, "Отправлены некорректные данные")

        if flag_ok:
            break

    writer.close()      # Закрываем соединение с данным клиентом
    await writer.wait_closed()
    print(f"{client} отсоединён от порта {PORT_1}")


# Функция-обработчик, принимающая сообщение и возвращающая ответ клиенту
async def handle_message(reader, writer):
    client = writer.get_extra_info('peername')
    print(f"Клиент {client} присоединился к порту {PORT_2}")

    data = await receive_data(reader)       # Считываем данные от клиента
    print(f"Получены данные от  {client}")

    params = await extract_params(data)     # Распаковываем данные
    if params:
        message, uid, code = params

        if uid in clients:                                              # Если информация о клиенте имеется
            if code == clients[uid]:                                    # и получен верный код,
                logging.info("%s", message)                             # то записываем сообщение в лог-файл
                print(f"Сообщение от {client} добавлено в лог")
                await send_data(writer, "Сообщение добавлено в лог")    # и отправляем ответ клиенту
            else:
                await send_data(writer, "Неверный код (CODE)")
        else:
            await send_data(writer, "Пользователя с данным UID не существует. Если UID введён верно, то перезапустите клиент")
    else:
        await send_data(writer, 'Введённые данные не соответствуют требуемому формату: "Текст сообщения" UID CODE')

    writer.close()      # Закрываем соединение с данным клиентом
    await writer.wait_closed()
    print(f"{client} отсоединён от порта {PORT_2}")


# Функция, реализующая main_loop
async def start():
    code_serv = await open_port(HOST, PORT_1, handle_code)          # Открываем порт 8000
    message_serv = await open_port(HOST, PORT_2, handle_message)    # Открываем порт 8001

    try:
        if code_serv and message_serv:                              # Если порты открыты успешно
            async with code_serv, message_serv:
                await code_serv.serve_forever()                     # Бесконечно прослушиваем 8000
                await message_serv.serve_forever()                  # Бесконечно прослушиваем 8001
        else:
            print("Не удалось открыть один или более портов. Работа сервера будет прекращена")
            input("***Нажмите Enter***")
    finally:
        if code_serv:
            code_serv.close()                                       # Закрываем порт 8000
            await code_serv.wait_closed()
        if message_serv:
            message_serv.close()                                    # Закрываем порт 8001
            await message_serv.wait_closed()


def main():
    print("Для завершения работы нажмите Ctrl+C\n")
    try:
        asyncio.run(start())    # Запускаем основной цикл событий
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
