from bot.db.session import SessionLocal
from bot.db.models import Quest, Task, Option

async def seed_database():
    async with SessionLocal() as session:
        # Квест "Знакомство с локацией"
        quest = Quest(title="Знакомство с локацией", description="Познакомьтесь с основными зонами локации.")
        session.add(quest)
        await session.commit()
        await session.refresh(quest)

        # Задачи для квеста
        tasks = [
            Task(quest_id=quest.id, text="Что находится под номером 1?"),
            Task(quest_id=quest.id, text="Что находится под номером 2?"),
            Task(quest_id=quest.id, text="Что находится под номером 3?"),
            Task(quest_id=quest.id, text="Что находится под номером 4?"),
            Task(quest_id=quest.id, text="Что находится под номером 5?"),
        ]
        session.add_all(tasks)
        await session.commit()
        await session.refresh(tasks[0])

        # Варианты ответов для задач
        options = [
            Option(task_id=tasks[0].id, text="Касса", is_correct=True),
            Option(task_id=tasks[0].id, text="Туалет", is_correct=False),
            Option(task_id=tasks[1].id, text="Фотозона", is_correct=True),
            Option(task_id=tasks[1].id, text="Кафе", is_correct=False),
            Option(task_id=tasks[2].id, text="Игровая зона", is_correct=True),
            Option(task_id=tasks[2].id, text="Парковка", is_correct=False),
            Option(task_id=tasks[3].id, text="Ресепшн", is_correct=True),
            Option(task_id=tasks[3].id, text="Кухня", is_correct=False),
            Option(task_id=tasks[4].id, text="Склад", is_correct=True),
            Option(task_id=tasks[4].id, text="Офис", is_correct=False),
        ]
        session.add_all(options)
        await session.commit()

if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_database())