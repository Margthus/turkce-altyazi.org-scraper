import os


def ensure_dir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def print_results(results):
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title']} - {result['url']}")


def print_subtitles(subtitles):
    for i, sub in enumerate(subtitles, 1):
        se = ""
        if sub.get("season") is not None and sub.get("episode") is not None:
            se = f" S{sub['season']:02d}E{sub['episode']:02d}"
        release = sub.get("release", "-")
        print(
            f"{i}. [{sub.get('language', 'Unknown')}] {sub['season_ep']}{se} - "
            f"{sub['translator']} - FPS: {sub['fps']} - Release: {release} "
            f"- Indirmeler: {sub['downloads']}"
        )
