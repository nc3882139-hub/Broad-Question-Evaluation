from app.services.qa_segmenter import segment_qa


def _pages(text):
    return [{"page_number": 1, "text": text}]


def test_basic_numbered():
    segs = segment_qa(_pages(
        "1. Explain photosynthesis.\nPhotosynthesis is the process by which plants make food.\n\n"
        "2. Write a short note on APJ Abdul Kalam.\nKalam was an Indian scientist."))["segments"]
    assert len(segs) == 2
    assert segs[0]["question"] == "Explain photosynthesis."
    assert "plants make food" in segs[0]["student_answer"]
    assert segs[1]["question_id"] == 2


def test_header_variants_and_answer_markers():
    segs = segment_qa(_pages(
        "Q1. Define gravity.\nAns: Gravity is a force that attracts objects.\n"
        "Question 2 - What is a CPU?\nAnswer: The CPU is the brain of the computer."))["segments"]
    assert len(segs) == 2
    assert segs[0]["question"].startswith("Define gravity")
    assert segs[0]["student_answer"].startswith("Gravity is a force")
    assert segs[1]["question"].startswith("What is a CPU")


def test_multiline_question():
    segs = segment_qa(_pages(
        "1. Explain the working\nof a CPU in detail.\nThe CPU fetches instructions."))["segments"]
    assert "of a CPU in detail." in segs[0]["question"]
    assert segs[0]["student_answer"].startswith("The CPU fetches")


def test_numbered_list_inside_answer_is_not_a_header():
    segs = segment_qa(_pages(
        "1. Explain photosynthesis.\nPhotosynthesis has two stages.\nThe light reaction happens in the thylakoid.\n"
        "\n1. Light energy is absorbed.\n2. Water is split.\nThese steps are important."))["segments"]
    assert len(segs) == 1
    assert "Water is split" in segs[0]["student_answer"]