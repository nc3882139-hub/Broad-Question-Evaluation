"""Seeds demo rubrics + datasets into data/ on first run.
The APJ Abdul Kalam question is DEMO DATA ONLY — the engine is fully general."""
import json

from app.config import settings

RUBRIC_SEEDS = [
    {"id": "apj-abdul-kalam-summary",
     "question": "Write a short summary on APJ Abdul Kalam.",
     "max_marks": 5,
     "reference_answer": ("Dr. A. P. J. Abdul Kalam was an Indian aerospace scientist who served "
        "as the 11th President of India. He worked with organizations such as ISRO and DRDO and "
        "played an important role in India's missile and space programmes. He was popularly known "
        "as the Missile Man of India and inspired many young people through his work and writings."),
     "source": "seed",
     "concepts": [
         {"concept": "Indian aerospace scientist", "weight": 1, "optional": False},
         {"concept": "11th President of India", "weight": 1, "optional": False},
         {"concept": "ISRO / DRDO contribution to missile and space programmes", "weight": 1, "optional": False},
         {"concept": "Missile Man of India", "weight": 1, "optional": False},
         {"concept": "Inspiration / contribution to education and youth", "weight": 1, "optional": False}]},
    {"id": "explain-photosynthesis",
     "question": "Explain photosynthesis.",
     "max_marks": 5,
     "reference_answer": ("Photosynthesis is the process by which green plants, algae and some "
        "bacteria convert light energy into chemical energy. Plants take in carbon dioxide and "
        "water and, using sunlight absorbed by chlorophyll in the chloroplasts, produce glucose "
        "(food) and release oxygen. This process is essential because it provides food and oxygen "
        "for almost all life on Earth."),
     "source": "seed",
     "concepts": [
         {"concept": "Process converting light energy into chemical energy", "weight": 1, "optional": False},
         {"concept": "Uses sunlight, water and carbon dioxide", "weight": 1, "optional": False},
         {"concept": "Produces glucose (food) and releases oxygen", "weight": 1, "optional": False},
         {"concept": "Takes place in chloroplasts using chlorophyll", "weight": 1, "optional": False},
         {"concept": "Importance: food and oxygen for life on Earth", "weight": 1, "optional": False}]},
    {"id": "working-of-a-cpu",
     "question": "Describe the working of a CPU.",
     "max_marks": 5,
     "reference_answer": ("The CPU (Central Processing Unit) is the brain of the computer that "
        "executes instructions using the fetch-decode-execute cycle. The Control Unit directs the "
        "flow of data and coordinates components, while the Arithmetic Logic Unit performs "
        "arithmetic and logical operations. Registers and cache provide fast temporary storage "
        "for data and instructions being processed."),
     "source": "seed",
     "concepts": [
         {"concept": "CPU is the central processing unit / brain of the computer", "weight": 1, "optional": False},
         {"concept": "Fetch-decode-execute cycle", "weight": 1, "optional": False},
         {"concept": "ALU performs arithmetic and logic operations", "weight": 1, "optional": False},
         {"concept": "Control Unit directs and coordinates operations", "weight": 1, "optional": False},
         {"concept": "Registers / cache provide fast temporary storage", "weight": 1, "optional": False}]},
    {"id": "advantages-of-cloud-computing",
     "question": "What are the advantages of cloud computing?",
     "max_marks": 5,
     "reference_answer": ("Cloud computing delivers computing services such as servers, storage "
        "and applications on demand over the internet with pay-as-you-go pricing. It offers "
        "scalability and elasticity, high accessibility from anywhere, reduced infrastructure and "
        "maintenance cost, and service models such as IaaS, PaaS and SaaS deployed on public, "
        "private or hybrid clouds."),
     "source": "seed",
     "concepts": [
         {"concept": "On-demand delivery of computing services over the internet", "weight": 1, "optional": False},
         {"concept": "Scalability and elasticity of resources", "weight": 1, "optional": False},
         {"concept": "Cost efficiency — pay as you go, less infrastructure", "weight": 1, "optional": False},
         {"concept": "Service models IaaS, PaaS, SaaS", "weight": 1, "optional": False},
         {"concept": "Accessibility from anywhere / easy maintenance", "weight": 1, "optional": False}]},
    {"id": "newtons-laws",
     "question": "Explain Newton's laws of motion.",
     "max_marks": 5,
     "reference_answer": ("Newton's first law states that an object remains at rest or in uniform "
        "motion unless acted upon by an external force (inertia). The second law states that force "
        "equals mass times acceleration (F = ma). The third law states that every action has an "
        "equal and opposite reaction. Examples include a ball at rest, accelerating a trolley, and "
        "rocket propulsion."),
     "source": "seed",
     "concepts": [
         {"concept": "First law: inertia — object stays at rest or uniform motion without external force", "weight": 1, "optional": False},
         {"concept": "Second law: force equals mass times acceleration (F = ma)", "weight": 1, "optional": False},
         {"concept": "Third law: every action has an equal and opposite reaction", "weight": 1, "optional": False},
         {"concept": "Real-world examples or applications of the laws", "weight": 1, "optional": False},
         {"concept": "Relationship between force, mass and acceleration", "weight": 1, "optional": False}]},
    {"id": "short-note-on-democracy",
     "question": "Write a short note on democracy.",
     "max_marks": 5,
     "reference_answer": ("Democracy is a system of government in which power lies with the "
        "people, who elect their representatives through free and fair elections. It guarantees "
        "fundamental rights and liberties, operates under the rule of law with accountable "
        "leaders, and follows majority rule while protecting the rights of minorities."),
     "source": "seed",
     "concepts": [
         {"concept": "Government by the people through elected representatives", "weight": 1, "optional": False},
         {"concept": "Free and fair elections", "weight": 1, "optional": False},
         {"concept": "Fundamental rights and liberties of citizens", "weight": 1, "optional": False},
         {"concept": "Rule of law and accountable government", "weight": 1, "optional": False},
         {"concept": "Majority rule with protection of minority rights", "weight": 1, "optional": False}]},
    {"id": "causes-of-climate-change",
     "question": "Explain the causes of climate change.",
     "max_marks": 5,
     "reference_answer": ("Climate change is driven mainly by greenhouse gases such as carbon "
        "dioxide and methane, which trap heat in the atmosphere. The largest human cause is the "
        "burning of fossil fuels for energy, industry and transport. Deforestation reduces the "
        "Earth's capacity to absorb carbon dioxide, and industrial agriculture adds further "
        "emissions. The result is global warming, rising sea levels and extreme weather events."),
     "source": "seed",
     "concepts": [
         {"concept": "Greenhouse gases (CO2, methane) trap heat in the atmosphere", "weight": 1, "optional": False},
         {"concept": "Burning of fossil fuels is the main human cause", "weight": 1, "optional": False},
         {"concept": "Deforestation reduces CO2 absorption", "weight": 1, "optional": False},
         {"concept": "Industry, transport and agriculture emissions", "weight": 1, "optional": False},
         {"concept": "Effects: global warming, sea level rise, extreme weather", "weight": 1, "optional": False}]},
]

