from definitions import PROJECT_ROOT
from src.db_connector import create_db


def initialize_app():
    data_dir = PROJECT_ROOT / "data"
    data_dir.mkdir(exist_ok=True)

    create_db()

    (PROJECT_ROOT / "defaults/categories.json").copy_into(data_dir)
