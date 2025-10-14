from dotenv import load_dotenv
from db import init_schema

if __name__ == "__main__":
    load_dotenv()
    init_schema()
