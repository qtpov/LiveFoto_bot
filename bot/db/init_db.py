from db.session import engine, Base

# Создаём все таблицы
Base.metadata.create_all(bind=engine)

print("База данных и таблицы созданы!")
