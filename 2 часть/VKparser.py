import os
import requests
import datetime
import json


ACCESS_TOKEN = os.environ["VK_TOKEN"]
VERSION = '5.131'
OWNER_ID = -48632629
POST_ID = 12829
OUTPUT_FILE = 'stats.json'

def get_likes(owner_id, item_id, token):
    user_ids = []
    offset = 0

    while True:
        params = {
            "type": "post",
            "owner_id": owner_id,
            "item_id": item_id,
            "access_token": token,
            "v": VERSION,
            "count": 1000,
            "offset": offset,
        }
        response = requests.get("https://api.vk.com/method/likes.getList", params=params).json()

        if 'error' in response:
            print(f"Ошибка: {response['error']['error_msg']}")
            break

        items = response['response']['items']
        if not items:
            break

        user_ids.extend(items)
        offset += 1000

    return user_ids


def get_users_data(user_ids, token):
    users_data = []
    chunk_size = 1000

    for i in range(0, len(user_ids), 1000):
        chunk = user_ids[i:i + 1000]
        ids_str = ",".join(map(str, chunk))

        params = {
            "user_ids": ids_str,
            "fields": "sex,bdate",
            "access_token": token,
            "v": VERSION
        }

        response = requests.get("https://api.vk.com/method/users.get", params=params).json()
        if 'response' in response:
            users_data.extend(response['response'])

    return users_data


def get_age(bdate):
    if not bdate or len(bdate.split('.')) != 3:
        return None

    day, month, year = map(int, bdate.split('.'))
    birth = datetime.date(year, month, day)
    today = datetime.date.today()

    return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

def build_stats(users, post_id):
    stats = {
        "post_id": post_id,
        "age": {"0-18": 0, "19-35": 0, "36-50": 0, ">50": 0, "unknown": 0},
        "sex": {"male": 0, "female": 0, "unknown": 0}
    }
    for user in users:
        sex = user.get('sex', 0)
        if sex == 1:
            stats['sex']['female'] += 1
        elif sex == 2:
            stats['sex']['male'] += 1
        else:
            stats['sex']['unknown'] += 1

        
        age = get_age(user.get('bdate'))
        if age is None:
            stats['age']['unknown'] += 1
        elif age <= 18:
            stats['age']['0-18'] += 1
        elif age <= 35:
            stats['age']['19-35'] += 1
        elif age <= 50:
            stats['age']['36-50'] += 1
        else:
            stats['age']['>50'] += 1

    return stats

def save_to_file(data, filename):
    os.makedirs('data', exist_ok=True)
    filepath = os.path.join('data', filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"Результат сохранен в: {filepath}")


if __name__ == "__main__":
    print(f"Анализ лайков поста {POST_ID}...\n")

    print("Сбор ID пользователей...")
    liked_ids = get_likes(OWNER_ID, POST_ID, ACCESS_TOKEN)
    print(f" Найдено лайков: {len(liked_ids)}\n")

    if liked_ids:

        print("Загрузка профилей пользователей...")
        users_info = get_users_data(liked_ids, ACCESS_TOKEN)
        print(f"Данные получены\n")


        print("Обработка статистики...")
        result_stats = build_stats(users_info, POST_ID)
        print(f"Статистика готова\n")


        print("РЕЗУЛЬТАТЫ:")
        print(json.dumps(result_stats, indent=4, ensure_ascii=False))


        save_to_file(result_stats, OUTPUT_FILE)
    else:

        print("Лайков не найдено или ошибка доступа.")
