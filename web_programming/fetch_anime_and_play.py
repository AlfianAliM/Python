import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from fake_useragent import UserAgent
import os
import subprocess

BASE_URL = "https://ww1.gogoanime2.org"


def search_scraper(anime_name: str) -> list:
    """Search for anime by name and return a list of results."""
    search_url = f"{BASE_URL}/search/{anime_name}"
    response = requests.get(search_url, headers={"User-Agent": UserAgent().chrome}, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    anime_ul = soup.find("ul", {"class": "items"})
    
    if anime_ul is None or isinstance(anime_ul, NavigableString):
        raise ValueError(f"Could not find any anime with name {anime_name}")

    anime_list = []
    for anime in anime_ul.children:
        if isinstance(anime, Tag):
            anime_url = anime.find("a")
            anime_title = anime_url["title"]
            anime_list.append({"title": anime_title, "url": anime_url["href"]})

    return anime_list


def search_anime_episode_list(episode_endpoint: str) -> list:
    """Return a list of episodes for a given anime."""
    request_url = f"{BASE_URL}{episode_endpoint}"
    response = requests.get(url=request_url, headers={"User-Agent": UserAgent().chrome}, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    episode_page_ul = soup.find("ul", {"id": "episode_related"})
    
    if episode_page_ul is None or isinstance(episode_page_ul, NavigableString):
        raise ValueError(f"Could not find any anime episodes for {episode_endpoint}")

    episode_list = []
    for episode in episode_page_ul.children:
        if isinstance(episode, Tag):
            url = episode.find("a")
            title = episode.find("div", {"class": "name"})
            episode_list.append({"title": title.text.strip(), "url": url["href"]})

    return episode_list


def get_anime_episode(episode_endpoint: str) -> list:
    """Get the video URL and download URL from the episode URL."""
    episode_page_url = f"{BASE_URL}{episode_endpoint}"
    response = requests.get(url=episode_page_url, headers={"User-Agent": UserAgent().chrome}, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    url = soup.find("iframe", {"id": "playerframe"})
    
    if url is None or isinstance(url, NavigableString):
        raise RuntimeError(f"Could not find URL for {episode_endpoint}")

    episode_url = url["src"]
    download_url = episode_url.replace("/embed/", "/playlist/") + ".m3u8"

    return [f"{BASE_URL}{episode_url}", f"{BASE_URL}{download_url}"]


def download_video(m3u8_url: str, output_file: str):
    """Download video from the given m3u8 URL using ffmpeg."""
    command = [
        'ffmpeg',
        '-i', m3u8_url,
        '-c', 'copy',
        output_file
    ]
    subprocess.run(command)
    print(f"Downloaded video to {output_file}")


if __name__ == "__main__":
    anime_name = input("Enter anime name: ").strip()
    anime_list = search_scraper(anime_name)
    print("\n")

    if len(anime_list) == 0:
        print("No anime found with this name")
    else:
        print(f"Found {len(anime_list)} results: ")
        for i, anime in enumerate(anime_list):
            print(f"{i + 1}. {anime['title']}")

        anime_choice = int(input("\nPlease choose from the following list: ").strip())
        chosen_anime = anime_list[anime_choice - 1]
        print(f"You chose {chosen_anime['title']}. Searching for episodes...")

        episode_list = search_anime_episode_list(chosen_anime["url"])
        if len(episode_list) == 0:
            print("No episodes found for this anime")
        else:
            print(f"Found {len(episode_list)} results: ")
            for i, episode in enumerate(episode_list):
                print(f"{i + 1}. {episode['title']}")

            episode_choice = int(input("\nChoose an episode by serial number: ").strip())
            chosen_episode = episode_list[episode_choice - 1]
            print(f"You chose {chosen_episode['title']}. Searching...")

            episode_url, download_url = get_anime_episode(chosen_episode["url"])
            print(f"\nTo watch, ctrl+click on {episode_url}.")
            print(f"To download, ctrl+click on {download_url}.")

            # Download the video
            output_filename = f"{chosen_episode['title']}.mp4"
            download_video(download_url, output_filename)
