import json
import requests

url_user = 'http://130.193.43.122:8081'
url_party = 'http://130.193.43.122:8080'


def handler(event, context):
    # try:
    body = json.loads(event['body'])

    print(body)

    if ('message' not in body) or ('text' not in body['message']) or ('reply_to_message' in body['message']):
        return {
            'statusCode': 200
        }
    if 'edited_message' in body:
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'method': 'sendMessage',
                'chat_id': body['edited_message']['chat']['id'],
                'text': 'Отредачил - молодец'
            }),
            'isBase64Encoded': False
        }

    # response_data = body
    response_data = ''

    if str.startswith(body['message']['text'], '/start'):
        response_data = c_start(body)

    if str.startswith(body['message']['text'], '/hello'):
        response_data = c_hello(body)

    if str.startswith(body['message']['text'], '/add'):
        response_data = c_add(body)

    if str.startswith(body['message']['text'], '/status'):
        response_data = c_status(body)

    if str.startswith(body['message']['text'], '/delete'):
        response_data = c_delete(body)

    if str.startswith(body['message']['text'], '/done'):
        response_data = c_done(body)

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'method': 'sendMessage',
            'chat_id': body['message']['chat']['id'],
            'text': response_data
        }),
        'isBase64Encoded': False
    }


# except:
#     return {
#         'statusCode': 200,
#         'headers': {
#             'Content-Type': 'application/json'
#         },
#         'body': json.dumps({
#             'method': 'sendMessage',
#             'chat_id': body['message']['chat']['id'],
#             'text': 'Ошибка обработки запроса'
#         }),
#         'isBase64Encoded': False
#     }


# старт
def c_start(body):
    # check if user exists
    headers = {
        'Content-Type': 'application/json'
    }
    response_user = requests.get(url_user + '/users/tg/' + str(body['message']['from']['id']), headers=headers)
    if (response_user.status_code != 200):
        # create user if not exist
        bodyReq = json.loads("   {\n        \"name\": \""
                             + str(body['message']['from']['first_name']) + " "
                             + str(body['message']['from']['last_name']) + "\",\n        \"telegram_id\": \""
                             + str(body['message']['from']['id']) + "\"\n    }")
        headers = {
            'Content-Type': 'application/json'
        }
        response_user = requests.post(url_user + '/users', headers=headers, json=bodyReq)

    response_user_json = json.loads(response_user.text)
    # create a new party or get existing
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    bodyReq = json.loads("{  \"userId\": \""
                         + str(response_user_json['user_id']) + "\",  \"name\": \""
                         + str(body['message']['chat']['title']) + "\",  \"chatId\": \""
                         + str(body['message']['chat']['id']) + "\"}")

    response_party = requests.post(url_party + '/party_tg', headers=headers, json=bodyReq)
    response_party_json = json.loads(response_party.text)

    # add user to party members
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    bodyReq = str(response_user_json['user_id'])
    response_party_member = requests.put(url_party + '/party/' + str(response_party_json['partyId']) + '/member',
                                         headers=headers, data=bodyReq)

    response_data = """Привет, я бот Party part! Я помогаю оптимально распределить расходы между учатстниками вечеринки!
    Добавь меня в групповой чат и пусть все участники вызовут /hello
    Чтобы добавить расход, используй команду /add <название расхода> <стоимость> <распределение стоимости по порядку участников>
    После того, как все расходы добавлены, введи /done"""  # + response_party.text

    return response_data


