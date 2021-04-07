# instory-dl
A script for downloading your stories from instory.su in machine-readable format.

# Usage

```bash
Usage: main.py [OPTIONS] URL

Options:
  --pages-file TEXT
  --help             Show this message and exit.
```

First argument must be the address of the page to download the story from, e.g. `https://instory.su/story/12345/play`.

You may also specify a different output path. By default the story will be saved to `data/story.json`.

Example: `python main.py https://instory.su/story/12345/play --pages-file ~/my_story.json`
