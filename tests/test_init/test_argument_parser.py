from sugar import ArgumentParser, auto


def test_example() -> None:
    parser = ArgumentParser()

    parser.add_positional_or_keyword(
        "name",
        help="Name of the student",
    )
    parser.add_positional_or_keyword(
        "age",
        help="Age of the student",
        action=auto(int),
    )
    parser.add_positional_or_keyword(
        "is_student",
        help="Is the student a student",
        action=auto(bool),
    )
    parser.add_positional_or_keyword(
        "gpa",
        help="GPA of the student",
        action=auto(float),
    )
    parser.add_positional_or_keyword(
        names=("courses", "c"),
        help="Courses the student is taking",
        action=auto(list[str]),
    )

    _, args, kwargs = parser.run(
        ["Stanley", "20", "True", "3.0", "-c", "Chinese", "Math", "English"]
    )

    assert args == ["Stanley", 20, True, 3.0, ["Chinese", "Math", "English"]]
    assert not kwargs
