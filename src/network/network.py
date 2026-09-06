# ----------------------------------------------------------------------------------
# brief : Define the network class
# author : l.heywang
# date : 06/09/2026
# ----------------------------------------------------------------------------------

# Imports
import aiohttp
import asyncio
import time


class networkEngine:
    """
    Handle the network IO from and to the base website. Does not ever know what discord is.
    """

    def __init__(self, url: str, session: aiohttp.ClientSession):
        # Store the requested url
        self.url = url

        # Store some state settings
        self.session = session
        self.etag = 0
        self.ts = 0
        self.is_updating = False
        self.is_updated = False

        # create the dict
        self._data = dict()
        self._valid = False

    # ------------------------------------------
    # BASIC METHODS
    # ------------------------------------------

    @classmethod
    async def create(cls, url: str):
        # Prepare the ressources before init
        session = aiohttp.ClientSession()

        # Init the class
        return cls(url=url, session=session)

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    # ------------------------------------------
    # DATA IO
    # ------------------------------------------
    def get_data(self) -> tuple[dict, bool]:
        """
        Return the data if available and a boolean to indicate if the data was updated or not.

        Will trigger the refresh if the data is older than 60 seconds.
        """

        # Fetch the time
        now = time.monotonic()

        # Trigger the refresh if needed
        if ((now - self.ts > 60) and not self.is_updating) or (not self._valid):
            asyncio.create_task(self.fetch())

        # If the data is valid, return.
        if self._valid:
            updated = self.is_updated
            self.is_updated = False
            return self._data, updated
        else:
            return dict(), False

    # ------------------------------------------
    # DATA SYNC
    # ------------------------------------------

    async def fetch(self):
        """
        Ensure the data update is done safely
        """

        self.is_updating = True

        try:
            await self._sync()
            self.ts = time.monotonic()
        except Exception as e:
            print(f"[WARNING] Could not fetch data : {e}")
        finally:
            self.is_updating = False
            self.is_updated = True

    async def _sync(self):

        # Build the headers
        headers = {}
        if self.etag:
            headers["If-None-Match"] = self.etag

        # Request
        async with self.session.get(self.url, headers=headers) as response:

            # ETAG has not changed.
            if response.status == 304:
                self._valid = True
                return

            if response.status == 200:
                self.etag = response.headers.get("ETag")
                self._data = await response.json(content_type=None)
                self._valid = True
                print("[INFO] Updated the database in cache")
                return

            response.raise_for_status()
