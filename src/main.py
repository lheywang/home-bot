# ----------------------------------------------------------------------------------
# brief : Launch the bot services
# author : l.heywang
# date : 06/09/2026
# ----------------------------------------------------------------------------------

# Imports
import asyncio
import time

from network import networkEngine
from search import searchEngine

WORDS = [
    "formattage",
    "cpu",
    "mcu😅",
    "l.Heywang",
    "alimentations",
    ["carte", "mere"],
    ["je", "suis", "un", "joli", "bonhomme", "heureux"],
    "csm",
]


async def main():
    # Open the clases
    client = await networkEngine.create("https://www.home-hardware.app/index.json")
    engine = searchEngine()

    await client.fetch()

    start = time.time()
    for word in WORDS:
        data, update = client.get_data()
        if update:
            engine.update(data)
        print(engine.search(word, 5))
    stop = time.time()
    print(
        f"Request were completed in {(stop - start) * 1000} ms, meaning each is {((stop - start) * 1000) / len(WORDS)} ms"
    )

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
