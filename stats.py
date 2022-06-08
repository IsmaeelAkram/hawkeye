import chalk

print(chalk.blue("Importing data libraries..."))

import redis
from dotenv import load_dotenv
from os import environ
from pyfiglet import Figlet
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from urllib.parse import urlparse
import json
import squarify
import seaborn as sns
import random

load_dotenv()
R = redis.Redis(host=environ["REDIS_HOST"], port=6379, password=environ["REDIS_PASS"])

print(chalk.red(Figlet(font="slant").renderText("HAWKEYE STATS")))

print(chalk.blue("Getting data from Redis..."))
count = int(R.get("hawkeye:count").decode("utf-8"))
queue_len = R.scard("hawkeye:queue")
visited_len = R.scard("hawkeye:visited")
results_len = R.llen("hawkeye:results")
domains_visited = R.scard("hawkeye:domains_visited")


def domain_treemap():
    # Generate treemap from all results based on domain
    df = pd.DataFrame(columns=["domain", "count"])
    for result in results:
        result = json.loads(result.decode("utf-8"))
        domain = urlparse(result["url"]).hostname
        try:
            df.at[domain, "count"] += 1
        except KeyError:
            df.at[domain, "count"] = 1
            df.at[domain, "domain"] = domain

    sns.set_style(style="whitegrid")
    sizes = df["count"].values
    label = df["domain"].values
    fig, ax = plt.subplots(figsize=(20, 20))
    colors = [(random.random(), random.random(), random.random()) for i in range(200)]
    squarify.plot(
        sizes=sizes, label=label, alpha=0.8, color=colors, linewidth=0.5, ax=ax
    )
    ax.axis("off")
    plt.savefig("charts/domains_treemap.png")


def keyword_treemap():
    # Generate treemap from all results based on keywords
    df = pd.DataFrame(columns=["keyword", "count"])
    for result in results:
        result = json.loads(result.decode("utf-8"))
        keywords = result["keywords"]
        for keyword in keywords:
            if "No keywords" in keyword:
                continue
            try:
                df.at[keyword, "count"] += 1
            except KeyError:
                df.at[keyword, "count"] = 1
                df.at[keyword, "keyword"] = keyword

    sns.set_style(style="whitegrid")
    sizes = df["count"].values
    label = df["keyword"].values
    fig, ax = plt.subplots(figsize=(20, 20))
    colors = [(random.random(), random.random(), random.random()) for i in range(200)]
    squarify.plot(
        sizes=sizes, label=label, alpha=0.8, color=colors, linewidth=0.5, ax=ax
    )
    ax.axis("off")
    print(chalk.yellow("UNIQUE KEYWORDS: ") + str(df.__len__()))
    plt.savefig("charts/keywords_treemap.png")


print(chalk.yellow(f"PAGES IN QUEUE: ") + "{:,}".format(queue_len))
print(chalk.yellow(f"PAGES SCANNED (COUNT): ") + "{:,}".format(count))
print(chalk.yellow(f"UNIQUE PAGES VISITED: ") + "{:,}".format(visited_len))
print(chalk.yellow(f"UNIQUE DOMAINS VISITED: ") + "{:,}".format(domains_visited))
print(chalk.yellow(f"# OF RESULTS: ") + "{:,}".format(results_len))
print()
print(
    "There are {:,} results to process, would you like to continue?".format(
        results_len
    ),
    end="",
)
input()
print(chalk.blue("Retrieving result data from Redis..."))
results = R.lrange("hawkeye:results", 0, -1)
print("Attempting to generate a domain treemap...")
domain_treemap()
print("Attempting to generate a keyword treemap...")
keyword_treemap()