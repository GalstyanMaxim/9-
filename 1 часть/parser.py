import os
import csv
import time
from datetime import datetime, timedelta
import requests
from tabulate import tabulate
import argparse
from bs4 import BeautifulSoup

AFISHA_URL = "https://www.afisha.ru/novorossijsk/cinema/"



def validate_date(date_str: str) -> str:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Неверный формат даты: {date_str}. Используйте YYYY-MM-DD."
        )


def fetch_afisha_page() -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get(AFISHA_URL, headers=headers, timeout=10)
        if resp.status_code != 200:
            print(f"[ОШИБКА] HTTP {resp.status_code}")
            return None
        return resp.text
    except requests.ConnectionError as e:
        print(f"[ОШИБКА] Ошибка подключения: {e}")
        return None
    except requests.Timeout as e:
        print(f"[ОШИБКА] Timeout: {e}")
        return None
    time.sleep(3)
    return resp.text


def parse_cinema_afisha(html_content: str):
    soup = BeautifulSoup(html_content, "html.parser")
    movies = []
    movie_containers = soup.find_all("div", attrs={"role": "listitem", "data-test": "ITEM"})

    print(f"[DEBUG] Найдено контейнеров фильмов: {len(movie_containers)}")

    for container in movie_containers:
        try:
            genre_div = container.find("div", class_="TmmXT")
            genre = genre_div.get_text(strip=True) if genre_div else "N/A"

            title_div = container.find("div", class_="VeVyd")
            title = title_div.get_text(strip=True) if title_div else "N/A"

            description_div = container.find("div", class_="gVGDC")
            description = description_div.get_text(strip=True) if description_div else "N/A"

            rating_div = container.find("div", attrs={"data-test": "RATING"})
            rating = rating_div.get_text(strip=True) if rating_div else "N/A"

            if title == "N/A" or len(title) < 2:
                print(f"[DEBUG] Пропущен фильм без названия")
                continue

            movies.append(
                {
                    "genre": genre,
                    "title": title,
                    "description": description,
                    "rating": rating,
                }
            )

            print(f"[DEBUG] Фильм: {title[:40]} | Жанр: {genre} | Рейтинг: {rating}")

        except Exception as e:
            print(f"[DEBUG] Ошибка парсинга блока: {e}")
            continue

    return movies


def main():
    parser = argparse.ArgumentParser(
        description="Парсер афиши кино Новороссийска с afisha.ru"
    )
    parser.add_argument(
        "--date1",
        type=validate_date,
        default=None,
        help="Дата начала (YYYY-MM-DD), опционально",
    )
    parser.add_argument(
        "--date2",
        type=validate_date,
        default=None,
        help="Дата окончания (YYYY-MM-DD), опционально",
    )
    args = parser.parse_args()

    if args.date1 is None or args.date2 is None:
        today = datetime.now()
        date1 = (today - timedelta(days=30)).strftime("%Y-%m-%d")
        date2 = today.strftime("%Y-%m-%d")
        print("Даты не указаны. Используются значения по умолчанию:")
        print(f"  --date1 {date1}")
        print(f"  --date2 {date2}\n")
    else:
        date1 = args.date1
        date2 = args.date2

        if datetime.strptime(date1, "%Y-%m-%d") > datetime.strptime(
                date2, "%Y-%m-%d"
        ):
            raise ValueError("Ошибка: дата начала периода позже даты окончания.")

    try:
        print("Загружаю афишу...")
        html_content = fetch_afisha_page()
    except Exception as e:
        print(f"Ошибка загрузки афиши: {e}")
        return

    print("Парсинг фильмов...\n")
    movies = parse_cinema_afisha(html_content)

    if not movies:
        print("На афише не найдено ни одного фильма.")
        return

    print(f"\nНайдено фильмов: {len(movies)}\n")

    table_data = [
        [
            idx + 1,
            m["genre"],
            m["title"][:30],
            m["description"][:35] + "...",
            m["rating"],
        ]
        for idx, m in enumerate(movies)
    ]
    print(
        tabulate(
            table_data,
            headers=["#", "Жанр", "Название", "Описание", "Рейтинг"],
            tablefmt="github",
        )
    )

    os.makedirs("data", exist_ok=True)
    csv_name = f"afisha_cinema_{date1}_to_{date2}.csv"
    csv_path = os.path.join("data", csv_name)

    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["genre", "title", "description", "rating"])
        for m in movies:
            writer.writerow(
                [m["genre"], m["title"], m["description"], m["rating"]]
            )

    print(f"\nДанные сохранены в {csv_path}")


if __name__ == "__main__":
    main()