# добавление участника для бота
def c_hello(body):
    # check if user exists
    headers = {
        'Content-Type': 'application/json'
    }
    response_user = requests.get(url_user + '/users/tg/' + str(body['message']['from']['id']), headers=headers)
    if (response_user.status_code != 200):
        # create user if not exist
        bodyReq = json.loads("   {\n        \"name\": \""
                             + str(body['message']['from']['first_name']) + " "
                             + str(body['message']['from']['last_name']) + "\",\n        \"telegram_id\": \""
                             + str(body['message']['from']['id']) + "\"\n    }")
        headers = {
            'Content-Type': 'application/json'
        }
        response_user = requests.post(url_user + '/users', headers=headers, json=bodyReq)
    # get party
    response_party_json = response_party_json = get_party(body)
    response_user_json = json.loads(response_user.text)
    # add user to party members
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    bodyReq = str(response_user_json['user_id'])
    response_party_member = requests.put(url_party + '/party/' + str(response_party_json['partyId']) + '/member',
                                         headers=headers, data=bodyReq)

    user_name = body['message']['from']['first_name']
    response_data = 'Привет, ' + user_name + '! Теперь ты участник! '  # + response_user.text
    return response_data


# проверка текущего состояние пати
def c_status(body):
    # get party
    response_party_json = get_party(body)

    # get users of a party
    response_members_json = get_party_members(body)
    # get entries
    response_entries = get_entries(body)
    response_entries_json = json.loads(response_entries.text)

    # response_data = 'Статус пати: \n' + response_party.text + '\n' + response_members.text + '\n'+ response_entries.text
    response_data = 'Название: ' + response_party_json['name'] + '\n'
    response_data += 'Участники: \n'
    for user in response_members_json:
        response_data += ' - ' + user['name'] + '\n'
    response_data += 'Расходы: \n'

    if (response_entries.status_code != 200):
        response_data += 'Пока нет \n'
    else:
        print(response_entries_json)
        print(str(response_entries_json.sort))
        lines = sorted(response_entries_json, key=lambda k: int(k['entryId']))
        print(lines)
        i = 1
        for entry in lines:
            print(entry)
            user_who_paid = get_user_by__internal_id(entry['userWhoPaidId'])
            response_data += str(i) + ': ' + entry['name'] + ' - ' + entry['cost'] + '\n'
            response_data += ' - Заплатил: ' + user_who_paid['name'] + '\n'
            response_data += ' - Распределение:\n'
            for split in entry['split']:
                user_split = get_user_by__internal_id(split['userId'])
                response_data += '    • ' + user_split['name'] + ': ' + str(split['proportion']) + '\n'
            i += 1

    return response_data


# добавление расхода <название> <стоимость>
def c_add(body):
    response_members_json = get_party_members(body)
    message_input = body['message']['text'].split()
    message_length_full = 3 + len(response_members_json)
    is_digits = True
    for i in range(2, len(message_input)):
        print(message_input[i])
        # if (re.match(r'^-?\d+(?:\.\d+)?$', message_input[i]) is None):
        if (not message_input[i].isnumeric()):
            is_digits = False
        print(is_digits)
    print(len(message_input))
    print(message_length_full)

    if (not (len(message_input) == message_length_full or len(message_input) == 3) or not is_digits):
        response_data = 'Расход введен неправильно, попробуй снова. Распределение расхода должно быть равно количеству ' \
                        'участников. Чтобы посмотреть статус, введи /status'
    else:
        add_party_entry_response = add_party_entry(body)
        if (add_party_entry_response.status_code == 400):
            return 'Сумма расхода и сумма распределний не совпадает'
        if (add_party_entry_response.status_code != 200):
            return 'Ошибка сервера, повторите позже'
        else:
            response_data = 'Добавлен расход с названием ' + message_input[1] + ' и стоимостью ' + message_input[
                2] + '\n'
            # response_data += 'Распределение: \n'
            # i = 3
            # for user in response_members_json:
            #     response_data += user['name'] + ': ' + message_input[i] + '\n'
            #     i += 1
    return response_data

# удаление расхода <номер>
def c_delete(body):
    message_input = body['message']['text'].split()
    message_length = 2

    response_entries = get_entries(body)
    response_entries_json = json.loads(response_entries.text)

    if (len(message_input) != message_length or
            not message_input[1].isnumeric() or
            int(message_input[1]) < 1 or
            int(message_input[1]) > len(response_entries_json)):
        return 'Неправильно введен номер расхода'
    print(response_entries_json)
    lines = sorted(response_entries_json, key=lambda k: int(k['entryId']))
    entry_to_delete = lines[int(message_input[1]) - 1]
    print(entry_to_delete)
    print(entry_to_delete['entryId'])
    if (delete_entry(body, entry_to_delete['entryId']).status_code != 200):
        return 'Ошибка, проверьте номер или попробуйте позже'
    return "Удалено успешно"


