# street_beat_parser
Web parser for street-beat.ru (selenium+bs4)

## Installation
```bash
pip install -r requirments.txt
```


## Usage
To scrape all products:
```bash
python3 sb_parser.py
```

To scrape content based on keyword:
```bash
python3 sb_parser.py converse кеды
```
## To be fixed
### Problem
502 Bad Gateway sometimes occurs
### Probable solution
Proxies?
### Problem
Duplicates occur in parsed links
### Probable solution
Selectors fix