DEMO_ANSWERS = [  # same question, five quality levels — used by demo + grading.csv
    {"label": "excellent", "score": 5, "answer": (
        "Dr. A. P. J. Abdul Kalam was an Indian aerospace scientist who served as the 11th "
        "President of India from 2002 to 2007. He worked with ISRO and DRDO and played a major "
        "role in India's missile and space programmes, including the AGNI and SLV projects. He "
        "was popularly known as the Missile Man of India. He was also called the People's "
        "President because he loved teaching and inspired millions of young people through his "
        "speeches and books such as Wings of Fire.")},
    {"label": "good", "score": 4, "answer": (
        "Dr. Kalam was a famous Indian aerospace scientist. He worked at ISRO and DRDO on "
        "India's missile programmes and was known as the Missile Man of India. He served as the "
        "11th President of India and wrote several books.")},
    {"label": "average", "score": 3, "answer": (
        "Dr. Kalam was an Indian scientist. He became the President of India. People called him "
        "the Missile Man.")},
    {"label": "incomplete", "score": 1.5, "answer": (
        "He was a great scientist and a very good person.")},
    {"label": "irrelevant", "score": 0, "answer": (
        "Cricket is a popular sport played in many countries. The Cricket World Cup is held "
        "every four years and India has won the tournament twice.")},
]

KALAM_Q = RUBRIC_SEEDS[0]["question"]
DEMO_RAW_TEXT = "\n\n".join(
    f"Question {i + 1}. {KALAM_Q}\n{a['answer']}" for i, a in enumerate(DEMO_ANSWERS))

