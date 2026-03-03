from aiogram import Dispatcher
from .start import router as start_router
from .catalog import router as catalog_router

def register_all_handlers(dp: Dispatcher):
    dp.include_router(start_router)
    dp.include_router(catalog_router)