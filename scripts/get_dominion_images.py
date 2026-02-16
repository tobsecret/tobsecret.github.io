import pandas as pd
from pathlib import Path
from typing import cast
import requests
import hashlib
from urllib.parse import quote
from argparse import ArgumentParser
import logging

wide_card_types = [
    "Way", "Event", "Trait", "State", 
    "Prophecy", "Project", "Landmark", "Hex",
    "Boon", "Artifact", "Ally"
    ]
card_parquet = "list_of_dominion_cards.parquet"


def card_name_to_image_url(card_name:str, wide:bool=False) -> str:
    image_name = card_name.strip().replace(" ", "_") + ".jpg"
    image_name_hash = hashlib.md5(image_name.encode()).hexdigest()
    res = "320px" if wide else "200px"
    image_name_quoted = quote(image_name)
    url = f"https://wiki.dominionstrategy.com/images/thumb/{image_name_hash[0]}/{image_name_hash[:2]}/{image_name_quoted}/{res}-{image_name_quoted}"
    return url

def card_is_wide(card_types:list[str]) -> bool:
    return not set(card_types).isdisjoint(wide_card_types)

def get_card_image(card:str, card_info:pd.DataFrame):
    if card not in card_info.index:
        raise ValueError(f"couldn't find {card} in card csv file")
    card_set = card_info.loc[card, "Set"][0]
    card_types = card_info.loc[card, "Types"]
    card_types = cast(list[str], card_types)
    card_wide = card_is_wide(card_types)
    card_image_url = card_name_to_image_url(card_name=card, wide=card_wide)
    destination_file = Path("../assets/dominion") / card_set.lower() / (card.replace(" ", "_") + ".jpg")
    if not destination_file.parent.exists():
        destination_file.parent.mkdir()
    r = requests.get(card_image_url)
    if r.status_code == 200:
        logging.info(f"got image for {card} from {card_image_url} and saved to {destination_file}")
        with open(destination_file, "wb") as f:
            f.write(r.content)
    else:
        logging.warning(f"failed to get image for {card} from {card_image_url} with status code {r.status_code}")


def get_card_images(txt_file:str, card_parquet:str=card_parquet):
    input_path = Path(txt_file)
    card_parquet_path = Path(card_parquet)
    if not input_path.exists():
        raise FileNotFoundError(input_path)
    if not card_parquet_path.exists():
        raise FileNotFoundError(card_parquet_path)
    card_info_df = pd.read_parquet(card_parquet).set_index("Name")
    with open(input_path, "r") as f:
        cards = [card.strip() for card in f.readlines()]
        for card in cards:
            get_card_image(card, card_info_df)

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
        )
    parser = ArgumentParser(description="Get image URLs for Dominion cards")
    parser.add_argument("txt_file", help="Path to the text file containing card names")
    parser.add_argument("--card_parquet", help="Path to the parquet file containing card information", default=card_parquet)
    args = parser.parse_args()
    get_card_images(args.txt_file, args.card_parquet)