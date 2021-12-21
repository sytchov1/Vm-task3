# Импорт модулей
import asyncio      # Для создания асинхронного сервера
import uuid         # Для генерации уникального кода


# Константы
HOST = '127.0.0.1'  # Localhost
PORT_1 = 8000       # Порт для уникальных кодов
PORT_2 = 8001       # Порт для сообщений
BUFFER_SIZE = 64    # Объём данных, считываемых с порта за раз


# Функция, генерирующая уникальный идентификатор на основе MAC-адреса и текущего времени
async def generate_uid():
    return str(uuid.uuid1())


# Функция, устанавливающая подключение к порту
async def connect(host, port):
    print('Подключаемся к серверу... (Убедитесь, что сервер включен)')
    while True:
        try:
            r, w = await asyncio.open_connection(host, port)
            break
        except ConnectionError:
            pass
    return r, w


# Функция для отправки данных на сервер
async def send_data(writer, data):
    print('Отправляем запрос на сервер...')
    try:
        writer.write(data.encode())
    except ConnectionError:
        print("Соединение с сервером потеряно")


# Функция для считывания данных от сервера
async def receive_data(reader):
    print("Ждём ответ...")
    d = bytearray()
    while True:
        chunk = await reader.read(BUFFER_SIZE)  # Считываем часть данных
        d += chunk
        reader.feed_eof()
        if reader.at_eof():                     # Если данные еще остались, то считываем повторно
            break
    return d.decode()


# Функция, реализующая отправку идентификатора на сервер и получение кода
async def get_code():
    reader, writer = await connect(HOST, PORT_1)                        # Подключаемся к порту 8000
    try:
        while True:                                                     # Пока не получим код...
            print("Генерируем уникальный идентификатор...")
            uid = await generate_uid()                                  # Генерируем идентификатор

            await send_data(writer, uid)                                # Отправляем данные на сервер

            response = await receive_data(reader)                       # Принимаем ответ от сервера

            if response:                                                # Если код получен,
                print(f"Ваш уникальный идентификатор (UID): {uid}")     # то выводим код и идентификатор
                print(f'Ваш код (CODE): {response}')
                break
    finally:
        writer.close()                                                  # Отключаемся от сервера
        await writer.wait_closed()
        print("Соединение закрыто\n")


# Функция, реализующая отправку сообщения на сервер и получение ответа
async def send_message(params):
    reader, writer = await connect(HOST, PORT_2)                        # Подключаемся к порту 8001
    try:
        await send_data(writer, params)                                 # Отправляем данные на сервер

        response = await receive_data(reader)                           # Получаем ответ от сервера
        print(f'<-- {response}')
    finally:
        writer.close()                                                  # Отключаемся от сервера
        await writer.wait_closed()
        print("Соединение закрыто\n")


# Основной цикл клиентского приложения
def main():
    try:
        asyncio.run(get_code())                     # Получаем код от сервера

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
                asyncio.run(send_message(temp))     # Отправляем сообщение на сервер
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
