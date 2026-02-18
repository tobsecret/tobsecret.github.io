import pandas as pd
from argparse import ArgumentParser
# Optionally we could get the data directly from the API but that requires a key:
# https://wiki.dominionstrategy.com/index.php?title=Special:CargoExport&tables=Components&&fields=Name%2C+Expansion&where=Purpose+in+(+%27Kingdom+Pile%27%2C+%27Landscape%27+)&order+by=Name+ASC&limit=1000&format=json

def html_to_csv(html_file, csv_file):
    tables = pd.read_html(html_file)
    df = tables[0]
    
    # clean up Types and Set columns
    df = df.assign(Types=df.Types.str.split(" - "))
    df = df.assign(Set=df.Set.str.split(", "))

    df.to_csv(csv_file)


if __name__ == "__main__":
    parser = ArgumentParser(description="Convert HTML table to CSV")
    parser.add_argument("html_file", help="Path to the HTML file")
    parser.add_argument("csv_file", help="Path to the output CSV file", default="list_of_dominion_cards.csv")
    args = parser.parse_args()
    html_to_csv(args.html_file, args.csv_file)