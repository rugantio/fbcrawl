#TYPE="fb"
TYPE="likers"
EMAIL="nicejaewon@gmail.com"
PASSWORD="qwcv135A"
PAGE="SBS8news"
DATE="2020-02-11"
OUT=$PAGE-$DATE.csv
LANG=kr
scrapy crawl $TYPE -a email="$EMAIL" -a password="$PASSWORD" -a page="$PAGE" -a date="$DATE" -a lang="kr" -o $OUT
