from models import User
from sqlalchemy import inspect

mapper = inspect(User)
print("Properties in User model:")
for prop in mapper.attrs:
    print(f"- {prop.key}")
