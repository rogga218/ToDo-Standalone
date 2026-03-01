import random
from datetime import date, timedelta

from sqlmodel import Session, select

from src.database import create_db_and_tables, engine
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
    (
        "Detta är en kritisk och brådskande uppgift som kräver fullt fokus. Se till att alla steg i processen "
        "följs noggrant och att inga genvägar tas. Om du stöter på problem, lyft det omedelbart på nästa "
        "avstämningsmöte."
    ),
    "Kom ihåg att dubbelkolla alla detaljer innan du börjar.",
    (
        "Kom ihåg att dubbelkolla alla detaljer inför leveransen nästa vecka. Vi har lovat kunden att allt ska "
        "vara perfekt, så det är viktigt att vi inte missar några av de mindre kraven i specifikationen. Fyll "
        "på med nödvändiga resurser om det behövs."
    ),
    "Snabb och enkel sak att bocka av.",
    (
        "Det här projektet kan dra ut på tiden, så det rekommenderas starkt att du tidsestimerar det i mindre "
        "delmoment innan du påbörjar arbetet. Glöm inte att stämma av budgeten också så vi inte bryter ramarna."
    ),
    "Behövs göras innan fredag.",
    (
        "Innan du sätter igång måste du säkerställa att du köpt in eller lagt order på allt material som "
        "krävs. Skriv gärna en inköpslista och förankra med inköpsavdelningen så leveransen sker i tid. "
        "Kvitton ska redovisas som vanligt."
    ),
    "Följ instruktionerna noga.",
    (
        "Ta först kontakt med ansvarig part för att bekräfta att öppettider eller tillgänglighet stämmer med "
        "våra antaganden. Om de inte svarar via telefon, skicka iväg ett e-postmeddelande med läskvitto och "
        "invänta återkoppling innan vi går vidare."
    ),
    "Ring gärna och kolla öppettiderna först.",
    (
        "Detta är en återkommande administrativ uppgift som tenderar att glömmas bort i stressen. Kan vi försöka "
        "bygga in en påminnelse i systemet för detta framöver? Tills vidare får vi hantera det manuellt."
    ),
    "Prioriterat av chefen.",
    (
        "Den här arbetsuppgiften är ganska omfattande och kan bli överväldigande om man gör den isolerat. "
        "Tveka inte ett ögonblick att be någon i teamet om hjälp, antingen för parprogrammering, fysiskt bärande, "
        "eller bara för ett bollplank."
    ),
    "Glöm inte att dokumentera.",
    (
        "Ett absolut grundkrav här är att allting dokumenteras väl. Vi måste kunna spåra vad som ändrats och "
        "varför, särskilt utifall vi får en audit framöver. Använd vår uppsatta mall i Wiki-verktyget och länka "
        "dokumentationen hit."
    ),
    "Vänta på feedback innan start.",
    (
        "Chefen har pekat ut detta som en P1-prioritering inför stundande releasen. Lägg allt annat åt sidan "
        "tills detta är löst och testat, och rapportera status via Slack vid arbetsdagens slut varje dag."
    ),
    "Trevlig uppgift att göra med en kaffe.",
    (
        "Det är egentligen ingen stress med denna uppgift, utan se det mer som en utfyllnadssysselsättning "
        "när du har en lucka, eller kanske vill rensa tankarna med något lite mer mekaniskt och repetitivt arbete."
    ),
    "Läs igenom manualen först.",
    (
        "Det här ärendet är för närvarande blockerat i väntan på feedback från kunden, men vi förbereder "
        "uppgiften ändå. Förmodligen är det inte läge att genomföra det förrän tidigast nästa vecka, så håll "
        "ögonen på kalendern."
    ),
    "Kräver lite extra fokus.",
    (
        "Detta kommer att bli en ganska rolig, men kreativ, utmaning! Bjud gärna med kollegorna på en snabb "
        "workshop och brainstorma lite idéer innan ni bestämmer er för en konkret inriktning. Fokusera på att "
        "ha kul längs vägen."
    ),
    "Bara gör det.",
    (
        "Detta kräver en exceptionell grad av noggrannhet och stort tålamod. Ett enda misstag i detta skede kan "
        "leda till kaskadfel längre fram. Gör gärna arbetet i etapper och dubbelkolla ofta gentemot regelverket."
    ),
    (
        "Dags att smutsa ner händerna (ibland bildligt, ibland bokstavligt). Har du all nödvändig utrustning, "
        "verktyg eller licenser redo innan start? Om inte, avbryt och ordna tillträde/rättigheter först."
    ),
    (
        "Var vänlig och läs igenom hela manualen/instruktionerna från början till slut, innan något faktiskt "
        "utövas. Förra gången blev det en del strul just för att man gissade sig till hur processen skulle se ut."
    ),
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
