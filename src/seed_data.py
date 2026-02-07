import random
from datetime import date, timedelta
from sqlmodel import Session, select
from src.database import engine, create_db_and_tables
from src.models import Person, Todo

# Realistic Data Source
TITLES = [
    "Köpa mjölk",
    "Måla staketet",
    "Fixa bilen",
    "Ringa mormor",
    "Betala räkningar",
    "Boka resa",
    "Städa garaget",
    "Planera middag",
    "Skriva rapport",
    "Läsa bok",
    "Gå till gymmet",
    "Byta däck",
    "Klippa gräset",
    "Rensa vinden",
    "Laga cykeln",
    "Handla mat",
    "Deklarera",
    "Vattna blommor",
    "Tvätta bilen",
    "Sortera papper",
    "Backa upp datorn",
    "Installera lampor",
    "Putsa fönster",
    "Dammsuga huset",
    "Skura golv",
    "Byta glödlampor",
    "Laga middag",
    "Baka bröd",
    "Springa 5km",
    "Gå promenad",
    "Spela gitarr",
    "Lära sig Python",
    "Skriva kod",
    "Fixa buggar",
    "Distribuera app",
    "Konfigurera server",
    "Uppdatera CV",
    "Söka jobb",
    "Ringa banken",
    "Boka tandläkare",
    "Köpa present",
    "Planera fest",
]

DESCRIPTIONS = [
    "Detta är en viktig uppgift som måste göras snart.",
    "Kom ihåg att dubbelkolla alla detaljer innan du börjar.",
    "Detta kan ta lite tid, så planera in det ordentligt.",
    "Glöm inte att köpa allt material som behövs.",
    "Ring gärna och kolla öppettiderna först.",
    "Detta är en återkommande uppgift som måste hanteras.",
    "Be om hjälp om det blir för tungt.",
    "Se till att dokumentera allt du gör.",
    "Detta är prioriterat av chefen.",
    "Gör det här när du har lite extra tid över.",
    "Kan vänta tills nästa vecka om det behövs.",
    "Detta är en rolig uppgift att göra med vänner.",
    "Kräver noggrannhet och tålamod.",
    "Se till att ha rätt verktyg till hands.",
    "Följ instruktionerna noga.",
]


def create_seed_data():
    # Ensure tables exist
    create_db_and_tables()

    with Session(engine) as session:
        # 1. Get existing persons
        persons = session.exec(select(Person)).all()
        if not persons:
            print("No persons found! Run the app first to create default persons.")
            return

        print(f"Found {len(persons)} persons: {[p.name for p in persons]}")

        # 2. Generate 42 Todos
        todos_to_create = []
        today = date.today()

        for _ in range(42):
            # Randomize attributes
            title = random.choice(TITLES)
            desc = random.choice(DESCRIPTIONS) + " " + random.choice(DESCRIPTIONS)
            person = random.choice(persons)
            priority = random.randint(1, 3)

            # Deadline: -3 to +4 days from today
            days_diff = random.randint(-3, 4)
            deadline = today + timedelta(days=days_diff)

            todo = Todo(
                title=title,
                description=desc,
                priority=priority,
                deadline=deadline,
                person_id=person.id,
                completed=random.choice([True, False, False]),  # 1/3 completion chance
            )
            todos_to_create.append(todo)

        # 3. Add to session
        for t in todos_to_create:
            session.add(t)

        session.commit()
        print(f"Successfully created {len(todos_to_create)} mock todos!")


if __name__ == "__main__":
    create_seed_data()