SENTIMENT_CSV = """text,label
I really enjoyed this lesson today,positive
The topic was about photosynthesis,neutral
I did not understand this topic,negative
This chapter explains how plants make food,neutral
I love learning about space and missiles,positive
This is too difficult and confusing,negative
The teacher explained the concept clearly,positive
Answer written for question three,neutral
I am stuck and unable to solve this problem,negative
The experiment was fun and exciting,positive
Chapter five covers the causes of climate change,neutral
I found the exam very hard and stressful,negative
The lecture notes were helpful and clear,positive
Definitions of democracy and its types,neutral
I think I might have failed this test,negative
This subject is amazing and interesting,positive
The diagram shows the water cycle,neutral
I am worried about my marks,negative
"""

UNLABELED_JSONL = "\n".join(
    json.dumps({"text": t}) for t in [
        "The process of photosynthesis converts sunlight into chemical energy stored in glucose.",
        "A CPU executes instructions using the fetch decode and execute cycle with the ALU and control unit.",
        "Dr. Kalam played an important role in the development of India's missile programme.",
        "Democracy allows citizens to choose their representatives through free and fair elections.",
        "Cloud computing provides scalable computing resources over the internet on demand.",
        "Newton's second law relates force mass and acceleration through the equation F equals m a.",
        "Greenhouse gases trap heat in the atmosphere and warm the surface of the Earth.",
        "Chlorophyll in the chloroplasts absorbs light energy during the light reaction.",
        "The control unit directs the flow of data between the processor memory and input output devices.",
        "Students who revise regularly and practice writing answers tend to perform better in exams.",
    ]) + "\n"


def seed_all():
    """Idempotent — writes any missing demo files so the project runs out of the box."""
    settings.RUBRIC_DIR.mkdir(parents=True, exist_ok=True)
    for r in RUBRIC_SEEDS:
        p = settings.RUBRIC_DIR / f"{r['id']}.json"
        if not p.exists():
            p.write_text(json.dumps(r, indent=2, ensure_ascii=False), encoding="utf-8")

    grading_csv = settings.DATA_DIR / "grading" / "grading.csv"
    grading_csv.parent.mkdir(parents=True, exist_ok=True)
    if not grading_csv.exists():
        rows = ["question_id,question,answer,max_marks,score"]
        for i, a in enumerate(DEMO_ANSWERS, 1):
            ans = a["answer"].replace('"', '""')
            q = KALAM_Q.replace('"', '""')
            rows.append(f'{i},"{q}","{ans}",5,{a["score"]}')
        grading_csv.write_text("\n".join(rows) + "\n", encoding="utf-8")

    demo_json = settings.DATA_DIR / "grading" / "demo_answers.json"
    if not demo_json.exists():
        demo_json.write_text(json.dumps(DEMO_ANSWERS, indent=2), encoding="utf-8")

    s_csv = settings.DATA_DIR / "sentiment" / "sentiment.csv"
    s_csv.parent.mkdir(parents=True, exist_ok=True)
    if not s_csv.exists():
        s_csv.write_text(SENTIMENT_CSV, encoding="utf-8")

    u_jsonl = settings.DATA_DIR / "unlabeled" / "unlabeled_answers.jsonl"
    u_jsonl.parent.mkdir(parents=True, exist_ok=True)
    if not u_jsonl.exists():
        u_jsonl.write_text(UNLABELED_JSONL, encoding="utf-8")

    readme = settings.DATA_DIR / "DATASETS.md"
    if not readme.exists():
        readme.write_text(
            "# Dataset folders\n\n"
            "- `raw/` — uploaded answer sheets (PDF/images) as received.\n"
            "- `processed/` — OCR output and segmented Q/A JSON.\n"
            "- `unlabeled/` — unlabeled student answers for self-supervised pretraining (JSONL/TXT).\n"
            "- `sentiment/` — labeled sentiment data (`text,label` CSV or JSONL).\n"
            "- `grading/` — graded answers (`question_id,question,answer,max_marks,score`).\n"
            "- `rubrics/` — question-specific rubric JSON files.\n\n"
            "Legal sources for research datasets (do NOT commit copyrighted data):\n"
            "ASAP / ASAP-SAS (Kaggle, The Hewlett Foundation), SciEntsBank & SemEval-2013 Task 3\n"
            "(student response assessment), Hewlett HP:SAS, and EngSAF where licensing permits.\n"
            "Place downloaded files here and point the training scripts at them.\n",
            encoding="utf-8")