# завершение добавление расхода
def c_done(body):
    response_calculate = get_calculate(body)
    response_calculate_json = json.loads(response_calculate.text)
    response_data = 'Распределение: \n'

    if (response_calculate.status_code != 200):
        response_data += 'Пока нет \n'
    else:
        if (len(response_calculate_json) == 0):
            response_data += "Все вышли в 0! Никто ничего не должен!"
        else:
            i = 1
            for entry in response_calculate_json:
                user_sender = get_user_by__internal_id(entry['userSenderId'])
                user_receiver = get_user_by__internal_id(entry['userReceiverId'])
                response_data += str(i) + ': \n - От: ' + str(user_sender['name']) + '\n - Кому: ' + str(
                    user_receiver['name']) + '\n'
                response_data += ' - Сколько: ' + entry['cost'] + '\n'
                i += 1
    return response_data


def get_party(body):
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    response_party = requests.get(url_party + '/party_tg/' + str(body['message']['chat']['id']), headers=headers)
    return json.loads(response_party.text)


def get_party_members(body):
    response_party_json = get_party(body)
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    response_members = requests.get(url_party + '/party/' + str(response_party_json['partyId']) + '/member',
                                    headers=headers)
    return json.loads(response_members.text)


def get_user(body):
    headers = {
        'Content-Type': 'application/json'
    }
    response_user = requests.get(url_user + '/users/tg/' + str(body['message']['from']['id']), headers=headers)
    return json.loads(response_user.text)


def get_user_by__internal_id(id):
    headers = {
        'Content-Type': 'application/json'
    }
    response_user = requests.get(url_user + '/users/id/' + str(id), headers=headers)
    return json.loads(response_user.text)


def add_party_entry(body):
    # curl - X
    # POST
    # "http://localhost:8080/party/111/enrty" - d
    # "{  \"userCreatorId\": \"string\",  \"userWhoPaidId\": \"string\",  \"name\": \"string\",  \"cost\": \"string\",  \"currency\": \"string\",  \"split\": \"string\"}"

    # create request for adding entry
    response_party_json = get_party(body)
    response_members_json = get_party_members(body)
    response_user = get_user(body)
    message_input = body['message']['text'].split()
    split = ""

    if (len(message_input) != 3):
        i = 3
        for user in response_members_json:
            split += "(" + str(user['userId']) + ',' + str(message_input[i]) + ');'
            i += 1
        split = split[:-1]

    data = "{  \"userCreatorId\": \"" + str(response_user['user_id']) + "\",  \"userWhoPaidId\": \"" + str(
        response_user['user_id']) \
           + "\",  \"name\": \"" + str(message_input[1]) + "\",  \"cost\": \"" + str(message_input[2]) \
           + "\",  \"currency\": \"rub\",  \"split\": \"" + split + "\"}"
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}

    print(data)

    return requests.post(url_party + '/party/' + str(response_party_json['partyId']) + '/entry', headers=headers,
                         data=data.encode(encoding='utf-8'))


def get_calculate(body):
    response_party_json = get_party(body)
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    response = requests.get(url_party + '/party/' + str(response_party_json['partyId']) + '/calculate', headers=headers)
    return response


def delete_entry(body, entry_id):
    response_party_json = get_party(body)
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    response = requests.delete(url_party + '/party/' + str(response_party_json['partyId']) + '/entry/' + str(entry_id),
                               headers=headers)
    return response


def get_entries(body):
    response_party_json = get_party(body)
    headers = {'accept': 'application/json', 'Content-Type': 'application/json'}
    response_entries = requests.get(url_party + '/party/' + str(response_party_json['partyId']) + '/entry',
                                    headers=headers)
    return response_entries
