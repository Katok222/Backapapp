import requests
import json
import logging
from tqdm import tqdm
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Входные данные
vk_user_id = "432290989"  # Убрали префикс 'id'
vk_token = (
    "vk1.a.K9rK0w7EwhNp93xFFENZq5HCsjEVwsa4-IXJINyw7_qFbE_Kc6qCtbfrL2dLSihpu-OlUdAqbc1fNVlT05urt57cTXYham0kwtLZQSwEUZAfIJk5t0ZwcmIS_cpF7c92sntzB6H30hCg1WedHVJbZQLatpOaOqV_HV2dEFbcQmPfMU4Do2xJafI8VLJU3ti-"
)
yandex_token = "y0_AgAAAAAkqe9gAADLWwAAAAEaqiOFAAA1by7JTwNDupVd5_RnRjGJ_FQnPg"

# URL для запросов
vk_api_url = "https://api.vk.com/method/photos.get"
yandex_api_url = "https://cloud-api.yandex.net/v1/disk/resources/upload"

# Параметры запроса к VK API
vk_params = {
    "owner_id": vk_user_id,
    "album_id": "profile",
    "extended": 1,
    "photo_sizes": 1,
    "access_token": vk_token,
    "v": "5.131"
}

# Получение фотографий с профиля VK
response = requests.get(vk_api_url, params=vk_params)
photos = response.json().get("response", {}).get("items", [])

# Проверка ответа от VK API
if not photos:
    logging.error("Ошибка при получении фотографий с VK. Проверьте токен и ID пользователя.")
    logging.error(response.json())
    exit(1)

# Словарь для хранения информации о фотографиях
photo_info = []

# Создание папки на Яндекс.Диске
folder_name = "VK_Photos"
requests.put(
    f"https://cloud-api.yandex.net/v1/disk/resources?path={folder_name}",
    headers={"Authorization": f"OAuth {yandex_token}"}
)

# Словарь для отслеживания количества лайков
likes_count = {}

# Количество фотографий для сохранения (по умолчанию 3)
num_photos_to_save = 3

# Загрузка фотографий на Яндекс.Диск
for photo in tqdm(photos, desc="Загрузка фотографий"):
    if len(photo_info) >= num_photos_to_save:
        break

    # Получение максимального размера фотографии
    max_size_photo = max(photo["sizes"], key=lambda x: x["width"] * x["height"])
    photo_url = max_size_photo["url"]
    likes = photo["likes"]["count"]
    date = datetime.fromtimestamp(photo["date"]).strftime("%Y-%m-%d")

    # Формирование имени файла
    file_name = f"{likes}.jpg"
    if file_name in [info["file_name"] for info in photo_info]:
        if likes in likes_count:
            likes_count[likes] += 1
        else:
            likes_count[likes] = 1
        file_name = f"{likes}_{date}_{likes_count[likes]}.jpg"

    # Загрузка фотографии на Яндекс.Диск
    upload_url = f"{yandex_api_url}?path={folder_name}/{file_name}&overwrite=true"
    headers = {"Authorization": f"OAuth {yandex_token}"}
    upload_response = requests.get(upload_url, headers=headers)
    upload_link = upload_response.json().get("href")

    # Проверка ответа от Яндекс.Диска
    if not upload_link:
        logging.error(f"Ошибка при получении ссылки для загрузки фотографии {file_name}.")
        logging.error(upload_response.json())
        continue

    photo_data = requests.get(photo_url).content
    upload_result = requests.put(upload_link, data=photo_data)

    # Проверка результата загрузки
    if upload_result.status_code != 201:
        logging.error(f"Ошибка при загрузке фотографии {file_name}.")
        logging.error(upload_result.json())
        continue

    # Сохранение информации о фотографии
    photo_info.append({
        "file_name": file_name,
        "size": max_size_photo["type"]
    })

# Проверка количества загруженных фотографий
if len(photo_info) < num_photos_to_save:
    logging.warning(f"Загружено меньше фотографий, чем ожидалось: {len(photo_info)} из {num_photos_to_save}.")

# Сохранение информации о фотографиях в JSON-файл
with open("photo_info.json", "w") as json_file:
    json.dump(photo_info, json_file, indent=4)

logging.info("Фотографии успешно загружены на Яндекс.Диск и информация сохранена в photo_info.json")

