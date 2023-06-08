from api.api import DKProducts, Chat
from api.account import User
from api.file import FileManager
from api.products import Product
from api.site_config import Main, Category

valid_urls = {
    "chat": Chat,
    "main": Main,
    "category": Category,
    "file_manager": FileManager,
    # "dashboard": Dashboard,
    # "comment": Comment,
    # "bookmark": Bookmark,
    # "ticket": Ticket,
    # "order": Order,
    # "address": Address,
    # "wallet": Wallet,
    # "affiliate": Affiliate,
    # "payment": Payment,
    "users": User,
    "products": Product,
    "dk_products": DKProducts,
}
