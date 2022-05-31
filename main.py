from dotenv import load_dotenv
from os import environ
from bs4 import BeautifulSoup
from requests import get, request
from printer import *
import redis
from pyfiglet import Figlet
import chalk
import json
from datetime import datetime
from urllib.parse import urlparse
import threading
from dataclasses import dataclass


@dataclass
class ScanResults:
    url: str
    links_found: list
    title: str
    description: str
    timestamp: str
    keywords: list


load_dotenv()
R = redis.Redis(host=environ["REDIS_HOST"], port=6379, password=environ["REDIS_PASS"])
STARTING_URL = "https://bths.edu/index.jsp"
USER_AGENT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
IP = get("https://checkip.amazonaws.com").text.replace("\n", "")
connectedToNord = get(
    "https://nordvpn.com/wp-admin/admin-ajax.php?action=get_user_info_data"
).json()["status"]

print(chalk.red(Figlet(font="slant").renderText("HAWKEYE")))
print(chalk.yellow(f"BY ") + "ISMAEEL AKRAM")
print(chalk.yellow(f"STARTING URL: ") + STARTING_URL)
print(chalk.yellow(f"USER AGENT: ") + USER_AGENT)
print(chalk.yellow(f"REDIS CONNECTED: ") + str(R.ping()))
print(chalk.yellow(f"IP ADDRESS: ") + IP)
print(chalk.yellow(f"CONNECTED TO NORDVPN: ") + str(connectedToNord))

if not connectedToNord:
    danger("You are not connected to NordVPN. Are you sure you want to proceed? (Y/N)")
    choice = input("> ").strip()
    if "n" in choice.lower():
        exit()


def scan(url: str):
    info(f"Starting to scan '{url}'")
    parsed_url = urlparse(url)

    R.srem("hawkeye:queue", url)
    R.sadd("hawkeye:visited", url)
    R.sadd("hawkeye:domains_visited", parsed_url.hostname)
    R.incr("hawkeye:count", 1)

    response = get(url, headers={"User-Agent": USER_AGENT})
    soup = BeautifulSoup(response.text, "html.parser")
    links_found = []
    for link in soup.find_all("a"):
        href = link.get("href")
        if not href:
            continue
        final_link = href
        if not href.startswith("http"):
            final_link = url + href
            continue
        links_found.append(final_link)
        if not R.sismember("hawkeye:pages_visited", final_link):
            R.sadd("hawkeye:queue", final_link)
            # info(f"Added '{final_link}' to the queue")

    try:
        title = soup.title.string
    except:
        title = "No title found"
    try:
        description = soup.find("meta", {"name": "description"}).get("content")
    except AttributeError:
        description = "No description"
    try:
        keywords = soup.find("meta", {"name": "keywords"}).get("content").split(",")
    except AttributeError:
        keywords = ["No keywords"]

    results = ScanResults(
        url=url,
        links_found=links_found,
        title=title,
        description=description,
        keywords=keywords,
        timestamp=datetime.now().isoformat(),
    )
    json_results = json.dumps(results.__dict__)

    R.lpush("hawkeye:results", json_results)
    good(f"Successfully scanned '{url}'")


R.sadd("hawkeye:queue", STARTING_URL)
while True:
    url = R.spop("hawkeye:queue")
    if url:
        scan_thread = threading.Thread(target=scan, args=(url.decode("utf-8"),))
        scan_thread.setDaemon(True)
        scan_thread.start()
    # else:
    # info("Queue is empty")
